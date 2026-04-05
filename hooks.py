"""
SemiShape Plugin - Lifecycle Management

Handles plugin installation, uninstallation, and updates for Agent Zero integration.
All functions return True on success, False on failure.
"""

import os
import shutil
from pathlib import Path


def install(project_path: str) -> bool:
    """
    Install plugin - create necessary directories and setup.
    
    Called when plugin is first enabled for a project.
    
    Args:
        project_path: Root path of the project where plugin is installed
        
    Returns:
        bool: True if installation successful, False otherwise
    """
    try:
        print("[SemiShape] Installing plugin...")
        
        # Create directory structure
        dirs_to_create = [
            "data/cache",
            "data/vectorstore",
            "data/logs",
            "output",
            "helpers",
            "tools",
            "prompts"
        ]
        
        for dir_path in dirs_to_create:
            full_path = Path(project_path) / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created: {dir_path}")
        
        # Create .gitkeep files in empty dirs
        for dir_path in ["output", "data/logs"]:
            gitkeep = Path(project_path) / dir_path / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
        
        print("[SemiShape] Installation complete!")
        return True
        
    except Exception as e:
        print(f"[SemiShape] Installation failed: {e}")
        return False


def uninstall(project_path: str) -> bool:
    """
    Uninstall plugin - cleanup resources.
    
    Called when plugin is disabled or removed from project.
    Preserves user data (output/, data/vectorstore/) by default.
    
    Args:
        project_path: Root path of the project
        
    Returns:
        bool: True if uninstallation successful, False otherwise
    """
    try:
        print("[SemiShape] Uninstalling plugin...")
        
        # Remove cache (temporary data only)
        cache_path = Path(project_path) / "data" / "cache"
        if cache_path.exists():
            shutil.rmtree(cache_path)
            print("  ✓ Removed: data/cache")
        
        # Note: vectorstore and output are preserved for user data safety
        print("[SemiShape] Note: Preserved user data in data/vectorstore/ and output/")
        print("[SemiShape] Uninstallation complete!")
        return True
        
    except Exception as e:
        print(f"[SemiShape] Uninstallation failed: {e}")
        return False


def update(project_path: str, from_version: str, to_version: str) -> bool:
    """
    Update plugin - handle migration between versions.
    
    Called when plugin is updated to new version.
    
    Args:
        project_path: Root path of the project
        from_version: Current installed version
        to_version: Target version to update to
        
    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        print(f"[SemiShape] Updating from {from_version} to {to_version}...")
        
        # Version-specific migrations
        if from_version.startswith("0.1") and to_version.startswith("0.2"):
            # Migration from v0.1 to v0.2
            print("  → Migrating to v0.2 structure...")
            
            # Ensure new directories exist
            new_dirs = ["helpers", "tools", "prompts"]
            for dir_name in new_dirs:
                dir_path = Path(project_path) / dir_name
                dir_path.mkdir(exist_ok=True)
                print(f"    ✓ Ensured: {dir_name}/")
        
        # Ensure all standard directories exist
        install(project_path)
        
        print(f"[SemiShape] Update to {to_version} complete!")
        return True
        
    except Exception as e:
        print(f"[SemiShape] Update failed: {e}")
        return False
