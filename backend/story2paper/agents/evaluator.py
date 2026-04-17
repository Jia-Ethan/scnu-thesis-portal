"""
Evaluator Agent — 20维度质量审计，检查与视觉契约的一致性
"""

from __future__ import annotations
from typing import Any
import json
from .base import BaseAgent, AgentConfig
from backend.story2paper.shared.llm_router import llm_call


# ─── 20 Audit Dimensions ─────────────────────────────────────────────────────

AUDIT_SYSTEM_PROMPT = """You are the Evaluator Agent in a multi-agent academic paper generation system.

Your task: Given the full draft and Visual Contract, audit the paper across 20 dimensions and produce a structured audit report.

Each dimension is rated: ok | warning | error
- error: critical flaw that must be fixed before the paper can proceed
- warning: quality degradation or minor inconsistency
- ok: meets standard

Also check Visual Contract consistency:
- All registered figures/tables must have matching captions in the text
- Claims must not contradict each other across sections
- Citation references must match the reference list

OUTPUT FORMAT — respond with valid JSON:
{
  "audit_results": [
    {
      "dimension": "dimension_name",
      "severity": "ok | warning | error",
      "message": "Specific finding with examples from the text",
      "location": "section_id or global"
    }
  ],
  "contract_violations": [
    {
      "type": "figure_caption_mismatch | claim_contradiction | citation_mismatch | ...",
      "description": "...",
      "affected_elements": ["fig_1", "claim_3"]
    }
  ],
  "overall_pass": true | false
}
"""


class AuditResult:
    def __init__(self, dimension: str, severity: str, message: str, location: str = "global"):
        self.dimension = dimension
        self.severity = severity  # error | warning | ok
        self.message = message
        self.location = location


class EvaluatorAgent(BaseAgent):
    def __init__(self, config: AgentConfig | None = None):
        super().__init__(config or AgentConfig(name="evaluator", temperature=0.3))

    def run(self, state: dict) -> dict:
        drafts: list = state.get("section_drafts", [])
        contract: dict = state["contract"]
        outline: dict = state["outline"]

        audit_results, contract_violations, overall_pass = self._audit_all(drafts, contract, outline)

        return {
            **state,
            "audit_results": [
                {
                    "dimension": r.dimension,
                    "severity": r.severity,
                    "message": r.message,
                    "location": r.location,
                }
                for r in audit_results
            ],
            "contract_violations": contract_violations,
            "pass_audit": overall_pass,
            "current_agent": "evaluator",
        }

    def _audit_all(self, drafts: list, contract: dict, outline: dict) -> tuple:
        """Run full 20-dimension audit via LLM."""
        # Assemble full paper text
        paper_text = self._assemble_paper(drafts, outline)

        prompt = self._build_audit_prompt(paper_text, drafts, contract, outline)
        result = llm_call(
            prompt=prompt,
            agent="evaluator",
            system_prompt=AUDIT_SYSTEM_PROMPT,
            json_schema={
                "type": "object",
                "properties": {
                    "audit_results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "dimension": {"type": "string"},
                                "severity": {"type": "string", "enum": ["ok", "warning", "error"]},
                                "message": {"type": "string"},
                                "location": {"type": "string"},
                            },
                            "required": ["dimension", "severity", "message"],
                        },
                    },
                    "contract_violations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "description": {"type": "string"},
                                "affected_elements": {"type": "array", "items": {"type": "string"}},
                            },
                            "required": ["type", "description"],
                        },
                    },
                    "overall_pass": {"type": "boolean"},
                },
                "required": ["audit_results", "overall_pass"],
            },
        )

        audit_results = [
            AuditResult(
                dimension=r["dimension"],
                severity=r["severity"],
                message=r["message"],
                location=r.get("location", "global"),
            )
            for r in result.get("audit_results", [])
        ]
        contract_violations = result.get("contract_violations", [])
        overall_pass = result.get("overall_pass", False)

        return audit_results, contract_violations, overall_pass

    def _assemble_paper(self, drafts: list, outline: dict) -> str:
        title = outline.get("title", "Untitled")
        sections = []
        for draft in drafts:
            sections.append(f"## {draft['title']}\n{draft['content']}")
        return f"# {title}\n\n" + "\n\n".join(sections)

    def _build_audit_prompt(self, paper_text: str, drafts: list, contract: dict, outline: dict) -> str:
        return f"""AUDIT THE FOLLOWING PAPER DRAFT:

===
{paper_text}
===

VISUAL CONTRACT (figures, tables, claims, citations to check against):
{json.dumps(contract, indent=2, ensure_ascii=False)}

PAPER OUTLINE (expected structure):
{json.dumps(outline, indent=2, ensure_ascii=False)}

AUDIT DIMENSIONS TO CHECK:
1. logical_flow: Does the paper follow a logical progression?
2. section_cohesion: Does each section have a clear purpose and stay on-topic?
3. abstract_completeness: Does abstract summarize motivation, method, results, contributions?
4. claim_consistency: Do claims agree with each other across sections?
5. causal_reasoning: Are cause-effect relationships logically sound?
6. circular_argument: Does the paper avoid circular reasoning?
7. figure_caption_match: Do figure captions match the described content?
8. table_data_alignment: Are table headers and data semantically aligned?
9. equation_description_match: Do equation descriptions match their mathematical content?
10. academic_tone: Is the writing formal and objective?
11. passive_active_voice: Is voice appropriate (mostly passive for methods)?
12. terminology_consistency: Are key terms used consistently throughout?
13. citation_presence: Are key claims supported by citations?
14. citation_alignment: Do in-text citations match the reference list?
15. reference_completeness: Are all cited works listed in the reference section?
16. motivation_clarity: Is the research motivation clearly articulated?
17. novelty_articulation: Is the paper's novelty clearly stated and differentiated from baselines?
18. limitation_honesty: Are limitations discussed honestly?
19. figure_caption_alignment: [see figure_caption_match]
20. table_semantic_consistency: [see table_data_alignment]

Perform the full audit now.
"""
