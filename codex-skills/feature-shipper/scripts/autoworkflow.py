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
from typing import Any


ALLOWED_ENV_KEYS = ("BUILD_CMD", "TEST_CMD", "LINT_CMD", "FORMAT_CHECK_CMD")
PLAN_FILE_NAME = "plan.yaml"
PLAN_REVIEW_FILE = "plan-review.md"

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

# Default plan template (JSON, valid YAML subset)
DEFAULT_PLAN_TEMPLATE = {
    "meta": {"version": 1},
    "goal_ref": "goal.json",
    "modules": [
        {
            "id": "default-module",
            "purpose": "TBD",
            "scope_in": [],
            "scope_out": [],
            "risks": [],
        }
    ],
    "milestones": [
        {
            "id": "m1",
            "module": "default-module",
            "title": "First milestone",
            "target_date": "",
            "deps": [],
            "success_criteria": ["All gates green"],
        }
    ],
    "tasks": [
        {
            "id": "t1",
            "milestone": "m1",
            "title": "Build & Test",
            "size_days": 0.5,
            "deps": [],
            "gate_cmds": ["build", "test"],
            "risk": "med",
            "blocking": False,
        }
    ],
    "data_specs": [],
    "review": {"decision": "pending", "score": 0, "reasons": [], "actions": []},
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


def plan_path(repo_root: Path) -> Path:
    return repo_autoworkflow_dir(repo_root) / PLAN_FILE_NAME


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


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _read_package_json_scripts(repo_root: Path) -> tuple[str, dict[str, str]]:
    package_json = repo_root / "package.json"
    if not package_json.exists():
        return "npm", {}
    pm = "npm"
    if (repo_root / "pnpm-lock.yaml").exists():
        pm = "pnpm"
    elif (repo_root / "yarn.lock").exists():
        pm = "yarn"

    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
        scripts = data.get("scripts") if isinstance(data, dict) else {}
        if isinstance(scripts, dict):
            return pm, {str(k): str(v) for k, v in scripts.items()}
    except Exception:
        pass
    return pm, {}


def _pm_cmd(pm: str, script: str, kind: str) -> str:
    # keep commands simple and reproducible
    if pm == "npm":
        if kind == "test":
            return "npm test"
        return f"npm run {script}"
    if pm == "pnpm":
        return f"pnpm {script if kind == 'test' else f'run {script}'}"
    if pm == "yarn":
        return f"yarn {script}"
    return f"{pm} {script}"


def detect_node_gate(repo_root: Path) -> dict[str, str]:
    pm, scripts = _read_package_json_scripts(repo_root)
    if not scripts and not (repo_root / "package.json").exists():
        return {}
    def pick(keys: list[str]) -> str | None:
        for k in keys:
            if k in scripts:
                return k
        return None

    build_script = pick(["build", "compile", "bundle"])
    test_script = pick(["test", "test:unit", "test:e2e", "ci:test"])
    lint_script = pick(["lint", "lint:fix", "check"])
    fmt_script = pick(["format", "fmt", "format:check"])

    result: dict[str, str] = {}
    if build_script:
        result["BUILD_CMD"] = _pm_cmd(pm, build_script, "build")
    if test_script:
        result["TEST_CMD"] = _pm_cmd(pm, test_script, "test")
    if lint_script:
        result["LINT_CMD"] = _pm_cmd(pm, lint_script, "lint")
    if fmt_script:
        result["FORMAT_CHECK_CMD"] = _pm_cmd(pm, fmt_script, "format")
    return result


def detect_python_gate(repo_root: Path) -> dict[str, str]:
    strong_project = any(
        [
            (repo_root / "pyproject.toml").exists(),
            (repo_root / "requirements.txt").exists(),
            (repo_root / "poetry.lock").exists(),
            (repo_root / "setup.py").exists(),
            (repo_root / "setup.cfg").exists(),
        ]
    )
    if strong_project:
        uses_poetry = (repo_root / "poetry.lock").exists()
        test_cmd = "poetry run pytest" if uses_poetry else "pytest"
        lint_cmd = "poetry run ruff check ." if uses_poetry else "ruff check ."
        fmt_cmd = "poetry run ruff format --check ." if uses_poetry else "ruff format --check ."
        return {
            "BUILD_CMD": "",
            "TEST_CMD": test_cmd,
            "LINT_CMD": lint_cmd,
            "FORMAT_CHECK_CMD": fmt_cmd,
        }

    # Fallback for "Python scripts" repos (no pyproject/requirements.txt):
    # prefer a deterministic syntax check over guessing pytest/ruff.
    weak_signal = any(
        [
            bool(list(repo_root.glob("requirements*.txt"))),
            bool(list(repo_root.glob("*.py"))),
            bool(list((repo_root / "scripts").glob("*.py"))),
            bool(list((repo_root / "tools").glob("*.py"))),
        ]
    )
    if not weak_signal:
        return {}

    # Avoid misclassifying obvious non-Python projects.
    other_markers = [
        repo_root / "package.json",
        repo_root / "Cargo.toml",
        repo_root / "go.mod",
        repo_root / "pom.xml",
        repo_root / "gradlew",
        repo_root / "gradlew.bat",
        repo_root / "build.gradle",
        repo_root / "build.gradle.kts",
    ]
    if any(p.exists() for p in other_markers) or bool(list(repo_root.glob("*.sln"))):
        return {}

    return {
        "BUILD_CMD": "",
        "TEST_CMD": "python -m compileall -q .",
        "LINT_CMD": "",
        "FORMAT_CHECK_CMD": "",
    }


def detect_rust_gate(repo_root: Path) -> dict[str, str]:
    if not (repo_root / "Cargo.toml").exists():
        return {}
    return {
        "BUILD_CMD": "cargo build",
        "TEST_CMD": "cargo test",
        "LINT_CMD": "cargo clippy -- -D warnings",
        "FORMAT_CHECK_CMD": "cargo fmt -- --check",
    }


def detect_go_gate(repo_root: Path) -> dict[str, str]:
    if not (repo_root / "go.mod").exists():
        return {}
    return {
        "BUILD_CMD": "go build ./...",
        "TEST_CMD": "go test ./...",
        "LINT_CMD": "go vet ./...",
        "FORMAT_CHECK_CMD": "",
    }


def detect_java_gate(repo_root: Path) -> dict[str, str]:
    # Maven / Gradle heuristics
    if (repo_root / "pom.xml").exists():
        return {
            "BUILD_CMD": "mvn -B -DskipTests package",
            "TEST_CMD": "mvn -B test",
            "LINT_CMD": "",
            "FORMAT_CHECK_CMD": "",
        }
    gradlew = repo_root / "gradlew"
    if gradlew.exists():
        gradle_bin = "./gradlew"
    elif (repo_root / "gradlew.bat").exists():
        gradle_bin = "gradlew.bat"
    elif (repo_root / "build.gradle").exists() or (repo_root / "build.gradle.kts").exists():
        gradle_bin = "gradle"
    else:
        return {}
    return {
        "BUILD_CMD": f"{gradle_bin} build -x test",
        "TEST_CMD": f"{gradle_bin} test",
        "LINT_CMD": "",
        "FORMAT_CHECK_CMD": "",
    }


def detect_dotnet_gate(repo_root: Path) -> dict[str, str]:
    has_sln = bool(list(repo_root.glob("*.sln")))
    has_csproj = bool(list(repo_root.rglob("*.csproj")))
    if not (has_sln or has_csproj):
        return {}
    return {
        "BUILD_CMD": "dotnet build",
        "TEST_CMD": "dotnet test",
        "LINT_CMD": "",
        "FORMAT_CHECK_CMD": "",
    }


def detect_claude_gate(repo_root: Path) -> dict[str, str]:
    path = repo_root / "CLAUDE.md"
    if not path.exists():
        return {}
    text = _read_text(path)
    result: dict[str, str] = {}
    rx = re.compile(r"(?im)^(build|test|lint|format)[^:：]{0,15}[:：]\s*`?(.+?)`?\s*$")
    for m in rx.finditer(text):
        key = m.group(1).lower()
        cmd = m.group(2).strip()
        if not cmd:
            continue
        if key == "build":
            result["BUILD_CMD"] = cmd
        elif key == "test":
            result["TEST_CMD"] = cmd
        elif key == "lint":
            result["LINT_CMD"] = cmd
        elif key == "format":
            result["FORMAT_CHECK_CMD"] = cmd
    return result


def detect_gate(repo_root: Path) -> tuple[dict[str, str], dict[str, str]]:
    """
    Returns (suggested, sources) where sources maps key->hint origin.
    Priority: CLAUDE.md overrides structural heuristics.
    """
    sources: dict[str, str] = {}
    suggested: dict[str, str] = {}

    claude = detect_claude_gate(repo_root)
    for k, v in claude.items():
        if v:
            suggested[k] = v
            sources[k] = "CLAUDE.md"

    detectors = [
        ("Node.js", detect_node_gate),
        ("Python", detect_python_gate),
        ("Rust", detect_rust_gate),
        ("Go", detect_go_gate),
        ("Java", detect_java_gate),
        (".NET", detect_dotnet_gate),
    ]
    for origin, fn in detectors:
        found = fn(repo_root)
        for k, v in found.items():
            if k in suggested:
                continue
            if v:
                suggested[k] = v
                sources[k] = origin
    return suggested, sources


def _normalize_gate_value(raw: str) -> str:
    val = raw.strip()
    if len(val) >= 2 and ((val[0] == val[-1] == '"') or (val[0] == val[-1] == "'")):
        val = val[1:-1].strip()
    val = val.strip("`").strip()
    return val


def parse_gate_kv_from_text(text: str) -> dict[str, str]:
    """
    Extracts BUILD_CMD/TEST_CMD/LINT_CMD/FORMAT_CHECK_CMD from arbitrary text.
    Accepts:
      - KEY=value
      - - KEY=value
      - `KEY=value`
    """
    found: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = line.strip().strip("`")
        if line.startswith(("-", "*")):
            line = line[1:].lstrip().strip("`")
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key not in ALLOWED_ENV_KEYS:
            continue
        found[key] = _normalize_gate_value(value)
    return found


def codex_detect_gate(
    repo_root: Path,
    *,
    oss: bool,
    local_provider: str | None,
    model: str | None,
    timeout_seconds: int,
) -> tuple[dict[str, str], str]:
    codex_bin = shutil.which("codex")
    if not codex_bin and os.name == "nt":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            candidate = Path(appdata) / "npm" / "codex.cmd"
            if candidate.exists():
                codex_bin = str(candidate)
    if not codex_bin:
        raise RuntimeError("codex CLI not found in PATH (install codex-cli or disable --codex).")

    prompt = "\n".join(
        [
            "You are in a project repository root.",
            "",
            "Goal: infer gate commands for the repo.",
            "",
            "Hard rules:",
            "- Do NOT run any commands/tests.",
            "- Do NOT modify any files.",
            "- You may read repo files.",
            "- Output exactly 4 lines (allow empty values). No markdown/code blocks/explanations:",
            "BUILD_CMD=",
            "TEST_CMD=",
            "LINT_CMD=",
            "FORMAT_CHECK_CMD=",
            "",
            "Hint: if you cannot infer a real test entrypoint, set TEST_CMD to: python -m compileall -q .",
        ]
    )

    cmd: list[str] = [
        codex_bin,
        "--sandbox",
        "read-only",
        "--ask-for-approval",
        "untrusted",
    ]
    if oss:
        cmd.append("--oss")
        if local_provider:
            cmd.extend(["--local-provider", local_provider])
    if model:
        cmd.extend(["--model", model])
    cmd.extend(["exec", "--skip-git-repo-check", "-C", str(repo_root), "-"])

    proc = subprocess.Popen(
        cmd,
        cwd=str(repo_root),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        output, _ = proc.communicate(input=prompt, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            else:
                proc.kill()
        except Exception:
            pass
        raise RuntimeError(f"codex exec timed out after {timeout_seconds}s")
    output = output or ""
    code = int(proc.returncode or 0)
    parsed = parse_gate_kv_from_text(output)
    if parsed:
        return parsed, output
    preview = output[:4000]
    suffix = "" if len(output) <= 4000 else "\n...(truncated)..."
    raise RuntimeError(f"codex exec failed (exit {code}) or produced no KEY=value output.\n{preview}{suffix}")


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


def run_gate(
    repo_root: Path,
    build: str | None,
    test: str | None,
    lint: str | None,
    fmt: str | None,
    allow_unreviewed: bool,
) -> int:
    guard_plan_review(repo_root, allow_unreviewed=allow_unreviewed)
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


def _load_plan(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError("Missing plan.yaml (run `autoworkflow plan init`)")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"plan.yaml 解析失败: {exc}")


def _dump_plan(path: Path, data: dict[str, Any]) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    safe_write_text(path, text + "\n", force=True)


def plan_init(repo_root: Path, force: bool) -> None:
    target = plan_path(repo_root)
    if target.exists() and not force:
        print(f"plan.yaml already exists, use --force to overwrite ({target})")
        return
    _dump_plan(target, DEFAULT_PLAN_TEMPLATE)
    print(f"Initialized plan: {target}")


def _detect_gate_ids(repo_root: Path) -> dict[str, str]:
    env = parse_gate_env(repo_autoworkflow_dir(repo_root) / "gate.env")
    mapping: dict[str, str] = {}
    if env.get("BUILD_CMD"):
        mapping["build"] = env["BUILD_CMD"]
    if env.get("TEST_CMD"):
        mapping["test"] = env["TEST_CMD"]
    if env.get("LINT_CMD"):
        mapping["lint"] = env["LINT_CMD"]
    if env.get("FORMAT_CHECK_CMD"):
        mapping["format"] = env["FORMAT_CHECK_CMD"]
    return mapping


def plan_gen(repo_root: Path) -> None:
    aw = repo_autoworkflow_dir(repo_root)
    aw.mkdir(parents=True, exist_ok=True)

    gates = _detect_gate_ids(repo_root)
    module_id = "default-module"
    tasks: list[dict[str, Any]] = []
    idx = 1
    for key in ("build", "test", "lint", "format"):
        if key in gates:
            tasks.append(
                {
                    "id": f"t{idx}",
                    "milestone": "m1",
                    "title": f"Run {key}",
                    "size_days": 0.25,
                    "deps": [],
                    "gate_cmds": [key],
                    "risk": "low",
                    "blocking": False,
                }
            )
            idx += 1
    if not tasks:
        tasks = [
            {
                "id": "t1",
                "milestone": "m1",
                "title": "Define gate commands",
                "size_days": 0.5,
                "deps": [],
                "gate_cmds": [],
                "risk": "med",
                "blocking": True,
            }
        ]

    plan = {
        "meta": {"version": 1},
        "goal_ref": "goal.json",
        "modules": [
            {
                "id": module_id,
                "purpose": "Auto-generated plan (edit as needed)",
                "scope_in": [],
                "scope_out": [],
                "risks": [],
            }
        ],
        "milestones": [
            {
                "id": "m1",
                "module": module_id,
                "title": "Initial delivery",
                "target_date": "",
                "deps": [],
                "success_criteria": ["Gate green"],
            }
        ],
        "tasks": tasks,
        "data_specs": [],
        "review": {"decision": "pending", "score": 0, "reasons": [], "actions": []},
    }
    _dump_plan(plan_path(repo_root), plan)
    print(f"Generated plan: {plan_path(repo_root)}")


def _penalize(condition: bool, penalty: int, reasons: list[str], msg: str) -> int:
    if condition:
        reasons.append(msg)
        return penalty
    return 0


def plan_review(repo_root: Path, min_score: int = 85) -> int:
    path = plan_path(repo_root)
    plan = _load_plan(path)
    reasons: list[str] = []
    actions: list[str] = []
    score = 100

    tasks = plan.get("tasks", [])
    milestones = {m.get("id"): m for m in plan.get("milestones", [])}
    data_specs = plan.get("data_specs", [])

    if not tasks:
        reasons.append("没有 tasks")
        score = 0

    for t in tasks:
        size = t.get("size_days", 0)
        score -= _penalize(size and size > 1.0, 10, reasons, f"Task {t.get('id')} size_days>1")
        g = t.get("gate_cmds") or []
        score -= _penalize(len(g) == 0, 12, reasons, f"Task {t.get('id')} 缺少 gate_cmds")
        mid = t.get("milestone")
        if mid and mid not in milestones:
            score -= _penalize(True, 8, reasons, f"Task {t.get('id')} 关联未知 milestone {mid}")

    for spec in data_specs:
        if spec.get("breaking_change"):
            mod = spec.get("module", "")
            related = [t for t in tasks if mod and mod in t.get("title", "").lower()]
            score -= _penalize(len(related) == 0, 12, reasons, f"{mod} 标记 breaking_change 但无迁移/兼容任务")

    decision = "approve" if score >= min_score else "reject"
    if decision == "reject":
        actions.append("调整 plan 后重跑 plan review（score>=85 才可通过 gate）")

    plan["review"] = {
        "decision": decision,
        "score": max(0, score),
        "reasons": reasons,
        "actions": actions,
        "reviewed_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
    }
    _dump_plan(path, plan)

    review_md = []
    review_md.append("# Plan Review")
    review_md.append(f"- decision: {decision}")
    review_md.append(f"- score: {max(0, score)}")
    if reasons:
        review_md.append("## Reasons")
        review_md.extend([f"- {r}" for r in reasons])
    if actions:
        review_md.append("## Actions")
        review_md.extend([f"- {a}" for a in actions])
    safe_write_text(repo_autoworkflow_dir(repo_root) / PLAN_REVIEW_FILE, "\n".join(review_md) + "\n", force=True)

    # append to state
    state_path = repo_autoworkflow_dir(repo_root) / "state.md"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    section = "\n".join(
        [
            "",
            "## Plan Review (latest)",
            f"- Time (UTC): {stamp}",
            f"- decision: {decision}",
            f"- score: {max(0, score)}",
            f"- reasons: {', '.join(reasons) if reasons else '(none)'}",
            "",
        ]
    )
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(section)

    print(f"Plan review: {decision} (score={max(0, score)})")
    return 0 if decision == "approve" else 1


def plan_status(repo_root: Path) -> int:
    try:
        plan = _load_plan(plan_path(repo_root))
    except Exception as exc:
        print(f"plan status: {exc}")
        return 1
    tasks = plan.get("tasks", [])
    total = len(tasks)
    blocking = len([t for t in tasks if t.get("blocking")])
    no_gate = len([t for t in tasks if not t.get("gate_cmds")])
    review = plan.get("review", {})
    summary = "\n".join(
        [
            "# Plan Status",
            f"- tasks: {total}",
            f"- blocking tasks: {blocking}",
            f"- tasks missing gate_cmds: {no_gate}",
            f"- last review: {review.get('decision','pending')} (score={review.get('score',0)})",
        ]
    )
    print(summary)
    # append to state
    state_path = repo_autoworkflow_dir(repo_root) / "state.md"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    section = "\n".join(
        [
            "",
            "## Plan Status (latest)",
            f"- Time (UTC): {stamp}",
            f"- tasks: {total}",
            f"- blocking: {blocking}",
            f"- missing gate_cmds: {no_gate}",
            f"- review decision: {review.get('decision','pending')} (score={review.get('score',0)})",
            "",
        ]
    )
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(section)
    return 0


def guard_plan_review(repo_root: Path, allow_unreviewed: bool) -> None:
    path = plan_path(repo_root)
    if not path.exists():
        return
    try:
        plan = _load_plan(path)
    except Exception as exc:
        if allow_unreviewed:
            print(f"plan guard warning: {exc}")
            return
        raise RuntimeError(f"plan guard: {exc}")
    review = plan.get("review", {})
    decision = review.get("decision", "pending")
    if decision != "approve" and not allow_unreviewed:
        raise RuntimeError("plan guard: plan review 未批准（decision!=approve），使用 --allow-unreviewed 可跳过（不推荐）。")


def plan_ci_template(repo_root: Path, provider: str) -> int:
    aw = repo_autoworkflow_dir(repo_root)
    aw.mkdir(parents=True, exist_ok=True)
    if provider == "github":
        path = repo_root / ".github" / "workflows"
        path.mkdir(parents=True, exist_ok=True)
        content = """name: aw-plan-gate

on:
  push:
    branches: [ "*" ]
  pull_request:
  workflow_dispatch:
  schedule:
    - cron: "0 3 * * *"  # set ENABLE_SCHEDULE=true to activate

jobs:
  plan-gate:
    runs-on: ubuntu-latest
    env:
      ENABLE_SCHEDULE: "false"
    if: github.event_name != 'schedule' || env.ENABLE_SCHEDULE == 'true'
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - name: Init autoworkflow
        run: python codex-skills/feature-shipper/scripts/autoworkflow.py --root . init --force
      - name: Plan review
        run: python .autoworkflow/tools/autoworkflow.py --root . plan review
      - name: Gate (dry-run)
        run: python .autoworkflow/tools/autoworkflow.py --root . gate --allow-unreviewed
      - name: Agents workflow (trace)
        run: python agents_runner.py --root . --allow-unreviewed
      - name: Agents SDK runner (optional)
        run: python agents_sdk_runner.py --root . --allow-unreviewed
        continue-on-error: true
      - name: Upload trace
        uses: actions/upload-artifact@v4
        with:
          name: aw-trace
          path: .autoworkflow/trace/*.jsonl
"""
    else:
        path = repo_root / ".gitlab-ci.yml"
        content = """plan_gate:
  image: python:3.11
  stage: test
  script:
    - python codex-skills/feature-shipper/scripts/autoworkflow.py --root . init --force
    - python .autoworkflow/tools/autoworkflow.py --root . plan review
    - python .autoworkflow/tools/autoworkflow.py --root . gate --allow-unreviewed
    - python agents_runner.py --root . --allow-unreviewed
    - python agents_sdk_runner.py --root . --allow-unreviewed || true
  artifacts:
    paths:
      - .autoworkflow/trace/*.jsonl
"""
    if provider == "github":
        target = path / "aw-plan-gate.yml"
    else:
        target = path
    target.parent.mkdir(parents=True, exist_ok=True)
    safe_write_text(target, content, force=True)
    print(f"Generated CI template: {target}")
    return 0


def auto_gate(
    repo_root: Path,
    overwrite: bool,
    dry_run: bool,
    *,
    use_codex: bool,
    codex_oss: bool,
    codex_local_provider: str | None,
    codex_model: str | None,
    codex_timeout_seconds: int,
) -> int:
    aw = repo_autoworkflow_dir(repo_root)
    if not aw.exists():
        init_autoworkflow(repo_root=repo_root, force=False)

    env_path = aw / "gate.env"
    existing = parse_gate_env(env_path)

    detected, sources = detect_gate(repo_root)
    final: dict[str, str] = dict(existing)
    for key in ALLOWED_ENV_KEYS:
        val = detected.get(key, "")
        if overwrite or not final.get(key):
            if val:
                final[key] = val

    if use_codex and (overwrite or not final.get("TEST_CMD")):
        try:
            codex_detected, _raw = codex_detect_gate(
                repo_root,
                oss=codex_oss,
                local_provider=codex_local_provider,
                model=codex_model,
                timeout_seconds=codex_timeout_seconds,
            )
            for key in ALLOWED_ENV_KEYS:
                val = codex_detected.get(key, "")
                if not val:
                    continue
                if overwrite or not final.get(key):
                    final[key] = val
                    sources[key] = "codex"
        except Exception as exc:
            print(f"auto-gate: codex fallback failed: {exc}")

    if not final.get("TEST_CMD"):
        print("auto-gate: 未能自动推导 TEST_CMD，请手动设置 `autoworkflow set-gate --test ...` 或编辑 .autoworkflow/gate.env")
        return 2

    lines: list[str] = []
    lines.append("Auto-detected gate commands:")
    for key in ALLOWED_ENV_KEYS:
        val = final.get(key, "")
        src = sources.get(key, "existing" if key in existing else "heuristic")
        lines.append(f"- {key}: {val or '(empty)'}  [source: {src}]")
    print("\n".join(lines))

    if dry_run:
        print("dry-run: 未写入 .autoworkflow/gate.env")
        return 0

    write_gate_env(env_path, updates=final, force_create=True)
    print("Updated: .autoworkflow/gate.env (auto-gate)")
    return 0


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

    p_auto = sub.add_parser("auto-gate", help="Auto-detect gate commands and write .autoworkflow/gate.env")
    p_auto.add_argument("--overwrite", action="store_true", help="Overwrite non-empty existing values")
    p_auto.add_argument("--dry-run", action="store_true", help="Only print detected commands")
    p_auto.add_argument("--codex", action="store_true", help="Also ask Codex CLI to infer gate commands (read-only)")
    p_auto.add_argument("--codex-oss", action="store_true", help="Use local OSS provider for Codex (--oss)")
    p_auto.add_argument("--codex-local-provider", choices=["ollama", "lmstudio"], default=None, help="Codex local provider")
    p_auto.add_argument("--codex-model", default=None, help="Codex model name (optional)")
    p_auto.add_argument("--codex-timeout", type=int, default=180, help="Codex exec timeout seconds (default 180)")

    p_gate = sub.add_parser("gate", help="Run the platform-appropriate gate script")
    p_gate.add_argument("--build", default=None, help="Override BUILD_CMD")
    p_gate.add_argument("--test", default=None, help="Override TEST_CMD")
    p_gate.add_argument("--lint", default=None, help="Override LINT_CMD")
    p_gate.add_argument("--format-check", dest="format_check", default=None, help="Override FORMAT_CHECK_CMD")
    p_gate.add_argument("--allow-unreviewed", action="store_true", help="Skip plan review guard (not recommended)")

    p_plan = sub.add_parser("plan", help="Plan lifecycle (init/gen/review/status)")
    plan_sub = p_plan.add_subparsers(dest="plan_cmd", required=True)
    p_plan_init = plan_sub.add_parser("init", help="Create default plan.yaml")
    p_plan_init.add_argument("--force", action="store_true", help="Overwrite existing plan.yaml")
    plan_sub.add_parser("gen", help="Generate plan.yaml from gate/env heuristics")
    p_plan_review = plan_sub.add_parser("review", help="Review plan.yaml and write plan-review.md/state")
    p_plan_review.add_argument("--min-score", type=int, default=85, help="Minimum score to approve (default 85)")
    plan_sub.add_parser("status", help="Summarize plan status and append to state.md")
    p_plan_ci = plan_sub.add_parser("ci-template", help="Generate CI template for plan review + gate dry-run")
    p_plan_ci.add_argument("--provider", choices=["github", "gitlab"], default="github", help="CI provider")

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

    if args.cmd == "auto-gate":
        return auto_gate(
            repo_root=repo_root,
            overwrite=bool(args.overwrite),
            dry_run=bool(args.dry_run),
            use_codex=bool(args.codex),
            codex_oss=bool(args.codex_oss),
            codex_local_provider=args.codex_local_provider,
            codex_model=args.codex_model,
            codex_timeout_seconds=int(args.codex_timeout),
        )

    if args.cmd == "gate":
        return run_gate(
            repo_root=repo_root,
            build=args.build,
            test=args.test,
            lint=args.lint,
            fmt=args.format_check,
            allow_unreviewed=bool(args.allow_unreviewed),
        )

    if args.cmd == "recommend-model":
        profile, claude, codex = recommend_model(repo_root=repo_root, intent=args.intent)
        print("# Model Recommendation")
        print(f"- profile: {profile}")
        print(f"- claude: {claude}")
        print(f"- codex: {codex}")
        return 0

    if args.cmd == "plan":
        if args.plan_cmd == "init":
            plan_init(repo_root=repo_root, force=bool(args.force))
            return 0
        if args.plan_cmd == "gen":
            plan_gen(repo_root=repo_root)
            return 0
        if args.plan_cmd == "review":
            return plan_review(repo_root=repo_root, min_score=int(args.min_score))
        if args.plan_cmd == "status":
            return plan_status(repo_root=repo_root)
        if args.plan_cmd == "ci-template":
            return plan_ci_template(repo_root=repo_root, provider=str(args.provider))
        raise AssertionError("unknown plan subcommand")

    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
