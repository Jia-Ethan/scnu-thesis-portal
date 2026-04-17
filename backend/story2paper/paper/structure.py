"""
Paper Structure Templates
定义 Story2Paper 论文的章节结构与各部分的写作规范。
参考 ACL/EMNLP/ICLR 的论文格式要求。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


# ─── Section Definition ────────────────────────────────────────────────────────

@dataclass
class SectionTemplate:
    name: str
    purpose: str                          # 该 section 的核心目的
    subsections: list[str] = field(default_factory=list)
    min_words: int = 300                 # 最少字数（英文词）
    typical_words: tuple[int, int] = (500, 1000)  # 典型字数范围
    required_elements: list[str] = field(default_factory=list)  # 必须包含的元素
    writer_role: str = "writer"           # 使用的 agent role


# ─── ACL/EMNLP/ICLR Section Templates ─────────────────────────────────────────

PAPER_SECTIONS: dict[str, SectionTemplate] = {
    "title": SectionTemplate(
        name="Title",
        purpose="吸引读者 + 准确描述贡献",
        min_words=0,
        typical_words=(8, 15),
        required_elements=["method name", "task", "key insight"],
    ),
    "abstract": SectionTemplate(
        name="Abstract",
        purpose="150-300 词概括全文明确贡献",
        min_words=150,
        typical_words=(150, 300),
        required_elements=["problem", "method", "key results", "impact"],
    ),
    "introduction": SectionTemplate(
        name="Introduction",
        purpose="吸引读者 + 概述背景 + 明确贡献",
        subsections=[
            "Research Problem (1段)",
            "Existing Approaches & Limitations (1段)",
            "Our Approach & Key Insight (1段)",
            "Technical Contributions (列表)",
            "Broader Impact / Ethical Consideration (可选，1段)",
        ],
        min_words=500,
        typical_words=(700, 1200),
        required_elements=[
            "problem statement",
            "existing gap",
            "our approach summary",
            "contribution list (3-4 bullet)",
            "paper structure overview",
        ],
    ),
    "related_work": SectionTemplate(
        name="Related Work",
        purpose="建立与现有工作的联系，区分差异",
        subsections=[
            "Multi-Agent Systems for Writing",
            "LLM Pipeline Orchestration",
            "Visual/Structured Output in LLM Agents",
        ],
        min_words=600,
        typical_words=(800, 1500),
        required_elements=[
            "taxonomy of prior work",
            "strengths of prior work",
            "limitations we address",
            "clear differentiation",
        ],
    ),
    "background": SectionTemplate(
        name="Background",
        purpose="提供阅读正文所需的概念基础",
        subsections=[
            "Large Language Models",
            "Multi-Agent Orchestration",
            "Contract-Based Coordination",
        ],
        min_words=400,
        typical_words=(500, 900),
        required_elements=[
            "formal definitions",
            "relevant prior work citations",
            "conceptual groundwork",
        ],
    ),
    "method": SectionTemplate(
        name="Method",
        purpose="精确描述技术方法",
        subsections=[
            "Overview / Problem Formalization",
            "Architect Agent",
            "Writer Agent",
            "Evaluator Agent",
            "Refiner Agent",
            "Visual Contract Mechanism",
            "Pipeline Orchestration",
        ],
        min_words=1000,
        typical_words=(1500, 3000),
        required_elements=[
            "problem definition (mathematical)",
            "algorithm description",
            "contract schema",
            "agent responsibilities",
            "complexity analysis",
        ],
    ),
    "experiment": SectionTemplate(
        name="Experiment",
        purpose="实验验证方法有效性",
        subsections=[
            "Setup / Datasets",
            "Baseline Methods",
            "Main Results",
            "Ablation Study",
            "Human Evaluation",
            "Error Analysis / Case Studies",
        ],
        min_words=800,
        typical_words=(1200, 2500),
        required_elements=[
            "research questions",
            "dataset description",
            "metrics",
            "baselines",
            "statistical significance",
            "ablation results",
            "human eval protocol",
        ],
    ),
    "discussion": SectionTemplate(
        name="Discussion (optional for ACL/EMNLP)",
        purpose="反思局限性、未来方向、社会影响",
        min_words=200,
        typical_words=(300, 600),
        required_elements=["limitations", "future work", "broader impact"],
    ),
    "conclusion": SectionTemplate(
        name="Conclusion",
        purpose="总结贡献，简洁有力",
        min_words=100,
        typical_words=(150, 300),
        required_elements=["summary of contributions", "key takeaways"],
    ),
}


# ─── ACL Submission Format ─────────────────────────────────────────────────────

ACL_REQUIREMENTS = {
    "title": {
        "max_words": 20,
        "format": "Plain text, first letter capitalized",
    },
    "abstract": {
        "max_words": 300,
        "format": "Plain text paragraph",
    },
    "introduction": {
        "max_words": 1500,
        "format": "Plain text with section markers",
    },
    "conclusion": {
        "max_words": 500,
        "format": "Plain text",
    },
    "references": {
        "format": "ACLAnthology style (commacomplete, titles italicized)",
    },
    "appendix": {
        "format": "After references, clearly marked",
    },
    "author_limit": {
        "ACL": "8 authors",
        "EMNLP": "8 authors",
        "ICLR": "no strict limit",
    },
    "page_limit": {
        "ACL": "8 pages + references",
        "EMNLP": "8 pages + references",
        "ICLR": "8 pages + supplementary",
    },
}


@dataclass
class PaperDraft:
    """论文草稿容器。"""
    title: str = ""
    abstract: str = ""
    sections: dict[str, str] = field(default_factory=dict)  # name -> content
    references: list[str] = field(default_factory=list)
    appendix: dict[str, str] = field(default_factory=dict)  # appendix section -> content
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "abstract": self.abstract,
            "sections": self.sections,
            "references": self.references,
            "appendix": self.appendix,
            "metadata": self.metadata,
        }

    def total_words(self) -> int:
        """估算总词数（英文）。"""
        text = (
            self.title + " " + self.abstract + " "
            + " ".join(self.sections.values())
        )
        return len(text.split())


def build_paper_from_sections(
    sections: dict[str, str],
    title: str = "",
    abstract: str = "",
    format: Literal["markdown", "latex", "plain"] = "markdown",
) -> str:
    """
    将各 section 内容组装为完整论文。
    """
    if format == "markdown":
        parts = [f"# {title}", f"\n## Abstract\n{abstract}"]
        for sec_name, sec_content in sections.items():
            parts.append(f"\n## {sec_name}\n{sec_content}")
        return "\n".join(parts)
    elif format == "latex":
        # LaTeX 格式（基础模板）
        body = _build_latex_body(sections)
        return _latex_template(title, abstract, body)
    else:
        parts = [title, "\n" + abstract]
        parts.extend(sections.values())
        return "\n\n".join(parts)


def _build_latex_body(sections: dict[str, str]) -> str:
    mapping = {
        "Introduction": "intro",
        "Related Work": "related",
        "Background": "background",
        "Method": "method",
        "Experiments": "experiments",
        "Discussion": "discussion",
        "Conclusion": "conclusion",
    }
    parts = []
    for sec_name, sec_content in sections.items():
        label = mapping.get(sec_name, sec_name.lower())
        parts.append(f"\\section{{{sec_name}}}\n\\label{{{label}}}\n{sec_content}")
    return "\n\n".join(parts)


def _latex_template(title: str, abstract: str, body: str) -> str:
    return f"""\\documentclass[12pt]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{acl}}
\\usepackage{{times}}
\\usepackage{{url}}
\\usepackage{{booktabs}}
\\usepackage{{amsmath}}

\\title{{{title}}}

\\author{{}}

\\begin{{document}}
\\maketitle
\\begin{{abstract}}
{abstract}
\\end{{abstract}}

{body}

\\bibliography{{references}}
\\bibliographystyle{{acl_natbib}}

\\end{{document}}
"""
