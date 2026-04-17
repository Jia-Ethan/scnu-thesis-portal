"""
Architect Agent — 分析研究想法，设计论文结构，初始化视觉契约
"""

from __future__ import annotations
from typing import Any
from .base import BaseAgent, AgentConfig
from backend.story2paper.shared.state import VisualContract, FigureEntry, TableEntry
from backend.story2paper.shared.llm_router import llm_call


SYSTEM_PROMPT = """You are the Architect Agent in a multi-agent academic paper generation system.

Your task: Given a research idea or raw prompt, produce a structured paper outline and initialize the Visual Contract.

Output format — respond ONLY with valid JSON matching this schema:
{
  "title": "Paper title",
  "abstract_summary": "2-3 sentence summary of the paper",
  "sections": [
    {
      "section_id": "sec_1",
      "title": "Section title",
      "purpose": "What this section accomplishes",
      "key_points": ["point 1", "point 2"],
      "expected_figures": ["fig_description"],
      "expected_tables": ["table_description"],
      "expected_equations": ["equation_description"]
    }
  ],
  "novelty_statement": "One sentence articulating the paper's main contribution",
  "baseline_comparisons": ["baseline 1", "baseline 2"]
}
"""


class ArchitectAgent(BaseAgent):
    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig(name="architect"))

    def run(self, state: dict) -> dict:
        research_prompt: str = state["research_prompt"]
        paper_id: str = state["paper_id"]

        # ── LLM call ────────────────────────────────────────────────────────
        outline = self._call_llm(research_prompt)

        # ── Initialize Visual Contract ──────────────────────────────────────
        contract = VisualContract(
            paper_id=paper_id,
            paper_title=outline.get("title", "Untitled"),
            research_prompt=research_prompt,
        )

        # Pre-register expected figures/tables from outline
        fig_counter = 0
        tbl_counter = 0
        for sec in outline.get("sections", []):
            for fig_desc in sec.get("expected_figures", []):
                fig_counter += 1
                contract.register_figure(FigureEntry(
                    figure_id=f"fig_{fig_counter}",
                    caption=fig_desc,
                    position=sec["section_id"],
                    semantic_commitment=fig_desc,
                ))
            for tbl_desc in sec.get("expected_tables", []):
                tbl_counter += 1
                contract.register_table(TableEntry(
                    table_id=f"tbl_{tbl_counter}",
                    caption=tbl_desc,
                    position=sec["section_id"],
                    columns=[],
                    data_semantics=tbl_desc,
                ))

        return {
            **state,
            "outline": outline,
            "contract": contract.model_dump(),
            "current_agent": "architect",
        }

    def _call_llm(self, prompt: str) -> dict:
        # Structured output schema matching SYSTEM_PROMPT output spec
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "abstract_summary": {"type": "string"},
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "section_id": {"type": "string"},
                            "title": {"type": "string"},
                            "purpose": {"type": "string"},
                            "key_points": {"type": "array", "items": {"type": "string"}},
                            "expected_figures": {"type": "array", "items": {"type": "string"}},
                            "expected_tables": {"type": "array", "items": {"type": "string"}},
                            "expected_equations": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["section_id", "title", "purpose", "key_points"],
                    },
                },
                "novelty_statement": {"type": "string"},
                "baseline_comparisons": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "sections"],
        }

        return llm_call(
            prompt=prompt,
            agent="architect",
            system_prompt=SYSTEM_PROMPT,
            json_schema=schema,
        )
