#!/usr/bin/env bash
# Claude Code Autoworkflow Wrapper (Linux/WSL/macOS)
# Usage: bash cc-aw.sh <command> [args]

set -euo pipefail

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="${TOOL_DIR}/claude_autoworkflow.py"

# Check script exists
if [[ ! -f "${SCRIPT}" ]]; then
    echo "Error: Script not found at ${SCRIPT}" >&2
    exit 1
fi

# Detect Python command
PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
    if command -v python3 &>/dev/null; then
        PYTHON_BIN="python3"
    elif command -v python &>/dev/null; then
        PYTHON_BIN="python"
    else
        echo "Error: Python not found. Please ensure Python is installed and in PATH." >&2
        exit 1
    fi
fi

# Execute script
"${PYTHON_BIN}" "${SCRIPT}" "$@"
