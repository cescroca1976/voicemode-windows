"""Unified service management tool for voice mode services."""

import asyncio
import json
import logging
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Literal, Optional, Dict, Any, Union

import psutil

from voice_mode.mcp_instance import mcp
# ... (Full content of service.py)
