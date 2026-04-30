---
title: "GitHub Release Publish Standard Flow"
status: active
updated: 2026-04-30
owner: aw-kernel
last_verified: 2026-04-30
---
# GitHub Release Publish Standard Flow

> Purpose: define the operator-facing standard flow for moving `develop-main` into `master`, creating an `aw-installer` GitHub Release, and letting the repository publish workflow move the npm release channel. This page records the reusable process; one-off evidence belongs in PRs, GitHub Actions runs, release notes, or worktrack handoff.

This page belongs to [Deploy Runbooks](./README.md). It applies after the candidate has already passed [aw-installer npx Pre-Publish Check](./aw-installer-npx-pre-publish-check.md) and satisfies [aw-installer Release Channel Contract](./release-channel-contract.md). The publish carrier is defined by [aw-installer Release Operation Model](./aw-installer-release-operation-model.md).

## Preconditions

- The release candidate version is already encoded in root `package.json`.
- `package.json` `awInstallerRelease` binds the exact approved tuple:
  - `approvedVersion`
  - `approvedGitTag`
  - `approvedChannel`
- The candidate branch contains the current package payload, docs, tests, and approval lock.
- npm has not already published the same immutable package version.
- The GitHub Release tag does not already exist.
- `gh` is authenticated against the target GitHub repository.
- The operator understands whether the release is prerelease or stable:
  - semver prerelease with `rc`, `alpha`, or `beta` publishes to npm `next`
  - semver prerelease with `canary` publishes to npm `canary`
  - stable semver publishes to npm `latest`

## 1. Refresh Local Repository State

Start from a clean worktree and refresh the release branches without clobbering local candidate work:

```bash
git status --short --branch
git fetch --no-tags origin master develop-main --prune
```

If local `master` has no commits that are absent from `origin/master`, fast-forward the local branch reference:

```bash
git log --oneline origin/master..master
git branch -f master origin/master
```

Fetch only the release tag being operated on. Avoid broad `--tags` if a local historical tag is known to differ from the remote:

```bash
git fetch --no-tags origin refs/tags/v<package.version>:refs/tags/v<package.version>
```

For a tag that does not exist yet, confirm absence instead:

```bash
git ls-remote --tags origin refs/tags/v<package.version>
gh release view v<package.version> --json tagName,url,isPrerelease,isDraft,name,targetCommitish,publishedAt
npm view aw-installer@<package.version> version --json
```

`npm view aw-installer@<package.version>` should fail with a 404 before a first publish of that version.

## 2. Run Local Release-Candidate Checks

Run the checks that match the changed surface before opening the merge PR:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/folder_logic_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/governance_semantic_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/closeout_acceptance_gate.py --json
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend claude
```

The closeout acceptance gate includes package and tarball smoke coverage. If it fails, do not publish; fix the candidate and rerun the relevant checks.

## 3. Push `develop-main`

Push the candidate branch to GitHub:

```bash
git push origin develop-main
```

If the execution environment blocks the porcelain `git push` but the update is confirmed fast-forward, the equivalent ref update is:

```bash
git merge-base --is-ancestor origin/develop-main develop-main
git send-pack git@github-work:OceanEyeFF/vibecoding_autoworkflow.git \
  refs/heads/develop-main:refs/heads/develop-main
```

Use this only for a confirmed fast-forward update to the intended GitHub remote.

## 4. Open And Check The Merge PR

Create a PR from `develop-main` to `master`:

```bash
gh pr create \
  --draft \
  --base master \
  --head develop-main \
  --title "Merge develop-main into master" \
  --body "<summary, impact, and validation>"
