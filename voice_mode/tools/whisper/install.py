"""MCP tool for installing whisper.cpp service."""
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
    get_cpu_cores,
    find_process_by_port
)
from voice_mode.tools.whisper.model_install import whisper_model_install

logger = logging.getLogger("voicemode")

WHISPER_REPO = "https://github.com/ggerganov/whisper.cpp"
WHISPER_VERSION = "v1.7.1" # Stable version

@mcp.tool()
async def whisper_install(
    install_dir: Optional[str] = None,
    model: str = "base",
    port: Union[int, str] = 2022,
    force_rebuild: Union[bool, str] = False,
    use_gpu: Union[bool, str] = True
) -> Dict[str, Any]:
    """Install whisper.cpp as a background speech-to-text service.
    
    Args:
        install_dir: Directory to install into (defaults to ~/.voicemode/services/whisper)
        model: Initial model to download (default: base)
        port: Port to run the server on (default: 2022)
        force_rebuild: Re-clone and rebuild even if already installed
        use_gpu: Enable GPU acceleration (Metal on Mac, CUDA on Linux if available)
        
    Returns:
        Dict with installation status and details
    """
    system = platform.system()
    machine = platform.machine()
    
    # Use standard directory if not specified
    if install_dir is None:
        install_dir = str(BASE_DIR / "services" / "whisper")
        
    install_path = Path(install_dir)
    os.makedirs(install_path.parent, exist_ok=True)
    
    # Normalize bools from potential string inputs (FastMCP sometimes sends strings)
    if isinstance(force_rebuild, str):
        force_rebuild = force_rebuild.lower() == "true"
    if isinstance(use_gpu, str):
        use_gpu = use_gpu.lower() == "true"
        
    logger.info(f"Starting Whisper installation on {system} ({machine})...")
    
    # 1. Dependency Checks
    deps = ["git", "cmake", "make"]
    if system == "Linux":
        deps.append("build-essential")
    elif system == "Darwin":
        # Check for command line tools
        if subprocess.run(["xcode-select", "-p"], capture_output=True).returncode != 0:
            return {
                "success": False,
                "error": "Xcode Command Line Tools not found. Run: xcode-select --install"
            }
            
    for dep in deps:
        if not check_dependency(dep):
            return {
                "success": False,
                "error": f"Missing required dependency: {dep}. Please install it and try again."
            }
            
    # 2. Clone Repository
    try:
        if not clone_or_update_repo(WHISPER_REPO, str(install_path), WHISPER_VERSION, force=force_rebuild):
             return {"success": False, "error": "Failed to clone or update whisper.cpp repository"}
    except Exception as e:
        return {"success": False, "error": f"Repository error: {str(e)}"}
        
    # 3. Build whisper.cpp
    build_dir = install_path / "build"
    if force_rebuild and build_dir.exists():
        shutil.rmtree(build_dir)
        
    build_dir.mkdir(exist_ok=True)
    
    cmake_flags = ["-DWHISPER_BUILD_SERVER=ON", "-DWHISPER_BUILD_EXAMPLES=OFF"]
    
    # Architecture specific flags
    if system == "Darwin":
        if use_gpu:
            cmake_flags.append("-DWHISPER_METAL=ON")
            if machine == "arm64":
                cmake_flags.append("-DWHISPER_COREML=ON")
        else:
            cmake_flags.append("-DWHISPER_METAL=OFF")
    elif system == "Linux":
        # Check for CUDA
        cuda_path = shutil.which("nvcc")
        if cuda_path and use_gpu:
            logger.info("CUDA detected, enabling GPU acceleration...")
            cmake_flags.append("-DWHISPER_CUDA=ON")
        else:
            logger.info("CUDA not detected or GPU disabled, using CPU only.")
            
    try:
        logger.info(f"Configuring build with flags: {' '.join(cmake_flags)}")
        subprocess.run(["cmake", ".."] + cmake_flags, cwd=build_dir, check=True, capture_output=True)
        
        cores = get_cpu_cores()
        logger.info(f"Building with {cores} cores...")
        subprocess.run(["make", "-j", str(cores)], cwd=build_dir, check=True, capture_output=True)
        
        # Binary name changed to 'whisper-server' in recent versions
        server_bin = build_dir / "bin" / "whisper-server"
        if not server_bin.exists():
            # Old name fallback
            server_bin = build_dir / "bin" / "server"
            
        if not server_bin.exists():
             return {"success": False, "error": "Build completed but whisper-server binary not found"}
            
        # Create a symlink in the root install dir for easier access
        target_bin = install_path / "whisper-server"
        if target_bin.exists():
            target_bin.unlink()
        os.symlink(os.path.relpath(server_bin, install_path), target_bin)
        
    except subprocess.CalledProcessError as e:
        return {
            "success": False, 
            "error": "Build failed", 
            "details": e.stderr.decode() if e.stderr else str(e)
        }
        
    # 4. Install Initial Model
    logger.info(f"Installing initial model: {model}...")
    await whisper_model_install(model=model)
    
    # 5. Set up System Service
    service_status = "Skipped"
    if system == "Darwin":
        service_status = await _setup_macos_service(install_path, model, port)
    elif system == "Linux":
        service_status = await _setup_linux_service(install_path, model, port)
        
    # Update global config
    update_env_file("VOICEMODE_WHISPER_PORT", port)
    update_env_file("VOICEMODE_WHISPER_MODEL", model)
    update_env_file("VOICEMODE_WHISPER_DIR", str(install_path))
    
    return {
        "success": True,
        "message": "whisper.cpp installed successfully",
        "install_dir": str(install_path),
        "active_model": model,
        "port": port,
        "service_status": service_status,
        "requires_restart": "If the service was already running, it needs to be restarted."
    }

