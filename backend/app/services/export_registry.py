from __future__ import annotations

import json
from dataclasses import dataclass

from ..contracts import NormalizedThesis
from ..errors import AppError
from .export import export_docx
from .precheck import run_precheck


@dataclass(frozen=True)
class ExportPayload:
    payload: bytes
    media_type: str
    extension: str
    summary: dict


def export_thesis(thesis: NormalizedThesis, export_format: str) -> ExportPayload:
    fmt = export_format.lower().strip()
    if fmt == "docx":
        return ExportPayload(
            payload=export_docx(thesis),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            extension="docx",
            summary={"format": "docx", "source": "sc-th-word"},
        )
    if fmt == "markdown":
        payload = _export_markdown(thesis).encode("utf-8")
        return ExportPayload(
            payload=payload,
            media_type="text/markdown; charset=utf-8",
            extension="md",
            summary={"format": "markdown", "blocks": len(thesis.blocks)},
        )
    if fmt in {"integrity_report", "report"}:
        payload = _export_integrity_report(thesis).encode("utf-8")
        return ExportPayload(
            payload=payload,
            media_type="application/json",
            extension="json",
            summary={"format": "integrity_report", "predicts_similarity": False},
        )
    if fmt == "pdf":
        docx_payload = export_docx(thesis)
        return ExportPayload(
            payload=docx_payload,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            extension="docx",
            summary={"format": "pdf", "status": "conversion_unavailable_docx_retained"},
        )
    raise AppError("UNSUPPORTED_EXPORT_FORMAT", f"暂不支持导出格式：{export_format}", status_code=400)


def _export_markdown(thesis: NormalizedThesis) -> str:
    lines = [f"# {thesis.cover.title.strip() or '未命名论文'}", ""]
    if thesis.abstract_cn.content.strip():
        lines.extend(["## 摘要", thesis.abstract_cn.content.strip(), ""])
    if thesis.abstract_cn.keywords:
        lines.extend([f"关键词：{'，'.join(thesis.abstract_cn.keywords)}", ""])
    if thesis.abstract_en.content.strip():
        lines.extend(["## Abstract", thesis.abstract_en.content.strip(), ""])
    for section in thesis.body_sections:
        level = min(max(section.level, 1), 4) + 1
        lines.extend([f"{'#' * level} {section.title.strip() or '正文'}", section.content.strip(), ""])
    if thesis.references:
        lines.append("## 参考文献")
        for index, item in enumerate(thesis.references, start=1):
            lines.append(f"[{index}] {item.normalized_text or item.raw_text}")
        lines.append("")
    if thesis.acknowledgements.strip():
        lines.extend(["## 致谢", thesis.acknowledgements.strip(), ""])
    return "\n".join(lines).rstrip() + "\n"


def _export_integrity_report(thesis: NormalizedThesis) -> str:
    precheck = run_precheck(thesis)
    payload = {
        "schema_version": thesis.schema_version,
        "revision_id": thesis.revision_id,
        "title": thesis.cover.title,
        "structure_risks": [item.model_dump() for item in precheck.issues if item.block in {"body", "cover"}],
        "citation_risks": [item.model_dump() for item in precheck.issues if item.block == "references"],
        "format_risks": [risk.model_dump() for risk in thesis.format_risks],
        "ai_assistance_notice": "报告只提示 AI 辅助痕迹与人工确认边界，不预测查重率。",
        "predicts_similarity": False,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
