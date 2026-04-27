from pathlib import Path
import time
from threading import Event
from zipfile import ZipFile
import io
import json
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.contracts import NormalizedThesis
from backend.app.security import export_token_for_digest, thesis_digest
from backend.app.storage import storage
from backend.app.worker import cleanup_public_export_jobs, cleanup_public_exports

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-thesis.docx"


def sample_payload():
    return {
        "source_type": "text",
        "cover": {
            "title": "结构化映射示例论文：副标题不会进入页眉——这是一个用于验证页眉截断规则的超长主标题",
            "advisor": "李老师",
            "student_name": "张三",
            "student_id": "2020123456",
            "school": "华南师范大学",
            "department": "计算机学院",
            "major": "网络工程",
            "class_name": "1班",
            "graduation_time": "2026年6月",
        },
        "abstract_cn": {
            "content": "本文展示结构化映射后的论文导出流程，并说明如何在统一中间结构下生成符合学校规范的本科论文 Word 文件。",
            "keywords": ["论文模板", "结构化映射", "Word 导出"],
        },
        "abstract_en": {
            "content": "This thesis demonstrates a standards-driven Word export pipeline for SCNU undergraduate theses.",
            "keywords": ["thesis", "word export", "mapping"],
        },
        "body_sections": [
            {
                "id": "section-1",
                "level": 1,
                "title": "引言",
                "content": "本章介绍系统目标、输入方式与规范仲裁逻辑。" * 8,
            },
            {
                "id": "section-2",
                "level": 2,
                "title": "结构设计",
                "content": "系统统一将输入映射为中间结构，再渲染为规范驱动的 Word 文档。" * 6,
            },
        ],
        "references": [
            {"raw_text": "【1】示例作者. 论文模板实践[J].", "normalized_text": "示例作者. 论文模板实践[J].", "detected_type": "J"},
        ],
        "appendices": [
            {"id": "appendix-1", "title": "附录 A 测试样例", "content": "这里是附录内容。"},
        ],
        "acknowledgements": "感谢导师的指导。",
        "notes": "",
        "warnings": [],
        "manual_review_flags": [],
        "missing_sections": [],
        "source_features": {
            "table_count": 0,
            "image_count": 0,
            "footnote_count": 0,
            "textbox_count": 0,
            "shape_count": 0,
            "field_count": 0,
            "rich_run_count": 0,
        },
        "capabilities": {
            "docx_export": True,
            "profile": "undergraduate",
        },
    }


def test_health_reports_word_capabilities_and_limits():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["template"] == "sc-th-word"
    assert body["capabilities"]["docx_export"] is True
    assert body["limits"]["max_docx_size_bytes"] == 20 * 1024 * 1024
    assert body["limits"]["max_text_precheck_chars"] == 80_000


def test_precheck_docx_rejects_non_docx_upload():
    with TestClient(app) as client:
        response = client.post(
            "/api/precheck/docx",
            files={"file": ("bad.txt", b"hello", "text/plain")},
        )

    assert response.status_code == 400
    assert response.json()["error_code"] == "UNSUPPORTED_FILE_TYPE"


