# Spec (Idea -> DoD)

## 1) One-liner
- ...

## 2) Problem & user
- Target user: ...
- Problem: ...
- Why now: ...

## 3) Scope
**In scope**
- ...

**Out of scope (explicit non-goals)**
- ...

## 4) Constraints
- Platforms: Windows / WSL / Ubuntu (which ones must work?)
- Languages/engine: ...
- Time/effort budget: ...
- No new dependencies? (yes/no)

## 5) Requirements (doc-driven list)
1. ...
2. ...

## 6) Acceptance criteria (verifiable)
- [ ] ...
- [ ] ...

## 7) Test-green definition (the gate)
This is the source of truth for "green":
- Build command: `...`
- Test command: `...`
- Optional: lint/format commands: `...` (only if repo-gated)

## 8) Local gate script location
- Windows: `.autoworkflow/tools/gate.ps1`
- WSL/Ubuntu: `.autoworkflow/tools/gate.sh`

## 9) Open questions (max 3 to unblock)
- ...

