#!/usr/bin/env bash
set -euo pipefail

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
FORCE=0
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: install-claude-global.sh [options]

Installs Claude Code agents/skills/commands to $CLAUDE_HOME.

Options:
  --claude-home <path>  Override CLAUDE_HOME
  --force               Overwrite existing files under $CLAUDE_HOME
  --dry-run             Print actions without writing
  -h, --help            Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FEATURE_SHIPPER_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILLS_ROOT="$(cd "${FEATURE_SHIPPER_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SKILLS_ROOT}/../.." && pwd)"

log() { echo "[install-claude-global] $*"; }
log "Source claude: ${REPO_ROOT}/Claude"
log "Target claude: ${CLAUDE_HOME}"
[[ "${DRY_RUN}" == "1" ]] && log "Dry-run mode (no changes will be written)"

print_copy_plan_claude() {
  local src="$1"
  local dst="$2"
  log "Would ensure dir ${dst}"
  if [[ -d "${src}" ]]; then
    while IFS= read -r -d '' f; do
      rel="${f#${src}/}"
      out="${dst}/${rel}"
      if [[ -e "${out}" && "${FORCE}" != "1" ]]; then
        log "Would skip existing ${out}"
      elif [[ -e "${out}" && "${FORCE}" == "1" ]]; then
        log "Would overwrite ${out}"
      else
        log "Would add ${out}"
      fi
    done < <(
      find "${src}" \
        -type d \( -name __pycache__ -o -name '.pytest_cache' -o -name '.mypy_cache' -o -name '.ruff_cache' \) -prune -o \
        -type f ! -name '*.pyc' ! -name '*.pyo' -print0
    )
  else
    log "Skip missing ${src}"
  fi
}

copy_claude_tree() {
  local src="$1"
  local dst="$2"
  local manifest_tmp="$3"
  if [[ ! -d "${src}" ]]; then
    log "Skip missing ${src}"
    return 0
  fi
  if [[ "${DRY_RUN}" == "1" ]]; then
    print_copy_plan_claude "${src}" "${dst}"
    return 0
  fi

  mkdir -p "${dst}"
  while IFS= read -r -d '' f; do
    rel="${f#${src}/}"
    out="${dst}/${rel}"
    if [[ -e "${out}" && "${FORCE}" != "1" ]]; then
      continue
    fi
    mkdir -p "$(dirname "${out}")"
    cp "${f}" "${out}"
    echo "${out}" >> "${manifest_tmp}"
  done < <(
    find "${src}" \
      -type d \( -name __pycache__ -o -name '.pytest_cache' -o -name '.mypy_cache' -o -name '.ruff_cache' \) -prune -o \
      -type f ! -name '*.pyc' ! -name '*.pyo' -print0
  )
  return 0
}

CLAUDE_MANIFEST="${CLAUDE_HOME}/.autoworkflow-claude-installed.txt"
CLAUDE_MANIFEST_LEGACY="${CLAUDE_HOME}/.autoworkflow-installed.txt"
if [[ "${DRY_RUN}" == "1" ]]; then
  log "Would write manifest ${CLAUDE_MANIFEST}"
  log "Would also write legacy manifest ${CLAUDE_MANIFEST_LEGACY}"
  print_copy_plan_claude "${REPO_ROOT}/Claude/agents" "${CLAUDE_HOME}/agents"
  print_copy_plan_claude "${REPO_ROOT}/Claude/skills" "${CLAUDE_HOME}/skills"
  print_copy_plan_claude "${REPO_ROOT}/Claude/commands" "${CLAUDE_HOME}/commands"
else
  mkdir -p "${CLAUDE_HOME}"
  MANIFEST_TMP="$(mktemp)"
  : > "${MANIFEST_TMP}"
  copy_claude_tree "${REPO_ROOT}/Claude/agents" "${CLAUDE_HOME}/agents" "${MANIFEST_TMP}"
  copy_claude_tree "${REPO_ROOT}/Claude/skills" "${CLAUDE_HOME}/skills" "${MANIFEST_TMP}"
  copy_claude_tree "${REPO_ROOT}/Claude/commands" "${CLAUDE_HOME}/commands" "${MANIFEST_TMP}"
  if [[ -s "${MANIFEST_TMP}" ]]; then
    if [[ -f "${CLAUDE_MANIFEST}" ]]; then
      cat "${CLAUDE_MANIFEST}" >> "${MANIFEST_TMP}" || true
    fi
    if [[ -f "${CLAUDE_MANIFEST_LEGACY}" ]]; then
      cat "${CLAUDE_MANIFEST_LEGACY}" >> "${MANIFEST_TMP}" || true
    fi
    sort -u "${MANIFEST_TMP}" > "${CLAUDE_MANIFEST}"
    cp "${CLAUDE_MANIFEST}" "${CLAUDE_MANIFEST_LEGACY}"
    rm -f "${MANIFEST_TMP}"
    log "Installed Claude assets (manifest: ${CLAUDE_MANIFEST})"
  else
    rm -f "${MANIFEST_TMP}"
    log "No Claude files installed (nothing to manifest)"
  fi
fi

log "Done."
