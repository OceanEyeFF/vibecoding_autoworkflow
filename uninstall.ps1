param(
  [ValidateSet("global", "local")]
  [string]$Mode = "global",

  [ValidateSet("both", "codex", "claude")]
  [string]$Target = "both",

  [string]$CodeXHome = $env:CODEX_HOME,
  [string]$ClaudeHome = $env:CLAUDE_HOME,

  [switch]$Force,
  [switch]$DryRun,
  [switch]$NoProfile,
  [switch]$Purge,

  [switch]$Yes,
  [switch]$RemoveExclude
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Msg) { Write-Host "[uninstall] $Msg" }

$root = [IO.Path]::GetFullPath($PSScriptRoot)

$codexUninstall = Join-Path $root "CodeX\\codex-skills\\feature-shipper\\scripts\\uninstall-codex-global.ps1"
$claudeUninstall = Join-Path $root "CodeX\\codex-skills\\feature-shipper\\scripts\\uninstall-claude-global.ps1"
$aw = Join-Path $root "CodeX\\codex-skills\\feature-shipper\\scripts\\autoworkflow.py"

if ($Force.IsPresent) { $Yes = $true }

if ($Mode -eq "global") {
  if ($Target -eq "both" -or $Target -eq "codex") {
    & $codexUninstall -CodeXHome $CodeXHome -Force:$Force -DryRun:$DryRun -NoProfile:$NoProfile -Purge:$Purge
  }
  if ($Target -eq "both" -or $Target -eq "claude") {
    & $claudeUninstall -ClaudeHome $ClaudeHome -Force:$Force -DryRun:$DryRun -Purge:$Purge
  }
  exit 0
}

# local mode
if (($CodeXHome -and $CodeXHome.Trim().Length -gt 0) -or ($ClaudeHome -and $ClaudeHome.Trim().Length -gt 0) -or $NoProfile.IsPresent -or $Purge.IsPresent) {
  Write-Step "Note: -CodeXHome/-ClaudeHome/-NoProfile/-Purge are ignored in -Mode local."
}

if ($Target -eq "both" -or $Target -eq "codex") {
  $cmd = @("python", "`"$aw`"", "--root", "`"$root`"", "uninstall")
  if ($Yes) { $cmd += "--yes" }
  if ($RemoveExclude.IsPresent) { $cmd += "--remove-exclude" }
  $cmdLine = $cmd -join " "
  if ($DryRun.IsPresent) { Write-Step "Would run: $cmdLine" } else { & powershell -NoProfile -ExecutionPolicy Bypass -Command $cmdLine }
}

if ($Target -eq "both" -or $Target -eq "claude") {
  $localClaudeHome = Join-Path $root ".claude"
  & $claudeUninstall -ClaudeHome $localClaudeHome -Force:$Force -DryRun:$DryRun -Purge
}

