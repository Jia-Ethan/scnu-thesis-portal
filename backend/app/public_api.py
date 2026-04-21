from __future__ import annotations

import json
import logging
import tempfile
import threading
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from .config import (
    ALLOWED_DOCX_CONTENT_TYPES,
    ALLOWED_DOCX_EXTENSIONS,
    MAX_TEXT_PRECHECK_CHARS,
    MAX_UPLOAD_SIZE_BYTES,
    PUBLIC_EXPORT_RATE_LIMIT_PER_HOUR,
    PUBLIC_EXPORT_RETENTION_SECONDS,
    turnstile_required,
    turnstile_secret_key,
)
from .contracts import CapabilityFlags, NormalizedThesis, PrecheckResponse
from .errors import AppError
from .security import export_token_for_digest, secret_key, thesis_digest, verify_export_token
from .services.export import export_docx
from .services.parse import normalize_text_input, parse_docx_file
from .services.precheck import run_precheck
from .storage import storage

logger = logging.getLogger("scnu-thesis-portal.public")
router = APIRouter(prefix="/api/public", tags=["public-export"])

_rate_windows: dict[tuple[str, int], int] = defaultdict(int)


class PublicTextPrecheckRequest(BaseModel):
    text: str
    privacy_accepted: bool = False
    turnstile_token: str = ""


class PublicExportDocxRequest(BaseModel):
    thesis: NormalizedThesis
    export_token: str


class PublicExportResponse(BaseModel):
    export_id: str
    download_url: str
    report_url: str
    expires_at: datetime


PublicExportJobStatus = Literal["running", "done", "failed", "canceled"]


class PublicExportJobResponse(BaseModel):
    job_id: str
    export_id: str
    status: PublicExportJobStatus
    progress: int = 0
    message: str = ""
    download_url: str | None = None
    report_url: str | None = None
    expires_at: datetime
    error_code: str | None = None


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def ip_hash(request: Request) -> str:
    return thesis_digest(f"ip:{client_ip(request)}:{secret_key()}")[:24]


def require_privacy(accepted: bool) -> None:
    if not accepted:
        raise AppError("PRIVACY_CONFIRMATION_REQUIRED", "请先确认隐私说明后再继续。", status_code=400)


