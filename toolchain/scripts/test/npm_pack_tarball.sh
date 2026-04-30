#!/usr/bin/env bash
set -euo pipefail

tmpdir="${1:-}"
if [[ -z "$tmpdir" ]]; then
  echo "usage: $0 <tmpdir>" >&2
  exit 2
fi

npm pack --json --pack-destination "$tmpdir" > "$tmpdir/pack.json"
node "$(dirname "$0")/npm_pack_tarball_result.js" "$tmpdir/pack.json" "$tmpdir"
