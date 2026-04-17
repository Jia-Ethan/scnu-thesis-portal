"""
DirectChat Baseline
最简单的 baseline：直接把 story 当作 prompt，让 LLM 生成一篇论文。
无任何 Agent，无任何结构化流程。
"""

from __future__ import annotations

from backend.story2paper.shared.llm_router import LLMRouter


SYSTEM_PROMPT = """You are an academic paper writing assistant. Given a research story or idea, write a complete academic paper.
The paper must include the following sections: Introduction, Related Work, Background, Method, Experiments, Conclusion.
Write in formal academic English. Be technically precise and thorough.
"""


USER_PROMPT_TEMPLATE = """Research Story:
{story}

Please write a complete academic paper based on the research story above.
"""


class DirectChatPipeline:
    """
    最简 baseline：
    story → 单一 LLM call → paper
    """

    def __init__(self, model: str | None = None):
        self.router = LLMRouter()
        self.model = model or "gpt-4o"

    def run(self, story: str) -> str:
        """给定 research story，直接生成一篇完整论文。"""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(story=story)},
        ]
        response = self.router.route(messages, model=self.model)
        return response["content"]


# 单例
_default_pipeline: DirectChatPipeline | None = None


def get_default() -> DirectChatPipeline:
    global _default_pipeline
    if _default_pipeline is None:
        _default_pipeline = DirectChatPipeline()
    return _default_pipeline


def run(story: str) -> str:
    """快捷入口。"""
    return get_default().run(story)
