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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FEATURE_SHIPPER_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILLS_ROOT="$(cd "${FEATURE_SHIPPER_DIR}/.." && pwd)"
TARGET_SKILLS="${CODEX_HOME}/skills"

log() { echo "[install-global] $*"; }
log "Source skills: ${SKILLS_ROOT}"
log "Target skills: ${TARGET_SKILLS}"
[[ "${DRY_RUN}" == "1" ]] && log "Dry-run mode (no changes will be written)"

copy_skill() {
  local name="$1"
  local src="${SKILLS_ROOT}/${name}"
  local dst="${TARGET_SKILLS}/${name}"
  if [[ "${DRY_RUN}" == "1" ]]; then
    log "Would copy ${src} -> ${dst}"
    return
  fi
  mkdir -p "${TARGET_SKILLS}"
  if [[ "${FORCE}" == "1" && -e "${dst}" ]]; then
    rm -rf "${dst}"
  fi
  cp -R "${src}" "${dst}"
  log "Installed ${name}"
}

mapfile -t skill_dirs < <(find "${SKILLS_ROOT}" -maxdepth 1 -mindepth 1 -type d ! -name '.*' -exec basename {} \; | sort || true)
if [[ "${#skill_dirs[@]}" -eq 0 ]]; then
  log "No skill directories found under ${SKILLS_ROOT}"
  exit 1
fi

for name in "${skill_dirs[@]}"; do
  copy_skill "${name}"
done

if [[ "${NO_PROFILE}" != "1" ]]; then
  PROFILE_PATH="${HOME}/.bashrc"
  MARKER="# codex autoworkflow aliases"
  ALIASES="${MARKER}
aw-init() { local root=\"${1:-$(pwd)}\"; python \"${CODEX_HOME}/skills/feature-shipper/scripts/autoworkflow.py\" --root \"${root}\" init; }
aw-auto() { local root=\"${1:-$(pwd)}\"; python \"${CODEX_HOME}/skills/feature-shipper/scripts/autoworkflow.py\" --root \"${root}\" auto-gate; }
aw-gate() { local root=\"${1:-$(pwd)}\"; python \"${CODEX_HOME}/skills/feature-shipper/scripts/autoworkflow.py\" --root \"${root}\" gate; }
aw-doctor() { local root=\"${1:-$(pwd)}\"; python \"${CODEX_HOME}/skills/feature-shipper/scripts/autoworkflow.py\" --root \"${root}\" doctor --write --update-state; }
"
  if [[ "${DRY_RUN}" == "1" ]]; then
    log "Would append aliases to ${PROFILE_PATH}"
  else
    touch "${PROFILE_PATH}"
    if ! grep -q "${MARKER}" "${PROFILE_PATH}"; then
      printf "\n%s\n" "${ALIASES}" >> "${PROFILE_PATH}"
      log "Appended autoworkflow aliases to ${PROFILE_PATH} (restart shell to load)"
    else
      log "Profile already contains aliases marker, skipping append"
    }
  fi
fi

log "Done."
