from pathlib import Path
from zipfile import ZipFile
import io

from fastapi.testclient import TestClient

from backend.app.main import app

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-thesis.docx"


def sample_payload():
    return {
        "source_type": "text",
        "metadata": {
            "title": "结构化映射示例论文",
            "author_name": "张三",
            "student_id": "2020123456",
            "department": "计算机学院",
            "major": "网络工程",
            "class_name": "1班",
            "advisor_name": "李老师",
            "submission_date": "2026-04-10",
        },
        "abstract_cn": {
            "content": "本文展示结构化映射后的论文导出流程。",
            "keywords": ["论文模板", "结构化映射"],
        },
        "abstract_en": {
            "content": "This thesis demonstrates a normalized export flow.",
            "keywords": ["thesis", "mapping"],
        },
        "body_sections": [
            {
                "id": "section-1",
                "level": 1,
                "title": "引言",
                "content": "本章介绍系统目标。",
            }
        ],
        "references": {"items": ["【1】示例作者. 论文模板实践."]},
        "acknowledgements": "感谢导师的指导。",
        "appendix": "附录 A：补充说明。",
        "warnings": [],
        "parse_errors": [],
        "capabilities": {
            "tex_zip": True,
            "pdf": False,
            "pdf_reason": "生产环境默认关闭 PDF，请导出 tex 工程 zip。",
        },
    }


def test_health_reports_capabilities_and_limits():
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert "capabilities" in body
    assert body["limits"]["max_docx_size_bytes"] == 4 * 1024 * 1024


def test_docx_endpoint_rejects_non_docx_upload():
    with TestClient(app) as client:
        response = client.post(
            "/api/parse/docx",
            files={"file": ("bad.txt", b"hello", "text/plain")},
        )
    assert response.status_code == 400
    assert response.json()["error_code"] == "UNSUPPORTED_FILE_TYPE"


def test_docx_endpoint_returns_normalized_payload():
    with TestClient(app) as client:
        with FIXTURE.open("rb") as fh:
            response = client.post(
                "/api/parse/docx",
                files={"file": ("sample-thesis.docx", fh, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "docx"
    assert payload["abstract_cn"]["content"]
    assert payload["abstract_en"]["content"]
    assert payload["body_sections"]


def test_text_normalize_returns_body_sections():
    with TestClient(app) as client:
        response = client.post(
            "/api/normalize/text",
            json={"text": "# 引言\n\n这是正文。\n\n# 参考文献\n\n【1】示例作者. 论文模板实践."},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "text"
    assert payload["body_sections"][0]["title"] == "引言"
    assert payload["references"]["items"]


def test_export_texzip_returns_zip_payload():
    with TestClient(app) as client:
        response = client.post("/api/export/texzip", json=sample_payload())
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    archive = ZipFile(io.BytesIO(response.content))
    names = set(archive.namelist())
    assert "main.tex" in names
    assert "body/generated-body.tex" in names
    assert "cover/image.tex" in names


def test_export_pdf_returns_disabled_when_feature_is_off(monkeypatch):
    monkeypatch.setattr("backend.app.services.pdf.ENABLE_PDF_EXPORT", False)
    with TestClient(app) as client:
        response = client.post("/api/export/pdf", json=sample_payload())
    assert response.status_code == 400
    assert response.json()["error_code"] == "PDF_DISABLED"
