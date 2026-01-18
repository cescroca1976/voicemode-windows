"""MCP tool for listing Whisper models."""
from typing import Dict, Any, List
from voice_mode.mcp_instance import mcp
from voice_mode.tools.whisper.models import (
    WHISPER_MODEL_REGISTRY,
    get_installed_whisper_models,
    get_active_model,
    has_whisper_coreml_model,
    format_size
)

@mcp.tool()
async def whisper_models() -> Dict[str, Any]:
    """List all available and installed Whisper speech-to-text models.
    
    Returns:
        Dict with model list and status information
    """
    installed = get_installed_whisper_models()
    active = get_active_model()
    
    models = []
    total_installed_size = 0
    
    for name, info in WHISPER_MODEL_REGISTRY.items():
        is_installed = name in installed
        has_coreml = has_whisper_coreml_model(name)
        
        model_data = {
            "name": name,
            "installed": is_installed,
            "active": name == active,
            "size_mb": info["size_mb"],
            "size_formatted": format_size(info["size_mb"]),
            "languages": info["languages"],
            "description": info["description"],
            "has_core_ml": has_coreml
        }
        
        if is_installed:
            total_installed_size += info["size_mb"]
            
        models.append(model_data)
        
    # Sort: active first, then installed, then alphabetical
    models.sort(key=lambda x: (not x["active"], not x["installed"], x["name"]))
    
    return {
        "success": True,
        "models": models,
        "count": len(models),
        "installed_count": len(installed),
        "total_installed_size_mb": total_installed_size,
        "total_installed_size_formatted": format_size(total_installed_size),
        "active_model": active,
        "instructions": (
            "To install a model: whisper_model_install(model='name')\n"
            "To change active model: whisper_model_active(model_name='name')\n"
            "To remove a model: whisper_model_remove(model_name='name')"
        )
    }
