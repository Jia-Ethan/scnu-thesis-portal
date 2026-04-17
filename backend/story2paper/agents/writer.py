"""
Writer Agent — 根据大纲和视觉契约，按 section 生成论文正文
"""

from __future__ import annotations
from typing import Any
import json
from .base import BaseAgent, AgentConfig
from backend.story2paper.shared.llm_router import llm_call


WRITER_SYSTEM_PROMPT = """You are the Writer Agent in a multi-agent academic paper generation system.

Your task: Given a section specification and the current Visual Contract, write the complete content for that section.

CONTEXT RULES:
- Write ONLY in academic prose — formal, precise, third-person
- Do not repeat content from other sections
- Reference figures/tables/equations by their registered IDs (e.g., Fig. 1, Table 2, Eq. 3)
- Track any new figures, tables, equations you introduce by adding entries to the Visual Contract
- Keep claims verifiable and cite existing work where appropriate

OUTPUT FORMAT — respond with valid JSON:
{
  "content": "Full section text in markdown...",
  "new_figures": [{"figure_id": "auto", "caption": "...", "semantic_commitment": "..."}],
  "new_tables": [{"table_id": "auto", "caption": "...", "columns": [...], "data_semantics": "..."}],
  "new_equations": [{"equation_id": "auto", "latex": "...", "description": "..."}],
  "new_claims": [{"claim_id": "auto", "claim_text": "...", "section": "current_section_id"}]
}
"""


class WriterAgent(BaseAgent):
    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig(name="writer", temperature=0.6))

    def run(self, state: dict) -> dict:
        outline: dict = state["outline"]
        contract: dict = state["contract"]
        sections = outline.get("sections", [])
        current_section_idx: int = state.get("current_section_index", 0)

        # Write current section
        if current_section_idx >= len(sections):
            return {**state, "current_agent": "writer", "writing_complete": True}

        section = sections[current_section_idx]
        result = self._write_section(section, contract, outline)

        # Store draft
        drafts = state.get("section_drafts", [])
        drafts.append({
            "section_id": section["section_id"],
            "title": section["title"],
            "content": result["content"],
        })

        # Merge new Visual Contract entries
        updated_contract = self._merge_contract_entries(contract, result)

        return {
            **state,
            "section_drafts": drafts,
            "contract": updated_contract,
            "current_section_index": current_section_idx + 1,
            "current_agent": "writer",
        }

    def _write_section(self, section: dict, contract: dict, outline: dict) -> dict:
        """Generate full content for one section."""
        prompt = self._build_section_prompt(section, contract, outline)
        return llm_call(
            prompt=prompt,
            agent="writer",
            system_prompt=WRITER_SYSTEM_PROMPT,
            json_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "new_figures": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "figure_id": {"type": "string"},
                                "caption": {"type": "string"},
                                "semantic_commitment": {"type": "string"},
                            },
                            "required": ["caption", "semantic_commitment"],
                        },
                    },
                    "new_tables": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "table_id": {"type": "string"},
                                "caption": {"type": "string"},
                                "columns": {"type": "array", "items": {"type": "string"}},
                                "data_semantics": {"type": "string"},
                            },
                            "required": ["caption", "columns", "data_semantics"],
                        },
                    },
                    "new_equations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "equation_id": {"type": "string"},
                                "latex": {"type": "string"},
                                "description": {"type": "string"},
                            },
                            "required": ["latex", "description"],
                        },
                    },
                    "new_claims": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "claim_id": {"type": "string"},
                                "claim_text": {"type": "string"},
                                "section": {"type": "string"},
                            },
                            "required": ["claim_text", "section"],
                        },
                    },
                },
                "required": ["content"],
            },
        )

    def _build_section_prompt(self, section: dict, contract: dict, outline: dict) -> str:
        title = outline.get("title", "")
        novelty = outline.get("novelty_statement", "")
        baselines = "\n".join(f"- {b}" for b in outline.get("baseline_comparisons", []))

        # Serialize relevant contract entries for this section
        sec_id = section["section_id"]
        figures = [f for f in contract.get("figures", []) if f.get("position") == sec_id]
        tables = [t for t in contract.get("tables", []) if t.get("position") == sec_id]

        prompt = f"""PAPER TITLE: {title}
NOVELTY: {novelty}
BASELINES TO COMPARE AGAINST:
{baselines}

CURRENT SECTION TO WRITE:
- Section ID: {section["section_id"]}
- Title: {section["title"]}
- Purpose: {section["purpose"]}
- Key Points to Cover:
{chr(10).join(f"  {i+1}. {pt}" for i, pt in enumerate(section.get("key_points", [])))}

VISUAL CONTRACT — Pre-registered Figures in this section:
{json.dumps(figures, indent=2, ensure_ascii=False)}

VISUAL CONTRACT — Pre-registered Tables in this section:
{json.dumps(tables, indent=2, ensure_ascii=False)}

FULL OUTLINE (for cross-section awareness):
{json.dumps(outline, indent=2, ensure_ascii=False)}

Write the complete section content now.
"""
        return prompt

    def _merge_contract_entries(self, contract: dict, result: dict) -> dict:
        """Merge new entries returned by Writer into the existing contract."""
        contract = dict(contract)  # shallow copy

        for fig in result.get("new_figures", []):
            # Auto-assign ID if not provided
            if fig.get("figure_id") == "auto" or not fig.get("figure_id"):
                fig["figure_id"] = f"fig_{len(contract.get("figures", [])) + 1}"
            contract.setdefault("figures", []).append(fig)

        for tbl in result.get("new_tables", []):
            if tbl.get("table_id") == "auto" or not tbl.get("table_id"):
                tbl["table_id"] = f"tbl_{len(contract.get("tables", [])) + 1}"
            contract.setdefault("tables", []).append(tbl)

        for eq in result.get("new_equations", []):
            if eq.get("equation_id") == "auto" or not eq.get("equation_id"):
                eq["equation_id"] = f"eq_{len(contract.get("equations", [])) + 1}"
            contract.setdefault("equations", []).append(eq)

        for claim in result.get("new_claims", []):
            if claim.get("claim_id") == "auto" or not claim.get("claim_id"):
                claim["claim_id"] = f"claim_{len(contract.get("claims", [])) + 1}"
            contract.setdefault("claims", []).append(claim)

        return contract
