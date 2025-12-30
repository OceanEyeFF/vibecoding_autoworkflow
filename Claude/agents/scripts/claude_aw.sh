#!/usr/bin/env bash
set -euo pipefail

ROOT="."
BRANCH_NAME=""
BASE="develop"
BOOTSTRAP_BASE_FROM=""
COMMIT=0
PUSH=0
PR=0
DRAFT=0
ALLOW_UNREVIEWED=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root) ROOT="$2"; shift ;;
    --branch|--branch-name) BRANCH_NAME="$2"; shift ;;
    --base) BASE="$2"; shift ;;
    --bootstrap-base-from) BOOTSTRAP_BASE_FROM="$2"; shift ;;
    --commit) COMMIT=1 ;;
    --push) PUSH=1 ;;
    --pr) PR=1 ;;
    --draft) DRAFT=1 ;;
    --allow-unreviewed) ALLOW_UNREVIEWED=1 ;;
    --dry-run) DRY_RUN=1 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
  shift
done

ROOT_PATH="$(cd "$ROOT" && pwd)"
CODEX_HOME_RESOLVED="${CODEX_HOME:-$HOME/.codex}"
if [[ "${CODEX_HOME_RESOLVED}" == "~" || "${CODEX_HOME_RESOLVED}" == "~/"* ]]; then
  CODEX_HOME_RESOLVED="${HOME}${CODEX_HOME_RESOLVED#\~}"
fi
TOOL=""
for cand in \
  "$ROOT_PATH/CodeX/codex-skills/feature-shipper/scripts/autoworkflow.py" \
  "${CODEX_HOME_RESOLVED}/skills/feature-shipper/scripts/autoworkflow.py" \
  "$ROOT_PATH/.autoworkflow/tools/autoworkflow.py"; do
  if [[ -n "$cand" && -f "$cand" ]]; then
    TOOL="$cand"
    break
  fi
done
if [[ -z "$TOOL" ]]; then
  echo "Missing autoworkflow.py. Expected one of:" >&2
  echo "  - $ROOT_PATH/.autoworkflow/tools/autoworkflow.py" >&2
  echo "  - ${CODEX_HOME_RESOLVED}/skills/feature-shipper/scripts/autoworkflow.py" >&2
  echo "  - $ROOT_PATH/CodeX/codex-skills/feature-shipper/scripts/autoworkflow.py" >&2
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

if [[ "$COMMIT" == "1" ]]; then
  run_step "git commit" python "$TOOL" --root "$ROOT_PATH" git commit --all --auto-message
fi

if [[ "$PR" == "1" ]]; then
  PR_ARGS=(--base "$BASE" --push -u)
  [[ "$DRAFT" == "1" ]] && PR_ARGS+=(--draft)
  [[ -n "$BOOTSTRAP_BASE_FROM" ]] && PR_ARGS+=(--bootstrap-base-from "$BOOTSTRAP_BASE_FROM")
  run_step "git pr create" python "$TOOL" --root "$ROOT_PATH" git pr create "${PR_ARGS[@]}"
elif [[ "$PUSH" == "1" ]]; then
  run_step "git push" python "$TOOL" --root "$ROOT_PATH" git push -u
fi

echo "Done."
