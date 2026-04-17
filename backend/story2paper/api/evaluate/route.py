"""
API Routes — Evaluation
POST /api/evaluate/benchmark  运行完整 benchmark
POST /api/evaluate/ablation   运行消融实验
GET  /api/evaluate/results     获取历史结果
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from backend.story2paper.evaluation.benchmark import load_benchmark, JerichoBenchmark
from backend.story2paper.evaluation.ablation import run_ablation, compare_table

router = APIRouter(prefix="/api/evaluate", tags=["evaluation"])


# ─── Request / Response Models ─────────────────────────────────────────────────

class BenchmarkRunRequest(BaseModel):
    system: str           # "Story2Paper" | "DirectChat" | "Story2Proposal"
    domains: list[str] | None = None
    difficulty: str | None = None   # "easy" | "medium" | "hard"


class AblationRunRequest(BaseModel):
    systems: list[str] | None = None


class BenchmarkResultItem(BaseModel):
    entry_id: str
    keyword_recall: float
    section_recall: float
    paper_length: int
    evaluator_score: float
    evaluator_pass: bool


class BenchmarkRunResponse(BaseModel):
    system: str
    n_entries: int
    avg_keyword_recall: float
    avg_section_recall: float
    avg_paper_length: float
    avg_evaluator_score: float
    evaluator_pass_rate: float
    details: list[BenchmarkResultItem]


class AblationResponse(BaseModel):
    comparison_table: str
    results: dict


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_pipeline_fn(system: str):
    if system == "Story2Paper":
        from backend.story2paper.pipeline.orchestrator import run_pipeline
        return lambda story: run_pipeline({"research_prompt": story})["final_output"] or ""
    elif system == "DirectChat":
        from backend.story2paper.baselines.direct_chat import run
        return run
    elif system == "Story2Proposal":
        from backend.story2paper.baselines.story2proposal import run
        return run
    else:
        raise ValueError(f"Unknown system: {system}")


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/benchmark", response_model=BenchmarkRunResponse)
async def run_benchmark(req: BenchmarkRunRequest):
    """在 Jericho benchmark 上运行指定系统。"""
    from backend.story2paper.evaluation.ablation import _fill_evaluator_scores

    entries = load_benchmark()
    if req.domains:
        entries = [e for e in entries if e.domain in req.domains]
    if req.difficulty:
        entries = [e for e in entries if e.difficulty == req.difficulty]

    pipeline_fn = _get_pipeline_fn(req.system)
    benchmark = JerichoBenchmark(pipeline_fn=pipeline_fn, system_name=req.system, entries=entries)

    results = benchmark.run_all()
    filled = _fill_evaluator_scores(results)
    agg = benchmark.aggregate(filled)

    return BenchmarkRunResponse(
        system=req.system,
        n_entries=agg["n_entries"],
        avg_keyword_recall=round(agg["avg_keyword_recall"], 4),
        avg_section_recall=round(agg["avg_section_recall"], 4),
        avg_paper_length=int(agg["avg_paper_length"]),
        avg_evaluator_score=round(agg["avg_evaluator_score"], 2),
        evaluator_pass_rate=round(agg["evaluator_pass_rate"], 4),
        details=[
            BenchmarkResultItem(
                entry_id=r.entry_id,
                keyword_recall=round(r.keyword_recall, 4),
                section_recall=round(r.section_recall, 4),
                paper_length=r.paper_length,
                evaluator_score=round(r.evaluator_score, 2),
                evaluator_pass=r.evaluator_pass,
            )
            for r in filled
        ],
    )


@router.post("/ablation", response_model=AblationResponse)
async def run_ablation_study(req: AblationRunRequest):
    """运行消融实验。"""
    results = run_ablation(systems=req.systems)
    table = compare_table(results)

    return AblationResponse(
        comparison_table=table,
        results={name: r.to_dict() for name, r in results.items()},
    )


@router.get("/benchmark/entries")
async def list_benchmark_entries():
    """列出所有 benchmark 条目（供前端展示）。"""
    entries = load_benchmark()
    return [
        {
            "id": e.id,
            "domain": e.domain,
            "difficulty": e.difficulty,
            "story_preview": e.story[:100] + "...",
            "expected_keywords": e.expected_keywords,
            "min_sections": e.min_sections,
        }
        for e in entries
    ]
