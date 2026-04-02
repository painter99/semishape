"""SemiShape generation module.

This module provides LLM-based build123d code generation capabilities
with RAG context integration, prompt engineering, and response parsing.

Key components:
- LLM clients (OpenRouter, Ollama)
- System prompts for build123d code generation
- Code parsing and validation
- High-level CodeGenerator interface

Usage:
    from generation import CodeGenerator, create_generator
    
    # Create generator with default OpenRouter config
    generator = create_generator(
        provider="openrouter",
        model="openai/gpt-4o-mini"
    )
    
    # Generate code
    result = generator.generate("Create a 100x50x10mm box with a 10mm hole")
    print(result.code)
    
    # With RAG context
    from rag import Retriever
    retriever = Retriever(vectorstore)
    generator = create_generator(retriever=retriever)
    result = generator.generate("Create a bracket", use_rag=True)
"""

from .llm_client import (
    LLMConfig,
    LLMResponse,
    ChatMessage,
    BaseLLMClient,
    OpenRouterClient,
    OllamaClient,
    create_client,
)

from .prompts import (
    Language,
    PromptSection,
    PromptBuilder,
    get_system_prompt,
    format_rag_context,
    INFERENCE_RULES_EN,
    INFERENCE_RULES_CS,
    BUILD123D_SYSTEM_PROMPT_EN,
    BUILD123D_SYSTEM_PROMPT_CS,
)

from .inference import (
    GeneratedCode,
    InferenceConfig,
    CodeParser,
    CodeGenerator,
    create_generator,
)

__all__ = [
    # LLM Client
    "LLMConfig",
    "LLMResponse",
    "ChatMessage",
    "BaseLLMClient",
    "OpenRouterClient",
    "OllamaClient",
    "create_client",
    
    # Prompts
    "Language",
    "PromptSection",
    "PromptBuilder",
    "get_system_prompt",
    "format_rag_context",
    "INFERENCE_RULES_EN",
    "INFERENCE_RULES_CS",
    "BUILD123D_SYSTEM_PROMPT_EN",
    "BUILD123D_SYSTEM_PROMPT_CS",
    
    # Inference
    "GeneratedCode",
    "InferenceConfig",
    "CodeParser",
    "CodeGenerator",
    "create_generator",
]
