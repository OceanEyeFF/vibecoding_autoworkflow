param(
  [ValidateSet("global", "local")]
  [string]$Mode = "global",

  [ValidateSet("both", "codex", "claude")]
  [string]$Target = "both",

  [string]$CodeXHome = $env:CODEX_HOME,
  [string]$ClaudeHome = $env:CLAUDE_HOME,

  [switch]$Force,
  [switch]$DryRun,
  [switch]$NoProfile
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Msg) { Write-Host "[install] $Msg" }

$root = [IO.Path]::GetFullPath($PSScriptRoot)

$codexInstall = Join-Path $root "CodeX\\codex-skills\\feature-shipper\\scripts\\install-codex-global.ps1"
$claudeInstall = Join-Path $root "CodeX\\codex-skills\\feature-shipper\\scripts\\install-claude-global.ps1"
$aw = Join-Path $root "CodeX\\codex-skills\\feature-shipper\\scripts\\autoworkflow.py"

if ($Mode -eq "global") {
  if ($Target -eq "both" -or $Target -eq "codex") {
    & $codexInstall -CodeXHome $CodeXHome -Force:$Force -DryRun:$DryRun -NoProfile:$NoProfile
  }
  if ($Target -eq "both" -or $Target -eq "claude") {
    & $claudeInstall -ClaudeHome $ClaudeHome -Force:$Force -DryRun:$DryRun
  }
  exit 0
}

# local mode
if (($CodeXHome -and $CodeXHome.Trim().Length -gt 0) -or ($ClaudeHome -and $ClaudeHome.Trim().Length -gt 0) -or $NoProfile.IsPresent) {
  Write-Step "Note: -CodeXHome/-ClaudeHome/-NoProfile are ignored in -Mode local."
}

if ($Target -eq "both" -or $Target -eq "codex") {
  $cmd = @("python", "`"$aw`"", "--root", "`"$root`"", "init")
  if ($Force.IsPresent) { $cmd += "--force" }
  $cmdLine = $cmd -join " "
  if ($DryRun.IsPresent) { Write-Step "Would run: $cmdLine" } else { & powershell -NoProfile -ExecutionPolicy Bypass -Command $cmdLine }
}

if ($Target -eq "both" -or $Target -eq "claude") {
  $localClaudeHome = Join-Path $root ".claude"
  & $claudeInstall -ClaudeHome $localClaudeHome -Force:$Force -DryRun:$DryRun
}

