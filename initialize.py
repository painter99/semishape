"""
SemiShape Plugin - Initialization and Dependency Check

Checks Python version, required packages, and API keys.
Returns 0 for success, 1 for failure.
"""

import sys
import subprocess
import importlib
from pathlib import Path


# Required Python version
MIN_PYTHON_VERSION = (3, 10)

# Required packages with their import names
REQUIRED_PACKAGES = {
    "build123d": "build123d",
    "chromadb": "chromadb",
    "openai": "openai",
    "duckduckgo-search": "duckduckgo_search",
    "requests": "requests",
    "pyyaml": "yaml",
}


def check_python_version() -> bool:
    """Check if Python version meets minimum requirements."""
    version = sys.version_info[:2]
    if version < MIN_PYTHON_VERSION:
        print(f"[SemiShape] ✗ Python {version[0]}.{version[1]} is too old")
        print(f"[SemiShape]   Required: Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+")
        return False
    print(f"[SemiShape] ✓ Python {version[0]}.{version[1]} OK")
    return True


def check_and_install_packages() -> bool:
    """Check and install required packages."""
    missing = []
    
    # Check which packages are missing
    for package_name, import_name in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(import_name)
            print(f"[SemiShape] ✓ {package_name}")
        except ImportError:
            print(f"[SemiShape] ✗ {package_name} - missing")
            missing.append(package_name)
    
    if not missing:
        return True
    
    # Install missing packages
    print(f"[SemiShape] Installing {len(missing)} missing package(s)...")
    for package in missing:
        print(f"  → Installing {package}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet", package],
                check=True,
                capture_output=True
            )
            print(f"    ✓ {package} installed")
        except subprocess.CalledProcessError as e:
            print(f"    ✗ Failed to install {package}: {e}")
            return False
    
    return True


def check_api_keys() -> bool:
    """Check if required API keys are configured."""
    # Check for secrets.env or environment variables
    secrets_paths = [
        Path(".a0proj/secrets.env"),
        Path("../.a0proj/secrets.env"),
        Path("../../.a0proj/secrets.env"),
    ]
    
    api_key = None
    
    # Try to load from secrets.env
    for secrets_path in secrets_paths:
        if secrets_path.exists():
            with open(secrets_path) as f:
                for line in f:
                    if line.startswith("OPENROUTER_API_KEY="):
                        api_key = line.strip().split("=", 1)[1].strip('"\'')
                        break
    
    # Also check environment
    if not api_key:
        import os
        api_key = os.environ.get("OPENROUTER_API_KEY")
    
    if api_key:
        masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"[SemiShape] ✓ OPENROUTER_API_KEY found ({masked})")
        return True
    else:
        print("[SemiShape] ⚠ OPENROUTER_API_KEY not found in secrets.env or environment")
        print("[SemiShape]   Please set OPENROUTER_API_KEY in .a0proj/secrets.env")
        return False


def main() -> int:
    """
    Main initialization routine.
    
    Returns:
        0 for success, 1 for failure
    """
    print("=" * 50)
    print("[SemiShape] Initializing plugin...")
    print("=" * 50)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Check and install packages
    if not check_and_install_packages():
        success = False
    
    # Check API keys (warning only - plugin can work without it for local mode)
    api_ok = check_api_keys()
    if not api_ok:
        print("[SemiShape]   (Plugin can run in limited mode without API key)")
    
    print("=" * 50)
    if success:
        print("[SemiShape] ✓ Initialization complete")
        return 0
    else:
        print("[SemiShape] ✗ Initialization failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
