"""MCP tool for installing Whisper models."""
import os
import shutil
import asyncio
import logging
from typing import Union, List, Optional, Dict, Any

from voice_mode.utils.services.common import download_file
from voice_mode.tools.whisper.models import (
    WHISPER_MODEL_REGISTRY,
    get_whisper_models_dir,
    is_whisper_model_installed,
    has_whisper_coreml_model,
    format_size
)

logger = logging.getLogger("voicemode")

async def whisper_model_install(
    model: Union[str, List[str]] = "base",
    force_download: Union[bool, str] = False,
    skip_core_ml: Union[bool, str] = False
) -> str:
    """Download and install Whisper models.
    
    Args:
        model: Model name, list of names, or 'all'.
        force_download: Re-download even if already exists.
        skip_core_ml: Skip downloading Core ML models on macOS.
        
    Returns:
        Status message with details of installed models.
    """
    # Normalize inputs
    if isinstance(force_download, str):
        force_download = force_download.lower() == "true"
    if isinstance(skip_core_ml, str):
        skip_core_ml = skip_core_ml.lower() == "true"
        
    models_to_install = []
    
    if model == "all":
        models_to_install = list(WHISPER_MODEL_REGISTRY.keys())
    elif isinstance(model, str):
        # Support comma separated string
        if "," in model:
            models_to_install = [m.strip() for m in model.split(",")]
        else:
            models_to_install = [model]
    else:
        models_to_install = model
        
    # Validate models
    invalid = [m for m in models_to_install if m not in WHISPER_MODEL_REGISTRY]
    if invalid:
        valid_models = ", ".join(WHISPER_MODEL_REGISTRY.keys())
        return f"Error: Invalid model name(s): {', '.join(invalid)}. \nValid models are: {valid_models}"
        
    # Filter out already installed models unless force
    if not force_download:
        already_installed = [m for m in models_to_install if is_whisper_model_installed(m)]
        models_to_install = [m for m in models_to_install if m not in already_installed]
        
        if not models_to_install:
            return f"All requested models are already installed: {', '.join(already_installed)}"
            
    # Perform downloads
    models_dir = get_whisper_models_dir()
    results = []
    total_size = 0
    
    logger.info(f"Downloading {len(models_to_install)} Whisper models to {models_dir}...")
    
    for model_name in models_to_install:
        info = WHISPER_MODEL_REGISTRY[model_name]
        filename = info["filename"]
        target_path = models_dir / filename
        
        # 1. Download standard GGML model
        url = f"https://huggingface.co/ggerganov/whisper.cpp/resolve/main/{filename}"
        logger.info(f"Downloading {model_name} model ({info['size_mb']} MB)...")
        
        try:
            success = await download_file(url, target_path)
            if success:
                results.append(f"✓ {model_name} ({info['size_mb']} MB)")
                total_size += info["size_mb"]
            else:
                results.append(f"✗ {model_name} (Download failed)")
                continue
        except Exception as e:
            results.append(f"✗ {model_name} (Error: {str(e)})")
            continue
            
        # 2. On macOS/Apple Silicon, try to get Core ML encoders if not skipped
        import platform
        if platform.system() == "Darwin" and platform.machine() == "arm64" and not skip_core_ml:
            if not has_whisper_coreml_model(model_name):
                logger.info(f"Downloading Core ML encoder for {model_name}...")
                coreml_filename = f"ggml-{model_name}-encoder.mlmodelc.zip"
                coreml_url = f"https://huggingface.co/ggerganov/whisper.cpp/resolve/main/{coreml_filename}"
                coreml_zip_path = models_dir / coreml_filename
                
                try:
                    if await download_file(coreml_url, coreml_zip_path):
                        # Unzip
                        import subprocess
                        subprocess.run(["unzip", "-o", str(coreml_zip_path), "-d", str(models_dir)], check=True)
                        coreml_zip_path.unlink() # Cleanup zip
                        results[-1] += " + Core ML"
                except Exception as e:
                    logger.warning(f"Failed to install Core ML for {model_name}: {e}")
                    
    summary = "\n".join(results)
    final_msg = f"Installation Complete!\n\nModels installed:\n{summary}\n\nTotal size: {format_size(total_size)}"
    
    # Check if we should recommend Core ML
    import platform
    if platform.system() == "Darwin" and platform.machine() == "arm64" and skip_core_ml:
        final_msg += "\n\nNote: You skipped Core ML models. Re-run without skip_core_ml=true for better performance on Mac."
        
    return final_msg
