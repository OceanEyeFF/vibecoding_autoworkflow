---
title: "aw-installer External Target Smoke"
status: active
updated: 2026-04-27
owner: aw-kernel
last_verified: 2026-04-27
---
# aw-installer External Target Smoke

> Purpose: provide an operator-run smoke procedure and report template for proving a local `aw-installer` package tarball can install and verify the `agents` payload in isolated target repositories. This page does not authorize or run real `npm publish`.

This page belongs to [Deploy Runbooks](./README.md). It supports [aw-installer Release Candidate Prep](./aw-installer-release-candidate-prep.md) by producing external target smoke evidence.

## Scope

This smoke proves:

- the root package can be packed as a local `.tgz`.
- packaged `aw-installer` can run through `npm exec --package <tgz>`.
- source payload resolves from the package when `AW_HARNESS_REPO_ROOT=""`.
- target root resolves from the temporary target repository when `AW_HARNESS_TARGET_REPO_ROOT=""`.
- `agents` install, verify, and update apply work in isolated target repositories.

It does not prove:

- real npm publish readiness by itself.
- remote update, channel resolution, self-update, signing, or automatic rollback.
- support for `claude` or `opencode` deploy backends.

## Preconditions

- Run from the repository root on the release-candidate checkpoint under review.
- Node.js satisfies the root `package.json` engine requirement.
- The worktree is clean or the operator has explicitly recorded why local changes are part of the candidate.
- The package remains local/pre-release unless a separate real publish approval exists.

## Operation

Run this block from the repository root:

```bash
set -eu

tmpdir="$(mktemp -d)"
echo "tmpdir=$tmpdir"

node --version > "$tmpdir/node.version"
npm --version > "$tmpdir/npm.version"
git rev-parse --abbrev-ref HEAD > "$tmpdir/git.branch"
git rev-parse HEAD > "$tmpdir/git.commit"

npm pack --json --pack-destination "$tmpdir" > "$tmpdir/pack.json"
package_file="$(
  node -e "const fs = require('node:fs'); const payload = JSON.parse(fs.readFileSync(process.argv[1], 'utf8')); console.log(payload[0].filename);" "$tmpdir/pack.json"
)"
package_path="$tmpdir/$package_file"

for target_name in target-alpha target-beta; do
  target_repo="$tmpdir/$target_name"
  mkdir -p "$target_repo"
  (
    cd "$target_repo"
    AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer --help > "$tmpdir/$target_name.help.out"
    AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer --version > "$tmpdir/$target_name.version.out"

    if AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer tui > "$tmpdir/$target_name.tui.out" 2> "$tmpdir/$target_name.tui.err"; then
      echo "expected aw-installer tui to require an interactive terminal for $target_name" >&2
      exit 1
    fi
    test ! -s "$tmpdir/$target_name.tui.out"
    grep -F "aw-installer tui requires an interactive terminal" "$tmpdir/$target_name.tui.err" > "$tmpdir/$target_name.tui.guard"

    AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer diagnose --backend agents --json > "$tmpdir/$target_name.diagnose.before.json"
    AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer update --backend agents --json > "$tmpdir/$target_name.update.dry-run.json"
    AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer install --backend agents > "$tmpdir/$target_name.install.out"
    AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer verify --backend agents > "$tmpdir/$target_name.verify.out"
    AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer update --backend agents --yes > "$tmpdir/$target_name.update.apply.out"
    AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer diagnose --backend agents --json > "$tmpdir/$target_name.diagnose.after.json"
  )
done

echo "package_path=$package_path"
echo "target_alpha=$tmpdir/target-alpha"
echo "target_beta=$tmpdir/target-beta"
echo "evidence_dir=$tmpdir"
```

## Pass Criteria

- Both target repositories complete the full command sequence.
- Non-interactive `aw-installer tui` fails with the expected guard message.
- `diagnose --json` and `update --json` run before mutation and produce JSON evidence.
- `install`, `verify`, and `update --yes` succeed in each target repository.
- After install/update, each target reports 17 managed installs, 0 conflicts, and 0 unrecognized entries.
- Source root in diagnose output points to the package installation used by `npm exec`, not the source checkout.
- Target root points inside the temporary target repository.

## Report Template

Copy this template into the worktrack evidence or release-candidate evidence bundle and fill it with the smoke output.

```markdown
# aw-installer External Target Smoke Report

## Candidate Identity

| Field | Value |
| --- | --- |
| git branch | N/A |
| git commit | N/A |
| package file | N/A |
| package version | N/A |
| node version | N/A |
| npm version | N/A |
| run date | N/A |
| operator | N/A |

## Target Summary

| Target | Path | Target Type | Result | Notes |
| --- | --- | --- | --- | --- |
| target-alpha | N/A | isolated temporary repo | N/A | N/A |
| target-beta | N/A | isolated temporary repo | N/A | N/A |

## Command Matrix

| Target | help | version | tui guard | diagnose before | update dry-run | install | verify | update --yes | diagnose after |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| target-alpha | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| target-beta | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Diagnose Evidence

| Target | before issue_count | after issue_count | managed installs after | unrecognized after | conflict after |
| --- | ---: | ---: | ---: | ---: | ---: |
| target-alpha | N/A | N/A | N/A | N/A | N/A |
| target-beta | N/A | N/A | N/A | N/A | N/A |

## Source / Target Separation Check

- `AW_HARNESS_REPO_ROOT` cleared: N/A
- `AW_HARNESS_TARGET_REPO_ROOT` cleared: N/A
- package payload used instead of checkout payload: N/A
- target root resolved to temporary target repo: N/A
- observed package source root: N/A
- observed target roots: N/A

## Failures And Recovery

| Target | Failed Command | Symptom | Recovery Attempted | Final State |
| --- | --- | --- | --- | --- |
| N/A | N/A | N/A | N/A | N/A |

## Verdict

- passed_targets: N/A
- failed_targets: N/A
- repeated_failure_pattern: N/A
- release_candidate_ready_for_local_tgz_evidence: N/A
- real_npm_publish_approval_required: true
```

## Failure Handling

- If `npm pack` fails, stop and fix package surface before rerunning this smoke.
- If both targets fail with the same symptom, open a bugfix or test worktrack from the shared failure.
- If one target passes and one fails, preserve both evidence sets and mark the smoke partial.
- If any command would mutate a non-temporary target repository, stop and request explicit approval.
