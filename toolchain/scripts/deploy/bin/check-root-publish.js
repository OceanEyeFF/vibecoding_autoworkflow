#!/usr/bin/env node
"use strict";

const { readFileSync } = require("node:fs");
const { join } = require("node:path");

const packagePath = join(__dirname, "..", "..", "..", "..", "package.json");
const packageMetadata = JSON.parse(readFileSync(packagePath, "utf8"));
const version = packageMetadata.version || "";
const isDryRun = process.env.npm_config_dry_run === "true";
const isLocalVersion = version === "0.0.0-local" || version.includes("-local");

if (packageMetadata.name !== "aw-installer") {
  console.error(`refusing to publish unexpected package ${packageMetadata.name || "<missing-name>"}`);
  process.exit(1);
}

if (isLocalVersion && !isDryRun) {
  console.error(
    `refusing to publish aw-installer ${version}; choose an approved non-local version first`,
  );
  process.exit(1);
}
