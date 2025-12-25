from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ALLOWED_ENV_KEYS = ("BUILD_CMD", "TEST_CMD", "LINT_CMD", "FORMAT_CHECK_CMD")

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass


DEFAULT_GATE_PS1 = """param(
  [string]$BuildCmd = "",
  [string]$TestCmd = "",
  [string]$LintCmd = "",
  [string]$FormatCheckCmd = ""
)

$ErrorActionPreference = "Stop"

function Read-GateEnv([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return @{} }
  $map = @{}
  Get-Content -LiteralPath $Path | ForEach-Object {
    $line = $_.Trim()
    if ($line.Length -eq 0) { return }
    if ($line.StartsWith("#")) { return }
    $idx = $line.IndexOf("=")
    if ($idx -lt 1) { return }
    $key = $line.Substring(0, $idx).Trim()
    $val = $line.Substring($idx + 1).Trim()
    if ($key -in @("BUILD_CMD","TEST_CMD","LINT_CMD","FORMAT_CHECK_CMD")) {
      $map[$key] = $val
    }
  }
  return $map
}

function Run-Step([string]$Name, [string]$Cmd) {
  if ([string]::IsNullOrWhiteSpace($Cmd)) { return }
  Write-Host "==> $Name"
  Write-Host $Cmd
  $global:LASTEXITCODE = 0
  Invoke-Expression $Cmd
  if ($LASTEXITCODE -ne 0) {
    throw "$Name failed (exit $LASTEXITCODE)."
  }
}

Write-Host "Gate start: $(Get-Date -Format o)"

if (([string]::IsNullOrWhiteSpace($BuildCmd)) -or ([string]::IsNullOrWhiteSpace($TestCmd)) -or ([string]::IsNullOrWhiteSpace($LintCmd)) -or ([string]::IsNullOrWhiteSpace($FormatCheckCmd))) {
  $envPath = Join-Path (Get-Location) ".autoworkflow\\gate.env"
  $envMap = Read-GateEnv $envPath
  if ([string]::IsNullOrWhiteSpace($BuildCmd) -and $envMap.ContainsKey("BUILD_CMD")) { $BuildCmd = $envMap["BUILD_CMD"] }
  if ([string]::IsNullOrWhiteSpace($TestCmd) -and $envMap.ContainsKey("TEST_CMD")) { $TestCmd = $envMap["TEST_CMD"] }
  if ([string]::IsNullOrWhiteSpace($LintCmd) -and $envMap.ContainsKey("LINT_CMD")) { $LintCmd = $envMap["LINT_CMD"] }
  if ([string]::IsNullOrWhiteSpace($FormatCheckCmd) -and $envMap.ContainsKey("FORMAT_CHECK_CMD")) { $FormatCheckCmd = $envMap["FORMAT_CHECK_CMD"] }
}

Run-Step "Build" $BuildCmd
if ([string]::IsNullOrWhiteSpace($TestCmd)) {
  throw "Missing TestCmd (set TEST_CMD in .autoworkflow\\gate.env or pass -TestCmd)."
}
Run-Step "Test" $TestCmd
Run-Step "Lint" $LintCmd
Run-Step "FormatCheck" $FormatCheckCmd

Write-Host "Gate done (green)."
"""


