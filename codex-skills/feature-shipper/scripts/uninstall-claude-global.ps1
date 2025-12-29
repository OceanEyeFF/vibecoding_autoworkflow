param(
  [string]$ClaudeHome = $env:CLAUDE_HOME,
  [switch]$Force,
  [switch]$DryRun,
  [switch]$Purge
)

$ErrorActionPreference = "Stop"

if (-not $ClaudeHome -or $ClaudeHome.Trim().Length -eq 0) {
  $ClaudeHome = Join-Path $env:USERPROFILE ".claude"
}
$ClaudeHome = [IO.Path]::GetFullPath($ClaudeHome)

$manifest = Join-Path $ClaudeHome ".autoworkflow-claude-installed.txt"
$manifestLegacy = Join-Path $ClaudeHome ".autoworkflow-installed.txt"

function Write-Step([string]$Msg) { Write-Host "[uninstall-claude-global] $Msg" }

Write-Step "Target claude: $ClaudeHome"
Write-Step "Claude manifest: $manifest"
Write-Step "Claude legacy manifest: $manifestLegacy"
if ($DryRun) { Write-Step "Dry-run mode (no files will be removed)" }

$manifests = @()
if (Test-Path -LiteralPath $manifest) { $manifests += $manifest }
if (Test-Path -LiteralPath $manifestLegacy) { $manifests += $manifestLegacy }

function Remove-File([string]$Path) {
  if ($DryRun) {
    Write-Step "Would remove $Path"
    return
  }
  try {
    Remove-Item -LiteralPath $Path -Force -ErrorAction Stop
  } catch {
    if ($Force) { return }
    throw
  }
}

if ($manifests.Count -gt 0) {
  Write-Step "Using manifest(s): $($manifests -join ', ')"
  $paths = @()
  foreach ($mf in $manifests) {
    $paths += Get-Content -LiteralPath $mf -ErrorAction SilentlyContinue
  }
  $paths = $paths | Where-Object { $_ } | Sort-Object -Unique
  foreach ($p in $paths) {
    $full = [IO.Path]::GetFullPath($p)
    if (-not $full.StartsWith($ClaudeHome)) {
      Write-Step "Skip unexpected path (outside CLAUDE_HOME): $p"
      continue
    }
    Remove-File -Path $full
  }
  if ($DryRun) {
    foreach ($mf in $manifests) { Write-Step "Would remove $mf" }
  } else {
    foreach ($mf in $manifests) { Remove-Item -LiteralPath $mf -Force -ErrorAction SilentlyContinue }
    foreach ($dir in @((Join-Path $ClaudeHome "agents"), (Join-Path $ClaudeHome "skills"), (Join-Path $ClaudeHome "commands"))) {
      if (Test-Path -LiteralPath $dir) {
        Get-ChildItem -LiteralPath $dir -Recurse -Directory -Force |
          Sort-Object FullName -Descending |
          Where-Object { (Get-ChildItem -LiteralPath $_.FullName -Force).Count -eq 0 } |
          Remove-Item -Force -ErrorAction SilentlyContinue
      }
    }
    Write-Step "Removed Claude assets listed in manifest"
  }
} else {
  Write-Step "Claude manifest not found (skip)."
}

if ($Purge -and -not $DryRun) {
  foreach ($dir in @((Join-Path $ClaudeHome "agents"), (Join-Path $ClaudeHome "skills"), (Join-Path $ClaudeHome "commands"))) {
    if (Test-Path -LiteralPath $dir) {
      Get-ChildItem -LiteralPath $dir -Recurse -Directory -Force |
        Sort-Object FullName -Descending |
        Where-Object { (Get-ChildItem -LiteralPath $_.FullName -Force).Count -eq 0 } |
        Remove-Item -Force -ErrorAction SilentlyContinue
      Remove-Item -LiteralPath $dir -Force -ErrorAction SilentlyContinue
    }
  }
  Remove-Item -LiteralPath $ClaudeHome -Force -ErrorAction SilentlyContinue
}

Write-Step "Done."

