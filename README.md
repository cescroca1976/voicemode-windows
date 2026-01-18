# Voice-Mode MCP Server - Windows 11 Edition

🎤 **Voice Mode MCP Server for Antigravity with full Windows 11 support**

This is a modified fork of [mbailey/voicemode](https://github.com/mbailey/voicemode) with specific fixes for Windows 11.

## ✨ Features

- ✅ **Windows 11 Compatible** - All dependencies work without compilation issues
- ✅ **Automatic Installation** - PowerShell script that configures everything
- ✅ **Python 3.12** - Stable version with full support
- ✅ **Integrated FFmpeg** - Automatic installation via Chocolatey
- ✅ **Singleton Pattern** - Avoids double-import issues
- ✅ **Antigravity Integration** - Automatic configuration

## 🚀 Quick Installation

### Prerequisites

- Windows 11
- [Chocolatey](https://chocolatey.org/install) (for FFmpeg)
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- OpenAI API Key

### Step 1: Clone the Repository

```powershell
cd C:\Users\$env:USERNAME
git clone https://github.com/cescroca1976/voicemode-windows.git
cd voicemode-windows
```

### Step 2: Configure API Key

Edit the `config.env` file and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXX
```

### Step 3: Run the Installer

```powershell
.\install.ps1
```

This script will:
1. ✅ Install Python 3.12
2. ✅ Install FFmpeg
3. ✅ Create a virtual environment
4. ✅ Install dependencies
5. ✅ Configure Antigravity
6. ✅ Verify the installation

### Step 4: Restart Antigravity

Close and reopen Antigravity. The `voicemode` server should appear in **green** with the following tools:
- `converse` - Voice conversation
- `service` - Service management
- `internal_list_tools` - Tool list

## 🎯 Usage

### Activate Voice Mode

In Antigravity, simply say:
```
Activate voice mode
```

Or use the `converse` tool directly:
```
Use the converse tool to listen to me
```

### Advanced Configuration

Edit `C:\Users\%USERNAME%\.gemini\antigravity\mcp_config.json` to customize:

```json
{
  "mcpServers": {
    "voicemode": {
      "env": {
        "VOICEMODE_DEBUG": "true",
        "VOICEMODE_DISABLE_SILENCE_DETECTION": "true",
        "VOICEMODE_DEFAULT_LISTEN_DURATION": "10.0",
        "VOICEMODE_AUDIO_FEEDBACK": "true"
      }
    }
  }
}
```

## 🔧 Modifications from Original

### Updated Dependencies
- `simpleaudio` → `simpleaudio-patched` (Windows wheels)
- `webrtcvad` → `webrtcvad-wheels` (Windows wheels)

### Modified Code
- **Singleton MCP** (`mcp_instance.py`) - Avoids double-importing
- **Windows Compatibility** - `fcntl` and `resource` made optional
- **Updated Imports** - All modules use the singleton instance

### New Files
- `install.ps1` - Automatic installation script
- `verify.ps1` - Verification script
- `config.env` - Configuration template
- `mcp_config.template.json` - Antigravity template

## 📚 Documentation

- [Full Installation Guide](docs/INSTALLATION.md)
- [Configuration](docs/CONFIGURATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Architecture](docs/ARCHITECTURE.md)

## 🐛 Common Issues

### Server shows as red
```powershell
# Verify installation
.\verify.ps1

# Reinstall
.\install.ps1 -Force
```

### I can't hear the chime
Check that `VOICEMODE_AUDIO_FEEDBACK` is set to `true` in the configuration.

### Error "No module named..."
```powershell
# Reinstall dependencies
cd voicemode-windows
.\.venv\Scripts\python.exe -m pip install -e .
```

## 🤝 Contributions

This is a fork with Windows-specific modifications. To contribute:

1. Fork this repository
2. Create a branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -am 'Add improvement'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Open a Pull Request

## 📝 License

Same as the original: [Original project license](https://github.com/mbailey/voicemode)

## 🙏 Acknowledgements

- [mbailey/voicemode](https://github.com/mbailey/voicemode) - Original project
- Antigravity community
- All contributors

## 📞 Support

If you have issues:
1. Review the [documentation](docs/)
2. Check [common issues](#-common-issues)
3. Open an [issue](https://github.com/cescroca1976/voicemode-windows/issues)

---

**Made with ❤️ for the Antigravity community**
