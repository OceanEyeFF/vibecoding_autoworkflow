#!/usr/bin/env node
"use strict";

const { spawn } = require("node:child_process");
const {
  existsSync,
  lstatSync,
  readFileSync,
  readdirSync,
  realpathSync,
} = require("node:fs");
const { basename, dirname, isAbsolute, join, relative, resolve, sep } = require("node:path");
const { createHash } = require("node:crypto");
const readline = require("node:readline");

const wrapperPath = join(__dirname, "..", "harness_deploy.py");
const pathSafetyPolicyPath = join(__dirname, "..", "path_safety_policy.json");
const defaultWrapperTimeoutMs = 300_000;
const wrapperTimeoutMs = readWrapperTimeoutMs();
const env = {
  ...process.env,
  PYTHONDONTWRITEBYTECODE: process.env.PYTHONDONTWRITEBYTECODE || "1",
};
const packageVersionFallbackMaxDepth = 20;
const payloadDescriptor = "payload.json";
const managedSkillMarker = "aw.marker";
const managedSkillMarkerVersion = "aw-managed-skill-marker.v2";
const expectedPayloadVersion = "agents-skill-payload.v1";
const unrecognizedIssueCodes = new Set(["unrecognized-target-directory"]);
const conflictIssueCodes = new Set([
  "unexpected-managed-directory",
  "unrecognized-target-directory",
  "wrong-target-entry-type",
]);
const updateRecoverableIssueCodes = new Set([
  "missing-target-root",
  "missing-target-entry",
  "missing-required-payload",
  "target-payload-drift",
  "unexpected-managed-directory",
]);
let cachedPathSafetyPolicy = null;

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

function pythonCandidates() {
  if (process.platform === "win32") {
    return [
      { command: "py", args: ["-3"] },
      { command: "python", args: [] },
      { command: "python3", args: [] },
    ];
  }
  return [
    { command: "python3", args: [] },
  ];
}

function formatPythonCandidate(candidate) {
  return [candidate.command, ...candidate.args].join(" ");
}

function tryReadPackageVersionAt(candidate) {
  try {
    const packageMetadata = JSON.parse(readFileSync(candidate, "utf8"));
    if (packageMetadata.name === "aw-installer" && packageMetadata.version) {
      return packageMetadata.version;
    }
    return "";
  } catch (error) {
    return "";
  }
}

function printHelp() {
  console.log(`usage: aw-installer [tui|<deploy-mode>] [options]

Run AW Harness installer commands through the stable distribution wrapper.
Deploy modes delegate to harness_deploy.py and preserve adapter_deploy.py
semantics.

commands:
  tui                         open the interactive installer shell
  diagnose --backend agents|claude
                              print a read-only deploy status summary
  verify --backend agents|claude
                              run strict read-only deploy verification
  install --backend agents|claude
                              install the current source payload
  update --backend agents|claude
                              print an update dry-run plan
  update --backend agents --yes
                              apply the explicit update plan
  update --backend agents --source github --github-ref REF
                              update from a GitHub source archive containing current payloads
  prune --all --backend agents|claude
                              remove managed installs for the backend
  check_paths_exist --backend agents|claude
                              scan write paths before install

options:
  -h, --help                  show this help message
  -V, --version               show package version
  --source package|github     select package-local or GitHub update source
  --agents-root PATH          override the managed agents skills target root
  --claude-root PATH          override the managed Claude skills target root
  --github-repo OWNER/REPO    GitHub source repository for --source github
                              defaults from AW_INSTALLER_GITHUB_REPO,
                              GITHUB_REPOSITORY, then upstream repo
  --github-ref REF            GitHub branch/ref for --source github
  --github-archive-sha256 SHA256
                              optional SHA256 digest for the GitHub source archive
`);
}

function readPackageVersion() {
  const knownPackagePaths = [
    join(__dirname, "..", "..", "..", "..", "package.json"),
    join(__dirname, "..", "package.json"),
  ];
  for (const candidate of knownPackagePaths) {
    if (!existsSync(candidate)) {
      continue;
    }
    const packageVersion = tryReadPackageVersionAt(candidate);
    if (packageVersion) {
      return packageVersion;
    }
  }

  let current = __dirname;
  for (let depth = 0; depth < packageVersionFallbackMaxDepth; depth += 1) {
    const candidate = join(current, "package.json");
    if (existsSync(candidate)) {
      const packageVersion = tryReadPackageVersionAt(candidate);
      if (packageVersion) {
        return packageVersion;
      }
    }

    const parent = dirname(current);
    if (parent === current) {
      throw new Error("could not find aw-installer package metadata");
    }
    current = parent;
  }
  throw new Error(
    `could not find aw-installer package metadata within ${packageVersionFallbackMaxDepth} parent directories`,
  );
}

function printVersion() {
  console.log(`aw-installer ${readPackageVersion()}`);
}

function pathExists(path) {
  return existsSync(path);
}

function lstatOrNull(path) {
  try {
    return lstatSync(path);
  } catch (error) {
    if (error.code === "ENOENT") {
      return null;
    }
    throw error;
  }
}

function resolveExistingOrLexical(path) {
  let candidate = path;
  if (candidate === "~" || candidate.startsWith(`~${sep}`) || candidate.startsWith("~/")) {
    const home = process.env.HOME || "";
    if (home) {
      candidate = join(home, candidate.slice(2));
    }
  }
  let resolved = resolve(candidate);
  try {
    return realpathSync(resolved);
  } catch (error) {
    if (error.code !== "ENOENT") {
      throw error;
    }
  }

  const suffix = [];
  while (!existsSync(resolved)) {
    const parent = dirname(resolved);
    if (parent === resolved) {
      return resolve(candidate);
    }
    suffix.unshift(basename(resolved));
    resolved = parent;
  }
  return resolve(realpathSync(resolved), ...suffix);
}

function pathIsRelativeTo(path, parent) {
  const relativePath = relative(parent, path);
  return relativePath === "" || (!relativePath.startsWith("..") && !isAbsolute(relativePath));
}

function pathSafetyPolicy() {
  if (cachedPathSafetyPolicy !== null) {
    return cachedPathSafetyPolicy;
  }
  cachedPathSafetyPolicy = readJsonObject(pathSafetyPolicyPath);
  return cachedPathSafetyPolicy;
}

function pathSafetyPolicyStringList(fieldName) {
  const value = pathSafetyPolicy()[fieldName];
  if (!Array.isArray(value) || !value.every((item) => typeof item === "string")) {
    throw new Error(`path safety policy field must be a string array: ${fieldName}`);
  }
  return value;
}

