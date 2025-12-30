$ErrorActionPreference = "Stop"

$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\\.."))

powershell -ExecutionPolicy Bypass -File (Join-Path $root "CodeX\\codex-skills\\feature-shipper\\scripts\\install-claude-global.ps1") `
  -ClaudeHome (Join-Path $root ".claude") `
  -Force

Write-Host "[install-local] Done: $(Join-Path $root '.claude')"