DEFAULT_GATE_SH = """#!/usr/bin/env bash
set -euo pipefail

AUTOWORKFLOW_DIR="${AUTOWORKFLOW_DIR:-.autoworkflow}"
GATE_ENV_FILE="${GATE_ENV_FILE:-${AUTOWORKFLOW_DIR}/gate.env}"

BUILD_CMD="${BUILD_CMD:-}"
TEST_CMD="${TEST_CMD:-}"
LINT_CMD="${LINT_CMD:-}"
FORMAT_CHECK_CMD="${FORMAT_CHECK_CMD:-}"

read_gate_env() {
  local file="$1"
  [[ -f "${file}" ]] || return 0
  while IFS= read -r line || [[ -n "${line}" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    [[ -z "${line}" ]] && continue
    [[ "${line}" == \\#* ]] && continue
    [[ "${line}" != *"="* ]] && continue
    local key="${line%%=*}"
    local val="${line#*=}"
    key="${key%"${key##*[![:space:]]}"}"
    val="${val#"${val%%[![:space:]]*}"}"
    case "${key}" in
      BUILD_CMD) [[ -z "${BUILD_CMD}" ]] && BUILD_CMD="${val}" ;;
      TEST_CMD) [[ -z "${TEST_CMD}" ]] && TEST_CMD="${val}" ;;
      LINT_CMD) [[ -z "${LINT_CMD}" ]] && LINT_CMD="${val}" ;;
      FORMAT_CHECK_CMD) [[ -z "${FORMAT_CHECK_CMD}" ]] && FORMAT_CHECK_CMD="${val}" ;;
    esac
  done < "${file}"
}

read_gate_env "${GATE_ENV_FILE}"

run_step() {
  local name="$1"
  local cmd="$2"
  if [[ -z "${cmd}" ]]; then
    return 0
  fi
  echo "==> ${name}"
  echo "${cmd}"
  eval "${cmd}"
}

echo "Gate start: $(date -Iseconds)"

run_step "Build" "${BUILD_CMD}"
if [[ -z "${TEST_CMD}" ]]; then
  echo "Missing TEST_CMD (set it in ${GATE_ENV_FILE} or pass env var TEST_CMD)." >&2
  exit 2
fi
run_step "Test" "${TEST_CMD}"
run_step "Lint" "${LINT_CMD}"
run_step "FormatCheck" "${FORMAT_CHECK_CMD}"

echo "Gate done (green)."
"""


DEFAULT_AW_PS1 = """$ErrorActionPreference = "Stop"

$toolDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $toolDir "autoworkflow.py"

if (-not (Test-Path -LiteralPath $script)) {
  throw "Missing $script (run autoworkflow init first)."
}

python $script @args
"""


DEFAULT_AW_SH = """#!/usr/bin/env bash
set -euo pipefail

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="${TOOL_DIR}/autoworkflow.py"

if [[ ! -f "${SCRIPT}" ]]; then
  echo "Missing ${SCRIPT} (run autoworkflow init first)." >&2
  exit 2
fi

PYTHON_BIN="python"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Missing python/python3 in PATH." >&2
  exit 127
fi

"${PYTHON_BIN}" "${SCRIPT}" "$@"
"""


DEFAULT_STATE_TEMPLATE = """# Feature Shipper State

## Definition of Done (tests must be green)
- [ ] Command(s) to run: `...`
- [ ] What "green" means (suites/configs): ...

## Source docs (spec/tasks)
- ...

## Task list
1. [ ] ...
2. [ ] ...

## Chosen commands
- Install/setup: `...`
- Build: `...`
- Test: `...`
- Lint/format (if CI-gated): `...`

## Last run
- When: ...
- Command: `...`
- Result: pass/fail
- Failure summary (paste key lines): ...

## Next step
- ...
"""


DEFAULT_SPEC_TEMPLATE = """# Spec (Idea -> DoD)

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
"""

DEFAULT_MODEL_POLICY = {
    "profiles": {
        "light": {
            "when": [
                "doctor / init / project survey",
                "formatting, renames, trivial doc edits",
            ],
            "claude": "haiku",
            "codex": "gpt-5-medium",
        },
        "medium": {
            "when": [
                "most feature work in a known codebase",
                "implementing from a spec with limited ambiguity",
                "adding a small number of tests",
            ],
            "claude": "sonnet",
            "codex": "gpt-5.2",
        },
        "heavy": {
            "when": [
                "gate/tests failing with unclear root cause",
                "cross-module refactors or high risk changes",
                "large diffs or complex debugging",
            ],
            "claude": "opus",
            "codex": "gpt-5.2-extra-high",
        },
    },
    "rules": [
        {
            "if": "gate_failed",
            "then": "heavy",
            "reason": "tests are failing; prioritize fast convergence and deeper debugging",
        },
        {
            "if": "no_gate_configured",
            "then": "medium",
            "reason": "need workshop + define DoD/gate first",
        },
        {
            "if": "doctor_only",
            "then": "light",
            "reason": "tooling/status checks are deterministic; keep it cheap",
        },
    ],
}


