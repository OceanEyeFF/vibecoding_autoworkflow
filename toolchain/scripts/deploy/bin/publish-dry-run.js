#!/usr/bin/env node
"use strict";

const { spawnSync } = require("node:child_process");

function main() {
  const releaseChannel = process.env.AW_INSTALLER_RELEASE_CHANNEL || process.env.npm_config_tag || "next";
  const completed = spawnSync(
    "npm",
    ["publish", "--dry-run", "--json", "--tag", releaseChannel],
    {
      cwd: process.cwd(),
      env: process.env,
      shell: process.platform === "win32",
      stdio: "inherit",
    },
  );

  if (completed.error) {
    console.error(completed.error.message);
    return 1;
  }

  if (completed.status === null) {
    console.error(
      `npm publish --dry-run terminated by signal ${completed.signal || "<unknown>"}`,
    );
    return 1;
  }
  return completed.status;
}

if (require.main === module) {
  process.exit(main());
}

module.exports = {
  main,
};
