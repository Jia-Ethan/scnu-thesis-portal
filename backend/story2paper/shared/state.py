"""
Visual Contract Registry — 全局共享状态的核心数据模型
Single source of truth for all agents
"""

from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ─── Entry Types ─────────────────────────────────────────────────────────────

class FigureEntry(BaseModel):
    figure_id: str                           # e.g. "fig_1"
    caption: str                             # full caption text
    position: str                            # section name, e.g. "sec_3_1"
    semantic_commitment: str                  # what the figure claims to show
    referred_by: list[str] = Field(default_factory=list)  # claim IDs
    status: str = "draft"                    # draft | confirmed | revised


class TableEntry(BaseModel):
    table_id: str
    caption: str
    position: str
    columns: list[str]
    data_semantics: str
    referred_by: list[str] = Field(default_factory=list)
    status: str = "draft"


class EquationEntry(BaseModel):
    equation_id: str                         # e.g. "eq_1"
    latex: str
    description: str
    referred_by: list[str] = Field(default_factory=list)
    status: str = "draft"


class ClaimEntry(BaseModel):
    claim_id: str
    claim_text: str
    section: str
    citations: list[str] = Field(default_factory=list)  # ref IDs
    contradicted_by: list[str] = Field(default_factory=list)
    status: str = "pending"                 # pending | confirmed | contradicted | resolved


class CitationEntry(BaseModel):
    ref_id: str                              # e.g. "[1]"
    full_reference: str
    semantic_context: str                    # in what context is this cited
    used_by_claims: list[str] = Field(default_factory=list)


class AuditEntry(BaseModel):
    timestamp: str
    agent: str                               # architect | writer | evaluator | refiner
    action: str
    details: str
    result: str                              # ok | warning | error


# ─── Visual Contract ────────────────────────────────────────────────────────

class VisualContract(BaseModel):
    paper_id: str
    paper_title: str
    research_prompt: str                     # original user input
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    figures: list[FigureEntry] = Field(default_factory=list)
    tables: list[TableEntry] = Field(default_factory=list)
    equations: list[EquationEntry] = Field(default_factory=list)
    claims: list[ClaimEntry] = Field(default_factory=list)
    citations: list[CitationEntry] = Field(default_factory=list)

    audit_log: list[AuditEntry] = Field(default_factory=list)

    # ─── Convenience helpers ────────────────────────────────────────────────

    def register_figure(self, figure: FigureEntry) -> None:
        self.figures.append(figure)
        self._log("writer", f"registered_figure:{figure.figure_id}", "ok")

    def register_table(self, table: TableEntry) -> None:
        self.tables.append(table)
        self._log("writer", f"registered_table:{table.table_id}", "ok")

    def register_equation(self, eq: EquationEntry) -> None:
        self.equations.append(eq)
        self._log("writer", f"registered_equation:{eq.equation_id}", "ok")

    def register_claim(self, claim: ClaimEntry) -> None:
        self.claims.append(claim)
        self._log("writer", f"registered_claim:{claim.claim_id}", "ok")

    def register_citation(self, citation: CitationEntry) -> None:
        self.citations.append(citation)
        self._log("writer", f"registered_citation:{citation.ref_id}", "ok")

    def update_figure_status(self, figure_id: str, status: str) -> None:
        for fig in self.figures:
            if fig.figure_id == figure_id:
                fig.status = status
                self._log("evaluator", f"figure_status_update:{figure_id}", status)
                break

    def flag_contradiction(self, claim_id: str, contradicting_id: str) -> None:
        for claim in self.claims:
            if claim.claim_id == claim_id:
                claim.contradicted_by.append(contradicting_id)
                claim.status = "contradicted"
                self._log("evaluator", f"flag_contradiction:{claim_id}", "error")
                break

    def _log(self, agent: str, action: str, result: str, details: str = "") -> None:
        self.audit_log.append(AuditEntry(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            action=action,
            details=details,
            result=result,
        ))
