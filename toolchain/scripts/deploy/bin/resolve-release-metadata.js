#!/usr/bin/env node
"use strict";

const { appendFileSync, readFileSync } = require("node:fs");
const { join } = require("node:path");

const { deriveReleaseChannelFromTag } = require("./check-root-publish.js");

const semverPattern =
  /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$/;

function parseBoolean(value) {
  return value === true || value === "true";
}

function deriveReleaseMetadata({ version, releaseTag, releasePrerelease, releaseBody }) {
  const match = (version || "").match(semverPattern);
  if (!match) {
    throw new Error(`package version ${version || "<missing>"} is not valid semver`);
  }

  if (releaseTag !== `v${version}`) {
    throw new Error(`release tag ${releaseTag || "<missing>"} must match package version v${version}`);
  }

  const prerelease = match[4] || "";
  const channel = deriveReleaseChannelFromTag(releaseTag, version, prerelease);
  if (!channel) {
    throw new Error(
      `package prerelease segment ${prerelease || "<none>"} does not map to a release channel`,
    );
  }

  const isGithubPrerelease = parseBoolean(releasePrerelease);
  if (isGithubPrerelease && channel === "latest") {
    throw new Error("GitHub prerelease releases cannot publish to latest");
  }
  if (!isGithubPrerelease && channel !== "latest") {
    throw new Error(`GitHub stable releases cannot publish prerelease channel ${channel}`);
  }

  const approvalMarker = `aw-installer-publish-approved: ${releaseTag}`;
  if (!(releaseBody || "").includes(approvalMarker)) {
    throw new Error(`release body must include explicit approval marker: ${approvalMarker}`);
  }

  return {
    releaseTag,
    releaseChannel: channel,
    npmConfigTag: channel,
    packageVersion: version,
    approvalMarker,
  };
}

function readPackageMetadata(packagePath) {
  return JSON.parse(readFileSync(packagePath, "utf8"));
}

function writeGithubEnv(githubEnvPath, metadata) {
  appendFileSync(githubEnvPath, `AW_INSTALLER_RELEASE_GIT_TAG=${metadata.releaseTag}\n`);
  appendFileSync(githubEnvPath, `AW_INSTALLER_RELEASE_CHANNEL=${metadata.releaseChannel}\n`);
  appendFileSync(githubEnvPath, `NPM_CONFIG_TAG=${metadata.npmConfigTag}\n`);
}

function main() {
  const packagePath = join(__dirname, "..", "..", "..", "..", "package.json");
  const packageMetadata = readPackageMetadata(packagePath);
  const metadata = deriveReleaseMetadata({
    version: packageMetadata.version || "",
    releaseTag: process.env.GITHUB_RELEASE_TAG || process.env.GITHUB_REF_NAME || "",
    releasePrerelease: process.env.GITHUB_RELEASE_PRERELEASE || "",
    releaseBody: process.env.GITHUB_RELEASE_BODY || "",
  });

  if (process.env.GITHUB_ENV) {
    writeGithubEnv(process.env.GITHUB_ENV, metadata);
  }

  console.log(
    `resolved aw-installer release ${metadata.releaseTag} -> npm dist-tag ${metadata.releaseChannel}`,
  );
  return 0;
}

if (require.main === module) {
  try {
    process.exit(main());
  } catch (error) {
    console.error(error.message || String(error));
    process.exit(1);
  }
}

module.exports = {
  deriveReleaseMetadata,
  writeGithubEnv,
};
