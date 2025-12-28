#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
FORCE=0
DRY_RUN=0
NO_PROFILE=0
NO_CLAUDE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --no-profile) NO_PROFILE=1 ;;
    --no-claude) NO_CLAUDE=1 ;;
    --codex-home) CODEX_HOME="$2"; shift ;;
    --claude-home) CLAUDE_HOME="$2"; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
  shift
done

if [[ "${CODEX_HOME}" != /* ]]; then
  if [[ "${CODEX_HOME}" == "~" || "${CODEX_HOME}" == "~/"* ]]; then
    CODEX_HOME="${HOME}${CODEX_HOME#\~}"
  else
    CODEX_HOME="$(pwd)/${CODEX_HOME}"
  fi
fi

if [[ "${CLAUDE_HOME}" != /* ]]; then
  if [[ "${CLAUDE_HOME}" == "~" || "${CLAUDE_HOME}" == "~/"* ]]; then
    CLAUDE_HOME="${HOME}${CLAUDE_HOME#\~}"
  else
    CLAUDE_HOME="$(pwd)/${CLAUDE_HOME}"
  fi
fi

SKILLS_DIR="${CODEX_HOME}/skills"
TARGETS=(feature-shipper feedback-logger)
PROFILE_PATH="${HOME}/.bashrc"
MARKER_BEGIN="# codex autoworkflow aliases (begin)"
MARKER_END="# codex autoworkflow aliases (end)"
LEGACY_MARKER="# codex autoworkflow aliases"

log() { echo "[uninstall-global] $*"; }
[[ "${DRY_RUN}" == "1" ]] && log "Dry-run mode (no files will be removed)"

for name in "${TARGETS[@]}"; do
  path="${SKILLS_DIR}/${name}"
  if [[ -e "${path}" ]]; then
    if [[ "${DRY_RUN}" == "1" ]]; then
      log "Would remove ${path}"
      if [[ -d "${path}" ]]; then
        while IFS= read -r -d '' p; do
          log "Would remove ${p}"
        done < <(find "${path}" -print0)
      fi
    else
      if [[ "${FORCE}" == "1" ]]; then
        rm -rf "${path}"
      else
        rm -rI "${path}"
      fi
      log "Removed ${path}"
    fi
  else
    log "Skip missing ${path}"
  fi
done

if [[ "${NO_CLAUDE}" != "1" ]]; then
  CLAUDE_MANIFEST="${CLAUDE_HOME}/.autoworkflow-installed.txt"
  if [[ -f "${CLAUDE_MANIFEST}" ]]; then
    log "Claude manifest: ${CLAUDE_MANIFEST}"
    while IFS= read -r p; do
      [[ -z "${p}" ]] && continue
      case "${p}" in
        "${CLAUDE_HOME}"/*) ;;
        *)
          log "Skip unexpected path (outside CLAUDE_HOME): ${p}"
          continue
          ;;
      esac
      if [[ "${DRY_RUN}" == "1" ]]; then
        log "Would remove ${p}"
      else
        rm -f "${p}" 2>/dev/null || true
      fi
    done < "${CLAUDE_MANIFEST}"

    if [[ "${DRY_RUN}" == "1" ]]; then
      log "Would remove ${CLAUDE_MANIFEST}"
    else
      rm -f "${CLAUDE_MANIFEST}" 2>/dev/null || true
      # prune empty directories under CLAUDE_HOME/agents, CLAUDE_HOME/skills, CLAUDE_HOME/commands
      if [[ -d "${CLAUDE_HOME}/agents" ]]; then
        find "${CLAUDE_HOME}/agents" -type d -empty -delete 2>/dev/null || true
      fi
      if [[ -d "${CLAUDE_HOME}/skills" ]]; then
        find "${CLAUDE_HOME}/skills" -type d -empty -delete 2>/dev/null || true
      fi
      if [[ -d "${CLAUDE_HOME}/commands" ]]; then
        find "${CLAUDE_HOME}/commands" -type d -empty -delete 2>/dev/null || true
      fi
      log "Removed Claude assets listed in manifest"
    fi
  else
    log "Claude manifest not found (skip): ${CLAUDE_MANIFEST}"
  fi
fi

if [[ "${NO_PROFILE}" != "1" && -f "${PROFILE_PATH}" ]]; then
  if grep -q "${MARKER_BEGIN}" "${PROFILE_PATH}"; then
    if [[ "${DRY_RUN}" == "1" ]]; then
      log "Would remove alias block from ${PROFILE_PATH}"
    else
      awk -v begin="${MARKER_BEGIN}" -v end="${MARKER_END}" '
        BEGIN{skip=0}
        index($0, begin){skip=1; next}
        skip==1 && index($0, end){skip=0; next}
        skip==0 {print}
      ' "${PROFILE_PATH}" > "${PROFILE_PATH}.tmp"
      mv "${PROFILE_PATH}.tmp" "${PROFILE_PATH}"
      log "Removed alias block from ${PROFILE_PATH} (restart shell to生效)"
    fi
  elif grep -q "${LEGACY_MARKER}" "${PROFILE_PATH}"; then
    if [[ "${DRY_RUN}" == "1" ]]; then
      log "Would remove legacy alias block from ${PROFILE_PATH}"
    else
      awk -v marker="${LEGACY_MARKER}" '
        BEGIN{skip=0}
        index($0, marker){skip=1; next}
        skip==0 {print}
      ' "${PROFILE_PATH}" > "${PROFILE_PATH}.tmp"
      mv "${PROFILE_PATH}.tmp" "${PROFILE_PATH}"
      log "Removed legacy alias block from ${PROFILE_PATH} (restart shell to生效)"
    fi
  else
    log "No alias marker in ${PROFILE_PATH}"
  fi
elif [[ "${NO_PROFILE}" != "1" ]]; then
  log "Profile not found: ${PROFILE_PATH} (skip)"
fi

log "Done."
