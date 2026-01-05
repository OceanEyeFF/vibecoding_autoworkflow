# Claude Code Agents/Skills Global Installation Script (PowerShell)
# Purpose: Install Claude/ directory contents to ~/.claude/ global directory
# Author: AW-Kernel Team
# Date: 2026-01-04

param(
    [string]$Namespace = "aw-kernel",
    [switch]$Force,
    [switch]$DryRun,
    [switch]$Uninstall,
    [switch]$Help
)

# Script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$ClaudeSrc = Join-Path $RepoRoot "Claude"

# Target directory
if ($env:CLAUDE_HOME) {
    $ClaudeHome = $env:CLAUDE_HOME
} else {
    $ClaudeHome = Join-Path $env:USERPROFILE ".claude"
}

# Color functions
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Blue }
function Write-Success { param($Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[ERR] $Message" -ForegroundColor Red }

# Show help information
function Show-Help {
    Write-Host "======================================================" -ForegroundColor Blue
    Write-Host "Claude Code Global Installation Script" -ForegroundColor Green
    Write-Host "======================================================" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Purpose: Install agents/skills/commands from Claude/ to global directory" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy Bypass -File install-global.ps1 [options]"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -Help               Show this help message"
    Write-Host "  -Namespace NAME     Specify namespace (default: aw-kernel)"
    Write-Host "  -Force              Force overwrite existing files"
    Write-Host "  -DryRun             Preview operations without executing"
    Write-Host "  -Uninstall          Uninstall installed content"
    Write-Host ""
    Write-Host "Environment Variables:" -ForegroundColor Yellow
    Write-Host "  CLAUDE_HOME         Claude Code global directory (default: ~/.claude)"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  # Standard installation"
    Write-Host "  powershell -ExecutionPolicy Bypass -File install-global.ps1"
    Write-Host ""
    Write-Host "  # Use custom namespace"
    Write-Host "  powershell -ExecutionPolicy Bypass -File install-global.ps1 -Namespace my-agents"
    Write-Host ""
    Write-Host "  # Preview installation"
    Write-Host "  powershell -ExecutionPolicy Bypass -File install-global.ps1 -DryRun"
    Write-Host ""
    Write-Host "  # Uninstall"
    Write-Host "  powershell -ExecutionPolicy Bypass -File install-global.ps1 -Uninstall"
    Write-Host ""
    Write-Host "Directory Structure:" -ForegroundColor Yellow
    Write-Host "  ~/.claude/agents/aw-kernel/           # Agents (AutoWorkflow Kernel)"
    Write-Host "  ~/.claude/skills/aw-kernel/           # Skills"
    Write-Host "  ~/.claude/commands/aw-kernel/         # Commands"
    Write-Host ""
    Write-Host "======================================================" -ForegroundColor Blue
}

# Execute command (supports dry-run)
function Invoke-Cmd {
    param($Command, $Description)

    if ($DryRun) {
        Write-Host "[DRY-RUN] $Description" -ForegroundColor Yellow
    } else {
        Invoke-Expression $Command
    }
}

# Uninstall function
function Uninstall-Claude {
    Write-Info "Starting uninstall for namespace: $Namespace"

    $AgentsDir = Join-Path $ClaudeHome "agents\$Namespace"
    $SkillsDir = Join-Path $ClaudeHome "skills\$Namespace"
    $CommandsDir = Join-Path $ClaudeHome "commands\$Namespace"

    if (Test-Path $AgentsDir) {
        Write-Warning "Removing Agents: $AgentsDir"
        Invoke-Cmd "Remove-Item -Path '$AgentsDir' -Recurse -Force" "Remove Agents"
    }

    if (Test-Path $SkillsDir) {
        Write-Warning "Removing Skills: $SkillsDir"
        Invoke-Cmd "Remove-Item -Path '$SkillsDir' -Recurse -Force" "Remove Skills"
    }

    if (Test-Path $CommandsDir) {
        Write-Warning "Removing Commands: $CommandsDir"
        Invoke-Cmd "Remove-Item -Path '$CommandsDir' -Recurse -Force" "Remove Commands"
    }

    Write-Success "Uninstall completed!"
}

# Install function
function Install-Claude {
    Write-Info "Starting installation to global directory: $ClaudeHome"
    Write-Info "Namespace: $Namespace"

    # Check source directory
    if (-not (Test-Path $ClaudeSrc)) {
        Write-Error "Source directory does not exist: $ClaudeSrc"
        exit 1
    }

    # Create target directories
    Write-Info "Creating target directories..."
    $AgentsTargetDir = Join-Path $ClaudeHome "agents\$Namespace"
    $SkillsTargetDir = Join-Path $ClaudeHome "skills\$Namespace"
    $CommandsTargetDir = Join-Path $ClaudeHome "commands\$Namespace"

    Invoke-Cmd "New-Item -ItemType Directory -Path '$AgentsTargetDir' -Force | Out-Null" "Create Agents directory"
    Invoke-Cmd "New-Item -ItemType Directory -Path '$SkillsTargetDir' -Force | Out-Null" "Create Skills directory"
    Invoke-Cmd "New-Item -ItemType Directory -Path '$CommandsTargetDir' -Force | Out-Null" "Create Commands directory"

    # Install Agents
    $AgentsSrcDir = Join-Path $ClaudeSrc "agents\aw-kernel"
    if (Test-Path $AgentsSrcDir) {
        Write-Info "Installing Agents..."
        $AgentCount = 0

        Get-ChildItem -Path $AgentsSrcDir -Filter "*.md" | ForEach-Object {
            $BaseName = $_.Name

            # Skip non-Agent files
            if ($BaseName -eq "CLAUDE.md" -or $BaseName -eq "TOOLCHAIN.md" -or $BaseName -eq "RECHECK-REPORT.md" -or $BaseName -eq "STANDARDS.md") {
                return
            }

            $Target = Join-Path $AgentsTargetDir $BaseName

            if ((Test-Path $Target) -and (-not $Force)) {
                Write-Warning "Skipping existing Agent: $BaseName"
            } else {
                Invoke-Cmd "Copy-Item -Path '$($_.FullName)' -Destination '$Target' -Force" "Install Agent: $BaseName"
                Write-Success "Installed Agent: $BaseName"
                $AgentCount++
            }
        }

        Write-Info "Installed $AgentCount Agents"
    }

    # Install Skills
    $SkillsSrcDir = Join-Path $ClaudeSrc "skills\aw-kernel"
    if (Test-Path $SkillsSrcDir) {
        Write-Info "Installing Skills..."
        $SkillCount = 0

        Get-ChildItem -Path $SkillsSrcDir -Directory | ForEach-Object {
            $SkillName = $_.Name
            $TargetDir = Join-Path $SkillsTargetDir $SkillName

            if ((Test-Path $TargetDir) -and (-not $Force)) {
                Write-Warning "Skipping existing Skill: $SkillName"
            } else {
                Invoke-Cmd "New-Item -ItemType Directory -Path '$TargetDir' -Force | Out-Null" "Create Skill directory"
                Invoke-Cmd "Copy-Item -Path '$($_.FullName)\*' -Destination '$TargetDir\' -Recurse -Force" "Copy Skill content"
                Write-Success "Installed Skill: $SkillName"
                $SkillCount++
            }
        }

        Write-Info "Installed $SkillCount Skills"
    }

    # Install Commands (if exists)
    $CommandsSrcDir = Join-Path $ClaudeSrc "commands"
    if (Test-Path $CommandsSrcDir) {
        Write-Info "Installing Commands..."
        Invoke-Cmd "Copy-Item -Path '$CommandsSrcDir\*' -Destination '$CommandsTargetDir\' -Recurse -Force" "Copy Commands"
    }

    # Copy documentation files
    Write-Info "Copying documentation files..."
    $ClaudeMd = Join-Path $AgentsSrcDir "CLAUDE.md"
    if (Test-Path $ClaudeMd) {
        Invoke-Cmd "Copy-Item -Path '$ClaudeMd' -Destination '$AgentsTargetDir\' -Force" "Copy CLAUDE.md"
    }

    $ToolchainMd = Join-Path $AgentsSrcDir "TOOLCHAIN.md"
    if (Test-Path $ToolchainMd) {
        Invoke-Cmd "Copy-Item -Path '$ToolchainMd' -Destination '$AgentsTargetDir\' -Force" "Copy TOOLCHAIN.md"
    }

    $StandardsMd = Join-Path $AgentsSrcDir "STANDARDS.md"
    if (Test-Path $StandardsMd) {
        Invoke-Cmd "Copy-Item -Path '$StandardsMd' -Destination '$AgentsTargetDir\' -Force" "Copy STANDARDS.md"
    }

    # Create installation marker file
    $MarkerFile = Join-Path $AgentsTargetDir ".installed"
    $UtcTime = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $MarkerContent = @"
# Installation Info
namespace: $Namespace
installed_at: $UtcTime
installed_by: $env:USERNAME
source_repo: $RepoRoot
version: 1.0.0
"@

    if (-not $DryRun) {
        $MarkerContent | Out-File -FilePath $MarkerFile -Encoding UTF8
    }

    Write-Success "================================================"
    Write-Success "Installation completed successfully!"
    Write-Success "================================================"
    Write-Info ""
    Write-Info "Installed content locations:"
    Write-Info "  Agents:   $AgentsTargetDir"
    Write-Info "  Skills:   $SkillsTargetDir"
    Write-Info "  Commands: $CommandsTargetDir"
    Write-Info ""
    Write-Info "To uninstall, run:"
    Write-Info "  powershell -ExecutionPolicy Bypass -File install-global.ps1 -Uninstall -Namespace $Namespace"
}

# Main logic
if ($Help) {
    Show-Help
    exit 0
}

Write-Host "======================================================" -ForegroundColor Blue
Write-Host "Claude Code Global Installation Script" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Blue
Write-Host ""

if ($Uninstall) {
    Uninstall-Claude
} else {
    Install-Claude
}

exit 0
