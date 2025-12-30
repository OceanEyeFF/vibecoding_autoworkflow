$ErrorActionPreference = "Stop"

$toolDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $toolDir "autoworkflow.py"

if (-not (Test-Path -LiteralPath $script)) {
  throw "Missing $script (run autoworkflow init first)."
}

python $script @args
