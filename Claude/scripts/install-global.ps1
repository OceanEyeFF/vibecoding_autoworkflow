# Claude Code Agents/Skills 全局安装脚本 (PowerShell)
# 用途：将 Claude/ 目录的内容安装到 ~/.claude/ 全局目录
# 作者：浮浮酱 (*^▽^*)
# 日期：2026-01-04

param(
    [string]$Namespace = "aw-kernel",
    [switch]$Force,
    [switch]$DryRun,
    [switch]$Uninstall,
    [switch]$Help
)

# 脚本目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$ClaudeSrc = Join-Path $RepoRoot "Claude"

# 目标目录
if ($env:CLAUDE_HOME) {
    $ClaudeHome = $env:CLAUDE_HOME
} else {
    $ClaudeHome = Join-Path $env:USERPROFILE ".claude"
}

# 颜色函数
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Blue }
function Write-Success { param($Message) Write-Host "[✓] $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "[⚠] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[✗] $Message" -ForegroundColor Red }

# 显示帮助信息
function Show-Help {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host "Claude Code 全局安装脚本 ฅ'ω'ฅ" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host ""
    Write-Host "用途：将 Claude/ 目录的 agents/skills/commands 安装到全局" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "用法：" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy Bypass -File install-global.ps1 [选项]"
    Write-Host ""
    Write-Host "选项：" -ForegroundColor Yellow
    Write-Host "  -Help               显示此帮助信息"
    Write-Host "  -Namespace NAME     指定命名空间（默认: aw-kernel）"
    Write-Host "  -Force              强制覆盖已存在的文件"
    Write-Host "  -DryRun             预览将要执行的操作，但不实际执行"
    Write-Host "  -Uninstall          卸载已安装的内容"
    Write-Host ""
    Write-Host "环境变量：" -ForegroundColor Yellow
    Write-Host "  CLAUDE_HOME         Claude Code 全局目录（默认: ~/.claude）"
    Write-Host ""
    Write-Host "示例：" -ForegroundColor Yellow
    Write-Host "  # 标准安装"
    Write-Host "  powershell -ExecutionPolicy Bypass -File install-global.ps1"
    Write-Host ""
    Write-Host "  # 使用自定义命名空间"
    Write-Host "  powershell -ExecutionPolicy Bypass -File install-global.ps1 -Namespace my-agents"
    Write-Host ""
    Write-Host "  # 预览安装操作"
    Write-Host "  powershell -ExecutionPolicy Bypass -File install-global.ps1 -DryRun"
    Write-Host ""
    Write-Host "  # 卸载"
    Write-Host "  powershell -ExecutionPolicy Bypass -File install-global.ps1 -Uninstall"
    Write-Host ""
    Write-Host "目录结构：" -ForegroundColor Yellow
    Write-Host "  ~/.claude/agents/aw-kernel/           # Agents (AutoWorkflow Kernel)"
    Write-Host "  ~/.claude/skills/aw-kernel/           # Skills"
    Write-Host "  ~/.claude/commands/aw-kernel/         # Commands"
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
}

# 执行命令（支持 dry-run）
function Invoke-Cmd {
    param($Command, $Description)

    if ($DryRun) {
        Write-Host "[DRY-RUN] $Description" -ForegroundColor Yellow
    } else {
        Invoke-Expression $Command
    }
}

# 卸载函数
function Uninstall-Claude {
    Write-Info "开始卸载命名空间: $Namespace"

    $AgentsDir = Join-Path $ClaudeHome "agents\$Namespace"
    $SkillsDir = Join-Path $ClaudeHome "skills\$Namespace"
    $CommandsDir = Join-Path $ClaudeHome "commands\$Namespace"

    if (Test-Path $AgentsDir) {
        Write-Warning "删除 Agents: $AgentsDir"
        Invoke-Cmd "Remove-Item -Path '$AgentsDir' -Recurse -Force" "删除 Agents"
    }

    if (Test-Path $SkillsDir) {
        Write-Warning "删除 Skills: $SkillsDir"
        Invoke-Cmd "Remove-Item -Path '$SkillsDir' -Recurse -Force" "删除 Skills"
    }

    if (Test-Path $CommandsDir) {
        Write-Warning "删除 Commands: $CommandsDir"
        Invoke-Cmd "Remove-Item -Path '$CommandsDir' -Recurse -Force" "删除 Commands"
    }

    Write-Success "卸载完成喵～"
}

# 安装函数
function Install-Claude {
    Write-Info "开始安装到全局目录: $ClaudeHome"
    Write-Info "命名空间: $Namespace"

    # 检查源目录
    if (-not (Test-Path $ClaudeSrc)) {
        Write-Error "源目录不存在: $ClaudeSrc"
        exit 1
    }

    # 创建目标目录
    Write-Info "创建目标目录..."
    $AgentsTargetDir = Join-Path $ClaudeHome "agents\$Namespace"
    $SkillsTargetDir = Join-Path $ClaudeHome "skills\$Namespace"
    $CommandsTargetDir = Join-Path $ClaudeHome "commands\$Namespace"

    Invoke-Cmd "New-Item -ItemType Directory -Path '$AgentsTargetDir' -Force | Out-Null" "创建 Agents 目录"
    Invoke-Cmd "New-Item -ItemType Directory -Path '$SkillsTargetDir' -Force | Out-Null" "创建 Skills 目录"
    Invoke-Cmd "New-Item -ItemType Directory -Path '$CommandsTargetDir' -Force | Out-Null" "创建 Commands 目录"

    # 安装 Agents
    $AgentsSrcDir = Join-Path $ClaudeSrc "agents\aw-kernel"
    if (Test-Path $AgentsSrcDir) {
        Write-Info "安装 Agents..."
        $AgentCount = 0

        Get-ChildItem -Path $AgentsSrcDir -Filter "*.md" | ForEach-Object {
            $BaseName = $_.Name

            # 跳过非 Agent 文件
            if ($BaseName -eq "CLAUDE.md" -or $BaseName -eq "TOOLCHAIN.md" -or $BaseName -eq "RECHECK-REPORT.md") {
                return
            }

            $Target = Join-Path $AgentsTargetDir $BaseName

            if ((Test-Path $Target) -and (-not $Force)) {
                Write-Warning "跳过已存在的 Agent: $BaseName"
            } else {
                Invoke-Cmd "Copy-Item -Path '$($_.FullName)' -Destination '$Target' -Force" "安装 Agent: $BaseName"
                Write-Success "安装 Agent: $BaseName"
                $AgentCount++
            }
        }

        Write-Info "已安装 $AgentCount 个 Agents"
    }

    # 安装 Skills
    $SkillsSrcDir = Join-Path $ClaudeSrc "skills\aw-kernel"
    if (Test-Path $SkillsSrcDir) {
        Write-Info "安装 Skills..."
        $SkillCount = 0

        Get-ChildItem -Path $SkillsSrcDir -Directory | ForEach-Object {
            $SkillName = $_.Name
            $TargetDir = Join-Path $SkillsTargetDir $SkillName

            if ((Test-Path $TargetDir) -and (-not $Force)) {
                Write-Warning "跳过已存在的 Skill: $SkillName"
            } else {
                Invoke-Cmd "New-Item -ItemType Directory -Path '$TargetDir' -Force | Out-Null" "创建 Skill 目录"
                Invoke-Cmd "Copy-Item -Path '$($_.FullName)\*' -Destination '$TargetDir\' -Recurse -Force" "复制 Skill 内容"
                Write-Success "安装 Skill: $SkillName"
                $SkillCount++
            }
        }

        Write-Info "已安装 $SkillCount 个 Skills"
    }

    # 安装 Commands（如果存在）
    $CommandsSrcDir = Join-Path $ClaudeSrc "commands"
    if (Test-Path $CommandsSrcDir) {
        Write-Info "安装 Commands..."
        Invoke-Cmd "Copy-Item -Path '$CommandsSrcDir\*' -Destination '$CommandsTargetDir\' -Recurse -Force" "复制 Commands"
    }

    # 复制文档文件
    Write-Info "复制文档文件..."
    $ClaudeMd = Join-Path $AgentsSrcDir "CLAUDE.md"
    if (Test-Path $ClaudeMd) {
        Invoke-Cmd "Copy-Item -Path '$ClaudeMd' -Destination '$AgentsTargetDir\' -Force" "复制 CLAUDE.md"
    }

    $ToolchainMd = Join-Path $AgentsSrcDir "TOOLCHAIN.md"
    if (Test-Path $ToolchainMd) {
        Invoke-Cmd "Copy-Item -Path '$ToolchainMd' -Destination '$AgentsTargetDir\' -Force" "复制 TOOLCHAIN.md"
    }

    # 创建安装标记文件
    $MarkerFile = Join-Path $AgentsTargetDir ".installed"
    $MarkerContent = @"
# 安装信息
namespace: $Namespace
installed_at: $(Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ" -AsUTC)
installed_by: $env:USERNAME
source_repo: $RepoRoot
version: 1.0.0
"@

    if (-not $DryRun) {
        $MarkerContent | Out-File -FilePath $MarkerFile -Encoding UTF8
    }

    Write-Success "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Success "安装完成喵～ o(*￣︶￣*)o"
    Write-Success "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Info ""
    Write-Info "已安装内容位于："
    Write-Info "  Agents:   $AgentsTargetDir"
    Write-Info "  Skills:   $SkillsTargetDir"
    Write-Info "  Commands: $CommandsTargetDir"
    Write-Info ""
    Write-Info "如需卸载，请运行："
    Write-Info "  powershell -ExecutionPolicy Bypass -File install-global.ps1 -Uninstall -Namespace $Namespace"
}

# 主逻辑
if ($Help) {
    Show-Help
    exit 0
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
Write-Host "Claude Code 全局安装脚本 ฅ'ω'ฅ" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
Write-Host ""

if ($Uninstall) {
    Uninstall-Claude
} else {
    Install-Claude
}

exit 0
