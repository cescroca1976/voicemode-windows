"""Configuration and shared utilities."""
import os
from pathlib import Path

BASE_DIR = Path.home() / ".voicemode"
EVENT_LOG_ENABLED = True
EVENT_LOG_DIR = str(BASE_DIR / "logs/events")

def setup_logging():
    import logging
    return logging.getLogger("voicemode")
