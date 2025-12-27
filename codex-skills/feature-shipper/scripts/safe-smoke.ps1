param(
  [string]$Root = (Get-Location).Path,
  [switch]$UseCodex,
  [switch]$UseOss,
  [ValidateSet("ollama", "lmstudio")]
  [string]$LocalProvider = "ollama",
  [string]$OssModel = "",
  [switch]$KeepTemp
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Msg) { Write-Host "[safe-smoke] $Msg" }

$rootPath = (Resolve-Path -LiteralPath $Root).Path
$ts = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$tempRepo = "$env:TEMP/aw-safe-smoke-$ts"

Write-Step "Source repo: $rootPath"
Write-Step "Temp repo: $tempRepo"

New-Item -ItemType Directory -Force -Path $tempRepo | Out-Null

try {
  # Copy repo to a temp workspace without touching the original working tree
  $excludeDirs = @(".git", ".autoworkflow", ".venv-agents", "__pycache__", ".spec-workflow", ".serena", "archive")
  $xd = ($excludeDirs | ForEach-Object { "`"$_`"" }) -join " "
  $copyCmd = "robocopy `"$rootPath`" `"$tempRepo`" /E /XD $xd"
  Write-Step $copyCmd
  cmd.exe /c $copyCmd | Out-Host
  $rc = $LASTEXITCODE
  if ($rc -gt 7) { throw "robocopy failed with exit code $rc" }

  $aw = Join-Path $rootPath "codex-skills/feature-shipper/scripts/autoworkflow.py"
  if (-not (Test-Path -LiteralPath $aw)) { throw "Missing autoworkflow.py at $aw" }

  # Cold start: init -> set-gate -> plan gen/review -> gate -> runner
  & python "$aw" --root "$tempRepo" init --force

  $testCmd = "python -m py_compile ./agents_runner.py ./agents_sdk_runner.py ./agents_workflow.py ./codex-skills/feature-shipper/scripts/autoworkflow.py"
  & python "$aw" --root "$tempRepo" set-gate --create --build "echo skip" --test "$testCmd" --lint "echo skip" --format-check "echo skip"

  & python "$aw" --root "$tempRepo" plan gen
  & python "$aw" --root "$tempRepo" plan review
  & python "$aw" --root "$tempRepo" gate

  $runner = Join-Path $rootPath "agents_runner.py"
  & python "$runner" --root "$tempRepo"

  if ($UseCodex) {
    $prompt = @"
You are in a project directory on Windows.

Goal: run an end-to-end automation smoke test in the real Codex CLI runtime.

Hard rules:
- Do NOT read or inspect any files.
- Do NOT run any commands other than the 4 commands listed below, in order.
- For each command: print the exact command, run it, then print its exit code.
- If any command fails (non-zero), stop immediately and report the failing step.
- Do NOT edit/create/delete any source files. Only allow artifacts created by these commands (e.g. .autoworkflow/**, .autoworkflow/trace/**, and Python __pycache__).
- Do NOT run git commit/push/reset.

Commands:
1) python -m py_compile ./agents_runner.py ./agents_sdk_runner.py ./agents_workflow.py ./codex-skills/feature-shipper/scripts/autoworkflow.py
2) python .autoworkflow/tools/autoworkflow.py --root . plan review
3) python .autoworkflow/tools/autoworkflow.py --root . gate --allow-unreviewed
4) python agents_runner.py --root . --allow-unreviewed

Finish with a 3-line summary and list any .autoworkflow/trace/*.jsonl files created.
"@

    $codexArgs = @(
      "exec",
      "--full-auto",
      "--skip-git-repo-check",
      "-C", "$tempRepo",
      "-c", 'model_reasoning_effort="low"',
      "-c", 'mcp_servers={}'
    )
    if ($UseOss) {
      $codexArgs += "--oss"
      if ($LocalProvider) { $codexArgs += @("--local-provider", "$LocalProvider") }
      if ($OssModel) { $codexArgs += @("-m", "$OssModel") }
    }
    $codexArgs += "-"

    $prompt | codex @codexArgs
  }

  Write-Step "OK (cold start + gate + runner)"
} finally {
  if (-not $KeepTemp) {
    Write-Step "Cleanup: $tempRepo"
    Remove-Item -LiteralPath $tempRepo -Recurse -Force
  } else {
    Write-Step "Keep temp repo: $tempRepo"
  }
}
