#!/usr/bin/env node
"use strict";

const { existsSync, readFileSync } = require("node:fs");
const { join } = require("node:path");

const packagePath = join(__dirname, "..", "..", "..", "..", "package.json");
const scaffoldPackagePath = join(__dirname, "..", "package.json");
const packageMetadata = JSON.parse(readFileSync(packagePath, "utf8"));
const scaffoldPackageMetadata = existsSync(scaffoldPackagePath)
  ? JSON.parse(readFileSync(scaffoldPackagePath, "utf8"))
  : null;
const packageJsonOverride = process.env.AW_INSTALLER_PACKAGE_JSON || "";
const version = packageMetadata.version || "";
const isDryRun = process.env.npm_config_dry_run === "true";
const isLocalVersion = version === "0.0.0-local" || version.includes("-local");
const semverPattern =
  /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$/;
const prerelease = (version.match(semverPattern) || [])[4] || "";
const releaseTag = process.env.AW_INSTALLER_RELEASE_GIT_TAG || "";
const envReleaseChannel = process.env.AW_INSTALLER_RELEASE_CHANNEL || "";
const derivedReleaseChannel = deriveReleaseChannelFromTag(releaseTag, version, prerelease);
const releaseChannel = derivedReleaseChannel || envReleaseChannel;
const npmDistTag = process.env.npm_config_tag || "latest";
const publishApproved = process.env.AW_INSTALLER_PUBLISH_APPROVED === "1";
const isCiRelease = process.env.CI === "true";

function deriveReleaseChannelFromTag(tag, packageVersion, packagePrerelease) {
  if (tag !== `v${packageVersion}`) {
    return "";
  }
  if (/(^|\.)canary(\.|$)/.test(packagePrerelease)) {
    return "canary";
  }
  if (/^(alpha|beta|rc)(\.|$)/.test(packagePrerelease)) {
    return "next";
  }
  if (!packagePrerelease) {
    return "latest";
  }
  return "";
}

function fail(message) {
  console.error(message);
  process.exit(1);
}

function runChecks(checks) {
  for (const check of checks) {
    if (!check.test()) {
      fail(check.message());
    }
  }
}

runChecks([
  {
    test: () => packageMetadata.name === "aw-installer",
    message: () => `refusing to publish unexpected package ${packageMetadata.name || "<missing-name>"}`,
  },
  {
    test: () => !packageJsonOverride,
    message: () =>
      "refusing to publish aw-installer; AW_INSTALLER_PACKAGE_JSON override is not supported",
  },
  {
    test: () =>
      scaffoldPackageMetadata === null || scaffoldPackageMetadata.version === packageMetadata.version,
    message: () =>
      `refusing to publish aw-installer; root package version ${packageMetadata.version || "<missing-version>"} does not match local scaffold package version ${scaffoldPackageMetadata.version || "<missing-version>"}`,
  },
]);

if (isDryRun) {
  process.exit(0);
}

runChecks([
  {
    test: () => !isLocalVersion,
    message: () =>
      `refusing to publish aw-installer ${version}; choose an approved non-local version first`,
  },
  {
    test: () => semverPattern.test(version),
    message: () => `refusing to publish aw-installer ${version}; version must be valid semver`,
  },
  {
    test: () => publishApproved,
    message: () =>
      "refusing to publish aw-installer; set AW_INSTALLER_PUBLISH_APPROVED=1 after release approval",
  },
  {
    test: () => isCiRelease,
    message: () => "refusing to publish aw-installer; real publish must run from a CI release context",
  },
  {
    test: () => ["latest", "next", "canary"].includes(releaseChannel),
    message: () =>
      "refusing to publish aw-installer; release channel must derive from AW_INSTALLER_RELEASE_GIT_TAG or use AW_INSTALLER_RELEASE_CHANNEL latest, next, or canary",
  },
  {
    test: () => npmDistTag === releaseChannel,
    message: () =>
      `refusing to publish aw-installer; npm dist-tag ${npmDistTag} does not match release channel ${releaseChannel}`,
  },
  {
    test: () => releaseChannel !== "latest" || !prerelease,
    message: () => "refusing to publish aw-installer latest; latest releases must not use prerelease versions",
  },
  {
    test: () => releaseChannel !== "next" || /^(alpha|beta|rc)(\.|$)/.test(prerelease),
    message: () =>
      "refusing to publish aw-installer next; next releases must use alpha, beta, or rc prerelease versions",
  },
  {
    test: () => releaseChannel !== "canary" || /(^|\.)canary(\.|$)/.test(prerelease),
    message: () =>
      "refusing to publish aw-installer canary; canary releases must include a canary prerelease segment",
  },
  {
    test: () => releaseTag === `v${version}`,
    message: () => `refusing to publish aw-installer; AW_INSTALLER_RELEASE_GIT_TAG must be v${version}`,
  },
]);
