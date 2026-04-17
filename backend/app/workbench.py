from __future__ import annotations

import base64
import hashlib
import ipaddress
import json
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .contracts import CapabilityFlags, NormalizedThesis
from .database import get_db
from .errors import AppError
from .models import (
    AgentEvent,
    AgentRun,
    Approval,
    AuditLog,
    ExportRecord,
    Issue,
    NormalizedBlockRecord,
    ProjectFile,
    Proposal,
    ProviderConfig,
    SourceDocument,
    ThesisProject,
    ThesisVersion,
)
from .parsers import parse_payload
from .services.export_registry import export_thesis
from .services.precheck import run_precheck
from .storage import storage

router = APIRouter(prefix="/api", tags=["workbench"])


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


class ProjectCreateRequest(BaseModel):
    title: str = "未命名论文项目"


class ProjectResponse(BaseModel):
    id: str
    title: str
    status: str
    current_version_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ProjectFileResponse(BaseModel):
    id: str
    project_id: str
    type: str
    filename: str
    content_type: str
    size: int
    sha256: str
    storage_key: str
    parser: str
    source_label: str
    created_at: datetime


class ParseJobRequest(BaseModel):
    file_id: str


class JobResponse(BaseModel):
    id: str
    project_id: str | None = None
    kind: str
    status: str
    current_agent: str | None = None
    result: dict = Field(default_factory=dict)


class VersionResponse(BaseModel):
    id: str
    project_id: str
    parent_version_id: str | None = None
    label: str
    thesis: dict
    created_by: str
    created_at: datetime


class ProposalResponse(BaseModel):
    id: str
    project_id: str
    version_id: str | None
    target_block_id: str | None
    operation: str
    before: str
    after: str
    reason: str
    risk: str
    source_refs: list
    affects_export: bool
    status: str
    created_at: datetime


class ExportCreateRequest(BaseModel):
    version_id: str | None = None
    format: str = "docx"


class ExportResponse(BaseModel):
    id: str
    project_id: str
    version_id: str
    format: str
    status: str
    storage_key: str | None
    filename: str
    summary: dict
    created_at: datetime


class ProviderConfigRequest(BaseModel):
    provider: str
    model: str = ""
    base_url: str | None = None
    api_key: str = ""
    allow_local: bool = False


class SourceSearchRequest(BaseModel):
    query: str


class SourceConfirmRequest(BaseModel):
    source_id: str
    title: str
    url: str
    summary: str = ""


def project_to_response(project: ThesisProject) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        title=project.title,
        status=project.status,
        current_version_id=project.current_version_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def require_project(db: Session, project_id: str) -> ThesisProject:
    project = db.get(ThesisProject, project_id)
    if not project or project.deleted_at is not None or project.status == "deleted":
        raise AppError("PROJECT_NOT_FOUND", "项目不存在或已删除。", status_code=404)
    return project


def latest_version(db: Session, project: ThesisProject) -> ThesisVersion:
    if project.current_version_id:
        version = db.get(ThesisVersion, project.current_version_id)
        if version:
            return version
    version = db.execute(
        select(ThesisVersion).where(ThesisVersion.project_id == project.id).order_by(ThesisVersion.created_at.desc())
    ).scalars().first()
    if not version:
        raise AppError("VERSION_NOT_FOUND", "项目尚未生成论文版本。", status_code=404)
    return version


@router.post("/projects", response_model=ProjectResponse)
def create_project(request: ProjectCreateRequest, db: Session = Depends(get_db)) -> ProjectResponse:
    project = ThesisProject(id=new_id("proj"), title=request.title.strip() or "未命名论文项目")
    db.add(project)
    db.add(AuditLog(id=new_id("audit"), project_id=project.id, action="project.created", target_type="project", target_id=project.id))
    db.commit()
    db.refresh(project)
    return project_to_response(project)


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)) -> list[ProjectResponse]:
    rows = db.execute(
        select(ThesisProject).where(ThesisProject.deleted_at.is_(None), ThesisProject.status != "deleted").order_by(ThesisProject.created_at.desc())
    ).scalars().all()
    return [project_to_response(row) for row in rows]


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)) -> ProjectResponse:
    return project_to_response(require_project(db, project_id))


@router.delete("/projects/{project_id}", response_model=ProjectResponse)
def delete_project(project_id: str, db: Session = Depends(get_db)) -> ProjectResponse:
    project = require_project(db, project_id)
    project.status = "deleted"
    project.deleted_at = datetime.now(UTC).replace(tzinfo=None)
    storage.delete_prefix(f"projects/{project.id}")
    db.add(AuditLog(id=new_id("audit"), project_id=project.id, action="project.deleted", target_type="project", target_id=project.id))
    db.commit()
    db.refresh(project)
    return project_to_response(project)


