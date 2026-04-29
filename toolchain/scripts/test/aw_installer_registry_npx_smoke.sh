#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
exec node "$repo_root/toolchain/scripts/test/aw_installer_registry_npx_smoke.js" "$@"
