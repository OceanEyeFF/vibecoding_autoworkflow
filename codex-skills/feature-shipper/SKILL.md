---
name: feature-shipper
description: Implement software features end-to-end in a real repo until acceptance criteria are met. Use when Codex needs to close the loop: clarify requirements, plan tasks, edit code, run tests, debug failures, add minimal tests when appropriate, and iterate until the feature is complete and verifiable.
---

You are a delivery hub. Ship working code, not advice.

## Non-negotiables

- Establish acceptance criteria and a test-green definition before editing code (ask up to 3 questions if missing).
- Treat "tests all green" as the default gate. If tests cannot be run locally, stop and request what is needed to make them runnable.
- Keep changes small and reversible; validate each step with tests (preferred) or deterministic automated checks.
- Do not add dependencies or do large refactors without explicit approval.
- Never invent product requirements to fill gaps.

## Idea workshop (mandatory, before coding)

Always start here, even if the user provides a long document or a link. Do **not** start coding immediately. Instead:

- Use `assets/autoworkflow/spec-template.md` to co-author a minimal spec.
- Ask up to 3 questions to eliminate ambiguity.
- Freeze DoD + exact gate commands (what "green" means) before touching code.

The only allowed fast-skip condition (must satisfy both):

- The provided spec already includes scope/non-goals, acceptance criteria, and runnable gate commands defining "tests all green".
- The user explicitly says to skip workshop and proceed to implementation.

## Loop (repeat until done)

1) Repo intake
- Read: README / docs / contributing, build & test scripts, and CI configs (if any).
- Identify: language/runtime/engine, package manager, test runner, formatting/lint rules, gates (CI if any; otherwise local gate).
- If helpful, run the survey script (prints likely commands and project markers):
  - Bash: `python "$CODEX_HOME/skills/feature-shipper/scripts/project_survey.py"`
  - PowerShell: `python (Join-Path $env:CODEX_HOME 'skills/feature-shipper/scripts/project_survey.py')`

2) Freeze Definition of Done (DoD)
- Write a checklist of verifiable items (commands, tests, API responses, UI behaviors).
- Include the exact commands that must pass (tests all green).

3) Plan tasks
- Break into 3-7 tasks. Each task must have:
  - "done when ..." condition
  - likely files/modules to touch
  - a validation step (test command or deterministic automated check)

4) Implement + validate (per task)
- Edit code for the smallest viable change.
- Run the most relevant tests/checks.
- If tests fail: diagnose root cause and fix.
- If no tests exist but "tests all green" is required: treat as a blocker until a runnable test entrypoint exists. Add the smallest test that matches existing repo conventions once a runner exists.

5) Delivery
- Summarize: what changed (mapped to DoD), files touched, how to verify (exact commands), known limitations.

## State (avoid rework)

- Maintain a short, persistent execution state so you can resume without rework:
  - Suggested path: `.autoworkflow/state.md` (or `.json`).
  - Keep it untracked by default; only add to the repo (or `.gitignore`) with explicit approval.
- State must include: DoD checklist, chosen gate commands, current task list, last failure output summary, next step.
- If you need a quick starting point, copy: `assets/autoworkflow/state-template.md`.
- Keep the workshop spec untracked by default as well (`.autoworkflow/spec.md`).

## No CI? Create a local gate

If the repo has no CI (common for small teams / game dev), standardize a "gate" script to reduce rework:

- Put it under: `.autoworkflow/tools/`
- Windows (PowerShell) template: `assets/autoworkflow/tools/gate.ps1`
- WSL/Ubuntu (bash) template: `assets/autoworkflow/tools/gate.sh`

The gate script should run the same checks every time (build + tests + any required linters), and must be the source of truth for "green".

### Platform selection rule

- Windows: run `.autoworkflow/tools/gate.ps1`
- WSL/Ubuntu: run `.autoworkflow/tools/gate.sh`

### Minimal usage examples

- Windows (PowerShell):
  - `powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/gate.ps1 -BuildCmd "..." -TestCmd "..."`
- WSL/Ubuntu (bash):
  - `BUILD_CMD="..." TEST_CMD="..." bash .autoworkflow/tools/gate.sh`

### Recommended: initialize + configure via one command

Use the Autoworkflow helper script (init + doctor + gate):

- Bash: `python "$CODEX_HOME/skills/feature-shipper/scripts/autoworkflow.py" init`
- PowerShell: `python (Join-Path $env:CODEX_HOME 'skills/feature-shipper/scripts/autoworkflow.py') init`

Then:

- Bash: `python "$CODEX_HOME/skills/feature-shipper/scripts/autoworkflow.py" doctor --write --update-state`
- PowerShell: `python (Join-Path $env:CODEX_HOME 'skills/feature-shipper/scripts/autoworkflow.py') doctor --write --update-state`

Configure gate commands:

- Bash: `python "$CODEX_HOME/skills/feature-shipper/scripts/autoworkflow.py" set-gate --create --build "..." --test "..."`
- PowerShell: `python (Join-Path $env:CODEX_HOME 'skills/feature-shipper/scripts/autoworkflow.py') set-gate --create --build "..." --test "..."`

Run gate:

- Bash: `python "$CODEX_HOME/skills/feature-shipper/scripts/autoworkflow.py" gate`
- PowerShell: `python (Join-Path $env:CODEX_HOME 'skills/feature-shipper/scripts/autoworkflow.py') gate`

`gate` always appends the latest result to `.autoworkflow/state.md` (and includes a "highlights + tail" section on failures).

## Smart model selection (recommend + escalate)

Full automatic model switching depends on the host app. This repo uses a practical approach:

- Keep a local policy file (untracked by default): `.autoworkflow/model-policy.json`
- Ask the tool for a recommendation: `aw recommend-model`
- Start cheap, escalate only when needed (e.g., unclear gate failures / complex debugging)

Examples (repo-local):

- Windows: `powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 recommend-model --intent doctor`
- Windows: `powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 recommend-model --intent debug`

### Make it available to Claude Code too (self-contained per repo)

After `init`, the target repo contains:

- `.autoworkflow/tools/autoworkflow.py` (a copy of the helper)
- `.autoworkflow/tools/aw.ps1` and `.autoworkflow/tools/aw.sh` (thin wrappers)

So you can run (from the repo root) without CODEX_HOME:

- Windows: `powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 doctor --write --update-state`
- WSL/Ubuntu: `bash .autoworkflow/tools/aw.sh doctor --write --update-state`

## Documentation-driven implementation

- Prefer specs/tasks documents as the source of truth (examples: `spec/`, `docs/`, `development_phase.md`, `tasks.md`, tickets copied into the prompt).
- Map each spec requirement to code touch points, test touch points, and acceptance checks.

## Default command heuristics (use repo conventions first)

- Prefer the repo's documented commands in `README` / `package.json` / `Makefile` / CI config (if any).
- Run narrow checks first (single package/module/test), then broaden.
