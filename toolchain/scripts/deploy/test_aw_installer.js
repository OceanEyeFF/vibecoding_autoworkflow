const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const { createHash } = require("node:crypto");
const { chmodSync, existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } = require("node:fs");
const { tmpdir } = require("node:os");
const { join } = require("node:path");
const test = require("node:test");

const installer = require("./bin/aw-installer.js");

function seedMinimalAgentsSource(root, skillId = "demo-skill", options = {}) {
  const canonicalDir = join(root, "product", "harness", "skills", skillId);
  const payloadDir = join(root, "product", "harness", "adapters", "agents", "skills", skillId);
  mkdirSync(canonicalDir, { recursive: true });
  mkdirSync(payloadDir, { recursive: true });
  mkdirSync(join(root, "product", "harness", "adapters", "claude", "skills"), { recursive: true });
  const targetDir = options.targetDir || `aw-${skillId}`;
  const payload = {
    payload_version: "agents-skill-payload.v1",
    backend: "agents",
    skill_id: skillId,
    target_dir: targetDir,
    target_entry_name: "SKILL.md",
    required_payload_files: ["SKILL.md", "payload.json", "aw.marker"],
    canonical_dir: `product/harness/skills/${skillId}`,
    canonical_paths: [`product/harness/skills/${skillId}/SKILL.md`],
    payload_policy: "canonical-copy",
    reference_distribution: "copy-listed-canonical-paths",
  };
  if (options.legacyTargetDirs !== undefined) {
    payload.legacy_target_dirs = options.legacyTargetDirs;
  }
  if (options.legacySkillIds !== undefined) {
    payload.legacy_skill_ids = options.legacySkillIds;
  }
  const payloadPath = join(payloadDir, "payload.json");
  writeFileSync(join(canonicalDir, "SKILL.md"), `# ${skillId}\n`, "utf8");
  writeFileSync(payloadPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  return {
    binding: {
      backend: "agents",
      skillId,
      payloadDir,
      payloadPath,
    },
    canonicalDir,
    payload,
    payloadDir,
    targetDir,
  };
}

function seedInstalledAgentsSkill(root, skillId = "demo-skill", options = {}) {
  const seeded = seedMinimalAgentsSource(root, skillId, options);
  const targetRoot = options.targetRoot || join(root, ".agents", "skills");
  const targetSkillDir = join(targetRoot, seeded.targetDir);
  mkdirSync(targetSkillDir, { recursive: true });
  const skillText = `# ${skillId}\n`;
  const payloadText = `${JSON.stringify(seeded.payload, null, 2)}\n`;
  writeFileSync(join(targetSkillDir, "SKILL.md"), skillText, "utf8");
  writeFileSync(join(targetSkillDir, "payload.json"), payloadText, "utf8");
  const metadata = installer.payloadTargetMetadata(seeded.payload, seeded.binding);
  const payloadFingerprint = installer.computePayloadFingerprint(
    seeded.binding,
    { sourceRoot: root },
    seeded.payload,
    payloadText,
    metadata,
  );
  const marker = {
    marker_version: "aw-managed-skill-marker.v2",
    backend: "agents",
    skill_id: skillId,
    payload_version: "agents-skill-payload.v1",
    payload_fingerprint: payloadFingerprint,
  };
  writeFileSync(join(targetSkillDir, "aw.marker"), `${JSON.stringify(marker, null, 2)}\n`, "utf8");
  return {
    ...seeded,
    marker,
    payloadText,
    targetRoot,
    targetSkillDir,
  };
}

function fakePythonBin(root) {
  const fakeBin = join(root, "fake-python-bin");
  mkdirSync(fakeBin);
  for (const pythonName of ["py", "python", "python3"]) {
    const pythonPath = join(fakeBin, pythonName);
    writeFileSync(
      pythonPath,
      "#!/bin/sh\nprintf 'unexpected-python %s\\n' \"$*\" >&2\nexit 97\n",
      "utf8",
    );
    chmodSync(pythonPath, 0o755);
  }
  return fakeBin;
}

function checkPathsExistEnv(root, fakeBin = null) {
  const pathSeparator = process.platform === "win32" ? ";" : ":";
  return {
    ...process.env,
    AW_HARNESS_REPO_ROOT: root,
    AW_HARNESS_TARGET_REPO_ROOT: root,
    PATH: fakeBin === null ? process.env.PATH || "" : `${fakeBin}${pathSeparator}${process.env.PATH || ""}`,
    PYTHONDONTWRITEBYTECODE: "1",
  };
}

function runNodeCheckPathsExist(root, args, fakeBin = null) {
  return spawnSync(
    process.execPath,
    [join(__dirname, "bin", "aw-installer.js"), "check_paths_exist", ...args],
    {
      cwd: root,
      env: checkPathsExistEnv(root, fakeBin),
      encoding: "utf8",
    },
  );
}

function runPythonCheckPathsExist(root, args) {
  return spawnSync(
    "python3",
    [join(__dirname, "adapter_deploy.py"), "check_paths_exist", ...args],
    {
      cwd: root,
      env: checkPathsExistEnv(root),
      encoding: "utf8",
    },
  );
}

function runNodeVerify(root, args, fakeBin = null) {
  return spawnSync(
    process.execPath,
    [join(__dirname, "bin", "aw-installer.js"), "verify", ...args],
    {
      cwd: root,
      env: checkPathsExistEnv(root, fakeBin),
      encoding: "utf8",
    },
  );
}

function runPythonVerify(root, args) {
  return spawnSync(
    "python3",
    [join(__dirname, "adapter_deploy.py"), "verify", ...args],
    {
      cwd: root,
      env: checkPathsExistEnv(root),
      encoding: "utf8",
    },
  );
}

function runNodeInstall(root, args, fakeBin = null) {
  return spawnSync(
    process.execPath,
    [join(__dirname, "bin", "aw-installer.js"), "install", ...args],
    {
      cwd: root,
      env: checkPathsExistEnv(root, fakeBin),
      encoding: "utf8",
    },
  );
}

function runNodePrune(root, args, fakeBin = null) {
  return spawnSync(
    process.execPath,
    [join(__dirname, "bin", "aw-installer.js"), "prune", ...args],
    {
      cwd: root,
      env: checkPathsExistEnv(root, fakeBin),
      encoding: "utf8",
    },
  );
}

function runNodeUpdate(root, args, fakeBin = null) {
  return spawnSync(
    process.execPath,
    [join(__dirname, "bin", "aw-installer.js"), "update", ...args],
    {
      cwd: root,
      env: checkPathsExistEnv(root, fakeBin),
      encoding: "utf8",
    },
  );
}

function runAwInstaller(root, args, fakeBin = null) {
  return spawnSync(process.execPath, [join(__dirname, "bin", "aw-installer.js"), ...args], {
    cwd: root,
    env: checkPathsExistEnv(root, fakeBin),
    encoding: "utf8",
  });
}

function runPythonInstall(root, args) {
  return spawnSync(
    "python3",
    [join(__dirname, "adapter_deploy.py"), "install", ...args],
    {
      cwd: root,
      env: checkPathsExistEnv(root),
      encoding: "utf8",
    },
  );
}

function runPythonPrune(root, args) {
  return spawnSync(
    "python3",
    [join(__dirname, "adapter_deploy.py"), "prune", ...args],
    {
      cwd: root,
      env: checkPathsExistEnv(root),
      encoding: "utf8",
    },
  );
}

function runPythonUpdate(root, args) {
  return spawnSync(
    "python3",
    [join(__dirname, "adapter_deploy.py"), "update", ...args],
    {
      cwd: root,
      env: checkPathsExistEnv(root),
      encoding: "utf8",
    },
  );
}

function assertNodeVerifyMatchesPython(root, args) {
  const fakeBin = fakePythonBin(root);
  const nodeWithSentinel = runNodeVerify(root, args, fakeBin);
  const node = runNodeVerify(root, args);
  const python = runPythonVerify(root, args);

  assert.equal(node.status, python.status);
  assert.equal(node.stdout, python.stdout);
  assert.equal(node.stderr, python.stderr);
  assert.equal(nodeWithSentinel.status, python.status);
  assert.equal(nodeWithSentinel.stdout, python.stdout);
  assert.equal(nodeWithSentinel.stderr.includes("unexpected-python"), false);
}

test("pythonCandidates avoids the usually-missing Linux python alias", () => {
  const commands = installer.pythonCandidates().map((candidate) => candidate.command);
  if (process.platform === "win32") {
    assert.deepEqual(commands, ["py", "python", "python3"]);
  } else {
    assert.deepEqual(commands, ["python3"]);
  }
});

test("node-owned summary and context helpers are exported for unit coverage", () => {
  assert.equal(typeof installer.buildNodeAgentsContext, "function");
  assert.equal(typeof installer.diagnosticSummary, "function");
  assert.deepEqual(
    installer.diagnosticSummary({
      sourceRoot: "/source",
      targetRoot: "/missing-target",
      issues: [],
      bindings: [],
      targetChildren: null,
    }),
    {
      backend: "agents",
      source_root: "/source",
      target_root: "/missing-target",
      target_root_status: "missing",
      target_root_exists: false,
      binding_count: 0,
      managed_install_count: 0,
      managed_installs: [],
      issue_count: 0,
      issue_codes: [],
      issues: [],
      unrecognized_count: 0,
      unrecognized: [],
      conflict_count: 0,
      conflicts: [],
    },
  );
});

test("path safety policy is loaded from the shared deploy JSON", () => {
  const policy = installer.pathSafetyPolicy();

  assert.ok(policy.exact_sensitive_target_repo_roots.includes("/etc"));
  assert.ok(policy.recursive_sensitive_target_repo_roots.includes("/proc"));
  assert.ok(policy.home_relative_recursive_sensitive_target_repo_roots.includes(".ssh"));
  assert.ok(policy.allowed_target_repo_root_prefixes.includes("$source_root"));
});

test("normalizeRelativePath rejects traversal and keeps clean relative paths", () => {
  assert.equal(
    installer.normalizeRelativePath("templates/SKILL.md", "field", "demo-skill", "repository root"),
    "templates/SKILL.md",
  );
  assert.throws(
    () => installer.normalizeRelativePath("../SKILL.md", "field", "demo-skill", "repository root"),
    /must not contain '\.\.'/,
  );
  assert.throws(
    () => installer.normalizeRelativePath("..\0/SKILL.md", "field", "demo-skill", "repository root"),
    /must not contain null bytes/,
  );
});

test("wrapper env strips common credential variables while preserving deploy controls", () => {
  assert.deepEqual(
    installer.buildWrapperEnv({
      ANTHROPIC_API_KEY: "secret",
      AW_HARNESS_REPO_ROOT: "/repo",
      GITHUB_TOKEN: "secret",
      HOME: "/home/demo",
      PATH: "/bin",
      PYTHONDONTWRITEBYTECODE: "0",
      HTTPS_PROXY: "http://proxy",
      SSL_CERT_DIR: "/etc/ssl/certs",
    }),
    {
      AW_HARNESS_REPO_ROOT: "/repo",
      HOME: "/home/demo",
      PATH: "/bin",
      PYTHONDONTWRITEBYTECODE: "0",
      HTTPS_PROXY: "http://proxy",
      SSL_CERT_DIR: "/etc/ssl/certs",
    },
  );
});

test("payloadTargetMetadata normalizes required target metadata", () => {
  const metadata = installer.payloadTargetMetadata(
    {
      target_dir: "aw-demo-skill",
      target_entry_name: "SKILL.md",
      required_payload_files: ["SKILL.md", "payload.json", "aw.marker"],
      legacy_target_dirs: ["demo-skill"],
      legacy_skill_ids: ["old-demo-skill"],
    },
    { skillId: "demo-skill" },
  );

  assert.deepEqual(metadata, {
    targetDir: "aw-demo-skill",
    targetEntryName: "SKILL.md",
    requiredPayloadFiles: ["SKILL.md", "payload.json", "aw.marker"],
    legacyTargetDirs: ["demo-skill"],
    legacySkillIds: ["old-demo-skill"],
  });
});

test("loadBindingPayloads rejects oversized JSON before parsing", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const payloadPath = join(root, "payload.json");
    writeFileSync(payloadPath, `{"data":"${"a".repeat(1_048_577)}"}`, "utf8");

    assert.throws(
      () => installer.loadBindingPayloads([{ payloadPath }]),
      /JSON payload exceeds 1048576 byte limit/,
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("computePayloadFingerprint matches the Python payload contract order", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const canonicalDir = join(root, "product", "harness", "skills", "demo-skill");
    const payloadDir = join(root, "product", "harness", "adapters", "agents", "skills", "demo-skill");
    mkdirSync(canonicalDir, { recursive: true });
    mkdirSync(payloadDir, { recursive: true });
    const skillText = "# Demo\n";
    const payload = {
      payload_version: "agents-skill-payload.v1",
      backend: "agents",
      skill_id: "demo-skill",
      target_dir: "aw-demo-skill",
      target_entry_name: "SKILL.md",
      required_payload_files: ["SKILL.md", "payload.json", "aw.marker"],
      canonical_dir: "product/harness/skills/demo-skill",
      canonical_paths: ["product/harness/skills/demo-skill/SKILL.md"],
    };
    const payloadText = `${JSON.stringify(payload, null, 2)}\n`;
    writeFileSync(join(canonicalDir, "SKILL.md"), skillText, "utf8");
    writeFileSync(join(payloadDir, "payload.json"), payloadText, "utf8");

    const binding = {
      backend: "agents",
      skillId: "demo-skill",
      payloadPath: join(payloadDir, "payload.json"),
    };
    const metadata = installer.payloadTargetMetadata(payload, binding);
    const fingerprint = installer.computePayloadFingerprint(
      binding,
      { sourceRoot: root },
      payload,
      payloadText,
      metadata,
    );
    const expected = createHash("sha256")
      .update(
        [
          "backend=agents\nskill_id=demo-skill\npayload_version=agents-skill-payload.v1\n",
          `file:SKILL.md\n${skillText}\n`,
          `file:payload.json\n${payloadText}\n`,
        ].join(""),
        "utf8",
      )
      .digest("hex");

    assert.equal(fingerprint, expected);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("parseNodeDiagnoseJsonArgs only accepts agents JSON diagnose", () => {
  assert.deepEqual(
    installer.parseNodeDiagnoseJsonArgs(["diagnose", "--backend", "agents", "--json"]),
    { backend: "agents" },
  );
  assert.equal(installer.parseNodeDiagnoseJsonArgs(["diagnose", "--backend", "claude", "--json"]), null);
  assert.equal(installer.parseNodeDiagnoseJsonArgs(["verify", "--backend", "agents", "--json"]), null);
});

test("parseNodeUpdateJsonArgs only accepts agents package JSON update dry-runs", () => {
  assert.deepEqual(
    installer.parseNodeUpdateJsonArgs(["update", "--backend", "agents", "--json"]),
    { backend: "agents", source: "package" },
  );
  assert.deepEqual(
    installer.parseNodeUpdateJsonArgs(["update", "--json", "--backend=agents", "--source=package"]),
    { backend: "agents", source: "package" },
  );

  assert.equal(
    installer.parseNodeUpdateJsonArgs(["update", "--backend", "agents", "--json", "--source", "github"]),
    null,
  );
  assert.equal(installer.parseNodeUpdateJsonArgs(["update", "--backend", "agents", "--yes"]), null);
  assert.equal(installer.parseNodeUpdateJsonArgs(["update", "--backend", "claude", "--json"]), null);
});

test("parseNodeUpdateYesArgs only accepts agents package update apply forms", () => {
  assert.deepEqual(
    installer.parseNodeUpdateYesArgs(["update", "--backend", "agents", "--yes"]),
    { backend: "agents", source: "package", yes: true, agentsRoot: undefined },
  );
  assert.deepEqual(
    installer.parseNodeUpdateYesArgs([
      "update",
      "--yes",
      "--backend=agents",
      "--source=package",
      "--agents-root=/tmp/agents-skills",
    ]),
    { backend: "agents", source: "package", yes: true, agentsRoot: "/tmp/agents-skills" },
  );

  assert.equal(
    installer.parseNodeUpdateYesArgs(["update", "--backend", "agents", "--yes", "--source", "github"]),
    null,
  );
  assert.equal(installer.parseNodeUpdateYesArgs(["update", "--backend", "agents", "--json", "--yes"]), null);
  assert.equal(installer.parseNodeUpdateYesArgs(["update", "--backend", "claude", "--yes"]), null);
  assert.equal(installer.parseNodeUpdateYesArgs(["update", "--backend", "agents"]), null);
});

test("parseNodeCheckPathsExistArgs accepts agents backend and target override forms", () => {
  assert.deepEqual(
    installer.parseNodeCheckPathsExistArgs(["check_paths_exist", "--backend", "agents"]),
    { backend: "agents", agentsRoot: undefined },
  );
  assert.deepEqual(
    installer.parseNodeCheckPathsExistArgs([
      "check_paths_exist",
      "--backend=agents",
      "--agents-root=/tmp/agents-skills",
    ]),
    { backend: "agents", agentsRoot: "/tmp/agents-skills" },
  );
  assert.deepEqual(
    installer.parseNodeCheckPathsExistArgs([
      "check_paths_exist",
      "--claude-root",
      "/tmp/ignored-claude-skills",
      "--agents-root",
      "/tmp/agents-skills",
    ]),
    { backend: "agents", agentsRoot: "/tmp/agents-skills" },
  );

  assert.equal(installer.parseNodeCheckPathsExistArgs(["check_paths_exist", "--backend", "claude"]), null);
  assert.equal(installer.parseNodeCheckPathsExistArgs(["check_paths_exist", "--source", "github"]), null);
});

test("parseNodeVerifyArgs accepts only agents package-local verify forms", () => {
  assert.deepEqual(
    installer.parseNodeVerifyArgs(["verify", "--backend", "agents"]),
    { backend: "agents", agentsRoot: undefined },
  );
  assert.deepEqual(
    installer.parseNodeVerifyArgs(["verify", "--backend=agents", "--agents-root=/tmp/agents-skills"]),
    { backend: "agents", agentsRoot: "/tmp/agents-skills" },
  );
  assert.equal(installer.parseNodeVerifyArgs(["verify", "--backend", "claude"]), null);
  assert.equal(installer.parseNodeVerifyArgs(["verify", "--source", "github"]), null);
  assert.equal(installer.parseNodeVerifyArgs(["diagnose", "--backend", "agents"]), null);
});

test("parseNodeInstallArgs accepts only agents package-local install forms", () => {
  assert.deepEqual(
    installer.parseNodeInstallArgs(["install", "--backend", "agents"]),
    { backend: "agents", agentsRoot: undefined },
  );
  assert.deepEqual(
    installer.parseNodeInstallArgs(["install", "--backend=agents", "--agents-root=/tmp/agents-skills"]),
    { backend: "agents", agentsRoot: "/tmp/agents-skills" },
  );
  assert.equal(installer.parseNodeInstallArgs(["install", "--backend", "claude"]), null);
  assert.equal(installer.parseNodeInstallArgs(["install", "--source", "github"]), null);
  assert.equal(installer.parseNodeInstallArgs(["verify", "--backend", "agents"]), null);
});

test("parseNodePruneArgs accepts only agents package-local prune all forms", () => {
  assert.deepEqual(
    installer.parseNodePruneArgs(["prune", "--all", "--backend", "agents"]),
    { backend: "agents", agentsRoot: undefined },
  );
  assert.deepEqual(
    installer.parseNodePruneArgs(["prune", "--backend=agents", "--agents-root=/tmp/agents-skills", "--all"]),
    { backend: "agents", agentsRoot: "/tmp/agents-skills" },
  );
  assert.equal(installer.parseNodePruneArgs(["prune", "--backend", "agents"]), null);
  assert.equal(installer.parseNodePruneArgs(["prune", "--all", "--backend", "claude"]), null);
  assert.equal(installer.parseNodePruneArgs(["prune", "--all", "--source", "github"]), null);
  assert.equal(installer.parseNodePruneArgs(["install", "--backend", "agents"]), null);
});

test("target dir helpers share duplicate checks and keep legacy dirs only in known set", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const alphaDir = join(root, "alpha");
    const betaDir = join(root, "beta");
    mkdirSync(alphaDir, { recursive: true });
    mkdirSync(betaDir, { recursive: true });
    const alphaPayloadPath = join(alphaDir, "payload.json");
    const betaPayloadPath = join(betaDir, "payload.json");
    writeFileSync(
      alphaPayloadPath,
      JSON.stringify({
        target_dir: "aw-alpha",
        target_entry_name: "SKILL.md",
        required_payload_files: ["SKILL.md", "payload.json", "aw.marker"],
        legacy_target_dirs: ["alpha"],
      }),
      "utf8",
    );
    writeFileSync(
      betaPayloadPath,
      JSON.stringify({
        target_dir: "aw-beta",
        target_entry_name: "SKILL.md",
        required_payload_files: ["SKILL.md", "payload.json", "aw.marker"],
        legacy_target_dirs: ["beta"],
      }),
      "utf8",
    );
    const bindings = [
      { backend: "agents", skillId: "alpha", payloadPath: alphaPayloadPath },
      { backend: "agents", skillId: "beta", payloadPath: betaPayloadPath },
    ];

    assert.deepEqual([...installer.expectedTargetDirs(bindings)].sort(), ["aw-alpha", "aw-beta"]);
    assert.deepEqual([...installer.collectAllKnownTargetDirs(bindings)].sort(), [
      "alpha",
      "aw-alpha",
      "aw-beta",
      "beta",
    ]);

    writeFileSync(
      betaPayloadPath,
      JSON.stringify({
        target_dir: "aw-alpha",
        target_entry_name: "SKILL.md",
        required_payload_files: ["SKILL.md", "payload.json", "aw.marker"],
      }),
      "utf8",
    );
    assert.throws(
      () => installer.expectedTargetDirs(bindings),
      /Multiple skills map to the same target_dir for backend agents: aw-alpha/,
    );
    assert.throws(
      () => installer.collectAllKnownTargetDirs(bindings),
      /Multiple skills map to the same target_dir for backend agents: aw-alpha/,
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("buildInstallPlan can reuse cached payload text instead of rereading payload.json", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const canonicalDir = join(root, "product", "harness", "skills", "demo-skill");
    const payloadDir = join(root, "product", "harness", "adapters", "agents", "skills", "demo-skill");
    const targetRoot = join(root, ".agents", "skills");
    mkdirSync(canonicalDir, { recursive: true });
    mkdirSync(payloadDir, { recursive: true });
    mkdirSync(targetRoot, { recursive: true });
    const skillText = "# Demo\n";
    const payload = {
      payload_version: "agents-skill-payload.v1",
      backend: "agents",
      skill_id: "demo-skill",
      target_dir: "aw-demo-skill",
      target_entry_name: "SKILL.md",
      required_payload_files: ["SKILL.md", "payload.json", "aw.marker"],
      canonical_dir: "product/harness/skills/demo-skill",
      canonical_paths: ["product/harness/skills/demo-skill/SKILL.md"],
      payload_policy: "canonical-copy",
      reference_distribution: "copy-listed-canonical-paths",
    };
    const payloadText = `${JSON.stringify(payload, null, 2)}\n`;
    const payloadPath = join(payloadDir, "payload.json");
    writeFileSync(join(canonicalDir, "SKILL.md"), skillText, "utf8");
    writeFileSync(payloadPath, payloadText, "utf8");
    const binding = {
      backend: "agents",
      skillId: "demo-skill",
      payloadDir,
      payloadPath,
    };
    const loadedPayloads = new Map([[payloadPath, { payload, payloadText }]]);
    writeFileSync(payloadPath, "{ invalid json", "utf8");

    const plan = installer.buildInstallPlan(binding, targetRoot, { sourceRoot: root }, { loadedPayloads });

    assert.equal(plan.targetSkillDir, join(targetRoot, "aw-demo-skill"));
    assert.equal(
      plan.payloadFingerprint,
      createHash("sha256")
        .update(
          [
            "backend=agents\nskill_id=demo-skill\npayload_version=agents-skill-payload.v1\n",
            `file:SKILL.md\n${skillText}\n`,
            `file:payload.json\n${payloadText}\n`,
          ].join(""),
          "utf8",
        )
        .digest("hex"),
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("verifyAgentsBackend passes cached payload text into deployed skill verification", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const canonicalDir = join(root, "product", "harness", "skills", "demo-skill");
    const payloadDir = join(root, "product", "harness", "adapters", "agents", "skills", "demo-skill");
    const targetRoot = join(root, ".agents", "skills");
    const targetSkillDir = join(targetRoot, "aw-demo-skill");
    mkdirSync(canonicalDir, { recursive: true });
    mkdirSync(payloadDir, { recursive: true });
    mkdirSync(targetSkillDir, { recursive: true });
    const skillText = "# Demo\n";
    const payload = {
      payload_version: "agents-skill-payload.v1",
      backend: "agents",
      skill_id: "demo-skill",
      target_dir: "aw-demo-skill",
      target_entry_name: "SKILL.md",
      required_payload_files: ["SKILL.md", "payload.json", "aw.marker"],
      canonical_dir: "product/harness/skills/demo-skill",
      canonical_paths: ["product/harness/skills/demo-skill/SKILL.md"],
      payload_policy: "canonical-copy",
      reference_distribution: "copy-listed-canonical-paths",
    };
    const payloadText = `${JSON.stringify(payload, null, 2)}\n`;
    const payloadPath = join(payloadDir, "payload.json");
    writeFileSync(join(canonicalDir, "SKILL.md"), skillText, "utf8");
    writeFileSync(payloadPath, payloadText, "utf8");
    writeFileSync(join(targetSkillDir, "SKILL.md"), skillText, "utf8");
    writeFileSync(join(targetSkillDir, "payload.json"), payloadText, "utf8");
    const binding = {
      backend: "agents",
      skillId: "demo-skill",
      payloadDir,
      payloadPath,
    };
    const metadata = installer.payloadTargetMetadata(payload, binding);
    const payloadFingerprint = installer.computePayloadFingerprint(
      binding,
      { sourceRoot: root },
      payload,
      payloadText,
      metadata,
    );
    const marker = {
      marker_version: "aw-managed-skill-marker.v2",
      backend: "agents",
      skill_id: "demo-skill",
      payload_version: "agents-skill-payload.v1",
      payload_fingerprint: payloadFingerprint,
    };
    writeFileSync(join(targetSkillDir, "aw.marker"), `${JSON.stringify(marker, null, 2)}\n`, "utf8");

    const loadedPayloads = new Map([[payloadPath, { payload, payloadText }]]);
    writeFileSync(payloadPath, "{ invalid json", "utf8");

    const result = installer.verifyAgentsBackend(
      {
        sourceRoot: root,
        targetRoot,
        adapterSkillsDir: join(root, "product", "harness", "adapters", "agents", "skills"),
      },
      { bindings: [binding], loadedPayloads },
    );

    const issueCodes = result.issues.map((currentIssue) => currentIssue.code);
    assert.equal(issueCodes.includes("payload-contract-invalid"), false);
    assert.deepEqual(issueCodes, ["target-payload-drift"]);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("update planning helpers expose direct issue and blocking behavior", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const targetRoot = join(root, ".agents", "skills");
    const targetDir = join(targetRoot, "aw-demo-skill");
    mkdirSync(targetDir, { recursive: true });

    const issues = installer.collectUpdateTargetEntryIssues(
      targetRoot,
      new Set(["aw-demo-skill"]),
      [targetDir],
    );

    assert.deepEqual(issues, [
      {
        code: "unrecognized-target-directory",
        path: targetDir,
        detail: "update will not remove target directories without a recognized marker",
      },
    ]);
    assert.equal(installer.isUpdateBlockingIssue(issues[0], new Set()), true);
    assert.equal(installer.isUpdateBlockingIssue(issues[0], new Set([targetDir])), false);
    assert.deepEqual(
      installer.dedupeIssues([
        issues[0],
        { ...issues[0], detail: "duplicate detail" },
        { code: "missing-target-root", path: targetRoot, detail: "missing" },
      ]),
      [issues[0], { code: "missing-target-root", path: targetRoot, detail: "missing" }],
    );
    for (const code of [
      "missing-target-root",
      "missing-target-entry",
      "missing-required-payload",
      "target-payload-drift",
      "unexpected-managed-directory",
    ]) {
      assert.equal(
        installer.isUpdateBlockingIssue({ code, path: targetRoot, detail: code }, new Set()),
        false,
      );
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("collectUpdateTargetEntryIssues covers non-directory, fallback children, wrong type, and foreign markers", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const missingTargetRoot = join(root, "missing", "skills");
    assert.deepEqual(
      installer.collectUpdateTargetEntryIssues(missingTargetRoot, new Set(["aw-demo-skill"]), null),
      [],
    );

    const targetRoot = join(root, ".agents", "skills");
    const wrongTypePath = join(targetRoot, "aw-demo-skill");
    const foreignPath = join(targetRoot, "aw-foreign-skill");
    mkdirSync(targetRoot, { recursive: true });
    writeFileSync(wrongTypePath, "not a directory\n", "utf8");
    mkdirSync(foreignPath, { recursive: true });
    writeFileSync(
      join(foreignPath, "aw.marker"),
      `${JSON.stringify({
        marker_version: "aw-managed-skill-marker.v2",
        backend: "claude",
        skill_id: "foreign-skill",
        payload_version: "agents-skill-payload.v1",
        payload_fingerprint: "abc",
      }, null, 2)}\n`,
      "utf8",
    );

    assert.deepEqual(
      installer.collectUpdateTargetEntryIssues(
        targetRoot,
        new Set(["aw-demo-skill", "aw-foreign-skill"]),
        null,
      ),
      [
        {
          code: "wrong-target-entry-type",
          path: wrongTypePath,
          detail: "update target path must be a real directory before reinstall",
        },
        {
          code: "foreign-managed-directory",
          path: foreignPath,
          detail: "update will not remove managed directory for backend claude",
        },
      ],
    );

    const symlinkPath = join(targetRoot, "aw-linked-skill");
    symlinkSync(foreignPath, symlinkPath, "dir");
    assert.deepEqual(
      installer.collectUpdateTargetEntryIssues(
        targetRoot,
        new Set(["aw-linked-skill"]),
        [symlinkPath],
      ),
      [
        {
          code: "wrong-target-entry-type",
          path: symlinkPath,
          detail: "update target path must be a real directory before reinstall",
        },
      ],
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("checkPathsExistSummary reports planned paths and no conflict without creating target root", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(root, "demo-skill");
    const targetRoot = join(root, ".agents", "skills");

    const summary = installer.checkPathsExistSummary({
      sourceRoot: root,
      targetRoot,
      adapterSkillsDir: join(root, "product", "harness", "adapters", "agents", "skills"),
    });

    assert.equal(summary.backend, "agents");
    assert.deepEqual(summary.plannedTargetPaths, [join(targetRoot, "aw-demo-skill")]);
    assert.deepEqual(summary.conflicts, []);
    assert.equal(existsSync(targetRoot), false);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("check path conflict helpers classify directories, files, broken symlinks, and legacy dirs", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const targetRoot = join(root, ".agents", "skills");
    mkdirSync(targetRoot, { recursive: true });
    const alpha = seedMinimalAgentsSource(root, "alpha", {
      targetDir: "aw-alpha",
      legacyTargetDirs: ["alpha"],
    });
    const beta = seedMinimalAgentsSource(root, "beta", { targetDir: "aw-beta" });
    const gamma = seedMinimalAgentsSource(root, "gamma", { targetDir: "aw-gamma" });
    mkdirSync(join(targetRoot, "aw-alpha"));
    writeFileSync(join(targetRoot, "aw-beta"), "occupied by file\n", "utf8");
    symlinkSync(join(root, "missing-gamma"), join(targetRoot, "aw-gamma"), "dir");
    mkdirSync(join(targetRoot, "alpha"));
    writeFileSync(join(targetRoot, "alpha", "SKILL.md"), "# unmanaged old skill\n", "utf8");
    const bindings = [alpha.binding, beta.binding, gamma.binding];
    const loadedPayloads = installer.loadBindingPayloads(bindings);
    const metadata = installer.collectTargetDirMetadata(bindings, loadedPayloads);
    const plans = bindings.map((binding) =>
      installer.buildInstallPlan(binding, targetRoot, { sourceRoot: root }, {
        loadedPayloads,
        targetMetadata: metadata.metadataByPayloadPath.get(binding.payloadPath),
      }),
    );

    assert.deepEqual(
      installer.collectPathConflicts(plans),
      [
        {
          skillId: "alpha",
          path: join(targetRoot, "aw-alpha"),
          detail: "existing target path is a directory",
        },
        {
          skillId: "beta",
          path: join(targetRoot, "aw-beta"),
          detail: "existing target path is a file",
        },
        {
          skillId: "gamma",
          path: join(targetRoot, "aw-gamma"),
          detail: "existing target path is a broken symlink",
        },
      ],
    );
    assert.deepEqual(installer.collectLegacyPathConflicts(plans, targetRoot), [
      {
        skillId: "alpha",
        path: join(targetRoot, "alpha"),
        detail: "legacy directory alpha is occupied by unmanaged content",
      },
    ]);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("checkPathsExistSummary keeps same source validation and duplicate target_dir failures", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const first = seedMinimalAgentsSource(root, "first", { targetDir: "aw-shared" });
    seedMinimalAgentsSource(root, "second", { targetDir: "aw-shared" });
    const context = {
      sourceRoot: root,
      targetRoot: join(root, ".agents", "skills"),
      adapterSkillsDir: join(root, "product", "harness", "adapters", "agents", "skills"),
    };

    assert.throws(
      () => installer.checkPathsExistSummary(context),
      /Multiple skills map to the same target_dir for backend agents: aw-shared/,
    );

    first.payload.backend = "claude";
    writeFileSync(first.binding.payloadPath, `${JSON.stringify(first.payload, null, 2)}\n`, "utf8");
    assert.throws(
      () => installer.checkPathsExistSummary(context),
      /Cannot check target paths because source validation failed:[\s\S]*payload backend must be agents/,
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("aw-installer check_paths_exist agents is node-owned without Python and honors agents-root", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(root, "demo-skill");
    const fakeBin = fakePythonBin(root);
    const agentsRoot = join(root, "custom-agents", "skills");

    const completed = runNodeCheckPathsExist(root, ["--backend=agents", `--agents-root=${agentsRoot}`], fakeBin);

    assert.equal(completed.status, 0, completed.stderr);
    assert.equal(completed.stdout, `[agents] ok: no conflicting target paths at ${agentsRoot}\n`);
    assert.equal(completed.stderr.includes("unexpected-python"), false);
    assert.equal(existsSync(agentsRoot), false);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("aw-installer check_paths_exist agents reports conflicts with Python-compatible stderr", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(root, "demo-skill");
    const targetRoot = join(root, ".agents", "skills");
    mkdirSync(join(targetRoot, "aw-demo-skill"), { recursive: true });
    const fakeBin = fakePythonBin(root);

    const completed = runNodeCheckPathsExist(root, ["--backend", "agents"], fakeBin);

    assert.equal(completed.status, 1);
    assert.equal(completed.stdout, "");
    assert.match(completed.stderr, /^error: \[agents\] found 1 conflicting target path\(s\)/);
    assert.match(completed.stderr, /target path conflicts:/);
    assert.match(completed.stderr, /demo-skill/);
    assert.match(completed.stderr, /existing target path is a directory/);
    assert.equal(completed.stderr.includes("unexpected-python"), false);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("aw-installer check_paths_exist agents stays node-owned for source and duplicate failures", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const first = seedMinimalAgentsSource(root, "first", { targetDir: "aw-shared" });
    seedMinimalAgentsSource(root, "second", { targetDir: "aw-shared" });
    const fakeBin = fakePythonBin(root);

    const duplicateResult = runNodeCheckPathsExist(root, ["--backend=agents"], fakeBin);
    assert.equal(duplicateResult.status, 1);
    assert.equal(duplicateResult.stdout, "");
    assert.match(duplicateResult.stderr, /Multiple skills map to the same target_dir for backend agents: aw-shared/);
    assert.equal(duplicateResult.stderr.includes("unexpected-python"), false);

    first.payload.backend = "claude";
    writeFileSync(first.binding.payloadPath, `${JSON.stringify(first.payload, null, 2)}\n`, "utf8");

    const sourceResult = runNodeCheckPathsExist(root, ["--backend=agents"], fakeBin);
    assert.equal(sourceResult.status, 1);
    assert.equal(sourceResult.stdout, "");
    assert.match(
      sourceResult.stderr,
      /Cannot check target paths because source validation failed:[\s\S]*payload backend must be agents/,
    );
    assert.equal(sourceResult.stderr.includes("unexpected-python"), false);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("aw-installer check_paths_exist agents reports target root readiness failures without Python", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(root, "demo-skill");
    const fakeBin = fakePythonBin(root);
    const agentsRoot = join(root, ".agents", "skills");
    mkdirSync(join(root, ".agents"), { recursive: true });
    writeFileSync(agentsRoot, "not a directory\n", "utf8");

    const completed = runNodeCheckPathsExist(root, ["--backend=agents", `--agents-root=${agentsRoot}`], fakeBin);

    assert.equal(completed.status, 1);
    assert.equal(completed.stdout, "");
    assert.match(completed.stderr, /Cannot check target paths because target root is not ready:/);
    assert.match(completed.stderr, /wrong-target-root-type/);
    assert.match(completed.stderr, /target root exists but is not a directory/);
    assert.equal(completed.stderr.includes("unexpected-python"), false);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("aw-installer check_paths_exist agents matches Python reference output for success and conflict", () => {
  const successRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  const conflictRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(successRoot, "demo-skill");
    const successAgentsRoot = join(successRoot, ".agents", "skills");

    const nodeSuccess = runNodeCheckPathsExist(
      successRoot,
      ["--backend=agents", `--agents-root=${successAgentsRoot}`],
    );
    const pythonSuccess = runPythonCheckPathsExist(
      successRoot,
      ["--backend=agents", `--agents-root=${successAgentsRoot}`],
    );

    assert.equal(nodeSuccess.status, pythonSuccess.status);
    assert.equal(nodeSuccess.stdout, pythonSuccess.stdout);
    assert.equal(nodeSuccess.stderr, pythonSuccess.stderr);

    seedMinimalAgentsSource(conflictRoot, "demo-skill");
    const conflictAgentsRoot = join(conflictRoot, ".agents", "skills");
    mkdirSync(join(conflictAgentsRoot, "aw-demo-skill"), { recursive: true });

    const nodeConflict = runNodeCheckPathsExist(
      conflictRoot,
      ["--backend=agents", `--agents-root=${conflictAgentsRoot}`],
    );
    const pythonConflict = runPythonCheckPathsExist(
      conflictRoot,
      ["--backend=agents", `--agents-root=${conflictAgentsRoot}`],
    );

    assert.equal(nodeConflict.status, pythonConflict.status);
    assert.equal(nodeConflict.stdout, pythonConflict.stdout);
    assert.equal(nodeConflict.stderr, pythonConflict.stderr);
  } finally {
    rmSync(successRoot, { recursive: true, force: true });
    rmSync(conflictRoot, { recursive: true, force: true });
  }
});

test("aw-installer verify agents is node-owned without Python for success and drift", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const installed = seedInstalledAgentsSkill(root, "demo-skill");
    const fakeBin = fakePythonBin(root);

    const success = runNodeVerify(root, ["--backend=agents", `--agents-root=${installed.targetRoot}`], fakeBin);
    assert.equal(success.status, 0, success.stderr);
    assert.equal(success.stdout, `[agents] ok: target root is ready at ${installed.targetRoot}\n`);
    assert.equal(success.stderr.includes("unexpected-python"), false);

    writeFileSync(join(installed.targetSkillDir, "SKILL.md"), "# drifted\n", "utf8");
    const drift = runNodeVerify(root, ["--backend=agents", `--agents-root=${installed.targetRoot}`], fakeBin);
    assert.equal(drift.status, 1);
    assert.match(drift.stdout, /^\[agents\] drift: 1 issue\(s\) in target root/);
    assert.match(drift.stdout, /target-payload-drift/);
    assert.equal(drift.stderr.includes("unexpected-python"), false);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("aw-installer verify agents is node-owned for missing and invalid target states", () => {
  const missingRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  const unrecognizedRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  const wrongTypeRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(missingRoot, "demo-skill");
    const missingFakeBin = fakePythonBin(missingRoot);
    const missingTargetRoot = join(missingRoot, ".agents", "skills");
    const missing = runNodeVerify(
      missingRoot,
      ["--backend=agents", `--agents-root=${missingTargetRoot}`],
      missingFakeBin,
    );
    assert.equal(missing.status, 1);
    assert.match(missing.stdout, /missing-target-root/);
    assert.match(missing.stdout, /agents target root does not exist/);
    assert.equal(missing.stderr.includes("unexpected-python"), false);

    const unrecognized = seedInstalledAgentsSkill(unrecognizedRoot, "demo-skill");
    rmSync(join(unrecognized.targetSkillDir, "aw.marker"), { force: true });
    const unrecognizedFakeBin = fakePythonBin(unrecognizedRoot);
    const unrecognizedResult = runNodeVerify(
      unrecognizedRoot,
      ["--backend=agents", `--agents-root=${unrecognized.targetRoot}`],
      unrecognizedFakeBin,
    );
    assert.equal(unrecognizedResult.status, 1);
    assert.match(unrecognizedResult.stdout, /unrecognized-target-directory/);
    assert.equal(unrecognizedResult.stderr.includes("unexpected-python"), false);

    seedMinimalAgentsSource(wrongTypeRoot, "demo-skill");
    const wrongTypeTargetRoot = join(wrongTypeRoot, ".agents", "skills");
    mkdirSync(join(wrongTypeRoot, ".agents"), { recursive: true });
    writeFileSync(wrongTypeTargetRoot, "not a directory\n", "utf8");
    const wrongTypeFakeBin = fakePythonBin(wrongTypeRoot);
    const wrongType = runNodeVerify(
      wrongTypeRoot,
      ["--backend=agents", `--agents-root=${wrongTypeTargetRoot}`],
      wrongTypeFakeBin,
    );
    assert.equal(wrongType.status, 1);
    assert.match(wrongType.stdout, /wrong-target-root-type/);
    assert.match(wrongType.stdout, /target root exists but is not a directory/);
    assert.equal(wrongType.stderr.includes("unexpected-python"), false);
  } finally {
    rmSync(missingRoot, { recursive: true, force: true });
    rmSync(unrecognizedRoot, { recursive: true, force: true });
    rmSync(wrongTypeRoot, { recursive: true, force: true });
  }
});

test("aw-installer verify agents covers broken symlink and foreign marker without Python", () => {
  const brokenSymlinkRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  const foreignMarkerRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(brokenSymlinkRoot, "demo-skill");
    const brokenTargetRoot = join(brokenSymlinkRoot, ".agents", "skills");
    mkdirSync(join(brokenSymlinkRoot, ".agents"), { recursive: true });
    symlinkSync(join(brokenSymlinkRoot, "missing-target"), brokenTargetRoot, "dir");
    const brokenFakeBin = fakePythonBin(brokenSymlinkRoot);
    const brokenResult = runNodeVerify(
      brokenSymlinkRoot,
      ["--backend=agents"],
      brokenFakeBin,
    );
    assert.equal(brokenResult.status, 1);
    assert.match(brokenResult.stdout, /broken-target-root-symlink/);
    assert.match(brokenResult.stdout, /target root is a broken symlink/);
    assert.equal(brokenResult.stderr.includes("unexpected-python"), false);

    const foreign = seedInstalledAgentsSkill(foreignMarkerRoot, "demo-skill");
    const foreignMarker = {
      ...foreign.marker,
      backend: "claude",
    };
    writeFileSync(join(foreign.targetSkillDir, "aw.marker"), `${JSON.stringify(foreignMarker, null, 2)}\n`, "utf8");
    const foreignFakeBin = fakePythonBin(foreignMarkerRoot);
    const foreignResult = runNodeVerify(
      foreignMarkerRoot,
      ["--backend=agents", `--agents-root=${foreign.targetRoot}`],
      foreignFakeBin,
    );
    assert.equal(foreignResult.status, 1);
    assert.match(foreignResult.stdout, /unrecognized-target-directory/);
    assert.match(foreignResult.stdout, /does not match current backend\/skill\/payload_version/);
    assert.equal(foreignResult.stderr.includes("unexpected-python"), false);
  } finally {
    rmSync(brokenSymlinkRoot, { recursive: true, force: true });
    rmSync(foreignMarkerRoot, { recursive: true, force: true });
  }
});

test("aw-installer verify agents matches Python reference output for success and drift", () => {
  const cases = [
    {
      name: "success",
      setup(root) {
        return seedInstalledAgentsSkill(root, "demo-skill").targetRoot;
      },
    },
    {
      name: "payload file drift",
      setup(root) {
        const installed = seedInstalledAgentsSkill(root, "demo-skill");
        writeFileSync(join(installed.targetSkillDir, "SKILL.md"), "# drifted\n", "utf8");
        return installed.targetRoot;
      },
    },
    {
      name: "marker fingerprint drift",
      setup(root) {
        const installed = seedInstalledAgentsSkill(root, "demo-skill");
        const driftedMarker = {
          ...installed.marker,
          payload_fingerprint: "0".repeat(64),
        };
        writeFileSync(join(installed.targetSkillDir, "aw.marker"), `${JSON.stringify(driftedMarker, null, 2)}\n`, "utf8");
        return installed.targetRoot;
      },
    },
    {
      name: "missing target root",
      setup(root) {
        seedMinimalAgentsSource(root, "demo-skill");
        return join(root, ".agents", "skills");
      },
    },
    {
      name: "wrong target root type",
      setup(root) {
        seedMinimalAgentsSource(root, "demo-skill");
        const targetRoot = join(root, ".agents", "skills");
        mkdirSync(join(root, ".agents"), { recursive: true });
        writeFileSync(targetRoot, "not a directory\n", "utf8");
        return targetRoot;
      },
    },
    {
      name: "broken target root symlink",
      setup(root) {
        seedMinimalAgentsSource(root, "demo-skill");
        const targetRoot = join(root, ".agents", "skills");
        mkdirSync(join(root, ".agents"), { recursive: true });
        symlinkSync(join(root, "missing-target"), targetRoot, "dir");
        return null;
      },
    },
    {
      name: "missing deployed skill directory",
      setup(root) {
        seedMinimalAgentsSource(root, "demo-skill");
        const targetRoot = join(root, ".agents", "skills");
        mkdirSync(targetRoot, { recursive: true });
        return targetRoot;
      },
    },
    {
      name: "unrecognized missing marker",
      setup(root) {
        const installed = seedInstalledAgentsSkill(root, "demo-skill");
        rmSync(join(installed.targetSkillDir, "aw.marker"), { force: true });
        return installed.targetRoot;
      },
    },
    {
      name: "foreign marker",
      setup(root) {
        const installed = seedInstalledAgentsSkill(root, "demo-skill");
        const foreignMarker = {
          ...installed.marker,
          backend: "claude",
        };
        writeFileSync(join(installed.targetSkillDir, "aw.marker"), `${JSON.stringify(foreignMarker, null, 2)}\n`, "utf8");
        return installed.targetRoot;
      },
    },
    {
      name: "missing required payload",
      setup(root) {
        const installed = seedInstalledAgentsSkill(root, "demo-skill");
        rmSync(join(installed.targetSkillDir, "payload.json"), { force: true });
        return installed.targetRoot;
      },
    },
    {
      name: "wrong target entry type",
      setup(root) {
        const installed = seedInstalledAgentsSkill(root, "demo-skill");
        rmSync(join(installed.targetSkillDir, "SKILL.md"), { force: true });
        mkdirSync(join(installed.targetSkillDir, "SKILL.md"));
        return installed.targetRoot;
      },
    },
    {
      name: "unexpected managed directory",
      setup(root) {
        const installed = seedInstalledAgentsSkill(root, "demo-skill");
        const unexpectedDir = join(installed.targetRoot, "aw-old-skill");
        mkdirSync(unexpectedDir, { recursive: true });
        const unexpectedMarker = {
          marker_version: "aw-managed-skill-marker.v2",
          backend: "agents",
          skill_id: "old-skill",
          payload_version: "agents-skill-payload.v1",
          payload_fingerprint: "1".repeat(64),
        };
        writeFileSync(join(unexpectedDir, "aw.marker"), `${JSON.stringify(unexpectedMarker, null, 2)}\n`, "utf8");
        return installed.targetRoot;
      },
    },
  ];
  for (const currentCase of cases) {
    const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
    try {
      const targetRoot = currentCase.setup(root);
      const args = targetRoot === null
        ? ["--backend=agents"]
        : ["--backend=agents", `--agents-root=${targetRoot}`];
      assertNodeVerifyMatchesPython(root, args);
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  }
});

test("aw-installer install agents writes a clean target without Python and verifies", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(root, "demo-skill");
    const fakeBin = fakePythonBin(root);
    const targetRoot = join(root, ".agents", "skills");
    const targetSkillDir = join(targetRoot, "aw-demo-skill");

    const completed = runNodeInstall(root, ["--backend=agents", `--agents-root=${targetRoot}`], fakeBin);

    assert.equal(completed.status, 0, completed.stderr);
    assert.match(completed.stdout, new RegExp(`created target root ${targetRoot.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`));
    assert.match(completed.stdout, new RegExp(`installed skill demo-skill -> ${targetSkillDir.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`));
    assert.equal(completed.stderr.includes("unexpected-python"), false);
    assert.equal(existsSync(targetSkillDir), true);
    assert.equal(lstatSync(targetSkillDir).mode & 0o777, 0o755);
    assert.equal(lstatSync(join(targetSkillDir, "SKILL.md")).mode & 0o777, 0o644);
    assert.equal(lstatSync(join(targetSkillDir, "payload.json")).mode & 0o777, 0o644);
    assert.equal(lstatSync(join(targetSkillDir, "aw.marker")).mode & 0o777, 0o644);
    assert.equal(readFileSync(join(targetSkillDir, "SKILL.md"), "utf8"), "# demo-skill\n");

    const result = installer.verifyAgentsBackend({
      sourceRoot: root,
      targetRoot,
      adapterSkillsDir: join(root, "product", "harness", "adapters", "agents", "skills"),
    });
    assert.deepEqual(result.issues, []);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("aw-installer install agents writes an existing empty target without Python", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(root, "demo-skill");
    const fakeBin = fakePythonBin(root);
    const targetRoot = join(root, ".agents", "skills");
    const targetSkillDir = join(targetRoot, "aw-demo-skill");
    mkdirSync(targetRoot, { recursive: true });

    const completed = runNodeInstall(root, ["--backend=agents", `--agents-root=${targetRoot}`], fakeBin);

    assert.equal(completed.status, 0, completed.stderr);
    assert.match(completed.stdout, new RegExp(`ready target root ${targetRoot.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`));
    assert.match(completed.stdout, new RegExp(`installed skill demo-skill -> ${targetSkillDir.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`));
    assert.equal(completed.stderr.includes("unexpected-python"), false);
    assert.equal(existsSync(join(targetSkillDir, "SKILL.md")), true);
    assert.deepEqual(
      installer.verifyAgentsBackend({
        sourceRoot: root,
        targetRoot,
        adapterSkillsDir: join(root, "product", "harness", "adapters", "agents", "skills"),
      }).issues,
      [],
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("aw-installer install agents matches Python reference on clean target output shape", () => {
  const nodeRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  const pythonRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(nodeRoot, "demo-skill");
    seedMinimalAgentsSource(pythonRoot, "demo-skill");
    const nodeTargetRoot = join(nodeRoot, ".agents", "skills");
    const pythonTargetRoot = join(pythonRoot, ".agents", "skills");

    const nodeResult = runNodeInstall(nodeRoot, ["--backend=agents", `--agents-root=${nodeTargetRoot}`]);
    const pythonResult = runPythonInstall(pythonRoot, ["--backend=agents", `--agents-root=${pythonTargetRoot}`]);
    const normalizeNodeRoot = (value) => value.replaceAll(nodeRoot, "<ROOT>");
    const normalizePythonRoot = (value) => value.replaceAll(pythonRoot, "<ROOT>");

    assert.equal(nodeResult.status, pythonResult.status);
    assert.equal(normalizeNodeRoot(nodeResult.stdout), normalizePythonRoot(pythonResult.stdout));
    assert.equal(nodeResult.stderr, pythonResult.stderr);
  } finally {
    rmSync(nodeRoot, { recursive: true, force: true });
    rmSync(pythonRoot, { recursive: true, force: true });
  }
});

test("aw-installer install agents falls back for non-clean target root without Node writes", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(root, "demo-skill");
    const targetRoot = join(root, ".agents", "skills");
    const targetSkillDir = join(targetRoot, "aw-demo-skill");
    mkdirSync(join(targetRoot, "user-owned"), { recursive: true });
    const fakeBin = fakePythonBin(root);

    const completed = runNodeInstall(root, ["--backend=agents", `--agents-root=${targetRoot}`], fakeBin);

    assert.equal(completed.status, 97);
    assert.equal(completed.stdout, "");
    assert.match(completed.stderr, /unexpected-python/);
    assert.equal(existsSync(targetSkillDir), false);
    assert.equal(existsSync(join(targetRoot, "user-owned")), true);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("aw-installer install agents rejects source and target readiness failures without Python", () => {
  const duplicateRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  const wrongTypeRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  const sourceFailureRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(duplicateRoot, "first", { targetDir: "aw-shared" });
    seedMinimalAgentsSource(duplicateRoot, "second", { targetDir: "aw-shared" });
    const duplicateFakeBin = fakePythonBin(duplicateRoot);
    const duplicateTargetRoot = join(duplicateRoot, ".agents", "skills");

    const duplicate = runNodeInstall(
      duplicateRoot,
      ["--backend=agents", `--agents-root=${duplicateTargetRoot}`],
      duplicateFakeBin,
    );
    assert.equal(duplicate.status, 1);
    assert.equal(duplicate.stdout, "");
    assert.match(duplicate.stderr, /Multiple skills map to the same target_dir for backend agents: aw-shared/);
    assert.equal(duplicate.stderr.includes("unexpected-python"), false);
    assert.equal(existsSync(duplicateTargetRoot), false);

    seedMinimalAgentsSource(wrongTypeRoot, "demo-skill");
    const wrongTypeTargetRoot = join(wrongTypeRoot, ".agents", "skills");
    mkdirSync(join(wrongTypeRoot, ".agents"), { recursive: true });
    writeFileSync(wrongTypeTargetRoot, "not a directory\n", "utf8");
    const wrongTypeFakeBin = fakePythonBin(wrongTypeRoot);

    const wrongType = runNodeInstall(
      wrongTypeRoot,
      ["--backend=agents", `--agents-root=${wrongTypeTargetRoot}`],
      wrongTypeFakeBin,
    );
    assert.equal(wrongType.status, 1);
    assert.equal(wrongType.stdout, "");
    assert.match(wrongType.stderr, /Cannot install because target root is not ready:/);
    assert.match(wrongType.stderr, /wrong-target-root-type/);
    assert.equal(wrongType.stderr.includes("unexpected-python"), false);

    const sourceFailure = seedMinimalAgentsSource(sourceFailureRoot, "demo-skill");
    rmSync(join(sourceFailure.canonicalDir, "SKILL.md"));
    const sourceFailureTargetRoot = join(sourceFailureRoot, ".agents", "skills");
    const sourceFailureFakeBin = fakePythonBin(sourceFailureRoot);

    const missingCanonical = runNodeInstall(
      sourceFailureRoot,
      ["--backend=agents", `--agents-root=${sourceFailureTargetRoot}`],
      sourceFailureFakeBin,
    );
    assert.equal(missingCanonical.status, 1);
    assert.equal(missingCanonical.stdout, "");
    assert.match(missingCanonical.stderr, /Cannot install because source validation failed:/);
    assert.match(missingCanonical.stderr, /missing-canonical-source/);
    assert.equal(missingCanonical.stderr.includes("unexpected-python"), false);
    assert.equal(existsSync(sourceFailureTargetRoot), false);
  } finally {
    rmSync(duplicateRoot, { recursive: true, force: true });
    rmSync(wrongTypeRoot, { recursive: true, force: true });
    rmSync(sourceFailureRoot, { recursive: true, force: true });
  }
});

test("aw-installer prune agents removes only same-backend managed dirs without Python", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const installed = seedInstalledAgentsSkill(root, "demo-skill");
    const targetRoot = installed.targetRoot;
    const staleDir = join(targetRoot, "aw-stale-skill");
    const foreignDir = join(targetRoot, "foreign-managed");
    const invalidDir = join(targetRoot, "invalid-marker");
    const unrecognizedDir = join(targetRoot, "unrecognized");
    const userFile = join(targetRoot, "user-file.txt");
    const userSymlink = join(targetRoot, "user-symlink");

    mkdirSync(staleDir, { recursive: true });
    writeFileSync(
      join(staleDir, "aw.marker"),
      `${JSON.stringify({
        marker_version: "aw-managed-skill-marker.v2",
        backend: "agents",
        skill_id: "stale-skill",
        payload_version: "stale-version",
        payload_fingerprint: "stale-fingerprint",
      }, null, 2)}\n`,
      "utf8",
    );
    mkdirSync(foreignDir, { recursive: true });
    writeFileSync(
      join(foreignDir, "aw.marker"),
      `${JSON.stringify({
        ...installed.marker,
        backend: "claude",
      }, null, 2)}\n`,
      "utf8",
    );
    mkdirSync(invalidDir, { recursive: true });
    writeFileSync(join(invalidDir, "aw.marker"), "{invalid json\n", "utf8");
    mkdirSync(unrecognizedDir, { recursive: true });
    writeFileSync(userFile, "user data\n", "utf8");
    symlinkSync(unrecognizedDir, userSymlink, "dir");
    const fakeBin = fakePythonBin(root);

    const completed = runNodePrune(root, ["--all", "--backend=agents", `--agents-root=${targetRoot}`], fakeBin);

    assert.equal(completed.status, 0, completed.stderr);
    assert.match(completed.stdout, new RegExp(`removed managed skill dir ${installed.targetSkillDir.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`));
    assert.match(completed.stdout, new RegExp(`removed managed skill dir ${staleDir.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`));
    assert.equal(completed.stderr.includes("unexpected-python"), false);
    assert.equal(existsSync(installed.targetSkillDir), false);
    assert.equal(existsSync(staleDir), false);
    assert.equal(existsSync(foreignDir), true);
    assert.equal(existsSync(invalidDir), true);
    assert.equal(existsSync(unrecognizedDir), true);
    assert.equal(existsSync(userFile), true);
    assert.equal(lstatSync(userSymlink).isSymbolicLink(), true);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("aw-installer prune agents handles missing and invalid target roots without Python", () => {
  const missingRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  const wrongTypeRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  const symlinkRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  const brokenSymlinkRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(missingRoot, "demo-skill");
    const missingTargetRoot = join(missingRoot, ".agents", "skills");
    const missingFakeBin = fakePythonBin(missingRoot);
    const missing = runNodePrune(
      missingRoot,
      ["--all", "--backend=agents", `--agents-root=${missingTargetRoot}`],
      missingFakeBin,
    );
    assert.equal(missing.status, 0, missing.stderr);
    assert.match(missing.stdout, new RegExp(`no managed skill dirs found at ${missingTargetRoot.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`));
    assert.equal(missing.stderr.includes("unexpected-python"), false);

    seedMinimalAgentsSource(wrongTypeRoot, "demo-skill");
    const wrongTypeTargetRoot = join(wrongTypeRoot, ".agents", "skills");
    mkdirSync(join(wrongTypeRoot, ".agents"), { recursive: true });
    writeFileSync(wrongTypeTargetRoot, "not a directory\n", "utf8");
    const wrongTypeFakeBin = fakePythonBin(wrongTypeRoot);
    const wrongType = runNodePrune(
      wrongTypeRoot,
      ["--all", "--backend=agents", `--agents-root=${wrongTypeTargetRoot}`],
      wrongTypeFakeBin,
    );
    assert.equal(wrongType.status, 1);
    assert.equal(wrongType.stdout, "");
    assert.match(wrongType.stderr, /Cannot prune managed installs because target root is not ready:/);
    assert.match(wrongType.stderr, /wrong-target-root-type/);
    assert.equal(wrongType.stderr.includes("unexpected-python"), false);

    seedMinimalAgentsSource(symlinkRoot, "demo-skill");
    const symlinkTargetRoot = join(symlinkRoot, ".agents", "skills");
    const symlinkTarget = join(symlinkRoot, "real-skills");
    mkdirSync(join(symlinkRoot, ".agents"), { recursive: true });
    mkdirSync(symlinkTarget);
    symlinkSync(symlinkTarget, symlinkTargetRoot, "dir");
    const symlinkFakeBin = fakePythonBin(symlinkRoot);
    const symlinkResult = runNodePrune(
      symlinkRoot,
      ["--all", "--backend=agents"],
      symlinkFakeBin,
    );
    assert.equal(symlinkResult.status, 1);
    assert.equal(symlinkResult.stdout, "");
    assert.match(symlinkResult.stderr, /wrong-target-root-type/);
    assert.match(symlinkResult.stderr, /target root must be a real directory, not a symlink/);
    assert.equal(symlinkResult.stderr.includes("unexpected-python"), false);

    seedMinimalAgentsSource(brokenSymlinkRoot, "demo-skill");
    const brokenTargetRoot = join(brokenSymlinkRoot, ".agents", "skills");
    mkdirSync(join(brokenSymlinkRoot, ".agents"), { recursive: true });
    symlinkSync(join(brokenSymlinkRoot, "missing-skills"), brokenTargetRoot, "dir");
    const brokenFakeBin = fakePythonBin(brokenSymlinkRoot);
    const broken = runNodePrune(
      brokenSymlinkRoot,
      ["--all", "--backend=agents"],
      brokenFakeBin,
    );
    assert.equal(broken.status, 1);
    assert.equal(broken.stdout, "");
    assert.match(broken.stderr, /broken-target-root-symlink/);
    assert.match(broken.stderr, /target root is a broken symlink/);
    assert.equal(broken.stderr.includes("unexpected-python"), false);
  } finally {
    rmSync(missingRoot, { recursive: true, force: true });
    rmSync(wrongTypeRoot, { recursive: true, force: true });
    rmSync(symlinkRoot, { recursive: true, force: true });
    rmSync(brokenSymlinkRoot, { recursive: true, force: true });
  }
});

test("aw-installer prune agents matches Python scan failure output shape", () => {
  if (process.platform === "win32") {
    return;
  }
  const nodeRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  const pythonRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  let nodeTargetRoot = null;
  let pythonTargetRoot = null;
  try {
    seedMinimalAgentsSource(nodeRoot, "demo-skill");
    seedMinimalAgentsSource(pythonRoot, "demo-skill");
    nodeTargetRoot = join(nodeRoot, ".agents", "skills");
    pythonTargetRoot = join(pythonRoot, ".agents", "skills");
    mkdirSync(nodeTargetRoot, { recursive: true });
    mkdirSync(pythonTargetRoot, { recursive: true });
    chmodSync(nodeTargetRoot, 0);
    chmodSync(pythonTargetRoot, 0);

    const nodeResult = runNodePrune(nodeRoot, ["--all", "--backend=agents", `--agents-root=${nodeTargetRoot}`]);
    const pythonResult = runPythonPrune(pythonRoot, ["--all", "--backend=agents", `--agents-root=${pythonTargetRoot}`]);
    const normalizeNodeRoot = (value) => value.replaceAll(nodeRoot, "<ROOT>");
    const normalizePythonRoot = (value) => value.replaceAll(pythonRoot, "<ROOT>");

    assert.equal(nodeResult.status, pythonResult.status);
    assert.equal(nodeResult.stdout, pythonResult.stdout);
    assert.match(normalizeNodeRoot(nodeResult.stderr), /Failed to scan managed install pruning at <ROOT>\/\.agents\/skills:/);
    assert.match(normalizePythonRoot(pythonResult.stderr), /Failed to scan managed install pruning at <ROOT>\/\.agents\/skills:/);
  } finally {
    if (nodeTargetRoot !== null && existsSync(nodeTargetRoot)) {
      chmodSync(nodeTargetRoot, 0o755);
    }
    if (pythonTargetRoot !== null && existsSync(pythonTargetRoot)) {
      chmodSync(pythonTargetRoot, 0o755);
    }
    rmSync(nodeRoot, { recursive: true, force: true });
    rmSync(pythonRoot, { recursive: true, force: true });
  }
});

test("aw-installer prune agents retains malformed same-backend marker shapes", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const installed = seedInstalledAgentsSkill(root, "demo-skill");
    const targetRoot = installed.targetRoot;
    const malformedMarkers = [
      ["wrong-version", { ...installed.marker, marker_version: "aw-managed-skill-marker.v1" }],
      ["missing-key", {
        marker_version: "aw-managed-skill-marker.v2",
        backend: "agents",
        skill_id: "missing-key",
        payload_version: "agents-skill-payload.v1",
      }],
      ["extra-key", { ...installed.marker, skill_id: "extra-key", extra: true }],
      ["non-string", { ...installed.marker, skill_id: 1 }],
    ];
    for (const [name, marker] of malformedMarkers) {
      const dir = join(targetRoot, name);
      mkdirSync(dir, { recursive: true });
      writeFileSync(join(dir, "aw.marker"), `${JSON.stringify(marker, null, 2)}\n`, "utf8");
    }
    const fakeBin = fakePythonBin(root);

    const completed = runNodePrune(root, ["--all", "--backend=agents", `--agents-root=${targetRoot}`], fakeBin);

    assert.equal(completed.status, 0, completed.stderr);
    assert.equal(completed.stderr.includes("unexpected-python"), false);
    assert.equal(existsSync(installed.targetSkillDir), false);
    for (const [name] of malformedMarkers) {
      assert.equal(existsSync(join(targetRoot, name)), true);
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("managed directory identity guard refuses replacement during pruning", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const targetDir = join(root, "managed");
    const replacement = join(root, "replacement");
    mkdirSync(targetDir);
    mkdirSync(replacement);
    const identity = installer.childDirectoryIdentity(targetDir);
    assert.notEqual(identity, null);

    rmSync(targetDir, { recursive: true });
    symlinkSync(replacement, targetDir, "dir");

    assert.throws(
      () => installer.assertManagedDirectoryIdentityCurrent(identity),
      /Managed skill dir changed during pruning, refusing to remove:/,
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("aw-installer prune agents matches Python reference output shape", () => {
  const nodeRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  const pythonRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const nodeInstalled = seedInstalledAgentsSkill(nodeRoot, "demo-skill");
    const pythonInstalled = seedInstalledAgentsSkill(pythonRoot, "demo-skill");

    const nodeResult = runNodePrune(nodeRoot, ["--all", "--backend=agents", `--agents-root=${nodeInstalled.targetRoot}`]);
    const pythonResult = runPythonPrune(pythonRoot, ["--all", "--backend=agents", `--agents-root=${pythonInstalled.targetRoot}`]);
    const normalizeNodeRoot = (value) => value.replaceAll(nodeRoot, "<ROOT>");
    const normalizePythonRoot = (value) => value.replaceAll(pythonRoot, "<ROOT>");

    assert.equal(nodeResult.status, pythonResult.status);
    assert.equal(normalizeNodeRoot(nodeResult.stdout), normalizePythonRoot(pythonResult.stdout));
    assert.equal(nodeResult.stderr, pythonResult.stderr);
    assert.equal(existsSync(nodeInstalled.targetSkillDir), false);
    assert.equal(existsSync(pythonInstalled.targetSkillDir), false);
  } finally {
    rmSync(nodeRoot, { recursive: true, force: true });
    rmSync(pythonRoot, { recursive: true, force: true });
  }
});

test("aw-installer leaves out-of-scope install and mutating commands on Python reference path", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(root, "demo-skill");
    const fakeBin = fakePythonBin(root);
    const commands = [
      ["install", "--backend", "claude"],
      ["install", "--backend", "agents", "--source", "github"],
      ["prune", "--backend", "agents"],
      ["prune", "--all", "--backend", "claude"],
      ["update", "--backend", "agents", "--yes", "--source", "github"],
      ["update", "--backend", "agents", "--json", "--yes"],
      ["update", "--backend", "claude", "--yes"],
    ];

    for (const args of commands) {
      const completed = runAwInstaller(root, args, fakeBin);
      assert.equal(completed.status, 97, args.join(" "));
      assert.equal(completed.stdout, "");
      assert.match(completed.stderr, /unexpected-python/, args.join(" "));
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("updatePlanSummary reports a nonblocking dry-run plan for missing target root", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const canonicalDir = join(root, "product", "harness", "skills", "demo-skill");
    const payloadDir = join(root, "product", "harness", "adapters", "agents", "skills", "demo-skill");
    const targetRoot = join(root, ".agents", "skills");
    mkdirSync(canonicalDir, { recursive: true });
    mkdirSync(payloadDir, { recursive: true });
    const payload = {
      payload_version: "agents-skill-payload.v1",
      backend: "agents",
      skill_id: "demo-skill",
      target_dir: "aw-demo-skill",
      target_entry_name: "SKILL.md",
      required_payload_files: ["SKILL.md", "payload.json", "aw.marker"],
      canonical_dir: "product/harness/skills/demo-skill",
      canonical_paths: ["product/harness/skills/demo-skill/SKILL.md"],
      payload_policy: "canonical-copy",
      reference_distribution: "copy-listed-canonical-paths",
    };
    writeFileSync(join(canonicalDir, "SKILL.md"), "# Demo\n", "utf8");
    writeFileSync(join(payloadDir, "payload.json"), `${JSON.stringify(payload, null, 2)}\n`, "utf8");

    const summary = installer.updatePlanSummary({
      sourceKind: "package",
      sourceRef: "package-local",
      sourceRoot: root,
      targetRoot,
      adapterSkillsDir: join(root, "product", "harness", "adapters", "agents", "skills"),
    });

    assert.equal(summary.backend, "agents");
    assert.deepEqual(summary.operation_sequence, ["prune --all", "check_paths_exist", "install", "verify"]);
    assert.deepEqual(summary.planned_target_paths, [join(targetRoot, "aw-demo-skill")]);
    assert.equal(summary.issue_count, 1);
    assert.equal(summary.issues[0].code, "missing-target-root");
    assert.equal(summary.blocking_issue_count, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("aw-installer update agents yes installs and verifies from missing root without Python", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(root, "demo-skill");
    const targetRoot = join(root, "custom-agents-skills");
    const fakeBin = fakePythonBin(root);

    const completed = runNodeUpdate(root, ["--backend=agents", "--yes", `--agents-root=${targetRoot}`], fakeBin);

    assert.equal(completed.status, 0, completed.stderr);
    assert.equal(completed.stderr.includes("unexpected-python"), false);
    const expectedFragments = [
      `[agents] update plan for ${targetRoot}`,
      "sequence: prune --all -> check_paths_exist -> install -> verify",
      "blocking preflight issues: 0",
      "[agents] applying update",
      `no managed skill dirs found at ${targetRoot}`,
      `[agents] ok: no conflicting target paths at ${targetRoot}`,
      `created target root ${targetRoot}`,
      `installed skill demo-skill -> ${join(targetRoot, "aw-demo-skill")}`,
      `[agents] ok: target root is ready at ${targetRoot}`,
      "[agents] update complete",
    ];
    let lastIndex = -1;
    for (const fragment of expectedFragments) {
      const index = completed.stdout.indexOf(fragment);
      assert.notEqual(index, -1, fragment);
      assert.ok(index > lastIndex, fragment);
      lastIndex = index;
    }
    assert.equal(existsSync(join(targetRoot, "aw-demo-skill", "SKILL.md")), true);
    assert.equal(existsSync(join(root, ".agents", "skills")), false);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("aw-installer update agents yes matches Python reference output shape", () => {
  const nodeRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  const pythonRoot = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(nodeRoot, "demo-skill");
    seedMinimalAgentsSource(pythonRoot, "demo-skill");
    const nodeResult = runNodeUpdate(nodeRoot, ["--backend=agents", "--yes"]);
    const pythonResult = runPythonUpdate(pythonRoot, ["--backend=agents", "--yes"]);
    const normalizeNodeRoot = (value) => value.replaceAll(nodeRoot, "<ROOT>");
    const normalizePythonRoot = (value) => value.replaceAll(pythonRoot, "<ROOT>");

    assert.equal(nodeResult.status, pythonResult.status);
    assert.equal(normalizeNodeRoot(nodeResult.stdout), normalizePythonRoot(pythonResult.stdout));
    assert.equal(normalizeNodeRoot(nodeResult.stderr), normalizePythonRoot(pythonResult.stderr));
    assert.equal(existsSync(join(nodeRoot, ".agents", "skills", "aw-demo-skill", "aw.marker")), true);
    assert.equal(existsSync(join(pythonRoot, ".agents", "skills", "aw-demo-skill", "aw.marker")), true);
  } finally {
    rmSync(nodeRoot, { recursive: true, force: true });
    rmSync(pythonRoot, { recursive: true, force: true });
  }
});

test("aw-installer update agents yes refreshes drifted and stale managed installs without Python", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const installed = seedInstalledAgentsSkill(root, "demo-skill");
    const targetSkillPath = join(installed.targetSkillDir, "SKILL.md");
    writeFileSync(join(installed.canonicalDir, "SKILL.md"), "# demo-skill\n\n# updated source\n", "utf8");
    writeFileSync(
      join(installed.targetSkillDir, "aw.marker"),
      `${JSON.stringify({
        marker_version: "aw-managed-skill-marker.v2",
        backend: "agents",
        skill_id: "legacy-demo-skill",
        payload_version: "agents-skill-payload.v0",
        payload_fingerprint: "old-fingerprint",
      }, null, 2)}\n`,
      "utf8",
    );
    const fakeBin = fakePythonBin(root);

    const completed = runNodeUpdate(root, ["--backend=agents", "--yes"], fakeBin);

    assert.equal(completed.status, 0, completed.stderr);
    assert.equal(completed.stderr.includes("unexpected-python"), false);
    assert.match(completed.stdout, new RegExp(`removed managed skill dir ${installed.targetSkillDir.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`));
    assert.equal(readFileSync(targetSkillPath, "utf8"), "# demo-skill\n\n# updated source\n");
    const verify = runNodeVerify(root, ["--backend=agents"], fakeBin);
    assert.equal(verify.status, 0, verify.stderr);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("aw-installer update agents yes blocks preflight issues without applying", () => {
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    seedMinimalAgentsSource(root, "demo-skill");
    seedMinimalAgentsSource(root, "other-skill");
    const targetRoot = join(root, ".agents", "skills");
    const unmanagedDir = join(targetRoot, "aw-demo-skill");
    mkdirSync(unmanagedDir, { recursive: true });
    writeFileSync(join(unmanagedDir, "SKILL.md"), "# unmanaged\n", "utf8");
    const fakeBin = fakePythonBin(root);

    const completed = runNodeUpdate(root, ["--backend=agents", "--yes"], fakeBin);

    assert.equal(completed.status, 1);
    assert.match(completed.stdout, /blocking preflight issues: 1/);
    assert.match(completed.stdout, /unrecognized-target-directory/);
    assert.equal(completed.stdout.includes("[agents] applying update"), false);
    assert.equal(completed.stdout.includes("installed skill"), false);
    assert.match(completed.stderr, /error: \[agents\] update blocked by 1 preflight issue\(s\)/);
    assert.equal(completed.stderr.includes("unexpected-python"), false);
    assert.equal(existsSync(unmanagedDir), true);
    assert.equal(existsSync(join(targetRoot, "aw-other-skill")), false);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("aw-installer update agents yes prints recovery hint after apply failure", () => {
  if (process.platform === "win32") {
    return;
  }
  const root = mkdtempSync(join(tmpdir(), "aw-installer-test-"));
  try {
    const installed = seedInstalledAgentsSkill(root, "demo-skill");
    chmodSync(installed.targetRoot, 0o555);
    const fakeBin = fakePythonBin(root);

    const completed = runNodeUpdate(root, ["--backend=agents", "--yes"], fakeBin);

    assert.equal(completed.status, 1);
    assert.match(completed.stdout, /blocking preflight issues: 0/);
    assert.match(completed.stdout, /\[agents\] applying update/);
    assert.match(completed.stderr, /Failed to remove managed skill dir/);
    assert.match(completed.stderr, /recovery: the update may be partially applied/);
    assert.match(completed.stderr, /aw-installer update --backend agents --yes/);
    assert.equal(completed.stderr.includes("unexpected-python"), false);
    assert.equal(existsSync(installed.targetSkillDir), true);
  } finally {
    const targetRoot = join(root, ".agents", "skills");
    if (existsSync(targetRoot)) {
      chmodSync(targetRoot, 0o755);
    }
    rmSync(root, { recursive: true, force: true });
  }
});
