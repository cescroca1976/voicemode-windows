"""MCP tool for managing the active Whisper model."""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from voice_mode.mcp_instance import mcp
from voice_mode.config import update_env_file
from voice_mode.tools.whisper.models import (
    WHISPER_MODEL_REGISTRY,
    is_whisper_model_installed,
    get_active_model
)

@mcp.tool()
async def whisper_model_active(model_name: Optional[str] = None) -> Dict[str, Any]:
    """Show or change the active Whisper speech-to-text model.
    
    Args:
        model_name: Name of the model to activate (optional)
        
    Returns:
        Status of active model
    """
    if model_name is None:
        # Just show current
        active = get_active_model()
        return {
            "success": True,
            "active_model": active,
            "installed": is_whisper_model_installed(active),
            "message": f"Current active model is '{active}'"
        }
        
    # Check if valid
    if model_name not in WHISPER_MODEL_REGISTRY:
        return {
            "success": False,
            "error": f"Model '{model_name}' not found. Use whisper_models() to see available models."
        }
        
    # Check if installed
    if not is_whisper_model_installed(model_name):
        return {
            "success": False,
            "error": f"Model '{model_name}' is not installed. Install it first with whisper_model_install(model='{model_name}')"
        }
        
    # Update config
    update_env_file("VOICEMODE_WHISPER_MODEL", model_name)
    os.environ["VOICEMODE_WHISPER_MODEL"] = model_name
    
    return {
        "success": True,
        "message": f"Successfully set active model to '{model_name}'",
        "active_model": model_name,
        "requires_restart": "Whisper service needs to be restarted for this to take effect: service(service_name='whisper', action='restart')"
    }
