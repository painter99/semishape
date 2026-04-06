"""
SemiShape Plugin - Dependency Installer

Run automatically during plugin enable (called from hooks.py install).
Defines main() that returns 0 on success, non-zero on failure.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def _find_python() -> str:
    """Return path to the correct Python interpreter (prefer A0 venv)."""
    for candidate in [
        "/opt/venv-a0/bin/python",
        "/a0/venv/bin/python",
    ]:
        if Path(candidate).exists():
            return candidate
    return sys.executable


def _install(pip_name: str, python: str) -> None:
    """Install a package using uv (preferred) or pip as fallback."""
    uv = shutil.which("uv")
    if uv:
        subprocess.check_call(
            [uv, "pip", "install", pip_name, "--python", python],
            stdout=subprocess.DEVNULL,
        )
    else:
        subprocess.check_call(
            [python, "-m", "pip", "install", "--quiet", pip_name]
        )


def main() -> int:
    """
    Install required dependencies for SemiShape.

    Returns:
        0 on success, 1 on failure.
    """
    python = _find_python()
    print(f"[SemiShape] Using Python: {python}")

    # (import_name, pip_package_spec)
    DEPS = [
        ("build123d",          "build123d>=0.10.0"),
        ("chromadb",           "chromadb>=0.5.0"),
        ("openai",             "openai>=1.0.0"),
        ("duckduckgo_search",  "duckduckgo-search>=3.0.0"),
        ("requests",           "requests>=2.31.0"),
        ("yaml",               "pyyaml>=6.0"),
        ("sentence_transformers", "sentence-transformers>=2.0.0"),
    ]

    for import_name, pip_spec in DEPS:
        # Check if already importable
        result = subprocess.run(
            [python, "-c", f"import {import_name}"],
            capture_output=True,
        )
        if result.returncode == 0:
            print(f"  ✓ {pip_spec.split('>=')[0]} — already installed")
            continue

        # Install missing package
        print(f"  → Installing {pip_spec} ...")
        try:
            _install(pip_spec, python)
            print(f"  ✓ {pip_spec.split('>=')[0]} — installed")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Failed to install {pip_spec}: {e}")
            return 1

    print("[SemiShape] All dependencies ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
