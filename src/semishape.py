"""SemiShape - build123d CAD Code Generation Assistant.

Main entry point for the SemiShape skill, integrating RAG retrieval,
LLM-based code generation, and safe code execution.

Usage:
    from semishape import SemiShape
    
    ss = SemiShape()
    result = ss.generate_and_execute("Create a 100mm cube with 10mm hole")
    print(result.output_path)
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
import time

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(Path("/a0/usr/.env"))

# Import components
from src.generation import (
    CodeGenerator,
    CodeParser,
    GeneratedCode,
    InferenceConfig,
    LLMConfig,
    Language,
    create_generator,
)
from src.rag import VectorStore, Retriever
from src.execution import ExecutionSandbox, ExecutionResult


# Export format enum
from enum import Enum


class ExportFormat(str, Enum):
    """Supported export formats."""
    STL = "stl"
    STEP = "step"
    PNG = "png"


@dataclass
class ExecutionResultAdapter:
    """Adapter for execution results with simplified interface."""
    success: bool
    stdout: str = ""
    stderr: str = ""
    output_path: Optional[Path] = None
    files: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "output_path": str(self.output_path) if self.output_path else None,
            "files": self.files,
        }


logger = logging.getLogger(__name__)


@dataclass
class SemiShapeResult:
    """Complete result from SemiShape operations."""
    success: bool
    code: str = ""
    explanation: str = ""
    output_path: str = ""
    files: List[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    warnings: List[str] = field(default_factory=list)
    rag_sources: List[str] = field(default_factory=list)
    model: str = ""
    execution_time: float = 0.0
    generation_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "code": self.code,
            "explanation": self.explanation,
            "output_path": self.output_path,
            "files": self.files,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "warnings": self.warnings,
            "rag_sources": self.rag_sources,
            "model": self.model,
            "execution_time": self.execution_time,
            "generation_time": self.generation_time,
        }


class SemiShape:
    """SemiShape build123d CAD Code Generation Assistant.
    
    Main entry point for generating and executing build123d code from
    natural language descriptions. Supports Czech and English.
    
    Features:
    - RAG-powered documentation retrieval
    - LLM-based code generation
    - Safe code execution sandbox
    - STL/STEP export
    
    Example:
        >>> ss = SemiShape()
        >>> result = ss.generate_and_execute(
        ...     "Create a bracket with 4 mounting holes",
        ...     language="en"
        ... )
        >>> print(result.output_path)
    """
    
    DEFAULT_VECTORSTORE_PATH = PROJECT_ROOT / "data" / "vectorstore"
    DEFAULT_DOCS_PATH = PROJECT_ROOT / "data" / "docs"
    DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "output"
    
    def __init__(
        self,
        vectorstore_path: Optional[Path] = None,
        docs_path: Optional[Path] = None,
        output_path: Optional[Path] = None,
        api_key: Optional[str] = None,
        model: str = "openai/gpt-4o-mini",
        provider: str = "openrouter",
        language: str = "en",
        use_rag: bool = True,
    ):
        """Initialize SemiShape.
        
        Args:
            vectorstore_path: Path to ChromaDB vector store
            docs_path: Path to build123d documentation
            output_path: Path for generated output files
            api_key: API key for LLM provider (default: from env)
            model: Model identifier (default: openai/gpt-4o-mini)
            provider: LLM provider (openrouter/ollama)
            language: Default language (en/cs)
            use_rag: Whether to use RAG by default
        """
        self.vectorstore_path = vectorstore_path or self.DEFAULT_VECTORSTORE_PATH
        self.docs_path = docs_path or self.DEFAULT_DOCS_PATH
        self.output_path = output_path or self.DEFAULT_OUTPUT_PATH
        self.default_language = Language.ENGLISH if language.lower() in ("en", "english") else Language.CZECH
        self.use_rag = use_rag
        
        # Initialize components
        self._retriever: Optional[Retriever] = None
        self._generator: Optional[CodeGenerator] = None
        self._sandbox: Optional[ExecutionSandbox] = None
        
        # Configuration
        self._api_key = api_key
        self._model = model
        self._provider = provider
        
        # Create output directory
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"SemiShape initialized (language={language}, use_rag={use_rag})")
    
    @property
    def retriever(self) -> Optional[Retriever]:
        """Lazy-load RAG retriever."""
        if self._retriever is None and self.use_rag:
            try:
                if self.vectorstore_path.exists():
                    store = VectorStore(self.vectorstore_path)
                    self._retriever = Retriever(store)
                    logger.info(f"RAG retriever loaded from {self.vectorstore_path}")
                else:
                    logger.warning(f"Vector store not found at {self.vectorstore_path}")
                    self.use_rag = False
            except Exception as e:
                logger.warning(f"Failed to load RAG retriever: {e}")
                self.use_rag = False
        return self._retriever
    
    @property
    def generator(self) -> CodeGenerator:
        """Lazy-load code generator."""
        if self._generator is None:
            self._generator = create_generator(
                provider=self._provider,
                model=self._model,
                api_key=self._api_key,
                language=self.default_language,
                retriever=self.retriever if self.use_rag else None,
            )
            logger.info(f"Code generator initialized (provider={self._provider}, model={self._model})")
        return self._generator
    
    @property
    def sandbox(self) -> ExecutionSandbox:
        """Lazy-load execution sandbox."""
        if self._sandbox is None:
            self._sandbox = ExecutionSandbox(work_dir=self.output_path)
            logger.info(f"Execution sandbox initialized at {self.output_path}")
        return self._sandbox
    
    def rag_search(
        self,
        query: str,
        top_k: int = 5,
        filter_code: bool = False,
    ) -> List[Dict[str, Any]]:
        """Search build123d documentation using RAG.
        
        Args:
            query: Search query
            top_k: Number of results
            filter_code: If True, only return code examples
        
        Returns:
            List of search results with content and metadata
        """
        if not self.retriever:
            return [{"error": "RAG not available. Check vector store."}]
        
        results = self.retriever.retrieve(
            query,
            top_k=top_k,
            filter_code=filter_code,
        )
        
        return [
            {
                "content": r.content,
                "source": r.source_file,
                "section": r.section_title,
                "score": r.score,
            }
            for r in results
        ]
    
    def generate_code(
        self,
        query: str,
        language: Optional[str] = None,
        use_rag: Optional[bool] = None,
    ) -> GeneratedCode:
        """Generate build123d code from natural language description.
        
        Args:
            query: Natural language description
            language: Language (en/cs), defaults to instance default
            use_rag: Whether to use RAG context, defaults to instance default
        
        Returns:
            GeneratedCode object with code and metadata
        """
        lang = self._parse_language(language)
        use_rag = use_rag if use_rag is not None else self.use_rag
        
        start_time = time.time()
        
        # Generate code
        result = self.generator.generate(
            user_request=query,
            use_rag=use_rag,
        )
        
        generation_time = time.time() - start_time
        
        logger.info(f"Code generated in {generation_time:.2f}s ({len(result.code)} chars)")
        
        return result
    
    def execute(
        self,
        code: str,
        export_format: str = "stl",
        timeout: int = 60,
    ) -> "ExecutionResultAdapter":
        """Execute build123d code and export result.
        
        Args:
            code: build123d Python code
            export_format: Export format (stl/step)
            timeout: Execution timeout in seconds
        
        Returns:
            ExecutionResultAdapter with output files
        """
        import time
        import re
        import uuid
        from src.execution import ModelExporter
        
        start_time = time.time()
        
        # CRITICAL: Strip any export code from generated code
        # Models sometimes ignore prompt rules and generate export code
        export_patterns = [
            r'\n*part\.part\.export\w*\([^)]*\)',
            r'\n*part\.export\w*\([^)]*\)',
            r'\n*export_stl\([^)]*\)',
            r'\n*export_step\([^)]*\)',
            r'\n*\.export_stl\([^)]*\)',
            r'\n*\.export_step\([^)]*\)',
        ]
        cleaned_code = code
        for pattern in export_patterns:
            cleaned_code = re.sub(pattern, '', cleaned_code, flags=re.IGNORECASE)
        
        # Generate unique filename
        model_id = str(uuid.uuid4())[:8]
        output_filename = f"model_{model_id}.{export_format}"
        output_filepath = self.output_path / output_filename
        
        # Add automatic export code
        export_code = f'''

# Auto-generated export code
from pathlib import Path
try:
    from build123d import export_stl, export_step
    
    # Find BuildPart and export its .part attribute
    _exported = False
    for _name, _obj in list(locals().items()):
        if _name.startswith('_'):
            continue
        # Check if it's a BuildPart context manager
        if hasattr(_obj, 'part'):
            try:
                # Get the part - it's a property that returns a Solid
                _part = _obj.part
                if _part is not None:
                    if "{export_format}" == "stl":
                        export_stl(_part, "{output_filepath}")
                    elif "{export_format}" == "step":
                        export_step(_part, "{output_filepath}")
                    print(f"Exported: {output_filepath}")
                    _exported = True
                    break
            except Exception as e:
                print(f"Export attempt failed for {{_name}}: {{e}}")
                continue
    
    if not _exported:
        print("Warning: No BuildPart found to export")
except Exception as e:
    print(f"Export error: {{e}}")
    import traceback
    traceback.print_exc()
'''
        
        # Combine cleaned code with export
        full_code = cleaned_code + export_code
        
        # Use ExecutionSandbox with timeout
        sandbox = ExecutionSandbox(timeout=timeout, work_dir=self.output_path)
        result = sandbox.execute(code=full_code)
        
        execution_time = time.time() - start_time
        logger.info(f"Code executed in {execution_time:.2f}s (success={result.success})")
        
        # Adapt the result to include output_path
        output_path = None
        files = result.files_generated if result.files_generated else []
        
        # Find output file
        if files:
            for f in files:
                if f.endswith(f'.{export_format}'):
                    output_path = f
                    break
            if not output_path and files:
                output_path = files[0]
        
        # Return adapted result
        return ExecutionResultAdapter(
            success=result.success,
            stdout=result.output,
            stderr=result.errors,
            output_path=Path(output_path) if output_path else None,
            files=files,
        )
    
    def generate_and_execute(
        self,
        query: str,
        language: Optional[str] = None,
        use_rag: Optional[bool] = None,
        export_format: str = "stl",
        timeout: int = 60,
    ) -> SemiShapeResult:
        """Generate and execute build123d code in one step.
        
        Args:
            query: Natural language description
            language: Language (en/cs)
            use_rag: Whether to use RAG context
            export_format: Export format (stl/step)
            timeout: Execution timeout in seconds
        
        Returns:
            SemiShapeResult with all information
        """
        start_time = time.time()
        
        # Generate code
        gen_result = self.generate_code(query, language, use_rag)
        generation_time = time.time() - start_time
        
        if not gen_result.code:
            return SemiShapeResult(
                success=False,
                explanation=gen_result.explanation,
                warnings=gen_result.warnings + ["No code generated"],
                rag_sources=gen_result.rag_sources,
                model=gen_result.model,
                generation_time=generation_time,
            )
        
        # Execute code
        exec_start = time.time()
        exec_result = self.execute(gen_result.code, export_format, timeout)
        execution_time = time.time() - exec_start
        
        return SemiShapeResult(
            success=exec_result.success,
            code=gen_result.code,
            explanation=gen_result.explanation,
            output_path=str(exec_result.output_path) if exec_result.output_path else "",
            files=exec_result.files,
            stdout=exec_result.stdout,
            stderr=exec_result.stderr,
            warnings=gen_result.warnings + ([] if exec_result.success else [exec_result.stderr]),
            rag_sources=gen_result.rag_sources,
            model=gen_result.model,
            execution_time=execution_time,
            generation_time=generation_time,
        )
    
    def _parse_language(self, language: Optional[str]) -> Language:
        """Parse language string to Language enum."""
        if language is None:
            return self.default_language
        
        lang_lower = language.lower()
        if lang_lower in ("cs", "cze", "czech", "česky", "český"):
            return Language.CZECH
        return Language.ENGLISH


# Convenience function for quick usage
def generate(
    query: str,
    language: str = "en",
    use_rag: bool = True,
    execute: bool = False,
    **kwargs
) -> Union[GeneratedCode, SemiShapeResult]:
    """Convenience function for quick code generation.
    
    Args:
        query: Natural language description
        language: Language (en/cs)
        use_rag: Whether to use RAG context
        execute: If True, also execute and return SemiShapeResult
        **kwargs: Additional arguments for SemiShape init
    
    Returns:
        GeneratedCode or SemiShapeResult depending on execute flag
    """
    ss = SemiShape(**kwargs)
    
    if execute:
        return ss.generate_and_execute(query, language=language, use_rag=use_rag)
    else:
        return ss.generate_code(query, language=language, use_rag=use_rag)


# Export main classes
__all__ = [
    "SemiShape",
    "SemiShapeResult",
    "generate",
    "Language",
    "GeneratedCode",
    "ExecutionResult",
]
