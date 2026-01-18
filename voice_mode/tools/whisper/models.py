"""Whisper model registry and utilities."""
import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, TypedDict

from voice_mode.config import BASE_DIR

logger = logging.getLogger("voicemode")

class ModelInfo(TypedDict):
    size_mb: int
    languages: str
    description: str
    filename: str

# Central registry of all available Whisper models
# Size is download size in MB
WHISPER_MODEL_REGISTRY: Dict[str, ModelInfo] = {
    "tiny": {
        "size_mb": 39,
        "languages": "Multilingual",
        "description": "Fastest, least accurate",
        "filename": "ggml-tiny.bin"
    },
    "tiny.en": {
        "size_mb": 39,
        "languages": "English only",
        "description": "Fastest, English only",
        "filename": "ggml-tiny.en.bin"
    },
    "base": {
        "size_mb": 74,
        "languages": "Multilingual",
        "description": "Very fast, basic accuracy",
        "filename": "ggml-base.bin"
    },
    "base.en": {
        "size_mb": 74,
        "languages": "English only",
        "description": "Very fast, basic English accuracy",
        "filename": "ggml-base.en.bin"
    },
    "small": {
        "size_mb": 244,
        "languages": "Multilingual",
        "description": "Fast, good balance",
        "filename": "ggml-small.bin"
    },
    "small.en": {
        "size_mb": 244,
        "languages": "English only",
        "description": "Fast, good English accuracy",
        "filename": "ggml-small.en.bin"
    },
    "medium": {
        "size_mb": 769,
        "languages": "Multilingual",
        "description": "Accurate, moderate speed",
        "filename": "ggml-medium.bin"
    },
    "medium.en": {
        "size_mb": 769,
        "languages": "English only",
        "description": "Accurate, English only",
        "filename": "ggml-medium.en.bin"
    },
    "large-v1": {
        "size_mb": 1600,
        "languages": "Multilingual",
        "description": "Most accurate (original large)",
        "filename": "ggml-large-v1.bin"
    },
    "large-v2": {
        "size_mb": 1600,
        "languages": "Multilingual",
        "description": "Enhanced accuracy (v2)",
        "filename": "ggml-large-v2.bin"
    },
    "large-v3": {
        "size_mb": 1600,
        "languages": "Multilingual",
        "description": "Best overall accuracy (v3)",
        "filename": "ggml-large-v3.bin"
    },
    "large-v3-turbo": {
        "size_mb": 1600,
        "languages": "Multilingual",
        "description": "Faster large model with good accuracy",
        "filename": "ggml-large-v3-turbo.bin"
    }
}

DEFAULT_WHISPER_MODEL = "base"

def get_whisper_models_dir() -> Path:
    """Get the directory where Whisper models are stored."""
    models_dir = BASE_DIR / "models" / "whisper"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir

def get_installed_whisper_models() -> List[str]:
    """Get list of currently installed Whisper model names."""
    models_dir = get_whisper_models_dir()
    installed = []
    
    for name, info in WHISPER_MODEL_REGISTRY.items():
        if (models_dir / info["filename"]).exists():
            installed.append(name)
            
    return installed

def is_whisper_model_installed(model_name: str) -> bool:
    """Check if a specific Whisper model is installed."""
    if model_name not in WHISPER_MODEL_REGISTRY:
        return False
        
    models_dir = get_whisper_models_dir()
    return (models_dir / WHISPER_MODEL_REGISTRY[model_name]["filename"]).exists()

def has_whisper_coreml_model(model_name: str) -> bool:
    """Check if a Core ML version of the model exists (macOS only)."""
    if model_name not in WHISPER_MODEL_REGISTRY:
        return False
        
    models_dir = get_whisper_models_dir()
    # Core ML models are folders named ggml-{name}-encoder.mlmodelc
    coreml_dir = models_dir / f"ggml-{model_name}-encoder.mlmodelc"
    return coreml_dir.exists() and coreml_dir.is_dir()

def get_active_model() -> str:
    """Get the currently active Whisper model name from environment."""
    return os.environ.get("VOICEMODE_WHISPER_MODEL", DEFAULT_WHISPER_MODEL)

def format_size(size_mb: float) -> str:
    """Format size in MB for display."""
    if size_mb < 1000:
        return f"{size_mb} MB"
    return f"{size_mb/1024:.2f} GB"

