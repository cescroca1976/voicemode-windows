"""Configuration management tools for voice-mode."""

import os
import re
from pathlib import Path
from typing import Dict, Optional, List
from voice_mode.mcp_instance import mcp
from voice_mode.config import BASE_DIR, reload_configuration, find_voicemode_env_files
import logging

logger = logging.getLogger("voicemode")
# ... (Full content of configuration_management.py)
