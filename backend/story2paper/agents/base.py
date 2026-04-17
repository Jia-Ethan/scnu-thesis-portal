"""
Base Agent — 所有 Agent 的基类
定义统一的接口和共享工具
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from backend.story2paper.shared.state import VisualContract


class AgentConfig(BaseModel):
    name: str
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4096


class BaseAgent(ABC):
    """Abstract base for all pipeline agents"""

    def __init__(self, config: AgentConfig):
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    @abstractmethod
    def run(self, state: dict) -> dict:
        """
        Execute the agent's task given current pipeline state.
        Returns updated state dict.
        """
        raise NotImplementedError

    def _prompt(self, template: str, **kwargs) -> str:
        """Simple Jinja2-free string template substitution"""
        result = template
        for k, v in kwargs.items():
            result = result.replace(f"{{{{ {k} }}}}", str(v))
        return result
