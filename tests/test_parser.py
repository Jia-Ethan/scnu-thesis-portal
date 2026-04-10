from pathlib import Path

from backend.app.contracts import CapabilityFlags
from backend.app.services.parse import normalize_text_input, parse_docx_file


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-thesis.docx"


def test_parse_docx_extracts_expected_sections():
    thesis = parse_docx_file(FIXTURE, CapabilityFlags(tex_zip=True, pdf=False, pdf_reason="local only"))
    assert thesis.abstract_cn.content
    assert thesis.abstract_en.content
    assert thesis.references.items
    assert thesis.acknowledgements
    assert thesis.appendix


def test_text_normalize_adds_missing_abstract_warnings():
    thesis = normalize_text_input("# 引言\n\n正文内容。", CapabilityFlags(tex_zip=True, pdf=False, pdf_reason="local only"))
    assert thesis.body_sections
    assert "未识别到中文摘要，可在下一步补充。" in thesis.warnings
    assert "未识别到 Abstract，可在下一步补充。" in thesis.warnings
