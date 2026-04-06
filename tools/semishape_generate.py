"""
SemiShape - CAD Code Generator Tool

Generates build123d Python code from a text description using
a dual-model approach (primary → backup) with automatic syntax
validation and correction.

Usage by the agent:
    When the user asks to create a 3D model, e.g.:
    "Create a 50×30×10 mm box with a hole in the centre"
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


class SemishapeGenerate(Tool):
    """
    Generate build123d CAD code from a text description.

    Tool arguments (via self.args):
        description (str, required)  — text description of the desired 3D model
        language    (str, optional)  — "cs" | "en"  (default: "cs")
        execute     (bool, optional) — also execute code and export STL (default: False)

    Note: Uses the AI model currently active in the Agent Zero conversation.
    """
    async def execute(self, **kwargs) -> Response:
        description: str = self.args.get("description", "").strip()
        language: str    = self.args.get("language", self.get_config("default_language", "cs"))
        also_execute: bool = str(self.args.get("execute", "false")).lower() == "true"

        # --- Validate ---
        if not description:
            return Response(
                message="❌ Argument `description` is required and must not be empty.",
                break_loop=False,
            )

        # --- Resolve output directory ---
        output_dir = self.get_config("output_dir", str(PROJECT_ROOT / "output"))
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # --- Resolve API key ---
        api_key = (
            self.get_config("openrouter_api_key")
            or os.environ.get("API_KEY_OPENROUTER")
            or os.environ.get("OPENROUTER_API_KEY", "")
        )
        if not api_key:
            return Response(
                message=(
                    "❌ No OpenRouter API key found.\n"
                    "Set `API_KEY_OPENROUTER` in your environment "
                    "or configure it in the plugin settings."
                ),
                break_loop=False,
            )

        # --- Map model alias ---
        model_map = {
            "kimi":    "moonshotai/kimi-k2.5",
            "minimax": "minimax/minimax-01",
        }
        primary_model = model_map.get(model, self.get_config("default_model", "moonshotai/kimi-k2.5"))
        backup_model  = self.get_config("backup_model", "minimax/minimax-01")

        self.set_progress("🎨 Generating CAD code…")

        try:
            client = SemiShapeClient(
                language=language,
                output_dir=output_dir,
                track_metrics=True,
            )

            result: Result = await client.generate(
                description=description,
                model=primary_model,
                backup_model=backup_model,
                also_execute=also_execute,
            )
        except Exception as exc:
            return Response(
                message=f"❌ Generation error: {type(exc).__name__}: {exc}",
                break_loop=False,
            )

        if not result.success:
            return Response(
                message=(
                    f"❌ Generation failed.\n\n"
                    f"**Error:** {result.error or 'Unknown error'}"
                ),
                break_loop=False,
            )

        # --- Build success message ---
        parts = [
            f"✅ **CAD code generated** (model: `{result.model_used}`)",
            "",
            "```python",
            result.code or "",
            "```",
        ]

        if also_execute and result.stl_path:
            parts += [
                "",
                f"📦 **STL exported:** `{result.stl_path}`",
            ]
        elif also_execute:
            parts += [
                "",
                "⚠️ Code generated but STL export failed — see error above.",
            ]

        if result.cost_usd:
            parts.append(f"💰 Cost: ${result.cost_usd:.5f}")

        return Response(message="\n".join(parts), break_loop=False)
