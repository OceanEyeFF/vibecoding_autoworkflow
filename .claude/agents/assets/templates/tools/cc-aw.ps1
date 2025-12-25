# Claude Code Autoworkflow Wrapper (Windows PowerShell)
# Usage: powershell -ExecutionPolicy Bypass -File cc-aw.ps1 <command> [args]

$ErrorActionPreference = "Stop"

$toolDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $toolDir "claude_autoworkflow.py"

# Check script exists
if (-not (Test-Path $script)) {
    Write-Error "Error: Script not found at $script"
    exit 1
}

# Detect Python command
$pythonCmd = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} else {
    Write-Error "Error: Python not found. Please ensure Python is installed and in PATH."
    exit 1
}

# Execute script
& $pythonCmd $script @args
exit $LASTEXITCODE
