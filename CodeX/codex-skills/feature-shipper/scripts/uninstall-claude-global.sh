#!/usr/bin/env bash
set -euo pipefail

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
DRY_RUN=0
FORCE=0
PURGE=0

usage() {
  cat <<'EOF'
Usage: uninstall-claude-global.sh [options]

Uninstalls Claude Code assets installed by this repo (agents/skills/commands) based on a manifest.

Options:
  --claude-home <path>  Override CLAUDE_HOME
  --force               Ignore missing paths when deleting
  --dry-run             Print actions without removing
  --purge               Also remove empty parent dirs if possible
  -h, --help            Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --purge) PURGE=1 ;;
    --claude-home) CLAUDE_HOME="$2"; shift ;;
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

CLAUDE_HOME="$(resolve_path "${CLAUDE_HOME}")"

CLAUDE_MANIFEST="${CLAUDE_HOME}/.autoworkflow-claude-installed.txt"
CLAUDE_MANIFEST_LEGACY="${CLAUDE_HOME}/.autoworkflow-installed.txt"

log() { echo "[uninstall-claude-global] $*"; }
[[ "${DRY_RUN}" == "1" ]] && log "Dry-run mode (no files will be removed)"

manifest_inputs=()
[[ -f "${CLAUDE_MANIFEST}" ]] && manifest_inputs+=("${CLAUDE_MANIFEST}")
[[ -f "${CLAUDE_MANIFEST_LEGACY}" ]] && manifest_inputs+=("${CLAUDE_MANIFEST_LEGACY}")

if [[ "${#manifest_inputs[@]}" -gt 0 ]]; then
  log "Claude manifest(s): ${manifest_inputs[*]}"

  if [[ "${DRY_RUN}" == "1" ]]; then
    for mf in "${manifest_inputs[@]}"; do
      log "Would read ${mf}"
    done
  else
    MANIFEST_MERGED="$(mktemp)"
    : > "${MANIFEST_MERGED}"
    for mf in "${manifest_inputs[@]}"; do
      cat "${mf}" >> "${MANIFEST_MERGED}" || true
    done
    sort -u "${MANIFEST_MERGED}" -o "${MANIFEST_MERGED}"
  fi

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
      rm -f "${p}" 2>/dev/null || { [[ "${FORCE}" == "1" ]] && true || false; }
    fi
  done < <(
    if [[ "${DRY_RUN}" == "1" ]]; then
      cat "${manifest_inputs[@]}" 2>/dev/null | sort -u
    else
      cat "${MANIFEST_MERGED}" 2>/dev/null || true
    fi
  )

  if [[ "${DRY_RUN}" == "1" ]]; then
    for mf in "${manifest_inputs[@]}"; do
      log "Would remove ${mf}"
    done
  else
    rm -f "${MANIFEST_MERGED}" 2>/dev/null || true
    rm -f "${CLAUDE_MANIFEST}" 2>/dev/null || true
    rm -f "${CLAUDE_MANIFEST_LEGACY}" 2>/dev/null || true
    for dir in "${CLAUDE_HOME}/agents" "${CLAUDE_HOME}/skills" "${CLAUDE_HOME}/commands"; do
      [[ -d "${dir}" ]] || continue
      find "${dir}" -type d -empty -delete 2>/dev/null || true
    done
    log "Removed Claude assets listed in manifest"
  fi
else
  log "Claude manifest not found (skip): ${CLAUDE_MANIFEST} / ${CLAUDE_MANIFEST_LEGACY}"
fi

if [[ "${PURGE}" == "1" && "${DRY_RUN}" != "1" ]]; then
  for dir in "${CLAUDE_HOME}/agents" "${CLAUDE_HOME}/skills" "${CLAUDE_HOME}/commands"; do
    [[ -d "${dir}" ]] || continue
    find "${dir}" -type d -empty -delete 2>/dev/null || true
    rmdir "${dir}" 2>/dev/null || true
  done
  rmdir "${CLAUDE_HOME}" 2>/dev/null || true
fi

log "Done."
