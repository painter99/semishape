"""
SemiShape - CAD Code Executor Tool

Executes build123d Python code in an isolated sandbox and exports
the resulting 3D model to STL or STEP format.

Usage by the agent:
    When the user provides or approves CAD code and wants it exported, e.g.:
    "Execute this code and export as STEP"
"""

import re
import sys
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.tool import Tool, Response
from src.execution.sandbox import ExecutionSandbox


class SemishapeExecute(Tool):
    """
    Execute build123d Python code and export the 3D model.

    Tool arguments (via self.args):
        code          (str, required)  — build123d Python code to execute
        output_name   (str, optional)  — filename stem for the export (default: "model")
        export_format (str, optional)  — "stl" | "step" | "both"  (default: "stl")
    """

    ALLOWED_FORMATS = {"stl", "step", "both"}

    async def execute(self, **kwargs) -> Response:
        code: str          = self.args.get("code", "").strip()
        output_name: str   = self.args.get("output_name", "model")
        export_format: str = self.args.get(
            "export_format",
            self.get_config("default_export_format", "stl"),
        ).lower()

        # --- Validate ---
        if not code:
            return Response(
                message="❌ Argument `code` is required and must not be empty.",
                break_loop=False,
            )

        if export_format not in self.ALLOWED_FORMATS:
            return Response(
                message=(
                    f"❌ Invalid `export_format`: `{export_format}`. "
                    f"Use one of: {', '.join(sorted(self.ALLOWED_FORMATS))}."
                ),
                break_loop=False,
            )

        # --- Resolve output directory ---
        output_dir = Path(self.get_config("output_dir", str(PROJECT_ROOT / "output")))
        output_dir.mkdir(parents=True, exist_ok=True)

        self.set_progress(f"⚙️ Executing CAD code → {export_format.upper()}…")

        # --- Run code and export ---
        exported_files = self._run_and_export(
            code=code,
            output_dir=output_dir,
            output_name=output_name,
            export_format=export_format,
        )

        if not exported_files:
            return Response(
                message=(
                    "❌ Execution succeeded but no output file was produced.\n\n"
                    "Make sure your code uses `with BuildPart() as part:` syntax "
                    "so the model can be detected and exported automatically."
                ),
                break_loop=False,
            )

        # --- Build success message ---
        parts = ["✅ **CAD model exported successfully.**", ""]
        for path in exported_files:
            ext = Path(path).suffix.upper().lstrip(".")
            parts.append(f"📦 **{ext}:** `{path}`")

        return Response(message="\n".join(parts), break_loop=False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_and_export(
        self,
        code: str,
        output_dir: Path,
        output_name: str,
        export_format: str,
    ) -> list:
        """Execute code in sandbox and return list of exported file paths."""

        # Strip any export code the user may have included
        for pattern in [
            r'\n*.*\.export_stl\([^)]*\)',
            r'\n*.*\.export_step\([^)]*\)',
            r'\n*export_stl\([^)]*\)',
            r'\n*export_step\([^)]*\)',
        ]:
            code = re.sub(pattern, '', code, flags=re.IGNORECASE)

        formats = ["stl", "step"] if export_format == "both" else [export_format]
        output_paths = {
            fmt: output_dir / f"{output_name}.{fmt}" for fmt in formats
        }

        # Build export snippet for each requested format
        export_blocks = []
        for fmt, path in output_paths.items():
            if fmt == "stl":
                fn = "export_stl"
            else:
                fn = "export_step"

            export_blocks.append(f'''
# Auto-export: {fmt.upper()}
try:
    from build123d import {fn} as _export_{fmt}
    _exported_{fmt} = False
    for _name, _obj in list(locals().items()):
        if _name.startswith('_'):
            continue
        if hasattr(_obj, 'part'):
            try:
                _part = _obj.part
                if _part is not None:
                    _export_{fmt}(_part, r"{path}")
                    print(f"Exported {fmt.upper()}: {path}")
                    _exported_{fmt} = True
                    break
            except Exception as _e:
                print(f"Export attempt failed for {{_name}} ({fmt}): {{_e}}")
    if not _exported_{fmt}:
        print("Warning: No BuildPart found for {fmt.upper()} export")
except Exception as _e:
    print(f"{fmt.upper()} export error: {{_e}}")
''')

        full_code = code + "\n\n" + "\n".join(export_blocks)

        sandbox = ExecutionSandbox(timeout=60, work_dir=output_dir)
        sandbox.execute(full_code)

        # Return paths of files that were actually created
        return [
            str(p) for p in output_paths.values()
            if p.exists() and p.stat().st_size > 0
        ]
