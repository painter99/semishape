"""
SemiShape - Documentation Search Tool

Searches the bundled build123d documentation for information about
API usage, examples, and troubleshooting.

Usage by the agent:
    When the user asks about build123d API, e.g.:
    "How does fillet work in build123d?"
    "Show me an example of extrude with taper"
"""

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

# Documentation root (bundled with the plugin)
DOCS_ROOT = PROJECT_ROOT / "data" / "docs"


class SemishapeRagSearch(Tool):
    """
    Search bundled build123d documentation.

    Tool arguments (via self.args):
        query   (str, required)  — search term or question
        top_k   (int, optional)  — max results to return (default: 5, max: 10)
        use_web (bool, optional) — also search web for build123d info (default: true)
    """

    async def execute(self, **kwargs) -> Response:
        query: str  = self.args.get("query", "").strip()
        top_k: int  = min(int(self.args.get("top_k", 5)), 10)
        use_web: bool = str(self.args.get("use_web", "true")).lower() != "false"

        # --- Validate ---
        if not query:
            return Response(
                message="❌ Argument `query` is required and must not be empty.",
                break_loop=False,
            )

        self.set_progress(f"🔍 Searching documentation for: {query}")

        local_results = await self._search_local(query, top_k)
        web_results: list = []

        if use_web:
            self.set_progress("🌐 Searching web…")
            web_results = await self._search_web(query)

        if not local_results and not web_results:
            return Response(
                message=(
                    f"📚 No results found for **\"{query}\"**.\n\n"
                    "Try different keywords, e.g. `fillet`, `extrude`, `sketch`, `loft`."
                ),
                break_loop=False,
            )

        # --- Build response ---
        parts = [f"📚 **Documentation results for:** \"{query}\"", ""]

        for i, r in enumerate(local_results, 1):
            snippet = r["snippet"][:600].strip()
            parts += [
                f"**{i}. {r['source']}**",
                f"```\n{snippet}\n```",
                "",
            ]

        if web_results:
            parts.append("**Web sources:**")
            for r in web_results[:3]:
                title   = r.get("title", "")
                url     = r.get("href") or r.get("url", "")
                snippet = r.get("body", "")[:200]
                parts.append(f"- [{title}]({url}): {snippet}")

        return Response(message="\n".join(parts), break_loop=False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _search_local(self, query: str, top_k: int) -> list:
        """Keyword search over bundled .rst and .py documentation files."""
        if not DOCS_ROOT.exists():
            return []

        results = []
        q = query.lower()

        for fpath in list(DOCS_ROOT.rglob("*.rst")) + list(DOCS_ROOT.rglob("*.py")):
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            if q not in text.lower():
                continue

            idx   = text.lower().find(q)
            start = max(0, idx - 120)
            end   = min(len(text), idx + 500)

            results.append({
                "source":  str(fpath.relative_to(PROJECT_ROOT)),
                "snippet": f"…{text[start:end].strip()}…",
            })

            if len(results) >= top_k:
                break

        return results

    async def _search_web(self, query: str) -> list:
        """DuckDuckGo web search for build123d information."""
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                return list(ddgs.text(f"build123d python CAD {query}", max_results=3))
        except Exception as exc:
            print(f"[SemiShape:rag_search] Web search unavailable: {exc}")
            return []
