#!/usr/bin/env bash
set -euo pipefail

tmpdir="${1:-}"
if [[ -z "$tmpdir" ]]; then
  echo "usage: $0 <tmpdir>" >&2
  exit 2
fi

npm pack --json --pack-destination "$tmpdir" > "$tmpdir/pack.json"
node -e '
const fs = require("node:fs");
const path = require("node:path");
const payload = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
if (!Array.isArray(payload) || payload.length !== 1 || !payload[0].filename) {
  throw new Error("expected one npm pack result with filename");
}
console.log(path.join(process.argv[2], payload[0].filename));
' "$tmpdir/pack.json" "$tmpdir"