@dataclass(frozen=True)
class HostInfo:
    os_name: str
    platform: str
    python: str
    is_wsl: bool


def is_wsl() -> bool:
    if sys.platform != "linux":
        return False
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8").lower()
    except Exception:
        return False


def host_info() -> HostInfo:
    return HostInfo(
        os_name=os.name,
        platform=sys.platform,
        python=sys.version.split()[0],
        is_wsl=is_wsl(),
    )


def skill_root() -> Path:
    # .../feature-shipper/scripts/autoworkflow.py -> .../feature-shipper
    return Path(__file__).resolve().parents[1]


def assets_autoworkflow_dir() -> Path:
    return skill_root() / "assets" / "autoworkflow"


def repo_autoworkflow_dir(repo_root: Path) -> Path:
    return repo_root / ".autoworkflow"


def safe_write_text(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def copy_file(src: Path, dst: Path, force: bool) -> None:
    if dst.exists() and not force:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def init_autoworkflow(repo_root: Path, force: bool) -> None:
    assets_dir = assets_autoworkflow_dir()
    target = repo_autoworkflow_dir(repo_root)
    tools_dir = target / "tools"

    if assets_dir.exists():
        copy_file(assets_dir / "tools" / "gate.ps1", tools_dir / "gate.ps1", force=force)
        copy_file(assets_dir / "tools" / "gate.sh", tools_dir / "gate.sh", force=force)
        copy_file(assets_dir / "tools" / "aw.ps1", tools_dir / "aw.ps1", force=force)
        copy_file(assets_dir / "tools" / "aw.sh", tools_dir / "aw.sh", force=force)
        state_template = (assets_dir / "state-template.md").read_text(encoding="utf-8")
        spec_template = (assets_dir / "spec-template.md").read_text(encoding="utf-8")
    else:
        safe_write_text(tools_dir / "gate.ps1", DEFAULT_GATE_PS1, force=force)
        safe_write_text(tools_dir / "gate.sh", DEFAULT_GATE_SH, force=force)
        safe_write_text(tools_dir / "aw.ps1", DEFAULT_AW_PS1, force=force)
        safe_write_text(tools_dir / "aw.sh", DEFAULT_AW_SH, force=force)
        state_template = DEFAULT_STATE_TEMPLATE
        spec_template = DEFAULT_SPEC_TEMPLATE

    # Make the tool self-contained in the target repo so it can be used from any environment (Claude/Codex/terminal)
    copy_file(Path(__file__).resolve(), tools_dir / "autoworkflow.py", force=force)

    safe_write_text(target / "state.md", state_template, force=force)
    safe_write_text(target / "spec.md", spec_template, force=force)

    gitignore = "\n".join(
        [
            "# local workflow state (keep untracked by default)",
            "state.md",
            "spec.md",
            "model-policy.json",
            "gate.env",
            "doctor.md",
            "logs/",
            "",
        ]
    )
    safe_write_text(target / ".gitignore", gitignore, force=force)

    env_stub = "\n".join(
        [
            "# Autoworkflow gate config (untracked by default).",
            "# Allowed keys: BUILD_CMD, TEST_CMD, LINT_CMD, FORMAT_CHECK_CMD",
            "BUILD_CMD=",
            "TEST_CMD=",
            "LINT_CMD=",
            "FORMAT_CHECK_CMD=",
            "",
        ]
    )
    safe_write_text(target / "gate.env", env_stub, force=force)

    policy_path = target / "model-policy.json"
    if not policy_path.exists() or force:
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        with policy_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(DEFAULT_MODEL_POLICY, ensure_ascii=False, indent=2))
            f.write("\n")


def parse_gate_env(env_path: Path) -> dict[str, str]:
    if not env_path.exists():
        return {}
    values: dict[str, str] = {}
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key not in ALLOWED_ENV_KEYS:
            continue
        value = value.strip()
        if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
            value = value[1:-1]
        values[key] = value
    return values


