"""
OpenAI Error Parser - Human-friendly error messages for Voice Mode.

This module intercepts OpenAI API errors (RateLimit, InsufficientFunds, etc.)
and converts them into helpful, actionable messages for the user.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple

# Configuration
logger = logging.getLogger("voicemode.error_parser")

class OpenAIErrorParser:
    """Parses OpenAI API errors into user-friendly messages."""
    
    @staticmethod
    def parse_error(e: Exception) -> Dict[str, Any]:
        """
        Parse an OpenAI error and return a structured response.
        
        Returns:
            Dict containing:
                - "message": Human friendly error message
                - "suggestion": What the user can do
                - "fallback": Recommended fallback (e.g., 'kokoro', 'whisper')
                - "category": Error category (e.g., 'auth', 'quota', 'rate_limit')
        """
        error_name = type(e).__name__
        error_msg = str(e)
        
        # Default response
        result = {
            "message": f"OpenAI API Error: {error_name}",
            "suggestion": "Check your internet connection and API key.",
            "fallback": None,
            "category": "unknown",
            "original_error": error_name
        }
        
        # 1. Quota / Billing errors
        if "insufficient_quota" in error_msg or "billing" in error_msg.lower():
            result.update({
                "message": "Your OpenAI API quota has been exceeded or billing is not set up.",
                "suggestion": "Check your usage at https://platform.openai.com/usage",
                "fallback": "local",
                "category": "quota"
            })
        
        # 2. Rate Limit errors
        elif "rate_limit" in error_msg.lower() or "RateLimitError" in error_name:
            result.update({
                "message": "OpenAI API rate limit reached.",
                "suggestion": "Wait a few seconds or switch to local models.",
                "fallback": "local",
                "category": "rate_limit"
            })
            
        # 3. Authentication errors
        elif "api_key" in error_msg.lower() or "AuthenticationError" in error_name:
            result.update({
                "message": "Invalid OpenAI API key.",
                "suggestion": "Run 'voicemode config set OPENAI_API_KEY <your-key>'",
                "fallback": "local",
                "category": "auth"
            })
            
        # 4. Model availability / Overloaded
        elif "overloaded" in error_msg.lower() or "engine_overloaded" in error_msg:
            result.update({
                "message": "OpenAI servers are currently overloaded.",
                "suggestion": "Try again in a moment or use local failover.",
                "fallback": "local",
                "category": "server_load"
            })
            
        # 5. Invalid Request (e.g. invalid parameters)
        elif "InvalidRequestError" in error_name or "invalid_request" in error_msg:
            result.update({
                "message": "The request to OpenAI was invalid.",
                "suggestion": "Check your configuration (e.g. voice name, model).",
                "fallback": None,
                "category": "invalid_request"
            })
            
        # 6. Connection Errors
        elif "connection" in error_msg.lower() or "Timeout" in error_name:
            result.update({
                "message": "Could not connect to OpenAI API.",
                "suggestion": "Check your internet connection.",
                "fallback": "local",
                "category": "connection"
            })

        return result

    @staticmethod
    def get_user_feedback(error_info: Dict[str, Any]) -> str:
        """Get the message to be displayed to the user or spoken."""
        msg = f"⚠️  {error_info['message']}"
        if error_info.get("suggestion"):
            msg += f"\n💡 Suggestion: {error_info['suggestion']}"
        if error_info.get("fallback") == "local":
            msg += "\n🔄 Tip: Use 'voicemode whisper' and 'voicemode kokoro' for local operation."
        return msg

    @staticmethod
    def should_failover(error_info: Dict[str, Any]) -> bool:
        """Determine if we should automatically failover to local models."""
        auto_failover_categories = ['quota', 'rate_limit', 'server_load', 'connection', 'auth']
        return error_info.get("category") in auto_failover_categories


def format_openai_error(e: Exception) -> str:
    """Helper function to quickly format an OpenAI error for the user."""
    parser = OpenAIErrorParser()
    info = parser.parse_error(e)
    return parser.get_user_feedback(info)


def get_fallback_advice(e: Exception, tool_type: str = "stt") -> str:
    """
    Get advice on which local tool to use as a fallback.
    
    Args:
        e: The exception that occurred
        tool_type: Either 'stt' or 'tts'
    """
    parser = OpenAIErrorParser()
    info = parser.parse_error(e)
    
    if not parser.should_failover(info):
        return ""
        
    if tool_type == "stt":
        return "You can use local Whisper instead: 'voicemode whisper start'"
    elif tool_type == "tts":
        return "You can use local Kokoro instead: 'voicemode kokoro start'"
    return "Check your local service status with 'voicemode status'"


# Example usage:
if __name__ == "__main__":
    # Mock some errors for testing
    class MockError(Exception): pass
    
    errors = [
        MockError("insufficient_quota: You exceeded your current quota..."),
        MockError("AuthenticationError: Incorrect API key provided..."),
        MockError("Rate limit reached for gpt-4o-mini-tts..."),
        MockError("Error communicating with OpenAI: Connection timed out")
    ]
    
    print("Testing OpenAI Error Parser:\n")
    for e in errors:
        print(f"Original: {e}")
        print(format_openai_error(e))
        print("-" * 40)
