param(
  [string]$CodeXHome = $env:CODEX_HOME,
  [switch]$Force,
  [switch]$DryRun,
  [switch]$NoProfile,
  [switch]$Purge
)

$ErrorActionPreference = "Stop"

if (-not $CodeXHome -or $CodeXHome.Trim().Length -eq 0) {
  $CodeXHome = Join-Path $env:USERPROFILE ".codex"
}
$CodeXHome = [IO.Path]::GetFullPath($CodeXHome)

$skillsDir = Join-Path $CodeXHome "skills"
$targets = @("feature-shipper", "feedback-logger")
$manifest = Join-Path $CodeXHome ".autoworkflow-codex-installed.txt"
$profilePath = $PROFILE
$markerBegin = "# codex autoworkflow aliases (begin)"
$markerEnd = "# codex autoworkflow aliases (end)"
$legacyMarker = "# codex autoworkflow aliases"

function Write-Step([string]$Msg) { Write-Host "[uninstall-codex-global] $Msg" }

Write-Step "Target skills dir: $skillsDir"
Write-Step "Codex manifest: $manifest"
if ($DryRun) { Write-Step "Dry-run mode (no files will be removed)" }

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

if (Test-Path -LiteralPath $manifest) {
  Write-Step "Using manifest: $manifest"
  $paths = Get-Content -LiteralPath $manifest -ErrorAction SilentlyContinue
  foreach ($p in $paths) {
    if (-not $p) { continue }
    $full = [IO.Path]::GetFullPath($p)
    if (-not $full.StartsWith($CodeXHome)) {
      Write-Step "Skip unexpected path (outside CODEX_HOME): $p"
      continue
    }
    Remove-File -Path $full
  }
  if ($DryRun) {
    Write-Step "Would remove $manifest"
  } else {
    Remove-Item -LiteralPath $manifest -Force -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $skillsDir) {
      Get-ChildItem -LiteralPath $skillsDir -Recurse -Directory -Force |
        Sort-Object FullName -Descending |
        Where-Object { (Get-ChildItem -LiteralPath $_.FullName -Force).Count -eq 0 } |
        Remove-Item -Force -ErrorAction SilentlyContinue
    }
  }
} else {
  Write-Step "Manifest not found; falling back to directory removal for known skills."
  foreach ($name in $targets) {
    $path = Join-Path $skillsDir $name
    if (Test-Path -LiteralPath $path) {
      if ($DryRun) { Write-Step "Would remove $path" }
      else {
        if ($Force) { Remove-Item -LiteralPath $path -Recurse -Force }
        else { Remove-Item -LiteralPath $path -Recurse -Confirm }
        Write-Step "Removed $path"
      }
    } else {
      Write-Step "Skip missing $path"
    }
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
      Write-Step "Removed alias block from $profilePath (restart shell to load)"
    }
  } elseif ($lines -like "*$legacyMarker*") {
    $pattern = "(?ms)^$([regex]::Escape($legacyMarker)).*\z"
    $new = [regex]::Replace($lines, $pattern, "", 1)
    if ($DryRun) {
      Write-Step "Would remove legacy alias block from $profilePath"
    } else {
      Set-Content -LiteralPath $profilePath -Value $new -Encoding UTF8
      Write-Step "Removed legacy alias block from $profilePath (restart shell to load)"
    }
  } else {
    Write-Step "No alias marker in $profilePath"
  }
} elseif (-not $NoProfile) {
  Write-Step "Profile not found: $profilePath (skip)"
}

if ($Purge) {
  foreach ($name in $targets) {
    $path = Join-Path $skillsDir $name
    if (Test-Path -LiteralPath $path) {
      if ($DryRun) { Write-Step "Would purge $path" }
      else {
        if ($Force) { Remove-Item -LiteralPath $path -Recurse -Force }
        else { Remove-Item -LiteralPath $path -Recurse -Confirm }
        Write-Step "Purged $path"
      }
    }
  }

  if (-not $DryRun) {
    if (Test-Path -LiteralPath $skillsDir) {
      Get-ChildItem -LiteralPath $skillsDir -Recurse -Directory -Force |
        Sort-Object FullName -Descending |
        Where-Object { (Get-ChildItem -LiteralPath $_.FullName -Force).Count -eq 0 } |
        Remove-Item -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path -LiteralPath $CodeXHome) {
      Get-ChildItem -LiteralPath $CodeXHome -Directory -Force |
        Sort-Object FullName -Descending |
        Where-Object { (Get-ChildItem -LiteralPath $_.FullName -Force).Count -eq 0 } |
        Remove-Item -Force -ErrorAction SilentlyContinue
    }
  }
}

Write-Step "Done."

