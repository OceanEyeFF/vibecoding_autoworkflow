#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

bash "${ROOT}/CodeX/codex-skills/feature-shipper/scripts/uninstall-claude-global.sh" \
  --claude-home "${ROOT}/.claude" \
  --force \
  --purge

echo "[uninstall-local] Done: ${ROOT}/.claude"
