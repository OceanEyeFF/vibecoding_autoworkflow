---
title: "aw-installer Release Standard Flow"
status: active
updated: 2026-05-06
owner: aw-kernel
last_verified: 2026-05-06
---
# aw-installer Release Standard Flow

> 目的：定义已批准 release candidate 经过 merge PR、GitHub Release、publish workflow 与 post-publish verification 的 operator-facing 顺序。

本页属于 [Governance](./README.md)。

Manages branch/merge sequence, GitHub Release creation, publish workflow observation and post-publish verification. For pre-publish readiness see Pre-Publish Governance, for channel policy see Release Channel Governance, for carrier model see Release Operation Model.

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
npm view aw-installer@latest version gitHead dist.tarball --json
npm view aw-installer@next version gitHead dist.tarball --json
```

For RC releases on `next`, verify that `next` moved and `latest` stayed unchanged unless this was an explicitly approved stable release.

## 7. Sync Version Facts

After registry verification and before final release handback, invoke [doc-catch-up-worker-skill](../../../product/harness/skills/doc-catch-up-worker-skill/SKILL.md) in `version fact sync` mode.

The handoff must include:

- source version facts: root `package.json`, approval lock, CLI `--version`, GitHub Release tag
- VCS tracking facts: git branch, commit SHA, tag and remote ref; SVN URL/revision/branch path only when the target is an SVN working copy
- published version facts: npm dist-tags, published versions, `gitHead`, tarball URLs
- release evidence: GitHub Release view, publish workflow run, registry query output
- doc update decision: documents updated and documents intentionally left unchanged

At minimum, review [Release Channel Governance](./aw-installer-release-channel-governance.md), [Pre-Publish Governance](./aw-installer-pre-publish-governance.md), [npx Command Test Execution](../testing/npx-command-test-execution.md), backend usage-help pages, and root `README.md`. Update only pages whose facts changed or whose freshness is being verified in this release closeout.

## 8. Hand Off To Registry Smoke

After publish, run registry `npx` smoke through [npx Command Test Execution](../testing/npx-command-test-execution.md).
