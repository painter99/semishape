"""Execution module for build123d code sandbox and export.

Provides safe code execution and CAD file export capabilities.

Classes:
    ExecutionSandbox: Safe execution environment for build123d code
    ExecutionResult: Structured result from code execution
    ModelExporter: CAD file export for build123d models
    ExportResult: Structured result from export operations

Functions:
    execute_code: Quick execution with default settings
    export_to_stl: Export part to STL format
    export_to_step: Export part to STEP format
    export_to_all: Export to multiple formats

Example:
    >>> from execution import ExecutionSandbox, execute_code
    >>> 
    >>> # Quick execution
    >>> code = '''
    ... from build123d import *
    ... with BuildPart() as box:
    ...     Box(10, 10, 10)
    ... print(f"Volume: {box.part.volume}")
    ... '''
    >>> result = execute_code(code)
    >>> print(result.success)
    True
    
    >>> # With sandbox instance
    >>> sandbox = ExecutionSandbox(timeout=30)
    >>> result = sandbox.execute(code)
    >>> print(result.output)
    Volume: 1000.0
"""

from .sandbox import (
    ExecutionSandbox,
    ExecutionResult,
    execute_code,
)

from .exporter import (
    ModelExporter,
    ExportResult,
    MultiExportResult,
    export_to_stl,
    export_to_step,
    export_to_all,
)

__all__ = [
    # Sandbox classes
    'ExecutionSandbox',
    'ExecutionResult',
    'execute_code',
    
    # Exporter classes
    'ModelExporter',
    'ExportResult',
    'MultiExportResult',
    'export_to_stl',
    'export_to_step',
    'export_to_all',
]

__version__ = '0.1.0'
