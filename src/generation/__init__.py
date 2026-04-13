"""SemiShape generation module.

Provides build123d system prompts and code-parsing utilities for
AI-assisted CAD code generation.

Note: LLM calls are made via Agent Zero's active model (self.agent.call_utility_model).
No separate LLM client is needed — the plugin inherits the model configured in Agent Zero.

Key components:
- Language enum: Supported output languages (English, Czech)
- get_system_prompt(): Build the build123d system prompt
- format_rag_context(): Format RAG retrieval results as prompt context
- PromptBuilder: Builder class for structured prompts
"""

from .prompts import (
    Language,
    PromptSection,
    PromptBuilder,
    get_system_prompt,
    format_rag_context,
    INFERENCE_RULES_EN,
    BUILD123D_SYSTEM_PROMPT_EN,
)

__all__ = [
    # Language
    "Language",
    "PromptSection",
    # Prompts
    "PromptBuilder",
    "get_system_prompt",
    "format_rag_context",
    "INFERENCE_RULES_EN",
    "BUILD123D_SYSTEM_PROMPT_EN",
]
