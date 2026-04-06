"""
SemiShape Plugin - Tool Base Classes

Provides Tool and Response base classes compatible with Agent Zero framework.
Tools in the tools/ directory inherit from Tool and implement execute().
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Response:
    """
    Return value from any Tool.execute() call.

    Attributes:
        message:    Text the agent sees as the tool result.
        break_loop: True  → agent delivers message as final answer.
                    False → agent continues its reasoning loop.
    """
    message: str
    break_loop: bool = False


class Tool(ABC):
    """
    Base class for all SemiShape tools.

    Agent Zero instantiates tools automatically from the tools/ directory.
    Override execute() to implement your tool's logic.
    Use self.args to access the arguments passed by the agent.
    """

    def __init__(
        self,
        agent=None,
        name: str = "",
        method: str | None = None,
        args: dict | None = None,
        message: str = "",
        loop_data: Any = None,
        **kwargs,
    ):
        self.agent = agent
        self.name = name
        self.method = method
        self.args: dict = args or {}
        self.message = message
        self.loop_data = loop_data
        self._progress: str = ""

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def execute(self, **kwargs) -> Response:
        """Implement tool logic here. Return a Response."""
        ...

    # ------------------------------------------------------------------
    # Lifecycle hooks (override if needed)
    # ------------------------------------------------------------------

    async def before_execution(self, **kwargs) -> None:
        """Called before execute(). Useful for setup / validation."""

    async def after_execution(self, response: Response, **kwargs) -> None:
        """Called after execute(). Useful for cleanup / logging."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def set_progress(self, message: str) -> None:
        """Update the visible progress indicator shown to the user."""
        self._progress = message or ""
        if message:
            print(f"[SemiShape:{self.name}] {message}")

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a plugin configuration value.

        Uses Agent Zero helpers.plugins.get_plugin_config when available,
        falling back to default_config.yaml via a simple YAML load.
        """
        try:
            # Prefer framework-native config access
            from helpers import plugins as _plugins
            cfg = _plugins.get_plugin_config("semishape", self.agent) or {}
            return cfg.get(key, default)
        except Exception:
            pass

        # Fallback: read default_config.yaml directly
        try:
            import yaml
            from pathlib import Path
            cfg_path = Path(__file__).parent.parent / "default_config.yaml"
            with open(cfg_path) as fh:
                cfg = yaml.safe_load(fh) or {}
            return cfg.get(key, default)
        except Exception:
            return default
