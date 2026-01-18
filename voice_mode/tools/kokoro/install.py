"""MCP tool for installing Kokoro TTS service."""
import os
import shutil
import platform
import subprocess
import logging
import asyncio
from typing import Optional, Dict, Any, Union
from pathlib import Path

from voice_mode.mcp_instance import mcp
from voice_mode.config import BASE_DIR, update_env_file
from voice_mode.utils.services.common import (
    check_dependency, 
    clone_or_update_repo,
    find_process_by_port
)

logger = logging.getLogger("voicemode")

KOKORO_REPO = "https://github.com/remsky/kokoro-fastapi"
KOKORO_VERSION = "v0.1.3" # Target version

@mcp.tool()
async def kokoro_install(
    install_dir: Optional[str] = None,
    models_dir: Optional[str] = None,
    port: Union[int, str] = 8880,
    force_reinstall: Union[bool, str] = False,
    use_gpu: Union[bool, str] = True
) -> Dict[str, Any]:
    """Install kokoro-fastapi as a background text-to-speech service.
    
    Args:
        install_dir: Directory to install into (defaults to ~/.voicemode/services/kokoro)
        models_dir: Directory for Kokoro models (defaults to ~/.voicemode/models/kokoro)
        port: Port to run the server on (default: 8880)
        force_reinstall: Re-clone and recreate venv even if already installed
        use_gpu: Enable GPU acceleration (CUDA on Linux, defaults to CPU on Mac currently)
        
    Returns:
        Dict with installation status and details
    """
    system = platform.system()
    
    # Use standard directory if not specified
    if install_dir is None:
        install_dir = str(BASE_DIR / "services" / "kokoro")
    if models_dir is None:
        models_dir = str(BASE_DIR / "models" / "kokoro")
        
    install_path = Path(install_dir)
    models_path = Path(models_dir)
    os.makedirs(install_path.parent, exist_ok=True)
    os.makedirs(models_path, exist_ok=True)
    
    # Normalize bools
    if isinstance(force_reinstall, str):
        force_reinstall = force_reinstall.lower() == "true"
    if isinstance(use_gpu, str):
        use_gpu = use_gpu.lower() == "true"
        
    logger.info(f"Starting Kokoro installation on {system}...")
    
    # 1. Dependency Checks
    deps = ["git", "python3"]
    if system == "Linux":
        deps.append("ffmpeg")
        deps.append("python3-venv")
            
    for dep in deps:
        if not check_dependency(dep):
            return {
                "success": False,
                "error": f"Missing required dependency: {dep}. Please install it and try again."
            }
            
    # Check for uv (preferred for speed)
    has_uv = check_dependency("uv")
            
    # 2. Clone Repository
    try:
        if not clone_or_update_repo(KOKORO_REPO, str(install_path), KOKORO_VERSION, force=force_reinstall):
            return {"success": False, "error": "Failed to clone or update kokoro-fastapi repository"}
    except Exception as e:
        return {"success": False, "error": f"Repository error: {str(e)}"}
        
    # 3. Create Virtual Environment and Install Dependencies
    venv_path = install_path / ".venv"
    pip_cmd = [str(venv_path / "bin" / "pip"), "install"]
    
    try:
        if force_reinstall and venv_path.exists():
            shutil.rmtree(venv_path)
            
        if not venv_path.exists():
            logger.info("Creating virtual environment...")
            if has_uv:
                subprocess.run(["uv", "venv", str(venv_path)], check=True)
                pip_cmd = ["uv", "pip", "install", "--python", str(venv_path / "bin" / "python")]
            else:
                subprocess.run(["python3", "-m", "venv", str(venv_path)], check=True)
                
            logger.info("Installing dependencies (this may take a few minutes)...")
            # Upgrade pip first
            subprocess.run(pip_cmd + ["--upgrade", "pip"], check=True)
            
            # Install requirements
            subprocess.run(pip_cmd + ["-r", "requirements.txt"], cwd=install_path, check=True)
            
            # Install specific voice dependencies
            subprocess.run(pip_cmd + ["soundfile", "phonemizer-fork"], check=True)
            
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": f"Dependency installation failed: {str(e)}"}
        
    # 4. Set up Start Script
    # The repo provides different start scripts based on setup
    start_script = install_path / "start.sh"
    
    # Determine the best way to start based on GPU
    gpu_available = False
    if system == "Linux" and use_gpu:
        try:
            subprocess.run(["nvidia-smi"], capture_output=True, check=True)
            gpu_available = True
        except:
            pass
            
    # Create a custom launcher to ensure correct environment
    launcher_path = install_path / "voicemode-start.sh"
    with open(launcher_path, "w") as f:
        f.write(f"""#!/bin/bash
export KOKORO_MODELS_DIR="{models_path}"
export PORT={port}
export HOST=127.0.0.1
cd {install_path}
source .venv/bin/activate
# Run the fastapi server directly
exec python -m uvicorn main:app --host $HOST --port $PORT
""")
    os.chmod(launcher_path, 0o755)
    
    # 5. Set up System Service
    service_status = "Skipped"
    if system == "Darwin":
        service_status = await _setup_macos_service(install_path, launcher_path, port)
    elif system == "Linux":
        service_status = await _setup_linux_service(install_path, launcher_path, port)
        
    # Update global config
    update_env_file("VOICEMODE_KOKORO_PORT", port)
    update_env_file("VOICEMODE_KOKORO_DIR", str(install_path))
    update_env_file("VOICEMODE_KOKORO_MODELS_DIR", str(models_path))
    
    return {
        "success": True,
        "message": "kokoro-fastapi installed successfully",
        "install_dir": str(install_path),
        "models_dir": str(models_path),
        "port": port,
        "service_status": service_status,
        "requires_restart": "If the service was already running, it needs to be restarted."
    }