@router.post("/projects/{project_id}/files", response_model=ProjectFileResponse)
async def upload_project_file(
    project_id: str,
    file: UploadFile = File(...),
    file_type: str = Form("docx"),
    source_label: str = Form(""),
    db: Session = Depends(get_db),
) -> ProjectFileResponse:
    require_project(db, project_id)
    payload = await file.read()
    if not payload:
        raise AppError("CONTENT_EMPTY", "上传文件为空。", status_code=400)
    digest = hashlib.sha256(payload).hexdigest()
    existing = db.execute(
        select(ProjectFile).where(ProjectFile.project_id == project_id, ProjectFile.sha256 == digest, ProjectFile.deleted_at.is_(None))
    ).scalars().first()
    if existing:
        return ProjectFileResponse.model_validate(existing, from_attributes=True)
    filename = Path(file.filename or "upload.bin").name
    storage_key = f"projects/{project_id}/files/{digest}/{filename}"
    stored = storage.put_bytes(storage_key, payload)
    row = ProjectFile(
        id=new_id("file"),
        project_id=project_id,
        type=file_type,
        filename=filename,
        content_type=file.content_type or "",
        size=stored.size,
        sha256=stored.sha256,
        storage_key=stored.key,
        parser="registry",
        source_label=source_label,
    )
    db.add(row)
    db.add(AuditLog(id=new_id("audit"), project_id=project_id, action="file.uploaded", target_type="project_file", target_id=row.id))
    db.commit()
    db.refresh(row)
    return ProjectFileResponse.model_validate(row, from_attributes=True)


@router.get("/projects/{project_id}/files", response_model=list[ProjectFileResponse])
def list_project_files(project_id: str, db: Session = Depends(get_db)) -> list[ProjectFileResponse]:
    require_project(db, project_id)
    rows = db.execute(
        select(ProjectFile).where(ProjectFile.project_id == project_id, ProjectFile.deleted_at.is_(None)).order_by(ProjectFile.created_at.desc())
    ).scalars().all()
    return [ProjectFileResponse.model_validate(row, from_attributes=True) for row in rows]


@router.post("/projects/{project_id}/parse-jobs", response_model=JobResponse)
def create_parse_job(project_id: str, request: ParseJobRequest, db: Session = Depends(get_db)) -> JobResponse:
    project = require_project(db, project_id)
    file_row = db.get(ProjectFile, request.file_id)
    if not file_row or file_row.project_id != project_id or file_row.deleted_at is not None:
        raise AppError("FILE_NOT_FOUND", "文件不存在或已删除。", status_code=404)

    run = AgentRun(id=new_id("job"), project_id=project_id, kind="parse", status="running", current_agent="Intake Parser")
    db.add(run)
    db.flush()
    db.add(AgentEvent(id=new_id("evt"), run_id=run.id, project_id=project_id, type="run_started", payload={"stage": "parse"}))

    try:
        payload = storage.get_bytes(file_row.storage_key)
        parsed = parse_payload(payload, filename=file_row.filename, file_type=file_row.type, file_id=file_row.id, capabilities=CapabilityFlags())
        source = SourceDocument(
            id=new_id("src"),
            project_id=project_id,
            file_id=file_row.id,
            kind=file_row.type,
            title=file_row.filename,
            ledger=parsed.ledger,
            confirmed=False,
        )
        db.add(source)
        thesis = parsed.thesis
        thesis.revision_id = new_id("rev")
        version = ThesisVersion(
            id=new_id("ver"),
            project_id=project_id,
            parent_version_id=project.current_version_id,
            label="baseline",
            thesis=thesis.model_dump(mode="json"),
            created_by="parser",
        )
        db.add(version)
        db.flush()
        _persist_blocks(db, project_id, version.id, thesis)
        precheck = run_precheck(thesis)
        for item in precheck.issues:
            db.add(
                Issue(
                    id=new_id("issue"),
                    project_id=project_id,
                    version_id=version.id,
                    code=item.code,
                    severity=item.severity,
                    block=item.block,
                    block_id=item.block_id,
                    title=item.title,
                    message=item.message,
                    source_span=item.source_span.model_dump(mode="json") if item.source_span else None,
                    rule_source_id=item.rule_source_id,
                    suggested_action=item.suggested_action,
                )
            )
        _create_rule_agent_proposals(db, project_id, version.id, thesis)
        project.current_version_id = version.id
        run.status = "completed"
        run.current_agent = None
        run.result = {"version_id": version.id, "source_document_id": source.id, "issue_count": len(precheck.issues)}
        db.add(AgentEvent(id=new_id("evt"), run_id=run.id, project_id=project_id, type="run_completed", payload=run.result))
    except Exception as exc:
        run.status = "failed"
        run.result = {"error": str(exc)}
        db.add(AgentEvent(id=new_id("evt"), run_id=run.id, project_id=project_id, type="run_failed", payload=run.result))
    db.commit()
    db.refresh(run)
    if run.status == "failed":
        raise AppError("PARSE_FAILED", "解析任务失败。", details=run.result, status_code=400)
    return JobResponse.model_validate(run, from_attributes=True)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobResponse:
    run = db.get(AgentRun, job_id)
    if not run:
        raise AppError("JOB_NOT_FOUND", "任务不存在。", status_code=404)
    return JobResponse.model_validate(run, from_attributes=True)


