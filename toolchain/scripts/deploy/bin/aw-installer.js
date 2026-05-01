#!/usr/bin/env node
"use strict";

const { spawn } = require("node:child_process");
const {
  chmodSync,
  closeSync,
  constants,
  existsSync,
  fstatSync,
  lstatSync,
  mkdirSync,
  openSync,
  readFileSync,
  readdirSync,
  realpathSync,
  rmSync,
  writeFileSync,
} = require("node:fs");
const { basename, dirname, isAbsolute, join, relative, resolve, sep } = require("node:path");
const { createHash } = require("node:crypto");
const readline = require("node:readline");

const wrapperPath = join(__dirname, "..", "harness_deploy.py");
const pathSafetyPolicyPath = join(__dirname, "..", "path_safety_policy.json");
const defaultWrapperTimeoutMs = 300_000;
const wrapperTimeoutMs = readWrapperTimeoutMs();
const maxJsonPayloadBytes = 1_048_576;
const env = buildWrapperEnv(process.env);
const packageVersionFallbackMaxDepth = 20;
const payloadDescriptor = "payload.json";
const managedSkillMarker = "aw.marker";
const managedSkillMarkerVersion = "aw-managed-skill-marker.v2";
const expectedPayloadVersion = "agents-skill-payload.v1";
const deployedFileMode = 0o644;
const deployedDirMode = 0o755;
const unrecognizedIssueCodes = new Set(["unrecognized-target-directory"]);
// Diagnose treats these as conflict signals for operator visibility. Update
// may still recover selected conflicts when prune --all can remove them safely.
const conflictIssueCodes = new Set([
  "unexpected-managed-directory",
  "unrecognized-target-directory",
  "wrong-target-entry-type",
]);
// These states are expected to be repaired by the destructive reinstall
// sequence. unexpected-managed-directory is also a diagnose conflict, but
// update can recover it because the recognized marker lets prune --all own it.
// Type/safety violations still block because update must not guess.
const updateRecoverableIssueCodes = new Set([
  "missing-target-root",
  "missing-target-entry",
  "missing-required-payload",
  "target-payload-drift",
  "unexpected-managed-directory",
]);
let cachedPathSafetyPolicy = null;

