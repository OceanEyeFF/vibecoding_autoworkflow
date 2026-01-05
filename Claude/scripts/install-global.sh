#!/bin/bash
# Claude Code Agents/Skills Global Installation Script
# Purpose: Install Claude/ directory contents to ~/.claude/ global directory
# Author: AW-Kernel Team
# Date: 2026-01-04

set -e  # Exit on error

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CLAUDE_SRC="$REPO_ROOT/Claude"

# Target directory
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
NAMESPACE="${NAMESPACE:-aw-kernel}"

# Show help information
show_help() {
    cat << EOF
${BLUE}======================================================${NC}
${GREEN}Claude Code Global Installation Script${NC}
${BLUE}======================================================${NC}

Purpose: Install agents/skills/commands from Claude/ to global directory

${YELLOW}Usage:${NC}
  $0 [options]

${YELLOW}Options:${NC}
  -h, --help              Show this help message
  -n, --namespace NAME    Specify namespace (default: aw-kernel)
  -f, --force             Force overwrite existing files
  -d, --dry-run           Preview operations without executing
  -u, --uninstall         Uninstall installed content

${YELLOW}Environment Variables:${NC}
  CLAUDE_HOME            Claude Code global directory (default: ~/.claude)
  NAMESPACE              Namespace (default: aw-kernel)

${YELLOW}Examples:${NC}
  # Standard installation
  bash $0

  # Use custom namespace
  bash $0 --namespace my-agents

  # Preview installation
  bash $0 --dry-run

  # Uninstall
  bash $0 --uninstall

${YELLOW}Directory Structure:${NC}
  ~/.claude/agents/aw-kernel/             # Agents (AutoWorkflow Kernel)
  ~/.claude/skills/aw-kernel/             # Skills
  ~/.claude/commands/aw-kernel/           # Commands

${BLUE}======================================================${NC}
EOF
}

# Parse command line arguments
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
            echo -e "${RED}Error: Unknown option $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Print functions
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERR]${NC} $1"
}

# Execute command (supports dry-run)
exec_cmd() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} $1"
    else
        eval "$1"
    fi
}

# Uninstall function
uninstall() {
    info "Starting uninstall for namespace: ${NAMESPACE}"

    local agents_dir="$CLAUDE_HOME/agents/$NAMESPACE"
    local skills_dir="$CLAUDE_HOME/skills/$NAMESPACE"
    local commands_dir="$CLAUDE_HOME/commands/$NAMESPACE"

    if [ -d "$agents_dir" ]; then
        warning "Removing Agents: $agents_dir"
        exec_cmd "rm -rf '$agents_dir'"
    fi

    if [ -d "$skills_dir" ]; then
        warning "Removing Skills: $skills_dir"
        exec_cmd "rm -rf '$skills_dir'"
    fi

    if [ -d "$commands_dir" ]; then
        warning "Removing Commands: $commands_dir"
        exec_cmd "rm -rf '$commands_dir'"
    fi

    success "Uninstall completed!"
}

