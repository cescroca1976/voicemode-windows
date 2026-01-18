# Voice-Mode Verification Script
# Checks if the installation is working correctly

param(
    [string]$InstallPath = "C:\Users\$env:USERNAME\voicemode-windows"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Voice-Mode Installation Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Check 1: FFmpeg
Write-Host "[1/6] Checking FFmpeg..." -ForegroundColor Cyan
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    $ffmpegVersion = & ffmpeg -version | Select-Object -First 1
    Write-Host "   ✓ FFmpeg installed: $ffmpegVersion" -ForegroundColor Green
} else {
    Write-Host "   ✗ FFmpeg not found" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# Check 2: Python 3.12
Write-Host "[2/6] Checking Python 3.12..." -ForegroundColor Cyan
if (Test-Path "$InstallPath\.venv\Scripts\python.exe") {
    $pythonVersion = & "$InstallPath\.venv\Scripts\python.exe" --version
    Write-Host "   ✓ Python installed: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "   ✗ Python virtual environment not found" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# Check 3: Dependencies
Write-Host "[3/6] Checking Python dependencies..." -ForegroundColor Cyan
$checkScript = @"
import sys
sys.path.insert(0, r'$InstallPath')
try:
    from voice_mode.mcp_instance import mcp
    import voice_mode.tools.converse
    import voice_mode.tools.service
    print('✓ All dependencies installed')
except Exception as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"@

$result = $checkScript | & "$InstallPath\.venv\Scripts\python.exe" - 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   $result" -ForegroundColor Green
} else {
    Write-Host "   $result" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# Check 4: Tool registration
Write-Host "[4/6] Checking tool registration..." -ForegroundColor Cyan
$toolCheckScript = @"
import sys
import asyncio
sys.path.insert(0, r'$InstallPath')

from voice_mode.mcp_instance import mcp
import voice_mode.tools.converse
import voice_mode.tools.service

async def check():
    tools = await mcp.get_tools()
    names = [t.name if hasattr(t, 'name') else str(t) for t in tools]
    print(f'✓ Registered tools ({len(tools)}): {", ".join(names)}')

asyncio.run(check())
"@

$result = $toolCheckScript | & "$InstallPath\.venv\Scripts\python.exe" - 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   $result" -ForegroundColor Green
} else {
    Write-Host "   ✗ Tool registration check failed" -ForegroundColor Red
    Write-Host "   $result" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# Check 5: Antigravity config
Write-Host "[5/6] Checking Antigravity configuration..." -ForegroundColor Cyan
$configPath = "$env:USERPROFILE\.gemini\antigravity\mcp_config.json"
if (Test-Path $configPath) {
    $config = Get-Content $configPath | ConvertFrom-Json
    if ($config.mcpServers.voicemode) {
        Write-Host "   ✓ Antigravity configured at: $configPath" -ForegroundColor Green
        
        # Check API key
        $apiKey = $config.mcpServers.voicemode.env.OPENAI_API_KEY
        if ($apiKey -and $apiKey -ne "YOUR_API_KEY_HERE") {
            Write-Host "   ✓ OpenAI API key configured" -ForegroundColor Green
        } else {
            Write-Host "   ✗ OpenAI API key not configured" -ForegroundColor Red
            $allGood = $false
        }
    } else {
        Write-Host "   ✗ voicemode server not found in config" -ForegroundColor Red
        $allGood = $false
    }
} else {
    Write-Host "   ✗ Antigravity config not found" -ForegroundColor Red
    $allGood = $false
}
Write-Host ""

# Check 6: Server startup test
Write-Host "[6/6] Testing server startup..." -ForegroundColor Cyan
Write-Host "   Starting server (this may take a few seconds)..." -ForegroundColor Yellow

$serverTest = Start-Process -FilePath "$InstallPath\.venv\Scripts\python.exe" `
    -ArgumentList "-m", "voice_mode.server", "--help" `
    -WorkingDirectory $InstallPath `
    -NoNewWindow `
    -PassThru `
    -RedirectStandardOutput "$env:TEMP\voicemode_test_out.txt" `
    -RedirectStandardError "$env:TEMP\voicemode_test_err.txt"

Start-Sleep -Seconds 3

if (-not $serverTest.HasExited) {
    $serverTest.Kill()
    Write-Host "   ✓ Server starts successfully" -ForegroundColor Green
} else {
    $exitCode = $serverTest.ExitCode
    if ($exitCode -eq 0) {
        Write-Host "   ✓ Server starts successfully" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Server failed to start (exit code: $exitCode)" -ForegroundColor Red
        $stderr = Get-Content "$env:TEMP\voicemode_test_err.txt" -Raw
        if ($stderr) {
            Write-Host "   Error output:" -ForegroundColor Red
            Write-Host $stderr -ForegroundColor Red
        }
        $allGood = $false
    }
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "  ✓ All checks passed!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your installation is ready to use." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Restart Antigravity if it's running" -ForegroundColor White
    Write-Host "2. Verify 'voicemode' server is green" -ForegroundColor White
    Write-Host "3. Try: 'Activa el mode de veu'" -ForegroundColor White
} else {
    Write-Host "  ✗ Some checks failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please review the errors above and:" -ForegroundColor Yellow
    Write-Host "1. Run: .\install.ps1 -Force" -ForegroundColor White
    Write-Host "2. Check the troubleshooting guide" -ForegroundColor White
    Write-Host "3. Open an issue on GitHub if problems persist" -ForegroundColor White
}
Write-Host ""