def enforce_rate_limit(request: Request) -> str:
    hashed = ip_hash(request)
    window = int(time.time() // 3600)
    key = (hashed, window)
    _rate_windows[key] += 1
    for old_key in list(_rate_windows):
        if old_key[1] < window - 1:
            _rate_windows.pop(old_key, None)
    if _rate_windows[key] > PUBLIC_EXPORT_RATE_LIMIT_PER_HOUR:
        raise AppError("RATE_LIMITED", "当前 IP 的公开导出请求过于频繁，请稍后再试。", status_code=429)
    return hashed


def verify_turnstile_or_raise(token: str, request: Request) -> None:
    if not turnstile_required():
        return
    secret = turnstile_secret_key()
    if not secret or not token:
        raise AppError("TURNSTILE_REQUIRED", "请完成人机验证后再提交。", status_code=400)
    payload = json.dumps({"secret": secret, "response": token, "remoteip": client_ip(request)}).encode("utf-8")
    siteverify = UrlRequest(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(siteverify, timeout=4) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise AppError("TURNSTILE_UNAVAILABLE", "人机验证服务暂时不可用，请稍后再试。", status_code=503) from exc
    if not result.get("success"):
        raise AppError("TURNSTILE_INVALID", "人机验证未通过，请刷新后重试。", status_code=400, details={"error_codes": result.get("error-codes", [])})


def attach_public_export_token(response: PrecheckResponse) -> PrecheckResponse:
    expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=PUBLIC_EXPORT_RETENTION_SECONDS)
    digest = thesis_digest(response.thesis.model_dump_json())
    response.export_token = export_token_for_digest(digest, int(expires_at.replace(tzinfo=UTC).timestamp()))
    response.expires_at = expires_at
    return response


def log_public_request(*, request: Request, size: int, status_code: int, error_code: str = "", elapsed_ms: int = 0) -> None:
    logger.info(
        "public_export_event ip_hash=%s file_size=%s status_code=%s error_code=%s elapsed_ms=%s",
        ip_hash(request),
        size,
        status_code,
        error_code,
        elapsed_ms,
    )


@router.post("/precheck/docx", response_model=PrecheckResponse)
async def public_precheck_docx(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    privacy_accepted: Annotated[bool, Form()] = False,
    turnstile_token: Annotated[str, Form()] = "",
) -> PrecheckResponse:
    started = time.perf_counter()
    require_privacy(privacy_accepted)
    verify_turnstile_or_raise(turnstile_token, request)
    enforce_rate_limit(request)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_DOCX_EXTENSIONS:
        raise AppError("UNSUPPORTED_FILE_TYPE", "请上传 .docx 文件，暂不支持 .doc 或其他格式。", status_code=400)
    if (file.content_type or "") not in ALLOWED_DOCX_CONTENT_TYPES:
        raise AppError("UNSUPPORTED_FILE_TYPE", "文件类型不符合 .docx，请重新选择 Word 文档。", status_code=400)
    payload = await file.read()
    if not payload:
        raise AppError("CONTENT_EMPTY", "上传文件为空，请选择包含论文内容的 .docx 文件。", status_code=400)
    if len(payload) > MAX_UPLOAD_SIZE_BYTES:
        raise AppError("FILE_TOO_LARGE", "文件超过当前上传大小限制，请压缩或删减后再试。", status_code=400)
    if not payload.startswith(b"PK"):
        raise AppError("DOCX_INVALID", "上传文件不是有效的 .docx 文档，请确认文件未损坏。", status_code=400)
    with tempfile.TemporaryDirectory(prefix="scnu-public-docx-") as tmp:
        upload_path = Path(tmp) / "input.docx"
        upload_path.write_bytes(payload)
        response = attach_public_export_token(run_precheck(parse_docx_file(upload_path, CapabilityFlags())))
        log_public_request(request=request, size=len(payload), status_code=200, elapsed_ms=int((time.perf_counter() - started) * 1000))
        return response


@router.post("/precheck/text", response_model=PrecheckResponse)
def public_precheck_text(request: PublicTextPrecheckRequest, raw_request: Request) -> PrecheckResponse:
    require_privacy(request.privacy_accepted)
    verify_turnstile_or_raise(request.turnstile_token, raw_request)
    enforce_rate_limit(raw_request)
    text = request.text.strip()
    if not text:
        raise AppError("CONTENT_EMPTY", "粘贴内容为空，请先输入已有论文正文或章节内容。", status_code=400)
    if len(text) > MAX_TEXT_PRECHECK_CHARS:
        raise AppError("TEXT_TOO_LONG", "粘贴正文超过当前长度限制，请改为上传 .docx。", status_code=400)
    return attach_public_export_token(run_precheck(normalize_text_input(text, CapabilityFlags())))


@router.post("/exports/docx", response_model=PublicExportResponse)
def public_export_docx(request: PublicExportDocxRequest) -> PublicExportResponse:
    digest = thesis_digest(request.thesis.model_dump_json())
    if not verify_export_token(request.export_token, digest):
        raise AppError("EXPORT_TOKEN_INVALID", "导出凭证已失效，请重新预检后再导出。", status_code=403)
    payload = export_docx(request.thesis)
    expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=PUBLIC_EXPORT_RETENTION_SECONDS)
    export_id = f"pub_{uuid.uuid4().hex[:16]}"
    safe_title = (request.thesis.cover.title.strip() or "SC-TH-export").replace("/", "-")[:40]
    filename = f"{safe_title}.docx"
    docx_key = f"public/exports/{export_id}/{filename}"
    report_key = f"public/exports/{export_id}/self-check-report.json"
    storage.put_bytes(docx_key, payload)
    storage.put_bytes(report_key, _public_report_payload(export_id, request.thesis, expires_at))
    _write_meta(export_id, {"expires_at": expires_at.isoformat(), "docx_key": docx_key, "report_key": report_key, "filename": filename})
    return PublicExportResponse(
        export_id=export_id,
        download_url=f"/api/public/exports/{export_id}/download",
        report_url=f"/api/public/exports/{export_id}/report",
        expires_at=expires_at,
    )


@router.post("/export-jobs/docx", response_model=PublicExportJobResponse)
def create_public_export_job(request: PublicExportDocxRequest) -> PublicExportJobResponse:
    digest = thesis_digest(request.thesis.model_dump_json())
    if not verify_export_token(request.export_token, digest):
        raise AppError("EXPORT_TOKEN_INVALID", "导出凭证已失效，请重新预检后再导出。", status_code=403)

    expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=PUBLIC_EXPORT_RETENTION_SECONDS)
    job_id = f"job_{uuid.uuid4().hex[:16]}"
    export_id = f"pub_{uuid.uuid4().hex[:16]}"
    request_payload = {
        "thesis": request.thesis.model_dump(mode="json"),
        "export_token": request.export_token,
    }
    storage.put_bytes(_job_request_key(job_id), json.dumps(request_payload, ensure_ascii=False).encode("utf-8"))
    _write_job_meta(
        job_id,
        {
            "job_id": job_id,
            "export_id": export_id,
            "status": "running",
            "progress": 5,
            "message": "导出任务已创建。",
            "download_url": None,
            "report_url": None,
            "expires_at": expires_at.isoformat(),
            "error_code": None,
            "cancel_requested": False,
        },
    )
    thread = threading.Thread(target=_run_public_export_job, args=(job_id,), daemon=True)
    thread.start()
    return _public_job_response(_read_job_meta(job_id))


