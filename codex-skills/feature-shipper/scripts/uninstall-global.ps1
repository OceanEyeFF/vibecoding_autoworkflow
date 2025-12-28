param(
  [string]$CodeXHome = $env:CODEX_HOME,
  [string]$ClaudeHome = $env:CLAUDE_HOME,
  [switch]$Force,
  [switch]$DryRun,
  [switch]$NoProfile,
  [switch]$NoClaude
)

$ErrorActionPreference = "Stop"

if (-not $CodeXHome -or $CodeXHome.Trim().Length -eq 0) {
  $CodeXHome = Join-Path $env:USERPROFILE ".codex"
}
$CodeXHome = [IO.Path]::GetFullPath($CodeXHome)

if (-not $ClaudeHome -or $ClaudeHome.Trim().Length -eq 0) {
  $ClaudeHome = Join-Path $env:USERPROFILE ".claude"
}
$ClaudeHome = [IO.Path]::GetFullPath($ClaudeHome)
$skillsDir = Join-Path $CodeXHome "skills"
$targets = @("feature-shipper", "feedback-logger")
$profilePath = $PROFILE
$markerBegin = "# codex autoworkflow aliases (begin)"
$markerEnd = "# codex autoworkflow aliases (end)"
$legacyMarker = "# codex autoworkflow aliases"

function Write-Step([string]$Msg) { Write-Host "[uninstall-global] $Msg" }

Write-Step "Target skills dir: $skillsDir"
if ($DryRun) { Write-Step "Dry-run mode (no files will be removed)" }

foreach ($name in $targets) {
  $path = Join-Path $skillsDir $name
  if (Test-Path -LiteralPath $path) {
    if ($DryRun) {
      Write-Step "Would remove $path"
      Get-ChildItem -LiteralPath $path -Recurse -Force | ForEach-Object {
        Write-Step "Would remove $($_.FullName)"
      }
    } else {
      if ($Force) { Remove-Item -LiteralPath $path -Recurse -Force }
      else { Remove-Item -LiteralPath $path -Recurse -Confirm }
      Write-Step "Removed $path"
    }
  } else {
    Write-Step "Skip missing $path"
  }
}

if (-not $NoClaude) {
  $manifest = Join-Path $ClaudeHome ".autoworkflow-installed.txt"
  if (Test-Path -LiteralPath $manifest) {
    Write-Step "Claude manifest: $manifest"
    $paths = Get-Content -LiteralPath $manifest -ErrorAction SilentlyContinue
    foreach ($p in $paths) {
      if (-not $p) { continue }
      $full = [IO.Path]::GetFullPath($p)
      if (-not $full.StartsWith($ClaudeHome)) {
        Write-Step "Skip unexpected path (outside CLAUDE_HOME): $p"
        continue
      }
      if ($DryRun) { Write-Step "Would remove $full" }
      else { Remove-Item -LiteralPath $full -Force -ErrorAction SilentlyContinue }
    }
    if ($DryRun) {
      Write-Step "Would remove $manifest"
    } else {
      Remove-Item -LiteralPath $manifest -Force -ErrorAction SilentlyContinue
      foreach ($dir in @((Join-Path $ClaudeHome "agents"), (Join-Path $ClaudeHome "skills"), (Join-Path $ClaudeHome "commands"))) {
        if (Test-Path -LiteralPath $dir) {
          # delete empty dirs bottom-up
          Get-ChildItem -LiteralPath $dir -Recurse -Directory -Force |
            Sort-Object FullName -Descending |
            Where-Object { (Get-ChildItem -LiteralPath $_.FullName -Force).Count -eq 0 } |
            Remove-Item -Force -ErrorAction SilentlyContinue
        }
      }
      Write-Step "Removed Claude assets listed in manifest"
    }
  } else {
    Write-Step "Claude manifest not found (skip): $manifest"
  }
}

if (-not $NoProfile -and (Test-Path -LiteralPath $profilePath)) {
  $lines = Get-Content -LiteralPath $profilePath -Raw
  if ($lines -like "*$markerBegin*") {
    $pattern = "(?ms)^$([regex]::Escape($markerBegin)).*?^$([regex]::Escape($markerEnd))\s*\r?\n?"
    $new = [regex]::Replace($lines, $pattern, "", 1)
    if ($DryRun) {
      Write-Step "Would remove alias block from $profilePath"
    } else {
      Set-Content -LiteralPath $profilePath -Value $new -Encoding UTF8
      Write-Step "Removed alias block from $profilePath (restart shell to生效)"
    }
  } elseif ($lines -like "*$legacyMarker*") {
    $pattern = "(?ms)^$([regex]::Escape($legacyMarker)).*\z"
    $new = [regex]::Replace($lines, $pattern, "", 1)
    if ($DryRun) {
      Write-Step "Would remove legacy alias block from $profilePath"
    } else {
      Set-Content -LiteralPath $profilePath -Value $new -Encoding UTF8
      Write-Step "Removed legacy alias block from $profilePath (restart shell to生效)"
    }
  } else {
    Write-Step "No alias marker in $profilePath"
  }
} elseif (-not $NoProfile) {
  Write-Step "Profile not found: $profilePath (skip)"
}

Write-Step "Done."
