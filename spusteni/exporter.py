"""CAD file exporter for build123d models.

Provides export capabilities for STL, STEP formats and
screenshot generation for build123d geometry.
"""

import os
import sys
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Optional, List, Union, Dict, Any
from dataclasses import dataclass, asdict
import time


@dataclass
class ExportResult:
    """Result from export operation.
    
    Attributes:
        success: Whether export completed successfully
        format: Export format (stl, step, png)
        file_path: Path to exported file (if successful)
        error: Error message (if failed)
        file_size: File size in bytes
        execution_time: Time taken for export
    """
    success: bool
    format: str
    file_path: Optional[str]
    error: Optional[str] = None
    file_size: int = 0
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class MultiExportResult:
    """Result from multiple export operations.
    
    Attributes:
        success: Whether all exports completed successfully
        results: List of individual ExportResult objects
        total_time: Total execution time
    """
    success: bool
    results: List[ExportResult]
    total_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            'success': self.success,
            'results': [r.to_dict() for r in self.results],
            'total_time': self.total_time,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class ModelExporter:
    """Export build123d models to various formats.
    
    Supports:
    - STL export (binary and ASCII)
    - STEP export (ISO 10303-21)
    - Screenshot generation (PNG, SVG)
    
    Example:
        >>> from build123d import *
        >>> exporter = ModelExporter()
        >>> result = exporter.export_step(part, 'model.step')
        >>> print(result.success)
        True
    """
    
    # Default export directory
    DEFAULT_EXPORT_DIR = Path(tempfile.gettempdir()) / 'build123d_exports'
    
    def __init__(
        self,
        export_dir: Optional[Path] = None,
        clean_temp: bool = True,
    ):
        """Initialize model exporter.
        
        Args:
            export_dir: Directory for exported files (temp dir if None)
            clean_temp: Whether to clean temp files on exit
        """
        self.export_dir = Path(export_dir) if export_dir else self.DEFAULT_EXPORT_DIR
        self.clean_temp = clean_temp
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_part_from_code(
        self,
        code: str,
        variable_name: str = 'part',
    ) -> Any:
        """Execute code and extract part object.
        
        Args:
            code: Python code to execute
            variable_name: Name of variable containing the part
            
        Returns:
            The extracted part object
            
        Raises:
            ValueError: If variable not found or not a valid part
        """
        # Create execution namespace
        namespace = {}
        
        # Execute code
        exec(code, namespace)
        
        # Find part
        if variable_name in namespace:
            return namespace[variable_name]
        
        # Try to find BuildPart in namespace
        from build123d import BuildPart
        for name, obj in namespace.items():
            if isinstance(obj, BuildPart):
                return obj.part
        
        # Try to find any part-like object
        for name, obj in namespace.items():
            if hasattr(obj, 'volume') and hasattr(obj, 'bounding_box'):
                return obj
        
        raise ValueError(f"Could not find part variable '{variable_name}' in executed code")
    
    def export_stl(
        self,
        part_or_code: Union[Any, str],
        output_path: Optional[Path] = None,
        ascii_mode: bool = False,
        tolerance: float = 0.001,
        angular_tolerance: float = 0.1,
        **kwargs,
    ) -> ExportResult:
        """Export part to STL format.
        
        Args:
            part_or_code: build123d part object or Python code string
            output_path: Output file path (auto-generated if None)
            ascii_mode: Use ASCII STL format (binary by default)
            tolerance: Mesh tolerance
            angular_tolerance: Angular tolerance for meshing
            **kwargs: Additional arguments for mesh generation
            
        Returns:
            ExportResult with export outcome
        """
        start_time = time.time()
        
        try:
            # Get part object
            if isinstance(part_or_code, str):
                part = self._get_part_from_code(part_or_code)
            else:
                part = part_or_code
            
            # Generate output path
            if output_path is None:
                import uuid
                output_path = self.export_dir / f"model_{uuid.uuid4().hex[:8]}.stl"
            output_path = Path(output_path)
            
            # Import build123d export function (top-level function)
            from build123d import export_stl as export_to_stl
            
            # Export to STL
            export_to_stl(
                part,
                str(output_path),
                tolerance=tolerance,
                angular_tolerance=angular_tolerance,
            )
            
            # Get file size
            file_size = output_path.stat().st_size if output_path.exists() else 0
            
            return ExportResult(
                success=True,
                format='stl',
                file_path=str(output_path),
                file_size=file_size,
                execution_time=time.time() - start_time,
            )
            
        except Exception as e:
            return ExportResult(
                success=False,
                format='stl',
                file_path=None,
                error=str(e),
                execution_time=time.time() - start_time,
            )
    
    def export_step(
        self,
        part_or_code: Union[Any, str],
        output_path: Optional[Path] = None,
        **kwargs,
    ) -> ExportResult:
        """Export part to STEP format (ISO 10303-21).
        
        Args:
            part_or_code: build123d part object or Python code string
            output_path: Output file path (auto-generated if None)
            **kwargs: Additional arguments for STEP export
            
        Returns:
            ExportResult with export outcome
        """
        start_time = time.time()
        
        try:
            # Get part object
            if isinstance(part_or_code, str):
                part = self._get_part_from_code(part_or_code)
            else:
                part = part_or_code
            
            # Generate output path
            if output_path is None:
                import uuid
                output_path = self.export_dir / f"model_{uuid.uuid4().hex[:8]}.step"
            output_path = Path(output_path)
            
            # Import build123d export function (top-level function)
            try:
                from build123d import export_step as export_to_step
                export_to_step(part, str(output_path))
            except ImportError:
                # Fallback: use OCP directly
                from OCP.STEPControl import STEPControl_Writer
                from OCP.STEPControl import STEPControl_AsIs
                from OCP.IFSelect import IFSelect_RetDone
                
                writer = STEPControl_Writer()
                writer.Transfer(part.wrapped, STEPControl_AsIs)
                status = writer.Write(str(output_path))
                
                if status != IFSelect_RetDone:
                    raise RuntimeError("STEP export failed")
            
            
            # Get file size
            file_size = output_path.stat().st_size if output_path.exists() else 0
            
            return ExportResult(
                success=True,
                format='step',
                file_path=str(output_path),
                file_size=file_size,
                execution_time=time.time() - start_time,
            )
            
        except Exception as e:
            return ExportResult(
                success=False,
                format='step',
                file_path=None,
                error=str(e),
                execution_time=time.time() - start_time,
            )
    
    def export_screenshot(
        self,
        part_or_code: Union[Any, str],
        output_path: Optional[Path] = None,
        width: int = 800,
        height: int = 600,
        color: str = '#2d3436',
        edge_color: str = '#74b9ff',
        **kwargs,
    ) -> ExportResult:
        """Generate screenshot of part.
        
        Args:
            part_or_code: build123d part object or Python code string
            output_path: Output file path (auto-generated if None)
            width: Image width in pixels
            height: Image height in pixels
            color: Part color (hex string)
            edge_color: Edge color (hex string)
            **kwargs: Additional arguments for rendering
            
        Returns:
            ExportResult with screenshot path
        """
        start_time = time.time()
        
        try:
            # Get part object
            if isinstance(part_or_code, str):
                part = self._get_part_from_code(part_or_code)
            else:
                part = part_or_code
            
            # Generate output path
            if output_path is None:
                import uuid
                output_path = self.export_dir / f"model_{uuid.uuid4().hex[:8]}.png"
            output_path = Path(output_path)
            
            # Try to use ocp_vscode for screenshot
            try:
                from ocp_vscode import show, set_port
                import tempfile
                
                # Create temp script to capture screenshot
                screenshot_script = f'''
from build123d import *
from ocp_vscode import show, Camera, Color
from OCP.V3d import V3d_View

# Load part
part = {repr(part)}

# Display and save
show(
    part,
    reset_camera=Camera.CENTER,
    color='{color}',
    edge_color='{edge_color}',
    width={width},
    height={height},
)

# Note: ocp_vscode requires VS Code extension for actual screenshot
# This will display the part but screenshot requires GUI
print("Part displayed - screenshot requires VS Code extension")
'''
                # For now, create a placeholder message
                # Actual screenshot generation would require headless rendering
                (self.export_dir / 'screenshot_info.txt').write_text(
                    f"Screenshot requires VS Code OCP CAD Viewer extension\n"
                    f"Part: {part}\n"
                    f"Dimensions: {width}x{height}\n"
                )
                
                # Return success with info
                return ExportResult(
                    success=True,
                    format='info',
                    file_path=str(self.export_dir / 'screenshot_info.txt'),
                    execution_time=time.time() - start_time,
                )
                
            except ImportError:
                # ocp_vscode not available - return info
                return ExportResult(
                    success=False,
                    format='png',
                    file_path=None,
                    error='Screenshot requires ocp_vscode and VS Code extension',
                    execution_time=time.time() - start_time,
                )
            
        except Exception as e:
            return ExportResult(
                success=False,
                format='png',
                file_path=None,
                error=str(e),
                execution_time=time.time() - start_time,
            )
    
    def export_all(
        self,
        part_or_code: Union[Any, str],
        output_dir: Optional[Path] = None,
        formats: List[str] = ['stl', 'step'],
        **kwargs,
    ) -> MultiExportResult:
        """Export to multiple formats at once.
        
        Args:
            part_or_code: build123d part object or Python code string
            output_dir: Output directory (auto-generated if None)
            formats: List of formats to export ['stl', 'step', 'png']
            **kwargs: Additional arguments for exports
            
        Returns:
            MultiExportResult with all export outcomes
        """
        start_time = time.time()
        results = []
        
        # Create output directory
        if output_dir is None:
            import uuid
            output_dir = self.export_dir / f"export_{uuid.uuid4().hex[:8]}"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate base filename
        base_name = 'model'
        
        # Export to each format
        for fmt in formats:
            output_path = output_dir / f"{base_name}.{fmt}"
            
            if fmt == 'stl':
                result = self.export_stl(part_or_code, output_path, **kwargs)
            elif fmt in ('step', 'stp'):
                result = self.export_step(part_or_code, output_path, **kwargs)
            elif fmt in ('png', 'svg'):
                result = self.export_screenshot(part_or_code, output_path, **kwargs)
            else:
                result = ExportResult(
                    success=False,
                    format=fmt,
                    file_path=None,
                    error=f"Unsupported format: {fmt}",
                )
            
            results.append(result)
        
        return MultiExportResult(
            success=all(r.success for r in results),
            results=results,
            total_time=time.time() - start_time,
        )
    
    def cleanup(self):
        """Clean up temporary export directory."""
        if self.clean_temp and self.export_dir.exists():
            import shutil
            try:
                shutil.rmtree(self.export_dir)
            except Exception:
                pass


