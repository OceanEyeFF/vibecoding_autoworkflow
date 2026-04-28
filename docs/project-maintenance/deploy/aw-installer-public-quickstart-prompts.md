---
title: "aw-installer Public Quickstart Prompts"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer Public Quickstart Prompts

> Purpose: give external testers one copy-paste path for installing AW artifacts into a target repository and initializing `.aw/` through Codex or Claude Code. The current rc2 registry trial path is `aw-installer@next`; bare `aw-installer` still resolves through npm `latest`.

This page belongs to [Deploy Runbooks](./README.md). It uses the current non-publish distribution boundary from [aw-installer Non-Publish Release Rehearsal](./aw-installer-release-rehearsal.md) and the feedback fields from [aw-installer External Trial Feedback Contract](./aw-installer-external-trial-feedback.md).

## Control Signal

- recommended_path: Codex with `agents` backend
- claude_code_path: trial-only compatibility lane
- direct_npx_available: true
- direct_npx_primary_path: `aw-installer@next`
- registry_rc_available: true
- npm_publish_allowed: completed-for-0.4.0-rc.2-next
- package_name_decided: true
- approved_package_name: unscoped `aw-installer`
- current_install_source: `aw-installer@next`, local `.tgz` package, or explicit source checkout
- target_repo_writes:
  - `.agents/skills/` for Codex/agents install
  - `.claude/skills/aw-set-harness-goal-skill/` for Claude Code cold-start helper
  - `.aw/` only after the operator asks the runtime agent to initialize the Harness control plane

## Before You Start

Run commands from the target repository root unless a command explicitly names the AW source checkout.

Prerequisites:

- Node.js and npm are available for the `aw-installer` package path.
- Python is available for the wrapper. The `0.4.0-rc.2` candidate tries `py -3`, `python`, then `python3` on Windows, and `python3` then `python` on Linux/macOS. It intentionally ignores `PYTHON` and `PYTHON3` environment overrides.
- The target repository is a git worktree you are allowed to modify.
- You have registry access to `aw-installer`, a local `aw-installer` `.tgz` package from the maintainer, or an explicit AW source checkout path.
- You understand that the current public trial path is RC pre-release: `aw-installer@next` resolves to `0.4.0-rc.2`, while bare `aw-installer` still follows npm `latest` and resolves to `0.4.0-rc.1`. Stable release semantics still require separate approval.

Privacy rule:

- Do not paste private repository names, tokens, credentials, customer names, or full logs into long-term reports.
- Use sanitized aliases when submitting feedback.

## Current RC Install Source

Use the rc2 registry package directly for the public trial path:

```bash
AW_INSTALLER_PACKAGE="aw-installer@next"
```

Use bare `aw-installer` only when explicitly reproducing the older `latest` path:

```bash
AW_INSTALLER_PACKAGE="aw-installer"
```

Maintainers can still create a local `.tgz` from the AW source checkout:

```bash
AW_SOURCE_REPO="/path/to/vibecoding_autoworkflow"
AW_PACKAGE_DIR="$(mktemp -d)"

npm --prefix "$AW_SOURCE_REPO" pack --json --pack-destination "$AW_PACKAGE_DIR" > "$AW_PACKAGE_DIR/pack.json"
AW_INSTALLER_PACKAGE="$AW_PACKAGE_DIR/$(node -e "const fs = require('node:fs'); const payload = JSON.parse(fs.readFileSync(process.argv[1], 'utf8')); console.log(payload[0].filename);" "$AW_PACKAGE_DIR/pack.json")"

printf 'AW_INSTALLER_PACKAGE=%s\n' "$AW_INSTALLER_PACKAGE"
```

External testers who receive a `.tgz` can skip this step and set:

```bash
AW_INSTALLER_PACKAGE="/path/to/aw-installer-0.4.0-rc.2.tgz"
```

The exact filename may differ. Prefer `aw-installer@next` for rc2 registry npx trials and local `.tgz` when validating the current checkout or when registry access is unavailable.

## Codex Quickstart

Use this path for the main Codex-first trial. It installs the `agents` backend payload into the target repository, then asks Codex to initialize `.aw/`.

From the target repository root on Linux or macOS bash:

```bash
AW_INSTALLER_PACKAGE="aw-installer@next"

AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npx --yes --package "$AW_INSTALLER_PACKAGE" -- aw-installer diagnose --backend agents --json
AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npx --yes --package "$AW_INSTALLER_PACKAGE" -- aw-installer update --backend agents
```

From the target repository root on Windows PowerShell:

```powershell
$env:AW_INSTALLER_PACKAGE = "aw-installer@next"
$env:AW_HARNESS_REPO_ROOT = ""
$env:AW_HARNESS_TARGET_REPO_ROOT = ""

npx --yes --package $env:AW_INSTALLER_PACKAGE -- aw-installer diagnose --backend agents --json
npx --yes --package $env:AW_INSTALLER_PACKAGE -- aw-installer update --backend agents
```

