"""
Paper Writer
完整论文写作 Agent，基于 Story2Paper pipeline 的输出，
生成符合 ACL/EMNLP/ICLR 格式的正式论文。
"""

from __future__ import annotations

from backend.story2paper.paper.structure import (
    PAPER_SECTIONS,
    PaperDraft,
    build_paper_from_sections,
)
from backend.story2paper.paper.method_formalizer import MethodFormalizer
from backend.story2paper.shared.llm_router import LLMRouter


# ─── Section Writing Prompts ───────────────────────────────────────────────────

SECTION_SYSTEM_PROMPT = """You are an expert academic paper writer with extensive experience in top-tier ML/NLP venues (ACL, EMNLP, ICLR, NeurIPS).
You write precise, technically rigorous English. You follow the style guidelines of ACL Rolling Review (ARR).
Never be vague. Every claim must be supported. Every technical term must be defined or cited."""


INTRO_PROMPT = """You are writing the Introduction section of an academic paper.

Research Story / Idea:
{story}

Method Summary (from pipeline):
{method_summary}

Task:
Write the Introduction section. It must contain:
1. **Problem Statement** — What is the problem and why does it matter? (1 paragraph)
2. **Existing Approaches & Limitations** — What have others done? What are their shortcomings? (1-2 paragraphs)
3. **Our Approach & Key Insight** — What do we propose? What is the key insight? (1-2 paragraphs)
4. **Technical Contributions** — List 3-4 concrete contributions as bullet points
5. **Paper Structure** — Brief overview of subsequent sections (1 paragraph)

Style:
- Formal academic English, no colloquialisms
- Use "we" for the authors
- Cite related work as [Author, Year] (generic citations are fine)
- Length: 700-1200 words

Output: Write the full Introduction section in academic English."""


RELATED_WORK_PROMPT = """You are writing the Related Work section of an academic paper.

Our Method:
{method_summary}

Our Key Differences from Prior Work:
{differentiation}

Task:
Write the Related Work section covering these subsections:
1. Multi-Agent Systems for Writing — ChatDev, MetaGPT, Story2Proposal
2. LLM Pipeline Orchestration — langgraph, AutoGen, sequential prompting
3. Visual/Structured Output in LLM Agents — JSON mode, guidance, contract-based agents

For each area:
- Describe the approach and its strengths
- Identify its key limitations
- Explain how our work addresses or differs from it

Style: Formal academic English. Length: 800-1500 words.
Cite as [Author, Year]. Generic citations are acceptable."""


BACKGROUND_PROMPT = """You are writing the Background section of an academic paper.

Topics to cover:
1. Large Language Models (transformer architecture, instruction tuning,涌现能力)
2. Multi-Agent Orchestration (why coordination matters, shared state)
3. Contract-Based Coordination (visual contracts, claim/constraint formalization)

Keep it concise — this section provides foundation for readers who may not be experts.
Length: 500-900 words.
Cite as [Author, Year]."""


EXPERIMENTS_PROMPT = """You are writing the Experiments section of an academic paper.

Research Questions:
{research_questions}

Baselines to Compare:
{baselines}

Results Summary (from benchmark):
{results_summary}

Task:
Write the Experiments section with these subsections:
1. **Setup** — Datasets, evaluation metrics, implementation details
2. **Baselines** — Description of baseline methods
3. **Main Results** — Main results table/figure, answer each RQ
4. **Ablation Study** — Effect of each component (contract, refiner, etc.)
5. **Human Evaluation** — Protocol and results
6. **Error Analysis** — Qualitative examples of failures

Style: Formal, data-driven, precise.
Report numerical results with appropriate precision.
State significance where applicable."""


DISCUSSION_PROMPT = """You are writing the Discussion section.
Cover:
1. **Limitations** — What are the failure modes and boundaries of validity?
2. **Future Work** — 3-4 concrete directions for future research
3. **Broader Impact** — Potential positive and negative societal implications

Length: 300-600 words. Be honest and thoughtful."""


CONCLUSION_PROMPT = """You are writing the Conclusion section.

Key Contributions:
{contributions}

Task:
Write a concise Conclusion (150-300 words):
- Summarize the problem and our approach
- List key results (quantitative if possible)
- State the main takeaway

Do NOT introduce new material. End with a forward-looking statement."""


