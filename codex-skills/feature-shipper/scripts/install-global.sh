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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FEATURE_SHIPPER_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILLS_ROOT="$(cd "${FEATURE_SHIPPER_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SKILLS_ROOT}/.." && pwd)"
TARGET_SKILLS="${CODEX_HOME}/skills"

log() { echo "[install-global] $*"; }
log "Source skills: ${SKILLS_ROOT}"
log "Target skills: ${TARGET_SKILLS}"
[[ "${DRY_RUN}" == "1" ]] && log "Dry-run mode (no changes will be written)"
if [[ "${NO_CLAUDE}" != "1" ]]; then
  log "Source claude: ${REPO_ROOT}/.claude"
  log "Target claude: ${CLAUDE_HOME}"
fi

print_copy_plan() {
  local src="$1"
  local dst="$2"
  log "Would ensure dir ${TARGET_SKILLS}"
  log "Would copy dir ${src} -> ${dst}"
  if [[ -d "${src}" ]]; then
    while IFS= read -r -d '' f; do
      rel="${f#${src}/}"
      log "Would add ${dst}/${rel}"
    done < <(
      find "${src}" \
        -type d \( -name __pycache__ -o -name '.pytest_cache' -o -name '.mypy_cache' -o -name '.ruff_cache' \) -prune -o \
        -type f ! -name '*.pyc' ! -name '*.pyo' -print0
    )
  fi
}

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

clean_caches() {
  local dst="$1"
  find "${dst}" -type d -name __pycache__ -prune -exec rm -rf '{}' + 2>/dev/null || true
  find "${dst}" -type d -name '.pytest_cache' -prune -exec rm -rf '{}' + 2>/dev/null || true
  find "${dst}" -type d -name '.mypy_cache' -prune -exec rm -rf '{}' + 2>/dev/null || true
  find "${dst}" -type d -name '.ruff_cache' -prune -exec rm -rf '{}' + 2>/dev/null || true
  find "${dst}" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete 2>/dev/null || true
}

copy_skill() {
  local name="$1"
  local src="${SKILLS_ROOT}/${name}"
  local dst="${TARGET_SKILLS}/${name}"
  if [[ "${DRY_RUN}" == "1" ]]; then
    if [[ "${FORCE}" == "1" && -e "${dst}" ]]; then
      log "Would remove (force) ${dst}"
    fi
    print_copy_plan "${src}" "${dst}"
    return
  fi
  mkdir -p "${TARGET_SKILLS}"
  if [[ "${FORCE}" == "1" && -e "${dst}" ]]; then
    rm -rf "${dst}"
  fi
  cp -R "${src}" "${dst}"
  clean_caches "${dst}"
  log "Installed ${name}"
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

mapfile -t skill_dirs < <(find "${SKILLS_ROOT}" -maxdepth 1 -mindepth 1 -type d ! -name '.*' -exec basename {} \; | sort || true)
if [[ "${#skill_dirs[@]}" -eq 0 ]]; then
  log "No skill directories found under ${SKILLS_ROOT}"
  exit 1
fi

for name in "${skill_dirs[@]}"; do
  copy_skill "${name}"
done

if [[ "${NO_CLAUDE}" != "1" ]]; then
  CLAUDE_MANIFEST="${CLAUDE_HOME}/.autoworkflow-installed.txt"
  if [[ "${DRY_RUN}" == "1" ]]; then
    log "Would write manifest ${CLAUDE_MANIFEST}"
    print_copy_plan_claude "${REPO_ROOT}/.claude/agents" "${CLAUDE_HOME}/agents"
    print_copy_plan_claude "${REPO_ROOT}/.claude/skills" "${CLAUDE_HOME}/skills"
    print_copy_plan_claude "${REPO_ROOT}/.claude/commands" "${CLAUDE_HOME}/commands"
  else
    mkdir -p "${CLAUDE_HOME}"
    MANIFEST_TMP="$(mktemp)"
    : > "${MANIFEST_TMP}"
    copy_claude_tree "${REPO_ROOT}/.claude/agents" "${CLAUDE_HOME}/agents" "${MANIFEST_TMP}"
    copy_claude_tree "${REPO_ROOT}/.claude/skills" "${CLAUDE_HOME}/skills" "${MANIFEST_TMP}"
    copy_claude_tree "${REPO_ROOT}/.claude/commands" "${CLAUDE_HOME}/commands" "${MANIFEST_TMP}"
    if [[ -s "${MANIFEST_TMP}" ]]; then
      if [[ -f "${CLAUDE_MANIFEST}" ]]; then
        cat "${CLAUDE_MANIFEST}" >> "${MANIFEST_TMP}" || true
      fi
      sort -u "${MANIFEST_TMP}" > "${CLAUDE_MANIFEST}"
      rm -f "${MANIFEST_TMP}"
      log "Installed Claude assets (manifest: ${CLAUDE_MANIFEST})"
    else
      rm -f "${MANIFEST_TMP}"
      log "No Claude files installed (nothing to manifest)"
    fi
  fi
fi

if [[ "${NO_PROFILE}" != "1" ]]; then
  PROFILE_PATH="${HOME}/.bashrc"
  MARKER_BEGIN="# codex autoworkflow aliases (begin)"
  MARKER_END="# codex autoworkflow aliases (end)"
  ALIASES="$(cat <<EOF
${MARKER_BEGIN}
aw-init() {
  local root="\$(pwd)"
  if [[ \$# -gt 0 && "\$1" != -* ]]; then
    root="\$1"
    shift
  fi
  python "${CODEX_HOME}/skills/feature-shipper/scripts/autoworkflow.py" --root "\$root" init "\$@"
}
aw-auto() {
  local root="\$(pwd)"
  if [[ \$# -gt 0 && "\$1" != -* ]]; then
    root="\$1"
    shift
  fi
  python "${CODEX_HOME}/skills/feature-shipper/scripts/autoworkflow.py" --root "\$root" auto-gate "\$@"
}
aw-gate() {
  local root="\$(pwd)"
  if [[ \$# -gt 0 && "\$1" != -* ]]; then
    root="\$1"
    shift
  fi
  python "${CODEX_HOME}/skills/feature-shipper/scripts/autoworkflow.py" --root "\$root" gate "\$@"
}
aw-doctor() {
  local root="\$(pwd)"
  if [[ \$# -gt 0 && "\$1" != -* ]]; then
    root="\$1"
    shift
  fi
  python "${CODEX_HOME}/skills/feature-shipper/scripts/autoworkflow.py" --root "\$root" doctor --write --update-state "\$@"
}
aw-uninstall() {
  local root="\$(pwd)"
  if [[ \$# -gt 0 && "\$1" != -* ]]; then
    root="\$1"
    shift
  fi
  python "${CODEX_HOME}/skills/feature-shipper/scripts/autoworkflow.py" --root "\$root" uninstall "\$@"
}
${MARKER_END}
EOF
)"
  if [[ "${DRY_RUN}" == "1" ]]; then
    log "Would append aliases to ${PROFILE_PATH}"
  else
    touch "${PROFILE_PATH}"
    if ! grep -q "${MARKER_BEGIN}" "${PROFILE_PATH}"; then
      printf "\n%s\n" "${ALIASES}" >> "${PROFILE_PATH}"
      log "Appended autoworkflow aliases to ${PROFILE_PATH} (restart shell to load)"
    else
      log "Profile already contains aliases marker, skipping append"
    fi
  fi
fi

log "Done."
