from pathlib import Path

from app.generator import convert_sections_to_markdown, render_body_from_markdown
from app.parser import parse_docx
from app.schemas import SectionNode


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-thesis.docx"


def test_parse_docx_extracts_expected_sections():
    result = parse_docx(FIXTURE)
    kinds = [section.kind for section in result.sections]
    assert "abstract_cn" in kinds
    assert "abstract_en" in kinds
    assert "references" in kinds
    assert "acknowledgements" in kinds
    assert "appendix" in kinds


def test_convert_sections_to_markdown_preserves_titles():
    markdown = convert_sections_to_markdown(
        [
            SectionNode(kind="body", title="引言", content="第一段"),
            SectionNode(kind="body", title="方案设计", content="第二段"),
        ]
    )
    assert "# 引言" in markdown
    assert "# 方案设计" in markdown


def test_render_body_from_markdown_adds_fallback_section():
    latex = render_body_from_markdown("这是没有标题的正文。")
    assert "\\section{正文}" in latex
