param(
  [string]$Root = ".",
  [Alias("branch","branch-name")]
  [string]$BranchName = "",
  [Alias("allow-unreviewed")]
  [switch]$AllowUnreviewed,
  [Alias("dry-run")]
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Run-Step($name, $cmd) {
  Write-Host "==> $name"
  Write-Host $cmd
  if ($DryRun) { return }
  & powershell -NoProfile -ExecutionPolicy Bypass -Command $cmd
  if ($LASTEXITCODE -ne 0) { throw "$name failed (exit $LASTEXITCODE)" }
}

$rootPath = Resolve-Path -LiteralPath $Root

$candidateTools = @()
$repoTool = Join-Path $rootPath "codex-skills/feature-shipper/scripts/autoworkflow.py"
$candidateTools += $repoTool

if ($env:CODEX_HOME -and $env:CODEX_HOME.Trim().Length -gt 0) {
  $codexHomeTool = Join-Path (Join-Path $env:CODEX_HOME "skills/feature-shipper/scripts") "autoworkflow.py"
  $candidateTools += $codexHomeTool
}

$localTool = Join-Path $rootPath ".autoworkflow/tools/autoworkflow.py"
$candidateTools += $localTool

$tool = $null
foreach ($cand in $candidateTools) {
  if ($cand -and (Test-Path -LiteralPath $cand)) { $tool = $cand; break }
}
if (-not $tool) {
  throw "autoworkflow.py not found. Expected one of: .autoworkflow/tools/autoworkflow.py, $env:CODEX_HOME/skills/feature-shipper/scripts/autoworkflow.py, or codex-skills/feature-shipper/scripts/autoworkflow.py"
}

if ($DryRun) {
  Write-Host "[dry-run] root: $rootPath"
}

Run-Step "init" "python `"$tool`" --root `"$rootPath`" init"
$branchArgs = ""
if ($BranchName -and $BranchName.Trim().Length -gt 0) { $branchArgs = "--name `"$BranchName`"" }
Run-Step "git branch start" "python `"$tool`" --root `"$rootPath`" git branch start $branchArgs"
Run-Step "auto-gate" "python `"$tool`" --root `"$rootPath`" auto-gate"
Run-Step "plan gen" "python `"$tool`" --root `"$rootPath`" plan gen"
Run-Step "plan review" "python `"$tool`" --root `"$rootPath`" plan review"
$allow = ""
if ($AllowUnreviewed.IsPresent) { $allow = "--allow-unreviewed" }
Run-Step "gate" "python `"$tool`" --root `"$rootPath`" gate $allow"

Write-Host "Done."
