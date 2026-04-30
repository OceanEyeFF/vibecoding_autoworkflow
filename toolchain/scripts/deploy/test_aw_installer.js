const assert = require("node:assert/strict");
const { createHash } = require("node:crypto");
const { mkdirSync, mkdtempSync, rmSync, symlinkSync, writeFileSync } = require("node:fs");
const { tmpdir } = require("node:os");
const { join } = require("node:path");
const test = require("node:test");

const installer = require("./bin/aw-installer.js");

test("pythonCandidates avoids the usually-missing Linux python alias", () => {
  const commands = installer.pythonCandidates().map((candidate) => candidate.command);
  if (process.platform === "win32") {
    assert.deepEqual(commands, ["py", "python", "python3"]);
  } else {
    assert.deepEqual(commands, ["python3"]);
  }
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
    }),
    {
      AW_HARNESS_REPO_ROOT: "/repo",
      HOME: "/home/demo",
      PATH: "/bin",
      PYTHONDONTWRITEBYTECODE: "0",
      HTTPS_PROXY: "http://proxy",
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
    assert.deepEqual([...installer.allKnownTargetDirs(bindings)].sort(), [
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
      () => installer.allKnownTargetDirs(bindings),
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

    const plan = installer.buildInstallPlan(
      binding,
      targetRoot,
      { sourceRoot: root },
      loadedPayloads,
    );

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
