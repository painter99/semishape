"""Execution module for build123d code sandbox and STL/STEP export.

Provides safe subprocess-based code execution and CAD file export.

Classes:
    ExecutionSandbox: Runs build123d code in an isolated subprocess
    ExecutionResult: Structured result from code execution
    ModelExporter: CAD file export (STL / STEP)
    ExportResult: Structured result from export operations

Example:
    >>> from src.execution import ExecutionSandbox
    >>> sandbox = ExecutionSandbox(timeout=60)
    >>> result = sandbox.execute(code)
    >>> print(result.success)
    True
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
    # Sandbox
    'ExecutionSandbox',
    'ExecutionResult',
    'execute_code',
    # Exporter
    'ModelExporter',
    'ExportResult',
    'MultiExportResult',
    'export_to_stl',
    'export_to_step',
    'export_to_all',
]
