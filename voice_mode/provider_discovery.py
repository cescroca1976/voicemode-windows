"""
Voice provider discovery and health checking.

This module probes local and remote endpoints to identify available
TTS and STT capabilities.
"""

import asyncio
import httpx
import logging
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from voice_mode.config import (
    OPENAI_API_KEY, 
    KOKORO_SERVER_URL, 
    WHISPER_SERVER_URL,
    logger
)

@dataclass
class VoiceProvider:
    name: str
    type: str  # "tts" or "stt"
    url: Optional[str] = None
    priority: int = 100
    is_local: bool = False
    healthy: bool = False
    available_models: List[str] = field(default_factory=list)
    available_voices: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class ProviderDiscovery:
    """Discovers and checks health of voice providers."""
    
    def __init__(self):
        self.providers: Dict[str, VoiceProvider] = {}
        
    async def discover_all(self):
        """Execute discovery of all configured providers."""
        # 1. OpenAI (Cloud)
        await self._check_openai()
        
        # 2. Kokoro (Local TTS)
        await self._check_kokoro()
        
        # 3. Whisper (Local STT)
        await self._check_whisper()
        
        return self.providers

    async def _check_openai(self):
        """Check OpenAI availability."""
        if not OPENAI_API_KEY:
            return
            
        # We assume OpenAI is available if key exists, 
        # but could do a lightweight model check
        self.providers["openai"] = VoiceProvider(
            name="OpenAI",
            type="tts_stt",
            is_local=False,
            healthy=True,
            available_models=["tts-1", "tts-1-hd", "whisper-1"],
            available_voices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        )

    async def _check_kokoro(self):
        """Probe local Kokoro TTS server."""
        if not KOKORO_SERVER_URL:
            return
            
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                response = await client.get(f"{KOKORO_SERVER_URL}/v1/voices")
                if response.status_code == 200:
                    voices_data = response.json()
                    # kokoro-fastapi returns list of strings or dicts
                    voices = []
                    if isinstance(voices_data, list):
                        voices = voices_data
                    elif isinstance(voices_data, dict) and "voices" in voices_data:
                        voices = voices_data["voices"]
                        
                    self.providers["kokoro"] = VoiceProvider(
                        name="Kokoro",
                        type="tts",
                        url=KOKORO_SERVER_URL,
                        is_local=True,
                        healthy=True,
                        available_voices=voices,
                        available_models=["kokoro"]
                    )
        except (httpx.ConnectError, httpx.TimeoutException):
            logger.debug("Kokoro server not reachable")
            # Create unhealthy record even if offline
            self.providers["kokoro"] = VoiceProvider(
                name="Kokoro",
                type="tts",
                url=KOKORO_SERVER_URL,
                is_local=True,
                healthy=False
            )

    async def _check_whisper(self):
        """Probe local Whisper STT server."""
        if not WHISPER_SERVER_URL:
            return
            
        try:
            # First try a generic health check /v1/models if it exists
            # Otherwise we'll just check if port is open
            async with httpx.AsyncClient(timeout=1.0) as client:
                response = await client.get(f"{WHISPER_SERVER_URL}/v1/models")
                if response.status_code == 200:
                    self.providers["whisper"] = VoiceProvider(
                        name="Whisper",
                        type="stt",
                        url=WHISPER_SERVER_URL,
                        is_local=True,
                        healthy=True
                    )
        except (httpx.ConnectError, httpx.TimeoutException):
            logger.debug("Whisper server not reachable")
            self.providers["whisper"] = VoiceProvider(
                name="Whisper",
                type="stt",
                url=WHISPER_SERVER_URL,
                is_local=True,
                healthy=False
            )

    def get_healthy_tts_providers(self) -> List[VoiceProvider]:
        """Get list of healthy providers capable of TTS."""
        return [p for p in self.providers.values() 
                if p.healthy and ("tts" in p.type or "tts_stt" in p.type)]

    def get_healthy_stt_providers(self) -> List[VoiceProvider]:
        """Get list of healthy providers capable of STT."""
        return [p for p in self.providers.values() 
                if p.healthy and ("stt" in p.type or "tts_stt" in p.type)]

    def get_preferred_tts(self, preferred: Optional[str] = None) -> Optional[VoiceProvider]:
        """Select preferred TTS provider with failover logic."""
        if preferred and preferred in self.providers and self.providers[preferred].healthy:
            return self.providers[preferred]
            
        # Auto-selection logic: local kokoro first, then openai
        if "kokoro" in self.providers and self.providers["kokoro"].healthy:
            return self.providers["kokoro"]
            
        if "openai" in self.providers and self.providers["openai"].healthy:
            return self.providers["openai"]
            
        return None

    def get_preferred_stt(self, preferred: Optional[str] = None) -> Optional[VoiceProvider]:
        """Select preferred STT provider with failover logic."""
        if preferred and preferred in self.providers and self.providers[preferred].healthy:
            return self.providers[preferred]
            
        # Auto-selection logic: local whisper first, then openai
        if "whisper" in self.providers and self.providers["whisper"].healthy:
            return self.providers["whisper"]
            
        if "openai" in self.providers and self.providers["openai"].healthy:
            return self.providers["openai"]
            
        return None


# Global registry instance
_registry = ProviderDiscovery()

async def get_provider_registry() -> ProviderDiscovery:
    """Get the initialized provider registry."""
    # We could do background refreshing here but for now discovery is manual
    if not _registry.providers:
        await _registry.discover_all()
    return _registry