def load_model_policy(repo_root: Path) -> dict:
    policy_path = repo_autoworkflow_dir(repo_root) / "model-policy.json"
    if not policy_path.exists():
        return DEFAULT_MODEL_POLICY
    try:
        return json.loads(policy_path.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_MODEL_POLICY


def detect_signals_for_model(repo_root: Path) -> set[str]:
    signals: set[str] = set()
    aw = repo_autoworkflow_dir(repo_root)
    env_path = aw / "gate.env"
    env_values = parse_gate_env(env_path)
    if not env_values.get("TEST_CMD"):
        signals.add("no_gate_configured")

    state_path = aw / "state.md"
    if state_path.exists():
        text = state_path.read_text(encoding="utf-8", errors="replace")
        # Heuristic: only consider the latest gate section (the last "## Gate (latest)").
        last = text.rfind("## Gate (latest)")
        if last != -1:
            tail = text[last:]
            m = re.search(r"^\\- Result:\\s*(.+)$", tail, re.MULTILINE)
            if m and m.group(1).strip().startswith("failed"):
                signals.add("gate_failed")
    return signals


def recommend_model(repo_root: Path, intent: str | None) -> tuple[str, str, str]:
    policy = load_model_policy(repo_root)
    profiles = policy.get("profiles", {})
    rules = policy.get("rules", [])

    signals = detect_signals_for_model(repo_root)
    intent_norm = (intent or "").strip().lower()
    if intent_norm in ("doctor", "init", "survey"):
        # Deterministic, tool-like actions: always keep it cheap.
        chosen = "light"
        prof = profiles.get(chosen, {})
        claude = str(prof.get("claude", "haiku"))
        codex = str(prof.get("codex", "gpt-5-medium"))
        return chosen, claude, codex + " (reason: deterministic tooling)"
    if intent_norm in ("debug", "fix", "refactor"):
        # These intents benefit from stronger models; still allow rules to override if needed.
        signals.add("gate_failed")

    chosen = "medium"
    reason = "default"
    for rule in rules:
        cond = rule.get("if")
        if isinstance(cond, str) and cond in signals:
            chosen = str(rule.get("then", chosen))
            reason = str(rule.get("reason", reason))
            break

    prof = profiles.get(chosen, {})
    claude = str(prof.get("claude", "sonnet"))
    codex = str(prof.get("codex", "gpt-5.2"))
    return chosen, claude, codex + f" (reason: {reason})"


def write_gate_env(env_path: Path, updates: dict[str, str], force_create: bool) -> None:
    current = parse_gate_env(env_path)
    current.update({k: v for k, v in updates.items() if v is not None})

    env_path.parent.mkdir(parents=True, exist_ok=True)
    if env_path.exists() or force_create:
        lines: list[str] = [
            "# Autoworkflow gate config (untracked by default).",
            "# Allowed keys: BUILD_CMD, TEST_CMD, LINT_CMD, FORMAT_CHECK_CMD",
        ]
        for key in ALLOWED_ENV_KEYS:
            value = current.get(key, "")
            # Keep plain values; gate scripts treat the remainder as raw string.
            lines.append(f"{key}={value}")
        lines.append("")
        with env_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines))


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def detect_markers(repo_root: Path) -> list[str]:
    markers: list[str] = []
    for rel in (
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "poetry.lock",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "CMakeLists.txt",
        ".gitmodules",
        ".gitignore",
    ):
        if (repo_root / rel).exists():
            markers.append(rel)
    if (repo_root / ".github" / "workflows").exists():
        markers.append(".github/workflows/")
    if list(repo_root.glob("*.uproject")):
        markers.append("*.uproject")
    if (repo_root / "ProjectSettings" / "ProjectVersion.txt").exists():
        markers.append("Unity ProjectSettings/ProjectVersion.txt")
    if list(repo_root.glob("*.sln")) or list(repo_root.rglob("*.csproj")):
        markers.append(".NET solution/project files")
    return markers


