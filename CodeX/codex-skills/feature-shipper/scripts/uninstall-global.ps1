param(
  [string]$CodeXHome = $env:CODEX_HOME,
  [string]$ClaudeHome = $env:CLAUDE_HOME,
  [switch]$Force,
  [switch]$DryRun,
  [switch]$NoProfile,
  [switch]$NoClaude,
  [switch]$Purge
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$codexScript = Join-Path $scriptDir "uninstall-codex-global.ps1"
$claudeScript = Join-Path $scriptDir "uninstall-claude-global.ps1"

& $codexScript -CodeXHome $CodeXHome -Force:$Force -DryRun:$DryRun -NoProfile:$NoProfile -Purge:$Purge
if (-not $NoClaude) {
  & $claudeScript -ClaudeHome $ClaudeHome -Force:$Force -DryRun:$DryRun -Purge:$Purge
}

Write-Host "[uninstall-global] Done."
