import { useState } from "react";
import type { NormalizedThesis } from "../generated/contracts";
import { ApiError, downloadBlob, exportThesis } from "./api";
import type { ExportKind, ExportReadiness, ToastState } from "./domain";
import { formatFieldList } from "./domain";

type UseExportFlowOptions = {
  thesis: NormalizedThesis;
  readiness: ExportReadiness;
};

export function useExportFlow({ thesis, readiness }: UseExportFlowOptions) {
  const [exporting, setExporting] = useState<ExportKind | null>(null);
  const [exportError, setExportError] = useState<ApiError | null>(null);
  const [exportToast, setExportToast] = useState<ToastState>(null);

  function resetExportError() {
    if (exportError) setExportError(null);
  }

  function clearExportToast() {
    setExportToast(null);
  }

  async function handleExport(kind: ExportKind) {
    resetExportError();
    clearExportToast();

    if (kind === "tex" && !readiness.canExport) {
      setExportError(
        new ApiError(`导出前请先补全：${formatFieldList(readiness.missingRequired)}。`, "FIELD_MISSING", {
          missing_fields: readiness.missingRequired.map((item) => item.field),
        }),
      );
      return;
    }

    setExporting(kind);
    try {
      const blob = await exportThesis(kind, thesis);
      const title = thesis.metadata.title || "scnu-thesis";
      downloadBlob(blob, kind === "tex" ? `${title}.zip` : `${title}.pdf`);
      setExportToast({
        tone: "success",
        title: kind === "tex" ? ".tex 工程 zip 已生成" : "PDF 已生成",
        message: kind === "tex" ? "可以下载后在本地继续调整与编译。" : "请检查下载文件是否符合预期。",
      });
    } catch (err) {
      setExportError(err instanceof ApiError ? err : new ApiError("导出失败", "EXPORT_FAILED"));
    } finally {
      setExporting(null);
    }
  }

  return {
    exporting,
    exportError,
    exportToast,
    clearExportToast,
    resetExportError,
    handleExport,
  };
}