@router.get("/export-jobs/{job_id}", response_model=PublicExportJobResponse)
def get_public_export_job(job_id: str) -> PublicExportJobResponse:
    return _public_job_response(_read_job_meta(job_id))


@router.post("/export-jobs/{job_id}/cancel", response_model=PublicExportJobResponse)
def cancel_public_export_job(job_id: str) -> PublicExportJobResponse:
    meta = _read_job_meta(job_id)
    if meta["status"] in {"done", "failed", "canceled"}:
        return _public_job_response(meta)
    meta["cancel_requested"] = True
    meta["status"] = "canceled"
    meta["message"] = "导出已取消，可重新导出。"
    meta["error_code"] = "EXPORT_CANCELED"
    _write_job_meta(job_id, meta)
    return _public_job_response(meta)


@router.post("/export-jobs/{job_id}/retry", response_model=PublicExportJobResponse)
def retry_public_export_job(job_id: str) -> PublicExportJobResponse:
    meta = _read_job_meta(job_id)
    if meta["status"] not in {"failed", "canceled"}:
        raise AppError("EXPORT_JOB_NOT_RETRYABLE", "当前导出任务尚未进入可重试状态。", status_code=409)
    payload = json.loads(storage.get_bytes(_job_request_key(job_id)).decode("utf-8"))
    thesis = NormalizedThesis.model_validate(payload["thesis"])
    digest = thesis_digest(thesis.model_dump_json())
    if not verify_export_token(payload["export_token"], digest):
        raise AppError("EXPORT_TOKEN_INVALID", "导出凭证已失效，请重新预检后再导出。", status_code=403)
    meta.update(
        {
            "status": "running",
            "progress": 5,
            "message": "正在重新导出。",
            "download_url": None,
            "report_url": None,
            "error_code": None,
            "cancel_requested": False,
        }
    )
    _write_job_meta(job_id, meta)
    thread = threading.Thread(target=_run_public_export_job, args=(job_id,), daemon=True)
    thread.start()
    return _public_job_response(meta)


@router.get("/exports/{export_id}/download")
def download_public_export(export_id: str) -> Response:
    meta = _read_valid_meta(export_id)
    payload = storage.get_bytes(meta["docx_key"])
    return Response(content=payload, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f'attachment; filename="{meta["filename"]}"'})


@router.get("/exports/{export_id}/report")
def download_public_report(export_id: str) -> Response:
    meta = _read_valid_meta(export_id)
    return Response(content=storage.get_bytes(meta["report_key"]), media_type="application/json; charset=utf-8")


