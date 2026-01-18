"""Enhanced version detection for voice mode."""

import os
import subprocess
from pathlib import Path
from typing import Optional

from .__version__ import __version__ as base_version


def get_git_commit_hash(short: bool = True) -> Optional[str]:
    """Get the current git commit hash."""
    try:
        module_dir = Path(__file__).parent
        cmd = ["git", "rev-parse", "--short", "HEAD"] if short else ["git", "rev-parse", "HEAD"]
        result = subprocess.run(
            cmd,
            cwd=module_dir,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def is_git_repository() -> bool:
    """Check if we're running from a git repository."""
    try:
        module_dir = Path(__file__).parent
        current = module_dir
        while current != current.parent:
            if (current / ".git").exists():
                return True
            current = current.parent
        return False
    except Exception:
        return False


def get_version() -> str:
    """Get the version string, including dev suffix if running from git."""
    version = base_version
    if is_git_repository():
        commit = get_git_commit_hash()
        if commit:
            try:
                module_dir = Path(__file__).parent
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=module_dir,
                    capture_output=True,
                    text=True
                )
                has_changes = bool(result.stdout.strip())
                version = f"{base_version}-dev.{commit}"
                if has_changes:
                    version += "-dirty"
            except Exception:
                version = f"{base_version}-dev.{commit}"
    return version


__version__ = get_version()
