"""LLM inference interface for build123d code generation.

Provides high-level interface for generating build123d code using LLMs,
with RAG context integration, response parsing, and error handling.
"""

import re
import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from .llm_client import (
    LLMConfig,
    LLMResponse,
    ChatMessage,
    create_client,
    BaseLLMClient
)
from .prompts import (
    Language,
    PromptBuilder,
    format_rag_context
)

logger = logging.getLogger(__name__)


@dataclass
class GeneratedCode:
    """Container for generated build123d code."""
    code: str
    explanation: str
    raw_response: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    rag_sources: List[str] = field(default_factory=list)
    
    def save(self, path: Path) -> None:
        """Save generated code to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.code, encoding='utf-8')
    
    def has_errors(self) -> bool:
        """Check if code contains TODO or incomplete markers."""
        return "TODO" in self.code or "FIXME" in self.code


@dataclass
class InferenceConfig:
    """Configuration for inference operations."""
    llm_config: LLMConfig = field(default_factory=LLMConfig.from_env)
    language: Language = Language.ENGLISH
    include_inference_rules: bool = True
    max_rag_snippets: int = 5
    max_retries: int = 3
    retry_delay: float = 2.0
    temperature: float = 0.7
    max_tokens: int = 4096


class CodeParser:
    """Parser for extracting build123d code from LLM responses."""
    
    # Regex patterns for code extraction
    CODE_BLOCK_PATTERN = re.compile(
        r'```python\s*\n(.*?)\n```',
        re.DOTALL | re.IGNORECASE
    )
    CODE_BLOCK_GENERIC = re.compile(
        r'```\s*\n(.*?)\n```',
        re.DOTALL
    )
    CODE_BLOCK_NAMED = re.compile(
        r'```(?:python|build123d|py)\s*\n(.*?)\n```',
        re.DOTALL | re.IGNORECASE
    )
    
    @classmethod
    def extract_code_blocks(cls, text: str) -> List[str]:
        """Extract all code blocks from response text.
        
        Args:
            text: Raw LLM response text
        
        Returns:
            List of extracted code blocks
        """
        # Try named code blocks first (python, build123d, py)
        matches = cls.CODE_BLOCK_NAMED.findall(text)
        if matches:
            return [m.strip() for m in matches]
        
        # Try generic code blocks
        matches = cls.CODE_BLOCK_GENERIC.findall(text)
        if matches:
            return [m.strip() for m in matches]
        
        return []
    
    @classmethod
    def extract_primary_code(cls, text: str) -> Tuple[str, str]:
        """Extract the primary code block and explanation.
        
        Args:
            text: Raw LLM response text
        
        Returns:
            Tuple of (code, explanation)
        """
        code_blocks = cls.extract_code_blocks(text)
        
        if code_blocks:
            # Merge all code blocks into one
            code = "\n\n".join(code_blocks)
            
            # Extract explanation (text before first code block)
            first_code_start = text.find('```')
            if first_code_start > 0:
                explanation = text[:first_code_start].strip()
            else:
                explanation = ""
            
            return code, explanation
        
        # No code blocks found - might be plain code or error
        # Check if it looks like Python code
        if 'from build123d' in text or 'import build123d' in text:
            return text.strip(), ""
        
        # No code found
        return "", text
    
    @classmethod
    def validate_build123d_code(cls, code: str) -> Tuple[bool, List[str]]:
        """Validate that code contains build123d constructs.
        
        Args:
            code: Python code to validate
        
        Returns:
            Tuple of (is_valid, list of warnings)
        """
        warnings = []
        
        # Check for essential imports
        if 'from build123d' not in code and 'import build123d' not in code:
            warnings.append("Missing build123d import")
        
        # Check for common patterns
        has_geometry = any([
            'Box(' in code,
            'Cylinder(' in code,
            'with BuildPart' in code,
            'with BuildSketch' in code,
            'extrude(' in code,
            'revolve(' in code,
        ])
        
        if not has_geometry:
            warnings.append("No build123d geometry operations found")
        
        # Check for magic numbers (dimensions not as variables)
        # This is a heuristic - might have false positives
        if re.search(r'(?:Box|Cylinder|Rectangle|Circle)\([^)]*[0-9]+[.,0-9]*[^)]*\)', code):
            # Check if variables are defined
            if not re.search(r'^[A-Z_]+\s*=\s*[0-9]+', code, re.MULTILINE):
                warnings.append("Consider defining dimensions as variables")
        
        return len(warnings) == 0, warnings


class CodeGenerator:
    """High-level code generation interface.
    
    Combines LLM client, RAG retriever, and prompt building
    for end-to-end build123d code generation.
    """
    
    def __init__(
        self,
        config: Optional[InferenceConfig] = None,
        retriever: Optional[Any] = None  # Retriever from rag module
    ):
        """Initialize code generator.
        
        Args:
            config: Inference configuration. If None, uses defaults.
            retriever: RAG retriever for documentation context.
        """
        self.config = config or InferenceConfig()
        self.llm_client = create_client(self.config.llm_config)
        self.retriever = retriever
        self.prompt_builder = PromptBuilder(
            language=self.config.language,
            include_inference_rules=self.config.include_inference_rules,
            max_rag_snippets=self.config.max_rag_snippets
        )
    
    def retrieve_context(self, query: str) -> Tuple[str, List[str]]:
        """Retrieve RAG context for a query.
        
        Args:
            query: User request/query
        
        Returns:
            Tuple of (formatted context, list of sources)
        """
        if not self.retriever:
            return "", []
        
        try:
            # Retrieve relevant documentation
            results = self.retriever.retrieve_for_topic(query, context_size=self.config.max_rag_snippets)
            
            if isinstance(results, tuple):
                context, raw_results = results
            else:
                context = results
                raw_results = []
            
            # Extract sources
            sources = []
            for result in raw_results:
                if hasattr(result, 'source_file'):
                    source = result.source_file
                    if result.section_title:
                        source += f" > {result.section_title}"
                    sources.append(source)
            
            return context, sources
            
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return "", []
    
    def generate(
        self,
        user_request: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        use_rag: bool = True
    ) -> GeneratedCode:
        """Generate build123d code for a user request.
        
        Args:
            user_request: Natural language description of desired geometry
            conversation_history: Optional previous messages for context
            use_rag: Whether to use RAG for documentation context
        
        Returns:
            GeneratedCode object with extracted code and metadata
        """
        # Retrieve RAG context if enabled and available
        rag_context = ""
        rag_sources = []
        
        if use_rag and self.retriever:
            rag_context, rag_sources = self.retrieve_context(user_request)
        
        # Build messages for LLM
        messages = self.prompt_builder.build_messages(
            user_request=user_request,
            rag_results=None,  # We format context separately
            conversation_history=conversation_history
        )
        
        # Add RAG context to system message if available
        if rag_context:
            for msg in messages:
                if msg["role"] == "system":
                    msg["content"] += f"\n\n## Relevant Documentation Context\n\n{rag_context}"
                    break
        
        # Convert to ChatMessage objects
        chat_messages = [
            ChatMessage(role=m["role"], content=m["content"])
            for m in messages
        ]
        
        # Call LLM
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = self.llm_client.complete(
                    messages=chat_messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                
                # Parse response
                code, explanation = CodeParser.extract_primary_code(response.content)
                
                if not code:
                    logger.warning(f"No code extracted from response (attempt {attempt + 1})")
                    last_error = "No code block found in response"
                    continue
                
                # Validate code
                is_valid, warnings = CodeParser.validate_build123d_code(code)
                
                return GeneratedCode(
                    code=code,
                    explanation=explanation,
                    raw_response=response.content,
                    model=response.model,
                    usage=response.usage,
                    warnings=warnings,
                    rag_sources=rag_sources
                )
                
            except Exception as e:
                last_error = e
                logger.error(f"LLM request failed (attempt {attempt + 1}): {e}")
                
                if attempt < self.config.max_retries - 1:
                    import time
                    time.sleep(self.config.retry_delay * (2 ** attempt))
        
        # All retries failed
        return GeneratedCode(
            code="",
            explanation="",
            raw_response=f"Generation failed after {self.config.max_retries} attempts",
            model="",
            warnings=[str(last_error)] if last_error else ["Unknown error"]
        )
    
    def generate_stream(
        self,
        user_request: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        use_rag: bool = True
    ):
        """Generate build123d code with streaming response.
        
        Args:
            user_request: Natural language description
            conversation_history: Optional previous messages
            use_rag: Whether to use RAG context
        
        Yields:
            Text chunks as they arrive
        """
        # Retrieve RAG context
        rag_context = ""
        if use_rag and self.retriever:
            rag_context, _ = self.retrieve_context(user_request)
        
        # Build messages
        messages = self.prompt_builder.build_messages(
            user_request=user_request,
            rag_results=None,
            conversation_history=conversation_history
        )
        
        # Add RAG context to system message
        if rag_context:
            for msg in messages:
                if msg["role"] == "system":
                    msg["content"] += f"\n\n## Relevant Documentation Context\n\n{rag_context}"
                    break
        
        # Convert to ChatMessage objects
        chat_messages = [
            ChatMessage(role=m["role"], content=m["content"])
            for m in messages
        ]
        
        # Stream from LLM
        for chunk in self.llm_client.stream_complete(
            messages=chat_messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        ):
            yield chunk


def create_generator(
    provider: str = "openrouter",
    model: str = "openai/gpt-4o-mini",
    api_key: Optional[str] = None,
    language: Language = Language.ENGLISH,
    retriever: Optional[Any] = None
) -> CodeGenerator:
    """Factory function to create a configured code generator.
    
    Args:
        provider: LLM provider ('openrouter' or 'ollama')
        model: Model identifier
        api_key: API key (optional, will use env var if not provided)
        language: Output language
        retriever: RAG retriever instance
    
    Returns:
        Configured CodeGenerator instance
    """
    llm_config = LLMConfig(
        provider=provider,
        model=model,
        api_key=api_key
    )
    
    inference_config = InferenceConfig(
        llm_config=llm_config,
        language=language
    )
    
    return CodeGenerator(config=inference_config, retriever=retriever)