```

Wait for GitHub checks:

```bash
gh pr checks <pr-number> --watch --interval 10 --fail-fast
gh pr view <pr-number> --json number,url,isDraft,mergeable,reviewDecision,state,headRefName,baseRefName,headRefOid,statusCheckRollup
```

GitHub does not allow the PR author to approve their own PR. If branch protection requires review approval, use a different authorized reviewer account.

## 5. Merge To `master`

Merge only after the PR is no longer draft, required checks pass, and any required review gates are satisfied.

After merge, record the merge commit:

```bash
gh pr view <pr-number> --json state,mergedAt,mergeCommit,url,baseRefName,headRefName
git fetch --no-tags origin master
git rev-parse origin/master
```

The GitHub Release must target the merge commit on `master`, not an unmerged candidate branch commit.

## 6. Create The GitHub Release

Create a GitHub Release whose tag exactly matches `v<package.version>`. For prerelease versions, pass `--prerelease`. The release body must include the exact approval marker consumed by `.github/workflows/publish.yml`:

```text
aw-installer-publish-approved: v<package.version>
```

Command shape:

```bash
gh release create v<package.version> \
  --target <master-merge-commit-sha> \
  --title "aw-installer v<package.version>" \
  --prerelease \
  --notes $'aw-installer-publish-approved: v<package.version>\n\n## Summary\n- ...\n\n## Validation\n- ...'
```

The GitHub Release `published` event triggers `.github/workflows/publish.yml`.

## 7. Watch Publish Workflow

Find and watch the publish run:

```bash
gh run list --workflow publish.yml --limit 5 --json databaseId,displayTitle,event,headBranch,headSha,status,conclusion,url,createdAt
gh run watch <run-id> --exit-status
```

The workflow must complete these gates before npm publish:

- resolve release metadata
- folder logic check
- path governance check
- governance semantic check
- governance tests
- deploy regression tests
- deploy package smoke
- root package pack dry-run
- root package publish dry-run
- real publish guard
- `npm publish --provenance --access public --tag <derived-channel>`

If the workflow waits on the `npm` GitHub Environment or Trusted Publishing authentication, treat that as an external operator configuration issue and do not bypass the release contract.

## 8. Verify Published State

After the workflow succeeds, verify both GitHub and npm:

```bash
gh release view v<package.version> --json tagName,url,isPrerelease,isDraft,name,targetCommitish,publishedAt
gh run view <run-id> --json databaseId,status,conclusion,url,headSha,displayTitle,event,createdAt,updatedAt
npm view aw-installer@<package.version> version dist-tags --json
npm view aw-installer dist-tags --json
```

For an RC release on `next`, `next` must point at the new version while `latest` remains unchanged unless this is an explicitly approved stable release.

## 9. Run Registry `npx` Smoke

Use a temporary target repository and force package-local payload resolution by clearing source and target overrides:

```bash
tmpdir="$(mktemp -d /tmp/aw-npx-install-test-XXXXXXXX)"
git init -q "$tmpdir"
printf '# AW npx install smoke\n' > "$tmpdir/README.md"

AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" \
  npx --yes --package aw-installer@next -- aw-installer --version

AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" \
  npx --yes --package aw-installer@next -- aw-installer update --backend agents --json
AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" \
  npx --yes --package aw-installer@next -- aw-installer update --backend agents --yes
AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" \
  npx --yes --package aw-installer@next -- aw-installer verify --backend agents

AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" \
  npx --yes --package aw-installer@next -- aw-installer update --backend claude --json
AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" \
  npx --yes --package aw-installer@next -- aw-installer update --backend claude --yes
AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" \
  npx --yes --package aw-installer@next -- aw-installer verify --backend claude
```

Run `npx` commands serially when sharing the same npm cache. Parallel `npx --package aw-installer@next` executions can race inside npm's `_npx` cache.

Clean the temporary target after evidence is collected:

```bash
rm -rf "$tmpdir"
```

## Verified Example: `0.4.1-rc.2`

The `0.4.1-rc.2` release followed this flow:

- PR: `develop-main -> master`, `#19`
- merge commit: `7f7536a538f16fb77d80e5f54a148bcff04beba4`
- GitHub Release: `v0.4.1-rc.2`
- Release URL: `https://github.com/OceanEyeFF/vibecoding_autoworkflow/releases/tag/v0.4.1-rc.2`
- publish workflow run: `https://github.com/OceanEyeFF/vibecoding_autoworkflow/actions/runs/25123594586`
- npm result:
  - `next`: `0.4.1-rc.2`
  - `latest`: `0.4.0-rc.1`
- post-publish `npx` smoke confirmed:
  - `agents` writes `.agents/skills`
  - `claude` writes `.claude/skills`
  - both backends verify in the same temporary target repository

Do not treat this historical tuple as authorization for a future release. Future releases must repeat the approval-lock, PR, GitHub Release, publish workflow, registry verification, and smoke sequence with their own version and tag.
