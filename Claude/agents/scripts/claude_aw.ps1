param(
  [string]$Root = ".",
  [Alias("branch","branch-name")]
  [string]$BranchName = "",
  [string]$Base = "develop",
  [Alias("bootstrap-base-from")]
  [string]$BootstrapBaseFrom = "",
  [switch]$Commit,
  [switch]$Push,
  [switch]$PR,
  [switch]$Draft,
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
$repoTool = Join-Path $rootPath "CodeX/codex-skills/feature-shipper/scripts/autoworkflow.py"
$candidateTools += $repoTool

$codexHome = $env:CODEX_HOME
if (-not $codexHome -or $codexHome.Trim().Length -eq 0) {
  $codexHome = Join-Path $HOME ".codex"
}
$codexHomeTool = Join-Path (Join-Path $codexHome "skills/feature-shipper/scripts") "autoworkflow.py"
$candidateTools += $codexHomeTool

$localTool = Join-Path $rootPath ".autoworkflow/tools/autoworkflow.py"
$candidateTools += $localTool

$tool = $null
foreach ($cand in $candidateTools) {
  if ($cand -and (Test-Path -LiteralPath $cand)) { $tool = $cand; break }
}
if (-not $tool) {
  throw "autoworkflow.py not found. Expected one of: .autoworkflow/tools/autoworkflow.py, $env:CODEX_HOME/skills/feature-shipper/scripts/autoworkflow.py, or CodeX/codex-skills/feature-shipper/scripts/autoworkflow.py"
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

if ($Commit.IsPresent) {
  Run-Step "git commit" "python `"$tool`" --root `"$rootPath`" git commit --all --auto-message"
}

if ($PR.IsPresent) {
  $draftArg = ""
  if ($Draft.IsPresent) { $draftArg = "--draft" }
  $bootstrapArg = ""
  if ($BootstrapBaseFrom -and $BootstrapBaseFrom.Trim().Length -gt 0) { $bootstrapArg = "--bootstrap-base-from `"$BootstrapBaseFrom`"" }
  Run-Step "git pr create" "python `"$tool`" --root `"$rootPath`" git pr create --base `"$Base`" --push -u $draftArg $bootstrapArg"
} elseif ($Push.IsPresent) {
  Run-Step "git push" "python `"$tool`" --root `"$rootPath`" git push -u"
}

Write-Host "Done."
