import click
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, List, Dict

# Import the service tool for restarting
from voice_mode.tools.service import restart_service
# Import model info from whisper tool
# Note: This is an internal import, make sure the tool is available
try:
    from voice_mode.tools.whisper import models
except ImportError:
    models = None

def model_name_completion(ctx, param, incomplete):
    """Provide completion for model names."""
    if not models:
        return []
    available_models = [m["name"] for m in models.AVAILABLE_MODELS]
    return [m for m in available_models if m.startswith(incomplete)]

@click.command("model", help="Manage Whisper models (view, list, switch)")
@click.argument('model_name', required=False, shell_complete=model_name_completion)
@click.option('--all', '-a', is_flag=True, help='List all available models')
@click.option('--no-install', is_flag=True, help="Don't auto-install missing models")
@click.option('--no-activate', is_flag=True, help="Don't auto-activate after installing")
@click.option('--no-restart', is_flag=True, help="Don't auto-restart whisper service after changing model")
def whisper_model_unified(model_name: Optional[str] = None, all: bool = False, no_install: bool = False, no_activate: bool = False, no_restart: bool = False):
    """Main command for gestion of whisper models."""
    if all:
        # Show all models and their status
        click.echo("\nAvailable Whisper Models:")
        click.echo("-" * 50)
        
        current = os.environ.get("VOICEMODE_WHISPER_MODEL", "base")
        
        if models:
            for m in models.AVAILABLE_MODELS:
                name = m["name"]
                status = "Installed" if models.is_model_installed(name) else "Not Installed"
                marker = "*" if name == current else " "
                click.echo(f"{marker} {name:<15} {status:<15} {m['size']}")
        
        click.echo("-" * 50)
        click.echo(f"\n* Current model: {current}")
        return

    if not model_name:
        # Show current model
        current = os.environ.get("VOICEMODE_WHISPER_MODEL", "base")
        click.echo(f"Current Whisper model: {current}")
        return

    # User wants to set/switch model
    # ... logic for switching model ...
    pass
