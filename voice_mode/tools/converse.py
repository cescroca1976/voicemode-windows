"""Conversation tools for voice interactions."""
import numpy as np
import sounddevice as sd
import logging
import os
import time
from typing import Optional, Dict, Any, Tuple
from voice_mode.mcp_instance import mcp

logger = logging.getLogger("voicemode")

SAMPLE_RATE = 24000
CHANNELS = 1

def record_audio(duration: float) -> np.ndarray:
    """Record audio for a fixed duration."""
    try:
        samples_to_record = int(duration * SAMPLE_RATE)
        recording = sd.rec(
            samples_to_record,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=np.int16
        )
        sd.wait()
        return recording.flatten()
    except Exception as e:
        logger.error(f"Recording failed: {e}")
        return np.array([], dtype=np.int16)

@mcp.tool()
async def converse(message: str) -> str:
    """Send a message and get a voice response."""
    # ... implementation ...
    return f"Response to: {message}"
