"""
Story2Proposal Baseline
简化版 pipeline：生成大纲 → 分段写作，无 Visual Contract 机制。
作为 Story2Paper 的消融对照（去掉 contract 协调机制）。
"""

from __future__ import annotations

import json
from backend.story2paper.shared.llm_router import LLMRouter


OUTLINE_PROMPT_TEMPLATE = """You are an academic paper architect. Given a research story, produce a detailed paper outline in JSON format.

Research Story:
{story}

Output ONLY a valid JSON object with this structure (no markdown, no explanation):
{{
  "title": "Paper Title",
  "abstract": "150-200 word abstract",
  "sections": [
    {{"name": "Introduction", "purpose": "...", "key_points": ["...", "..."]}},
    {{"name": "Related Work", "purpose": "...", "key_points": ["...", "..."]}},
    {{"name": "Background", "purpose": "...", "key_points": ["...", "..."]}},
    {{"name": "Method", "purpose": "...", "key_points": ["...", "..."]}},
    {{"name": "Experiments", "purpose": "...", "key_points": ["...", "..."]}},
    {{"name": "Conclusion", "purpose": "...", "key_points": ["...", "..."]}}
  ]
}}
"""


SECTION_PROMPT_TEMPLATE = """You are an academic paper writer. Write the complete section named "{section_name}" for a paper about the following research story.

Research Story:
{story}

Current Paper Outline:
{outline}

Requirements for this section:
- Purpose: {purpose}
- Key Points to Cover: {key_points}
- Write in formal academic English
- Be technically precise and thorough
- This section should be substantial (at least 300 words)
- Include citations placeholders like [Author, Year] where appropriate
"""


SECTION_NAMES_ORDER = [
    "Introduction",
    "Related Work",
    "Background",
    "Method",
    "Experiments",
    "Conclusion",
]


class Story2ProposalPipeline:
    """
    无 Contract 的简化 pipeline：
    1. LLM 生成大纲（JSON）
    2. LLM 按大纲逐节写作
    无 Architect/Writer/Evaluator/Refiner 的分工协调，
    无 Visual Contract 状态共享。
    """

    def __init__(self, model: str | None = None):
        self.router = LLMRouter()
        self.model = model or "gpt-4o"

    def _generate_outline(self, story: str) -> dict:
        messages = [
            {"role": "user", "content": OUTLINE_PROMPT_TEMPLATE.format(story=story)},
        ]
        response = self.router.route(messages, model=self.model)
        try:
            # 尝试从响应中提取 JSON
            content = response["content"].strip()
            # 去除可能的 markdown 代码块
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.strip())
        except (json.JSONDecodeError, KeyError) as e:
            # fallback：返回默认大纲
            return {
                "title": "Generated Paper",
                "abstract": "",
                "sections": [
                    {"name": name, "purpose": "", "key_points": []}
                    for name in SECTION_NAMES_ORDER
                ],
            }

    def _write_section(self, story: str, outline: dict, section: dict) -> str:
        messages = [
            {
                "role": "user",
                "content": SECTION_PROMPT_TEMPLATE.format(
                    section_name=section["name"],
                    story=story,
                    outline=json.dumps(outline, indent=2, ensure_ascii=False),
                    purpose=section.get("purpose", ""),
                    key_points=", ".join(section.get("key_points", [])),
                ),
            },
        ]
        response = self.router.route(messages, model=self.model)
        return response["content"]

    def run(self, story: str) -> str:
        """运行完整 pipeline，返回完整论文文本。"""
        # Step 1: 生成大纲
        outline = self._generate_outline(story)

        # Step 2: 按顺序写每个 section
        sections_text = []
        for sec in outline.get("sections", []):
            sec_text = self._write_section(story, outline, sec)
            sections_text.append(f"## {sec['name']}\n{sec_text}")

        # 组装完整论文
        title = outline.get("title", "Paper Title")
        abstract = outline.get("abstract", "")

        paper_parts = [
            f"# {title}",
            f"\n## Abstract\n{abstract}",
        ]
        paper_parts.extend(sections_text)

        return "\n\n".join(paper_parts)


# 单例
_default_pipeline: Story2ProposalPipeline | None = None


def get_default() -> Story2ProposalPipeline:
    global _default_pipeline
    if _default_pipeline is None:
        _default_pipeline = Story2ProposalPipeline()
    return _default_pipeline


def run(story: str) -> str:
    """快捷入口。"""
    return get_default().run(story)