@router.get("/jobs/{job_id}/events")
def get_job_events(job_id: str, db: Session = Depends(get_db)) -> list[dict]:
    run = db.get(AgentRun, job_id)
    if not run:
        raise AppError("JOB_NOT_FOUND", "任务不存在。", status_code=404)
    events = db.execute(select(AgentEvent).where(AgentEvent.run_id == job_id).order_by(AgentEvent.created_at.asc())).scalars().all()
    return [{"id": event.id, "type": event.type, "payload": event.payload, "created_at": event.created_at.isoformat()} for event in events]


@router.get("/jobs/{job_id}/events/stream")
def stream_job_events(job_id: str, db: Session = Depends(get_db)) -> StreamingResponse:
    run = db.get(AgentRun, job_id)
    if not run:
        raise AppError("JOB_NOT_FOUND", "任务不存在。", status_code=404)
    events = db.execute(select(AgentEvent).where(AgentEvent.run_id == job_id).order_by(AgentEvent.created_at.asc())).scalars().all()

    def iter_events():
        for event in events:
            payload = {"id": event.id, "type": event.type, "payload": event.payload, "created_at": event.created_at.isoformat()}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(iter_events(), media_type="text/event-stream")


@router.get("/projects/{project_id}/versions", response_model=list[VersionResponse])
def list_versions(project_id: str, db: Session = Depends(get_db)) -> list[VersionResponse]:
    require_project(db, project_id)
    rows = db.execute(select(ThesisVersion).where(ThesisVersion.project_id == project_id).order_by(ThesisVersion.created_at.desc())).scalars().all()
    return [VersionResponse.model_validate(row, from_attributes=True) for row in rows]


@router.get("/projects/{project_id}/versions/{version_id}", response_model=VersionResponse)
def get_version(project_id: str, version_id: str, db: Session = Depends(get_db)) -> VersionResponse:
    require_project(db, project_id)
    version = db.get(ThesisVersion, version_id)
    if not version or version.project_id != project_id:
        raise AppError("VERSION_NOT_FOUND", "版本不存在。", status_code=404)
    return VersionResponse.model_validate(version, from_attributes=True)


@router.get("/projects/{project_id}/issues")
def list_issues(project_id: str, db: Session = Depends(get_db)) -> list[dict]:
    require_project(db, project_id)
    rows = db.execute(select(Issue).where(Issue.project_id == project_id).order_by(Issue.created_at.desc())).scalars().all()
    return [_row_public(row) for row in rows]


@router.get("/projects/{project_id}/proposals", response_model=list[ProposalResponse])
def list_proposals(project_id: str, db: Session = Depends(get_db)) -> list[ProposalResponse]:
    require_project(db, project_id)
    rows = db.execute(select(Proposal).where(Proposal.project_id == project_id).order_by(Proposal.created_at.desc())).scalars().all()
    return [ProposalResponse.model_validate(row, from_attributes=True) for row in rows]


@router.post("/proposals/{proposal_id}/accept")
def accept_proposal(proposal_id: str, db: Session = Depends(get_db)) -> dict:
    return _decide_proposal(db, proposal_id, "accepted")


@router.post("/proposals/{proposal_id}/reject")
def reject_proposal(proposal_id: str, db: Session = Depends(get_db)) -> dict:
    return _decide_proposal(db, proposal_id, "rejected")


@router.post("/proposals/{proposal_id}/stash")
def stash_proposal(proposal_id: str, db: Session = Depends(get_db)) -> dict:
    return _decide_proposal(db, proposal_id, "stashed")


