const assert = require("node:assert/strict");
const { createHash } = require("node:crypto");
const { mkdirSync, mkdtempSync, rmSync, writeFileSync } = require("node:fs");
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
