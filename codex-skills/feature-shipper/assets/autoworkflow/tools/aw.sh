#!/usr/bin/env bash
set -euo pipefail

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="${TOOL_DIR}/autoworkflow.py"

if [[ ! -f "${SCRIPT}" ]]; then
  echo "Missing ${SCRIPT} (run autoworkflow init first)." >&2
  exit 2
fi

PYTHON_BIN="python"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Missing python/python3 in PATH." >&2
  exit 127
fi

"${PYTHON_BIN}" "${SCRIPT}" "$@"
