#!/bin/bash

echo "=== Installing Audio Dependencies ==="
echo

# Install system audio packages
echo "1. Installing system audio packages..."
sudo apt update
sudo apt install -y libasound2-plugins pulseaudio pulseaudio-utils libportaudio2 portaudio19-dev python3-pip

# Create virtual environment and install Python packages
echo "2. Creating virtual environment and installing Python audio libraries..."
cd /home/bron/claude/voicemode
uv venv
source .venv/bin/activate
uv pip install sounddevice numpy scipy

# Try to start PulseAudio
echo "3. Starting PulseAudio..."
pulseaudio --start 2>/dev/null || echo "   PulseAudio already running or using WSLg"

# Test installation
echo "4. Testing audio libraries..."
python3 -c "
try:
    import sounddevice
    import numpy
    import scipy
    print('✅ Audio libraries installed successfully')
    print('Available audio devices:')
    print(sounddevice.query_devices())
except ImportError as e:
    print(f'❌ Audio library missing: {e}')
except Exception as e:
    print(f'⚠️  Audio libraries installed but device access failed: {e}')
"

echo
echo "=== Installation Complete ==="
echo "The voice-mode MCP server may need to be restarted to pick up the new dependencies."