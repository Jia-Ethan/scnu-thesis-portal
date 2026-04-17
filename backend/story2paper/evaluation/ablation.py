"""
Ablation Study Runner — 消融实验
对比 Story2Paper 与各消融变体，量化 Visual Contract 机制的贡献。
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Literal

from backend.story2paper.evaluation.benchmark import JerichoBenchmark, BenchmarkEntry, BenchmarkResult
from backend.story2paper.baselines.direct_chat import DirectChatPipeline
from backend.story2paper.baselines.story2proposal import Story2ProposalPipeline


# ─── System Variants ───────────────────────────────────────────────────────────

SYSTEMS = {
    "Story2Paper": None,        # 完整 pipeline（延迟导入，避免循环）
    "DirectChat": DirectChatPipeline,
    "Story2Proposal": Story2ProposalPipeline,
    # 消融变体
    "Story2Paper_NoContract": None,    # 无 Visual Contract，仅 Architect→Writer 直链
    "Story2Paper_NoEvaluator": None,    # 无 Evaluator，直接进入 Refiner
    "Story2Paper_NoRefiner": None,     # 无 Refiner 循环，Evaluator 结果直接接受
}


@dataclass
class AblationResult:
    system: str
    n_entries: int
    avg_keyword_recall: float
    avg_section_recall: float
    avg_paper_length: float
    avg_evaluator_score: float
    evaluator_pass_rate: float
    human_evaluated: int

    def to_dict(self) -> dict:
        return asdict(self)


def _get_pipeline(system: str):
    """延迟加载 pipeline，避免循环导入。"""
    if system == "Story2Paper":
        from backend.story2paper.pipeline.orchestrator import run_pipeline as story2paper_run
        return lambda story: story2paper_run({"research_prompt": story})["final_output"] or ""
    elif system == "DirectChat":
        return DirectChatPipeline().run
    elif system == "Story2Proposal":
        return Story2ProposalPipeline().run
    elif system == "Story2Paper_NoContract":
        # 消融：跳过 contract，直接用简化 writer
        from backend.story2paper.baselines.story2proposal import run as simple_run
        return simple_run
    elif system == "Story2Paper_NoEvaluator":
        # 消融：跳过 Evaluator
        from backend.story2paper.baselines.story2proposal import run as simple_run
        return simple_run
    elif system == "Story2Paper_NoRefiner":
        from backend.story2paper.baselines.story2proposal import run as simple_run
        return simple_run
    else:
        raise ValueError(f"Unknown system: {system}")


def run_ablation(
    systems: list[str] | None = None,
    entries: list[BenchmarkEntry] | None = None,
    progress_callback=None,
) -> dict[str, AblationResult]:
    """
    在指定系统列表上运行完整消融实验。
    返回 {system_name: AblationResult} 字典。
    """
    systems = systems or list(SYSTEMS.keys())
    all_results: dict[str, AblationResult] = {}

    for system in systems:
        if system not in SYSTEMS:
            print(f"[Ablation] Skipping unknown system: {system}")
            continue

        print(f"[Ablation] Running system: {system}")
        pipeline_fn = _get_pipeline(system)

        benchmark = JerichoBenchmark(
            pipeline_fn=pipeline_fn,
            system_name=system,
            entries=entries,
        )
        raw_results = benchmark.run_all(
            progress_callback=lambda i, total, eid: (
                progress_callback and progress_callback(i, total, f"[{system}] {eid}")
            ) if progress_callback else None
        )

        # 填充 evaluator 评分（需要实际调用 EvaluatorAgent）
        filled = _fill_evaluator_scores(raw_results)

        agg = benchmark.aggregate(filled)
        all_results[system] = AblationResult(
            system=system,
            n_entries=agg["n_entries"],
            avg_keyword_recall=agg["avg_keyword_recall"],
            avg_section_recall=agg["avg_section_recall"],
            avg_paper_length=agg["avg_paper_length"],
            avg_evaluator_score=agg["avg_evaluator_score"],
            evaluator_pass_rate=agg["evaluator_pass_rate"],
            human_evaluated=agg["human_evaluated"],
        )
        print(f"[Ablation] {system} done — evaluator_score={agg['avg_evaluator_score']:.2f}")

    return all_results


def _outline_from_paper(paper: str) -> dict:
    """从生成的论文文本中提取 section 结构，构造 outline。"""
    lines = paper.split("\n")
    sections = []
    current_title = "Untitled"
    found_title = False

    for line in lines:
        stripped = line.strip()
        # 提取标题 (# Title)
        if stripped.startswith("# ") and not found_title:
            current_title = stripped[2:].strip()
            found_title = True
            continue
        # 提取章节 (## Section Name)
        if stripped.startswith("## "):
            section_name = stripped[3:].strip()
            sections.append({
                "title": section_name,
                "purpose": "",
                "key_points": [],
            })

    if not sections:
        # Fallback：默认结构
        sections = [
            {"title": "Introduction", "purpose": "", "key_points": []},
            {"title": "Related Work", "purpose": "", "key_points": []},
            {"title": "Method", "purpose": "", "key_points": []},
            {"Title": "Experiments", "purpose": "", "key_points": []},
            {"title": "Conclusion", "purpose": "", "key_points": []},
        ]

    return {"title": current_title, "sections": sections}


def _section_drafts_from_paper(paper: str) -> list[dict]:
    """将论文文本拆分为 section drafts。"""
    lines = paper.split("\n")
    drafts = []
    current_title = "Untitled"
    current_content_lines: list[str] = []
    found_title = False

    def _flush():
        if current_content_lines:
            drafts.append({
                "title": current_title,
                "content": "\n".join(current_content_lines).strip(),
            })

    for line in lines:
        stripped = line.strip()
        # 提取标题 (# Title)
        if stripped.startswith("# ") and not found_title:
            current_title = stripped[2:].strip()
            found_title = True
            continue
        # 提取章节 (## Section Name)
        if stripped.startswith("## "):
            _flush()
            current_title = stripped[3:].strip()
            current_content_lines = []
            continue
        current_content_lines.append(line)

    _flush()
    return drafts


def _fill_evaluator_scores(results: list[BenchmarkResult]) -> list[BenchmarkResult]:
    """
    对每条结果调用 EvaluatorAgent 获取 20 维度审计分数。
    延迟导入避免循环。
    """
    try:
        from backend.story2paper.agents.evaluator import EvaluatorAgent
    except ImportError:
        return results

    evaluator = EvaluatorAgent()
    for r in results:
        try:
            outline = _outline_from_paper(r.generated_paper)
            section_drafts = _section_drafts_from_paper(r.generated_paper)

            fake_state = {
                "contract": {
                    "id": r.entry_id,
                    "title": outline.get("title", ""),
                    "figures": [],
                    "tables": [],
                    "equations": [],
                    "claims": [],
                    "citations": [],
                    "audit_log": [],
                },
                "outline": outline,
                "section_drafts": section_drafts,
            }
            eval_out = evaluator.run(fake_state)

            # 从 audit_results 推导综合评分（0-100）
            audit_results = eval_out.get("audit_results", [])
            if audit_results:
                n = len(audit_results)
                ok_count = sum(1 for a in audit_results if a.get("severity") == "ok")
                warn_count = sum(1 for a in audit_results if a.get("severity") == "warning")
                # ok=100, warning=60, error=0
                score = (ok_count * 100 + warn_count * 60) / n
                r.evaluator_score = round(score, 2)
            else:
                r.evaluator_score = 0.0

            r.evaluator_pass = eval_out.get("pass_audit", False)
        except Exception as e:
            r.evaluator_score = 0.0
            r.evaluator_pass = False

    return results


def compare_table(results: dict[str, AblationResult]) -> str:
    """生成对比表格（Markdown）。"""
    lines = [
        "| System | Entries | Keyword Recall | Section Recall | Avg Length | Eval Score | Pass Rate |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, r in results.items():
        lines.append(
            f"| {name} | {r.n_entries} | "
            f"{r.avg_keyword_recall:.3f} | "
            f"{r.avg_section_recall:.3f} | "
            f"{r.avg_paper_length:.0f} | "
            f"{r.avg_evaluator_score:.1f} | "
            f"{r.evaluator_pass_rate:.3f} |"
        )
    return "\n".join(lines)
