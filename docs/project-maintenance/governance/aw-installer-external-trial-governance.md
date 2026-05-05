---
title: "aw-installer External Trial Governance"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# aw-installer External Trial Governance

> Purpose: define the target list template and feedback contract for post-RC `aw-installer` external trials.

This page belongs to [Governance](./README.md).

## Control Signal

- trial_status: planned
- trial_sources:
  - programmer-owned repositories
  - forum volunteer repositories
- future_npm_publish_allowed: false
- public_recruitment_copy_in_scope: false
- private_repo_identifiers_allowed_in_long_term_docs: false
- supported_backend_for_trial: `agents`
- feedback_decision_goal: decide whether the next main contradiction is adoption, reliability, or documentation

## Trial Target Categories

| Category | Purpose | Minimum count | Privacy rule |
| --- | --- | ---: | --- |
| programmer-owned repository | first realistic trial under trusted operator control | 2 | store only aliases unless explicit approval allows names |
| forum volunteer repository | observe cold external operator friction | 2 | store only anonymized aliases and consented facts |
| intentionally unsupported repository | confirm failure messaging and recovery path | 1 | store only anonymized shape and failure category |

Do not store private repository names, URLs, tokens, logs with secrets, or user handles in long-term docs unless separately approved.

## Command Feedback Fields

Each trial report should capture:

- target alias
- target category
- candidate version/source
- install command used
- shell/runtime path
- sanitized `aw-installer-npx-run.log` when applicable
- `help`, `version`, `tui` guard, `diagnose`, dry-run `update`, `install`, `verify`, optional `update --yes`
- operator confusion
- adoption blocker
- reuse intent
- trust concern
- workflow-fit concern
- recovery attempted
- final verdict

## Operator Confusion Taxonomy

- `entrypoint-confusion`
- `backend-confusion`
- `target-root-confusion`
- `update-boundary-confusion`
- `approval-boundary-confusion`
- `diagnose-output-confusion`
- `docs-navigation-confusion`
- `no-confusion-observed`

## Decision Criteria

After the first external trial batch, classify the next main contradiction:

| Evidence pattern | Next main contradiction |
| --- | --- |
| installs fail or verify fails on multiple targets | reliability |
| commands pass but operators cannot choose the right path | documentation |
| operators understand docs and commands but hesitate to adopt | adoption |
| failures cluster around unsupported repo shapes | target compatibility |
| confusion centers on update/publish expectations | release-channel communication |

Minimum threshold:

- at least two programmer-owned targets complete or fail with preserved evidence
- at least one volunteer or cold-operator trial completes or names a concrete blocker
- no private identifiers or secrets are required to understand the result

## Related Documents

- [aw-installer Release Channel Governance](./aw-installer-release-channel-governance.md)
- [npx Command Test Execution](../testing/npx-command-test-execution.md)
- [trial feedback issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-trial-feedback.yml)
- [bug/blocker issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-bug.yml)
