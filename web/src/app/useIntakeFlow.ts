import { FormEvent, useState } from "react";
import type { NormalizedThesis } from "../generated/contracts";
import { ApiError, normalizeText, parseDocx } from "./api";
import type { InputMode, ToastState } from "./domain";

type UseIntakeFlowOptions = {
  onParsed: (thesis: NormalizedThesis) => void;
};

export function useIntakeFlow({ onParsed }: UseIntakeFlowOptions) {
  const [mode, setMode] = useState<InputMode>("docx");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [rawText, setRawText] = useState("");
  const [busy, setBusy] = useState(false);
  const [intakeError, setIntakeError] = useState<ApiError | null>(null);
  const [intakeToast, setIntakeToast] = useState<ToastState>(null);

  function resetIntakeError() {
    if (intakeError) setIntakeError(null);
  }

  function clearIntakeToast() {
    setIntakeToast(null);
  }

  function handleModeChange(nextMode: InputMode) {
    setMode(nextMode);
    resetIntakeError();
  }

  function handleFileChange(file: File | null) {
    setSelectedFile(file);
    resetIntakeError();
  }

  function handleTextChange(value: string) {
    setRawText(value);
    resetIntakeError();
  }

  async function handleParse(event?: FormEvent) {
    event?.preventDefault();
    resetIntakeError();
    clearIntakeToast();

    if (mode === "docx" && !selectedFile) {
      setIntakeError(new ApiError("请先选择一个 .docx 文件。", "UNSUPPORTED_FILE_TYPE"));
      return;
    }

    if (mode === "text" && !rawText.trim()) {
      setIntakeError(new ApiError("粘贴内容为空，请先输入论文正文或章节内容。", "CONTENT_EMPTY"));
      return;
    }

    setBusy(true);
    try {
      const parsed = mode === "docx" ? await parseDocx(selectedFile as File) : await normalizeText(rawText);
      onParsed(parsed);
      setIntakeToast({
        tone: "success",
        title: "结构识别完成",
        message: "请先校对字段与章节，再导出 .tex 工程 zip。",
      });
    } catch (err) {
      setIntakeError(err instanceof ApiError ? err : new ApiError("解析失败", "PARSE_FAILED"));
    } finally {
      setBusy(false);
    }
  }

  return {
    mode,
    selectedFile,
    rawText,
    busy,
    intakeError,
    intakeToast,
    clearIntakeToast,
    resetIntakeError,
    handleModeChange,
    handleFileChange,
    handleTextChange,
    handleParse,
  };
}