def doctor_report(repo_root: Path) -> str:
    host = host_info()
    aw = repo_autoworkflow_dir(repo_root)
    env_path = aw / "gate.env"
    env_values = parse_gate_env(env_path)
    markers = detect_markers(repo_root)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    lines: list[str] = []
    lines.append("# Autoworkflow Doctor Report")
    lines.append("")
    lines.append(f"- Time (UTC): {now}")
    lines.append(f"- Platform: {platform.platform()}")
    lines.append(f"- Python: {host.python}")
    lines.append(f"- WSL: {'yes' if host.is_wsl else 'no'}")
    lines.append("")
    lines.append("## Repo signals")
    if markers:
        for m in markers:
            lines.append(f"- {m}")
    else:
        lines.append("- (no common markers detected)")
    lines.append("")
    lines.append("## .autoworkflow status")
    lines.append(f"- Exists: {'yes' if aw.exists() else 'no'}")
    lines.append(f"- Gate env: {'yes' if env_path.exists() else 'no'}")
    lines.append(f"- Gate (Windows): {'yes' if (aw / 'tools' / 'gate.ps1').exists() else 'no'}")
    lines.append(f"- Gate (WSL/Ubuntu): {'yes' if (aw / 'tools' / 'gate.sh').exists() else 'no'}")
    lines.append("")
    lines.append("## Gate config (from gate.env)")
    if not env_values:
        lines.append("- (empty / not configured)")
    else:
        for key in ALLOWED_ENV_KEYS:
            value = env_values.get(key, "")
            lines.append(f"- {key}: `{value}`")
    lines.append("")
    lines.append("## Tooling availability (PATH)")
    for cmd in ("git", "python", "cmake", "ctest", "dotnet", "node", "npm", "pnpm", "yarn", "mvn", "gradle"):
        found = which(cmd)
        lines.append(f"- {cmd}: {'OK' if found else 'missing'}")
    lines.append("")
    lines.append("## Next actions (tests must be green)")
    if not aw.exists():
        lines.append("- Run: `autoworkflow init` (see usage below)")
        lines.append("- Then set gate commands: `autoworkflow set-gate --build ... --test ...`")
    else:
        if not env_values.get("TEST_CMD"):
            lines.append("- Set `TEST_CMD` in `.autoworkflow/gate.env` (or via `autoworkflow set-gate`).")
        lines.append("- Run gate: `autoworkflow gate` (or run the platform script directly).")
    lines.append("")
    lines.append("## Usage")
    lines.append("- init:   `python autoworkflow.py init`")
    lines.append("- doctor: `python autoworkflow.py doctor`")
    lines.append("- set:    `python autoworkflow.py set-gate --build \"...\" --test \"...\"`")
    lines.append("- gate:   `python autoworkflow.py gate`")
    lines.append("")
    return "\n".join(lines)


def write_doctor(repo_root: Path, write: bool, update_state: bool) -> str:
    report = doctor_report(repo_root)
    aw = repo_autoworkflow_dir(repo_root)
    if write:
        safe_write_text(aw / "doctor.md", report, force=True)
    if update_state:
        state_path = aw / "state.md"
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
        appendix = "\n".join(
            [
                "",
                "## Doctor (latest)",
                f"- Time (UTC): {stamp}",
                "- See `.autoworkflow/doctor.md` for full report.",
                "",
            ]
        )
        state_path.parent.mkdir(parents=True, exist_ok=True)
        if state_path.exists():
            with state_path.open("w", encoding="utf-8", newline="\n") as f:
                f.write(state_path.read_text(encoding="utf-8") + appendix)
        else:
            safe_write_text(state_path, appendix.lstrip("\n"), force=True)
    return report


def _stdout_write(text: str) -> None:
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        buffer = getattr(sys.stdout, "buffer", None)
        if buffer is not None:
            buffer.write(text.encode(encoding, errors="replace"))
            buffer.flush()
        else:
            # Last resort: drop unencodable characters.
            sys.stdout.write(text.encode(encoding, errors="replace").decode(encoding, errors="ignore"))
            sys.stdout.flush()