@router.post("/projects/{project_id}/exports", response_model=ExportResponse)
def create_export(project_id: str, request: ExportCreateRequest, db: Session = Depends(get_db)) -> ExportResponse:
    project = require_project(db, project_id)
    version = db.get(ThesisVersion, request.version_id) if request.version_id else latest_version(db, project)
    if not version or version.project_id != project_id:
        raise AppError("VERSION_NOT_FOUND", "版本不存在。", status_code=404)
    thesis = NormalizedThesis.model_validate(version.thesis)
    exported = export_thesis(thesis, request.format)
    export_id = new_id("exp")
    safe_title = thesis.cover.title.strip() or "SC-TH-export"
    filename = f"{safe_title[:40]}.{exported.extension}"
    storage_key = f"projects/{project_id}/exports/{export_id}/{filename}"
    storage.put_bytes(storage_key, exported.payload)
    row = ExportRecord(
        id=export_id,
        project_id=project_id,
        version_id=version.id,
        format=request.format,
        status="completed",
        storage_key=storage_key,
        filename=filename,
        summary=exported.summary,
    )
    db.add(row)
    db.add(AuditLog(id=new_id("audit"), project_id=project_id, action="export.created", target_type="export", target_id=row.id))
    db.commit()
    db.refresh(row)
    return ExportResponse.model_validate(row, from_attributes=True)


@router.get("/projects/{project_id}/exports", response_model=list[ExportResponse])
def list_exports(project_id: str, db: Session = Depends(get_db)) -> list[ExportResponse]:
    require_project(db, project_id)
    rows = db.execute(select(ExportRecord).where(ExportRecord.project_id == project_id).order_by(ExportRecord.created_at.desc())).scalars().all()
    return [ExportResponse.model_validate(row, from_attributes=True) for row in rows]


@router.get("/exports/{export_id}/download")
def download_export(export_id: str, db: Session = Depends(get_db)) -> Response:
    row = db.get(ExportRecord, export_id)
    if not row or not row.storage_key or not storage.exists(row.storage_key):
        raise AppError("EXPORT_NOT_FOUND", "导出文件不存在或已删除。", status_code=404)
    payload = storage.get_bytes(row.storage_key)
    return Response(content=payload, media_type=_media_type_for_export(row), headers={"Content-Disposition": f'attachment; filename="{row.filename}"'})


@router.get("/providers")
def list_providers() -> dict:
    return {
        "providers": [
            {"id": "openai", "name": "OpenAI", "remote": True},
            {"id": "gemini", "name": "Gemini", "remote": True},
            {"id": "deepseek", "name": "DeepSeek", "remote": True},
            {"id": "minimax", "name": "MiniMax", "remote": True},
            {"id": "ollama", "name": "Ollama", "remote": False},
        ],
        "keys_exposed": False,
    }


@router.post("/provider-configs")
def create_provider_config(request: ProviderConfigRequest, db: Session = Depends(get_db)) -> dict:
    validate_base_url(request.base_url, allow_local=request.allow_local or request.provider == "ollama")
    row = ProviderConfig(
        id=new_id("prov"),
        provider=request.provider,
        model=request.model,
        base_url=request.base_url,
        encrypted_api_key=_seal_secret(request.api_key),
        allow_local=request.allow_local,
    )
    db.add(row)
    db.add(AuditLog(id=new_id("audit"), action="provider_config.created", target_type="provider_config", target_id=row.id))
    db.commit()
    return {"id": row.id, "provider": row.provider, "model": row.model, "base_url": row.base_url, "has_api_key": bool(request.api_key)}


@router.post("/source-guardian/search")
def source_guardian_search(request: SourceSearchRequest) -> dict:
    return {
        "query": request.query,
        "status": "pending_user_confirmation",
        "sources": [
            {
                "id": "manual-source-placeholder",
                "title": request.query.strip() or "待确认规范来源",
                "url": "",
                "summary": "联网检索结果必须由用户确认后才能进入规则库。当前实现只返回待确认占位，不影响合规结论。",
            }
        ],
    }


@router.post("/source-guardian/confirm")
def source_guardian_confirm(request: SourceConfirmRequest, db: Session = Depends(get_db)) -> dict:
    db.add(
        AuditLog(
            id=new_id("audit"),
            action="source.confirmed",
            target_type="rule_source",
            target_id=request.source_id,
            metadata_json={"title": request.title, "url": request.url, "summary": request.summary},
        )
    )
    db.commit()
    return {"source_id": request.source_id, "confirmed": True, "affects_auditor": False}


def _persist_blocks(db: Session, project_id: str, version_id: str, thesis: NormalizedThesis) -> None:
    for block in thesis.blocks:
        db.add(
            NormalizedBlockRecord(
                id=new_id("blk"),
                project_id=project_id,
                version_id=version_id,
                block_id=block.id,
                kind=block.kind,
                title=block.title,
                content=block.content,
                source_spans=[span.model_dump(mode="json") for span in block.source_spans],
            )
        )


