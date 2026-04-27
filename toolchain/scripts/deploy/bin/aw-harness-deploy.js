#!/usr/bin/env node
"use strict";

const { spawnSync } = require("node:child_process");
const { join } = require("node:path");

const python = "python3";
const wrapperPath = join(__dirname, "..", "harness_deploy.py");
const env = {
  ...process.env,
  PYTHONDONTWRITEBYTECODE: process.env.PYTHONDONTWRITEBYTECODE || "1",
};

const result = spawnSync(python, [wrapperPath, ...process.argv.slice(2)], {
  env,
  stdio: "inherit",
});

if (result.error) {
  console.error(`aw-harness-deploy failed to start ${python}: ${result.error.message}`);
  process.exit(1);
}

if (result.signal) {
  console.error(`aw-harness-deploy terminated by signal ${result.signal}`);
  process.exit(1);
}

process.exit(result.status === null ? 1 : result.status);