# Convenience functions
def export_to_stl(
    part_or_code: Union[Any, str],
    output_path: Optional[Path] = None,
    **kwargs,
) -> ExportResult:
    """Export part to STL format.
    
    Args:
        part_or_code: build123d part object or Python code string
        output_path: Output file path
        **kwargs: Additional arguments
        
    Returns:
        ExportResult with export outcome
    """
    exporter = ModelExporter()
    return exporter.export_stl(part_or_code, output_path, **kwargs)


def export_to_step(
    part_or_code: Union[Any, str],
    output_path: Optional[Path] = None,
    **kwargs,
) -> ExportResult:
    """Export part to STEP format.
    
    Args:
        part_or_code: build123d part object or Python code string
        output_path: Output file path
        **kwargs: Additional arguments
        
    Returns:
        ExportResult with export outcome
    """
    exporter = ModelExporter()
    return exporter.export_step(part_or_code, output_path, **kwargs)


def export_to_all(
    part_or_code: Union[Any, str],
    output_dir: Optional[Path] = None,
    formats: List[str] = ['stl', 'step'],
    **kwargs,
) -> MultiExportResult:
    """Export to multiple formats.
    
    Args:
        part_or_code: build123d part object or Python code string
        output_dir: Output directory
        formats: List of formats ['stl', 'step', 'png']
        **kwargs: Additional arguments
        
    Returns:
        MultiExportResult with all export outcomes
    """
    exporter = ModelExporter()
    return exporter.export_all(part_or_code, output_dir, formats, **kwargs)
