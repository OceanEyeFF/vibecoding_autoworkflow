---
title: "aw-installer Public Quickstart Prompts"
status: active
updated: 2026-05-04
owner: aw-kernel
last_verified: 2026-05-04
---
# aw-installer Public Quickstart Prompts

> Purpose: give external testers one copy-paste path for installing AW artifacts into a target repository and initializing `.aw/` through Codex or Claude Code. The current published RC registry trial path is `aw-installer@next`; bare `aw-installer` still resolves through npm `latest`.

This page belongs to [Deploy Runbooks](./README.md). It uses the current distribution boundary from [aw-installer Release Channel Contract](./release-channel-contract.md) and the feedback fields from [aw-installer External Trial Feedback Contract](./aw-installer-external-trial-feedback.md).

## Control Signal

- recommended_path: Codex with `agents` backend
- claude_code_path: Claude Code adapter lane
- direct_npx_available: true
- direct_npx_primary_path: `aw-installer@next`
- registry_rc_available: true
- npm_publish_allowed: completed-for-0.4.3-rc.2-next; 4.4.0-rc.0 is prepared locally and remains publish-workflow gated
- package_name_decided: true
- approved_package_name: unscoped `aw-installer`
- current_install_source:
  - published_registry: `aw-installer@next` currently resolving to `0.4.3-rc.2`
  - local_package: local `4.4.0-rc.0` `.tgz` package when validating the current checkout without registry access
  - source_checkout: explicit AW source checkout
- target_repo_writes:
  - `.agents/skills/` for Codex/agents install
  - `.claude/skills/<skill-name>/` for Claude managed adapter install
  - `.claude/skills/aw-set-harness-goal-skill/` only for the standalone cold-start helper
  - `.aw/` only after the operator asks the runtime agent to initialize the Harness control plane

## Before You Start

Run commands from the target repository root unless a command explicitly names the AW source checkout.

Prerequisites:

- Node.js and npm are available for the `aw-installer` package path.
- Python is available only for explicitly documented repo-local reference helpers. The published `aw-installer@next` selector currently resolves to the immutable `0.4.3-rc.2` artifact; it does not include checkout-only changes made after that publish. A local `.tgz` built from this checkout reports `4.4.0-rc.0` and is release-candidate evidence, not registry evidence.
- When validating the current checkout, an explicit source checkout, or a maintainer-provided local `.tgz` built from this checkout, `aw-installer --help`, `--version`, `agents` package/local lifecycle commands, `claude` package/local lifecycle commands, and explicit `agents` GitHub-source update JSON/human/apply are handled by Node directly. For `agents`, this includes diagnose human/JSON, package/local update dry-run human/JSON, GitHub-source update dry-run JSON/human, GitHub-source `update --yes`, check_paths_exist, verify, install, prune --all, package/local update --yes, and selected invalid variants. For `claude`, this includes diagnose human/JSON, `--claude-root`, check_paths_exist, verify, update dry-run human/JSON, install, prune --all and update --yes. Node-owned install writes only after source/target/path preflight passes; planned path conflicts fail before writes and do not invoke Python. Node-owned Claude install also preserves full Harness skill payload, `.claude/skills/<skill_id>` naming, frontmatter transform, and same-backend managed legacy cleanup. Node-owned prune only removes recognized current-backend managed install directories and retains foreign, unrecognized, invalid-marker and user content. Node-owned `update --yes` for package/local agents, package/local Claude and explicit agents GitHub-source composes `prune --all -> check_paths_exist -> install -> verify` with blocking preflight, strict post-apply verify and backend/source-aware recovery hint semantics. Published registry artifacts get these checkout-only behaviors only after a future approved release. Unsupported variants no longer fall back to the Python deploy wrapper; the Node package/runtime entrypoint fails with an explicit unsupported-command error. The Node-owned update dry-run preserves the existing JSON fields, including `backend`, `source_kind`, `source_ref`, `source_root`, `target_root`, `operation_sequence`, `managed_installs_to_delete`, `planned_target_paths`, `issues`, and `blocking_issues`, and the human-readable output remains dry-run only.
- The target repository is a git worktree you are allowed to modify.
- You have registry access to `aw-installer`, a local `aw-installer` `.tgz` package from the maintainer, or an explicit AW source checkout path.
- You understand that the current public trial path is RC pre-release: `aw-installer@next` currently resolves to `0.4.3-rc.2` on npm `next`, while bare `aw-installer` still follows npm `latest` and resolves to `0.4.0-rc.1`. Stable release semantics still require separate approval.

