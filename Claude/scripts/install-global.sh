#!/bin/bash
# Claude Code Agents/Skills 全局安装脚本
# 用途：将 Claude/ 目录的内容安装到 ~/.claude/ 全局目录
# 作者：浮浮酱 (*^▽^*)
# 日期：2026-01-04

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CLAUDE_SRC="$REPO_ROOT/Claude"

# 目标目录
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
NAMESPACE="${NAMESPACE:-aw-kernel}"  # 命名空间，避免冲突

# 显示帮助信息
show_help() {
    cat << EOF
${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}
${GREEN}Claude Code 全局安装脚本 ฅ'ω'ฅ${NC}
${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

用途：将 Claude/ 目录的 agents/skills/commands 安装到全局

${YELLOW}用法：${NC}
  $0 [选项]

${YELLOW}选项：${NC}
  -h, --help              显示此帮助信息
  -n, --namespace NAME    指定命名空间（默认: aw-kernel）
  -f, --force             强制覆盖已存在的文件
  -d, --dry-run           预览将要执行的操作，但不实际执行
  -u, --uninstall         卸载已安装的内容

${YELLOW}环境变量：${NC}
  CLAUDE_HOME            Claude Code 全局目录（默认: ~/.claude）
  NAMESPACE              命名空间（默认: aw-kernel）

${YELLOW}示例：${NC}
  # 标准安装
  bash $0

  # 使用自定义命名空间
  bash $0 --namespace my-agents

  # 预览安装操作
  bash $0 --dry-run

  # 卸载
  bash $0 --uninstall

${YELLOW}目录结构：${NC}
  ~/.claude/agents/aw-kernel/             # Agents (AutoWorkflow Kernel)
  ~/.claude/skills/aw-kernel/             # Skills
  ~/.claude/commands/aw-kernel/           # Commands

${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}
EOF
}

# 解析命令行参数
FORCE=false
DRY_RUN=false
UNINSTALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -u|--uninstall)
            UNINSTALL=true
            shift
            ;;
        *)
            echo -e "${RED}错误：未知选项 $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 打印信息
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 执行命令（支持 dry-run）
exec_cmd() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} $1"
    else
        eval "$1"
    fi
}

# 卸载函数
uninstall() {
    info "开始卸载命名空间: ${NAMESPACE}"

    local agents_dir="$CLAUDE_HOME/agents/$NAMESPACE"
    local skills_dir="$CLAUDE_HOME/skills/$NAMESPACE"
    local commands_dir="$CLAUDE_HOME/commands/$NAMESPACE"

    if [ -d "$agents_dir" ]; then
        warning "删除 Agents: $agents_dir"
        exec_cmd "rm -rf '$agents_dir'"
    fi

    if [ -d "$skills_dir" ]; then
        warning "删除 Skills: $skills_dir"
        exec_cmd "rm -rf '$skills_dir'"
    fi

    if [ -d "$commands_dir" ]; then
        warning "删除 Commands: $commands_dir"
        exec_cmd "rm -rf '$commands_dir'"
    fi

    success "卸载完成喵～"
}

# 安装函数
install() {
    info "开始安装到全局目录: $CLAUDE_HOME"
    info "命名空间: $NAMESPACE"

    # 检查源目录
    if [ ! -d "$CLAUDE_SRC" ]; then
        error "源目录不存在: $CLAUDE_SRC"
        exit 1
    fi

    # 创建目标目录
    info "创建目标目录..."
    exec_cmd "mkdir -p '$CLAUDE_HOME/agents/$NAMESPACE'"
    exec_cmd "mkdir -p '$CLAUDE_HOME/skills/$NAMESPACE'"
    exec_cmd "mkdir -p '$CLAUDE_HOME/commands/$NAMESPACE'"

    # 安装 Agents
    if [ -d "$CLAUDE_SRC/agents/aw-kernel" ]; then
        info "安装 Agents..."
        local agent_count=0

        for agent_file in "$CLAUDE_SRC/agents/aw-kernel"/*.md; do
            if [ -f "$agent_file" ]; then
                local basename=$(basename "$agent_file")

                # 跳过非 Agent 文件
                if [[ "$basename" == "CLAUDE.md" ]] || \
                   [[ "$basename" == "TOOLCHAIN.md" ]] || \
                   [[ "$basename" == "RECHECK-REPORT.md" ]]; then
                    continue
                fi

                local target="$CLAUDE_HOME/agents/$NAMESPACE/$basename"

                if [ -f "$target" ] && [ "$FORCE" = false ]; then
                    warning "跳过已存在的 Agent: $basename"
                else
                    exec_cmd "cp '$agent_file' '$target'"
                    success "安装 Agent: $basename"
                    ((agent_count++))
                fi
            fi
        done

        info "已安装 $agent_count 个 Agents"
    fi

    # 安装 Skills
    if [ -d "$CLAUDE_SRC/skills/aw-kernel" ]; then
        info "安装 Skills..."
        local skill_count=0

        for skill_dir in "$CLAUDE_SRC/skills/aw-kernel"/*; do
            if [ -d "$skill_dir" ]; then
                local skill_name=$(basename "$skill_dir")
                local target_dir="$CLAUDE_HOME/skills/$NAMESPACE/$skill_name"

                if [ -d "$target_dir" ] && [ "$FORCE" = false ]; then
                    warning "跳过已存在的 Skill: $skill_name"
                else
                    exec_cmd "mkdir -p '$target_dir'"
                    exec_cmd "cp -r '$skill_dir'/* '$target_dir/'"
                    success "安装 Skill: $skill_name"
                    ((skill_count++))
                fi
            fi
        done

        info "已安装 $skill_count 个 Skills"
    fi

    # 安装 Commands（如果存在）
    if [ -d "$CLAUDE_SRC/commands" ]; then
        info "安装 Commands..."
        exec_cmd "cp -r '$CLAUDE_SRC/commands'/* '$CLAUDE_HOME/commands/$NAMESPACE/'"
    fi

    # 复制文档文件
    info "复制文档文件..."
    if [ -f "$CLAUDE_SRC/agents/aw-kernel/CLAUDE.md" ]; then
        exec_cmd "cp '$CLAUDE_SRC/agents/aw-kernel/CLAUDE.md' '$CLAUDE_HOME/agents/$NAMESPACE/'"
    fi
    if [ -f "$CLAUDE_SRC/agents/aw-kernel/TOOLCHAIN.md" ]; then
        exec_cmd "cp '$CLAUDE_SRC/agents/aw-kernel/TOOLCHAIN.md' '$CLAUDE_HOME/agents/$NAMESPACE/'"
    fi

    # 创建安装标记文件
    local marker_file="$CLAUDE_HOME/agents/$NAMESPACE/.installed"
    exec_cmd "cat > '$marker_file' << EOF
# 安装信息
namespace: $NAMESPACE
installed_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
installed_by: $(whoami)
source_repo: $REPO_ROOT
version: 1.0.0
EOF"

    success "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    success "安装完成喵～ o(*￣︶￣*)o"
    success "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    info ""
    info "已安装内容位于："
    info "  Agents:   $CLAUDE_HOME/agents/$NAMESPACE/"
    info "  Skills:   $CLAUDE_HOME/skills/$NAMESPACE/"
    info "  Commands: $CLAUDE_HOME/commands/$NAMESPACE/"
    info ""
    info "如需卸载，请运行："
    info "  bash $0 --uninstall --namespace $NAMESPACE"
}

# 主逻辑
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Claude Code 全局安装脚本 ฅ'ω'ฅ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$UNINSTALL" = true ]; then
    uninstall
else
    install
fi

exit 0
