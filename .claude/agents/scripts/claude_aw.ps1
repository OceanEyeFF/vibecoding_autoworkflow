$ErrorActionPreference = "Stop"
param(
  [string]$Root = ".",
  [switch]$AllowUnreviewed,
  [switch]$DryRun
)

function Run-Step($name, $cmd) {
  Write-Host "==> $name"
  Write-Host $cmd
  if ($DryRun) { return }
  & powershell -NoProfile -ExecutionPolicy Bypass -Command $cmd
  if ($LASTEXITCODE -ne 0) { throw "$name failed (exit $LASTEXITCODE)" }
}

$rootPath = Resolve-Path -LiteralPath $Root
$tool = Join-Path $rootPath ".autoworkflow/tools/autoworkflow.py"
if (-not (Test-Path -LiteralPath $tool)) {
  # try repo script
  $tool = Join-Path $rootPath "codex-skills/feature-shipper/scripts/autoworkflow.py"
}

if ($DryRun) {
  Write-Host "[dry-run] root: $rootPath"
}

Run-Step "init" "python `"$tool`" --root `"$rootPath`" init"
Run-Step "auto-gate" "python `"$tool`" --root `"$rootPath`" auto-gate"
Run-Step "plan gen" "python `"$tool`" --root `"$rootPath`" plan gen"
Run-Step "plan review" "python `"$tool`" --root `"$rootPath`" plan review"
$allow = $AllowUnreviewed.IsPresent ? "--allow-unreviewed" : ""
Run-Step "gate (dry-run)" "python `"$tool`" --root `"$rootPath`" gate $allow --test '''' --build '''' --lint '''' --format-check ''''"

Write-Host "Done."