def _create_rule_agent_proposals(db: Session, project_id: str, version_id: str, thesis: NormalizedThesis) -> None:
    if not thesis.abstract_cn.content.strip():
        db.add(
            Proposal(
                id=new_id("prop"),
                project_id=project_id,
                version_id=version_id,
                target_block_id="abstract-cn",
                operation="suggest",
                before="",
                after="请根据正文自行确认中文摘要候选后再写入。",
                reason="缺少中文摘要会影响正式论文结构完整性。",
                risk="摘要属于论文正文的一部分，必须由用户确认后才能进入导出版本。",
                source_refs=[],
                affects_export=False,
            )
        )
    if thesis.manual_review_flags:
        db.add(
            Proposal(
                id=new_id("prop"),
                project_id=project_id,
                version_id=version_id,
                target_block_id=None,
                operation="review",
                before="",
                after="\n".join(thesis.manual_review_flags),
                reason="检测到复杂元素，导出后需要人工复核。",
                risk="复杂对象可能无法高保真还原。",
                source_refs=[],
                affects_export=False,
            )
        )


def _decide_proposal(db: Session, proposal_id: str, decision: str) -> dict:
    proposal = db.get(Proposal, proposal_id)
    if not proposal:
        raise AppError("PROPOSAL_NOT_FOUND", "建议不存在。", status_code=404)
    if proposal.status != "pending":
        raise AppError("PROPOSAL_ALREADY_DECIDED", "建议已经处理过。", status_code=400)
    project = require_project(db, proposal.project_id)
    proposal.status = decision
    resulting_version_id = None
    if decision == "accepted":
        base = db.get(ThesisVersion, proposal.version_id) if proposal.version_id else latest_version(db, project)
        if not base:
            raise AppError("VERSION_NOT_FOUND", "版本不存在。", status_code=404)
        thesis = NormalizedThesis.model_validate(base.thesis)
        if proposal.affects_export:
            _apply_proposal_to_thesis(thesis, proposal)
        thesis.revision_id = new_id("rev")
        new_version = ThesisVersion(
            id=new_id("ver"),
            project_id=proposal.project_id,
            parent_version_id=base.id,
            label=f"accepted:{proposal.id}",
            thesis=thesis.model_dump(mode="json"),
            created_by="approval",
        )
        db.add(new_version)
        db.flush()
        _persist_blocks(db, proposal.project_id, new_version.id, thesis)
        project.current_version_id = new_version.id
        resulting_version_id = new_version.id
    approval = Approval(id=new_id("appr"), proposal_id=proposal.id, project_id=proposal.project_id, decision=decision, resulting_version_id=resulting_version_id)
    db.add(approval)
    db.add(AuditLog(id=new_id("audit"), project_id=proposal.project_id, action=f"proposal.{decision}", target_type="proposal", target_id=proposal.id))
    db.commit()
    return {"proposal_id": proposal.id, "decision": decision, "resulting_version_id": resulting_version_id}


def _apply_proposal_to_thesis(thesis: NormalizedThesis, proposal: Proposal) -> None:
    if not proposal.target_block_id:
        return
    for section in thesis.body_sections:
        if section.id == proposal.target_block_id and proposal.operation in {"replace", "rewrite", "insert"}:
            section.content = proposal.after
    thesis.blocks = []
    upgraded = NormalizedThesis.model_validate(thesis.model_dump(mode="json"))
    thesis.blocks = upgraded.blocks


def _row_public(row: Any) -> dict:
    return {key: value for key, value in row.__dict__.items() if not key.startswith("_")}


def _media_type_for_export(row: ExportRecord) -> str:
    if row.filename.endswith(".md"):
        return "text/markdown; charset=utf-8"
    if row.filename.endswith(".json"):
        return "application/json"
    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _seal_secret(value: str) -> str:
    if not value:
        return ""
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii")


def validate_base_url(base_url: str | None, *, allow_local: bool) -> None:
    if not base_url:
        return
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise AppError("INVALID_PROVIDER_BASE_URL", "Provider base_url 只允许 http/https URL。", status_code=400)
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80), proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise AppError("INVALID_PROVIDER_BASE_URL", "Provider base_url 无法解析。", status_code=400) from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if allow_local:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise AppError("PROVIDER_BASE_URL_BLOCKED", "Provider base_url 指向内网或本机地址，已被 SSRF 防护拦截。", status_code=400)
