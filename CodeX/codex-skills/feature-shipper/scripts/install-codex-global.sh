#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
FORCE=0
DRY_RUN=0
NO_PROFILE=0

usage() {
  cat <<'EOF'
Usage: install-codex-global.sh [options]

Installs Codex skills to $CODEX_HOME/skills and (optionally) appends aw-* helpers to shell profiles.

Options:
  --codex-home <path>  Override CODEX_HOME
  --force              Overwrite existing installed skill dirs
  --dry-run            Print actions without writing
  --no-profile         Do not modify ~/.bashrc or ~/.zshrc
  -h, --help           Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --no-profile) NO_PROFILE=1 ;;
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FEATURE_SHIPPER_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILLS_ROOT="$(cd "${FEATURE_SHIPPER_DIR}/.." && pwd)"
TARGET_SKILLS="${CODEX_HOME}/skills"
CODEX_MANIFEST="${CODEX_HOME}/.autoworkflow-codex-installed.txt"

log() { echo "[install-codex-global] $*"; }
log "Source skills: ${SKILLS_ROOT}"
log "Target skills: ${TARGET_SKILLS}"
log "Codex manifest: ${CODEX_MANIFEST}"
[[ "${DRY_RUN}" == "1" ]] && log "Dry-run mode (no changes will be written)"

clean_caches() {
  local dst="$1"
  find "${dst}" -type d -name __pycache__ -prune -exec rm -rf '{}' + 2>/dev/null || true
  find "${dst}" -type d -name '.pytest_cache' -prune -exec rm -rf '{}' + 2>/dev/null || true
  find "${dst}" -type d -name '.mypy_cache' -prune -exec rm -rf '{}' + 2>/dev/null || true
  find "${dst}" -type d -name '.ruff_cache' -prune -exec rm -rf '{}' + 2>/dev/null || true
  find "${dst}" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete 2>/dev/null || true
}

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

copy_skill() {
  local name="$1"
  local src="${SKILLS_ROOT}/${name}"
  local dst="${TARGET_SKILLS}/${name}"
  if [[ -e "${dst}" && "${FORCE}" != "1" ]]; then
    log "Skip existing ${dst} (use --force to overwrite)"
    return 0
  fi
  if [[ "${DRY_RUN}" == "1" ]]; then
    [[ "${FORCE}" == "1" && -e "${dst}" ]] && log "Would remove (force) ${dst}"
    print_copy_plan "${src}" "${dst}"
    return 0
  fi
  mkdir -p "${TARGET_SKILLS}"
  if [[ "${FORCE}" == "1" && -e "${dst}" ]]; then
    rm -rf "${dst}"
  fi
  cp -R "${src}" "${dst}"
  clean_caches "${dst}"
  if [[ -n "${MANIFEST_TMP:-}" ]]; then
    find "${dst}" \
      -type d \( -name __pycache__ -o -name '.pytest_cache' -o -name '.mypy_cache' -o -name '.ruff_cache' \) -prune -o \
      -type f ! -name '*.pyc' ! -name '*.pyo' -print >> "${MANIFEST_TMP}" || true
  fi
  log "Installed ${name}"
}

if [[ "${DRY_RUN}" == "1" ]]; then
  log "Would write manifest ${CODEX_MANIFEST}"
else
  MANIFEST_TMP="$(mktemp)"
  : > "${MANIFEST_TMP}"
fi

mapfile -t skill_dirs < <(find "${SKILLS_ROOT}" -maxdepth 1 -mindepth 1 -type d ! -name '.*' -exec basename {} \; | sort || true)
if [[ "${#skill_dirs[@]}" -eq 0 ]]; then
  log "No skill directories found under ${SKILLS_ROOT}"
  exit 1
fi

for name in "${skill_dirs[@]}"; do
  copy_skill "${name}"
done

if [[ "${DRY_RUN}" != "1" ]]; then
  if [[ -s "${MANIFEST_TMP}" ]]; then
    if [[ -f "${CODEX_MANIFEST}" ]]; then
      cat "${CODEX_MANIFEST}" >> "${MANIFEST_TMP}" || true
    fi
    sort -u "${MANIFEST_TMP}" > "${CODEX_MANIFEST}"
    log "Updated manifest ${CODEX_MANIFEST}"
  else
    log "No new Codex files installed (manifest unchanged)"
  fi
  rm -f "${MANIFEST_TMP}" || true
fi

append_aliases() {
  local profile_path="$1"
  local marker_begin="# codex autoworkflow aliases (begin)"
  local marker_end="# codex autoworkflow aliases (end)"
  local aliases
  aliases="$(cat <<EOF
${marker_begin}
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
${marker_end}
EOF
)"

  if [[ "${DRY_RUN}" == "1" ]]; then
    log "Would append aliases to ${profile_path}"
    return 0
  fi

  touch "${profile_path}"
  if ! grep -q "${marker_begin}" "${profile_path}"; then
    printf "\n%s\n" "${aliases}" >> "${profile_path}"
    log "Appended autoworkflow aliases to ${profile_path} (restart shell to load)"
  else
    log "Profile already contains aliases marker, skipping append (${profile_path})"
  fi
}

if [[ "${NO_PROFILE}" != "1" ]]; then
  if [[ -f "${HOME}/.bashrc" || ! -f "${HOME}/.zshrc" ]]; then
    append_aliases "${HOME}/.bashrc"
  fi
  if [[ -f "${HOME}/.zshrc" ]]; then
    append_aliases "${HOME}/.zshrc"
  fi
fi

log "Done."
