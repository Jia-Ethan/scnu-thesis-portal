from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-thesis.docx"


def test_health_reports_missing_styles_when_forced(monkeypatch):
    monkeypatch.setenv("SCNU_EXTRA_REQUIRED_STYLES", "missing-style-for-test.sty")
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert "missing-style-for-test.sty" in body["tex"]["missing_styles"]


def test_form_request_missing_fields_returns_explicit_error():
    with TestClient(app) as client:
        response = client.post("/api/jobs/from-form", json={})
    assert response.status_code == 422
    payload = response.json()
    assert payload["error_code"] == "FIELD_MISSING"


def test_docx_endpoint_rejects_non_docx_upload():
    with TestClient(app) as client:
        response = client.post(
            "/api/jobs/from-docx",
            data={
                "title": "示例",
                "author_name": "张三",
                "student_id": "2020123456",
                "department": "计算机学院",
                "major": "网络工程",
                "class_name": "1班",
                "advisor_name": "李老师",
                "submission_date": "2026-04-10",
            },
            files={"file": ("bad.txt", b"hello", "text/plain")},
        )
    assert response.status_code == 400
    assert response.json()["error_code"] == "DOCX_INVALID"


def test_docx_endpoint_accepts_valid_docx_and_creates_job():
    with TestClient(app) as client:
        with FIXTURE.open("rb") as fh:
            response = client.post(
                "/api/jobs/from-docx",
                data={
                    "title": "示例论文",
                    "author_name": "张三",
                    "student_id": "2020123456",
                    "department": "计算机学院",
                    "major": "网络工程",
                    "class_name": "1班",
                    "advisor_name": "李老师",
                    "submission_date": "2026-04-10",
                },
                files={"file": ("sample-thesis.docx", fh, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "queued"
    assert payload["job_id"]
