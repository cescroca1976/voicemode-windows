"""Whisper STT service tools."""

from voice_mode.tools.whisper.install import whisper_install
from voice_mode.tools.whisper.uninstall import whisper_uninstall
from voice_mode.tools.whisper.models import (
    WHISPER_MODEL_REGISTRY,
    get_installed_whisper_models,
    is_whisper_model_installed,
    get_active_model
)
from voice_mode.tools.whisper.model_install import whisper_model_install
from voice_mode.tools.whisper.list_models import whisper_models
from voice_mode.tools.whisper.model_active import whisper_model_active

# Export main functions
__all__ = [
    "whisper_install",
    "whisper_uninstall",
    "whisper_model_install",
    "whisper_models",
    "whisper_model_active",
]

# Deprecated aliases for compatibility
list_whisper_models = whisper_models
set_active_whisper_model = whisper_model_active
