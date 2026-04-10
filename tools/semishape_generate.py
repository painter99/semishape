"""
SemiShape - CAD Code Generator Tool

Generates build123d Python code from a text description using
the currently active Agent Zero model. No separate API key needed —
the plugin uses whatever model the user has configured in Agent Zero.

Usage by the agent:
    When the user asks to create a 3D model, e.g.:
    "Create a 50×30×10 mm box with a hole in the centre"
"""

import re
import sys
import importlib.util as _ilu
from pathlib import Path

# Resolve project root
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Force-load SemiShape's own helpers/tool.py using absolute path.
# This bypasses Python's module cache, which would otherwise return
# Agent Zero's cached helpers.tool (which has a different API and
# lacks get_config() — causing AttributeError at runtime).
_tool_spec = _ilu.spec_from_file_location(
    "semishape_helpers_tool",
    PROJECT_ROOT / "helpers" / "tool.py",
)
_tool_mod = _ilu.module_from_spec(_tool_spec)
_tool_spec.loader.exec_module(_tool_mod)
Tool = _tool_mod.Tool
Response = _tool_mod.Response

from src.generation.prompts import get_system_prompt, Language
from src.execution.sandbox import ExecutionSandbox


class SemishapeGenerate(Tool):
    """
    Generate build123d CAD code from a text description and export to STL.

    Uses the currently active Agent Zero model — no separate model config needed.

    Tool arguments (via self.args):
        description (str, required)  — text description of the desired 3D model
        language    (str, optional)  — "cs" | "en"  (default: "cs")
        execute     (bool, optional) — also execute code and export STL (default: True)
    """

    async def execute(self, **kwargs) -> Response:
        description: str = self.args.get("description", "").strip()
        language: str    = self.args.get("language", self.get_config("default_language", "cs"))
        also_execute: bool = str(self.args.get("execute", "true")).lower() != "false"

        # --- Validate ---
        if not description:
            return Response(
                message="❌ Argument `description` is required and must not be empty.",
                break_loop=False,
            )

        # --- Resolve output directory ---
        output_dir = Path(self.get_config("output_dir", str(PROJECT_ROOT / "output")))
        output_dir.mkdir(parents=True, exist_ok=True)

        # --- Build system prompt ---
        lang = Language.CZECH if language.lower() in ("cs", "cze", "czech") else Language.ENGLISH

        # Try to get RAG context to improve code quality
        rag_context = ""
        try:
            rag_context = await self._get_rag_context(description)
        except Exception:
            pass  # RAG is optional — continue without it

        system_prompt = get_system_prompt(
            language=lang,
            rag_context=rag_context,
            include_inference_rules=True,
        )

        self.set_progress("🎨 Generating CAD code using active model…")

        # --- Call active Agent Zero model ---
        try:
            raw_response = await self.agent.call_utility_model(
                system=system_prompt,
                message=description,
            )
        except Exception as exc:
            return Response(
                message=f"❌ Model call failed: {type(exc).__name__}: {exc}",
                break_loop=False,
            )

        # --- Parse code from response ---
        code = self._extract_code(raw_response)
        if not code:
            return Response(
                message=(
                    f"❌ No build123d code block found in the model response.\n\n"
                    f"**Raw response:**\n{raw_response[:800]}"
                ),
                break_loop=False,
            )

        # --- Build success message ---
        parts = [
            "✅ **CAD code generated.**",
            "",
            "```python",
            code,
            "```",
        ]

        # --- Optionally execute and export to STL ---
        if also_execute:
            self.set_progress("⚙️ Executing code and exporting STL…")
            stl_path = self._run_and_export(code, output_dir)
            if stl_path:
                parts += [
                    "",
                    f"📦 **STL exported:** `{stl_path}`",
                ]
            else:
                parts += [
                    "",
                    "⚠️ Code generated but STL export failed. Try `semishape_execute` with the code above.",
                ]

        return Response(message="\n".join(parts), break_loop=False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_code(self, text: str) -> str:
        """Extract the first Python code block from an LLM response."""
        # Named code blocks (python, build123d, py)
        named = re.findall(
            r'```(?:python|build123d|py)\s*\n(.*?)\n```',
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if named:
            return "\n\n".join(b.strip() for b in named)

        # Generic code blocks
        generic = re.findall(r'```\s*\n(.*?)\n```', text, re.DOTALL)
        if generic:
            return "\n\n".join(b.strip() for b in generic)

        # Fallback: treat whole response as code if it looks like Python
        if "from build123d" in text or "import build123d" in text:
            return text.strip()

        return ""

    def _run_and_export(self, code: str, output_dir: Path) -> str:
        """Execute build123d code in sandbox and return STL path or empty string."""
        import uuid, re

        # Strip any export code models may have sneaked in
        for pattern in [
            r'\n*.*\.export_stl\([^)]*\)',
            r'\n*.*\.export_step\([^)]*\)',
            r'\n*export_stl\([^)]*\)',
            r'\n*export_step\([^)]*\)',
        ]:
            code = re.sub(pattern, '', code, flags=re.IGNORECASE)

        model_id = str(uuid.uuid4())[:8]
        stl_path = output_dir / f"model_{model_id}.stl"

        export_snippet = f'''

# Auto-generated export (OCCT mesh-first method — reliable in sandbox)
try:
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.StlAPI import StlAPI_Writer
    import os as _os
    _exported = False
    for _name, _obj in list(locals().items()):
        if _name.startswith("_"):
            continue
        if hasattr(_obj, "part"):
            try:
                _part = _obj.part
                if _part is not None:
                    BRepMesh_IncrementalMesh(_part.wrapped, 0.01).Perform()
                    StlAPI_Writer().Write(_part.wrapped, r"{stl_path}")
                    if _os.path.exists(r"{stl_path}") and _os.path.getsize(r"{stl_path}") > 0:
                        print(f"Exported: {stl_path}")
                        _exported = True
                    break
            except Exception as _e:
                print(f"Export attempt failed for {{_name}}: {{_e}}")
    if not _exported:
        print("Warning: No BuildPart found to export")
except Exception as _e:
    print(f"Export error: {{_e}}")
'''

        sandbox = ExecutionSandbox(timeout=60, work_dir=output_dir)
        result = sandbox.execute(code + export_snippet)

        if stl_path.exists() and stl_path.stat().st_size > 0:
            return str(stl_path)
        return ""

    async def _get_rag_context(self, description: str) -> str:
        """Retrieve relevant build123d documentation snippets (optional)."""
        from src.rag.vectorstore import VectorStore
        from src.rag.retriever import Retriever
        from src.generation.prompts import format_rag_context

        vs_path = PROJECT_ROOT / "data" / "vectorstore"
        if not vs_path.exists():
            return ""

        store = VectorStore(vs_path)
        retriever = Retriever(store)
        results = retriever.retrieve(description, top_k=3)
        return format_rag_context(results, max_snippets=3)
