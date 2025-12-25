---
name: feedback-logger
description: Lightweight, optional logging for agent runs. Use when you want a background log to capture valuable intermediate signals (commands run, gate output highlights, state/doctor changes, manual notes) to reduce rework and improve tests. Works offline and writes untracked logs under .autoworkflow/logs.
---

Use this skill to keep a lightweight, persistent log during work without polluting git history.

## Setup (per repo)

Initialize `.autoworkflow/logs` and repo-local commands:

- Bash: `python "$CODEX_HOME/skills/feedback-logger/scripts/feedback.py" init`
- PowerShell: `python (Join-Path $env:CODEX_HOME 'skills/feedback-logger/scripts/feedback.py') init`

This creates:

- `.autoworkflow/tools/feedback.py`
- `.autoworkflow/tools/fb.ps1` and `.autoworkflow/tools/fb.sh`
- `.autoworkflow/logs/feedback.jsonl` (untracked)

## Run (repo-local)

- Windows: `powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/fb.ps1 start`
- WSL/Ubuntu: `bash .autoworkflow/tools/fb.sh start`

Stop:

- Windows: `powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/fb.ps1 stop`
- WSL/Ubuntu: `bash .autoworkflow/tools/fb.sh stop`

## Log what matters (during test improvement)

- Add a manual note:
  - `... fb.ps1 log --message "Hypothesis: flaky test due to race in X" --tag hypothesis`
- Wrap a command (captures highlights + tail on failure):
  - `... fb.ps1 wrap aw gate`

## Files

- Logs: `.autoworkflow/logs/feedback.jsonl`
- Watch PID: `.autoworkflow/logs/feedback-watch.pid`
