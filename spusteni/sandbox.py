"""Safe execution sandbox for build123d Python code.

Provides isolated execution environment with timeout protection,
output capture, and working directory isolation.
"""

import subprocess
import sys
import os
import json
import tempfile
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict


@dataclass
class ExecutionResult:
    """Structured result from code execution.
    
    Attributes:
        success: Whether execution completed without errors
        output: Captured stdout content
        errors: Captured stderr content
        return_code: Process exit code
        execution_time: Time in seconds for execution
        exception: Exception traceback if execution failed
        files_generated: List of generated file paths
    """
    success: bool
    output: str
    errors: str
    return_code: int
    execution_time: float
    exception: Optional[str] = None
    files_generated: List[str] = None
    
    def __post_init__(self):
        if self.files_generated is None:
            self.files_generated = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class ExecutionSandbox:
    """Safe execution environment for build123d code.
    
    Features:
    - Subprocess isolation
    - Timeout protection (default 60 seconds)
    - Output capture (stdout/stderr)
    - Working directory isolation
    
    Security is provided by subprocess isolation and timeout protection.
    No import restrictions - build123d requires access to standard library modules.
    """
    
    def __init__(
        self,
        timeout: int = 60,
        work_dir: Optional[Path] = None,
        max_output_size: int = 10_000_000,  # 10 MB
    ):
        """Initialize execution sandbox.
        
        Args:
            timeout: Maximum execution time in seconds
            work_dir: Working directory for execution (temp dir if None)
            max_output_size: Maximum output size in bytes
        """
        self.timeout = timeout
        self.work_dir = Path(work_dir) if work_dir else None
        self.max_output_size = max_output_size
    
    def _setup_work_dir(self) -> Path:
        """Create or use working directory.
        
        Returns:
            Path to working directory
        """
        if self.work_dir:
            self.work_dir.mkdir(parents=True, exist_ok=True)
            return self.work_dir
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp(prefix='build123d_exec_')
        return Path(temp_dir)
    
    def execute(
        self,
        code: str,
        input_files: Optional[List[Path]] = None,
    ) -> ExecutionResult:
        """Execute Python code in sandboxed environment.
        
        Args:
            code: Python code to execute
            input_files: Optional list of input file paths to copy to work dir
            
        Returns:
            ExecutionResult with execution outcome
        """
        import time
        start_time = time.time()
        
        # Setup working directory
        work_dir = self._setup_work_dir()
        script_path = work_dir / 'execute.py'
        
        try:
            # Write code to script file
            script_path.write_text(code, encoding='utf-8')
            
            # Copy input files if provided
            if input_files:
                for input_file in input_files:
                    if input_file.exists():
                        import shutil
                        shutil.copy2(input_file, work_dir / input_file.name)
            
            # Execute in subprocess with timeout
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(work_dir),
                env={
                    **os.environ,
                    'PYTHONIOENCODING': 'utf-8',
                    'PYTHONDONTWRITEBYTECODE': '1',
                },
            )
            
            execution_time = time.time() - start_time
            
            # Truncate output if too large
            output = result.stdout[:self.max_output_size] if result.stdout else ''
            errors = result.stderr[:self.max_output_size] if result.stderr else ''
            
            # Check for generated files
            files_generated = []
            for ext in ['.stl', '.step', '.stp', '.brep', '.png', '.jpg', '.svg']:
                files_generated.extend(str(f) for f in work_dir.glob(f'*{ext}'))
            
            return ExecutionResult(
                success=(result.returncode == 0),
                output=output,
                errors=errors,
                return_code=result.returncode,
                execution_time=execution_time,
                exception=None,
                files_generated=files_generated,
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                output='',
                errors=f'Execution timeout after {self.timeout} seconds',
                return_code=-1,
                execution_time=execution_time,
                exception='TimeoutError',
            )
            
        except subprocess.CalledProcessError as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                output=e.stdout or '',
                errors=e.stderr or str(e),
                return_code=e.returncode,
                execution_time=execution_time,
                exception=traceback.format_exc(),
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                output='',
                errors=str(e),
                return_code=-1,
                execution_time=execution_time,
                exception=traceback.format_exc(),
            )
            
        finally:
            # Cleanup temp directory if we created it
            if not self.work_dir and work_dir.exists():
                import shutil
                try:
                    shutil.rmtree(work_dir)
                except Exception:
                    pass  # Ignore cleanup errors
    
    def execute_async(
        self,
        code: str,
        callback: Optional[callable] = None,
    ) -> ExecutionResult:
        """Execute code asynchronously (non-blocking).
        
        Args:
            code: Python code to execute
            callback: Optional callback(result) when execution completes
            
        Returns:
            ExecutionResult (synchronous execution for now)
        """
        # For true async, would use asyncio or threading
        # Current implementation is synchronous
        result = self.execute(code)
        
        if callback:
            callback(result)
        
        return result


# Convenience function for quick execution
def execute_code(
    code: str,
    timeout: int = 60,
    work_dir: Optional[Path] = None,
) -> ExecutionResult:
    """Execute build123d code with default sandbox settings.
    
    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds
        work_dir: Optional working directory
        
    Returns:
        ExecutionResult with execution outcome
    
    Example:
        >>> code = '''
    ... from build123d import *
    ... with BuildPart() as box:
    ...     Box(10, 10, 10)
    ... print(f"Volume: {box.part.volume}")
    ... '''
        >>> result = execute_code(code)
        >>> print(result.success)
        True
    """
    sandbox = ExecutionSandbox(timeout=timeout, work_dir=work_dir)
    return sandbox.execute(code)
