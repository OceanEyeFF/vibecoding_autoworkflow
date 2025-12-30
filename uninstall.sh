#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE="global"   # global | local
TARGET="both"   # both | codex | claude
FORCE=0
YES=0
DRY_RUN=0
NO_PROFILE=0
PURGE=0
REMOVE_EXCLUDE=0
CODEX_HOME_ARG=""
CLAUDE_HOME_ARG=""

usage() {
  cat <<'EOF'
Usage: uninstall.sh [options]

Unified uninstaller entrypoint for this repo.

Modes:
  --global               Uninstall from CODEX_HOME / CLAUDE_HOME (default)
  --local                Clean this repo only (.autoworkflow/ and/or .claude/)

Targets:
  --both                 Uninstall Codex + Claude (default)
  --codex                Uninstall Codex only
  --claude               Uninstall Claude only

Common options:
  --force                Remove without interactive prompts (also implies --yes in --local)
  --dry-run              Print actions without removing
  --purge                Also remove empty parent dirs where possible

Global-only options:
  --no-profile            Do not modify ~/.bashrc or ~/.zshrc
  --codex-home <path>     Override CODEX_HOME (default: ~/.codex)
  --claude-home <path>    Override CLAUDE_HOME (default: ~/.claude)

Local-only options:
  --yes                   Skip confirmation for .autoworkflow removal
  --remove-exclude         Also remove .autoworkflow entries from .git/info/exclude

Examples:
  bash uninstall.sh --global --both --purge
  bash uninstall.sh --local --both --force
EOF
}

log() { echo "[uninstall] $*"; }

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
    --yes) YES=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --no-profile) NO_PROFILE=1 ;;
    --purge) PURGE=1 ;;
    --remove-exclude) REMOVE_EXCLUDE=1 ;;
    --codex-home) CODEX_HOME_ARG="$2"; shift ;;
    --claude-home) CLAUDE_HOME_ARG="$2"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) log "Unknown arg: $1"; usage; exit 1 ;;
  esac
  shift
done

CODEX_UNINSTALL="${ROOT}/CodeX/codex-skills/feature-shipper/scripts/uninstall-codex-global.sh"
CLAUDE_UNINSTALL="${ROOT}/CodeX/codex-skills/feature-shipper/scripts/uninstall-claude-global.sh"
AW="${ROOT}/CodeX/codex-skills/feature-shipper/scripts/autoworkflow.py"

if [[ "${FORCE}" == "1" ]]; then
  YES=1
fi

if [[ "${MODE}" == "global" ]]; then
  if [[ "${TARGET}" == "both" || "${TARGET}" == "codex" ]]; then
    args=()
    [[ "${FORCE}" == "1" ]] && args+=(--force)
    [[ "${DRY_RUN}" == "1" ]] && args+=(--dry-run)
    [[ "${NO_PROFILE}" == "1" ]] && args+=(--no-profile)
    [[ "${PURGE}" == "1" ]] && args+=(--purge)
    [[ -n "${CODEX_HOME_ARG}" ]] && args+=(--codex-home "${CODEX_HOME_ARG}")
    bash "${CODEX_UNINSTALL}" "${args[@]}"
  fi
  if [[ "${TARGET}" == "both" || "${TARGET}" == "claude" ]]; then
    args=()
    [[ "${FORCE}" == "1" ]] && args+=(--force)
    [[ "${DRY_RUN}" == "1" ]] && args+=(--dry-run)
    [[ "${PURGE}" == "1" ]] && args+=(--purge)
    [[ -n "${CLAUDE_HOME_ARG}" ]] && args+=(--claude-home "${CLAUDE_HOME_ARG}")
    bash "${CLAUDE_UNINSTALL}" "${args[@]}"
  fi
  exit 0
fi

# local mode
if [[ -n "${CODEX_HOME_ARG}" || -n "${CLAUDE_HOME_ARG}" || "${NO_PROFILE}" == "1" || "${PURGE}" == "1" ]]; then
  log "Note: --codex-home/--claude-home/--no-profile/--purge are ignored in --local mode."
fi

if [[ "${TARGET}" == "both" || "${TARGET}" == "codex" ]]; then
  cmd=("${PYTHON_BIN}" "${AW}" --root "${ROOT}" uninstall)
  [[ "${YES}" == "1" ]] && cmd+=(--yes)
  [[ "${REMOVE_EXCLUDE}" == "1" ]] && cmd+=(--remove-exclude)
  if [[ "${DRY_RUN}" == "1" ]]; then
    log "Would run: ${cmd[*]}"
  else
    "${cmd[@]}"
  fi
fi

if [[ "${TARGET}" == "both" || "${TARGET}" == "claude" ]]; then
  args=(--claude-home "${ROOT}/.claude" --purge)
  [[ "${FORCE}" == "1" ]] && args+=(--force)
  [[ "${DRY_RUN}" == "1" ]] && args+=(--dry-run)
  bash "${CLAUDE_UNINSTALL}" "${args[@]}"
fi

