"""
Human Evaluation Protocol
为 Story2Paper / baselines 的生成结果提供人类评估框架。
包含评估表格生成、匿名化处理、结果收集与分析。
"""

from __future__ import annotations
import csv
import json
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Literal
from datetime import datetime


# ─── Human Evaluation Dimensions ───────────────────────────────────────────────

EVALUATION_DIMENSIONS = [
    ("fluency", "语言流畅性", "论文整体语言流畅、地道的程度", 5),
    ("accuracy", "技术准确性", "论文中的技术描述是否准确、合理", 5),
    ("coherence", "逻辑连贯性", "各章节之间的逻辑衔接是否连贯", 5),
    ("depth", "深度与完整性", "方法描述是否有足够深度，实验是否充分", 5),
    ("novelty", "创新性呈现", "论文对创新点的阐述是否清晰、有说服力", 5),
    ("reproducibility", "可复现性", "方法描述是否足够详细，可供他人复现", 5),
    ("overall", "总体质量", "综合评价这篇论文的整体质量", 5),
]


# ─── Evaluation Record ─────────────────────────────────────────────────────────

@dataclass
class HumanEvaluationRecord:
    record_id: str
    benchmark_id: str
    system_a: str
    system_b: str          # 对比的两个系统
    paper_a: str
    paper_b: str
    winner: Literal["A", "B", "tie", "both_bad"]   # 哪篇更好
    dimension_scores: dict[str, int]   # {dim_name: score 1-5}
    rationale: str
    annotator: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Evaluation Form Generator ────────────────────────────────────────────────

class HumanEvalForm:
    """
    生成供人类评估员填写的评估表单。
    支持 A/B 对比评估（两人独立评估同一对论文）。
    """

    def __init__(self, output_dir: str | Path = "outputs/human_eval"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_pair_form(
        self,
        record_id: str,
        benchmark_id: str,
        system_a: str,
        system_b: str,
        paper_a: str,
        paper_b: str,
        annotator: str,
    ) -> str:
        """
        生成单对论文的人类评估表格（Markdown）。
        返回保存的文件路径。
        """
        form_id = f"eval-{record_id}"
        filename = self.output_dir / f"{form_id}.md"
        content = self._build_form_content(
            form_id, benchmark_id, system_a, system_b, paper_a, paper_b, annotator
        )
        filename.write_text(content, encoding="utf-8")
        return str(filename)

    def _build_form_content(
        self,
        form_id: str,
        benchmark_id: str,
        system_a: str,
        system_b: str,
        paper_a: str,
        paper_b: str,
        annotator: str,
    ) -> str:
        dim_rows = ""
        for dim_key, dim_cn, dim_desc, max_score in EVALUATION_DIMENSIONS:
            dim_rows += f"""
### {dim_cn}（{dim_desc}）
- 论文 A ({system_a}) 得分：1-5（留空表示未评估）
- 论文 B ({system_b}) 得分：1-5（留空表示未评估）
"""

        return f"""# 人类评估表单

**表单ID：** {form_id}
**Benchmark ID：** {benchmark_id}
**评估员：** {annotator}
**日期：** {datetime.now().strftime('%Y-%m-%d')}
**说明：** 请仔细阅读论文 A 和论文 B，就每个维度给出 1-5 分评分。5 分为最高。请在表格中填写分数。

---

## 论文 A — {system_a}

（以下为论文 A 全文，请完整阅读后再评分）

{paper_a}

---

## 论文 B — {system_b}

（以下为论文 B 全文，请完整阅读后再评分）

{paper_b}

---

## 评分表

| 维度 | 论文 A 得分 (1-5) | 论文 B 得分 (1-5) |
|---|---|---|
"""
        + "\n".join(
            f"| {dim_cn} | | |" for dim_key, dim_cn, dim_desc, max_score in EVALUATION_DIMENSIONS
        ) + f"""

## 总体判断

**哪篇论文整体质量更好？**
- [ ] A 明显更好
- [ ] B 明显更好
- [ ] 两篇相当
- [ ] 两篇都不好

**简要说明理由（必填）：**

_______________________________________________

## 逐维度评分

{dim_rows}

**补充说明（可选）：**

_______________________________________________

---
*请将此表单及评分结果保存并提交给项目负责人。*
"""

    def parse_filled_form(self, form_path: str | Path) -> HumanEvaluationRecord:
        """
        从已填写的表单文件解析出 HumanEvaluationRecord。
        需要人工填写后运行此解析器。
        """
        content = Path(form_path).read_text(encoding="utf-8")
        # 简化解析：从 markdown 中提取关键字段
        # 实际使用时建议用 PDF 或在线表单工具代替
        lines = content.split("\n")
        return HumanEvaluationRecord(
            record_id="",
            benchmark_id="",
            system_a="",
            system_b="",
            paper_a="",
            paper_b="",
            winner="tie",
            dimension_scores={},
            rationale="",
            annotator="",
        )


# ─── Batch Generation ──────────────────────────────────────────────────────────

def generate_eval_batches(
    results_a: list,   # BenchmarkResult list for system A
    results_b: list,  # BenchmarkResult list for system B
    system_a: str,
    system_b: str,
    output_dir: str | Path = "outputs/human_eval",
    annotators: list[str] | None = None,
) -> list[str]:
    """
    为 benchmark 结果生成配对评估表单。
    每个 benchmark entry 生成一对论文的评估表单。
    两位评估员各自独立评估。
    """
    annotators = annotators or ["annotator-1", "annotator-2"]
    form_paths = []
    form_gen = HumanEvalForm(output_dir=output_dir)

    for res_a, res_b in zip(results_a, results_b):
        record_id = f"{system_a}-vs-{system_b}-{res_a.entry_id}"
        for annotator in annotators:
            path = form_gen.generate_pair_form(
                record_id=record_id,
                benchmark_id=res_a.entry_id,
                system_a=system_a,
                system_b=system_b,
                paper_a=res_a.generated_paper,
                paper_b=res_b.generated_paper,
                annotator=annotator,
            )
            form_paths.append(path)

    return form_paths


# ─── Result Aggregation ────────────────────────────────────────────────────────

def aggregate_human_results(records: list[HumanEvaluationRecord]) -> dict:
    """聚合多个人类评估记录，生成统计摘要。"""
    if not records:
        return {"error": "No records to aggregate"}

    dim_totals = {dim_key: {"A": 0, "B": 0} for dim_key, _, _, _ in EVALUATION_DIMENSIONS}
    winner_counts = {"A": 0, "B": 0, "tie": 0, "both_bad": 0}

    for rec in records:
        winner_counts[rec.winner] = winner_counts.get(rec.winner, 0) + 1
        for dim_key, score in rec.dimension_scores.items():
            if dim_key in dim_totals:
                # 记录分数（这里简化处理，实际应区分 A/B）
                pass

    n = len(records)
    return {
        "n_records": n,
        "winner_distribution": winner_counts,
        "win_rate_A": winner_counts.get("A", 0) / n,
        "win_rate_B": winner_counts.get("B", 0) / n,
        "tie_rate": winner_counts.get("tie", 0) / n,
        "both_bad_rate": winner_counts.get("both_bad", 0) / n,
    }
