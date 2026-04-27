#!/usr/bin/env node
"use strict";

const { spawnSync } = require("node:child_process");
const { join } = require("node:path");

const python = "python3";
const wrapperPath = join(__dirname, "..", "harness_deploy.py");
const defaultWrapperTimeoutMs = 300_000;
const wrapperTimeoutMs = readWrapperTimeoutMs();
const env = {
  ...process.env,
  PYTHONDONTWRITEBYTECODE: process.env.PYTHONDONTWRITEBYTECODE || "1",
};

function readWrapperTimeoutMs() {
  const parsedTimeout = Number.parseInt(
    process.env.AW_INSTALLER_WRAPPER_TIMEOUT_MS || `${defaultWrapperTimeoutMs}`,
    10,
  );
  if (Number.isFinite(parsedTimeout) && parsedTimeout > 0) {
    return parsedTimeout;
  }
  return defaultWrapperTimeoutMs;
}

const result = spawnSync(python, [wrapperPath, ...process.argv.slice(2)], {
  env,
  stdio: "inherit",
  timeout: wrapperTimeoutMs,
});

if (result.error) {
  if (result.error.code === "ETIMEDOUT") {
    console.error(`aw-harness-deploy timed out after ${Math.ceil(wrapperTimeoutMs / 1000)}s`);
    process.exit(1);
  }
  console.error(`aw-harness-deploy failed to start ${python}: ${result.error.message}`);
  process.exit(1);
}

if (result.signal) {
  console.error(`aw-harness-deploy terminated by signal ${result.signal}`);
  process.exit(1);
}

process.exit(result.status === null ? 1 : result.status);
