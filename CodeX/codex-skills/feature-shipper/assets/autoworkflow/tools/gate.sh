#!/usr/bin/env bash
set -euo pipefail

AUTOWORKFLOW_DIR="${AUTOWORKFLOW_DIR:-.autoworkflow}"
GATE_ENV_FILE="${GATE_ENV_FILE:-${AUTOWORKFLOW_DIR}/gate.env}"

BUILD_CMD="${BUILD_CMD:-}"
TEST_CMD="${TEST_CMD:-}"
LINT_CMD="${LINT_CMD:-}"
FORMAT_CHECK_CMD="${FORMAT_CHECK_CMD:-}"

read_gate_env() {
  local file="$1"
  [[ -f "${file}" ]] || return 0
  while IFS= read -r line || [[ -n "${line}" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    [[ -z "${line}" ]] && continue
    [[ "${line}" == \#* ]] && continue
    [[ "${line}" != *"="* ]] && continue
    local key="${line%%=*}"
    local val="${line#*=}"
    key="${key%"${key##*[![:space:]]}"}"
    val="${val#"${val%%[![:space:]]*}"}"
    case "${key}" in
      BUILD_CMD) [[ -z "${BUILD_CMD}" ]] && BUILD_CMD="${val}" ;;
      TEST_CMD) [[ -z "${TEST_CMD}" ]] && TEST_CMD="${val}" ;;
      LINT_CMD) [[ -z "${LINT_CMD}" ]] && LINT_CMD="${val}" ;;
      FORMAT_CHECK_CMD) [[ -z "${FORMAT_CHECK_CMD}" ]] && FORMAT_CHECK_CMD="${val}" ;;
    esac
  done < "${file}"
}

read_gate_env "${GATE_ENV_FILE}"

run_step() {
  local name="$1"
  local cmd="$2"
  if [[ -z "${cmd}" ]]; then
    return 0
  fi
  echo "==> ${name}"
  echo "${cmd}"
  eval "${cmd}"
}

echo "Gate start: $(date -Iseconds)"

run_step "Build" "${BUILD_CMD}"
if [[ -z "${TEST_CMD}" ]]; then
  echo "Missing TEST_CMD (set it in ${GATE_ENV_FILE} or pass env var TEST_CMD)."
  exit 2
fi
run_step "Test" "${TEST_CMD}"
run_step "Lint" "${LINT_CMD}"
run_step "FormatCheck" "${FORMAT_CHECK_CMD}"

echo "Gate done (green)."
