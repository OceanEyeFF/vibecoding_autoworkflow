#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE="global"   # global | local
TARGET="both"   # both | codex | claude
FORCE=0
DRY_RUN=0
NO_PROFILE=0
CODEX_HOME_ARG=""
CLAUDE_HOME_ARG=""

usage() {
  cat <<'EOF'
Usage: install.sh [options]

Unified installer entrypoint for this repo.

Modes:
  --global              Install to CODEX_HOME / CLAUDE_HOME (default)
  --local               Install into this repo only (.autoworkflow/ and/or .claude/)

Targets:
  --both                Install Codex + Claude (default)
  --codex               Install Codex only
  --claude              Install Claude only

Common options:
  --force               Overwrite existing files
  --dry-run             Print actions without writing

Global-only options:
  --no-profile           Do not modify ~/.bashrc or ~/.zshrc (Codex aliases)
  --codex-home <path>    Override CODEX_HOME (default: ~/.codex)
  --claude-home <path>   Override CLAUDE_HOME (default: ~/.claude)

Examples:
  bash install.sh --global --both
  bash install.sh --global --codex --no-profile
  bash install.sh --local --both --force
EOF
}

log() { echo "[install] $*"; }

PYTHON_BIN="python"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  log "Missing python/python3 in PATH."
  exit 127
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --global) MODE="global" ;;
    --local) MODE="local" ;;
    --both) TARGET="both" ;;
    --codex) TARGET="codex" ;;
    --claude) TARGET="claude" ;;
    --force) FORCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --no-profile) NO_PROFILE=1 ;;
    --codex-home) CODEX_HOME_ARG="$2"; shift ;;
    --claude-home) CLAUDE_HOME_ARG="$2"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) log "Unknown arg: $1"; usage; exit 1 ;;
  esac
  shift
done

CODEX_INSTALL="${ROOT}/CodeX/codex-skills/feature-shipper/scripts/install-codex-global.sh"
CLAUDE_INSTALL="${ROOT}/CodeX/codex-skills/feature-shipper/scripts/install-claude-global.sh"
AW="${ROOT}/CodeX/codex-skills/feature-shipper/scripts/autoworkflow.py"

if [[ "${MODE}" == "global" ]]; then
  if [[ "${TARGET}" == "both" || "${TARGET}" == "codex" ]]; then
    args=()
    [[ "${FORCE}" == "1" ]] && args+=(--force)
    [[ "${DRY_RUN}" == "1" ]] && args+=(--dry-run)
    [[ "${NO_PROFILE}" == "1" ]] && args+=(--no-profile)
    [[ -n "${CODEX_HOME_ARG}" ]] && args+=(--codex-home "${CODEX_HOME_ARG}")
    bash "${CODEX_INSTALL}" "${args[@]}"
  fi
  if [[ "${TARGET}" == "both" || "${TARGET}" == "claude" ]]; then
    args=()
    [[ "${FORCE}" == "1" ]] && args+=(--force)
    [[ "${DRY_RUN}" == "1" ]] && args+=(--dry-run)
    [[ -n "${CLAUDE_HOME_ARG}" ]] && args+=(--claude-home "${CLAUDE_HOME_ARG}")
    bash "${CLAUDE_INSTALL}" "${args[@]}"
  fi
  exit 0
fi

# local mode
if [[ -n "${CODEX_HOME_ARG}" || -n "${CLAUDE_HOME_ARG}" || "${NO_PROFILE}" == "1" ]]; then
  log "Note: --codex-home/--claude-home/--no-profile are ignored in --local mode."
fi

if [[ "${TARGET}" == "both" || "${TARGET}" == "codex" ]]; then
  cmd=("${PYTHON_BIN}" "${AW}" --root "${ROOT}" init)
  [[ "${FORCE}" == "1" ]] && cmd+=(--force)
  if [[ "${DRY_RUN}" == "1" ]]; then
    log "Would run: ${cmd[*]}"
  else
    "${cmd[@]}"
  fi
fi

if [[ "${TARGET}" == "both" || "${TARGET}" == "claude" ]]; then
  args=(--claude-home "${ROOT}/.claude")
  [[ "${FORCE}" == "1" ]] && args+=(--force)
  [[ "${DRY_RUN}" == "1" ]] && args+=(--dry-run)
  bash "${CLAUDE_INSTALL}" "${args[@]}"
fi

