from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from ..contracts import CapabilityFlags, NormalizedThesis, SourceSpan
from ..services.parse import normalize_reference_text, normalize_text_input, parse_docx_file


@dataclass
class SourceBlock:
    id: str
    kind: str
    text: str
    span: SourceSpan
    confidence: float = 0.75


@dataclass
class ParsedSource:
    parser: str
    thesis: NormalizedThesis
    blocks: list[SourceBlock] = field(default_factory=list)
    ledger: dict = field(default_factory=dict)


def _text_blocks(text: str, *, file_id: str | None, method: str) -> list[SourceBlock]:
    blocks: list[SourceBlock] = []
    for index, line in enumerate(text.splitlines()):
        if not line.strip():
            continue
        blocks.append(
            SourceBlock(
                id=f"source-block-{index + 1}",
                kind="text",
                text=line.strip(),
                span=SourceSpan(file_id=file_id, paragraph_index=index, block_index=index, extraction_method=method),
            )
        )
    return blocks


def parse_payload(
    payload: bytes,
    *,
    filename: str,
    file_type: str,
    file_id: str | None = None,
    capabilities: CapabilityFlags | None = None,
) -> ParsedSource:
    capabilities = capabilities or CapabilityFlags()
    suffix = Path(filename).suffix.lower()
    normalized_type = (file_type or "").lower()

    if suffix == ".docx" or normalized_type in {"docx", "comment", "task", "proposal"}:
        with tempfile.TemporaryDirectory(prefix="scnu-workbench-docx-") as tmp:
            path = Path(tmp) / "input.docx"
            path.write_bytes(payload)
            thesis = parse_docx_file(path, capabilities)
        text = "\n".join(section.content for section in thesis.body_sections)
        return ParsedSource(
            parser="docx",
            thesis=thesis,
            blocks=_text_blocks(text, file_id=file_id, method="docx"),
            ledger={"input": filename, "parser": "docx", "source": "user_upload"},
        )

    if suffix == ".pdf" or normalized_type == "pdf":
        extracted = _parse_pdf_text(payload)
        thesis = normalize_text_input(extracted, capabilities)
        thesis.source_type = "pdf"
        return ParsedSource(
            parser="pdf-local",
            thesis=thesis,
            blocks=_text_blocks(extracted, file_id=file_id, method="pdf-local"),
            ledger={"input": filename, "parser": "pdf-local", "source": "user_upload", "ocr": False},
        )

    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"} or normalized_type in {"image", "ocr"}:
        text = "图片/OCR 文件已进入 source ledger，等待 OCR Provider 或人工校对后写入论文结构。"
        thesis = normalize_text_input(f"# OCR 待确认\n\n{text}", capabilities)
        thesis.source_type = "image"
        return ParsedSource(
            parser="image-ocr-placeholder",
            thesis=thesis,
            blocks=_text_blocks(text, file_id=file_id, method="ocr-placeholder"),
            ledger={"input": filename, "parser": "image-ocr-placeholder", "source": "user_upload", "ocr": True},
        )

    if suffix in {".bib", ".ris", ".txt"} or normalized_type == "reference":
        text = payload.decode("utf-8", errors="ignore")
        refs = []
        for line in text.splitlines():
            if not line.strip():
                continue
            raw, normalized = normalize_reference_text(line)
            refs.append(normalized or raw)
        body = "# 参考文献候选\n\n" + "\n".join(refs or ["参考文献文件已上传，未识别到可用条目。"])
        thesis = normalize_text_input(body, capabilities)
        thesis.source_type = "reference"
        return ParsedSource(
            parser="reference-local",
            thesis=thesis,
            blocks=_text_blocks("\n".join(refs), file_id=file_id, method="reference-local"),
            ledger={"input": filename, "parser": "reference-local", "source": "user_upload", "fabricated_metadata": False},
        )

    text = payload.decode("utf-8", errors="ignore")
    thesis = normalize_text_input(text, capabilities)
    return ParsedSource(
        parser="text",
        thesis=thesis,
        blocks=_text_blocks(text, file_id=file_id, method="text"),
        ledger={"input": filename, "parser": "text", "source": "user_upload"},
    )


def _parse_pdf_text(payload: bytes) -> str:
    # MVP parser: keep PDF local and extract visible literal strings where possible.
    # Full layout/OCR is intentionally behind the parser registry seam.
    decoded = payload.decode("latin-1", errors="ignore")
    strings = re.findall(r"\(([^()]{4,})\)", decoded)
    text = "\n".join(item.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore") for item in strings)
    if len(text.strip()) < 20:
        text = "# PDF 待确认\n\nPDF 已进入 source ledger。当前 MVP 仅提供结构级定位，复杂版面需人工复核。"
    return text