def remove_whisper_model(model_name: str, remove_coreml: bool = True) -> Dict[str, Any]:
    """
    Remove an installed Whisper model.
    
    Args:
        model_name: Name of the model to remove
        remove_coreml: Whether to also remove the Core ML version if it exists
        
    Returns:
        Dict with status and details
    """
    if model_name not in WHISPER_MODEL_REGISTRY:
        return {
            "success": False, 
            "error": f"Model '{model_name}' not found in registry"
        }
        
    models_dir = get_whisper_models_dir()
    model_info = WHISPER_MODEL_REGISTRY[model_name]
    model_file = models_dir / model_info["filename"]
    
    space_freed_mb = 0
    removed_files = []
    
    # 1. Remove standard GGML model
    if model_file.exists():
        size = model_file.stat().st_size / (1024 * 1024)
        model_file.unlink()
        space_freed_mb += size
        removed_files.append(model_info["filename"])
        
    # 2. Remove Core ML model if requested
    if remove_coreml:
        coreml_dir = models_dir / f"ggml-{model_name}-encoder.mlmodelc"
        if coreml_dir.exists():
            # Calculate recursive size for directory
            size = sum(f.stat().st_size for f in coreml_dir.glob('**/*') if f.is_file()) / (1024 * 1024)
            shutil.rmtree(coreml_dir)
            space_freed_mb += size
            removed_files.append(f"ggml-{model_name}-encoder.mlmodelc (Core ML)")
            
    if not removed_files:
        return {
            "success": False,
            "message": f"Model {model_name} was not installed"
        }
        
    return {
        "success": True,
        "message": f"Successfully removed model {model_name}",
        "removed_files": removed_files,
        "space_freed_mb": round(space_freed_mb, 1)
    }

def benchmark_whisper_model(model_name: str, sample_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Benchmark the performance of a specific model.
    
    Args:
        model_name: Name of model to benchmark
        sample_file: Path to optional sample audio file
        
    Returns:
        Dict with benchmark results
    """
    # This is a stub for the actual implementation in whisper-server
    # In practice, we call the whisper-server binary with the benchmark flag
    import subprocess
    import time
    
    if not is_whisper_model_installed(model_name):
        return {"success": False, "error": f"Model {model_name} is not installed"}
        
    whisper_dir = BASE_DIR / "services" / "whisper"
    binary = whisper_dir / "whisper-server"
    if not binary.exists():
        # Fallback to current dir if not in services/whisper
        binary = whisper_dir / "server"
        if not binary.exists():
            return {"success": False, "error": "whisper-server binary not found. Install whisper first."}
            
    models_dir = get_whisper_models_dir()
    model_path = models_dir / WHISPER_MODEL_REGISTRY[model_name]["filename"]
    
    # Use internal samples if provided, otherwise use a generic 30s audio for testing
    # whisper.cpp has a 'bench' command or we can just measure a transcription
    test_audio = sample_file or str(whisper_dir / "samples" / "jfk.wav")
    
    if not os.path.exists(test_audio):
        # Create a simple dummy test if needed or return error
        return {"success": False, "error": f"Sample file not found: {test_audio}"}
        
    logger.info(f"Benchmarking model {model_name} with {test_audio}...")
    
    try:
        start_time = time.time()
        # We'll use the 'main' tool from whisper.cpp for benchmarking if available
        # otherwise we use the server for a real-world test
        cmd = [
            str(whisper_dir / "main"),
            "-m", str(model_path),
            "-f", test_audio,
            "-nt" # no timestamps for pure speed test
        ]
        
        # Check if main exists
        if not os.path.exists(cmd[0]):
             return {"success": False, "error": "whisper.cpp 'main' utility not found for benchmarking."}
             
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        end_time = time.time()
        
        if process.returncode != 0:
            return {"success": False, "error": f"Benchmark failed: {process.stderr}"}
            
        total_time = end_time - start_time
        
        # Parse output for actual processing metrics if possible
        # whisper.cpp main prints timing info at the end
        # Example: whisper_print_timings:     load time =   123.45 ms
        #          whisper_print_timings:     total time =  1234.56 ms
        
        load_time_ms = 0
        p_time_ms = 0
        
        for line in process.stderr.splitlines():
            if "load time =" in line:
                try: load_time_ms = float(line.split("=")[1].strip().split()[0])
                except: pass
            if "total time =" in line:
                try: p_time_ms = float(line.split("=")[1].strip().split()[0])
                except: pass
        
        return {
            "success": True,
            "model": model_name,
            "total_time_ms": round(total_time * 1000, 2),
            "load_time_ms": load_time_ms,
            "decode_time_ms": p_time_ms,
            "real_time_factor": round(30000 / p_time_ms, 2) if p_time_ms > 0 else 0 # Assuming jfk.wav is ~30s
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Benchmark timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}
