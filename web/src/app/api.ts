import type { HealthResponse, NormalizedThesis, PrecheckResponse } from "../generated/contracts";

export type ApiErrorPayload = {
  error_code?: string;
  error_message?: string;
  details?: unknown;
};

export class ApiError extends Error {
  code?: string;
  details?: unknown;

  constructor(message: string, code?: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.details = details;
  }
}

async function readError(response: Response): Promise<ApiError> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return new ApiError(payload.error_message || response.statusText, payload.error_code, payload.details);
  } catch {
    return new ApiError(response.statusText || "请求失败", "NETWORK_ERROR");
  }
}

async function jsonRequest<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(input, init);
  } catch (error) {
    throw new ApiError(error instanceof Error ? error.message : "服务暂时不可用", "NETWORK_ERROR");
  }

  if (!response.ok) {
    throw await readError(response);
  }

  return (await response.json()) as T;
}

async function blobRequest(input: RequestInfo | URL, init?: RequestInit): Promise<Blob> {
  let response: Response;
  try {
    response = await fetch(input, init);
  } catch (error) {
    throw new ApiError(error instanceof Error ? error.message : "服务暂时不可用", "NETWORK_ERROR");
  }

  if (!response.ok) {
    throw await readError(response);
  }

  return response.blob();
}

export function getHealth() {
  return jsonRequest<HealthResponse>("/api/health");
}

export function precheckDocx(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return jsonRequest<PrecheckResponse>("/api/precheck/docx", {
    method: "POST",
    body: formData,
  });
}

export function precheckText(text: string) {
  return jsonRequest<PrecheckResponse>("/api/precheck/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export function exportDocx(thesis: NormalizedThesis) {
  return blobRequest("/api/export/docx", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(thesis),
  });
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

// ─── Story2Paper Integration ─────────────────────────────────────────────────

export interface Story2PaperGenerateResponse {
  paper_id: string;
  status: string;
}

export interface Story2PaperResult {
  paper_id: string;
  outline: Record<string, unknown> | null;
  section_drafts: Array<{
    section_id: string;
    title: string;
    content: string;
  }>;
  contract: Record<string, unknown> | null;
  final_output: string | null;
  status: string;
}

export interface Story2PaperWSEvent {
  event: string;
  current_agent?: string;
  section_index?: number;
  audit_pass?: boolean;
  revision_round?: number;
  final_output?: boolean;
}

const STORY2PAPER_BASE = import.meta.env.VITE_STORY2PAPER_URL ?? "http://localhost:8000";

export async function story2paperGenerate(researchPrompt: string): Promise<Story2PaperGenerateResponse> {
  const response = await fetch(`${STORY2PAPER_BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ research_prompt: researchPrompt }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new ApiError(`Story2Paper 生成失败: ${response.status} ${text}`, "STORY2PAPER_ERROR");
  }
  return response.json() as Promise<Story2PaperGenerateResponse>;
}

export async function story2paperGetResult(paperId: string): Promise<Story2PaperResult> {
  const response = await fetch(`${STORY2PAPER_BASE}/generate/result/${paperId}`);
  if (!response.ok) {
    const text = await response.text();
    throw new ApiError(`获取生成结果失败: ${response.status} ${text}`, "STORY2PAPER_ERROR");
  }
  return response.json() as Promise<Story2PaperResult>;
}

export function story2paperWS(paperId: string): WebSocket {
  const wsUrl = STORY2PAPER_BASE.replace(/^http/, "ws") + `/ws/${paperId}`;
  return new WebSocket(wsUrl);
}

export function precheckFromStory2Paper(schemaData: object, cover: import("../generated/contracts").CoverFields) {
  return jsonRequest<PrecheckResponse>("/api/precheck/from-story2paper", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ schema_data: schemaData, cover }),
  });
}
