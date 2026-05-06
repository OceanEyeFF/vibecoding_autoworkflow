---
title: "aw-installer Release Standard Flow"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# aw-installer Release Standard Flow

> Purpose: define the operator-facing sequence for moving an approved release candidate through merge PR, GitHub Release, publish workflow, and post-publish verification.

This page belongs to [Governance](./README.md).

Manages branch/merge sequence, GitHub Release creation, publish workflow observation and post-publish verification; does not manage pre-publish readiness (see Pre-Publish Governance), channel policy (see Release Channel Governance) or carrier model (see Release Operation Model).

## Preconditions

Only start after passing Pre-Publish Governance, tuple still satisfies Channel Governance, root `package.json` has approved version+lock, and release notes are ready.

## 1. Refresh Local State

```bash
git status --short --branch
git fetch --no-tags origin master develop-main --prune
git fetch --no-tags origin refs/tags/v<package.version>:refs/tags/v<package.version>
gh release view v<package.version> --json tagName,url,isPrerelease,isDraft,name,targetCommitish,publishedAt
npm view aw-installer@<package.version> version --json
```

If tag or published version exists, stop and resolve conflict before continuing.

## 2. Push And Open The Merge PR

```bash
git push origin develop-main
```

```bash
gh pr create \
  --draft \
  --base master \
  --head develop-main \
  --title "Merge develop-main into master" \
  --body "<summary, impact, and validation>"
```

```bash
gh pr checks <pr-number> --watch --interval 10 --fail-fast
gh pr view <pr-number> --json number,url,isDraft,mergeable,reviewDecision,state,headRefName,baseRefName,headRefOid,statusCheckRollup
```

## 3. Merge To `master`

Merge only after PR is not draft, checks pass, and review gates are satisfied.

```bash
gh pr view <pr-number> --json state,mergedAt,mergeCommit,url,baseRefName,headRefName
git fetch --no-tags origin master
git rev-parse origin/master
```

The GitHub Release must target the merge commit on `master`.

## 4. Create The GitHub Release

The tag must exactly match `v<package.version>`, and the body must include `aw-installer-publish-approved: v<package.version>`:

```bash
gh release create v<package.version> \
  --target <master-merge-commit-sha> \
  --title "aw-installer v<package.version>" \
  --prerelease \
  --notes $'aw-installer-publish-approved: v<package.version>\n\n<version-specific release notes>'
```

## 5. Watch The Publish Workflow

```bash
gh run list --workflow publish.yml --limit 5 --json databaseId,displayTitle,event,headBranch,headSha,status,conclusion,url,createdAt
gh run watch <run-id> --exit-status
```

If the workflow blocks on the `npm` environment or Trusted Publishing authentication, treat that as an external operator/configuration issue.

## 6. Verify Published State

```bash
gh release view v<package.version> --json tagName,url,isPrerelease,isDraft,name,targetCommitish,publishedAt
gh run view <run-id> --json databaseId,status,conclusion,url,headSha,displayTitle,event,createdAt,updatedAt
npm view aw-installer@<package.version> version dist-tags --json
npm view aw-installer dist-tags --json
```

For RC releases on `next`, verify that `next` moved and `latest` stayed unchanged unless this was an explicitly approved stable release.

## 7. Hand Off To Registry Smoke

After publish, run registry `npx` smoke through [npx Command Test Execution](../testing/npx-command-test-execution.md).