Review the dry-run plan. If the target owner approves writing `.agents/skills/`, run this on Linux or macOS bash:

```bash
AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npx --yes --package "$AW_INSTALLER_PACKAGE" -- aw-installer update --backend agents --yes
AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npx --yes --package "$AW_INSTALLER_PACKAGE" -- aw-installer verify --backend agents
```

Or run this on Windows PowerShell:

```powershell
npx --yes --package $env:AW_INSTALLER_PACKAGE -- aw-installer update --backend agents --yes
npx --yes --package $env:AW_INSTALLER_PACKAGE -- aw-installer verify --backend agents
```

Then open Codex in the target repository and paste:

```text
$set-harness-goal-skill

Initialize AW Harness control-plane artifacts in this repository.

Goal:
Use AW as the repo-side control layer for bounded AI coding work in this existing repository.

Requirements:
- Create or update the minimal `.aw/` control-plane artifacts needed for Harness operation.
- Preserve existing source code and docs.
- Treat existing repository facts as discovery input, not as a replacement for the confirmed goal.
- If the repository already has `.aw/`, inspect the current control state and avoid overwriting confirmed truth without asking.
- Do not run npm publish.
- Prefer `aw-installer@next` for the current rc2 registry trial path; bare `aw-installer` still resolves to the older `latest` path.

After initialization, summarize:
- which `.aw/` files were created or reused
- the baseline branch/ref used
- any questions that require human confirmation
- the next recommended Harness route
```

If Codex does not recognize `$set-harness-goal-skill`, first confirm `verify --backend agents` passed and that the target repository contains `.agents/skills/aw-set-harness-goal-skill/SKILL.md`.

## Claude Code Quickstart

Use this path only for the current Claude Code compatibility trial. The repository does not provide a stable `adapter_deploy.py --backend claude` contract.

From the AW source checkout, install the Claude project-level cold-start helper into the target repository:

```bash
AW_SOURCE_REPO="/path/to/vibecoding_autoworkflow"
TARGET_REPO="/path/to/target-project"

PYTHONDONTWRITEBYTECODE=1 python3 "$AW_SOURCE_REPO/product/harness/skills/set-harness-goal-skill/scripts/deploy_aw.py" \
  install-claude-skill \
  --deploy-path "$TARGET_REPO"
```

Then open Claude Code in the target repository and paste:

```text
/aw-set-harness-goal-skill

Initialize AW Harness control-plane artifacts in this repository.

Goal:
Use AW as the repo-side control layer for bounded AI coding work in this existing repository.

Requirements:
- Use the project-level `aw-set-harness-goal-skill` entry.
- Create the minimal `.aw/goal-charter.md`, `.aw/control-state.md`, and `.aw/repo/snapshot-status.md` artifacts if they do not exist.
- Preserve existing source code and docs.
- Do not call `adapter_deploy.py --backend claude`; this repository does not provide that stable adapter.
- Do not run npm publish.
- Prefer `aw-installer@next` for the current rc2 registry trial path; bare `aw-installer` still resolves to the older `latest` path.

After initialization, summarize:
- which `.aw/` files were created or reused
- whether Claude Code recognized the project-level skill
- any questions that require human confirmation
- the next recommended Harness route
```

If Claude Code does not recognize `/aw-set-harness-goal-skill`, confirm the target repository contains `.claude/skills/aw-set-harness-goal-skill/SKILL.md`, then check Claude Code project trust and project-level skill loading.

## What To Report

Use [aw-installer External Trial Feedback Contract](./aw-installer-external-trial-feedback.md) for structured reporting. For GitHub reports, use the [aw-installer trial feedback issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-trial-feedback.yml) or the [aw-installer bug/blocker issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-bug.yml). At minimum, preserve:

- target alias
- target category
- package source
- install command used
- sanitized `aw-installer-npx-run.log` path or attached excerpt when the registry smoke runner was used
- `diagnose`, dry-run `update`, write `update --yes`, and `verify` result
- Codex or Claude Code initialization result
- operator confusion labels
- adoption blocker
- reuse intent
- trust concern
- workflow-fit concern
- sanitized failure line

## Stop Conditions

Stop and report a blocker if:

- dry-run `update` plans writes outside the expected target repository.
- `verify --backend agents` fails after install.
- Codex cannot see `set-harness-goal-skill` after a passing agents install.
- Claude Code cannot read the project-level `aw-set-harness-goal-skill` entry.
- initialization would overwrite an existing confirmed `.aw/goal-charter.md` without operator approval.
- a report needs full command logs but the log contains private paths, tokens, credentials, or private repository identifiers; sanitize first, then attach or summarize the relevant excerpt.
