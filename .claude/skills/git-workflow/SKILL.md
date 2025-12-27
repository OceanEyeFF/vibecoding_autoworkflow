---
name: git-workflow
description: >
  Provide a safe, deterministic git workflow for the delivery loop:
  create a work branch when on main/master (or detached HEAD), and optionally create a local commit.
allowed-tools: Bash, Read, Grep, Glob
---

# Git workflow (branch/commit helpers)

Use the repo-local `autoworkflow` git helpers (no network required):

## Create a work branch

- Prefer running before making changes:
  - `python .autoworkflow/tools/autoworkflow.py --root . git branch start`
- If you are already on a non-protected branch, it should no-op.
- If you are on `main`/`master` (or detached `HEAD`), it should create a new branch.

Options:
- `--name <branch>`: explicit branch name
- `--prefix <prefix>`: auto-generated branch name prefix (default: `aw/`)
- `--dry-run`: print actions without modifying git state
- `--require-git`: fail instead of skipping when not in a git repo

## Create a local commit (optional)

- Commit staged changes:
  - `python .autoworkflow/tools/autoworkflow.py --root . git commit -m "message"`
- Stage all changes then commit:
  - `python .autoworkflow/tools/autoworkflow.py --root . git commit -m "message" --all`

Safety notes:
- These helpers never `push` by default.
- PR creation is intentionally out of scope here (use `gh`/`glab` explicitly when ready).

