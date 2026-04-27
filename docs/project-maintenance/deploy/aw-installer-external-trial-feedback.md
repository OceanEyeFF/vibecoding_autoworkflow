---
title: "aw-installer External Trial Feedback Contract"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer External Trial Feedback Contract

> Purpose: define the target list template and feedback contract for post-RC `aw-installer` external trials. This page does not recruit testers, publish npm packages, or store private repository identifiers.

This page belongs to [Deploy Runbooks](./README.md). It follows the candidate boundary in [aw-installer RC Approval Package](./aw-installer-rc-approval-package.md) and the non-publish rehearsal evidence in [aw-installer Non-Publish Release Rehearsal](./aw-installer-release-rehearsal.md).

GitHub issue entry points:

- [aw-installer trial feedback issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-trial-feedback.yml)
- [aw-installer bug or blocker issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-bug.yml)

## Control Signal

- trial_status: planned
- trial_sources:
  - programmer-owned repositories
  - forum volunteer repositories
- real_npm_publish_allowed: false
- public_recruitment_copy_in_scope: false
- private_repo_identifiers_allowed_in_long_term_docs: false
- supported_backend_for_trial: `agents`
- feedback_decision_goal: decide whether the next main contradiction is adoption, reliability, or documentation.

## Trial Target Categories

| Category | Purpose | Minimum count | Privacy rule |
|---|---|---:|---|
| programmer-owned repository | first realistic trial under trusted operator control | 2 | store only aliases such as `owned-alpha`, unless explicit approval allows names |
| forum volunteer repository | observe cold external operator friction | 2 | store only anonymized aliases and consented facts |
| intentionally unsupported repository | confirm failure messaging and recovery path | 1 | store only anonymized shape and failure category |

Do not store private repository names, organization names, URLs, tokens, logs with secrets, or user handles in long-term docs unless separately approved. Runtime evidence may use temporary local paths, but long-term writeback should keep only sanitized summaries.

## Trial Target List Template

| Alias | Category | Repo shape | OS/runtime | Operator type | Candidate source | Status | Notes |
|---|---|---|---|---|---|---|---|
| owned-alpha | programmer-owned | N/A | N/A | maintainer | local `.tgz` or approved RC | planned | N/A |
| owned-beta | programmer-owned | N/A | N/A | maintainer | local `.tgz` or approved RC | planned | N/A |
| forum-alpha | forum volunteer | N/A | N/A | external tester | separately approved candidate only unless local tarball handoff is explicit | planned | N/A |
| forum-beta | forum volunteer | N/A | N/A | external tester | separately approved candidate only unless local tarball handoff is explicit | planned | N/A |
| unsupported-alpha | unsupported shape | N/A | N/A | maintainer or tester | local `.tgz` or approved RC | planned | N/A |

## Command Feedback Fields

Each trial report should capture one row per target:

| Field | Required | Notes |
|---|---|---|
| target alias | yes | sanitized alias only |
| target category | yes | one of the categories above |
| candidate version/source | yes | local `.tgz`, approved RC version, or explicit checkout override |
| install command used | yes | redact paths if needed |
| `aw-installer --help` | yes | pass/fail |
| `aw-installer --version` | yes | observed version |
| non-interactive `aw-installer tui` guard | yes | pass/fail or N/A for interactive trial |
| `diagnose --backend agents --json` before install | yes | issue count and major issue codes |
| `update --backend agents --json` dry-run | yes | blocking issue count and planned operation sequence |
| `install --backend agents` | yes | pass/fail and first failure line |
| `verify --backend agents` | yes | pass/fail |
| `update --backend agents --yes` | conditional | run only with explicit target-owner approval |
| `diagnose --backend agents --json` after install/update | yes | issue count, managed install count, conflict count, unrecognized count |
| operator confusion | yes | short free-text summary |
| adoption blocker | yes | none, trust, workflow fit, install risk, unclear value, unsupported environment, other |
| reuse intent | yes | would reuse, would retry after fix, would not reuse, undecided |
| trust concern | yes | none, package provenance, target writes, update behavior, npm availability, other |
| workflow-fit concern | yes | none, command ergonomics, docs fit, team process fit, backend fit, other |
| recovery attempted | yes | command or documentation path used |
| final verdict | yes | passed, partial, failed, blocked |

## Operator Confusion Taxonomy

Use these labels to make feedback comparable:

| Label | Meaning |
|---|---|
| `entrypoint-confusion` | operator did not know which `aw-installer` command to run |
| `backend-confusion` | operator did not know why `--backend agents` is required |
| `target-root-confusion` | operator did not understand where files would be written |
| `update-boundary-confusion` | operator expected remote update, self-update, or channel update |
| `approval-boundary-confusion` | operator believed publish, destructive update, or public availability was already approved |
| `diagnose-output-confusion` | operator could not interpret JSON issue codes |
| `docs-navigation-confusion` | operator could not find the relevant runbook |
| `no-confusion-observed` | operator completed the trial without notable confusion |

## Trial Report Template

For GitHub-based feedback, prefer the structured issue templates above. Use the Markdown template below when collecting evidence outside GitHub or when preparing a batch summary.

```markdown
# aw-installer External Trial Report

## Candidate

- candidate source: N/A
- candidate version observed: N/A
- trial date: N/A
- operator type: N/A

## Target Summary

| Alias | Category | Repo shape | OS/runtime | Final verdict | Main issue |
|---|---|---|---|---|---|
| N/A | N/A | N/A | N/A | N/A | N/A |

## Command Results

| Alias | help | version | tui guard | diagnose before | update dry-run | install | verify | update --yes | diagnose after |
|---|---|---|---|---|---|---|---|---|---|
| N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

## Feedback

- operator confusion labels: N/A
- adoption blocker: N/A
- reuse intent: N/A
- trust concern: N/A
- workflow-fit concern: N/A
- first failure or hesitation point: N/A
- recovery path used: N/A
- docs page used: N/A
- suggested fix: N/A

## Sanitization Check

- private repo names removed: N/A
- tokens/secrets absent: N/A
- user handles anonymized or consented: N/A
```

## Decision Criteria

After the first external trial batch, classify the next main contradiction:

| Evidence pattern | Next main contradiction |
|---|---|
| installs fail or verify fails on multiple targets | reliability |
| commands pass but operators cannot choose the right path | documentation |
| operators understand docs and commands but hesitate to adopt | adoption |
| failures cluster around unsupported repo shapes | target compatibility |
| confusion centers on update/publish expectations | release-channel communication |

Minimum decision threshold:

- at least two programmer-owned targets complete or fail with preserved evidence.
- at least one volunteer or cold-operator trial completes or names a concrete blocker.
- no private identifiers or secrets are required to understand the result.

## Out Of Scope

- real npm publish.
- public recruitment copy.
- storage of private repository identifiers.
- support for non-`agents` backends.
- remote update, self-update, signing, or automatic rollback.
