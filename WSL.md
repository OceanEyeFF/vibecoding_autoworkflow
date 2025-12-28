# WSL Usage Guide (Windows + Ubuntu)

This repo is optimized for WSL-first workflows. Follow these steps to run the full Codex/Claude Code loop on Windows with WSL.

## 1) Prerequisites
- Windows 10/11 with WSL installed (Ubuntu recommended).
- Python 3.10+ available in WSL.
- Git configured; set `core.autocrlf=input` to avoid CRLF issues:
  - `git config --global core.autocrlf input`

## 2) Clone and prepare
```bash
# In WSL
git clone <repo-url>
cd <repo>
python codex-skills/feature-shipper/scripts/autoworkflow.py --root . init
python .autoworkflow/tools/autoworkflow.py --root . auto-gate   # or set-gate --test "<your test>"
bash .autoworkflow/tools/aw.sh doctor --write --update-state
```

## 3) Run the gate (WSL first, fail-fast)
```bash
bash .autoworkflow/tools/aw.sh gate
# or
python .autoworkflow/tools/autoworkflow.py --root . gate
```
> If WSL is unavailable, the command fails (no auto-downgrade to Windows). Fix WSL or run the Windows gate explicitly:
> `powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 gate`

## 4) Tokens for remote push/PR
- Set in the WSL shell or write to `.autoworkflow/secret.env` (do not commit):
```bash
export GITEE_TOKEN=xxxx    # or GITHUB_TOKEN=xxxx
echo "GITEE_TOKEN=xxxx" > .autoworkflow/secret.env
```
- Then run one-shot PR flow:
```bash
python .autoworkflow/tools/autoworkflow.py --root . \
  git pr create --push --set-upstream --wait-ci \
  --base develop --bootstrap-base-from origin/master
```

## 5) Using Codex CLI (WSL)
```bash
codex --full-auto -C .
```
- First message: ask Codex to read `codex-skills/feature-shipper/SKILL.md`.
- It will follow spec/DoD → plan → gate → fix → gate until green.

## 6) Using Claude Code (no Python commands)
1) Copy `.claude/agents/`, `.claude/skills/`, and `.autoworkflow/` into your target repo.
2) Open the project in Claude Code, choose agent `feature-shipper`.
3) Describe the task; it will drive spec/DoD → plan → gate automatically. Tokens from step 4 are reused for push/PR.

## 7) Common issues
- **WSL not found**: Install WSL (`wsl --install`) and restart the terminal.
- **Token missing**: set env or `.autoworkflow/secret.env`, then rerun PR command.
- **Base branch missing**: rerun with `--bootstrap-base-from origin/master`.
- **.autoworkflow ignored by git**: use `git add -f .autoworkflow/...` when you need to commit tool changes.

Keep gates green; treat `gate` as the single source of truth for “done”.