function exactSensitiveTargetRepoRoots() {
  return pathSafetyPolicyStringList("exact_sensitive_target_repo_roots").map((path) =>
    resolveExistingOrLexical(path),
  );
}

function recursiveSensitiveTargetRepoRoots() {
  const home = process.env.HOME || "";
  const roots = [...pathSafetyPolicyStringList("recursive_sensitive_target_repo_roots")];
  if (home) {
    roots.push(
      ...pathSafetyPolicyStringList("home_relative_recursive_sensitive_target_repo_roots").map(
        (path) => join(home, path),
      ),
    );
  }
  return roots.map((path) => resolveExistingOrLexical(path));
}

function validateTargetRepoRoot(path, sourceRoot) {
  const resolved = resolveExistingOrLexical(path);
  for (const sensitiveRoot of exactSensitiveTargetRepoRoots()) {
    if (resolved === sensitiveRoot) {
      throw new Error(`Target repo root is protected and cannot be managed: ${resolved}`);
    }
  }
  for (const sensitiveRoot of recursiveSensitiveTargetRepoRoots()) {
    if (resolved === sensitiveRoot || pathIsRelativeTo(resolved, sensitiveRoot)) {
      throw new Error(`Target repo root is protected and cannot be managed: ${resolved}`);
    }
  }

  const tokens = {
    $cwd: process.cwd(),
    $source_root: sourceRoot,
    $home: process.env.HOME || "",
  };
  const allowedPrefixes = pathSafetyPolicyStringList("allowed_target_repo_root_prefixes")
    .map((entry) => tokens[entry] || entry)
    .filter(Boolean)
    .map((candidate) => resolveExistingOrLexical(candidate));
  const uniqueAllowedPrefixes = [...new Set(allowedPrefixes)];
  if (!uniqueAllowedPrefixes.some((prefix) => resolved === prefix || pathIsRelativeTo(resolved, prefix))) {
    throw new Error(
      `Target repo root ${resolved} is outside allowed paths: ${uniqueAllowedPrefixes.join(", ")}`,
    );
  }
  return resolved;
}

function validateSourceRepoRoot(path) {
  const resolved = resolveExistingOrLexical(path);
  for (const sensitiveRoot of exactSensitiveTargetRepoRoots()) {
    if (resolved === sensitiveRoot) {
      throw new Error(`Source repo root is protected and cannot be used: ${resolved}`);
    }
  }
  for (const sensitiveRoot of recursiveSensitiveTargetRepoRoots()) {
    if (resolved === sensitiveRoot || pathIsRelativeTo(resolved, sensitiveRoot)) {
      throw new Error(`Source repo root is protected and cannot be used: ${resolved}`);
    }
  }

  const requiredPaths = [
    join(resolved, "product", "harness", "adapters", "agents", "skills"),
    join(resolved, "product", "harness", "adapters", "claude", "skills"),
    join(resolved, "product", "harness", "skills"),
  ];
  const missingPaths = requiredPaths
    .filter((requiredPath) => !isDirectory(requiredPath))
    .map((requiredPath) => relative(resolved, requiredPath).split(sep).join("/"));
  if (missingPaths.length > 0) {
    throw new Error(
      `Source repo root ${resolved} is not a Harness payload source; missing: ${missingPaths.join(", ")}`,
    );
  }
  return resolved;
}

function resolveSourceRoot() {
  const override = process.env.AW_HARNESS_REPO_ROOT;
  if (override) {
    return validateSourceRepoRoot(override);
  }
  return validateSourceRepoRoot(join(__dirname, "..", "..", "..", ".."));
}

function resolveTargetRepoRoot(sourceRoot, sourceRootFromEnv) {
  const targetOverride = process.env.AW_HARNESS_TARGET_REPO_ROOT;
  if (targetOverride) {
    return validateTargetRepoRoot(targetOverride, sourceRoot);
  }
  if (sourceRootFromEnv) {
    return validateTargetRepoRoot(sourceRoot, sourceRoot);
  }
  return validateTargetRepoRoot(process.cwd(), sourceRoot);
}

function buildNodeAgentsContext() {
  const sourceRootFromEnv = Boolean(process.env.AW_HARNESS_REPO_ROOT);
  const sourceRoot = resolveSourceRoot();
  const targetRepoRoot = resolveTargetRepoRoot(sourceRoot, sourceRootFromEnv);
  return {
    sourceKind: "package",
    sourceRef: "package-local",
    sourceRoot,
    targetRepoRoot,
    targetRoot: join(targetRepoRoot, ".agents", "skills"),
    adapterSkillsDir: join(sourceRoot, "product", "harness", "adapters", "agents", "skills"),
  };
}

function buildNodeDiagnoseContext() {
  return buildNodeAgentsContext();
}

function isDirectory(path) {
  const stat = lstatOrNull(path);
  return stat !== null && !stat.isSymbolicLink() && stat.isDirectory();
}

function isFile(path) {
  const stat = lstatOrNull(path);
  return stat !== null && !stat.isSymbolicLink() && stat.isFile();
}

function readJsonObject(path) {
  let data;
  try {
    data = JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    throw new Error(`Invalid JSON in ${path}: ${error.message}`);
  }
  if (data === null || Array.isArray(data) || typeof data !== "object") {
    throw new Error(`JSON payload must be an object: ${path}`);
  }
  return data;
}

function readJsonObjectWithText(path) {
  let text;
  try {
    text = readFileSync(path, "utf8");
  } catch (error) {
    if (error.code === "ENOENT") {
      throw new Error(`Missing JSON file: ${path}`);
    }
    throw error;
  }
  let data;
  try {
    data = JSON.parse(text);
  } catch (error) {
    throw new Error(`Invalid JSON in ${path}: ${error.message}`);
  }
  if (data === null || Array.isArray(data) || typeof data !== "object") {
    throw new Error(`JSON payload must be an object: ${path}`);
  }
  return { data, text };
}

function normalizeRelativePath(value, fieldName, skillId, rootDescription) {
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`${fieldName} must be a non-empty relative path for skill ${skillId}`);
  }
  const normalized = value.replace(/\\/g, "/");
  if (normalized.startsWith("/") || /^[A-Za-z]:/.test(normalized)) {
    throw new Error(`${fieldName} must stay within the ${rootDescription} for skill ${skillId}: ${value}`);
  }
  const segments = normalized.split("/").filter(Boolean);
  const invalidSegment = segments.find((segment) => segment === "." || segment === "..");
  if (invalidSegment) {
    throw new Error(`${fieldName} must not contain '${invalidSegment}' path segments for skill ${skillId}: ${value}`);
  }
  if (segments.length === 0) {
    throw new Error(`${fieldName} must be a non-empty relative path for skill ${skillId}`);
  }
  return segments.join("/");
}

