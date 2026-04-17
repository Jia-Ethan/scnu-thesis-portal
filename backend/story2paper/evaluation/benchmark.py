"""
Jericho-Style Benchmark for Story2Paper
参照 Jericho（Marasovic et al. 2022）风格构建：
给定一个 research story/prompt，评估 LLM 生成的论文在多个维度的质量。
"""

from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Literal


# ─── Benchmark Entry ──────────────────────────────────────────────────────────

@dataclass
class BenchmarkEntry:
    """单条 benchmark 数据。"""
    id: str                          # 唯一标识
    story: str                       # 输入的故事/研究方向描述
    domain: str                      # 领域：AI/ML/NLP/HCI/Systems
    expected_keywords: list[str]    # 期望出现的关键词（用于 recall 粗估）
    min_sections: list[str]         # 期望的最低 sections 列表
    difficulty: Literal["easy", "medium", "hard"]  # 难度
    ground_truth_summary: str | None = None  # 参考摘要（可选）

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Default Jericho Benchmark Dataset ────────────────────────────────────────
# 10 条，覆盖不同领域和难度

JERICHO_BENCHMARK: list[dict] = [
    {
        "id": "jericho-001",
        "story": (
            "A researcher observed that large language models tend to hallucinate "
            "facts when asked about obscure historical events, especially in languages "
            "other than English. She proposes a method called FactualAnchor that "
            "uses Wikipedia as a grounding source during generation."
        ),
        "domain": "NLP",
        "expected_keywords": ["hallucination", "grounding", "Wikipedia", "factual", "retrieval"],
        "min_sections": ["Introduction", "Related Work", "Method", "Experiment", "Conclusion"],
        "difficulty": "medium",
        "ground_truth_summary": None,
    },
    {
        "id": "jericho-002",
        "story": (
            "Multi-agent reinforcement learning systems often suffer from credit assignment "
            "problems when agents must cooperate on sparse reward tasks. We propose "
            "CreditFlow, a differentiable communication channel that propagates reward "
            "signals across agent boundaries."
        ),
        "domain": "ML",
        "expected_keywords": ["MARL", "credit assignment", "multi-agent", "sparse reward", "communication"],
        "min_sections": ["Introduction", "Background", "Method", "Experiments", "Related Work", "Conclusion"],
        "difficulty": "hard",
        "ground_truth_summary": None,
    },
    {
        "id": "jericho-003",
        "story": (
            "User studies show that code autocomplete suggestions are most helpful when "
            "they match the developer's coding style. Current tools use generic language "
            "models. We fine-tune a personal style adapter on each developer's commit history."
        ),
        "domain": "SE",
        "expected_keywords": ["autocomplete", "style", "fine-tuning", "personalization", "code"],
        "min_sections": ["Introduction", "Motivation", "Method", "Evaluation", "Conclusion"],
        "difficulty": "easy",
        "ground_truth_summary": None,
    },
    {
        "id": "jericho-004",
        "story": (
            "Graph neural networks fail to capture long-range dependencies in molecular graphs "
            "because message passing is limited to k-hop neighborhoods. We propose "
            "GraphTransformer with global attention over all nodes simultaneously."
        ),
        "domain": "ML",
        "expected_keywords": ["GNN", "graph", "long-range", "attention", "molecular"],
        "min_sections": ["Introduction", "Background", "Method", "Experiments", "Conclusion"],
        "difficulty": "medium",
        "ground_truth_summary": None,
    },
    {
        "id": "jericho-005",
        "story": (
            "Video captioning models often produce generic descriptions that miss "
            "domain-specific details. A radiology department wants to generate structured "
            "reports from X-ray videos with medical terminology."
        ),
        "domain": "HCI",
        "expected_keywords": ["video captioning", "radiology", "structured report", "medical", "domain-specific"],
        "min_sections": ["Introduction", "Related Work", "Method", "Experiments", "Conclusion"],
        "difficulty": "medium",
        "ground_truth_summary": None,
    },
    {
        "id": "jericho-006",
        "story": (
            "Distributed training of large models suffers from slow convergence when "
            "using synchronous SGD due to stragglers. We design an asynchronous gradient "
            "accumulation scheme with bounded staleness guarantees."
        ),
        "domain": "Systems",
        "expected_keywords": ["distributed training", "asynchronous", "SGD", "stragglers", "staleness"],
        "min_sections": ["Introduction", "Background", "Method", "Experiments", "Related Work", "Conclusion"],
        "difficulty": "hard",
        "ground_truth_summary": None,
    },
    {
        "id": "jericho-007",
        "story": (
            "Dialogue systems tend to repeat themselves when trained with maximum likelihood "
            "estimation. We propose a novel loss function that penalizes repetitiveness "
            "directly at the token level during training."
        ),
        "domain": "NLP",
        "expected_keywords": ["dialogue", "repetition", "MLE", "loss function", "training"],
        "min_sections": ["Introduction", "Related Work", "Method", "Experiments", "Conclusion"],
        "difficulty": "easy",
        "ground_truth_summary": None,
    },
    {
        "id": "jericho-008",
        "story": (
            "Contrastive learning has shown promise for few-shot image classification, but "
            "existing methods require large amounts of unlabeled data. We adapt contrastive "
            "pre-training to the few-shot regime using a meta-learning framework."
        ),
        "domain": "CV",
        "expected_keywords": ["few-shot", "contrastive", "meta-learning", "image classification", "pre-training"],
        "min_sections": ["Introduction", "Background", "Method", "Experiments", "Conclusion"],
        "difficulty": "medium",
        "ground_truth_summary": None,
    },
    {
        "id": "jericho-009",
        "story": (
            "Federated learning with heterogeneous client data leads to client drift. "
            "We propose a regularized local update scheme that constrains each client's "
            "update direction toward the global objective."
        ),
        "domain": "ML",
        "expected_keywords": ["federated learning", "heterogeneous", "client drift", "regularization"],
        "min_sections": ["Introduction", "Related Work", "Method", "Experiments", "Conclusion"],
        "difficulty": "hard",
        "ground_truth_summary": None,
    },
    {
        "id": "jericho-010",
        "story": (
            "Recommender systems often suffer from popularity bias, over-recommending "
            "mainstream items. We propose a popularity-agnostic training objective that "
            "equalizes exposure across item frequency tiers."
        ),
        "domain": "RecSys",
        "expected_keywords": ["recommender", "popularity bias", "exposure", "fairness"],
        "min_sections": ["Introduction", "Related Work", "Method", "Experiments", "Conclusion"],
        "difficulty": "easy",
        "ground_truth_summary": None,
    },
]


