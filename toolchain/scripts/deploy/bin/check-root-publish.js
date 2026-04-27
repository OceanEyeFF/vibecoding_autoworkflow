#!/usr/bin/env node
"use strict";

const { readFileSync } = require("node:fs");
const { join } = require("node:path");

const packagePath = join(__dirname, "..", "..", "..", "..", "package.json");
const packageMetadata = JSON.parse(readFileSync(packagePath, "utf8"));
const version = packageMetadata.version || "";
const isDryRun = process.env.npm_config_dry_run === "true";
const isLocalVersion = version === "0.0.0-local" || version.includes("-local");
const semverPattern =
  /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$/;
const prerelease = (version.match(semverPattern) || [])[4] || "";
const releaseChannel = process.env.AW_INSTALLER_RELEASE_CHANNEL || "";
const npmDistTag = process.env.npm_config_tag || "latest";
const releaseTag = process.env.AW_INSTALLER_RELEASE_GIT_TAG || "";
const publishApproved = process.env.AW_INSTALLER_PUBLISH_APPROVED === "1";
const isCiRelease = process.env.CI === "true";

if (packageMetadata.name !== "aw-installer") {
  console.error(`refusing to publish unexpected package ${packageMetadata.name || "<missing-name>"}`);
  process.exit(1);
}

if (isDryRun) {
  process.exit(0);
}

if (isLocalVersion && !isDryRun) {
  console.error(
    `refusing to publish aw-installer ${version}; choose an approved non-local version first`,
  );
  process.exit(1);
}

if (!semverPattern.test(version)) {
  console.error(`refusing to publish aw-installer ${version}; version must be valid semver`);
  process.exit(1);
}

if (!publishApproved) {
  console.error("refusing to publish aw-installer; set AW_INSTALLER_PUBLISH_APPROVED=1 after release approval");
  process.exit(1);
}

if (!isCiRelease) {
  console.error("refusing to publish aw-installer; real publish must run from a CI release context");
  process.exit(1);
}

if (!["latest", "next", "canary"].includes(releaseChannel)) {
  console.error("refusing to publish aw-installer; AW_INSTALLER_RELEASE_CHANNEL must be latest, next, or canary");
  process.exit(1);
}

if (npmDistTag !== releaseChannel) {
  console.error(
    `refusing to publish aw-installer; npm dist-tag ${npmDistTag} does not match release channel ${releaseChannel}`,
  );
  process.exit(1);
}

if (releaseChannel === "latest" && prerelease) {
  console.error("refusing to publish aw-installer latest; latest releases must not use prerelease versions");
  process.exit(1);
}

if (releaseChannel === "next" && !/^(alpha|beta|rc)(\.|$)/.test(prerelease)) {
  console.error("refusing to publish aw-installer next; next releases must use alpha, beta, or rc prerelease versions");
  process.exit(1);
}

if (releaseChannel === "canary" && !/(^|\.)canary(\.|$)/.test(prerelease)) {
  console.error("refusing to publish aw-installer canary; canary releases must include a canary prerelease segment");
  process.exit(1);
}

if (releaseTag !== `v${version}`) {
  console.error(`refusing to publish aw-installer; AW_INSTALLER_RELEASE_GIT_TAG must be v${version}`);
  process.exit(1);
}
