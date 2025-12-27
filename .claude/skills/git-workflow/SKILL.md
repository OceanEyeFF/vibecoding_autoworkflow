---
name: git-workflow
description: >
  Provide a safe, deterministic git workflow for the delivery loop:
  create a work branch when on main/master (or detached HEAD), create Conventional Commits, and optionally push + open a PR.
allowed-tools: Bash, Read, Grep, Glob
---

# Git workflow (branch/commit/push/pr helpers)

Use the repo-local `autoworkflow` git helpers.

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

This repo enforces **Conventional Commits** by default.

- Auto-generate a Conventional Commit message (Chinese by default):
  - `python .autoworkflow/tools/autoworkflow.py --root . git commit --all --auto-message`
- Commit staged changes with an explicit message (must be Conventional):
  - `python .autoworkflow/tools/autoworkflow.py --root . git commit -m "chore(scope): 简短说明"`

Options:
- `--lang zh|en`: language for `--auto-message` (default `zh`)
- `--type <feat|fix|docs|...>`: override commit type for `--auto-message`
- `--scope <scope>`: optional scope (e.g. `claude`, `autoworkflow`)
- `--no-conventional`: disable validation (not recommended)

## Push (remote)

- Push current branch:
  - `python .autoworkflow/tools/autoworkflow.py --root . git push -u`

## Create a PR (remote, GitHub/Gitee)

- Create a PR for the current branch (provider auto-detected from `origin` url):
  - `python .autoworkflow/tools/autoworkflow.py --root . git pr create --base develop --push -u`

Auth (env vars):
- Gitee: set `GITEE_TOKEN`
- GitHub: set `GITHUB_TOKEN` (or install/auth `gh`)

Notes:
- If the remote **does not** have `develop`, `git pr create` will fail with a suggested fix:
  - rerun with `--bootstrap-base-from origin/master` (recommended) or pass `--base master`

Safety notes:
- These helpers never push / create PR unless you pass `git push` / `git pr ...` explicitly.