async def _setup_macos_service(install_path: Path, launcher_path: Path, port: Union[int, str]) -> str:
    """Create launchd plist for macOS."""
    label = "com.voicemode.kokoro"
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{launcher_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{BASE_DIR}/logs/kokoro.out.log</string>
    <key>StandardErrorPath</key>
    <string>{BASE_DIR}/logs/kokoro.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
"""
    
    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_dir.mkdir(parents=True, exist_ok=True)
    plist_file = plist_dir / f"{label}.plist"
    
    with open(plist_file, "w") as f:
        f.write(plist_content)
        
    try:
        subprocess.run(["launchctl", "unload", str(plist_file)], capture_output=True)
        subprocess.run(["launchctl", "load", str(plist_file)], check=True)
        return "Service created and loaded via launchd"
    except Exception as e:
        return f"Service file created but failed to load: {e}"

async def _setup_linux_service(install_path: Path, launcher_path: Path, port: Union[int, str]) -> str:
    """Create systemd service for Linux."""
    service_content = f"""[Unit]
Description=VoiceMode Kokoro TTS Service
After=network.target

[Service]
Type=simple
ExecStart={launcher_path}
Restart=always
RestartSec=5
StandardOutput=file:{BASE_DIR}/logs/kokoro.out.log
StandardError=file:{BASE_DIR}/logs/kokoro.err.log

[Install]
WantedBy=default.target
"""
    
    service_dir = Path.home() / ".config" / "systemd" / "user"
    service_dir.mkdir(parents=True, exist_ok=True)
    service_file = service_dir / "voicemode-kokoro.service"
    
    with open(service_file, "w") as f:
        f.write(service_content)
        
    try:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "enable", "voicemode-kokoro.service"], check=True)
        subprocess.run(["systemctl", "--user", "restart", "voicemode-kokoro.service"], check=True)
        return "Service created and enabled via systemd"
    except Exception as e:
        return f"Service file created but failed to start: {e}"