function buildWrapperEnv(sourceEnv) {
  const passThroughNames = new Set([
    "AW_HARNESS_REPO_ROOT",
    "AW_HARNESS_TARGET_REPO_ROOT",
    "AW_INSTALLER_GITHUB_REPO",
    "ComSpec",
    "GITHUB_REPOSITORY",
    "HOME",
    "LANG",
    "LC_ALL",
    "PATH",
    "PATHEXT",
    "PYTHONDONTWRITEBYTECODE",
    "REQUESTS_CA_BUNDLE",
    "SSL_CERT_DIR",
    "SSL_CERT_FILE",
    "SystemRoot",
    "TEMP",
    "TMP",
    "TMPDIR",
    "USERPROFILE",
    "WINDIR",
  ]);
  const nextEnv = {};
  for (const [key, value] of Object.entries(sourceEnv)) {
    if (
      passThroughNames.has(key) ||
      key.toLowerCase() === "http_proxy" ||
      key.toLowerCase() === "https_proxy" ||
      key.toLowerCase() === "no_proxy"
    ) {
      nextEnv[key] = value;
    }
  }
  nextEnv.PYTHONDONTWRITEBYTECODE = sourceEnv.PYTHONDONTWRITEBYTECODE || "1";
  return nextEnv;
}

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
    if (error.code === "ENOENT" || error.code === "EACCES" || error.code === "EPERM") {
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

function validateNotSensitiveRepoRoot(resolved, subject, action) {
  for (const sensitiveRoot of exactSensitiveTargetRepoRoots()) {
    if (resolved === sensitiveRoot) {
      throw new Error(`${subject} is protected and cannot be ${action}: ${resolved}`);
    }
  }
  for (const sensitiveRoot of recursiveSensitiveTargetRepoRoots()) {
    if (resolved === sensitiveRoot || pathIsRelativeTo(resolved, sensitiveRoot)) {
      throw new Error(`${subject} is protected and cannot be ${action}: ${resolved}`);
    }
  }
}

function validateTargetRepoRoot(path, sourceRoot) {
  const resolved = resolveExistingOrLexical(path);
  validateNotSensitiveRepoRoot(resolved, "Target repo root", "managed");

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
  validateNotSensitiveRepoRoot(resolved, "Source repo root", "used");

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

function buildNodeAgentsContext(options = {}) {
  const sourceRootFromEnv = Boolean(process.env.AW_HARNESS_REPO_ROOT);
  const sourceRoot = resolveSourceRoot();
  const targetRepoRoot = resolveTargetRepoRoot(sourceRoot, sourceRootFromEnv);
  const targetRoot =
    options.agentsRoot === undefined
      ? join(targetRepoRoot, ".agents", "skills")
      : validateTargetRepoRoot(options.agentsRoot, sourceRoot);
  return {
    sourceKind: "package",
    sourceRef: "package-local",
    sourceRoot,
    targetRepoRoot,
    targetRoot,
    adapterSkillsDir: join(sourceRoot, "product", "harness", "adapters", "agents", "skills"),
  };
}

function isDirectory(path) {
  const stat = lstatOrNull(path);
  return stat !== null && !stat.isSymbolicLink() && stat.isDirectory();
}

function isFile(path) {
  const stat = lstatOrNull(path);
  return stat !== null && !stat.isSymbolicLink() && stat.isFile();
}

function readRegularFileText(path) {
  const noFollowFlag = constants.O_NOFOLLOW || 0;
  let fd = null;
  try {
    fd = openSync(path, constants.O_RDONLY | noFollowFlag);
    const stat = fstatSync(fd);
    if (!stat.isFile()) {
      const error = new Error(`Path is not a regular file: ${path}`);
      error.code = "ENOTREG";
      throw error;
    }
    return readFileSync(fd, "utf8");
  } catch (error) {
    if (error.code === "ELOOP") {
      const regularFileError = new Error(`Path is not a regular file: ${path}`);
      regularFileError.code = "ENOTREG";
      throw regularFileError;
    }
    throw error;
  } finally {
    if (fd !== null) {
      closeSync(fd);
    }
  }
}

function readJsonText(path, missingMessage) {
  let stat;
  try {
    stat = lstatSync(path);
  } catch (error) {
    if (error.code === "ENOENT" && missingMessage) {
      throw new Error(missingMessage);
    }
    throw error;
  }
  if (!stat.isFile()) {
    throw new Error(`JSON payload must be a real file: ${path}`);
  }
  if (stat.size > maxJsonPayloadBytes) {
    throw new Error(
      `JSON payload exceeds ${maxJsonPayloadBytes} byte limit: ${path}`,
    );
  }
  return readFileSync(path, "utf8");
}

function readJsonObject(path) {
  let data;
  try {
    data = JSON.parse(readJsonText(path));
  } catch (error) {
    throw new Error(`Invalid JSON in ${path}: ${error.message}`);
  }
  if (data === null || Array.isArray(data) || typeof data !== "object") {
    throw new Error(`JSON payload must be an object: ${path}`);
  }
  return data;
}

function readJsonObjectWithText(path) {
  const text = readJsonText(path, `Missing JSON file: ${path}`);
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
  if (value.includes("\0")) {
    throw new Error(`${fieldName} must not contain null bytes for skill ${skillId}: ${value}`);
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

class PayloadLoadError extends Error {
  constructor(binding, cause) {
    super(cause.message, { cause });
    this.name = "PayloadLoadError";
    this.payloadPath = binding.payloadPath;
  }
}

/**
 * Preloads payload JSON and original text by payload path for one deploy pass.
 */
function loadBindingPayloads(bindings) {
  const loadedPayloads = new Map();
  for (const binding of bindings) {
    try {
      loadedPayloads.set(binding.payloadPath, bindingPayloadWithText(binding, null));
    } catch (error) {
      throw new PayloadLoadError(binding, error);
    }
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

function sourcePathForTargetRelativeFile(binding, relativeName, context, payload, canonicalSource = null) {
  if (relativeName === payloadDescriptor) {
    return binding.payloadPath;
  }
  if (relativeName === managedSkillMarker) {
    throw new Error(`${managedSkillMarker} is runtime-generated for skill ${binding.skillId}`);
  }
  const resolvedCanonicalSource = canonicalSource || canonicalSourceMetadata(payload, binding, context);
  const sourcePath = resolvedCanonicalSource.canonicalFiles.get(relativeName);
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
  let canonicalSource = null;
  for (const relativeName of metadata.requiredPayloadFiles) {
    if (relativeName === managedSkillMarker || relativeName === payloadDescriptor) {
      continue;
    }
    if (canonicalSource === null) {
      canonicalSource = canonicalSourceMetadata(payload, binding, context);
    }
    const sourcePath = sourcePathForTargetRelativeFile(
      binding,
      relativeName,
      context,
      payload,
      canonicalSource,
    );
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

function buildRuntimeMarker(backend, skillId, payloadVersion, payloadFingerprint) {
  return {
    marker_version: managedSkillMarkerVersion,
    backend,
    skill_id: skillId,
    payload_version: payloadVersion,
    payload_fingerprint: payloadFingerprint,
  };
}

function targetRootChildren(targetRoot, action = "verify target root") {
  try {
    return readdirSync(targetRoot, { withFileTypes: true })
      .map((entry) => join(targetRoot, entry.name))
      .sort();
  } catch (error) {
    throw new Error(`Failed to scan ${action} at ${targetRoot}: ${error.message}`);
  }
}

function targetRootIdentity(path) {
  let stat;
  try {
    stat = lstatSync(path);
  } catch (error) {
    if (error.code === "ENOENT") {
      throw new Error(`Target root does not exist: ${path}`);
    }
    throw error;
  }
  if (stat.isSymbolicLink()) {
    if (existsSync(path)) {
      throw new Error(`Target root must be a real directory, not a symlink: ${path}`);
    }
    throw new Error(`Target root is a broken symlink: ${path}`);
  }
  if (!stat.isDirectory()) {
    throw new Error(`Target root exists but is not a directory: ${path}`);
  }
  return { path, dev: stat.dev, ino: stat.ino };
}

function assertDirectoryIdentityCurrent(identity, action) {
  let stat;
  try {
    stat = lstatSync(identity.path);
  } catch (error) {
    if (error.code === "ENOENT") {
      throw new Error(`Target root changed during ${action}, refusing to continue: ${identity.path}`);
    }
    throw error;
  }
  if (stat.dev !== identity.dev || stat.ino !== identity.ino || stat.isSymbolicLink() || !stat.isDirectory()) {
    throw new Error(`Target root changed during ${action}, refusing to continue: ${identity.path}`);
  }
}

function ensureInstallTargetRoot(path) {
  if (pathExists(path) || lstatOrNull(path)?.isSymbolicLink()) {
    const identity = targetRootIdentity(path);
    console.log(`ready target root ${path}`);
    return identity;
  }
  try {
    mkdirSync(dirname(path), { recursive: true, mode: deployedDirMode });
    mkdirSync(path, { mode: deployedDirMode });
  } catch (error) {
    if (error.code === "EEXIST") {
      const identity = targetRootIdentity(path);
      console.log(`ready target root ${path}`);
      return identity;
    }
    throw new Error(`Target root could not be created: ${path}: ${error.message}`);
  }
  const identity = targetRootIdentity(path);
  console.log(`created target root ${path}`);
  return identity;
}

/**
 * Resolves each binding target metadata and rejects duplicate live target dirs.
 */
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

/**
 * Collects live and legacy target dir names that update may recognize.
 */
function collectAllKnownTargetDirs(bindings, loadedPayloads = null) {
  const { metadataByPayloadPath } = collectTargetDirMetadata(bindings, loadedPayloads);
  return knownTargetDirsFromMetadata(bindings, metadataByPayloadPath);
}

function loadDeployedSkillState(binding, targetRoot, context, loadedPayloads) {
  try {
    const loadedPayload = bindingPayloadWithText(binding, loadedPayloads);
    const payload = loadedPayload.payload;
    const metadata = payloadTargetMetadata(payload, binding);
    return {
      payload,
      metadata,
      payloadFingerprint: computePayloadFingerprint(
        binding,
        context,
        payload,
        loadedPayload.payloadText,
        metadata,
      ),
      targetSkillDir: join(targetRoot, metadata.targetDir),
    };
  } catch (error) {
    return {
      issues: [issue("payload-contract-invalid", binding.payloadPath, error.message)],
    };
  }
}

function verifyDeployedSkillDirectory(binding, targetSkillDir) {
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
  return [];
}

function verifyDeployedMarker(binding, targetSkillDir, payload, payloadFingerprint) {
  const marker = loadRuntimeMarker(join(targetSkillDir, managedSkillMarker));
  if (marker === null) {
    return {
      fatalIssues: [
        issue(
          "unrecognized-target-directory",
          targetSkillDir,
          `existing deployed directory has no recognized ${managedSkillMarker}`,
        ),
      ],
    };
  }
  if (marker.backend !== "agents" || marker.skill_id !== binding.skillId || marker.payload_version !== payload.payload_version) {
    return {
      fatalIssues: [
        issue(
          "unrecognized-target-directory",
          targetSkillDir,
          `recognized ${managedSkillMarker} does not match current backend/skill/payload_version`,
        ),
      ],
    };
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
  return {
    expectedMarker,
    issues,
    markerMatchesSource,
  };
}

function targetPayloadReadIssue(error, targetPath, relativeName, binding) {
  if (error.code === "ENOENT") {
    return issue(
      "missing-required-payload",
      targetPath,
      `missing deployed payload file ${relativeName} for skill ${binding.skillId}`,
    );
  }
  if (error.code === "ENOTREG" || error.code === "EISDIR") {
    return issue(
      "wrong-target-entry-type",
      targetPath,
      `deployed payload file ${relativeName} must be a real file for skill ${binding.skillId}`,
    );
  }
  return issue(
    "target-payload-drift",
    targetPath,
    `could not read deployed payload file ${relativeName} for skill ${binding.skillId}: ${error.message}`,
  );
}

function verifyDeployedPayloadFiles(binding, targetSkillDir, context, payload, metadata, markerState) {
  const issues = [];
  let canonicalSource = null;
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
      let markerText;
      try {
        markerText = readRegularFileText(targetPath);
      } catch (error) {
        issues.push(targetPayloadReadIssue(error, targetPath, relativeName, binding));
        continue;
      }
      if (markerState.markerMatchesSource && markerText !== runtimeMarkerText(markerState.expectedMarker)) {
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
      if (relativeName !== payloadDescriptor && canonicalSource === null) {
        canonicalSource = canonicalSourceMetadata(payload, binding, context);
      }
      sourcePath =
        relativeName === payloadDescriptor
          ? binding.payloadPath
          : sourcePathForTargetRelativeFile(binding, relativeName, context, payload, canonicalSource);
    } catch (error) {
      issues.push(issue("payload-contract-invalid", binding.payloadPath, error.message));
      continue;
    }
    let sourceText;
    let targetText;
    try {
      sourceText = readFileSync(sourcePath, "utf8");
    } catch (error) {
      issues.push(issue("payload-contract-invalid", binding.payloadPath, error.message));
      continue;
    }
    try {
      targetText = readRegularFileText(targetPath);
    } catch (error) {
      issues.push(targetPayloadReadIssue(error, targetPath, relativeName, binding));
      continue;
    }
    if (sourceText !== targetText) {
      issues.push(
        issue(
          "target-payload-drift",
          targetPath,
          `deployed payload file ${relativeName} drifted from adapter source for skill ${binding.skillId}`,
        ),
      );
    }
  }
  return issues;
}

function verifyDeployedTargetEntry(binding, targetSkillDir, metadata) {
  const targetEntry = join(targetSkillDir, metadata.targetEntryName);
  if (!pathExists(targetEntry)) {
    return [
      issue(
        "missing-target-entry",
        targetEntry,
        `missing target entry ${metadata.targetEntryName} for skill ${binding.skillId}`,
      ),
    ];
  }
  if (!isFile(targetEntry)) {
    return [
      issue(
        "wrong-target-entry-type",
        targetEntry,
        `target entry ${metadata.targetEntryName} must be a real file for skill ${binding.skillId}`,
      ),
    ];
  }
  return [];
}

function verifyDeployedSkill(binding, targetRoot, context, loadedPayloads = null) {
  const state = loadDeployedSkillState(binding, targetRoot, context, loadedPayloads);
  if (state.issues) {
    return state.issues;
  }

  const directoryIssues = verifyDeployedSkillDirectory(binding, state.targetSkillDir);
  if (directoryIssues.length > 0) {
    return directoryIssues;
  }

  const markerState = verifyDeployedMarker(
    binding,
    state.targetSkillDir,
    state.payload,
    state.payloadFingerprint,
  );
  if (markerState.fatalIssues) {
    return markerState.fatalIssues;
  }

  return [
    ...markerState.issues,
    ...verifyDeployedPayloadFiles(
      binding,
      state.targetSkillDir,
      context,
      state.payload,
      state.metadata,
      markerState,
    ),
    ...verifyDeployedTargetEntry(binding, state.targetSkillDir, state.metadata),
  ];
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

/**
 * Verifies the agents backend using optional pre-collected bindings/payloads.
 */
function verifyAgentsBackend(context, options = {}) {
  const targetRoot = context.targetRoot;
  const issues = verifyTargetRoot(targetRoot);
  const bindings = options.bindings ?? collectSkillBindings(context);
  const loadedPayloads = options.loadedPayloads ?? null;
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

function targetRootReadyIssuesForAction(targetRoot) {
  return verifyTargetRoot(targetRoot).filter((currentIssue) => currentIssue.code !== "missing-target-root");
}

function childDirectoryIdentity(path) {
  const stat = lstatOrNull(path);
  if (stat === null || stat.isSymbolicLink() || !stat.isDirectory()) {
    return null;
  }
  return { path, dev: stat.dev, ino: stat.ino };
}

function assertManagedDirectoryIdentityCurrent(identity) {
  const stat = lstatOrNull(identity.path);
  if (stat === null) {
    return false;
  }
  if (stat.dev !== identity.dev || stat.ino !== identity.ino || stat.isSymbolicLink() || !stat.isDirectory()) {
    throw new Error(`Managed skill dir changed during pruning, refusing to remove: ${identity.path}`);
  }
  return true;
}

function pruneBackendManagedInstalls(context) {
  const targetRootIssues = targetRootReadyIssuesForAction(context.targetRoot);
  if (targetRootIssues.length > 0) {
    throw new Error(targetRootReadyFailureMessage("prune managed installs", targetRootIssues));
  }

  if (!pathExists(context.targetRoot)) {
    console.log(`no managed skill dirs found at ${context.targetRoot}`);
    return 0;
  }

  let removedCount = 0;
  for (const child of targetRootChildren(context.targetRoot, "managed install pruning")) {
    const identity = childDirectoryIdentity(child);
    if (identity === null) {
      continue;
    }

    const marker = loadRuntimeMarker(join(child, managedSkillMarker));
    if (marker === null || marker.backend !== "agents") {
      continue;
    }

    if (!assertManagedDirectoryIdentityCurrent(identity)) {
      continue;
    }

    try {
      rmSync(child, { recursive: true });
    } catch (error) {
      throw new Error(`Failed to remove managed skill dir ${child}: ${error.message}`);
    }
    removedCount += 1;
    console.log(`removed managed skill dir ${child}`);
  }

  if (removedCount === 0) {
    console.log(`no managed skill dirs found at ${context.targetRoot}`);
  }
  return removedCount;
}

/**
 * Finds existing target entries that update must refuse or classify before prune.
 */
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

function pathExistsOrIsSymlink(path) {
  return lstatOrNull(path) !== null;
}

function describeExistingTargetPath(path) {
  const stat = lstatOrNull(path);
  if (stat === null) {
    return "existing target path already exists";
  }
  if (stat.isSymbolicLink()) {
    return existsSync(path)
      ? "existing target path is a symlink"
      : "existing target path is a broken symlink";
  }
  if (stat.isDirectory()) {
    return "existing target path is a directory";
  }
  if (stat.isFile()) {
    return "existing target path is a file";
  }
  return "existing target path already exists";
}

function pathConflict(skillId, path, detail) {
  return { skillId, path, detail };
}

function collectPathConflicts(plans) {
  const conflicts = [];
  for (const plan of plans) {
    if (!pathExistsOrIsSymlink(plan.targetSkillDir)) {
      continue;
    }
    conflicts.push(
      pathConflict(
        plan.binding.skillId,
        plan.targetSkillDir,
        describeExistingTargetPath(plan.targetSkillDir),
      ),
    );
  }
  return conflicts;
}

function collectLegacyPathConflicts(plans, targetRoot) {
  const conflicts = [];
  for (const plan of plans) {
    for (const legacyDirName of plan.targetMetadata.legacyTargetDirs) {
      const legacyPath = join(targetRoot, legacyDirName);
      if (!pathExists(legacyPath)) {
        continue;
      }
      const marker = loadRuntimeMarker(join(legacyPath, managedSkillMarker));
      if (
        marker !== null &&
        marker.backend === plan.binding.backend &&
        (marker.skill_id === plan.binding.skillId ||
          plan.targetMetadata.legacySkillIds.includes(marker.skill_id))
      ) {
        continue;
      }
      conflicts.push(
        pathConflict(
          plan.binding.skillId,
          legacyPath,
          `legacy directory ${legacyDirName} is occupied by unmanaged content`,
        ),
      );
    }
  }
  return conflicts;
}

function formatPathConflicts(conflicts) {
  return [
    "target path conflicts:",
    ...conflicts.map((conflict) => `- ${conflict.skillId}: ${conflict.path} (${conflict.detail})`),
  ].join("\n");
}

function sourceValidationFailureMessage(action, issues) {
  const details = issues
    .map((currentIssue) => `  - ${currentIssue.code}: ${currentIssue.path} (${currentIssue.detail})`)
    .join("\n");
  return `Cannot ${action} because source validation failed:\n${details}`;
}

function targetRootReadyFailureMessage(action, issues) {
  const details = issues
    .map((currentIssue) => `  - ${currentIssue.code}: ${currentIssue.path} (${currentIssue.detail})`)
    .join("\n");
  return `Cannot ${action} because target root is not ready:\n${details}`;
}

function collectValidatedBindingsForAction(context, action) {
  const bindings = collectSkillBindings(context);
  if (bindings.length === 0) {
    throw new Error("No payload bindings found for backend agents.");
  }

  const validationIssues = [];
  for (const binding of bindings) {
    validationIssues.push(...verifySourceBinding(binding, context));
  }
  if (validationIssues.length > 0) {
    throw new Error(sourceValidationFailureMessage(action, validationIssues));
  }
  const loadedPayloads = loadBindingPayloads(bindings);
  return { bindings, loadedPayloads };
}

function collectValidatedBindingsForCheckPaths(context) {
  return collectValidatedBindingsForAction(context, "check target paths");
}

function checkPathsExistSummary(context) {
  const { bindings, loadedPayloads } = collectValidatedBindingsForCheckPaths(context);
  const targetRootIssues = verifyTargetRoot(context.targetRoot).filter(
    (currentIssue) => currentIssue.code !== "missing-target-root",
  );
  if (targetRootIssues.length > 0) {
    throw new Error(targetRootReadyFailureMessage("check target paths", targetRootIssues));
  }

  const targetMetadata = collectTargetDirMetadata(bindings, loadedPayloads);
  const plans = bindings.map((binding) =>
    buildInstallPlan(binding, context.targetRoot, context, {
      loadedPayloads,
      targetMetadata: targetMetadata.metadataByPayloadPath.get(binding.payloadPath),
    }),
  );
  const conflicts = [
    ...collectPathConflicts(plans),
    ...collectLegacyPathConflicts(plans, context.targetRoot),
  ];
  return {
    backend: "agents",
    targetRoot: context.targetRoot,
    plannedTargetPaths: plans.map((plan) => plan.targetSkillDir),
    conflicts,
  };
}

function targetRootIsCleanForNodeInstall(targetRoot) {
  const stat = lstatOrNull(targetRoot);
  if (stat === null) {
    return true;
  }
  if (!stat.isDirectory() || stat.isSymbolicLink()) {
    return true;
  }
  return targetRootChildren(targetRoot).length === 0;
}

function writeDeployedTextFile(path, text) {
  writeFileSync(path, text, "utf8");
  chmodSync(path, deployedFileMode);
}

function sourceTextForTargetRelativeFile(binding, relativeName, context, payload, loadedPayload, canonicalSource) {
  if (relativeName === payloadDescriptor) {
    return loadedPayload.payloadText;
  }
  const sourcePath = sourcePathForTargetRelativeFile(binding, relativeName, context, payload, canonicalSource);
  return readFileSync(sourcePath, "utf8");
}

function installBackendPayloads(context) {
  const { bindings, loadedPayloads } = collectValidatedBindingsForAction(context, "install");
  const targetRootIssues = verifyTargetRoot(context.targetRoot).filter(
    (currentIssue) => currentIssue.code !== "missing-target-root",
  );
  if (targetRootIssues.length > 0) {
    throw new Error(targetRootReadyFailureMessage("install", targetRootIssues));
  }

  const targetMetadata = collectTargetDirMetadata(bindings, loadedPayloads);
  const plans = bindings.map((binding) =>
    buildInstallPlan(binding, context.targetRoot, context, {
      loadedPayloads,
      targetMetadata: targetMetadata.metadataByPayloadPath.get(binding.payloadPath),
    }),
  );
  const conflicts = [
    ...collectPathConflicts(plans),
    ...collectLegacyPathConflicts(plans, context.targetRoot),
  ];
  if (conflicts.length > 0) {
    throw new Error(
      `[agents] install blocked by ${conflicts.length} existing target path(s)\n\n${formatPathConflicts(conflicts)}`,
    );
  }

  const targetRootIdentitySnapshot = ensureInstallTargetRoot(context.targetRoot);
  for (const plan of plans) {
    const binding = plan.binding;
    const loadedPayload = bindingPayloadWithText(binding, loadedPayloads);
    const payload = loadedPayload.payload;
    const targetSkillDir = plan.targetSkillDir;
    const targetMetadataForPlan = plan.targetMetadata;
    let canonicalSource = null;

    assertDirectoryIdentityCurrent(targetRootIdentitySnapshot, "install");
    mkdirSync(targetSkillDir, { mode: deployedDirMode });
    assertDirectoryIdentityCurrent(targetRootIdentitySnapshot, "install");
    chmodSync(targetSkillDir, deployedDirMode);

    for (const relativeName of targetMetadataForPlan.requiredPayloadFiles) {
      const targetPath = join(targetSkillDir, relativeName);
      assertDirectoryIdentityCurrent(targetRootIdentitySnapshot, "install");
      mkdirSync(dirname(targetPath), { recursive: true, mode: deployedDirMode });
      chmodSync(dirname(targetPath), deployedDirMode);
      assertDirectoryIdentityCurrent(targetRootIdentitySnapshot, "install");
      if (relativeName === managedSkillMarker) {
        writeDeployedTextFile(
          targetPath,
          runtimeMarkerText(
            buildRuntimeMarker(
              binding.backend,
              binding.skillId,
              payload.payload_version,
              plan.payloadFingerprint,
            ),
          ),
        );
        continue;
      }
      if (relativeName !== payloadDescriptor && canonicalSource === null) {
        canonicalSource = canonicalSourceMetadata(payload, binding, context);
      }
      writeDeployedTextFile(
        targetPath,
        sourceTextForTargetRelativeFile(binding, relativeName, context, payload, loadedPayload, canonicalSource),
      );
    }
    console.log(`installed skill ${binding.skillId} -> ${targetSkillDir}`);
  }
}

/**
 * Keeps the first issue for each code/path pair while preserving issue order.
 */
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

/**
 * Builds the dry-run install plan entry for one binding.
 */
function buildInstallPlan(binding, targetRoot, context, options = {}) {
  const loadedPayloads = options.loadedPayloads ?? null;
  const targetMetadata = options.targetMetadata ?? null;
  const includePayloadFingerprint = options.includePayloadFingerprint !== false;
  const resolvedTargetMetadata =
    targetMetadata || payloadTargetMetadata(bindingPayloadObject(binding, loadedPayloads), binding);
  const plan = {
    binding,
    targetMetadata: resolvedTargetMetadata,
    targetSkillDir: join(targetRoot, resolvedTargetMetadata.targetDir),
  };
  if (includePayloadFingerprint) {
    const loadedPayload = bindingPayloadWithText(binding, loadedPayloads);
    plan.payloadFingerprint = computePayloadFingerprint(
      binding,
      context,
      loadedPayload.payload,
      loadedPayload.payloadText,
      resolvedTargetMetadata,
    );
  }
  return plan;
}

/**
 * Classifies whether an issue should block the destructive reinstall wrapper.
 */
function isUpdateBlockingIssue(currentIssue, managedDeletePaths) {
  if (updateRecoverableIssueCodes.has(currentIssue.code)) {
    return false;
  }
  if (currentIssue.code === "unrecognized-target-directory" && managedDeletePaths.has(currentIssue.path)) {
    return false;
  }
  return true;
}

/**
 * Produces the agents update dry-run JSON summary without mutating target files.
 */
function updatePlanSummary(context) {
  const bindings = collectSkillBindings(context);
  let loadedPayloads = null;
  const preloadIssues = [];
  try {
    loadedPayloads = loadBindingPayloads(bindings);
  } catch (error) {
    preloadIssues.push(
      issue(
        "payload-contract-invalid",
        error.payloadPath || context.adapterSkillsDir,
        `failed to preload payloads: ${error.message}`,
      ),
    );
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
        buildInstallPlan(binding, targetRoot, context, {
          loadedPayloads,
          targetMetadata: targetMetadata.metadataByPayloadPath.get(binding.payloadPath),
          includePayloadFingerprint: false,
        }),
      );
    } catch (error) {
      planIssues.push(issue("payload-contract-invalid", context.adapterSkillsDir, error.message));
    }
  }

  const targetEntryIssues = collectUpdateTargetEntryIssues(targetRoot, knownTargetDirNames, targetChildren);
  const managedInstallsToDelete = managedInstallDirs(targetRoot, targetChildren);
  const managedDeletePaths = new Set(managedInstallsToDelete);
  const allIssues = dedupeIssues([...result.issues, ...planIssues, ...targetEntryIssues, ...preloadIssues]);
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

function sortJsonObjectKeys(value) {
  if (Array.isArray(value)) {
    return value.map((item) => sortJsonObjectKeys(item));
  }
  if (value === null || typeof value !== "object") {
    return value;
  }
  return Object.fromEntries(
    Object.keys(value)
      .sort()
      .map((key) => [key, sortJsonObjectKeys(value[key])]),
  );
}

function parseNodeJsonArgs(args, command, options = {}) {
  const allowSource = options.allowSource === true;
  if (args[0] !== command) {
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
    if (allowSource && arg === "--source") {
      if (index + 1 >= args.length) {
        return null;
      }
      source = args[index + 1];
      index += 1;
      continue;
    }
    if (allowSource && arg.startsWith("--source=")) {
      source = arg.slice("--source=".length);
      continue;
    }
    return null;
  }
  if (!json || backend !== "agents" || source !== "package") {
    return null;
  }
  return allowSource ? { backend, source } : { backend };
}

function parseNodeDiagnoseJsonArgs(args) {
  return parseNodeJsonArgs(args, "diagnose");
}

function parseNodeUpdateJsonArgs(args) {
  return parseNodeJsonArgs(args, "update", { allowSource: true });
}

function parseNodeUpdateYesArgs(args) {
  if (args[0] !== "update") {
    return null;
  }
  let backend = "agents";
  let source = "package";
  let yes = false;
  let agentsRoot;
  for (let index = 1; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--yes") {
      yes = true;
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
    if (arg === "--agents-root") {
      if (index + 1 >= args.length) {
        return null;
      }
      agentsRoot = args[index + 1];
      index += 1;
      continue;
    }
    if (arg.startsWith("--agents-root=")) {
      agentsRoot = arg.slice("--agents-root=".length);
      continue;
    }
    if (arg === "--claude-root") {
      if (index + 1 >= args.length) {
        return null;
      }
      index += 1;
      continue;
    }
    if (arg.startsWith("--claude-root=")) {
      continue;
    }
    return null;
  }
  if (!yes || backend !== "agents" || source !== "package") {
    return null;
  }
  return { backend, source, yes, agentsRoot };
}

function parseNodeCheckPathsExistArgs(args) {
  if (args[0] !== "check_paths_exist") {
    return null;
  }
  let backend = "agents";
  let agentsRoot;
  for (let index = 1; index < args.length; index += 1) {
    const arg = args[index];
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
    if (arg === "--agents-root") {
      if (index + 1 >= args.length) {
        return null;
      }
      agentsRoot = args[index + 1];
      index += 1;
      continue;
    }
    if (arg.startsWith("--agents-root=")) {
      agentsRoot = arg.slice("--agents-root=".length);
      continue;
    }
    if (arg === "--claude-root") {
      if (index + 1 >= args.length) {
        return null;
      }
      index += 1;
      continue;
    }
    if (arg.startsWith("--claude-root=")) {
      continue;
    }
    return null;
  }
  if (backend !== "agents") {
    return null;
  }
  return { backend, agentsRoot };
}

function runNodeJson(args, parser, buildSummary, exitStatus) {
  if (parser(args) === null) {
    return null;
  }
  try {
    const summary = buildSummary(buildNodeAgentsContext());
    console.log(JSON.stringify(sortJsonObjectKeys(summary), null, 2));
    return exitStatus(summary);
  } catch (error) {
    console.error(error.message);
    return 1;
  }
}

function runNodeDiagnoseJson(args) {
  return runNodeJson(
    args,
    parseNodeDiagnoseJsonArgs,
    (context) => diagnosticSummary(verifyAgentsBackend(context)),
    () => 0,
  );
}

function runNodeUpdateJson(args) {
  return runNodeJson(
    args,
    parseNodeUpdateJsonArgs,
    (context) => updatePlanSummary(context),
    (summary) => (summary.blocking_issue_count ? 1 : 0),
  );
}

function printUpdatePlan(summary) {
  console.log(`[${summary.backend}] update plan for ${summary.target_root}`);
  console.log(`sequence: ${summary.operation_sequence.join(" -> ")}`);
  console.log(`managed installs to delete: ${summary.managed_installs_to_delete.length}`);
  for (const currentPath of summary.managed_installs_to_delete) {
    console.log(`  - ${currentPath}`);
  }
  console.log(`target paths to write: ${summary.planned_target_paths.length}`);
  for (const currentPath of summary.planned_target_paths) {
    console.log(`  - ${currentPath}`);
  }
  console.log(`blocking preflight issues: ${summary.blocking_issue_count}`);
  for (const currentIssue of summary.blocking_issues) {
    console.log(`  - ${currentIssue.code}: ${currentIssue.path} (${currentIssue.detail})`);
  }
}

function updateFailureRecoveryHint(context) {
  return (
    `[agents] recovery: the update may be partially applied at ${context.targetRoot}. ` +
    "After fixing the reported error, run diagnose and then rerun " +
    "`aw-installer update --backend agents --yes`."
  );
}

function checkBackendTargetPaths(context) {
  const summary = checkPathsExistSummary(context);
  if (summary.conflicts.length > 0) {
    throw new Error(
      `[agents] found ${summary.conflicts.length} conflicting target path(s)\n\n${formatPathConflicts(summary.conflicts)}`,
    );
  }
  console.log(`[agents] ok: no conflicting target paths at ${summary.targetRoot}`);
}

function runNodeUpdateYes(args) {
  const parsed = parseNodeUpdateYesArgs(args);
  if (parsed === null) {
    return null;
  }
  try {
    const context = buildNodeAgentsContext(parsed);
    const summary = updatePlanSummary(context);
    printUpdatePlan(summary);
    if (summary.blocking_issue_count > 0) {
      throw new Error(`[agents] update blocked by ${summary.blocking_issue_count} preflight issue(s)`);
    }

    console.log("[agents] applying update");
    let result = null;
    try {
      pruneBackendManagedInstalls(context);
      checkBackendTargetPaths(context);
      installBackendPayloads(context);
      result = verifyAgentsBackend(context);
      if (result.issues.length > 0) {
        printVerifyResult(result);
        throw new Error(`[agents] update failed strict verify with ${result.issues.length} issue(s)`);
      }
    } catch (error) {
      throw new Error(`${error.message}\n${updateFailureRecoveryHint(context)}`);
    }
    printVerifyResult(result);
    console.log("[agents] update complete");
    return 0;
  } catch (error) {
    console.error(`error: ${error.message}`);
    return 1;
  }
}

function runNodeCheckPathsExist(args) {
  const parsed = parseNodeCheckPathsExistArgs(args);
  if (parsed === null) {
    return null;
  }
  try {
    const summary = checkPathsExistSummary(buildNodeAgentsContext(parsed));
    if (summary.conflicts.length > 0) {
      console.error(
        `error: [agents] found ${summary.conflicts.length} conflicting target path(s)\n\n${formatPathConflicts(summary.conflicts)}`,
      );
      return 1;
    }
    console.log(`[agents] ok: no conflicting target paths at ${summary.targetRoot}`);
    return 0;
  } catch (error) {
    console.error(`error: ${error.message}`);
    return 1;
  }
}

function parseNodeVerifyArgs(args) {
  if (args[0] !== "verify") {
    return null;
  }
  return parseNodeCheckPathsExistArgs(["check_paths_exist", ...args.slice(1)]);
}

function parseNodeInstallArgs(args) {
  if (args[0] !== "install") {
    return null;
  }
  return parseNodeCheckPathsExistArgs(["check_paths_exist", ...args.slice(1)]);
}

function parseNodePruneArgs(args) {
  if (args[0] !== "prune") {
    return null;
  }
  let hasAll = false;
  let backend = "agents";
  let agentsRoot;
  for (let index = 1; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--all") {
      hasAll = true;
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
    if (arg === "--agents-root") {
      if (index + 1 >= args.length) {
        return null;
      }
      agentsRoot = args[index + 1];
      index += 1;
      continue;
    }
    if (arg.startsWith("--agents-root=")) {
      agentsRoot = arg.slice("--agents-root=".length);
      continue;
    }
    if (arg === "--claude-root") {
      if (index + 1 >= args.length) {
        return null;
      }
      index += 1;
      continue;
    }
    if (arg.startsWith("--claude-root=")) {
      continue;
    }
    return null;
  }
  if (!hasAll || backend !== "agents") {
    return null;
  }
  return { backend, agentsRoot };
}

function printVerifyResult(result) {
  if (result.issues.length === 0) {
    console.log(`[${result.backend}] ok: target root is ready at ${result.targetRoot}`);
    return;
  }
  console.log(
    `[${result.backend}] drift: ${result.issues.length} issue(s) in target root at ${result.targetRoot}`,
  );
  for (const currentIssue of result.issues) {
    console.log(`  - ${currentIssue.code}: ${currentIssue.path} (${currentIssue.detail})`);
  }
}

function runNodeVerify(args) {
  const parsed = parseNodeVerifyArgs(args);
  if (parsed === null) {
    return null;
  }
  try {
    const result = verifyAgentsBackend(buildNodeAgentsContext(parsed));
    printVerifyResult(result);
    return result.issues.length > 0 ? 1 : 0;
  } catch (error) {
    console.error(`error: ${error.message}`);
    return 1;
  }
}

function runNodeInstall(args) {
  const parsed = parseNodeInstallArgs(args);
  if (parsed === null) {
    return null;
  }
  try {
    const context = buildNodeAgentsContext(parsed);
    if (!targetRootIsCleanForNodeInstall(context.targetRoot)) {
      return null;
    }
    installBackendPayloads(context);
    return 0;
  } catch (error) {
    console.error(`error: ${error.message}`);
    return 1;
  }
}

function runNodePrune(args) {
  const parsed = parseNodePruneArgs(args);
  if (parsed === null) {
    return null;
  }
  try {
    pruneBackendManagedInstalls(buildNodeAgentsContext(parsed));
    return 0;
  } catch (error) {
    console.error(`error: ${error.message}`);
    return 1;
  }
}

async function runNodeOwnedOrWrapper(args) {
  const nodeDiagnoseStatus = runNodeDiagnoseJson(args);
  if (nodeDiagnoseStatus !== null) {
    return nodeDiagnoseStatus;
  }

  const nodeUpdateStatus = runNodeUpdateJson(args);
  if (nodeUpdateStatus !== null) {
    return nodeUpdateStatus;
  }

  const nodeUpdateYesStatus = runNodeUpdateYes(args);
  if (nodeUpdateYesStatus !== null) {
    return nodeUpdateYesStatus;
  }

  const nodeCheckPathsExistStatus = runNodeCheckPathsExist(args);
  if (nodeCheckPathsExistStatus !== null) {
    return nodeCheckPathsExistStatus;
  }

  const nodeVerifyStatus = runNodeVerify(args);
  if (nodeVerifyStatus !== null) {
    return nodeVerifyStatus;
  }

  const nodeInstallStatus = runNodeInstall(args);
  if (nodeInstallStatus !== null) {
    return nodeInstallStatus;
  }

  const nodePruneStatus = runNodePrune(args);
  if (nodePruneStatus !== null) {
    return nodePruneStatus;
  }

  return await runWrapper(args);
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
  const diagnoseStatus = await runNodeOwnedOrWrapper(["diagnose", "--backend", "agents", "--json"]);
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
    await runNodeOwnedOrWrapper(["update", "--backend", "agents", "--yes"]);
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
        await runNodeOwnedOrWrapper(["diagnose", "--backend", "agents", "--json"]);
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

  return await runNodeOwnedOrWrapper(args);
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
  buildNodeAgentsContext,
  buildWrapperEnv,
  buildInstallPlan,
  buildRuntimeMarker,
  canonicalSourceMetadata,
  assertManagedDirectoryIdentityCurrent,
  childDirectoryIdentity,
  collectAllKnownTargetDirs,
  collectLegacyPathConflicts,
  collectPathConflicts,
  collectTargetDirMetadata,
  collectUpdateTargetEntryIssues,
  computePayloadFingerprint,
  dedupeIssues,
  describeExistingTargetPath,
  diagnosticSummary,
  exactSensitiveTargetRepoRoots,
  expectedTargetDirs,
  checkPathsExistSummary,
  installBackendPayloads,
  isUpdateBlockingIssue,
  loadBindingPayloads,
  loadRuntimeMarker,
  normalizeRelativePath,
  parseNodeCheckPathsExistArgs,
  parseNodeDiagnoseJsonArgs,
  parseNodeInstallArgs,
  parseNodePruneArgs,
  parseNodeUpdateJsonArgs,
  parseNodeUpdateYesArgs,
  parseNodeVerifyArgs,
  pathSafetyPolicy,
  payloadTargetMetadata,
  printVerifyResult,
  printUpdatePlan,
  pruneBackendManagedInstalls,
  pythonCandidates,
  recursiveSensitiveTargetRepoRoots,
  resolveExistingOrLexical,
  updatePlanSummary,
  validateSourceRepoRoot,
  validateTargetRepoRoot,
  verifyAgentsBackend,
  verifyDeployedSkill,
};
