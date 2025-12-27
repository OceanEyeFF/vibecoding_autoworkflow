#!/usr/bin/env bash
set -euo pipefail

ROOT="."
BRANCH_NAME=""
ALLOW_UNREVIEWED=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root) ROOT="$2"; shift ;;
    --branch|--branch-name) BRANCH_NAME="$2"; shift ;;
    --allow-unreviewed) ALLOW_UNREVIEWED=1 ;;
    --dry-run) DRY_RUN=1 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
  shift
done

ROOT_PATH="$(cd "$ROOT" && pwd)"
TOOL=""
for cand in \
  "$ROOT_PATH/codex-skills/feature-shipper/scripts/autoworkflow.py" \
  "${CODEX_HOME:-}/skills/feature-shipper/scripts/autoworkflow.py" \
  "$ROOT_PATH/.autoworkflow/tools/autoworkflow.py"; do
  if [[ -n "$cand" && -f "$cand" ]]; then
    TOOL="$cand"
    break
  fi
done
if [[ -z "$TOOL" ]]; then
  echo "Missing autoworkflow.py. Expected one of:" >&2
  echo "  - $ROOT_PATH/.autoworkflow/tools/autoworkflow.py" >&2
  echo "  - ${CODEX_HOME:-\$CODEX_HOME}/skills/feature-shipper/scripts/autoworkflow.py" >&2
  echo "  - $ROOT_PATH/codex-skills/feature-shipper/scripts/autoworkflow.py" >&2
  exit 2
fi

run_step() {
  local name="$1"; shift
  echo "==> $name"
  echo "$@"
  [[ "$DRY_RUN" == "1" ]] && return 0
  "$@"
}

run_step "init" python "$TOOL" --root "$ROOT_PATH" init
BRANCH_ARGS=()
[[ -n "$BRANCH_NAME" ]] && BRANCH_ARGS=(--name "$BRANCH_NAME")
run_step "git branch start" python "$TOOL" --root "$ROOT_PATH" git branch start "${BRANCH_ARGS[@]}"
run_step "auto-gate" python "$TOOL" --root "$ROOT_PATH" auto-gate
run_step "plan gen" python "$TOOL" --root "$ROOT_PATH" plan gen
run_step "plan review" python "$TOOL" --root "$ROOT_PATH" plan review
ALLOW=()
[[ "$ALLOW_UNREVIEWED" == "1" ]] && ALLOW=(--allow-unreviewed)
run_step "gate" python "$TOOL" --root "$ROOT_PATH" gate "${ALLOW[@]}"

echo "Done."
