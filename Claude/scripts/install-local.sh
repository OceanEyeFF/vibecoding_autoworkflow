#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

bash "${ROOT}/CodeX/codex-skills/feature-shipper/scripts/install-claude-global.sh" \
  --claude-home "${ROOT}/.claude" \
  --force

echo "[install-local] Done: ${ROOT}/.claude"
