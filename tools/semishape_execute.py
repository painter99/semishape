"""
SemiShape - CAD Code Executor Tool

Executes build123d Python code in an isolated sandbox and exports
the resulting 3D model to STL or STEP format.

Usage by the agent:
    When the user provides or approves CAD code and wants it exported, e.g.:
    "Execute this code and export as STEP"
"""

import os
import sys
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.tool import Tool, Response
from helpers.semishape_client import SemiShapeClient, Result


class SemishapeExecute(Tool):
    """
    Execute build123d Python code and export the 3D model.

    Tool arguments (via self.args):
        code          (str, required)  — build123d Python code to execute
        output_name   (str, optional)  — filename stem for the export (default: "model")
        export_format (str, optional)  — "stl" | "step" | "both"        (default: "stl")
    """

    async def execute(self, **kwargs) -> Response:
        code: str          = self.args.get("code", "").strip()
        output_name: str   = self.args.get("output_name", "model")
        export_format: str = self.args.get("export_format", self.get_config("default_export_format", "stl"))

        # --- Validate ---
        if not code:
            return Response(
                message="❌ Argument `code` is required and must not be empty.",
                break_loop=False,
            )

        allowed_formats = {"stl", "step", "both"}
        if export_format not in allowed_formats:
            return Response(
                message=f"❌ Invalid `export_format`: `{export_format}`. Use one of: {', '.join(sorted(allowed_formats))}.",
                break_loop=False,
            )

        # --- Resolve output directory ---
        output_dir = self.get_config("output_dir", str(PROJECT_ROOT / "output"))
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        self.set_progress(f"⚙️ Executing CAD code → {export_format.upper()}…")

        try:
            client = SemiShapeClient(
                language="cs",
                output_dir=output_dir,
                track_metrics=False,
            )

            result: Result = await client.execute_code(
                code=code,
                output_name=output_name,
                export_format=export_format,
            )
        except Exception as exc:
            return Response(
                message=f"❌ Execution error: {type(exc).__name__}: {exc}",
                break_loop=False,
            )

        if not result.success:
            return Response(
                message=(
                    f"❌ Execution failed.\n\n"
                    f"**Error:** {result.error or 'Unknown error'}"
                ),
                break_loop=False,
            )

        # --- Build success message ---
        parts = ["✅ **CAD model exported successfully.**", ""]

        if result.stl_path:
            parts.append(f"📦 **STL:** `{result.stl_path}`")
        if result.step_path:
            parts.append(f"📦 **STEP:** `{result.step_path}`")

        return Response(message="\n".join(parts), break_loop=False)
