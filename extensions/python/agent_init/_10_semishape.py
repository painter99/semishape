"""
SemiShape Plugin - Agent Init Extension

Runs when Agent Zero initializes. Validates plugin configuration
and optionally reports readiness to the agent context.

This file is symlinked to /a0/extensions/python/agent_init/ by hooks.py install().
"""

from pathlib import Path


async def execute(agent, **kwargs):
    """Called by Agent Zero on every agent startup."""
    try:
        from helpers import plugins
        cfg = plugins.get_plugin_config("semishape", agent=agent) or {}
    except Exception:
        # Framework config not available — read default_config.yaml
        try:
            import yaml
            cfg_path = Path("/a0/usr/projects/semishape/default_config.yaml")
            with open(cfg_path) as fh:
                cfg = yaml.safe_load(fh) or {}
        except Exception:
            cfg = {}

    # Only proceed if an API key is configured
    api_key = cfg.get("openrouter_api_key", "")
    if not api_key:
        # Also check environment
        import os
        api_key = os.environ.get("API_KEY_OPENROUTER") or os.environ.get("OPENROUTER_API_KEY", "")

    if api_key:
        print("[SemiShape] ✓ Plugin ready — CAD generation available.")
    else:
        print(
            "[SemiShape] ⚠ No API key found. "
            "Set API_KEY_OPENROUTER in your environment or plugin settings."
        )
