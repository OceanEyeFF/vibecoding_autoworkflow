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

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$featureShipperDir = Split-Path -Parent $scriptDir
$skillsRoot = Split-Path -Parent $featureShipperDir
$targetSkills = Join-Path $CodeXHome "skills"

function Write-Step([string]$Msg) { Write-Host "[install-global] $Msg" }

Write-Step "Source skills: $skillsRoot"
Write-Step "Target skills: $targetSkills"
if ($DryRun) { Write-Step "Dry-run mode (no changes will be written)" }

function Copy-SkillDir([string]$Name) {
  $src = Join-Path $skillsRoot $Name
  $dst = Join-Path $targetSkills $Name
  if ($DryRun) { Write-Step "Would copy $src -> $dst"; return }
  if ($Force -and (Test-Path -LiteralPath $dst)) {
    Remove-Item -LiteralPath $dst -Recurse -Force
  }
  Copy-Item -LiteralPath $src -Destination $dst -Recurse -Force
  Write-Step "Installed $Name"
}

$skillDirs = Get-ChildItem -LiteralPath $skillsRoot -Directory | Where-Object { $_.Name -notlike ".*" }
if (-not $skillDirs) {
  Write-Step "No skill directories found under $skillsRoot"
  exit 1
}

if (-not $DryRun) {
  New-Item -ItemType Directory -Force -Path $targetSkills | Out-Null
}

foreach ($dir in $skillDirs) {
  Copy-SkillDir $dir.Name
}

if (-not $NoProfile) {
  $profilePath = $PROFILE
  $marker = "# codex autoworkflow aliases"
  $aliases = @"
$marker
function aw-init { param([string]\$root = (Get-Location)) python (Join-Path \$env:CODEX_HOME 'skills/feature-shipper/scripts/autoworkflow.py') --root \$root init }
function aw-auto { param([string]\$root = (Get-Location)) python (Join-Path \$env:CODEX_HOME 'skills/feature-shipper/scripts/autoworkflow.py') --root \$root auto-gate }
function aw-gate { param([string]\$root = (Get-Location)) python (Join-Path \$env:CODEX_HOME 'skills/feature-shipper/scripts/autoworkflow.py') --root \$root gate }
function aw-doctor { param([string]\$root = (Get-Location)) python (Join-Path \$env:CODEX_HOME 'skills/feature-shipper/scripts/autoworkflow.py') --root \$root doctor --write --update-state }
"

  if ($DryRun) {
    Write-Step "Would append aliases to $profilePath"
  } else {
    New-Item -ItemType File -Force -Path $profilePath | Out-Null
    $current = Get-Content -LiteralPath $profilePath -ErrorAction SilentlyContinue
    if ($current -notcontains $marker) {
      Add-Content -LiteralPath $profilePath -Value $aliases
      Write-Step "Appended autoworkflow aliases to $profilePath (restart shell to load)"
    } else {
      Write-Step "Profile already contains aliases marker, skipping append"
    }
  }
}

Write-Step "Done."
