"""
Pronunciation engine for TTS and STT.

Provides a set of rules for text replacement before TTS synthesis
and after STT transcription to handle common mispronunciations,
formatting (e.g., lowercase conversion), and custom aliases.

Rules are loaded from environment variables and built-in defaults.
"""

import os
import re
import logging
from typing import Dict, List, Tuple, Pattern

from voice_mode.config import logger


class Pronounce:
    """Handles pronunciation rules for TTS and STT text processing."""

    def __init__(self):
        self.tts_rules: List[Tuple[Pattern, str]] = []
        self.stt_rules: List[Tuple[Pattern, str]] = []
        self.load_rules()

    def load_rules(self):
        """Load rules from environment variables and defaults."""
        # TTS Rules (before speaking)
        # Format: VOICEMODE_TTS_REPLACE="cora=cora,claude=cloud"
        self._load_from_env("VOICEMODE_TTS_REPLACE", self.tts_rules)
        
        # STT Rules (after hearing)
        # Format: VOICEMODE_STT_REPLACE="kora=cora,claud=claude"
        self._load_from_env("VOICEMODE_STT_REPLACE", self.stt_rules)

        # Built-in defaults
        self._add_default_rules()

    def _load_from_env(self, env_var: str, rule_list: List[Tuple[Pattern, str]]):
        """Parse comma-separated rules from an environment variable."""
        raw_rules = os.getenv(env_var, "")
        if not raw_rules:
            return

        for rule in raw_rules.split(','):
            if '=' in rule:
                pattern, replacement = rule.split('=', 1)
                # Escape pattern for literal match but keep it case-insensitive
                # Use word boundaries to avoid partial matches
                compiled = re.compile(rf'\b{re.escape(pattern.strip())}\b', re.IGNORECASE)
                rule_list.append((compiled, replacement.strip()))

    def _add_default_rules(self):
        """Add hardcoded defaults for common issues."""
        # Default TTS fixes
        # 'cora' is often mispronounced as 'korah' with certain voices
        # self.tts_rules.append((re.compile(r'\bcora\b', re.IGNORECASE), "Cora"))
        pass

    def process_tts(self, text: str) -> str:
        """Process text before sending to TTS engine."""
        if not text:
            return text
            
        result = text
        for pattern, replacement in self.tts_rules:
            result = pattern.sub(replacement, result)
        
        return result

    def process_stt(self, text: str) -> str:
        """Process text after receiving from STT engine."""
        if not text:
            return text
            
        # 1. Basic cleaning
        result = text.strip()
        
        # 2. Apply rules
        for pattern, replacement in self.stt_rules:
            result = pattern.sub(replacement, result)
            
        # 3. Handle casing (default: normalize to lower for matching)
        # result = result.lower()
        
        return result


# Global instance
_engine = None

def get_pronounce_engine() -> Pronounce:
    """Get the global pronunciation engine instance."""
    global _engine
    if _engine is None:
        _engine = Pronounce()
    return _engine


def process_text_for_tts(text: str) -> str:
    """Utility function to process text for TTS."""
    return get_pronounce_engine().process_tts(text)


def process_text_from_stt(text: str) -> str:
    """Utility function to process text from STT."""
    return get_pronounce_engine().process_stt(text)


if __name__ == "__main__":
    # Test cases
    os.environ["VOICEMODE_TTS_REPLACE"] = "cora=cora,claude=clohde"
    os.environ["VOICEMODE_STT_REPLACE"] = "kora=cora,claud=claude"
    
    engine = Pronounce()
    
    # Test TTS
    t1 = "Hello cora, tell claude to wait."
    p1 = engine.process_tts(t1)
    print(f"TTS In:  {t1}")
    print(f"TTS Out: {p1}")
    
    # Test STT
    t2 = "Hey kora, i heard claud is here."
    p2 = engine.process_stt(t2)
    print(f"STT In:  {t2}")
    print(f"STT Out: {p2}")