def load_benchmark() -> list[BenchmarkEntry]:
    """加载默认 Jericho benchmark 数据集。"""
    return [BenchmarkEntry(**entry) for entry in JERICHO_BENCHMARK]


def get_entries_by_domain(domain: str) -> list[BenchmarkEntry]:
    """按领域过滤。"""
    return [e for e in load_benchmark() if e.domain == domain]


def get_entries_by_difficulty(difficulty: str) -> list[BenchmarkEntry]:
    """按难度过滤。"""
    return [e for e in load_benchmark() if e.difficulty == difficulty]


# ─── Benchmark Run Result ──────────────────────────────────────────────────────

@dataclass
class BenchmarkResult:
    entry_id: str
    system: str                           # "Story2Paper" | "DirectChat" | "Story2Proposal"
    generated_paper: str
    # Auto metrics
    keyword_recall: float                 # 0-1，期望关键词覆盖率
    section_recall: float                 # 0-1，期望 section 覆盖率
    paper_length: int                     # token 数（估算）
    # Evaluator metrics (from 20-dim audit)
    evaluator_score: float                # 0-100，20维度加权平均
    evaluator_pass: bool
    # Human metrics (filled later)
    human_fluency: int | None = None     # 1-5
    human_accuracy: int | None = None     # 1-5
    human_overall: int | None = None      # 1-5
    human_notes: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Benchmark Runner ──────────────────────────────────────────────────────────

class JerichoBenchmark:
    """
    运行 Jericho-style 基准评测。
    给定一个 pipeline（Story2Paper / DirectChat / Story2Proposal），
    在所有 benchmark 条目上运行，收集指标。
    """

    def __init__(
        self,
        pipeline_fn,          # callable(story: str) -> str (generated paper)
        system_name: str,
        entries: list[BenchmarkEntry] | None = None,
    ):
        self.pipeline_fn = pipeline_fn
        self.system_name = system_name
        self.entries = entries or load_benchmark()

    def _keyword_recall(self, paper: str, keywords: list[str]) -> float:
        paper_lower = paper.lower()
        hits = sum(1 for kw in keywords if kw.lower() in paper_lower)
        return hits / len(keywords) if keywords else 0.0

    def _section_recall(self, paper: str, sections: list[str]) -> float:
        paper_lower = paper.lower()
        hits = sum(1 for sec in sections if sec.lower() in paper_lower)
        return hits / len(sections) if sections else 0.0

    def _estimate_tokens(self, text: str) -> int:
        # 粗略估算：中文 ~1.5 chars/token，英文 ~4 chars/token
        # 简化：总字符数 / 3
        return len(text) // 3

    def run_single(self, entry: BenchmarkEntry) -> BenchmarkResult:
        """在单条 benchmark entry 上运行 pipeline。"""
        paper = self.pipeline_fn(entry.story)
        return BenchmarkResult(
            entry_id=entry.id,
            system=self.system_name,
            generated_paper=paper,
            keyword_recall=self._keyword_recall(paper, entry.expected_keywords),
            section_recall=self._section_recall(paper, entry.min_sections),
            paper_length=self._estimate_tokens(paper),
            evaluator_score=0.0,    # 后续由 EvaluatorAgent 填充
            evaluator_pass=False,
        )

    def run_all(self, progress_callback=None) -> list[BenchmarkResult]:
        """在所有条目上运行。"""
        results = []
        for i, entry in enumerate(self.entries):
            result = self.run_single(entry)
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, len(self.entries), entry.id)
        return results

    def aggregate(self, results: list[BenchmarkResult]) -> dict:
        """聚合所有结果，生成 summary。"""
        n = len(results)
        return {
            "system": self.system_name,
            "n_entries": n,
            "avg_keyword_recall": sum(r.keyword_recall for r in results) / n,
            "avg_section_recall": sum(r.section_recall for r in results) / n,
            "avg_paper_length": sum(r.paper_length for r in results) / n,
            "avg_evaluator_score": sum(r.evaluator_score for r in results) / n,
            "evaluator_pass_rate": sum(1 for r in results if r.evaluator_pass) / n,
            "human_evaluated": sum(1 for r in results if r.human_overall is not None),
        }
