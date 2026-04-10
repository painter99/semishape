"""
SemiShape Plugin - Agent Init Extension

Runs when Agent Zero initializes. Validates that the API key is available
and reports plugin readiness to the console.

This file is symlinked to /a0/extensions/python/agent_init/ by hooks.py install().
"""

import os
from pathlib import Path


async def execute(agent, **kwargs):
    """Called by Agent Zero on every agent startup."""
    # Attempt to read API key from Agent Zero plugin config first, then environment
    api_key = ""
    try:
        from helpers import plugins
        cfg = plugins.get_plugin_config("semishape", agent=agent) or {}
        api_key = cfg.get("openrouter_api_key", "")
    except Exception:
        pass

    if not api_key:
        api_key = (
            os.environ.get("API_KEY_OPENROUTER", "")
            or os.environ.get("OPENROUTER_API_KEY", "")
        )

    if api_key:
        print("[SemiShape] ✓ Plugin ready — CAD generation available.")
    else:
        print(
            "[SemiShape] ⚠ No API key found. "
            "Set API_KEY_OPENROUTER in your environment or in Agent Zero secrets."
        )
