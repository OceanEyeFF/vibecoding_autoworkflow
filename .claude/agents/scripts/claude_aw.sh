#!/usr/bin/env bash
set -euo pipefail

ROOT="."
ALLOW_UNREVIEWED=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root) ROOT="$2"; shift ;;
    --allow-unreviewed) ALLOW_UNREVIEWED=1 ;;
    --dry-run) DRY_RUN=1 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
  shift
done

ROOT_PATH="$(cd "$ROOT" && pwd)"
TOOL="$ROOT_PATH/.autoworkflow/tools/autoworkflow.py"
if [[ ! -f "$TOOL" ]]; then
  TOOL="$ROOT_PATH/codex-skills/feature-shipper/scripts/autoworkflow.py"
fi

run_step() {
  local name="$1"; shift
  echo "==> $name"
  echo "$@"
  [[ "$DRY_RUN" == "1" ]] && return 0
  "$@"
}

run_step "init" python "$TOOL" --root "$ROOT_PATH" init
run_step "auto-gate" python "$TOOL" --root "$ROOT_PATH" auto-gate
run_step "plan gen" python "$TOOL" --root "$ROOT_PATH" plan gen
run_step "plan review" python "$TOOL" --root "$ROOT_PATH" plan review
ALLOW=()
[[ "$ALLOW_UNREVIEWED" == "1" ]] && ALLOW=(--allow-unreviewed)
run_step "gate (dry-run)" python "$TOOL" --root "$ROOT_PATH" gate "${ALLOW[@]}"

echo "Done."
