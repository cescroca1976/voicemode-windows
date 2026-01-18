"""
Voice provider selection and initialization logic.

Provides a unified interface for selecting and using different TTS and STT
providers based on configuration and availability.
"""

from typing import Optional, Dict, Any, List
import logging

from voice_mode.config import (
    DEFAULT_TTS_PROVIDER,
    DEFAULT_STT_PROVIDER,
    OPENAI_API_KEY,
    KOKORO_SERVER_URL,
    WHISPER_SERVER_URL,
    logger
)

# Provider types
TTS = "tts"
STT = "stt"

class ProviderManager:
    """Manages voice provider selection and configuration."""

    def __init__(self):
        self.tts_provider = DEFAULT_TTS_PROVIDER
        self.stt_provider = DEFAULT_STT_PROVIDER

    def get_tts_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for a TTS provider."""
        p = provider or self.tts_provider
        
        if p == "openai":
            return {
                "name": "OpenAI",
                "api_key": OPENAI_API_KEY,
                "base_url": None,
                "models": ["tts-1", "tts-1-hd"],
                "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            }
        elif p == "kokoro":
            return {
                "name": "Kokoro",
                "api_key": "not-needed",
                "base_url": KOKORO_SERVER_URL,
                "models": ["kokoro"],
                "voices": [] # Populated dynamically during discovery
            }
        
        return {}

    def get_stt_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for an STT provider."""
        p = provider or self.stt_provider
        
        if p == "openai":
            return {
                "name": "OpenAI",
                "api_key": OPENAI_API_KEY,
                "base_url": None,
                "models": ["whisper-1"]
            }
        elif p == "whisper":
            return {
                "name": "Local Whisper",
                "api_key": "not-needed",
                "base_url": WHISPER_SERVER_URL,
                "models": ["base", "small", "medium", "large"]
            }
        
        return {}

    def set_preferred_tts(self, provider: str):
        """Set the preferred TTS provider."""
        if provider not in ["openai", "kokoro"]:
            raise ValueError(f"Invalid TTS provider: {provider}")
        self.tts_provider = provider

    def set_preferred_stt(self, provider: str):
        """Set the preferred STT provider."""
        if provider not in ["openai", "whisper"]:
            raise ValueError(f"Invalid STT provider: {provider}")
        self.stt_provider = provider


# Global provider manager instance
_manager = ProviderManager()

def get_provider_manager() -> ProviderManager:
    """Get the global provider manager instance."""
    return _manager


def get_active_tts_provider() -> str:
    """Get the name of the currently active TTS provider."""
    return get_provider_manager().tts_provider


def get_active_stt_provider() -> str:
    """Get the name of the currently active STT provider."""
    return get_provider_manager().stt_provider


async def check_provider_health(provider_name: str, provider_type: str = TTS) -> bool:
    """
    Check if a provider is healthy and responsive.
    
    This is a simplified version of health checking that doesn't 
    require the full provider_discovery module to be loaded.
    """
    import httpx
    
    manager = get_provider_manager()
    if provider_type == TTS:
        config = manager.get_tts_config(provider_name)
    else:
        config = manager.get_stt_config(provider_name)
        
    if not config:
        return False
        
    # OpenAI is assumed healthy if key exists (unless we do an actual API call)
    if provider_name == "openai":
        return bool(config.get("api_key"))
        
    # Local services require a network probe
    url = config.get("base_url")
    if not url:
        return False
        
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            # Simple probe - if it's kokoro, check /v1/voices. 
            # If whisper, check /v1/models (if supported) or just the root.
            endpoint = "/v1/voices" if provider_name == "kokoro" else "/"
            response = await client.get(f"{url}{endpoint}")
            return response.status_code < 500
    except (httpx.ConnectError, httpx.TimeoutException):
        return False
    except Exception:
        return False
