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
$CodeXHome = [IO.Path]::GetFullPath($CodeXHome)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$featureShipperDir = Split-Path -Parent $scriptDir
$skillsRoot = Split-Path -Parent $featureShipperDir
$targetSkills = Join-Path $CodeXHome "skills"
$manifest = Join-Path $CodeXHome ".autoworkflow-codex-installed.txt"

function Write-Step([string]$Msg) { Write-Host "[install-codex-global] $Msg" }

Write-Step "Source skills: $skillsRoot"
Write-Step "Target skills: $targetSkills"
Write-Step "Codex manifest: $manifest"
if ($DryRun) { Write-Step "Dry-run mode (no changes will be written)" }

function Get-SkillFiles([string]$Path) {
  Get-ChildItem -LiteralPath $Path -Recurse -File -Force | Where-Object {
    $_.Extension -notin @(".pyc", ".pyo") -and
    $_.FullName -notmatch "(\\\\|/)(__pycache__|\\.pytest_cache|\\.mypy_cache|\\.ruff_cache)(\\\\|/)"
  }
}

function Copy-SkillDir([string]$Name, [System.Collections.Generic.List[string]]$Installed) {
  $src = Join-Path $skillsRoot $Name
  $dst = Join-Path $targetSkills $Name

  if ((Test-Path -LiteralPath $dst) -and -not $Force) {
    Write-Step "Skip existing $dst (use -Force to overwrite)"
    return
  }

  if ($DryRun) {
    if ($Force -and (Test-Path -LiteralPath $dst)) {
      Write-Step "Would remove (force) $dst"
    }
    Write-Step "Would ensure dir $targetSkills"
    Write-Step "Would copy dir $src -> $dst"
    Get-SkillFiles -Path $src | ForEach-Object {
      $rel = $_.FullName.Substring($src.Length).TrimStart('\', '/')
      $destFile = Join-Path $dst $rel
      Write-Step "Would add $destFile"
    }
    return
  }

  New-Item -ItemType Directory -Force -Path $targetSkills | Out-Null
  if ($Force -and (Test-Path -LiteralPath $dst)) {
    Remove-Item -LiteralPath $dst -Recurse -Force
  }
  Copy-Item -LiteralPath $src -Destination $dst -Recurse -Force

  Get-ChildItem -LiteralPath $dst -Recurse -Directory -Force | Where-Object {
    $_.Name -in @("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")
  } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
  Get-ChildItem -LiteralPath $dst -Recurse -File -Force | Where-Object {
    $_.Extension -in @(".pyc", ".pyo")
  } | Remove-Item -Force -ErrorAction SilentlyContinue

  Get-SkillFiles -Path $dst | ForEach-Object { $Installed.Add($_.FullName) | Out-Null }
  Write-Step "Installed $Name"
}

$skillDirs = Get-ChildItem -LiteralPath $skillsRoot -Directory | Where-Object { $_.Name -notlike ".*" }
if (-not $skillDirs) {
  Write-Step "No skill directories found under $skillsRoot"
  exit 1
}

$installed = New-Object 'System.Collections.Generic.List[string]'
foreach ($dir in $skillDirs) {
  Copy-SkillDir -Name $dir.Name -Installed $installed
}

if ($DryRun) {
  Write-Step "Would write manifest $manifest"
} else {
  if ($installed.Count -gt 0) {
    $existing = @()
    if (Test-Path -LiteralPath $manifest) {
      $existing = Get-Content -LiteralPath $manifest -ErrorAction SilentlyContinue
    }
    ($existing + $installed) | Sort-Object -Unique | Set-Content -LiteralPath $manifest -Encoding UTF8
    Write-Step "Updated manifest $manifest"
  } else {
    Write-Step "No new Codex files installed (manifest unchanged)"
  }
}

if (-not $NoProfile) {
  $profilePath = $PROFILE
  $markerBegin = "# codex autoworkflow aliases (begin)"
  $markerEnd = "# codex autoworkflow aliases (end)"
  $tool = Join-Path (Join-Path $CodeXHome "skills/feature-shipper/scripts") "autoworkflow.py"
  $aliasesTemplate = @'
# codex autoworkflow aliases (begin)
if (-not $env:CODEX_HOME -or $env:CODEX_HOME.Trim().Length -eq 0) { $env:CODEX_HOME = "__AW_CODEX_HOME__" }
function aw-init {
  $root = (Get-Location)
  $rest = @()
  if ($args.Count -gt 0 -and -not ($args[0] -match '^-')) { $root = $args[0]; $rest = if ($args.Count -gt 1) { $args[1..($args.Count-1)] } else { @() } } else { $rest = $args }
  python "__AW_TOOL__" --root $root init @rest
}
function aw-auto {
  $root = (Get-Location)
  $rest = @()
  if ($args.Count -gt 0 -and -not ($args[0] -match '^-')) { $root = $args[0]; $rest = if ($args.Count -gt 1) { $args[1..($args.Count-1)] } else { @() } } else { $rest = $args }
  python "__AW_TOOL__" --root $root auto-gate @rest
}
function aw-gate {
  $root = (Get-Location)
  $rest = @()
  if ($args.Count -gt 0 -and -not ($args[0] -match '^-')) { $root = $args[0]; $rest = if ($args.Count -gt 1) { $args[1..($args.Count-1)] } else { @() } } else { $rest = $args }
  python "__AW_TOOL__" --root $root gate @rest
}
function aw-doctor {
  $root = (Get-Location)
  $rest = @()
  if ($args.Count -gt 0 -and -not ($args[0] -match '^-')) { $root = $args[0]; $rest = if ($args.Count -gt 1) { $args[1..($args.Count-1)] } else { @() } } else { $rest = $args }
  python "__AW_TOOL__" --root $root doctor --write --update-state @rest
}
function aw-uninstall {
  $root = (Get-Location)
  $rest = @()
  if ($args.Count -gt 0 -and -not ($args[0] -match '^-')) { $root = $args[0]; $rest = if ($args.Count -gt 1) { $args[1..($args.Count-1)] } else { @() } } else { $rest = $args }
  python "__AW_TOOL__" --root $root uninstall @rest
}
# codex autoworkflow aliases (end)
'@
  $aliases = (
    $aliasesTemplate.
      Replace("__AW_TOOL__", $tool).
      Replace("__AW_CODEX_HOME__", $CodeXHome)
  )

  if ($DryRun) {
    Write-Step "Would append aliases to $profilePath"
  } else {
    New-Item -ItemType File -Force -Path $profilePath | Out-Null
    $current = Get-Content -LiteralPath $profilePath -ErrorAction SilentlyContinue
    if ($current -notcontains $markerBegin) {
      Add-Content -LiteralPath $profilePath -Value $aliases
      Write-Step "Appended autoworkflow aliases to $profilePath (restart shell to load)"
    } else {
      Write-Step "Profile already contains aliases marker, skipping append"
    }
  }
}

Write-Step "Done."

