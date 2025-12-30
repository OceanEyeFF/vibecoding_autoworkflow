#!/usr/bin/env bash
set -euo pipefail

FORCE=0
DRY_RUN=0
NO_PROFILE=0
NO_CLAUDE=0
PURGE=0
CODEX_HOME_ARG=""
CLAUDE_HOME_ARG=""

usage() {
  cat <<'EOF'
Usage: uninstall-global.sh [options]

Back-compat wrapper that uninstalls:
  - Codex skills installed by this repo
  - Claude Code agents/skills/commands installed by this repo (unless --no-claude)

Options:
  --force              Remove without interactive prompts
  --dry-run            Print actions without removing
  --no-profile         Do not modify ~/.bashrc or ~/.zshrc
  --no-claude          Skip uninstalling Claude assets
  --purge              Also remove empty parent dirs if possible
  --codex-home <path>  Override CODEX_HOME
  --claude-home <path> Override CLAUDE_HOME
  -h, --help           Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --no-profile) NO_PROFILE=1 ;;
    --no-claude) NO_CLAUDE=1 ;;
    --purge) PURGE=1 ;;
    --codex-home) CODEX_HOME_ARG="$2"; shift ;;
    --claude-home) CLAUDE_HOME_ARG="$2"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
  shift
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CODEX_ARGS=()
CLAUDE_ARGS=()
[[ "${FORCE}" == "1" ]] && CODEX_ARGS+=(--force) && CLAUDE_ARGS+=(--force)
[[ "${DRY_RUN}" == "1" ]] && CODEX_ARGS+=(--dry-run) && CLAUDE_ARGS+=(--dry-run)
[[ "${NO_PROFILE}" == "1" ]] && CODEX_ARGS+=(--no-profile)
[[ "${PURGE}" == "1" ]] && CODEX_ARGS+=(--purge) && CLAUDE_ARGS+=(--purge)
[[ -n "${CODEX_HOME_ARG}" ]] && CODEX_ARGS+=(--codex-home "${CODEX_HOME_ARG}")
[[ -n "${CLAUDE_HOME_ARG}" ]] && CLAUDE_ARGS+=(--claude-home "${CLAUDE_HOME_ARG}")

bash "${SCRIPT_DIR}/uninstall-codex-global.sh" "${CODEX_ARGS[@]}"
if [[ "${NO_CLAUDE}" != "1" ]]; then
  bash "${SCRIPT_DIR}/uninstall-claude-global.sh" "${CLAUDE_ARGS[@]}"
fi

echo "[uninstall-global] Done."