function stringList(value) {
  return Array.isArray(value) && value.every((item) => typeof item === "string") ? value : null;
}

function payloadTargetMetadata(payload, binding) {
  const targetDirValue = payload.target_dir;
  const targetEntryName = payload.target_entry_name;
  const requiredPayloadFiles = stringList(payload.required_payload_files);
  if (typeof targetDirValue !== "string" || typeof targetEntryName !== "string") {
    throw new Error(`payload target metadata is invalid for skill ${binding.skillId}`);
  }
  if (requiredPayloadFiles === null) {
    throw new Error(`payload required_payload_files must be a string array for skill ${binding.skillId}`);
  }

  const targetDir = normalizeRelativePath(
    targetDirValue,
    "payload target_dir",
    binding.skillId,
    "backend target root",
  );
  if (targetDir.includes("/")) {
    throw new Error(`payload target_dir must be a single directory name for skill ${binding.skillId}: ${targetDirValue}`);
  }
  const targetEntry = normalizeRelativePath(
    targetEntryName,
    "payload target_entry_name",
    binding.skillId,
    "backend target root",
  );
  const requiredFiles = requiredPayloadFiles.map((entry) =>
    normalizeRelativePath(entry, "payload required_payload_files entry", binding.skillId, "backend target root"),
  );
  if (!requiredFiles.includes(targetEntry)) {
    throw new Error(
      `payload target_entry_name ${targetEntryName} must be listed in required_payload_files for skill ${binding.skillId}`,
    );
  }
  if (!requiredFiles.includes(payloadDescriptor)) {
    throw new Error(`payload required_payload_files must include ${payloadDescriptor} for skill ${binding.skillId}`);
  }
  if (!requiredFiles.includes(managedSkillMarker)) {
    throw new Error(`payload required_payload_files must include ${managedSkillMarker} for skill ${binding.skillId}`);
  }

  const legacyTargetDirsRaw = payload.legacy_target_dirs === undefined ? [] : stringList(payload.legacy_target_dirs);
  if (legacyTargetDirsRaw === null) {
    throw new Error(`payload legacy_target_dirs must be a list of strings for skill ${binding.skillId}`);
  }
  const legacyTargetDirs = legacyTargetDirsRaw.map((entry) =>
    normalizeRelativePath(entry, "payload legacy_target_dirs entry", binding.skillId, "backend target root"),
  );
  for (const legacyDir of legacyTargetDirs) {
    if (legacyDir.includes("/")) {
      throw new Error(
        `payload legacy_target_dirs entries must be single directory names for skill ${binding.skillId}: ${legacyDir}`,
      );
    }
  }
  if (legacyTargetDirs.includes(targetDir)) {
    throw new Error(`payload target_dir ${targetDir} must not be listed in legacy_target_dirs for skill ${binding.skillId}`);
  }

  const legacySkillIdsRaw = payload.legacy_skill_ids === undefined ? [] : stringList(payload.legacy_skill_ids);
  if (legacySkillIdsRaw === null) {
    throw new Error(`payload legacy_skill_ids must be a list of strings for skill ${binding.skillId}`);
  }
  const legacySkillIds = legacySkillIdsRaw.map((entry) =>
    normalizeRelativePath(entry, "payload legacy_skill_ids entry", binding.skillId, "backend target root"),
  );
  for (const legacySkillId of legacySkillIds) {
    if (legacySkillId.includes("/")) {
      throw new Error(
        `payload legacy_skill_ids entries must be single directory names for skill ${binding.skillId}: ${legacySkillId}`,
      );
    }
  }
  if (legacySkillIds.includes(binding.skillId)) {
    throw new Error(`binding skill_id ${binding.skillId} must not be listed in legacy_skill_ids for skill ${binding.skillId}`);
  }

  return {
    targetDir,
    targetEntryName: targetEntry,
    requiredPayloadFiles: requiredFiles,
    legacyTargetDirs,
    legacySkillIds,
  };
}

