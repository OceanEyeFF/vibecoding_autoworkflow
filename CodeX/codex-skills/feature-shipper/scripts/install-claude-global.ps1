param(
  [string]$ClaudeHome = $env:CLAUDE_HOME,
  [switch]$Force,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if (-not $ClaudeHome -or $ClaudeHome.Trim().Length -eq 0) {
  $ClaudeHome = Join-Path $env:USERPROFILE ".claude"
}
$ClaudeHome = [IO.Path]::GetFullPath($ClaudeHome)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$featureShipperDir = Split-Path -Parent $scriptDir
$skillsRoot = Split-Path -Parent $featureShipperDir
$repoRoot = Split-Path -Parent (Split-Path -Parent $skillsRoot)

$manifest = Join-Path $ClaudeHome ".autoworkflow-claude-installed.txt"
$manifestLegacy = Join-Path $ClaudeHome ".autoworkflow-installed.txt"

function Write-Step([string]$Msg) { Write-Host "[install-claude-global] $Msg" }

Write-Step "Source claude: $(Join-Path $repoRoot 'Claude')"
Write-Step "Target claude: $ClaudeHome"
Write-Step "Claude manifest: $manifest"
Write-Step "Claude legacy manifest: $manifestLegacy"
if ($DryRun) { Write-Step "Dry-run mode (no changes will be written)" }

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

$installed = New-Object 'System.Collections.Generic.List[string]'
Copy-ClaudeTree -Src (Join-Path $repoRoot "Claude\\agents") -Dst (Join-Path $ClaudeHome "agents") -Installed $installed
Copy-ClaudeTree -Src (Join-Path $repoRoot "Claude\\skills") -Dst (Join-Path $ClaudeHome "skills") -Installed $installed
Copy-ClaudeTree -Src (Join-Path $repoRoot "Claude\\commands") -Dst (Join-Path $ClaudeHome "commands") -Installed $installed

if ($DryRun) {
  Write-Step "Would write manifest $manifest"
  Write-Step "Would also write legacy manifest $manifestLegacy"
} else {
  if ($installed.Count -gt 0) {
    New-Item -ItemType Directory -Force -Path $ClaudeHome | Out-Null
    $existing = @()
    if (Test-Path -LiteralPath $manifest) {
      $existing += Get-Content -LiteralPath $manifest -ErrorAction SilentlyContinue
    }
    if (Test-Path -LiteralPath $manifestLegacy) {
      $existing += Get-Content -LiteralPath $manifestLegacy -ErrorAction SilentlyContinue
    }
    ($existing + $installed) | Sort-Object -Unique | Set-Content -LiteralPath $manifest -Encoding UTF8
    Copy-Item -LiteralPath $manifest -Destination $manifestLegacy -Force
    Write-Step "Installed Claude assets (manifest: $manifest)"
  } else {
    Write-Step "No Claude files installed (nothing to manifest)"
  }
}

Write-Step "Done."
