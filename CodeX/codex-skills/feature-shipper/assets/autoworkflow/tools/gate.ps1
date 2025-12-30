param(
  [string]$BuildCmd = "",
  [string]$TestCmd = "",
  [string]$LintCmd = "",
  [string]$FormatCheckCmd = ""
)

$ErrorActionPreference = "Stop"

function Read-GateEnv([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return @{} }
  $map = @{}
  Get-Content -LiteralPath $Path | ForEach-Object {
    $line = $_.Trim()
    if ($line.Length -eq 0) { return }
    if ($line.StartsWith("#")) { return }
    $idx = $line.IndexOf("=")
    if ($idx -lt 1) { return }
    $key = $line.Substring(0, $idx).Trim()
    $val = $line.Substring($idx + 1).Trim()
    if ($key -in @("BUILD_CMD","TEST_CMD","LINT_CMD","FORMAT_CHECK_CMD")) {
      $map[$key] = $val
    }
  }
  return $map
}

function Run-Step([string]$Name, [string]$Cmd) {
  if ([string]::IsNullOrWhiteSpace($Cmd)) { return }
  Write-Host "==> $Name"
  Write-Host $Cmd
  $global:LASTEXITCODE = 0
  Invoke-Expression $Cmd
  if ($LASTEXITCODE -ne 0) {
    throw "$Name failed (exit $LASTEXITCODE)."
  }
}

Write-Host "Gate start: $(Get-Date -Format o)"

if (([string]::IsNullOrWhiteSpace($BuildCmd)) -or ([string]::IsNullOrWhiteSpace($TestCmd)) -or ([string]::IsNullOrWhiteSpace($LintCmd)) -or ([string]::IsNullOrWhiteSpace($FormatCheckCmd))) {
  $envPath = Join-Path (Get-Location) ".autoworkflow\\gate.env"
  $envMap = Read-GateEnv $envPath
  if ([string]::IsNullOrWhiteSpace($BuildCmd) -and $envMap.ContainsKey("BUILD_CMD")) { $BuildCmd = $envMap["BUILD_CMD"] }
  if ([string]::IsNullOrWhiteSpace($TestCmd) -and $envMap.ContainsKey("TEST_CMD")) { $TestCmd = $envMap["TEST_CMD"] }
  if ([string]::IsNullOrWhiteSpace($LintCmd) -and $envMap.ContainsKey("LINT_CMD")) { $LintCmd = $envMap["LINT_CMD"] }
  if ([string]::IsNullOrWhiteSpace($FormatCheckCmd) -and $envMap.ContainsKey("FORMAT_CHECK_CMD")) { $FormatCheckCmd = $envMap["FORMAT_CHECK_CMD"] }
}

Run-Step "Build" $BuildCmd
if ([string]::IsNullOrWhiteSpace($TestCmd)) {
  throw "Missing TestCmd (set TEST_CMD in .autoworkflow\\gate.env or pass -TestCmd)."
}
Run-Step "Test" $TestCmd
Run-Step "Lint" $LintCmd
Run-Step "FormatCheck" $FormatCheckCmd

Write-Host "Gate done (green)."
