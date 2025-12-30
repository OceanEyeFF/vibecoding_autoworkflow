$ErrorActionPreference = "Stop"

$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\\.."))

python (Join-Path $root "CodeX\\codex-skills\\feature-shipper\\scripts\\autoworkflow.py") --root $root uninstall --yes
Write-Host "[uninstall-local] Done: $(Join-Path $root '.autoworkflow')"

