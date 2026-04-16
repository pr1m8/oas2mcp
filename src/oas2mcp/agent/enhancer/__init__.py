"""Operation enhancer agent submodule for ``oas2mcp``.

Purpose:
    Provide structured models, deterministic context builders, tools, prompt
    builders, and agent logic for the operation-level enhancer workflow.

Design:
    - Keep enhancer-specific models and context isolated from summarizer logic.
    - Prepare one normalized operation at a time for later export into an
      enhanced OpenAPI/FastMCP pipeline.

Attributes:
    __all__: Curated public exports for enhancer helpers.
"""

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
    "EnhancementPromptCandidate",
    "OperationEnhancement",
    "OperationEnhancementContext",
    "ResolvedSchemaContext",
    "SecuritySchemeContext",
    "build_operation_enhancement_context",
]
