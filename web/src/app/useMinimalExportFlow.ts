import { useEffect, useMemo, useRef, useState } from "react";
import type { CoverFields, HealthResponse, PrecheckResponse } from "../generated/contracts";
import {
  ApiError,
  downloadBlob,
  exportDocx,
  getHealth,
  precheckDocx,
  precheckText,
  precheckFromStory2Paper,
  story2paperGenerate,
  story2paperGetResult,
  story2paperWS,
  type Story2PaperWSEvent,
} from "./api";
import { exportFilename, inferPhase, mapApiError, validateDocxFile, validateTextInput, type FlowPhase, type InlineErrorState } from "./domain";

const EXPORT_MIN_DURATION_MS = typeof navigator !== "undefined" && /jsdom/i.test(navigator.userAgent) ? 20 : 4200;

export type AIGenPhase = "idle" | "generating" | "done" | "error";

const EMPTY_COVER = (): CoverFields => ({
  title: "",
  advisor: "",
  student_name: "",
  student_id: "",
  school: "华南师范大学",
  department: "",
  major: "",
  class_name: "",
  graduation_time: "",
});

export function useMinimalExportFlow() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [rawText, setRawText] = useState("");
  const [busy, setBusy] = useState(false);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [precheck, setPrecheck] = useState<PrecheckResponse | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [inlineError, setInlineError] = useState<InlineErrorState | null>(null);

  // AI generation state
  const [aiPhase, setAiPhase] = useState<AIGenPhase>("idle");
  const [sourceTab, setSourceTab] = useState<"upload" | "ai">("upload");
  const [researchPrompt, setResearchPrompt] = useState("");
  const [paperId, setPaperId] = useState<string | null>(null);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const [sectionIndex, setSectionIndex] = useState(0);
  const [revisionRound, setRevisionRound] = useState(0);
  const [aiError, setAiError] = useState<string | null>(null);
  const [coverFields, setCoverFields] = useState<CoverFields>(EMPTY_COVER);

  // WebSocket reference for cleanup
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    getHealth()
      .then((response) => {
        setHealth(response);
      })
      .catch((error) => setInlineError(mapApiError(error instanceof ApiError ? error : new ApiError("健康检查失败", "NETWORK_ERROR"))));
  }, []);

  useEffect(() => {
    if (!exporting) {
      setExportProgress(0);
      return;
    }

    setExportProgress(0);
    const timer = window.setInterval(() => {
      setExportProgress((current) => {
        if (current >= 92) return current;
        const next = current + Math.max(1.5, (92 - current) * 0.11);
        return Math.min(next, 92);
      });
    }, 120);

    return () => window.clearInterval(timer);
  }, [exporting]);

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
    setInlineError(null);
    clearAIGen();
  }

  function clearAIGen() {
    wsRef.current?.close();
    wsRef.current = null;
    setAiPhase("idle");
    setPaperId(null);
    setCurrentAgent(null);
    setSectionIndex(0);
    setRevisionRound(0);
    setAiError(null);
    setResearchPrompt("");
    setCoverFields(EMPTY_COVER());
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
      const response = selectedFile ? await precheckDocx(selectedFile) : await precheckText(rawText);
      setPrecheck(response);
      setPreviewModalOpen(true);
    } catch (error) {
      setInlineError(mapApiError(error instanceof ApiError ? error : new ApiError("预检失败", "PARSE_FAILED")));
    } finally {
      setBusy(false);
    }
  }

  async function handleAIGenerate() {
    if (!researchPrompt.trim()) return;
    setInlineError(null);
    setAiPhase("generating");
    setPaperId(null);
    setCurrentAgent(null);
    setSectionIndex(0);
    setRevisionRound(0);
    setAiError(null);

    try {
      // Start generation
      const genRes = await story2paperGenerate(researchPrompt);
      const pid = genRes.paper_id;
      setPaperId(pid);

      // Connect WebSocket to track progress
      const ws = story2paperWS(pid);
      wsRef.current = ws;

      await new Promise<void>((resolve, reject) => {
        ws.onmessage = (event: MessageEvent<string>) => {
          try {
            const data = JSON.parse(event.data) as Story2PaperWSEvent;
            if (data.current_agent) setCurrentAgent(data.current_agent ?? null);
            if (data.section_index !== undefined) setSectionIndex(data.section_index ?? 0);
            if (data.revision_round !== undefined) setRevisionRound(data.revision_round ?? 0);
            if (data.event === "done" && data.final_output) {
              ws.close();
              resolve();
            }
          } catch {
            // ignore parse errors
          }
        };
        ws.onerror = () => {
          ws.close();
          reject(new ApiError("WebSocket 连接失败", "WS_ERROR"));
        };
        ws.onclose = () => {
          if (wsRef.current === ws) resolve();
        };
      });

      // Fetch full result
      const result = await story2paperGetResult(pid);

      // Build schema_data from result
      const schemaData = {
        title: (result.outline as Record<string, unknown>)?.["title"] ?? researchPrompt,
        outline: result.outline ?? {},
        section_drafts: result.section_drafts ?? [],
        contract: result.contract ?? {},
        figures: ((result.contract as Record<string, unknown>)?.["figures"] as unknown[]) ?? [],
        tables: ((result.contract as Record<string, unknown>)?.["tables"] as unknown[]) ?? [],
        references: ((result.contract as Record<string, unknown>)?.["citations"] as unknown[]) ?? [],
        abstract_zh: "",
        abstract_en: "",
        keywords: [],
      };

      // Precheck via portal
      setBusy(true);
      const precheckRes = await precheckFromStory2Paper(schemaData, coverFields);
      setPrecheck(precheckRes);
      setPreviewModalOpen(true);
      setAiPhase("done");
    } catch (error) {
      setAiPhase("error");
      setAiError(
        error instanceof ApiError
          ? error.message
          : error instanceof Error
            ? error.message
            : "生成失败，请稍后重试",
      );
      wsRef.current?.close();
    } finally {
      setBusy(false);
      wsRef.current = null;
    }
  }

  function handleCancelPreview() {
    setPreviewModalOpen(false);
  }

  async function handleConfirmExport() {
    if (!precheck?.summary.can_confirm) {
      setInlineError({ message: precheck?.summary.blocking_message || "预检仍存在阻塞项，暂时无法导出。", code: "FIELD_MISSING" });
      return;
    }

    setInlineError(null);
    setPreviewModalOpen(false);
    setExporting(true);

    try {
      const minDelay = new Promise((resolve) => window.setTimeout(resolve, EXPORT_MIN_DURATION_MS));
      const [blob] = await Promise.all([exportDocx(precheck.thesis), minDelay]);
      setExportProgress(100);
      downloadBlob(blob, exportFilename(precheck.thesis));
      await new Promise((resolve) => window.setTimeout(resolve, 220));
      clearAll();
    } catch (error) {
      setExporting(false);
      setInlineError(mapApiError(error instanceof ApiError ? error : new ApiError("导出失败", "EXPORT_FAILED")));
    }
  }

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
    inlineError,
    clearAll,
    handleFileSelect,
    handleUploadTrigger,
    handleTextChange,
    handlePrecheck,
    handleCancelPreview,
    handleConfirmExport,
    // AI generation
    aiPhase,
    sourceTab,
    setSourceTab,
    researchPrompt,
    paperId,
    currentAgent,
    sectionIndex,
    revisionRound,
    aiError,
    coverFields,
    setResearchPrompt,
    setCoverFields,
    handleAIGenerate,
    handleAIClear: clearAIGen,
  };
}
