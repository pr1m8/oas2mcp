"""Operation enhancer agent submodule for ``oas2mcp``.

Purpose:
    Provide structured models, deterministic context builders, prompt builders,
    and agent logic for the operation-level enhancer workflow.

Design:
    - Keep enhancer-specific models and context isolated from summarizer logic.
    - Prepare one normalized operation at a time for later export into an
      enhanced OpenAPI/FastMCP pipeline.

Attributes:
    __all__: Curated public exports for enhancer helpers.
"""

from oas2mcp.agent.enhancer.agent import (
    DEFAULT_ENHANCER_MODEL_NAME,
    DEFAULT_ENHANCER_REASONING_EFFORT,
    build_enhancer_agent,
    run_operation_enhancer,
)
from oas2mcp.agent.enhancer.context import (
    build_operation_enhancement_context,
)
from oas2mcp.agent.enhancer.models import (
    EnhancementPromptCandidate,
    OperationEnhancement,
    OperationEnhancementContext,
    ResolvedSchemaContext,
    SecuritySchemeContext,
)

__all__ = [
    "DEFAULT_ENHANCER_MODEL_NAME",
    "DEFAULT_ENHANCER_REASONING_EFFORT",
    "EnhancementPromptCandidate",
    "OperationEnhancement",
    "OperationEnhancementContext",
    "ResolvedSchemaContext",
    "SecuritySchemeContext",
    "build_enhancer_agent",
    "build_operation_enhancement_context",
    "run_operation_enhancer",
]