REFERENCES_SUGGESTION_PROMPT = """Based on the following paper content, suggest 15-20 key references in ACL Anthology format.
Include references from these categories:
- Multi-agent LLM systems (ChatDev, MetaGPT, etc.)
- LLM pipeline orchestration
- JSON/structured output for LLMs
- Evaluation of LLM-generated text
- The specific domain mentioned in the paper

Paper abstract/outline:
{outline}

Output: A list of references in ACLAnthology BibTeX format."""


# ─── Paper Writer ──────────────────────────────────────────────────────────────

class PaperWriter:
    """
    将 Story2Paper pipeline 输出转换为正式论文。
    """

    def __init__(self, model: str | None = None):
        self.router = LLMRouter()
        self.model = model or "gpt-4o"
        self.formalizer = MethodFormalizer(model=self.model)

    def _write_section(
        self,
        prompt_template: str,
        **kwargs,
    ) -> str:
        messages = [
            {"role": "system", "content": SECTION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt_template.format(**kwargs)},
        ]
        resp = self.router.route(messages, model=self.model)
        return resp["content"]

    def write_full_paper(
        self,
        story: str,
        method_summary: str,
        contract_description: str,
        results_summary: str = "",
        baselines: list[str] | None = None,
        research_questions: list[str] | None = None,
        output_format: str = "markdown",
    ) -> PaperDraft:
        """
        生成完整论文草稿。
        """
        baselines = baselines or ["DirectChat", "Story2Proposal"]
        research_questions = research_questions or [
            "RQ1: Does Story2Paper outperform baseline methods?",
            "RQ2: What is the contribution of the Visual Contract mechanism?",
            "RQ3: How do human evaluators perceive the quality?",
        ]

        # 各 section 独立写作
        intro = self._write_section(INTRO_PROMPT, story=story, method_summary=method_summary)
        related = self._write_section(
            RELATED_WORK_PROMPT,
            method_summary=method_summary,
            differentiation="See introduction",
        )
        background = self._write_section(BACKGROUND_PROMPT)

        # Method section 需要 formalize
        method_formal = self.formalizer.build_method_section(
            informal_method=method_summary,
            contract_description=contract_description,
        )

        experiments = self._write_section(
            EXPERIMENTS_PROMPT,
            research_questions="\n".join(f"- {rq}" for rq in research_questions),
            baselines="\n".join(f"- {b}" for b in baselines),
            results_summary=results_summary or "See benchmark results section",
        )
        discussion = self._write_section(DISCUSSION_PROMPT)
        conclusion = self._write_section(
            CONCLUSION_PROMPT,
            contributions="See paper introduction contribution list",
        )

        # References（单独 LLM call）
        refs = self._write_section(
            REFERENCES_SUGGESTION_PROMPT,
            outline=method_summary[:500],
        )

        draft = PaperDraft(
            title=self._extract_title(method_summary),
            abstract=self._extract_abstract(story),
            sections={
                "Introduction": intro,
                "Related Work": related,
                "Background": background,
                "Method": method_formal,
                "Experiments": experiments,
                "Discussion": discussion,
                "Conclusion": conclusion,
            },
            references=self._parse_references(refs),
            metadata={
                "story": story,
                "method_summary": method_summary,
                "contract_description": contract_description,
            },
        )

        return draft

    def _extract_title(self, method_summary: str) -> str:
        """从 method_summary 中尝试提取标题。"""
        first_line = method_summary.strip().split("\n")[0]
        if len(first_line) < 80:
            return first_line
        # fallback：生成描述性标题
        return "Story2Paper: Multi-Agent Contract-Driven Academic Paper Generation"

    def _extract_abstract(self, story: str) -> str:
        """从 story 生成摘要。"""
        prompt = f"""Given the following research story, write a 200-word abstract for an academic paper.
Research Story: {story}
Write in formal academic English. Start with "We propose...""""
        return self._write_section(prompt)

    def _parse_references(self, refs_text: str) -> list[str]:
        """从 LLM 输出解析 references 列表。"""
        lines = refs_text.split("\n")
        result = []
        in_item = False
        current = []
        for line in lines:
            if "@inproceedings{" in line or "@article{" in line or "@book{" in line:
                in_item = True
                current = [line]
            elif in_item:
                current.append(line)
                if line.strip().endswith("}"):
                    result.append("\n".join(current))
                    in_item = False
                    current = []
        return result

    def export(
        self,
        draft: PaperDraft,
        fmt: str = "markdown",
    ) -> str:
        """导出为指定格式。"""
        return build_paper_from_sections(
            sections=draft.sections,
            title=draft.title,
            abstract=draft.abstract,
            format=fmt,
        )