def _run_and_tee(cmd: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        universal_newlines=True,
    )
    assert proc.stdout is not None
    out_lines: list[str] = []
    for line in proc.stdout:
        _stdout_write(line)
        out_lines.append(line)
    proc.wait()
    return int(proc.returncode), "".join(out_lines)


def _redact(text: str) -> str:
    # Best-effort redaction to avoid leaking secrets into local state logs.
    out = text

    rx_kv = re.compile(
        r"(?i)\b(password|passwd|token|secret|api[_-]?key|access[_-]?key)\b(\s*[:=]\s*)([^\s\"']+)"
    )
    out = rx_kv.sub(lambda m: f"{m.group(1)}{m.group(2)}***REDACTED***", out)

    rx_bearer = re.compile(r"(?i)\b(bearer)(\s+)([a-z0-9\-\._~\+/]+=*)")
    out = rx_bearer.sub(lambda m: f"{m.group(1)}{m.group(2)}***REDACTED***", out)

    rx_jwt = re.compile(r"\beyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\b")
    out = rx_jwt.sub("***REDACTED***", out)

    return out


def _extract_failure_highlights(output: str, max_tail_lines: int = 40, max_highlight_lines: int = 25) -> str:
    output = _redact(output)
    lines = output.splitlines()
    tail = lines[-max_tail_lines:] if len(lines) > max_tail_lines else lines

    patterns = [
        r"\berror\b",
        r"\bfatal\b",
        r"\bfailed\b",
        r"\bexception\b",
        r"\btraceback\b",
        r"\bassert\b",
        r"cmake error",
        r"msb\d{4}",
        r"\blnk\d+\b",
        r"undefined reference",
        r"segmentation fault",
    ]
    rx = re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)

    highlights: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if rx.search(line):
            key = line.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            highlights.append(line)
            if len(highlights) >= max_highlight_lines:
                break

    buf: list[str] = []
    if highlights:
        buf.append("### Highlights")
        buf.extend([f"- {h.strip()}" for h in highlights])
        buf.append("")
    buf.append("### Tail")
    buf.extend(tail)
    return "\n".join(buf).rstrip() + "\n"


