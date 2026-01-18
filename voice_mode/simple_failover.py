"""
Simple try-failover implementation for Voice Mode.

Provides a basic mechanism to attempt a voice operation with a primary
provider and fall back to a secondary provider upon failure, without
requiring the full heavy health-checking discovery system.
"""

import asyncio
import logging
import os
from typing import Any, Callable, Dict, Optional, TypeVar, Awaitable

from voice_mode.config import logger

T = TypeVar('T')

class SimpleFailover:
    """Implements basic try-failover for voice operations."""

    @staticmethod
    async def try_with_failover(
        primary_fn: Callable[..., Awaitable[T]],
        secondary_fn: Callable[..., Awaitable[T]],
        *args,
        primary_name: str = "Primary",
        secondary_name: str = "Secondary",
        **kwargs
    ) -> T:
        """
        Attempt an operation with a primary function, falling back to secondary.
        
        Args:
            primary_fn: Primary async function to call
            secondary_fn: Fallback async function to call
            primary_name: Name of the primary provider (for logging)
            secondary_name: Name of the secondary provider (for logging)
            *args: Arguments to pass to both functions
            **kwargs: Keyword arguments to pass to both functions
            
        Returns:
            The result of whichever function succeeds
            
        Raises:
            The exception from the secondary function if both fail
        """
        try:
            logger.debug(f"Attempting {primary_name}...")
            return await primary_fn(*args, **kwargs)
        except Exception as e:
            logger.warning(f"{primary_name} failed: {e}. Falling back to {secondary_name}...")
            
            # Record original error for possible reporting
            kwargs['_original_error'] = e
            
            try:
                return await secondary_fn(*args, **kwargs)
            except Exception as secondary_e:
                logger.error(f"Both {primary_name} and {secondary_name} failed.")
                logger.error(f"Secondary error: {secondary_e}")
                # Re-raise the secondary error
                raise secondary_e

    @staticmethod
    def get_stt_failover_plan(preferred: Optional[str] = None) -> Tuple[str, str]:
        """Determine primary and secondary STT providers."""
        # Respect preferred if provided
        if preferred == "whisper":
            return "whisper", "openai"
        elif preferred == "openai":
            return "openai", "whisper"
            
        # Default logic
        from voice_mode.config import DEFAULT_STT_PROVIDER
        if DEFAULT_STT_PROVIDER == "whisper":
            return "whisper", "openai"
        return "openai", "whisper"

    @staticmethod
    def get_tts_failover_plan(preferred: Optional[str] = None) -> Tuple[str, str]:
        """Determine primary and secondary TTS providers."""
        # Respect preferred if provided
        if preferred == "kokoro":
            return "kokoro", "openai"
        elif preferred == "openai":
            return "openai", "kokoro"
            
        # Default logic
        from voice_mode.config import DEFAULT_TTS_PROVIDER
        if DEFAULT_TTS_PROVIDER == "kokoro":
            return "kokoro", "openai"
        return "openai", "kokoro"


# Helper for unified failover logic in higher-level tools
async def execute_with_failover(
    stt_or_tts: str,
    operation_fn: Callable[..., Awaitable[Any]],
    primary_provider: str,
    secondary_provider: str,
    *args,
    **kwargs
) -> Any:
    """
    Executes a voice operation with failover logic tailored to the tool type.
    """
    try:
        # Clone kwargs to avoid side effects
        call_kwargs = kwargs.copy()
        call_kwargs['provider'] = primary_provider
        
        logger.debug(f"Executing {stt_or_tts} with {primary_provider}...")
        return await operation_fn(*args, **call_kwargs)
        
    except Exception as e:
        logger.warning(f"{stt_or_tts} {primary_provider} failed: {e}")
        
        # Determine if we should failover based on error type (if possible)
        # For now, we simple-failover on any exception
        
        logger.info(f"Falling back to {secondary_provider} for {stt_or_tts}...")
        
        call_kwargs = kwargs.copy()
        call_kwargs['provider'] = secondary_provider
        call_kwargs['is_fallback'] = True
        call_kwargs['fallback_reason'] = str(e)
        
        return await operation_fn(*args, **call_kwargs)


if __name__ == "__main__":
    # Test stub
    async def primary():
        print("Running primary...")
        raise ValueError("Primary failed")
        
    async def secondary():
        print("Running secondary...")
        return "Secondary result"
        
    async def run_test():
        result = await SimpleFailover.try_with_failover(
            primary, secondary, primary_name="OpenAI", secondary_name="Local"
        )
        print(f"Final result: {result}")
        
    asyncio.run(run_test())
