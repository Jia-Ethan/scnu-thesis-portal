from __future__ import annotations

from urllib.parse import quote


def attachment_disposition(filename: str, fallback: str = "Forma-export.docx") -> str:
    safe_fallback = "".join(char if char.isascii() and char not in '\r\n";\\' else "-" for char in fallback).strip("-")
    safe_fallback = safe_fallback or "Forma-export.docx"
    return f"attachment; filename=\"{safe_fallback}\"; filename*=UTF-8''{quote(filename, safe='')}"
