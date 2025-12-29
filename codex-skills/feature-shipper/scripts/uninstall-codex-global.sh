#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
FORCE=0
DRY_RUN=0
NO_PROFILE=0
PURGE=0

usage() {
  cat <<'EOF'
Usage: uninstall-codex-global.sh [options]

Uninstalls Codex skills installed by this repo and removes aw-* helpers from shell profiles.

Options:
  --codex-home <path>  Override CODEX_HOME
  --force              Remove without interactive prompts
  --dry-run            Print actions without removing
  --no-profile         Do not modify ~/.bashrc or ~/.zshrc
  --purge              Also remove empty parent dirs if possible
  -h, --help           Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --no-profile) NO_PROFILE=1 ;;
    --purge) PURGE=1 ;;
    --codex-home) CODEX_HOME="$2"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
  shift
done

resolve_path() {
  local p="$1"
  if [[ "${p}" != /* ]]; then
    if [[ "${p}" == "~" || "${p}" == "~/"* ]]; then
      echo "${HOME}${p#\~}"
    else
      echo "$(pwd)/${p}"
    fi
  else
    echo "${p}"
  fi
}

CODEX_HOME="$(resolve_path "${CODEX_HOME}")"

SKILLS_DIR="${CODEX_HOME}/skills"
TARGETS=(feature-shipper feedback-logger)
CODEX_MANIFEST="${CODEX_HOME}/.autoworkflow-codex-installed.txt"
MARKER_BEGIN="# codex autoworkflow aliases (begin)"
MARKER_END="# codex autoworkflow aliases (end)"
LEGACY_MARKER="# codex autoworkflow aliases"

log() { echo "[uninstall-codex-global] $*"; }
[[ "${DRY_RUN}" == "1" ]] && log "Dry-run mode (no files will be removed)"

if [[ -f "${CODEX_MANIFEST}" ]]; then
  log "Codex manifest: ${CODEX_MANIFEST}"
  while IFS= read -r p; do
    [[ -z "${p}" ]] && continue
    case "${p}" in
      "${CODEX_HOME}"/*) ;;
      *)
        log "Skip unexpected path (outside CODEX_HOME): ${p}"
        continue
        ;;
    esac
    if [[ "${DRY_RUN}" == "1" ]]; then
      log "Would remove ${p}"
    else
      rm -f "${p}" 2>/dev/null || { [[ "${FORCE}" == "1" ]] && true || false; }
    fi
  done < "${CODEX_MANIFEST}"
  if [[ "${DRY_RUN}" == "1" ]]; then
    log "Would remove ${CODEX_MANIFEST}"
  else
    rm -f "${CODEX_MANIFEST}" 2>/dev/null || true
    if [[ -d "${SKILLS_DIR}" ]]; then
      find "${SKILLS_DIR}" -type d -empty -delete 2>/dev/null || true
    fi
    log "Removed Codex files listed in manifest"
  fi
else
  log "Codex manifest not found; falling back to directory removal for known skills."
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
fi

remove_alias_block() {
  local profile_path="$1"
  [[ -f "${profile_path}" ]] || return 0
  if grep -q "${MARKER_BEGIN}" "${profile_path}"; then
    if [[ "${DRY_RUN}" == "1" ]]; then
      log "Would remove alias block from ${profile_path}"
      return 0
    fi
    awk -v begin="${MARKER_BEGIN}" -v end="${MARKER_END}" '
      BEGIN{skip=0}
      index($0, begin){skip=1; next}
      skip==1 && index($0, end){skip=0; next}
      skip==0 {print}
    ' "${profile_path}" > "${profile_path}.tmp"
    mv "${profile_path}.tmp" "${profile_path}"
    log "Removed alias block from ${profile_path} (restart shell to load)"
    return 0
  fi
  if grep -q "${LEGACY_MARKER}" "${profile_path}"; then
    if [[ "${DRY_RUN}" == "1" ]]; then
      log "Would remove legacy alias block from ${profile_path}"
      return 0
    fi
    awk -v marker="${LEGACY_MARKER}" '
      BEGIN{skip=0}
      index($0, marker){skip=1; next}
      skip==0 {print}
    ' "${profile_path}" > "${profile_path}.tmp"
    mv "${profile_path}.tmp" "${profile_path}"
    log "Removed legacy alias block from ${profile_path} (restart shell to load)"
  fi
}

if [[ "${NO_PROFILE}" != "1" ]]; then
  remove_alias_block "${HOME}/.bashrc"
  remove_alias_block "${HOME}/.zshrc"
fi

if [[ "${PURGE}" == "1" ]]; then
  for name in "${TARGETS[@]}"; do
    path="${SKILLS_DIR}/${name}"
    [[ -e "${path}" ]] || continue
    if [[ "${DRY_RUN}" == "1" ]]; then
      log "Would purge ${path}"
    else
      if [[ "${FORCE}" == "1" ]]; then
        rm -rf "${path}"
      else
        rm -rI "${path}"
      fi
      log "Purged ${path}"
    fi
  done
  if [[ "${DRY_RUN}" != "1" ]]; then
    if [[ -d "${SKILLS_DIR}" ]]; then
      find "${SKILLS_DIR}" -type d -empty -delete 2>/dev/null || true
    fi
    if [[ -d "${CODEX_HOME}" ]]; then
      find "${CODEX_HOME}" -maxdepth 2 -type d -empty -delete 2>/dev/null || true
    fi
  fi
fi

log "Done."
