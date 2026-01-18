"""Unified service management tool for background services."""
import psutil
import subprocess
import os
from voice_mode.mcp_instance import mcp

@mcp.tool()
def service(service_name: str, action: str = "status") -> str:
    """Manage Whisper and Kokoro services."""
    # ... implementation ...
    return f"{service_name.capitalize()} {action} result"