def _append_gate_to_state(repo_root: Path, gate_cmd: str, exit_code: int, output: str) -> None:
    aw = repo_autoworkflow_dir(repo_root)
    state_path = aw / "state.md"

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    status = "green" if exit_code == 0 else f"failed (exit {exit_code})"

    gate_cmd = _redact(gate_cmd)

    section: list[str] = []
    section.append("")
    section.append("## Gate (latest)")
    section.append(f"- Time (UTC): {stamp}")
    section.append(f"- Command: `{gate_cmd}`")
    section.append(f"- Result: {status}")
    section.append("")

    if exit_code != 0:
        section.append(_extract_failure_highlights(output))
    else:
        # Keep success logs minimal to avoid bloating the state file.
        section.append("### Output (success)")
        section.append("- (omitted)")
        section.append("")

    aw.mkdir(parents=True, exist_ok=True)
    if state_path.exists():
        with state_path.open("a", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(section))
    else:
        with state_path.open("w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(section).lstrip("\n"))


def run_gate(repo_root: Path, build: str | None, test: str | None, lint: str | None, fmt: str | None) -> int:
    aw = repo_autoworkflow_dir(repo_root)
    env_path = aw / "gate.env"
    env_values = parse_gate_env(env_path)
    if build is not None:
        env_values["BUILD_CMD"] = build
    if test is not None:
        env_values["TEST_CMD"] = test
    if lint is not None:
        env_values["LINT_CMD"] = lint
    if fmt is not None:
        env_values["FORMAT_CHECK_CMD"] = fmt

    host = host_info()
    if os.name == "nt" and not host.is_wsl:
        gate_ps1 = aw / "tools" / "gate.ps1"
        if not gate_ps1.exists():
            raise RuntimeError("Missing `.autoworkflow/tools/gate.ps1` (run init first).")
        cmd = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(gate_ps1),
        ]
        if env_values.get("BUILD_CMD"):
            cmd += ["-BuildCmd", env_values["BUILD_CMD"]]
        if env_values.get("TEST_CMD"):
            cmd += ["-TestCmd", env_values["TEST_CMD"]]
        if env_values.get("LINT_CMD"):
            cmd += ["-LintCmd", env_values["LINT_CMD"]]
        if env_values.get("FORMAT_CHECK_CMD"):
            cmd += ["-FormatCheckCmd", env_values["FORMAT_CHECK_CMD"]]
        code, output = _run_and_tee(cmd, cwd=repo_root)
        _append_gate_to_state(repo_root, gate_cmd=" ".join(cmd), exit_code=code, output=output)
        return code

    gate_sh = aw / "tools" / "gate.sh"
    if not gate_sh.exists():
        raise RuntimeError("Missing `.autoworkflow/tools/gate.sh` (run init first).")
    cmd = ["bash", str(gate_sh)]
    code, output = _run_and_tee(cmd, cwd=repo_root)
    _append_gate_to_state(repo_root, gate_cmd=" ".join(cmd), exit_code=code, output=output)
    return code


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="autoworkflow")
    parser.add_argument("--root", default=".", help="Target repo root (default: current directory)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize .autoworkflow in the target repo")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing files")

    p_doctor = sub.add_parser("doctor", help="Print a repo+host diagnostics report")
    p_doctor.add_argument("--write", action="store_true", help="Write report to .autoworkflow/doctor.md")
    p_doctor.add_argument("--update-state", action="store_true", help="Append a short marker to .autoworkflow/state.md")

    p_set = sub.add_parser("set-gate", help="Set gate commands in .autoworkflow/gate.env")
    p_set.add_argument("--build", default=None, help="BUILD_CMD")
    p_set.add_argument("--test", default=None, help="TEST_CMD")
    p_set.add_argument("--lint", default=None, help="LINT_CMD")
    p_set.add_argument("--format-check", dest="format_check", default=None, help="FORMAT_CHECK_CMD")
    p_set.add_argument("--create", action="store_true", help="Create gate.env if missing")

    p_gate = sub.add_parser("gate", help="Run the platform-appropriate gate script")
    p_gate.add_argument("--build", default=None, help="Override BUILD_CMD")
    p_gate.add_argument("--test", default=None, help="Override TEST_CMD")
    p_gate.add_argument("--lint", default=None, help="Override LINT_CMD")
    p_gate.add_argument("--format-check", dest="format_check", default=None, help="Override FORMAT_CHECK_CMD")

    p_rec = sub.add_parser("recommend-model", help="Recommend model profile (light/medium/heavy) for Claude/Codex")
    p_rec.add_argument("--intent", default=None, help="Optional intent hint (e.g., doctor, workshop, debug)")

    args = parser.parse_args(argv)
    repo_root = Path(args.root).resolve()

    if args.cmd == "init":
        init_autoworkflow(repo_root=repo_root, force=bool(args.force))
        print(f"Initialized: {repo_autoworkflow_dir(repo_root)}")
        return 0

    if args.cmd == "doctor":
        print(write_doctor(repo_root, write=bool(args.write), update_state=bool(args.update_state)))
        return 0

    if args.cmd == "set-gate":
        write_gate_env(
            repo_autoworkflow_dir(repo_root) / "gate.env",
            updates={
                "BUILD_CMD": args.build,
                "TEST_CMD": args.test,
                "LINT_CMD": args.lint,
                "FORMAT_CHECK_CMD": args.format_check,
            },
            force_create=bool(args.create),
        )
        print("Updated: .autoworkflow/gate.env")
        return 0

    if args.cmd == "gate":
        return run_gate(
            repo_root=repo_root,
            build=args.build,
            test=args.test,
            lint=args.lint,
            fmt=args.format_check,
        )

    if args.cmd == "recommend-model":
        profile, claude, codex = recommend_model(repo_root=repo_root, intent=args.intent)
        print("# Model Recommendation")
        print(f"- profile: {profile}")
        print(f"- claude: {claude}")
        print(f"- codex: {codex}")
        return 0

    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
