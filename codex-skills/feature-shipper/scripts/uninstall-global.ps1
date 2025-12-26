param(
  [string]$CodeXHome = $env:CODEX_HOME,
  [switch]$Force,
  [switch]$DryRun,
  [switch]$NoProfile
)

$ErrorActionPreference = "Stop"

if (-not $CodeXHome -or $CodeXHome.Trim().Length -eq 0) {
  $CodeXHome = Join-Path $env:USERPROFILE ".codex"
}
$skillsDir = Join-Path $CodeXHome "skills"
$targets = @("feature-shipper", "feedback-logger")
$profilePath = $PROFILE
$marker = "# codex autoworkflow aliases"

function Write-Step([string]$Msg) { Write-Host "[uninstall-global] $Msg" }

Write-Step "Target skills dir: $skillsDir"
if ($DryRun) { Write-Step "Dry-run mode (no files will be removed)" }

foreach ($name in $targets) {
  $path = Join-Path $skillsDir $name
  if (Test-Path -LiteralPath $path) {
    if ($DryRun) {
      Write-Step "Would remove $path"
    } else {
      if ($Force) { Remove-Item -LiteralPath $path -Recurse -Force }
      else { Remove-Item -LiteralPath $path -Recurse -Confirm }
      Write-Step "Removed $path"
    }
  } else {
    Write-Step "Skip missing $path"
  }
}

if (-not $NoProfile -and (Test-Path -LiteralPath $profilePath)) {
  $lines = Get-Content -LiteralPath $profilePath -Raw
  if ($lines -like "*$marker*") {
    $pattern = "(?ms)$([regex]::Escape($marker)).*?(?=^#|\\z)"
    $new = [regex]::Replace($lines, $pattern, "", 1)
    if ($DryRun) {
      Write-Step "Would remove alias block from $profilePath"
    } else {
      Set-Content -LiteralPath $profilePath -Value $new -Encoding UTF8
      Write-Step "Removed alias block from $profilePath (restart shell to生效)"
    }
  } else {
    Write-Step "No alias marker in $profilePath"
  }
} elseif (-not $NoProfile) {
  Write-Step "Profile not found: $profilePath (skip)"
}

Write-Step "Done."
