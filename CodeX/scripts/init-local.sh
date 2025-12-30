#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

python "${ROOT}/CodeX/codex-skills/feature-shipper/scripts/autoworkflow.py" --root "${ROOT}" init "$@"
echo "[init-local] Done: ${ROOT}/.autoworkflow"