# Install function
install() {
    info "Starting installation to global directory: $CLAUDE_HOME"
    info "Namespace: $NAMESPACE"

    # Check source directory
    if [ ! -d "$CLAUDE_SRC" ]; then
        error "Source directory does not exist: $CLAUDE_SRC"
        exit 1
    fi

    # Create target directories
    info "Creating target directories..."
    exec_cmd "mkdir -p '$CLAUDE_HOME/agents/$NAMESPACE'"
    exec_cmd "mkdir -p '$CLAUDE_HOME/skills/$NAMESPACE'"
    exec_cmd "mkdir -p '$CLAUDE_HOME/commands/$NAMESPACE'"

    # Install Agents
    if [ -d "$CLAUDE_SRC/agents/aw-kernel" ]; then
        info "Installing Agents..."
        local agent_count=0

        for agent_file in "$CLAUDE_SRC/agents/aw-kernel"/*.md; do
            if [ -f "$agent_file" ]; then
                local basename=$(basename "$agent_file")

                # Skip non-Agent files
                if [[ "$basename" == "CLAUDE.md" ]] || \
                   [[ "$basename" == "TOOLCHAIN.md" ]] || \
                   [[ "$basename" == "RECHECK-REPORT.md" ]] || \
                   [[ "$basename" == "STANDARDS.md" ]]; then
                    continue
                fi

                local target="$CLAUDE_HOME/agents/$NAMESPACE/$basename"

                if [ -f "$target" ] && [ "$FORCE" = false ]; then
                    warning "Skipping existing Agent: $basename"
                else
                    exec_cmd "cp '$agent_file' '$target'"
                    success "Installed Agent: $basename"
                    ((agent_count++)) || true
                fi
            fi
        done

        info "Installed $agent_count Agents"
    fi

    # Install Skills
    if [ -d "$CLAUDE_SRC/skills/aw-kernel" ]; then
        info "Installing Skills..."
        local skill_count=0

        for skill_dir in "$CLAUDE_SRC/skills/aw-kernel"/*; do
            if [ -d "$skill_dir" ]; then
                local skill_name=$(basename "$skill_dir")
                local target_dir="$CLAUDE_HOME/skills/$NAMESPACE/$skill_name"

                if [ -d "$target_dir" ] && [ "$FORCE" = false ]; then
                    warning "Skipping existing Skill: $skill_name"
                else
                    exec_cmd "mkdir -p '$target_dir'"
                    exec_cmd "cp -r '$skill_dir'/* '$target_dir/'"
                    success "Installed Skill: $skill_name"
                    ((skill_count++)) || true
                fi
            fi
        done

        info "Installed $skill_count Skills"
    fi

    # Install Commands (if exists)
    if [ -d "$CLAUDE_SRC/commands" ]; then
        info "Installing Commands..."
        exec_cmd "cp -r '$CLAUDE_SRC/commands'/* '$CLAUDE_HOME/commands/$NAMESPACE/'"
    fi

    # Copy documentation files
    info "Copying documentation files..."
    if [ -f "$CLAUDE_SRC/agents/aw-kernel/CLAUDE.md" ]; then
        exec_cmd "cp '$CLAUDE_SRC/agents/aw-kernel/CLAUDE.md' '$CLAUDE_HOME/agents/$NAMESPACE/'"
    fi
    if [ -f "$CLAUDE_SRC/agents/aw-kernel/TOOLCHAIN.md" ]; then
        exec_cmd "cp '$CLAUDE_SRC/agents/aw-kernel/TOOLCHAIN.md' '$CLAUDE_HOME/agents/$NAMESPACE/'"
    fi
    if [ -f "$CLAUDE_SRC/agents/aw-kernel/STANDARDS.md" ]; then
        exec_cmd "cp '$CLAUDE_SRC/agents/aw-kernel/STANDARDS.md' '$CLAUDE_HOME/agents/$NAMESPACE/'"
    fi

    # Create installation marker file
    local marker_file="$CLAUDE_HOME/agents/$NAMESPACE/.installed"
    exec_cmd "cat > '$marker_file' << EOF
# Installation Info
namespace: $NAMESPACE
installed_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
installed_by: $(whoami)
source_repo: $REPO_ROOT
version: 1.0.0
EOF"

    success "================================================"
    success "Installation completed successfully!"
    success "================================================"
    info ""
    info "Installed content locations:"
    info "  Agents:   $CLAUDE_HOME/agents/$NAMESPACE/"
    info "  Skills:   $CLAUDE_HOME/skills/$NAMESPACE/"
    info "  Commands: $CLAUDE_HOME/commands/$NAMESPACE/"
    info ""
    info "To uninstall, run:"
    info "  bash $0 --uninstall --namespace $NAMESPACE"
}

# Main logic
echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}Claude Code Global Installation Script${NC}"
echo -e "${BLUE}======================================================${NC}"
echo ""

if [ "$UNINSTALL" = true ]; then
    uninstall
else
    install
fi

exit 0
