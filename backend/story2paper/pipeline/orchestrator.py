"""
LangGraph Pipeline Orchestrator
Story2Paper 的核心流水线：Architect → Writer (loop) → Evaluator → Refiner (loop) → END
"""

from __future__ import annotations
from typing import TypedDict
from langgraph.graph import StateGraph, END

from backend.story2paper.agents.architect import ArchitectAgent
from backend.story2paper.agents.writer import WriterAgent
from backend.story2paper.agents.evaluator import EvaluatorAgent
from backend.story2paper.agents.refiner import RefinerAgent


# ─── Pipeline State Schema ────────────────────────────────────────────────────

class PipelineState(TypedDict):
    paper_id: str
    research_prompt: str
    outline: dict | None
    contract: dict | None
    section_drafts: list
    current_section_index: int
    audit_results: list
    contract_violations: list
    pass_audit: bool
    revision_round: int
    writing_complete: bool
    refinement_complete: bool
    current_agent: str
    final_output: str | None


# ─── Build Graph ──────────────────────────────────────────────────────────────

def build_pipeline() -> StateGraph:
    architect = ArchitectAgent()
    writer = WriterAgent()
    evaluator = EvaluatorAgent()
    refiner = RefinerAgent()

    graph = StateGraph(PipelineState)

    # Nodes
    graph.add_node("architect", _wrap(architect))
    graph.add_node("writer", _wrap(writer))
    graph.add_node("evaluator", _wrap(evaluator))
    graph.add_node("refiner", _wrap(refiner))

    # Entry point
    graph.set_entry_point("architect")

    # Architect → Writer (once architect finishes, move to writer)
    graph.add_edge("architect", "writer")

    # Writer loops back to itself until all sections are written
    graph.add_conditional_edges(
        "writer",
        _writing_gate,
        {
            "continue": "writer",   # more sections to write → loop
            "done": "evaluator",    # all sections done → evaluate
        }
    )

    # Evaluator → conditional: pass → END; fail → refiner
    graph.add_conditional_edges(
        "evaluator",
        _audit_gate,
        {
            "pass": END,
            "refine": "refiner",
        }
    )

    # Refiner → Evaluator (re-audit after fixing)
    graph.add_edge("refiner", "evaluator")

    return graph.compile()


def _wrap(agent):
    """Wrap agent.run() so it conforms to (state) -> state."""
    def node(state: PipelineState) -> PipelineState:
        return agent.run(state)
    return node


def _writing_gate(state: PipelineState) -> str:
    """Route writer: keep looping if more sections, otherwise to evaluator."""
    if state.get("writing_complete", False):
        return "done"
    return "continue"


def _audit_gate(state: PipelineState) -> str:
    """Route evaluator: pass → END; fail (and under round limit) → refine."""
    if state.get("pass_audit", False):
        return "pass"
    if state.get("revision_round", 0) >= 2:
        return "pass"  # Force stop after 2 refinement rounds
    return "refine"


# ─── Singleton ────────────────────────────────────────────────────────────────

_pipeline_instance: StateGraph | None = None


def get_pipeline() -> StateGraph:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = build_pipeline()
    return _pipeline_instance
