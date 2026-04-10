"""
SemiShape Plugin - Agent Init Extension

Runs when Agent Zero initializes. Injects CAD generation awareness into the
agent's system prompt so that the model can:
  - Auto-detect natural language CAD requests
  - Handle slash commands (/3d, /cad, /docs, /export)
  - Suggest SemiShape tools proactively

This file is symlinked to /a0/extensions/python/agent_init/ by hooks.py install().
"""




# ──────────────────────────────────────────────────────────
# Prompt injected into the agent's system context
# Teaches the active model when and how to use SemiShape
# ──────────────────────────────────────────────────────────

SEMISHAPE_SYSTEM_INJECTION = """

## SemiShape — 3D CAD Model Generation

You have access to three tools that can generate, execute, and search
parametric 3D CAD models using the build123d library.

### Slash Commands (Easiest for users)

When a user types a slash command, convert it to the appropriate tool call:

| User types | Action |
|------------|--------|
| `/3d <description>` | Call `semishape_generate` to create a 3D model |
| `/cad <description>` | Same as `/3d` |
| `/model <description>` | Same as `/3d` |
| `/docs <query>` | Call `semishape_rag_search` to search build123d docs |
| `/export <format>` | Call `semishape_execute` to re-export with given format |

Examples:
- `/3d Create a 50×30×10 mm box with a centred hole` → call semishape_generate
- `/docs how to use fillet` → call semishape_rag_search
- `/export step` → call semishape_execute with export_format="step"

### Auto-Detection

When the user describes something that sounds like a 3D model request —
even without using a slash command or @tool syntax — you should proactively
use `semishape_generate`. Trigger phrases include:

- "create a 3D model", "model a", "design a", "build a [physical object]"
- "generate an STL", "make a STEP file", "for 3D printing"
- "parametric design for", "CAD model of", "I need a part"
- Geometric descriptions: "a box", "a bracket", "a cylinder with a hole"

When auto-detecting, briefly confirm: "I'll generate that using SemiShape…"
then call the tool.

### Tool Reference

```
@semishape_generate description="..." [language="en"] [execute=true]
@semishape_execute code="..." [export_format="stl|step|both"] [output_name="model"]
@semishape_rag_search query="..." [top_k=5] [use_web=true]
```

### Important
- SemiShape uses **your current active model** — no extra API key is needed.
- Generated STL/STEP files are saved in the `output/` directory.
- Code runs in an isolated sandbox (60-second timeout).
- Always verify AI-generated geometry before 3D printing or manufacturing.
"""


async def execute(agent, **kwargs):
    """Called by Agent Zero on every agent startup."""

    # ── Inject CAD awareness into agent system prompt ─────────────────────────
    # SemiShape uses the ACTIVE Agent Zero model — no separate API key needed.
    try:
        if hasattr(agent, "system_prompt") and isinstance(agent.system_prompt, str):
            if "SemiShape" not in agent.system_prompt:
                agent.system_prompt += SEMISHAPE_SYSTEM_INJECTION
    except Exception as exc:
        print(f"[SemiShape] ⚠ Could not inject system prompt: {exc}")
        return

    # ── Report ready status ───────────────────────────────────────────────────
    print("[SemiShape] ✓ Plugin ready — CAD generation available.")
    print("[SemiShape] ℹ Quick start: /3d Create a 50×30×10 mm box")