def _public_report_payload(export_id: str, thesis: NormalizedThesis, expires_at: datetime) -> bytes:
    return json.dumps(
        {
            "export_id": export_id,
            "expires_at": expires_at.isoformat(),
            "source_type": thesis.source_type,
            "manual_review_flags": thesis.manual_review_flags,
            "missing_sections": thesis.missing_sections,
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")


def _meta_key(export_id: str) -> str:
    return f"public/exports/{export_id}/meta.json"


def _write_meta(export_id: str, meta: dict) -> None:
    storage.put_bytes(_meta_key(export_id), json.dumps(meta, ensure_ascii=False).encode("utf-8"))


def _read_valid_meta(export_id: str) -> dict:
    try:
        meta = json.loads(storage.get_bytes(_meta_key(export_id)).decode("utf-8"))
    except FileNotFoundError as exc:
        raise AppError("EXPORT_NOT_FOUND", "导出文件不存在或已删除。", status_code=404) from exc
    expires_at = datetime.fromisoformat(meta["expires_at"])
    if expires_at < datetime.now(UTC).replace(tzinfo=None):
        storage.delete_prefix(f"public/exports/{export_id}")
        raise AppError("EXPORT_EXPIRED", "导出文件已超过 30 分钟保留期，请重新生成。", status_code=410)
    return meta


def _job_meta_key(job_id: str) -> str:
    return f"public/export-jobs/{job_id}/meta.json"


def _job_request_key(job_id: str) -> str:
    return f"public/export-jobs/{job_id}/request.json"


def _write_job_meta(job_id: str, meta: dict) -> None:
    storage.put_bytes(_job_meta_key(job_id), json.dumps(meta, ensure_ascii=False).encode("utf-8"))


def _read_job_meta(job_id: str) -> dict:
    try:
        meta = json.loads(storage.get_bytes(_job_meta_key(job_id)).decode("utf-8"))
    except FileNotFoundError as exc:
        raise AppError("EXPORT_JOB_NOT_FOUND", "导出任务不存在或已删除。", status_code=404) from exc
    expires_at = datetime.fromisoformat(meta["expires_at"])
    if expires_at < datetime.now(UTC).replace(tzinfo=None):
        storage.delete_prefix(f"public/export-jobs/{job_id}")
        if meta.get("export_id"):
            storage.delete_prefix(f"public/exports/{meta['export_id']}")
        raise AppError("EXPORT_EXPIRED", "导出任务已超过 30 分钟保留期，请重新生成。", status_code=410)
    return meta


def _public_job_response(meta: dict) -> PublicExportJobResponse:
    return PublicExportJobResponse(
        job_id=meta["job_id"],
        export_id=meta["export_id"],
        status=meta["status"],
        progress=max(0, min(100, int(meta.get("progress", 0)))),
        message=meta.get("message", ""),
        download_url=meta.get("download_url"),
        report_url=meta.get("report_url"),
        expires_at=datetime.fromisoformat(meta["expires_at"]),
        error_code=meta.get("error_code"),
    )


def _job_cancel_requested(job_id: str) -> bool:
    try:
        meta = _read_job_meta(job_id)
    except AppError:
        return True
    return bool(meta.get("cancel_requested")) or meta.get("status") == "canceled"


def _update_job(job_id: str, **patch: object) -> dict:
    meta = _read_job_meta(job_id)
    if meta.get("status") in {"done", "failed", "canceled"} and patch.get("status") not in {meta.get("status"), None}:
        return meta
    meta.update(patch)
    _write_job_meta(job_id, meta)
    return meta


def _run_public_export_job(job_id: str) -> None:
    try:
        if _job_cancel_requested(job_id):
            return
        _update_job(job_id, progress=18, message="正在准备导出参数。")
        payload = json.loads(storage.get_bytes(_job_request_key(job_id)).decode("utf-8"))
        thesis = NormalizedThesis.model_validate(payload["thesis"])
        digest = thesis_digest(thesis.model_dump_json())
        if not verify_export_token(payload["export_token"], digest):
            _update_job(
                job_id,
                status="failed",
                progress=100,
                message="导出凭证已失效，请重新预检后再导出。",
                error_code="EXPORT_TOKEN_INVALID",
            )
            return
        if _job_cancel_requested(job_id):
            return
        _update_job(job_id, progress=46, message="正在生成 Word 文件。")
        payload_bytes = export_docx(thesis)
        if _job_cancel_requested(job_id):
            return
        _update_job(job_id, progress=82, message="正在保存导出文件。")
        meta = _read_job_meta(job_id)
        expires_at = datetime.fromisoformat(meta["expires_at"])
        export_id = meta["export_id"]
        safe_title = (thesis.cover.title.strip() or "SC-TH-export").replace("/", "-")[:40]
        filename = f"{safe_title}.docx"
        docx_key = f"public/exports/{export_id}/{filename}"
        report_key = f"public/exports/{export_id}/self-check-report.json"
        storage.put_bytes(docx_key, payload_bytes)
        storage.put_bytes(report_key, _public_report_payload(export_id, thesis, expires_at))
        _write_meta(export_id, {"expires_at": expires_at.isoformat(), "docx_key": docx_key, "report_key": report_key, "filename": filename})
        if _job_cancel_requested(job_id):
            storage.delete_prefix(f"public/exports/{export_id}")
            return
        _update_job(
            job_id,
            status="done",
            progress=100,
            message="导出完成。",
            download_url=f"/api/public/exports/{export_id}/download",
            report_url=f"/api/public/exports/{export_id}/report",
            error_code=None,
        )
    except AppError as exc:
        try:
            _update_job(job_id, status="failed", progress=100, message=exc.message, error_code=exc.code)
        except AppError:
            return
    except Exception:
        logger.exception("public export job failed job_id=%s", job_id)
        try:
            _update_job(job_id, status="failed", progress=100, message="导出失败，请稍后重试。", error_code="EXPORT_FAILED")
        except AppError:
            return
