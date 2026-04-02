"""SemiShape - build123d CAD Code Generation Assistant.

Main package for AI-assisted parametric CAD code generation.
"""

from src.semishape import (
    SemiShape,
    SemiShapeResult,
    generate,
)
from src.generation import (
    Language,
    GeneratedCode,
    InferenceConfig,
    CodeGenerator,
    CodeParser,
)
from src.execution import (
    ExecutionSandbox,
    ExecutionResult,
    ModelExporter,
)


# Execution result adapter for simplified interface
class ExecutionResultAdapter:
    """Adapter for execution results."""
    def __init__(self, success=True, stdout='', stderr='', output_path=None, files=None):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.output_path = output_path
        self.files = files or []


__all__ = [
    # Main entry point
    "SemiShape",
    "SemiShapeResult",
    "generate",
    
    # Generation
    "Language",
    "GeneratedCode",
    "InferenceConfig",
    "CodeGenerator",
    "CodeParser",
    
    # RAG
    "VectorStore",
    "Retriever",
    
    # Execution
    "ExecutionSandbox",
    "ExecutionResult",
    "ModelExporter",
]
