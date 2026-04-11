import { FormEvent, useEffect, useMemo, useState } from "react";
import type { BodySection, HealthResponse, MetadataFields, NormalizedThesis } from "../generated/contracts";
import { ApiError, downloadBlob, exportThesis, getHealth, normalizeText, parseDocx } from "./api";
import {
  ExportKind,
  InputMode,
  WorkspaceStep,
  createBlankSection,
  defaultThesis,
  hydrateThesis,
} from "./domain";

export type ToastState = {
  tone: "success" | "info";
  title: string;
  message: string;
} | null;

export function useThesisWorkspace() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [mode, setMode] = useState<InputMode>("docx");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [rawText, setRawText] = useState("");
  const [thesis, setThesis] = useState<NormalizedThesis | null>(null);
  const [busy, setBusy] = useState(false);
  const [exporting, setExporting] = useState<ExportKind | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [showDebug, setShowDebug] = useState(false);
  const [toast, setToast] = useState<ToastState>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err) => setError(err instanceof ApiError ? err : new ApiError("健康检查失败", "NETWORK_ERROR")));
  }, []);

  const currentThesis = useMemo(() => thesis ?? defaultThesis(health), [health, thesis]);
  const step: WorkspaceStep = exporting ? "export" : busy ? "recognizing" : thesis ? "review" : "input";

  function resetError() {
    if (error) setError(null);
  }

  function clearToast() {
    setToast(null);
  }

  function handleModeChange(nextMode: InputMode) {
    setMode(nextMode);
    resetError();
  }

  function handleFileChange(file: File | null) {
    setSelectedFile(file);
    resetError();
  }

  function handleTextChange(value: string) {
    setRawText(value);
    resetError();
  }

  function updateMetadata(field: keyof MetadataFields, value: string) {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      return { ...base, metadata: { ...base.metadata, [field]: value } };
    });
  }

  function updateAbstract(kind: "cn" | "en", patch: Partial<NormalizedThesis["abstract_cn"]>) {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      const field = kind === "cn" ? "abstract_cn" : "abstract_en";
      return { ...base, [field]: { ...base[field], ...patch } };
    });
  }

  function updateSection(index: number, patch: Partial<BodySection>) {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      const bodySections = [...base.body_sections];
      bodySections[index] = { ...bodySections[index], ...patch };
      return { ...base, body_sections: bodySections };
    });
  }

  function addSection() {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      return { ...base, body_sections: [...base.body_sections, createBlankSection(base.body_sections.length)] };
    });
  }

  function removeSection(index: number) {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      return { ...base, body_sections: base.body_sections.filter((_, currentIndex) => currentIndex !== index) };
    });
  }

  function updateReferences(items: string[]) {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      return { ...base, references: { items } };
    });
  }

  function updateLongText(field: "acknowledgements" | "appendix", value: string) {
    setThesis((prev) => {
      const base = prev ?? defaultThesis(health);
      return { ...base, [field]: value };
    });
  }

  async function handleParse(event?: FormEvent) {
    event?.preventDefault();
    resetError();
    clearToast();

    if (mode === "docx" && !selectedFile) {
      setError(new ApiError("请先选择一个 .docx 文件。", "UNSUPPORTED_FILE_TYPE"));
      return;
    }

    if (mode === "text" && !rawText.trim()) {
      setError(new ApiError("粘贴内容为空，请先输入论文正文或章节内容。", "CONTENT_EMPTY"));
      return;
    }

    setBusy(true);
    try {
      const parsed = mode === "docx" ? await parseDocx(selectedFile as File) : await normalizeText(rawText);
      setThesis(hydrateThesis(parsed, health));
      setToast({
        tone: "success",
        title: "结构识别完成",
        message: "请先校对字段与章节，再导出 .tex 工程 zip。",
      });
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError("解析失败", "PARSE_FAILED"));
    } finally {
      setBusy(false);
    }
  }

  async function handleExport(kind: ExportKind) {
    resetError();
    clearToast();
    setExporting(kind);
    try {
      const blob = await exportThesis(kind, currentThesis);
      const title = currentThesis.metadata.title || "scnu-thesis";
      downloadBlob(blob, kind === "tex" ? `${title}.zip` : `${title}.pdf`);
      setToast({
        tone: "success",
        title: kind === "tex" ? ".tex 工程 zip 已生成" : "PDF 已生成",
        message: kind === "tex" ? "可以下载后在本地继续调整与编译。" : "请检查下载文件是否符合预期。",
      });
    } catch (err) {
      setError(err instanceof ApiError ? err : new ApiError("导出失败", "EXPORT_FAILED"));
    } finally {
      setExporting(null);
    }
  }

  return {
    health,
    mode,
    selectedFile,
    rawText,
    thesis,
    currentThesis,
    busy,
    exporting,
    error,
    showDebug,
    toast,
    step,
    setShowDebug,
    clearToast,
    handleModeChange,
    handleFileChange,
    handleTextChange,
    handleParse,
    handleExport,
    updateMetadata,
    updateAbstract,
    updateSection,
    addSection,
    removeSection,
    updateReferences,
    updateLongText,
  };
}
