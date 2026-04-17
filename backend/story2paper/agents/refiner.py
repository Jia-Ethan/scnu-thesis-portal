"""
Refiner Agent — 根据 Evaluator 审计报告修复问题，更新视觉契约
"""

from __future__ import annotations
from typing import Any
import json
from .base import BaseAgent, AgentConfig
from backend.story2paper.shared.llm_router import llm_call


REFINER_SYSTEM_PROMPT = """You are the Refiner Agent in a multi-agent academic paper generation system.

Your task: Given the Evaluator's audit report, fix all error-severity issues and as many warning-severity issues as possible in the paper drafts.

CRITICAL RULES:
- Only fix issues flagged by the Evaluator — do not rewrite sections unnecessarily
- Maintain the paper's overall structure and argument flow
- Preserve all figure/table references already in the text
- If a claim is contradicted, resolve by clarifying the weaker claim or adding appropriate hedging
- Update Visual Contract entries if fixing figure/table/citation-related issues

OUTPUT FORMAT — respond with valid JSON:
{
  "revised_drafts": [
    {
      "section_id": "sec_1",
      "section_title": "...",
      "original_content": "...",
      "revised_content": "... (full revised section content)"
    }
  ],
  "contract_updates": {
    "updated_figures": [...],
    "updated_claims": [...],
    "updated_citations": [...]
  },
  "fixed_dimensions": ["claim_consistency", "figure_caption_match", ...],
  "unfixed_reasons": ["dimension_name: reason why it could not be fixed in this round", ...]
}
"""


class RefinerAgent(BaseAgent):
    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig(name="refiner", temperature=0.5))

    def run(self, state: dict) -> dict:
        audit_results: list = state["audit_results"]
        contract_violations: list = state.get("contract_violations", [])
        section_drafts: list = state["section_drafts"]
        contract: dict = state["contract"]

        revision_round: int = state.get("revision_round", 0)
        if revision_round >= 2:
            return {**state, "current_agent": "refiner", "refinement_complete": True}

        # Filter to error + warning severity only
        issues_to_fix = [
            r for r in audit_results
            if r.get("severity") in ("error", "warning")
        ]

        if not issues_to_fix:
            return {**state, "current_agent": "refiner", "refinement_complete": True}

        fixes = self._fix_issues(issues_to_fix, contract_violations, section_drafts, contract)

        return {
            **state,
            "section_drafts": fixes["revised_drafts"],
            "contract": {**contract, **fixes.get("contract_updates", {})},
            "revision_round": revision_round + 1,
            "current_agent": "refiner",
        }

    def _fix_issues(
        self,
        audit_results: list,
        contract_violations: list,
        drafts: list,
        contract: dict,
    ) -> dict:
        prompt = self._build_fix_prompt(audit_results, contract_violations, drafts, contract)

        return llm_call(
            prompt=prompt,
            agent="refiner",
            system_prompt=REFINER_SYSTEM_PROMPT,
            json_schema={
                "type": "object",
                "properties": {
                    "revised_drafts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "section_id": {"type": "string"},
                                "section_title": {"type": "string"},
                                "original_content": {"type": "string"},
                                "revised_content": {"type": "string"},
                            },
                            "required": ["section_id", "revised_content"],
                        },
                    },
                    "contract_updates": {"type": "object"},
                    "fixed_dimensions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "unfixed_reasons": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["revised_drafts"],
            },
        )

    def _build_fix_prompt(
        self,
        audit_results: list,
        contract_violations: list,
        drafts: list,
        contract: dict,
    ) -> str:
        audit_text = "\n".join(
            f"- [{r['severity'].upper()}] {r['dimension']}: {r['message']} (location: {r.get('location', 'global')})"
            for r in audit_results
        )
        violations_text = "\n".join(
            f"- {v['type']}: {v['description']} → affects {v.get('affected_elements', [])}"
            for v in contract_violations
        ) if contract_violations else "None"

        drafts_text = "\n\n".join(
            f"=== {d['section_id']}: {d['title']} ===\n{d['content']}"
            for d in drafts
        )

        return f"""FIX THE FOLLOWING AUDIT ISSUES IN THE PAPER DRAFTS:

AUDIT FINDINGS:
{audit_text}

CONTRACT VIOLATIONS:
{violations_text}

CURRENT PAPER DRAFTS:
{drafts_text}

VISUAL CONTRACT:
{json.dumps(contract, indent=2, ensure_ascii=False)}

Fix each issue by revising the relevant sections. Output the full revised content for any section you modify.
"""
