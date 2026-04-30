#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");

function resolvePackedTarball(packJsonPath, destinationDir) {
  const payload = JSON.parse(fs.readFileSync(packJsonPath, "utf8"));
  if (!Array.isArray(payload) || payload.length !== 1 || !payload[0].filename) {
    throw new Error("expected one npm pack result with filename");
  }
  return path.join(destinationDir, payload[0].filename);
}

if (require.main === module) {
  if (process.argv.length !== 4) {
    console.error("usage: npm_pack_tarball_result.js <pack.json> <tmpdir>");
    process.exit(2);
  }
  try {
    console.log(resolvePackedTarball(process.argv[2], process.argv[3]));
  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }
}

module.exports = {
  resolvePackedTarball,
};