def test_precheck_docx_returns_new_contract_payload():
    with TestClient(app) as client:
        with FIXTURE.open("rb") as fh:
            response = client.post(
                "/api/precheck/docx",
                files={"file": ("sample-thesis.docx", fh, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )

    assert response.status_code == 200
    payload = response.json()
    assert payload["thesis"]["source_type"] == "docx"
    assert payload["thesis"]["cover"]["title"] == "基于结构化映射的本科论文生成示例"
    assert payload["summary"]["can_confirm"] is True
    assert payload["preview_blocks"]


def test_precheck_text_keeps_missing_sections_as_warnings():
    with TestClient(app) as client:
        response = client.post(
            "/api/precheck/text",
            json={"text": "# 引言\n\n这是正文。"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["can_confirm"] is True
    assert payload["summary"]["warning_count"] >= 1
    assert any(issue["code"] == "ABSTRACT_CN_BLANK" for issue in payload["issues"])


def test_public_precheck_requires_privacy_confirmation():
    with TestClient(app) as client:
        response = client.post("/api/public/precheck/text", json={"text": "已有论文正文"})

    assert response.status_code == 400
    assert response.json()["error_code"] == "PRIVACY_CONFIRMATION_REQUIRED"


def test_public_text_precheck_returns_export_token_and_expires_at():
    with TestClient(app) as client:
        response = client.post(
            "/api/public/precheck/text",
            json={"text": "# 引言\n\n这是已有论文正文。" * 20, "privacy_accepted": True},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["export_token"]
    assert payload["expires_at"]


def test_public_text_precheck_rejects_long_input():
    with TestClient(app) as client:
        response = client.post(
            "/api/public/precheck/text",
            json={"text": "x" * 80001, "privacy_accepted": True},
        )

    assert response.status_code == 400
    assert response.json()["error_code"] == "TEXT_TOO_LONG"


def test_public_docx_precheck_validates_file_header():
    with TestClient(app) as client:
        response = client.post(
            "/api/public/precheck/docx",
            data={"privacy_accepted": "true"},
            files={"file": ("paper.docx", b"not-a-zip", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )

    assert response.status_code == 400
    assert response.json()["error_code"] == "DOCX_INVALID"


def test_public_docx_export_uses_token_and_retained_download():
    with TestClient(app) as client:
        precheck = client.post(
            "/api/public/precheck/text",
            json={"text": "# 引言\n\n这是已有论文正文。" * 40, "privacy_accepted": True},
        ).json()
        export = client.post(
            "/api/public/exports/docx",
            json={"thesis": sample_payload(), "export_token": precheck["export_token"]},
        )
        assert export.status_code == 403

        export = client.post(
            "/api/public/exports/docx",
            json={"thesis": precheck["thesis"], "export_token": precheck["export_token"]},
        )

        assert export.status_code == 200
        payload = export.json()
        download = client.get(payload["download_url"])
        report = client.get(payload["report_url"])
        assert download.status_code == 200
        assert download.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert report.status_code == 200
        assert report.json()["export_id"] == payload["export_id"]


def test_public_export_job_completes_and_serves_download():
    with TestClient(app) as client:
        precheck = client.post(
            "/api/public/precheck/text",
            json={"text": "# 引言\n\n这是已有论文正文。" * 40, "privacy_accepted": True},
        ).json()
        job = client.post(
            "/api/public/export-jobs/docx",
            json={"thesis": precheck["thesis"], "export_token": precheck["export_token"]},
        )
        assert job.status_code == 200
        job_payload = job.json()
        assert job_payload["status"] in {"running", "done"}

        deadline = time.time() + 3
        while job_payload["status"] == "running" and time.time() < deadline:
            time.sleep(0.05)
            job_payload = client.get(f"/api/public/export-jobs/{job_payload['job_id']}").json()

        assert job_payload["status"] == "done"
        assert job_payload["progress"] == 100
        download = client.get(job_payload["download_url"])
        assert download.status_code == 200
        assert download.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert "filename*=UTF-8''" in download.headers["content-disposition"]


def test_public_export_download_supports_non_ascii_filename():
    payload = sample_payload()
    payload["cover"]["title"] = "中文论文标题"
    thesis = NormalizedThesis.model_validate(payload)
    expires_at = int((datetime.now(UTC) + timedelta(minutes=30)).timestamp())
    export_token = export_token_for_digest(thesis_digest(thesis.model_dump_json()), expires_at)
    with TestClient(app) as client:
        export = client.post(
            "/api/public/exports/docx",
            json={"thesis": payload, "export_token": export_token},
        ).json()

        download = client.get(export["download_url"])
        assert download.status_code == 200
        disposition = download.headers["content-disposition"]
        assert 'filename="Forma-export.docx"' in disposition
        assert "%E4%B8%AD%E6%96%87" in disposition


def test_public_export_job_can_be_canceled(monkeypatch):
    started = Event()
    release = Event()

    def slow_export(_thesis):
        started.set()
        release.wait(2)
        return b"PK-slow-docx"

    monkeypatch.setattr("backend.app.public_api.export_docx", slow_export)

    with TestClient(app) as client:
        precheck = client.post(
            "/api/public/precheck/text",
            json={"text": "# 引言\n\n这是已有论文正文。" * 40, "privacy_accepted": True},
        ).json()
        job = client.post(
            "/api/public/export-jobs/docx",
            json={"thesis": precheck["thesis"], "export_token": precheck["export_token"]},
        ).json()
        assert started.wait(1)
        canceled = client.post(f"/api/public/export-jobs/{job['job_id']}/cancel").json()
        release.set()

        assert canceled["status"] == "canceled"
        assert canceled["error_code"] == "EXPORT_CANCELED"
        final = client.get(f"/api/public/export-jobs/{job['job_id']}").json()
        assert final["status"] == "canceled"


def test_public_export_expiry_and_janitor_cleanup():
    with TestClient(app) as client:
        precheck = client.post(
            "/api/public/precheck/text",
            json={"text": "# 引言\n\n这是已有论文正文。" * 40, "privacy_accepted": True},
        ).json()
        export = client.post(
            "/api/public/exports/docx",
            json={"thesis": precheck["thesis"], "export_token": precheck["export_token"]},
        ).json()

    meta_path = storage.root / "public" / "exports" / export["export_id"] / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["expires_at"] = (datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1)).isoformat()
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    assert cleanup_public_exports() == 1
    assert not meta_path.exists()


def test_public_export_job_expiry_cleanup():
    job_id = "job_expired_cleanup"
    export_id = "pub_expired_cleanup"
    meta = {
        "job_id": job_id,
        "export_id": export_id,
        "status": "done",
        "progress": 100,
        "message": "导出完成。",
        "download_url": f"/api/public/exports/{export_id}/download",
        "report_url": f"/api/public/exports/{export_id}/report",
        "expires_at": (datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1)).isoformat(),
        "error_code": None,
        "cancel_requested": False,
    }
    storage.put_bytes(f"public/export-jobs/{job_id}/meta.json", json.dumps(meta).encode("utf-8"))
    storage.put_bytes(f"public/exports/{export_id}/demo.docx", b"PK-expired")
    meta_path = storage.root / "public" / "export-jobs" / job_id / "meta.json"

    assert cleanup_public_export_jobs() == 1
    assert not meta_path.exists()


def test_export_docx_rejects_blocking_payload():
    payload = sample_payload()
    payload["body_sections"] = []
    with TestClient(app) as client:
        response = client.post("/api/export/docx", json=payload)

    assert response.status_code == 400
    assert response.json()["error_code"] == "FIELD_MISSING"
    assert response.json()["details"]["blocking_count"] >= 1


def test_export_docx_returns_word_document():
    with TestClient(app) as client:
        response = client.post("/api/export/docx", json=sample_payload())

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert response.headers["content-disposition"] == 'attachment; filename="SC-TH-export.docx"'

    archive = ZipFile(io.BytesIO(response.content))
    names = set(archive.namelist())
    assert "word/document.xml" in names
    assert "word/styles.xml" in names
    document_xml = archive.read("word/document.xml").decode("utf-8")
    assert "华南师范大学" in document_xml
    assert "参考文献" in document_xml
    assert 'TOC \\o "1-4" \\h \\z \\u' in document_xml


def test_export_docx_fails_when_template_is_missing(monkeypatch):
    monkeypatch.setattr("backend.app.services.export.TEMPLATE_DOCX_PATH", Path("/tmp/missing-template.docx"))
    with TestClient(app) as client:
        response = client.post("/api/export/docx", json=sample_payload())

    assert response.status_code == 500
    assert response.json()["error_code"] == "TEMPLATE_DEPENDENCY_MISSING"