Privacy rule:

- Do not paste private repository names, tokens, credentials, customer names, or full logs into long-term reports.
- Use sanitized aliases when submitting feedback.

## Current RC Install Source

Use the published RC registry package directly for the public trial path:

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
AW_INSTALLER_PACKAGE="/path/to/aw-installer-4.4.0-rc.0.tgz"
```

The exact filename may differ. Prefer `aw-installer@next` for published RC registry npx trials and local `.tgz` when validating the current checkout or when registry access is unavailable.

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
- Prefer `aw-installer@next` for the published RC registry trial path; bare `aw-installer` still resolves to the older `latest` path.

After initialization, summarize:
- which `.aw/` files were created or reused
- the baseline branch/ref used
- any questions that require human confirmation
- the next recommended Harness route
```

If Codex does not recognize `$set-harness-goal-skill`, first confirm `verify --backend agents` passed and that the target repository contains `.agents/skills/aw-set-harness-goal-skill/SKILL.md`.

## Claude Code Quickstart

Use this path for the current Claude Code adapter trial. The repository provides a bounded `adapter_deploy.py --backend claude` contract for the full Harness skill payload set; it is still not the `agents` mainline.

Claude compatibility requires an install source that contains `product/harness/adapters/claude/skills`. Until the published selector is verified for that payload, use an explicit source checkout or maintainer-provided local `.tgz` rather than assuming every registry selector contains the Claude lane.

From the AW source checkout, install the Claude project-level cold-start helper into the target repository. The helper path remains the most explicit cold-start route:

```bash
AW_SOURCE_REPO="/path/to/vibecoding_autoworkflow"
TARGET_REPO="/path/to/target-project"

node "$AW_SOURCE_REPO/product/harness/skills/set-harness-goal-skill/scripts/deploy_aw.js" \
  install-claude-skill \
  --deploy-path "$TARGET_REPO"
```

The equivalent managed adapter path is:

```bash
AW_HARNESS_TARGET_REPO_ROOT="$TARGET_REPO" \
PYTHONDONTWRITEBYTECODE=1 python3 "$AW_SOURCE_REPO/toolchain/scripts/deploy/adapter_deploy.py" install --backend claude

AW_HARNESS_TARGET_REPO_ROOT="$TARGET_REPO" \
PYTHONDONTWRITEBYTECODE=1 python3 "$AW_SOURCE_REPO/toolchain/scripts/deploy/adapter_deploy.py" verify --backend claude
```

Then open Claude Code in the target repository and paste. If you installed through the managed adapter path, use `/set-harness-goal-skill`; if you used the standalone helper path above, use `/aw-set-harness-goal-skill`.

```text
/set-harness-goal-skill

Initialize AW Harness control-plane artifacts in this repository.

Goal:
Use AW as the repo-side control layer for bounded AI coding work in this existing repository.

Requirements:
- Use the project-level `set-harness-goal-skill` entry when installed by `adapter_deploy.py --backend claude`.
- Create the minimal `.aw/goal-charter.md`, `.aw/control-state.md`, and `.aw/repo/snapshot-status.md` artifacts if they do not exist.
- Preserve existing source code and docs.
- If using `adapter_deploy.py --backend claude`, treat it as the bounded Claude adapter lane for the full Harness payload set, not as a replacement for the `agents` mainline.
- Do not run npm publish.
- Prefer `aw-installer@next` for the published RC registry trial path; bare `aw-installer` still resolves to the older `latest` path.

After initialization, summarize:
- which `.aw/` files were created or reused
- whether Claude Code recognized the project-level skill
- any questions that require human confirmation
- the next recommended Harness route
```

If Claude Code does not recognize `/set-harness-goal-skill`, confirm the target repository contains `.claude/skills/set-harness-goal-skill/SKILL.md`, then check Claude Code project trust and project-level skill loading. If you used the standalone helper path, check `.claude/skills/aw-set-harness-goal-skill/SKILL.md` instead.

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
- Claude Code cannot read the project-level `set-harness-goal-skill` entry after managed Claude install, or `aw-set-harness-goal-skill` after standalone helper install.
- initialization would overwrite an existing confirmed `.aw/goal-charter.md` without operator approval.
- a report needs full command logs but the log contains private paths, tokens, credentials, or private repository identifiers; sanitize first, then attach or summarize the relevant excerpt.
