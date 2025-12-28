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

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$featureShipperDir = Split-Path -Parent $scriptDir
$skillsRoot = Split-Path -Parent $featureShipperDir
$repoRoot = Split-Path -Parent $skillsRoot
$targetSkills = Join-Path $CodeXHome "skills"

function Write-Step([string]$Msg) { Write-Host "[install-global] $Msg" }

Write-Step "Source skills: $skillsRoot"
Write-Step "Target skills: $targetSkills"
if (-not $NoClaude) {
  Write-Step "Source claude: $(Join-Path $repoRoot '.claude')"
  Write-Step "Target claude: $ClaudeHome"
}
if ($DryRun) { Write-Step "Dry-run mode (no changes will be written)" }

function Copy-SkillDir([string]$Name) {
  $src = Join-Path $skillsRoot $Name
  $dst = Join-Path $targetSkills $Name
  if ($DryRun) {
    if ($Force -and (Test-Path -LiteralPath $dst)) {
      Write-Step "Would remove (force) $dst"
    }
    Write-Step "Would ensure dir $targetSkills"
    Write-Step "Would copy dir $src -> $dst"
    Get-ChildItem -LiteralPath $src -Recurse -File -Force | Where-Object {
      $_.Extension -notin @(".pyc", ".pyo") -and
      $_.FullName -notmatch "(\\\\|/)(__pycache__|\\.pytest_cache|\\.mypy_cache|\\.ruff_cache)(\\\\|/)"
    } | ForEach-Object {
      $rel = $_.FullName.Substring($src.Length).TrimStart('\', '/')
      $destFile = Join-Path $dst $rel
      Write-Step "Would add $destFile"
    }
    return
  }
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

function Copy-ClaudeTree([string]$Src, [string]$Dst, [System.Collections.Generic.List[string]]$Installed) {
  if (-not (Test-Path -LiteralPath $Src)) {
    Write-Step "Skip missing $Src"
    return
  }

  if ($DryRun) {
    Write-Step "Would ensure dir $Dst"
    Get-ChildItem -LiteralPath $Src -Recurse -File -Force | Where-Object {
      $_.Extension -notin @(".pyc", ".pyo") -and
      $_.FullName -notmatch "(\\\\|/)(__pycache__|\\.pytest_cache|\\.mypy_cache|\\.ruff_cache)(\\\\|/)"
    } | ForEach-Object {
      $rel = $_.FullName.Substring($Src.Length).TrimStart('\', '/')
      $destFile = Join-Path $Dst $rel
      if ((Test-Path -LiteralPath $destFile) -and -not $Force) {
        Write-Step "Would skip existing $destFile"
      } elseif ((Test-Path -LiteralPath $destFile) -and $Force) {
        Write-Step "Would overwrite $destFile"
      } else {
        Write-Step "Would add $destFile"
      }
    }
    return
  }

  New-Item -ItemType Directory -Force -Path $Dst | Out-Null
  Get-ChildItem -LiteralPath $Src -Recurse -File -Force | Where-Object {
    $_.Extension -notin @(".pyc", ".pyo") -and
    $_.FullName -notmatch "(\\\\|/)(__pycache__|\\.pytest_cache|\\.mypy_cache|\\.ruff_cache)(\\\\|/)"
  } | ForEach-Object {
    $rel = $_.FullName.Substring($Src.Length).TrimStart('\', '/')
    $destFile = Join-Path $Dst $rel
    if ((Test-Path -LiteralPath $destFile) -and -not $Force) { return }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destFile) | Out-Null
    Copy-Item -LiteralPath $_.FullName -Destination $destFile -Force
    $Installed.Add($destFile) | Out-Null
  }
}

if (-not $NoClaude) {
  $manifest = Join-Path $ClaudeHome ".autoworkflow-installed.txt"
  if ($DryRun) {
    Write-Step "Would write manifest $manifest"
  }

  $installed = New-Object 'System.Collections.Generic.List[string]'
  Copy-ClaudeTree -Src (Join-Path $repoRoot ".claude\\agents") -Dst (Join-Path $ClaudeHome "agents") -Installed $installed
  Copy-ClaudeTree -Src (Join-Path $repoRoot ".claude\\skills") -Dst (Join-Path $ClaudeHome "skills") -Installed $installed
  Copy-ClaudeTree -Src (Join-Path $repoRoot ".claude\\commands") -Dst (Join-Path $ClaudeHome "commands") -Installed $installed

  if (-not $DryRun) {
    if ($installed.Count -gt 0) {
      New-Item -ItemType Directory -Force -Path $ClaudeHome | Out-Null
      $existing = @()
      if (Test-Path -LiteralPath $manifest) {
        $existing = Get-Content -LiteralPath $manifest -ErrorAction SilentlyContinue
      }
      ($existing + $installed) | Sort-Object -Unique | Set-Content -LiteralPath $manifest -Encoding UTF8
      Write-Step "Installed Claude assets (manifest: $manifest)"
    } else {
      Write-Step "No Claude files installed (nothing to manifest)"
    }
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
if (-not $env:CLAUDE_HOME -or $env:CLAUDE_HOME.Trim().Length -eq 0) { $env:CLAUDE_HOME = "__AW_CLAUDE_HOME__" }
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
      Replace("__AW_CODEX_HOME__", $CodeXHome).
      Replace("__AW_CLAUDE_HOME__", $ClaudeHome)
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
