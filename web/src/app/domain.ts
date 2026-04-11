import type { BodySection, HealthResponse, MetadataFields, NormalizedThesis } from "../generated/contracts";
import { ApiError } from "./api";

export type InputMode = "docx" | "text";
export type ExportKind = "tex" | "pdf";
export type WorkspaceStep = "input" | "recognizing" | "review" | "export";

export type FriendlyError = {
  title: string;
  message: string;
  action: string;
  code?: string;
};

export const emptyMetadata: MetadataFields = {
  title: "",
  author_name: "",
  student_id: "",
  department: "",
  major: "",
  class_name: "",
  advisor_name: "",
  submission_date: new Date().toISOString().slice(0, 10),
};

export function defaultThesis(health: HealthResponse | null): NormalizedThesis {
  return {
    source_type: "text",
    metadata: { ...emptyMetadata },
    abstract_cn: { content: "", keywords: [] },
    abstract_en: { content: "", keywords: [] },
    body_sections: [],
    references: { items: [] },
    acknowledgements: "",
    appendix: "",
    warnings: [],
    parse_errors: [],
    capabilities: health?.capabilities ?? {
      tex_zip: true,
      pdf: false,
      pdf_reason: "当前能力尚未加载完成。",
    },
  };
}

export function hydrateThesis(parsed: NormalizedThesis, health: HealthResponse | null): NormalizedThesis {
  return {
    ...parsed,
    metadata: { ...emptyMetadata, ...parsed.metadata },
    capabilities: health?.capabilities ?? parsed.capabilities,
  };
}

export function createBlankSection(count: number): BodySection {
  return {
    id: `manual-${Date.now()}`,
    level: 1,
    title: `新章节 ${count + 1}`,
    content: "",
  };
}

export function keywordsToString(keywords: string[]) {
  return keywords.join("；");
}

export function splitKeywords(value: string) {
  return value
    .split(/[\n，,；;、]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function referencesToString(thesis: NormalizedThesis) {
  return thesis.references.items.join("\n");
}

export function splitReferences(value: string) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function formatBytes(bytes?: number) {
  if (!bytes) return "加载中";
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${Math.floor(bytes / 1024 / 1024)} MB`;
}

export function friendlyError(error: ApiError | null): FriendlyError | null {
  if (!error) return null;

  const map: Record<string, FriendlyError> = {
    UNSUPPORTED_FILE_TYPE: {
      title: "文件格式不符合要求",
      message: "当前只支持上传 .docx 文件，暂不支持 .doc、PDF 或其他格式。",
      action: "请重新选择 Word 的 .docx 文件，或切换到粘贴正文模式。",
    },
    CONTENT_EMPTY: {
      title: "没有识别到可用内容",
      message: "提交的文件或文本为空，系统无法继续做结构识别。",
      action: "请确认文件内有正文内容，或在文本框中粘贴论文正文后再试。",
    },
    FILE_TOO_LARGE: {
      title: "文件超过上传上限",
      message: "当前环境限制了 .docx 文件大小，过大的文件无法稳定解析。",
      action: "请先压缩图片、删减无关附件，或改用粘贴正文模式。",
    },
    DOCX_INVALID: {
      title: "文件可能已损坏",
      message: "上传内容不是有效的 .docx 文档。",
      action: "请用 Word 或 WPS 重新另存为 .docx 后再上传。",
    },
    PARSE_FAILED: {
      title: "结构识别没有完成",
      message: "文档内容可能包含当前解析器暂不支持的结构。",
      action: "请先尝试粘贴正文；如果仍失败，保留原文后人工拆分章节。",
    },
    FIELD_MISSING: {
      title: "导出信息不完整",
      message: "模板导出需要若干封面字段，当前还有必填字段为空。",
      action: "请补全题目、姓名、学号等基础信息后再导出。",
    },
    PDF_DISABLED: {
      title: "PDF 导出未开启",
      message: "生产环境默认关闭 PDF 编译，以避免线上 TeX 依赖不稳定。",
      action: "请先导出 .tex 工程 zip，再在本地 TeX 环境中编译。",
    },
    EXPORT_FAILED: {
      title: "导出没有完成",
      message: "服务在生成产物时遇到问题。",
      action: "请检查字段内容是否完整，再重新导出 .tex 工程 zip。",
    },
    NETWORK_ERROR: {
      title: "服务暂时不可用",
      message: "前端没有连上后端服务，或请求在网络层失败。",
      action: "请确认本地后端或线上服务可访问后再试。",
    },
  };

  return {
    ...(map[error.code ?? ""] ?? {
      title: "操作没有完成",
      message: error.message || "系统返回了一个暂未归类的问题。",
      action: "请按当前页面提示修正内容后重试。",
    }),
    code: error.code,
  };
}

export function stepIndex(step: WorkspaceStep) {
  return {
    input: 0,
    recognizing: 1,
    review: 2,
    export: 3,
  }[step];
}

export function bodySummary(thesis: NormalizedThesis) {
  return {
    abstractCn: Boolean(thesis.abstract_cn.content),
    abstractEn: Boolean(thesis.abstract_en.content),
    bodyCount: thesis.body_sections.length,
    referencesCount: thesis.references.items.length,
    acknowledgements: Boolean(thesis.acknowledgements),
    appendix: Boolean(thesis.appendix),
  };
}
