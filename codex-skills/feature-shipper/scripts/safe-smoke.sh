#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(pwd)}"
USE_CODEX="false"
KEEP_TEMP="false"

for arg in "$@"; do
  case "$arg" in
    --use-codex) USE_CODEX="true" ;;
    --keep-temp) KEEP_TEMP="true" ;;
  esac
done

ts="$(date -u +%Y%m%dT%H%M%SZ)"
temp_repo="${TMPDIR:-/tmp}/aw-safe-smoke-${ts}"

echo "[safe-smoke] Source repo: ${ROOT}"
echo "[safe-smoke] Temp repo: ${temp_repo}"

mkdir -p "${temp_repo}"

cleanup() {
  if [[ "${KEEP_TEMP}" == "true" ]]; then
    echo "[safe-smoke] Keep temp repo: ${temp_repo}"
    return 0
  fi
  echo "[safe-smoke] Cleanup: ${temp_repo}"
  rm -rf "${temp_repo}"
}
trap cleanup EXIT

if command -v rsync >/dev/null 2>&1; then
  rsync -a \
    --exclude ".git" \
    --exclude ".autoworkflow" \
    --exclude ".venv*" \
    --exclude "__pycache__" \
    --exclude ".spec-workflow" \
    --exclude ".serena" \
    --exclude "archive" \
    "${ROOT}/" "${temp_repo}/"
else
  (cd "${ROOT}" && tar --exclude=".git" --exclude=".autoworkflow" --exclude=".venv*" --exclude="__pycache__" --exclude=".spec-workflow" --exclude=".serena" --exclude="archive" -cf - .) \
    | (cd "${temp_repo}" && tar -xf -)
fi

aw="${ROOT}/codex-skills/feature-shipper/scripts/autoworkflow.py"
if [[ ! -f "${aw}" ]]; then
  echo "[safe-smoke] Missing autoworkflow.py at ${aw}" >&2
  exit 2
fi

python "${aw}" --root "${temp_repo}" init --force

test_cmd="python -m py_compile ./agents_runner.py ./agents_sdk_runner.py ./agents_workflow.py ./codex-skills/feature-shipper/scripts/autoworkflow.py"
python "${aw}" --root "${temp_repo}" set-gate --create --build "echo skip" --test "${test_cmd}" --lint "echo skip" --format-check "echo skip"

python "${aw}" --root "${temp_repo}" plan gen
python "${aw}" --root "${temp_repo}" plan review
python "${aw}" --root "${temp_repo}" gate

python "${ROOT}/agents_runner.py" --root "${temp_repo}"

if [[ "${USE_CODEX}" == "true" ]]; then
  cat <<'PROMPT' | codex exec --full-auto -C "${temp_repo}" -c 'model_reasoning_effort="low"' -c 'mcp_servers={}' -
You are in a Git repository root on Windows.

Goal: run an end-to-end automation smoke test in the real Codex CLI runtime.

Hard rules:
- Do NOT read or inspect any files.
- Do NOT run any commands other than the 4 commands listed below, in order.
- For each command: print the exact command, run it, then print its exit code.
- If any command fails (non-zero), stop immediately and report the failing step.
- Do NOT edit/create/delete any source files. Only allow artifacts created by these commands (e.g. .autoworkflow/**, .autoworkflow/trace/**, and Python __pycache__).
- Do NOT run git commit/push/reset.

Commands:
1) python -m py_compile ./agents_runner.py ./agents_sdk_runner.py ./agents_workflow.py ./codex-skills/feature-shipper/scripts/autoworkflow.py
2) python .autoworkflow/tools/autoworkflow.py --root . plan review
3) python .autoworkflow/tools/autoworkflow.py --root . gate --allow-unreviewed
4) python agents_runner.py --root . --allow-unreviewed

Finish with a 3-line summary and list any .autoworkflow/trace/*.jsonl files created.
PROMPT
fi

echo "[safe-smoke] OK (cold start + gate + runner)"