async def _setup_macos_service(install_path: Path, model: str, port: Union[int, str]) -> str:
    """Create launchd plist for macOS."""
    models_dir = BASE_DIR / "models" / "whisper"
    model_info = WHISPER_MODEL_REGISTRY[model]
    model_path = models_dir / model_info["filename"]
    
    label = "com.voicemode.whisper"
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{install_path}/whisper-server</string>
        <string>-m</string>
        <string>{model_path}</string>
        <string>--port</string>
        <string>{port}</string>
        <string>--host</string>
        <string>127.0.0.1</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{BASE_DIR}/logs/whisper.out.log</string>
    <key>StandardErrorPath</key>
    <string>{BASE_DIR}/logs/whisper.err.log</string>
</dict>
</plist>
"""
    
    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_dir.mkdir(parents=True, exist_ok=True)
    plist_file = plist_dir / f"{label}.plist"
    
    with open(plist_file, "w") as f:
        f.write(plist_content)
        
    # Load the service
    try:
        subprocess.run(["launchctl", "unload", str(plist_file)], capture_output=True)
        subprocess.run(["launchctl", "load", str(plist_file)], check=True)
        return "Service created and loaded via launchd"
    except Exception as e:
        return f"Service file created but failed to load: {e}"

async def _setup_linux_service(install_path: Path, model: str, port: Union[int, str]) -> str:
    """Create systemd service for Linux."""
    models_dir = BASE_DIR / "models" / "whisper"
    model_info = WHISPER_MODEL_REGISTRY[model]
    model_path = models_dir / model_info["filename"]
    
    service_content = f"""[Unit]
Description=VoiceMode Whisper STT Service
After=network.target

[Service]
Type=simple
ExecStart={install_path}/whisper-server -m {model_path} --port {port} --host 127.0.0.1
Restart=always
RestartSec=5
StandardOutput=file:{BASE_DIR}/logs/whisper.out.log
StandardError=file:{BASE_DIR}/logs/whisper.err.log

[Install]
WantedBy=default.target
"""
    
    service_dir = Path.home() / ".config" / "systemd" / "user"
    service_dir.mkdir(parents=True, exist_ok=True)
    service_file = service_dir / "voicemode-whisper.service"
    
    with open(service_file, "w") as f:
        f.write(service_content)
        
    try:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "enable", "voicemode-whisper.service"], check=True)
        subprocess.run(["systemctl", "--user", "restart", "voicemode-whisper.service"], check=True)
        return "Service created and enabled via systemd"
    except Exception as e:
        return f"Service file created but failed to start: {e}"