function collectSkillBindings(context) {
  if (!isDirectory(context.adapterSkillsDir)) {
    return [];
  }
  return readdirSync(context.adapterSkillsDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort()
    .map((skillId) => ({
      backend: "agents",
      skillId,
      payloadDir: join(context.adapterSkillsDir, skillId),
      payloadPath: join(context.adapterSkillsDir, skillId, payloadDescriptor),
    }));
}

function cachedBindingPayload(binding, loadedPayloads) {
  if (loadedPayloads === null || loadedPayloads === undefined) {
    return null;
  }
  return loadedPayloads.get(binding.payloadPath) || null;
}

function bindingPayloadObject(binding, loadedPayloads) {
  const cachedPayload = cachedBindingPayload(binding, loadedPayloads);
  if (cachedPayload !== null) {
    return cachedPayload.payload;
  }
  return readJsonObject(binding.payloadPath);
}

function bindingPayloadWithText(binding, loadedPayloads) {
  const cachedPayload = cachedBindingPayload(binding, loadedPayloads);
  if (cachedPayload !== null) {
    return cachedPayload;
  }
  const loadedPayload = readJsonObjectWithText(binding.payloadPath);
  return {
    payload: loadedPayload.data,
    payloadText: loadedPayload.text,
  };
}

function loadBindingPayloads(bindings) {
  const loadedPayloads = new Map();
  for (const binding of bindings) {
    loadedPayloads.set(binding.payloadPath, bindingPayloadWithText(binding, null));
  }
  return loadedPayloads;
}

function issue(code, path, detail) {
  return { code, path, detail };
}

function verifyTargetRoot(targetRoot) {
  const stat = lstatOrNull(targetRoot);
  if (stat === null) {
    return [issue("missing-target-root", targetRoot, "agents target root does not exist")];
  }
  if (stat.isSymbolicLink()) {
    if (existsSync(targetRoot)) {
      return [issue("wrong-target-root-type", targetRoot, "target root must be a real directory, not a symlink")];
    }
    return [issue("broken-target-root-symlink", targetRoot, "target root is a broken symlink")];
  }
  if (stat.isDirectory()) {
    return [];
  }
  return [issue("wrong-target-root-type", targetRoot, "target root exists but is not a directory")];
}

function canonicalSourceMetadata(payload, binding, context) {
  const canonicalDirValue = payload.canonical_dir;
  const canonicalPaths = stringList(payload.canonical_paths);
  if (typeof canonicalDirValue !== "string" || canonicalPaths === null) {
    throw new Error(`payload canonical_dir and canonical_paths must be defined for skill ${binding.skillId}`);
  }
  const canonicalDir = normalizeRelativePath(
    canonicalDirValue,
    "payload canonical_dir",
    binding.skillId,
    "repository root",
  );
  const canonicalFiles = new Map();
  const includedPaths = [];
  for (const canonicalPath of canonicalPaths) {
    const normalizedCanonicalPath = normalizeRelativePath(
      canonicalPath,
      "payload canonical_paths entry",
      binding.skillId,
      "repository root",
    );
    const relativePath = relative(
      join(context.sourceRoot, canonicalDir),
      join(context.sourceRoot, normalizedCanonicalPath),
    ).split(sep).join("/");
    if (relativePath === "" || relativePath.startsWith("..") || isAbsolute(relativePath)) {
      throw new Error(
        `payload canonical_paths entry must stay within canonical_dir for skill ${binding.skillId}: ${canonicalPath}`,
      );
    }
    if (canonicalFiles.has(relativePath)) {
      throw new Error(
        `payload canonical_paths contain duplicate target-relative file ${relativePath} for skill ${binding.skillId}`,
      );
    }
    includedPaths.push(relativePath);
    canonicalFiles.set(relativePath, join(context.sourceRoot, normalizedCanonicalPath));
  }
  return { canonicalDir, includedPaths, canonicalFiles };
}

function verifySourceBinding(binding, context, loadedPayloads = null) {
  const issues = [];
  if (!isDirectory(binding.payloadDir)) {
    return [
      issue(
        "missing-backend-payload-source",
        binding.payloadDir,
        `missing backend payload source for skill ${binding.skillId}`,
      ),
    ];
  }

  let payload;
  try {
    payload = bindingPayloadObject(binding, loadedPayloads);
  } catch (error) {
    return [issue("payload-contract-invalid", binding.payloadPath, error.message)];
  }

  let canonicalSource = null;
  try {
    canonicalSource = canonicalSourceMetadata(payload, binding, context);
  } catch (error) {
    issues.push(issue("payload-contract-invalid", binding.payloadPath, error.message));
  }

  const canonicalDir = join(
    context.sourceRoot,
    canonicalSource === null ? String(payload.canonical_dir || "") : canonicalSource.canonicalDir,
  );
  if (!isDirectory(canonicalDir)) {
    issues.push(issue("missing-canonical-source", canonicalDir, `missing canonical directory for skill ${binding.skillId}`));
  }
  if (canonicalSource !== null && canonicalSource.canonicalDir.split("/").at(-1) !== binding.skillId) {
    issues.push(
      issue(
        "payload-contract-invalid",
        binding.payloadPath,
        `payload canonical_dir must end with ${binding.skillId} for skill ${binding.skillId}`,
      ),
    );
  }
  if (canonicalSource !== null) {
    for (const [includedPath, canonicalFile] of canonicalSource.canonicalFiles) {
      if (!isFile(canonicalFile)) {
        issues.push(
          issue("missing-canonical-source", canonicalFile, `missing canonical file ${includedPath} for skill ${binding.skillId}`),
        );
      }
    }
  }

  if (payload.payload_version !== expectedPayloadVersion) {
    issues.push(
      issue(
        "payload-contract-invalid",
        binding.payloadPath,
        `payload payload_version must be ${expectedPayloadVersion} for backend agents skill ${binding.skillId}`,
      ),
    );
  }
  if (payload.backend !== "agents") {
    issues.push(issue("payload-contract-invalid", binding.payloadPath, `payload backend must be agents for skill ${binding.skillId}`));
  }
  if (payload.skill_id !== binding.skillId) {
    issues.push(issue("payload-contract-invalid", binding.payloadPath, `payload skill_id must be ${binding.skillId}`));
  }

  try {
    const targetMetadata = payloadTargetMetadata(payload, binding);
    const expectedRequiredFiles = [
      ...(canonicalSource === null ? [] : canonicalSource.includedPaths),
      payloadDescriptor,
      managedSkillMarker,
    ];
    if (JSON.stringify(targetMetadata.requiredPayloadFiles) !== JSON.stringify(expectedRequiredFiles)) {
      issues.push(
        issue(
          "payload-contract-invalid",
          binding.payloadPath,
          `payload required_payload_files must equal payload canonical_paths plus ${payloadDescriptor} and ${managedSkillMarker} for skill ${binding.skillId}`,
        ),
      );
    }
  } catch (error) {
    issues.push(issue("payload-contract-invalid", binding.payloadPath, error.message));
  }

  if (payload.payload_policy !== "canonical-copy") {
    issues.push(
      issue(
        "payload-policy-mismatch",
        binding.payloadPath,
        `payload_policy must be canonical-copy for backend agents skill ${binding.skillId}`,
      ),
    );
  }
  if (payload.reference_distribution !== "copy-listed-canonical-paths") {
    issues.push(
      issue(
        "reference-policy-mismatch",
        binding.payloadPath,
        `reference_distribution must be copy-listed-canonical-paths for backend agents skill ${binding.skillId}`,
      ),
    );
  }

  return issues;
}

function loadRuntimeMarker(markerPath) {
  if (!isFile(markerPath)) {
    return null;
  }
  let marker;
  try {
    marker = readJsonObject(markerPath);
  } catch (error) {
    return null;
  }
  const expectedKeys = [
    "backend",
    "marker_version",
    "payload_fingerprint",
    "payload_version",
    "skill_id",
  ];
  if (JSON.stringify(Object.keys(marker).sort()) !== JSON.stringify(expectedKeys)) {
    return null;
  }
  if (
    marker.marker_version !== managedSkillMarkerVersion ||
    typeof marker.backend !== "string" ||
    typeof marker.skill_id !== "string" ||
    typeof marker.payload_version !== "string" ||
    typeof marker.payload_fingerprint !== "string"
  ) {
    return null;
  }
  return marker;
}

function sourcePathForTargetRelativeFile(binding, relativeName, context, payload) {
  if (relativeName === payloadDescriptor) {
    return binding.payloadPath;
  }
  if (relativeName === managedSkillMarker) {
    throw new Error(`${managedSkillMarker} is runtime-generated for skill ${binding.skillId}`);
  }
  const canonicalSource = canonicalSourceMetadata(payload, binding, context);
  const sourcePath = canonicalSource.canonicalFiles.get(relativeName);
  if (sourcePath === undefined) {
    throw new Error(
      `payload required file ${relativeName} is not declared in payload canonical_paths for skill ${binding.skillId}`,
    );
  }
  return sourcePath;
}

function computePayloadFingerprint(binding, context, payload, payloadText, metadata) {
  if (typeof payload.payload_version !== "string") {
    throw new Error(`payload payload_version must be a string for skill ${binding.skillId}`);
  }
  const fingerprintParts = [
    `backend=${binding.backend}\nskill_id=${binding.skillId}\npayload_version=${payload.payload_version}\n`,
  ];
  for (const relativeName of metadata.requiredPayloadFiles) {
    if (relativeName === managedSkillMarker || relativeName === payloadDescriptor) {
      continue;
    }
    const sourcePath = sourcePathForTargetRelativeFile(binding, relativeName, context, payload);
    let sourceText;
    try {
      sourceText = readFileSync(sourcePath, "utf8");
    } catch (error) {
      if (error.code === "ENOENT") {
        throw new Error(`Missing payload source file while computing fingerprint: ${sourcePath}`);
      }
      throw error;
    }
    fingerprintParts.push(`file:${relativeName}\n${sourceText}\n`);
  }
  fingerprintParts.push(`file:${payloadDescriptor}\n${payloadText}\n`);
  return createHash("sha256").update(fingerprintParts.join(""), "utf8").digest("hex");
}

function runtimeMarkerText(marker) {
  return `${JSON.stringify(
    {
      marker_version: marker.marker_version,
      backend: marker.backend,
      skill_id: marker.skill_id,
      payload_version: marker.payload_version,
      payload_fingerprint: marker.payload_fingerprint,
    },
    null,
    2,
  )}\n`;
}

function targetRootChildren(targetRoot) {
  try {
    return readdirSync(targetRoot, { withFileTypes: true })
      .map((entry) => join(targetRoot, entry.name))
      .sort();
  } catch (error) {
    throw new Error(`Failed to scan verify target root at ${targetRoot}: ${error.message}`);
  }
}

function collectTargetDirMetadata(bindings, loadedPayloads = null) {
  const targetDirs = new Set();
  const metadataByPayloadPath = new Map();
  for (const binding of bindings) {
    const metadata = payloadTargetMetadata(bindingPayloadObject(binding, loadedPayloads), binding);
    if (targetDirs.has(metadata.targetDir)) {
      throw new Error(`Multiple skills map to the same target_dir for backend agents: ${metadata.targetDir}`);
    }
    targetDirs.add(metadata.targetDir);
    metadataByPayloadPath.set(binding.payloadPath, metadata);
  }
  return { targetDirs, metadataByPayloadPath };
}

function expectedTargetDirs(bindings, loadedPayloads = null) {
  return collectTargetDirMetadata(bindings, loadedPayloads).targetDirs;
}

function knownTargetDirsFromMetadata(bindings, metadataByPayloadPath) {
  const knownTargetDirs = new Set();
  for (const binding of bindings) {
    const metadata = metadataByPayloadPath.get(binding.payloadPath);
    knownTargetDirs.add(metadata.targetDir);
    for (const legacyTargetDir of metadata.legacyTargetDirs) {
      knownTargetDirs.add(legacyTargetDir);
    }
  }
  return knownTargetDirs;
}

function allKnownTargetDirs(bindings, loadedPayloads = null) {
  const { metadataByPayloadPath } = collectTargetDirMetadata(bindings, loadedPayloads);
  return knownTargetDirsFromMetadata(bindings, metadataByPayloadPath);
}

function verifyDeployedSkill(binding, targetRoot, context, loadedPayloads = null) {
  let payload;
  let payloadText;
  let metadata;
  let payloadFingerprint;
  try {
    const loadedPayload = bindingPayloadWithText(binding, loadedPayloads);
    payload = loadedPayload.payload;
    payloadText = loadedPayload.payloadText;
    metadata = payloadTargetMetadata(payload, binding);
    payloadFingerprint = computePayloadFingerprint(binding, context, payload, payloadText, metadata);
  } catch (error) {
    return [issue("payload-contract-invalid", binding.payloadPath, error.message)];
  }

  const targetSkillDir = join(targetRoot, metadata.targetDir);
  if (!pathExists(targetSkillDir)) {
    return [
      issue(
        "missing-target-entry",
        targetSkillDir,
        `missing deployed skill directory for skill ${binding.skillId}`,
      ),
    ];
  }
  if (!isDirectory(targetSkillDir)) {
    return [
      issue(
        "wrong-target-entry-type",
        targetSkillDir,
        `deployed skill directory must be a real directory for skill ${binding.skillId}`,
      ),
    ];
  }
  const marker = loadRuntimeMarker(join(targetSkillDir, managedSkillMarker));
  if (marker === null) {
    return [
      issue(
        "unrecognized-target-directory",
        targetSkillDir,
        `existing deployed directory has no recognized ${managedSkillMarker}`,
      ),
    ];
  }
  if (marker.backend !== "agents" || marker.skill_id !== binding.skillId || marker.payload_version !== payload.payload_version) {
    return [
      issue(
        "unrecognized-target-directory",
        targetSkillDir,
        `recognized ${managedSkillMarker} does not match current backend/skill/payload_version`,
      ),
    ];
  }

  const issues = [];
  const expectedMarker = {
    marker_version: managedSkillMarkerVersion,
    backend: binding.backend,
    skill_id: binding.skillId,
    payload_version: payload.payload_version,
    payload_fingerprint: payloadFingerprint,
  };
  const markerMatchesSource = marker.payload_fingerprint === payloadFingerprint;
  if (!markerMatchesSource) {
    issues.push(
      issue(
        "target-payload-drift",
        join(targetSkillDir, managedSkillMarker),
        `deployed payload fingerprint drifted from adapter source for skill ${binding.skillId}`,
      ),
    );
  }
  for (const relativeName of metadata.requiredPayloadFiles) {
    const targetPath = join(targetSkillDir, relativeName);
    if (!pathExists(targetPath)) {
      issues.push(
        issue(
          "missing-required-payload",
          targetPath,
          `missing deployed payload file ${relativeName} for skill ${binding.skillId}`,
        ),
      );
      continue;
    }
    if (!isFile(targetPath)) {
      issues.push(
        issue(
          "wrong-target-entry-type",
          targetPath,
          `deployed payload file ${relativeName} must be a real file for skill ${binding.skillId}`,
        ),
      );
      continue;
    }
    if (relativeName === managedSkillMarker) {
      if (markerMatchesSource && readFileSync(targetPath, "utf8") !== runtimeMarkerText(expectedMarker)) {
        issues.push(
          issue(
            "target-payload-drift",
            targetPath,
            `deployed payload file ${relativeName} drifted from adapter source for skill ${binding.skillId}`,
          ),
        );
      }
      continue;
    }
    let sourcePath;
    try {
      sourcePath =
        relativeName === payloadDescriptor
          ? binding.payloadPath
          : sourcePathForTargetRelativeFile(binding, relativeName, context, payload);
    } catch (error) {
      issues.push(issue("payload-contract-invalid", binding.payloadPath, error.message));
      continue;
    }
    if (readFileSync(sourcePath, "utf8") !== readFileSync(targetPath, "utf8")) {
      issues.push(
        issue(
          "target-payload-drift",
          targetPath,
          `deployed payload file ${relativeName} drifted from adapter source for skill ${binding.skillId}`,
        ),
      );
    }
  }
  const targetEntry = join(targetSkillDir, metadata.targetEntryName);
  if (!pathExists(targetEntry)) {
    issues.push(
      issue(
        "missing-target-entry",
        targetEntry,
        `missing target entry ${metadata.targetEntryName} for skill ${binding.skillId}`,
      ),
    );
  } else if (!isFile(targetEntry)) {
    issues.push(
      issue(
        "wrong-target-entry-type",
        targetEntry,
        `target entry ${metadata.targetEntryName} must be a real file for skill ${binding.skillId}`,
      ),
    );
  }
  return issues;
}

function unexpectedManagedTargetDirs(targetRoot, expectedTargetDirNames, targetChildren) {
  if (!isDirectory(targetRoot)) {
    return [];
  }
  const issues = [];
  for (const child of targetChildren) {
    const stat = lstatOrNull(child);
    if (stat === null || stat.isSymbolicLink() || !stat.isDirectory()) {
      continue;
    }
    if (expectedTargetDirNames.has(child.split(/[\\/]/).at(-1))) {
      continue;
    }
    const marker = loadRuntimeMarker(join(child, managedSkillMarker));
    if (marker === null || marker.backend !== "agents") {
      continue;
    }
    issues.push(
      issue(
        "unexpected-managed-directory",
        child,
        `recognized managed install for skill ${marker.skill_id} is not part of the current source bindings`,
      ),
    );
  }
  return issues;
}

function verifyAgentsBackend(context, options = {}) {
  const targetRoot = context.targetRoot;
  const issues = verifyTargetRoot(targetRoot);
  const bindings = options.bindings || collectSkillBindings(context);
  const loadedPayloads = options.loadedPayloads || null;
  if (bindings.length === 0) {
    issues.push(
      issue(
        "missing-backend-payload-source",
        context.adapterSkillsDir,
        "No payload bindings found for backend agents.",
      ),
    );
  } else {
    for (const binding of bindings) {
      issues.push(...verifySourceBinding(binding, context, loadedPayloads));
    }
  }

  let expectedTargetDirNames = new Set();
  if (issues.length === 0) {
    try {
      expectedTargetDirNames = expectedTargetDirs(bindings, loadedPayloads);
    } catch (error) {
      issues.push(issue("payload-contract-invalid", context.adapterSkillsDir, error.message));
    }
  }

  let children = null;
  if (issues.length === 0 && isDirectory(targetRoot)) {
    children = targetRootChildren(targetRoot);
    for (const binding of bindings) {
      issues.push(...verifyDeployedSkill(binding, targetRoot, context, loadedPayloads));
    }
    issues.push(...unexpectedManagedTargetDirs(targetRoot, expectedTargetDirNames, children));
  }

  return {
    backend: "agents",
    sourceRoot: context.sourceRoot,
    targetRoot,
    issues,
    bindings,
    targetChildren: children,
  };
}

function targetRootStatus(path) {
  const stat = lstatOrNull(path);
  if (stat === null) {
    return "missing";
  }
  if (stat.isSymbolicLink()) {
    return existsSync(path) ? "symlink" : "broken-symlink";
  }
  if (stat.isDirectory()) {
    return "directory";
  }
  return "wrong-type";
}

function managedInstallDirs(targetRoot, targetChildren) {
  if (!isDirectory(targetRoot)) {
    return [];
  }
  const children = targetChildren === null ? targetRootChildren(targetRoot) : targetChildren;
  return children.filter((child) => {
    const stat = lstatOrNull(child);
    if (stat === null || stat.isSymbolicLink() || !stat.isDirectory()) {
      return false;
    }
    const marker = loadRuntimeMarker(join(child, managedSkillMarker));
    return marker !== null && marker.backend === "agents";
  });
}

function collectUpdateTargetEntryIssues(targetRoot, knownTargetDirNames, targetChildren) {
  if (!isDirectory(targetRoot)) {
    return [];
  }
  const children = targetChildren === null ? targetRootChildren(targetRoot) : targetChildren;
  const issues = [];
  for (const child of children) {
    const childName = child.split(/[\\/]/).at(-1);
    if (!knownTargetDirNames.has(childName)) {
      continue;
    }

    const stat = lstatOrNull(child);
    if (stat === null || stat.isSymbolicLink() || !stat.isDirectory()) {
      issues.push(
        issue(
          "wrong-target-entry-type",
          child,
          "update target path must be a real directory before reinstall",
        ),
      );
      continue;
    }

    const marker = loadRuntimeMarker(join(child, managedSkillMarker));
    if (marker === null) {
      issues.push(
        issue(
          "unrecognized-target-directory",
          child,
          "update will not remove target directories without a recognized marker",
        ),
      );
      continue;
    }

    if (marker.backend !== "agents") {
      issues.push(
        issue(
          "foreign-managed-directory",
          child,
          `update will not remove managed directory for backend ${marker.backend}`,
        ),
      );
    }
  }
  return issues;
}

function dedupeIssues(issues) {
  const seen = new Set();
  const uniqueIssues = [];
  for (const currentIssue of issues) {
    const key = `${currentIssue.code}\0${currentIssue.path}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    uniqueIssues.push(currentIssue);
  }
  return uniqueIssues;
}

function buildInstallPlan(binding, targetRoot, context, loadedPayloads = null, targetMetadata = null) {
  const loadedPayload = bindingPayloadWithText(binding, loadedPayloads);
  const resolvedTargetMetadata = targetMetadata || payloadTargetMetadata(loadedPayload.payload, binding);
  const payloadFingerprint = computePayloadFingerprint(
    binding,
    context,
    loadedPayload.payload,
    loadedPayload.payloadText,
    resolvedTargetMetadata,
  );
  return {
    binding,
    targetMetadata: resolvedTargetMetadata,
    targetSkillDir: join(targetRoot, resolvedTargetMetadata.targetDir),
    payloadFingerprint,
  };
}

function isUpdateBlockingIssue(currentIssue, managedDeletePaths) {
  if (updateRecoverableIssueCodes.has(currentIssue.code)) {
    return false;
  }
  if (currentIssue.code === "unrecognized-target-directory" && managedDeletePaths.has(currentIssue.path)) {
    return false;
  }
  return true;
}

function updatePlanSummary(context) {
  const bindings = collectSkillBindings(context);
  let loadedPayloads = null;
  try {
    loadedPayloads = loadBindingPayloads(bindings);
  } catch (error) {
    loadedPayloads = null;
  }
  const result = verifyAgentsBackend(context, { bindings, loadedPayloads });
  const targetRoot = result.targetRoot;
  const targetChildren =
    result.targetChildren === null && isDirectory(targetRoot) ? targetRootChildren(targetRoot) : result.targetChildren;

  const planIssues = [];
  let plans = [];
  let knownTargetDirNames = new Set();
  if (bindings.length === 0) {
    planIssues.push(
      issue(
        "missing-backend-payload-source",
        context.adapterSkillsDir,
        "No payload bindings found for backend agents.",
      ),
    );
  } else {
    try {
      const targetMetadata = collectTargetDirMetadata(bindings, loadedPayloads);
      knownTargetDirNames = knownTargetDirsFromMetadata(bindings, targetMetadata.metadataByPayloadPath);
      plans = bindings.map((binding) =>
        buildInstallPlan(
          binding,
          targetRoot,
          context,
          loadedPayloads,
          targetMetadata.metadataByPayloadPath.get(binding.payloadPath),
        ),
      );
    } catch (error) {
      planIssues.push(issue("payload-contract-invalid", context.adapterSkillsDir, error.message));
    }
  }

  const targetEntryIssues = collectUpdateTargetEntryIssues(targetRoot, knownTargetDirNames, targetChildren);
  const managedInstallsToDelete = managedInstallDirs(targetRoot, targetChildren);
  const managedDeletePaths = new Set(managedInstallsToDelete);
  const allIssues = dedupeIssues([...result.issues, ...planIssues, ...targetEntryIssues]);
  const blockingIssues = allIssues.filter((currentIssue) => isUpdateBlockingIssue(currentIssue, managedDeletePaths));

  return {
    backend: "agents",
    source_kind: context.sourceKind,
    source_ref: context.sourceRef,
    source_root: context.sourceRoot,
    target_root: targetRoot,
    operation_sequence: ["prune --all", "check_paths_exist", "install", "verify"],
    managed_installs_to_delete: managedInstallsToDelete,
    planned_target_paths: plans.map((plan) => plan.targetSkillDir),
    issue_count: allIssues.length,
    issues: allIssues,
    blocking_issue_count: blockingIssues.length,
    blocking_issues: blockingIssues,
  };
}

function diagnosticSummary(result) {
  const managedDirs = managedInstallDirs(result.targetRoot, result.targetChildren);
  const issueCodes = [...new Set(result.issues.map((currentIssue) => currentIssue.code))].sort();
  const unrecognized = result.issues.filter((currentIssue) => unrecognizedIssueCodes.has(currentIssue.code));
  const conflicts = result.issues.filter((currentIssue) => conflictIssueCodes.has(currentIssue.code));
  return {
    backend: "agents",
    source_root: result.sourceRoot,
    target_root: result.targetRoot,
    target_root_status: targetRootStatus(result.targetRoot),
    target_root_exists: pathExists(result.targetRoot),
    binding_count: result.bindings.length,
    managed_install_count: managedDirs.length,
    managed_installs: managedDirs,
    issue_count: result.issues.length,
    issue_codes: issueCodes,
    issues: result.issues,
    unrecognized_count: unrecognized.length,
    unrecognized,
    conflict_count: conflicts.length,
    conflicts,
  };
}

function parseNodeDiagnoseJsonArgs(args) {
  if (args[0] !== "diagnose") {
    return null;
  }
  let backend = "agents";
  let json = false;
  for (let index = 1; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--json") {
      json = true;
      continue;
    }
    if (arg === "--backend") {
      if (index + 1 >= args.length) {
        return null;
      }
      backend = args[index + 1];
      index += 1;
      continue;
    }
    if (arg.startsWith("--backend=")) {
      backend = arg.slice("--backend=".length);
      continue;
    }
    return null;
  }
  if (!json || backend !== "agents") {
    return null;
  }
  return { backend };
}

function parseNodeUpdateJsonArgs(args) {
  if (args[0] !== "update") {
    return null;
  }
  let backend = "agents";
  let json = false;
  let source = "package";
  for (let index = 1; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--json") {
      json = true;
      continue;
    }
    if (arg === "--backend") {
      if (index + 1 >= args.length) {
        return null;
      }
      backend = args[index + 1];
      index += 1;
      continue;
    }
    if (arg.startsWith("--backend=")) {
      backend = arg.slice("--backend=".length);
      continue;
    }
    if (arg === "--source") {
      if (index + 1 >= args.length) {
        return null;
      }
      source = args[index + 1];
      index += 1;
      continue;
    }
    if (arg.startsWith("--source=")) {
      source = arg.slice("--source=".length);
      continue;
    }
    return null;
  }
  if (!json || backend !== "agents" || source !== "package") {
    return null;
  }
  return { backend, source };
}

function runNodeDiagnoseJson(args) {
  if (parseNodeDiagnoseJsonArgs(args) === null) {
    return null;
  }
  try {
    const context = buildNodeDiagnoseContext();
    const result = verifyAgentsBackend(context);
    console.log(JSON.stringify(diagnosticSummary(result), null, 2));
    return 0;
  } catch (error) {
    console.error(error.message);
    return 1;
  }
}

function runNodeUpdateJson(args) {
  if (parseNodeUpdateJsonArgs(args) === null) {
    return null;
  }
  try {
    const context = buildNodeAgentsContext();
    const summary = updatePlanSummary(context);
    console.log(JSON.stringify(summary, null, 2));
    return summary.blocking_issue_count ? 1 : 0;
  } catch (error) {
    console.error(error.message);
    return 1;
  }
}

function runWrapperWithCandidate(args, candidate) {
  return new Promise((resolve) => {
    const abortController = new AbortController();
    // The child can emit both error and close; settle once and keep timeout reporting distinct.
    let timedOut = false;
    let settled = false;
    const finish = (status) => {
      if (settled) {
        return false;
      }
      settled = true;
      clearTimeout(timer);
      resolve(status);
      return true;
    };
    const timeoutSeconds = Math.ceil(wrapperTimeoutMs / 1000);
    const timer = setTimeout(() => {
      timedOut = true;
      abortController.abort();
    }, wrapperTimeoutMs);
    if (typeof timer.unref === "function") {
      timer.unref();
    }

    let child;
    try {
      child = spawn(candidate.command, [...candidate.args, wrapperPath, ...args], {
        env,
        signal: abortController.signal,
        stdio: "inherit",
      });
    } catch (error) {
      clearTimeout(timer);
      if (error.code === "ENOENT") {
        resolve({ status: 1, missing: true, error });
        return;
      }
      console.error(
        `aw-installer failed to start ${formatPythonCandidate(candidate)}: ${error.message}`,
      );
      resolve({ status: 1, missing: false, error });
      return;
    }

    child.on("error", (error) => {
      if (timedOut || error.name === "AbortError") {
        if (finish({ status: 1, missing: false })) {
          console.error(`aw-installer timed out after ${timeoutSeconds}s`);
        }
        return;
      }
      if (error.code === "ENOENT") {
        if (settled) {
          return;
        }
        settled = true;
        clearTimeout(timer);
        resolve({ status: 1, missing: true, error });
        return;
      }
      if (!finish({ status: 1, missing: false, error })) {
        return;
      }
      console.error(
        `aw-installer failed to start ${formatPythonCandidate(candidate)}: ${error.message}`,
      );
    });
    child.on("close", (code, signal) => {
      if (timedOut) {
        if (finish({ status: 1, missing: false })) {
          console.error(`aw-installer timed out after ${timeoutSeconds}s`);
        }
        return;
      }
      if (signal) {
        if (!finish({ status: 1, missing: false })) {
          return;
        }
        console.error(`aw-installer terminated by signal ${signal}`);
        return;
      }
      finish({ status: code === null ? 1 : code, missing: false });
    });
  });
}

async function runWrapper(args) {
  const missingCandidates = [];
  for (const candidate of pythonCandidates()) {
    const result = await runWrapperWithCandidate(args, candidate);
    if (result.missing) {
      missingCandidates.push(formatPythonCandidate(candidate));
      continue;
    }
    return result.status;
  }
  console.error(
    `aw-installer failed to start Python; tried ${missingCandidates.join(", ")}`,
  );
  return 1;
}

function question(rl, prompt) {
  return new Promise((resolve) => {
    rl.question(prompt, resolve);
  });
}

async function pause(rl) {
  await question(rl, "\nPress Enter to return to the installer menu...");
}

async function runGuidedUpdateFlow(rl) {
  console.log("\nGuided update flow");
  console.log("Step 1: Diagnose current agents install.");
  const diagnoseStatus = await runWrapper(["diagnose", "--backend", "agents", "--json"]);
  if (diagnoseStatus !== 0) {
    console.log("Diagnose failed; update may not succeed as expected.");
    const proceed = (await question(
      rl,
      "Continue with update dry-run anyway? Type yes to continue: ",
    )).trim();
    if (proceed !== "yes") {
      console.log("Update cancelled.");
      await pause(rl);
      return;
    }
  }

  console.log("\nStep 2: Review update dry-run plan.");
  const dryRunStatus = await runWrapper(["update", "--backend", "agents"]);
  if (dryRunStatus !== 0) {
    console.log("Update plan failed; not applying.");
    await pause(rl);
    return;
  }

  const confirmation = (await question(
    rl,
    "Step 3: Type yes to apply update via prune --all -> check_paths_exist -> install -> verify: ",
  )).trim();
  if (confirmation === "yes") {
    console.log("\nStep 4: Applying update and running strict verify.");
    await runWrapper(["update", "--backend", "agents", "--yes"]);
  } else {
    console.log("Update cancelled.");
  }
  await pause(rl);
}

async function runTui() {
  if (!process.stdin.isTTY || !process.stdout.isTTY) {
    console.error("aw-installer tui requires an interactive terminal.");
    return 1;
  }

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  try {
    while (true) {
      console.log(`
AW Installer
Backend: agents

1. Guided update flow
2. Diagnose current install
3. Verify current install
4. Show update dry-run plan
5. Show CLI help
6. Exit
`);
      const choice = (await question(rl, "Select an action: ")).trim().toLowerCase();

      if (choice === "1") {
        await runGuidedUpdateFlow(rl);
      } else if (choice === "2") {
        await runWrapper(["diagnose", "--backend", "agents", "--json"]);
        await pause(rl);
      } else if (choice === "3") {
        await runWrapper(["verify", "--backend", "agents"]);
        await pause(rl);
      } else if (choice === "4") {
        await runWrapper(["update", "--backend", "agents"]);
        await pause(rl);
      } else if (choice === "5") {
        printHelp();
        await pause(rl);
      } else if (choice === "6" || choice === "q" || choice === "quit" || choice === "exit") {
        return 0;
      } else {
        console.log("Unknown selection.");
      }
    }
  } finally {
    rl.close();
  }
}

async function main() {
  const args = process.argv.slice(2);

  // P0-035 slices: selected agents JSON dry-run paths are Node-owned and
  // read-only. Other deploy modes and unsupported variants stay on the Python
  // reference path until their adapter_deploy.py contracts are migrated.
  if (args.length === 0) {
    if (process.stdin.isTTY && process.stdout.isTTY) {
      return runTui();
    }
    printHelp();
    return 0;
  }

  if (args[0] === "--help" || args[0] === "-h") {
    printHelp();
    return 0;
  }

  if (args[0] === "--version" || args[0] === "-V") {
    printVersion();
    return 0;
  }

  if (args[0] === "tui") {
    return runTui();
  }

  const nodeDiagnoseStatus = runNodeDiagnoseJson(args);
  if (nodeDiagnoseStatus !== null) {
    return nodeDiagnoseStatus;
  }

  const nodeUpdateStatus = runNodeUpdateJson(args);
  if (nodeUpdateStatus !== null) {
    return nodeUpdateStatus;
  }

  return await runWrapper(args);
}

if (require.main === module) {
  main()
    .then((status) => {
      process.exit(status);
    })
    .catch((error) => {
      console.error(`aw-installer failed: ${error.message}`);
      process.exit(1);
    });
}

module.exports = {
  allKnownTargetDirs,
  buildInstallPlan,
  canonicalSourceMetadata,
  collectTargetDirMetadata,
  collectUpdateTargetEntryIssues,
  computePayloadFingerprint,
  dedupeIssues,
  exactSensitiveTargetRepoRoots,
  expectedTargetDirs,
  isUpdateBlockingIssue,
  loadBindingPayloads,
  loadRuntimeMarker,
  normalizeRelativePath,
  parseNodeDiagnoseJsonArgs,
  parseNodeUpdateJsonArgs,
  pathSafetyPolicy,
  payloadTargetMetadata,
  pythonCandidates,
  recursiveSensitiveTargetRepoRoots,
  resolveExistingOrLexical,
  updatePlanSummary,
  validateSourceRepoRoot,
  validateTargetRepoRoot,
  verifyAgentsBackend,
  verifyDeployedSkill,
};
