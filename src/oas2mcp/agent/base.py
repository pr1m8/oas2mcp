"""Thin LangChain v1 agent factory helpers for ``oas2mcp``."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from oas2mcp.agent.runtime import Oas2McpRuntimeContext
from oas2mcp.agent.state import OpenApiEnhancementState

DEFAULT_MODEL_NAME = "gpt-5.1"
DEFAULT_REASONING_EFFORT = "high"


def load_project_env() -> None:
    """Load likely project-local environment files."""
    load_dotenv()
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env, override=False)


def require_openai_api_key() -> str:
    """Return the OpenAI API key from env."""
    load_project_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Put it in your shell environment or .env."
        )
    return api_key


def build_default_chat_model(
    *,
    model_name: str = DEFAULT_MODEL_NAME,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
    api_key: str | None = None,
    **kwargs: Any,
) -> ChatOpenAI:
    """Build the default OpenAI chat model."""
    resolved_api_key = api_key or require_openai_api_key()
    return ChatOpenAI(
        model=model_name,
        api_key=resolved_api_key,
        reasoning={"effort": reasoning_effort},
        **kwargs,
    )


def build_base_agent(
    *,
    response_format: Any,
    tools: list[Any] | None = None,
    middleware: list[Any] | None = None,
    system_prompt: str | None = None,
    model: Any | None = None,
    model_name: str = DEFAULT_MODEL_NAME,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
    model_kwargs: dict[str, Any] | None = None,
):
    """Build a stateful LangChain v1 agent for oas2mcp."""
    resolved_model = model or build_default_chat_model(
        model_name=model_name,
        reasoning_effort=reasoning_effort,
        **(model_kwargs or {}),
    )

    return create_agent(
        model=resolved_model,
        tools=tools or [],
        middleware=middleware or [],
        system_prompt=system_prompt or "",
        response_format=response_format,
        context_schema=Oas2McpRuntimeContext,
        state_schema=OpenApiEnhancementState,
    )
