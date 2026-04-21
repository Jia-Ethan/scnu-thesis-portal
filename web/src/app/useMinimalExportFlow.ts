import { useEffect, useMemo, useRef, useState } from "react";
import type { HealthResponse, PrecheckResponse } from "../generated/contracts";
import {
  ApiError,
  cancelPublicExportJob,
  createPublicExportJob,
  downloadUrlAsBlob,
  downloadBlob,
  getPublicExportJob,
  getHealth,
  publicPrecheckDocx,
  publicPrecheckText,
  type PublicExportJobResponse,
} from "./api";
import { exportFilename, inferPhase, mapApiError, validateDocxFile, validateTextInput, type FlowPhase, type InlineErrorState } from "./domain";

const EXPORT_JOB_POLL_INTERVAL_MS = typeof navigator !== "undefined" && /jsdom/i.test(navigator.userAgent) ? 20 : 700;

export function useMinimalExportFlow() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [rawText, setRawText] = useState("");
  const [busy, setBusy] = useState(false);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [precheck, setPrecheck] = useState<PrecheckResponse | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportMessage, setExportMessage] = useState("");
  const [inlineError, setInlineError] = useState<InlineErrorState | null>(null);
  const exportJobIdRef = useRef<string | null>(null);
  const cancelRequestedRef = useRef(false);

  useEffect(() => {
    getHealth()
      .then((response) => {
        setHealth(response);
      })
      .catch((error) => setInlineError(mapApiError(error instanceof ApiError ? error : new ApiError("健康检查失败", "NETWORK_ERROR"))));
  }, []);

  const phase: FlowPhase = useMemo(
    () => inferPhase(rawText, selectedFile, busy, previewModalOpen, exporting),
    [busy, exporting, previewModalOpen, rawText, selectedFile],
  );

  function clearAll() {
    setSelectedFile(null);
    setRawText("");
    setBusy(false);
    setPreviewModalOpen(false);
    setPrecheck(null);
    setExporting(false);
    setExportProgress(0);
    setExportMessage("");
    setInlineError(null);
    exportJobIdRef.current = null;
    cancelRequestedRef.current = false;
  }

  function resetResult() {
    if (precheck) setPrecheck(null);
    if (previewModalOpen) setPreviewModalOpen(false);
  }

  function handleUploadTrigger() {
    if (busy || exporting) return false;
    if (rawText.trim()) {
      setInlineError({ message: "请先清空当前输入，再切换输入方式。", code: "SOURCE_CONFLICT" });
      return false;
    }
    setInlineError(null);
    return true;
  }

  function handleFileSelect(file: File | null) {
    if (busy || exporting) {
      return;
    }
    if (rawText.trim()) {
      setInlineError({ message: "请先清空当前输入，再切换输入方式。", code: "SOURCE_CONFLICT" });
      return;
    }
    resetResult();
    const validation = validateDocxFile(file);
    if (validation && file) {
      setSelectedFile(null);
      setInlineError(validation);
      return;
    }
    setInlineError(null);
    setSelectedFile(file);
  }

  function handleTextChange(value: string) {
    if (selectedFile && value.trim()) {
      setInlineError({ message: "请先清空当前输入，再切换输入方式。", code: "SOURCE_CONFLICT" });
      return;
    }
    resetResult();
    setInlineError(null);
    setRawText(value);
  }

  async function handlePrecheck() {
    setInlineError(null);
    resetResult();

    const validation = selectedFile ? validateDocxFile(selectedFile) : validateTextInput(rawText);
    if (validation) {
      setInlineError(validation);
      return;
    }

    setBusy(true);
    try {
      const response = selectedFile ? await publicPrecheckDocx(selectedFile, true, "") : await publicPrecheckText(rawText, true, "");
      setPrecheck(response);
      setPreviewModalOpen(true);
    } catch (error) {
      setInlineError(mapApiError(error instanceof ApiError ? error : new ApiError("预检失败", "PARSE_FAILED")));
    } finally {
      setBusy(false);
    }
  }

  function handleCancelPreview() {
    setPreviewModalOpen(false);
  }

  function syncExportJob(job: PublicExportJobResponse) {
    setExportProgress(job.progress);
    setExportMessage(job.message || "正在生成 Word 文件");
  }

  function sleep(ms: number) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
  }

  async function handleConfirmExport() {
    if (!precheck) {
      setInlineError({ message: "请先完成预检后再导出。", code: "FIELD_MISSING" });
      return;
    }

    setInlineError(null);
    setPreviewModalOpen(false);
    setExporting(true);
    setExportProgress(0);
    setExportMessage("正在创建导出任务。");
    cancelRequestedRef.current = false;

    try {
      if (!precheck.export_token) {
        throw new ApiError("导出凭证已失效，请重新预检后再导出。", "EXPORT_TOKEN_INVALID");
      }
      let job = await createPublicExportJob(precheck.thesis, precheck.export_token);
      exportJobIdRef.current = job.job_id;
      syncExportJob(job);

      while (job.status === "running") {
        await sleep(EXPORT_JOB_POLL_INTERVAL_MS);
        if (cancelRequestedRef.current) {
          return;
        }
        job = await getPublicExportJob(job.job_id);
        syncExportJob(job);
      }

      if (job.status === "canceled") {
        throw new ApiError("导出已取消，可重新导出。", "EXPORT_CANCELED");
      }
      if (job.status === "failed") {
        throw new ApiError(job.message || "导出失败，请稍后重试。", job.error_code || "EXPORT_FAILED");
      }
      if (!job.download_url) {
        throw new ApiError("导出文件尚未生成，请重新导出。", "EXPORT_FAILED");
      }

      const blob = await downloadUrlAsBlob(job.download_url);
      setExportProgress(100);
      downloadBlob(blob, exportFilename(precheck.thesis));
      await new Promise((resolve) => window.setTimeout(resolve, 220));
      clearAll();
    } catch (error) {
      setExporting(false);
      setExportMessage("");
      setInlineError(mapApiError(error instanceof ApiError ? error : new ApiError("导出失败", "EXPORT_FAILED")));
    }
  }

  async function handleCancelExport() {
    const jobId = exportJobIdRef.current;
    cancelRequestedRef.current = true;
    if (!jobId) {
      setExporting(false);
      setInlineError({ message: "导出已取消，可重新导出。", code: "EXPORT_CANCELED" });
      return;
    }
    try {
      const job = await cancelPublicExportJob(jobId);
      syncExportJob(job);
      setInlineError({ message: "导出已取消，可重新导出。", code: "EXPORT_CANCELED" });
    } catch (error) {
      setInlineError(mapApiError(error instanceof ApiError ? error : new ApiError("取消失败，请稍后重试。", "EXPORT_FAILED")));
    } finally {
      setExporting(false);
      setExportMessage("");
    }
  }

  const canRetryExport =
    Boolean(precheck?.summary.can_confirm) &&
    !busy &&
    !exporting &&
    !previewModalOpen &&
    (inlineError?.code === "EXPORT_FAILED" || inlineError?.code === "EXPORT_CANCELED");

  return {
    health,
    selectedFile,
    rawText,
    phase,
    busy,
    previewModalOpen,
    precheck,
    exporting,
    exportProgress,
    exportMessage,
    inlineError,
    canRetryExport,
    clearAll,
    handleFileSelect,
    handleUploadTrigger,
    handleTextChange,
    handlePrecheck,
    handleCancelPreview,
    handleConfirmExport,
    handleCancelExport,
    handleRetryExport: handleConfirmExport,
  };
}
