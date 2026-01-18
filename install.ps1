# Voice-Mode Windows Installation Script
# Automated installer for Windows 11

param(
    [switch]$Force,
    [string]$InstallPath = "C:\Users\$env:USERNAME\voicemode-windows"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Voice-Mode MCP Server Installer" -ForegroundColor Cyan
Write-Host "  Windows 11 Edition" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check for admin rights (needed for Chocolatey)
if (-not (Test-Administrator)) {
    Write-Host "⚠️  This script requires administrator privileges for FFmpeg installation." -ForegroundColor Yellow
    Write-Host "   Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Right-click PowerShell → Run as Administrator" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Running with administrator privileges" -ForegroundColor Green
Write-Host ""

# Step 1: Check/Install Chocolatey
Write-Host "[1/7] Checking Chocolatey..." -ForegroundColor Cyan
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "   Installing Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    # Refresh environment
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
} else {
    Write-Host "   ✓ Chocolatey already installed" -ForegroundColor Green
}
Write-Host ""

# Step 2: Install FFmpeg
Write-Host "[2/7] Installing FFmpeg..." -ForegroundColor Cyan
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    choco install ffmpeg -y
    # Refresh environment
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "   ✓ FFmpeg installed" -ForegroundColor Green
} else {
    Write-Host "   ✓ FFmpeg already installed" -ForegroundColor Green
}
Write-Host ""

# Step 3: Check/Install uv
Write-Host "[3/7] Checking uv (Python package manager)..." -ForegroundColor Cyan
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "   Installing uv..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri https://astral.sh/uv/install.ps1 -UseBasicParsing | Invoke-Expression
    
    # Refresh environment
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
} else {
    Write-Host "   ✓ uv already installed" -ForegroundColor Green
}
Write-Host ""

# Step 4: Install Python 3.12
Write-Host "[4/7] Installing Python 3.12..." -ForegroundColor Cyan
try {
    uv python install 3.12
    Write-Host "   ✓ Python 3.12 installed" -ForegroundColor Green
} catch {
    Write-Host "   ✓ Python 3.12 already available" -ForegroundColor Green
}
Write-Host ""

# Step 5: Create virtual environment and install dependencies
Write-Host "[5/7] Setting up virtual environment..." -ForegroundColor Cyan
Push-Location $InstallPath

if (Test-Path ".venv" -and -not $Force) {
    Write-Host "   ✓ Virtual environment already exists" -ForegroundColor Green
} else {
    if (Test-Path ".venv") {
        Remove-Item -Recurse -Force ".venv"
    }
    
    Write-Host "   Creating virtual environment with Python 3.12..." -ForegroundColor Yellow
    uv venv --python 3.12
    
    Write-Host "   Installing dependencies..." -ForegroundColor Yellow
    uv pip install -e .
    
    Write-Host "   ✓ Dependencies installed" -ForegroundColor Green
}
Write-Host ""

# Step 6: Configure Antigravity
Write-Host "[6/7] Configuring Antigravity..." -ForegroundColor Cyan

# Check if config.env exists
if (-not (Test-Path "config.env")) {
    Write-Host "   ⚠️  config.env not found!" -ForegroundColor Red
    Write-Host "   Please create config.env with your OpenAI API key:" -ForegroundColor Yellow
    Write-Host "   OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXX" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Copy config.env.example to config.env and edit it." -ForegroundColor Yellow
    exit 1
}

# Load API key from config.env
$apiKey = Get-Content "config.env" | Where-Object { $_ -match "^OPENAI_API_KEY=" } | ForEach-Object { $_.Split("=")[1] }

if (-not $apiKey -or $apiKey -eq "YOUR_API_KEY_HERE") {
    Write-Host "   ⚠️  OpenAI API key not configured!" -ForegroundColor Red
    Write-Host "   Please edit config.env and add your API key." -ForegroundColor Yellow
    exit 1
}

# Create Antigravity config directory
$antigravityConfigDir = "$env:USERPROFILE\.gemini\antigravity"
if (-not (Test-Path $antigravityConfigDir)) {
    New-Item -ItemType Directory -Path $antigravityConfigDir -Force | Out-Null
}

# Generate mcp_config.json
$mcpConfig = @{
    mcpServers = @{
        voicemode = @{
            command = "$InstallPath\.venv\Scripts\python.exe"
            args = @("-m", "voice_mode.server")
            env = @{
                PYTHONPATH = $InstallPath
                VOICEMODE_TOOLS_ENABLED = "converse,service"
                OPENAI_API_KEY = $apiKey
                VOICEMODE_DEBUG = "true"
                VOICEMODE_DISABLE_SILENCE_DETECTION = "true"
                VOICEMODE_DEFAULT_LISTEN_DURATION = "5.0"
                VOICEMODE_AUDIO_FEEDBACK = "true"
            }
            disabled = $false
        }
    }
}

$configPath = "$antigravityConfigDir\mcp_config.json"
$mcpConfig | ConvertTo-Json -Depth 10 | Set-Content $configPath

Write-Host "   ✓ Antigravity configured at: $configPath" -ForegroundColor Green
Write-Host ""

# Step 7: Verify installation
Write-Host "[7/7] Verifying installation..." -ForegroundColor Cyan

# Test Python import
Write-Host "   Testing Python imports..." -ForegroundColor Yellow
$testScript = @"
import sys
sys.path.insert(0, r'$InstallPath')
from voice_mode.mcp_instance import mcp
import voice_mode.tools.converse
import voice_mode.tools.service
print('✓ All imports successful')
"@

$testScript | & "$InstallPath\.venv\Scripts\python.exe" -

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Python environment verified" -ForegroundColor Green
} else {
    Write-Host "   ✗ Python environment verification failed" -ForegroundColor Red
    exit 1
}

Pop-Location

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Restart Antigravity" -ForegroundColor White
Write-Host "2. Verify that 'voicemode' server appears in green" -ForegroundColor White
Write-Host "3. Check for tools: converse, service, internal_list_tools" -ForegroundColor White
Write-Host ""
Write-Host "To test voice mode, say: 'Activa el mode de veu'" -ForegroundColor Cyan
Write-Host ""
Write-Host "For troubleshooting, run: .\verify.ps1" -ForegroundColor Yellow
Write-Host ""
