#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
FORCE=0
DRY_RUN=0
NO_PROFILE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --no-profile) NO_PROFILE=1 ;;
    --codex-home) CODEX_HOME="$2"; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
  shift
done

SKILLS_DIR="${CODEX_HOME}/skills"
TARGETS=(feature-shipper feedback-logger)
PROFILE_PATH="${HOME}/.bashrc"
MARKER="# codex autoworkflow aliases"

log() { echo "[uninstall-global] $*"; }
[[ "${DRY_RUN}" == "1" ]] && log "Dry-run mode (no files will be removed)"

for name in "${TARGETS[@]}"; do
  path="${SKILLS_DIR}/${name}"
  if [[ -e "${path}" ]]; then
    if [[ "${DRY_RUN}" == "1" ]]; then
      log "Would remove ${path}"
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

if [[ "${NO_PROFILE}" != "1" && -f "${PROFILE_PATH}" ]]; then
  if grep -q "${MARKER}" "${PROFILE_PATH}"; then
    if [[ "${DRY_RUN}" == "1" ]]; then
      log "Would remove alias block from ${PROFILE_PATH}"
    else
      # remove marker block until next marker or EOF
      awk -v marker="${MARKER}" '
        BEGIN{skip=0}
        index($0, marker){skip=1; next}
        skip==1 && /^#/ {skip=0}
        skip==0 {print}
      ' "${PROFILE_PATH}" > "${PROFILE_PATH}.tmp"
      mv "${PROFILE_PATH}.tmp" "${PROFILE_PATH}"
      log "Removed alias block from ${PROFILE_PATH} (restart shell to生效)"
    fi
  else
    log "No alias marker in ${PROFILE_PATH}"
  fi
elif [[ "${NO_PROFILE}" != "1" ]]; then
  log "Profile not found: ${PROFILE_PATH} (skip)"
fi

log "Done."
