"""
LLM Router — 统一路由层
支持 GPT / Claude / Gemini / Ollama，通过 LiteLLM 调用
支持结构化输出（response_format / json_schema）
"""

from __future__ import annotations
import os
import json
import litellm
from typing import Any

# 允许所有 LiteLLM 支持的 provider
litellm.drop_params = True


# ─── Per-Agent 默认模型配置 ─────────────────────────────────────────────────

DEFAULT_MODEL_MAP = {
    "architect":  {"provider": "openai",  "model": "gpt-4o",        "temperature": 0.7},
    "writer":     {"provider": "openai",  "model": "gpt-4o",        "temperature": 0.6},
    "evaluator":  {"provider": "openai",  "model": "gpt-4o-mini",  "temperature": 0.3},
    "refiner":    {"provider": "openai",  "model": "gpt-4o-mini",  "temperature": 0.5},
}


# ─── Environment 配置映射 ───────────────────────────────────────────────────

def _resolve_model(agent: str) -> dict:
    """从环境变量或默认值解析模型配置"""
    defaults = DEFAULT_MODEL_MAP.get(agent, DEFAULT_MODEL_MAP["writer"])

    provider = os.getenv(f"LITELLM_{agent.upper()}_PROVIDER") or defaults["provider"]
    model = os.getenv(f"LITELLM_{agent.upper()}_MODEL") or defaults["model"]
    temperature = float(os.getenv(f"LITELLM_{agent.upper()}_TEMPERATURE") or defaults["temperature"])

    return {
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "max_tokens": 8192,
    }


# ─── Core Router ─────────────────────────────────────────────────────────────

def llm_call(
    prompt: str,
    agent: str = "writer",
    *,
    system_prompt: str | None = None,
    json_schema: dict | None = None,
    **override_kwargs,
) -> dict | str:
    """
    统一 LLM 调用入口。

    Args:
        prompt: 用户级输入 prompt
        agent: 调度到哪个 Agent，决定默认模型
        system_prompt: 可选系统提示，优先级高于默认
        json_schema: 若提供，强制结构化输出（必须是 dict，兼容 OpenAI json_schema 格式）
        **override_kwargs: 临时覆盖默认参数（model, temperature, max_tokens…）

    Returns:
        若 json_schema 提供 → dict（已解析）
        否则 → str（原始文本）
    """
    cfg = _resolve_model(agent)
    cfg.update(override_kwargs)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    kwargs = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg["temperature"],
        "max_tokens": cfg["max_tokens"],
    }

    # 结构化输出
    if json_schema:
        kwargs["response_format"] = {"type": "json_object", "json_schema": json_schema}

    response = litellm.completion(**kwargs)
    content: str = response["choices"][0]["message"]["content"]

    if json_schema:
        return json.loads(content)
    return content


def llm_stream(
    prompt: str,
    agent: str = "writer",
    *,
    system_prompt: str | None = None,
    **override_kwargs,
):
    """
    流式调用入口。供前端 SSE / WebSocket streaming 使用。
    Yields token chunks.
    """
    cfg = _resolve_model(agent)
    cfg.update(override_kwargs)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    kwargs = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg["temperature"],
        "max_tokens": cfg["max_tokens"],
        "stream": True,
    }

    response = litellm.completion(**kwargs)
    for chunk in response:
        delta = chunk["choices"][0]["delta"].get("content", "")
        if delta:
            yield delta
