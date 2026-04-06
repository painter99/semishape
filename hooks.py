"""
SemiShape Plugin - Lifecycle Hooks

Called by Agent Zero framework during plugin lifecycle events.
All functions accept **kwargs for forward compatibility.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Paths
PLUGIN_DIR = Path(__file__).parent
A0_ROOT = Path("/a0")
SKILLS_DST = A0_ROOT / "usr" / "skills"
EXTENSIONS_DST = A0_ROOT / "extensions" / "python" / "agent_init"

# Extension source (inside plugin)
AGENT_INIT_SRC = PLUGIN_DIR / "extensions" / "python" / "agent_init" / "_10_semishape.py"
AGENT_INIT_DST = EXTENSIONS_DST / "_10_semishape.py"


def install(**kwargs):
    """
    Called after plugin is enabled. Creates directories, symlinks extensions, copies skills.
    """
    print("[SemiShape] Running install hook...")

    # 1. Create required directories
    for d in [
        PLUGIN_DIR / "output",
        PLUGIN_DIR / "data" / "cache",
        PLUGIN_DIR / "data" / "vectorstore",
        PLUGIN_DIR / "data" / "logs",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    # 2. Create .gitkeep sentinels
    for d in [PLUGIN_DIR / "output", PLUGIN_DIR / "data" / "logs"]:
        sentinel = d / ".gitkeep"
        if not sentinel.exists():
            sentinel.touch()

    # 3. Symlink agent_init extension → /a0/extensions/python/agent_init/
    EXTENSIONS_DST.mkdir(parents=True, exist_ok=True)
    if AGENT_INIT_SRC.exists() and not AGENT_INIT_DST.exists():
        AGENT_INIT_DST.symlink_to(AGENT_INIT_SRC)
        print(f"  ✓ Extension symlinked: {AGENT_INIT_DST.name}")

    # 4. Copy skill to /a0/usr/skills/
    skill_src = PLUGIN_DIR / "skills" / "semishape"
    skill_dst = SKILLS_DST / "semishape"
    if skill_src.is_dir():
        skill_dst.mkdir(parents=True, exist_ok=True)
        for f in skill_src.iterdir():
            if f.is_file():
                shutil.copy2(str(f), str(skill_dst / f.name))
        print(f"  ✓ Skill copied: {skill_dst}")

    # 5. Run dependency installer
    init_script = PLUGIN_DIR / "initialize.py"
    python = _find_python()
    try:
        subprocess.run([python, str(init_script)], check=True)
        print("  ✓ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"  ⚠ Dependency install returned non-zero: {e}")

    print("[SemiShape] Install complete.")


def uninstall(**kwargs):
    """
    Called when plugin is disabled or removed. Removes extensions and skills symlinks.
    User data (output/, data/vectorstore/) is preserved.
    """
    print("[SemiShape] Running uninstall hook...")

    # Remove extension symlink
    if AGENT_INIT_DST.is_symlink():
        AGENT_INIT_DST.unlink()
        print(f"  ✓ Removed extension symlink: {AGENT_INIT_DST.name}")

    # Remove skill copy
    skill_dst = SKILLS_DST / "semishape"
    if skill_dst.is_dir():
        shutil.rmtree(str(skill_dst))
        print(f"  ✓ Removed skill: {skill_dst}")

    # Remove cache only (preserve user output and vectorstore)
    cache = PLUGIN_DIR / "data" / "cache"
    if cache.exists():
        shutil.rmtree(str(cache))
        print("  ✓ Removed data/cache")

    print("[SemiShape] Uninstall complete. User data preserved in output/ and data/vectorstore/.")


def pre_update(**kwargs):
    """
    Called before plugin code is updated. Preserve user configuration and data.
    """
    print("[SemiShape] Running pre_update hook...")

    # Preserve user config if it exists
    user_config = PLUGIN_DIR / "default_config.yaml"
    if user_config.exists():
        print("  ✓ User configuration will be preserved during update.")

    # Remove stale extension symlink so install() re-creates it fresh
    if AGENT_INIT_DST.is_symlink():
        AGENT_INIT_DST.unlink()
        print("  ✓ Removed stale extension symlink (will be re-created after update)")

    print("[SemiShape] Pre-update complete.")


def _find_python() -> str:
    """Return path to the correct Python interpreter (prefer A0 venv)."""
    for candidate in [
        "/opt/venv-a0/bin/python",
        "/a0/venv/bin/python",
    ]:
        if Path(candidate).exists():
            return candidate
    return sys.executable
