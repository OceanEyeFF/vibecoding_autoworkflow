#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Code Autoworkflow - 自动化工具链

功能：init / doctor / set-gate / gate / recommend-model
特点：
1. 与 Codex autoworkflow.py 功能对齐
2. 为 Claude Code 环境优化
3. 支持与 Codex 混合使用（共享层 + 隔离层）
4. 软锁协调机制避免并发冲突

使用方式：
  python claude_autoworkflow.py init [--force]
  python claude_autoworkflow.py doctor [--write] [--update-state]
  python claude_autoworkflow.py set-gate --build "..." --test "..."
  python claude_autoworkflow.py gate
  python claude_autoworkflow.py recommend-model --intent <doctor|implement|debug|refactor>
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# ============================================================================
# Constants
# ============================================================================

TOOL_NAME = "claude-code"
TOOL_VERSION = "1.0.0"

# Shared layer paths (project-level, shared with Codex)
SHARED_DIR_NAME = ".autoworkflow"

# Isolated layer paths (AI software-level, Claude Code only)
LOGS_SUBDIR = "logs"
CLAUDE_LOGS_SUBDIR = "claude-code"

# Ownership settings
OWNERSHIP_TTL_MINUTES = 30

# Allowed environment keys in gate.env
ALLOWED_ENV_KEYS = frozenset({
    "BUILD_CMD", "TEST_CMD", "LINT_CMD", "FORMAT_CHECK_CMD",
})

# ============================================================================
# Cross-platform Output Helpers
# ============================================================================

def safe_print(msg: str, **kwargs) -> None:
    """Safe print that handles encoding issues on Windows console.

    Implements multi-level fallback:
    1. Try native encoding
    2. Fall back to ASCII with replacement
    3. Fall back to stderr if all else fails
    """
    flush = kwargs.pop("flush", True)  # Always flush

    try:
        print(msg, flush=flush, **kwargs)
        return
    except UnicodeEncodeError:
        pass  # Try fallback
    except Exception as e:
        # Last resort: write to stderr
        sys.stderr.write(f"[PRINT ERROR] {repr(msg)}\n")
        sys.stderr.flush()
        return

    # Fallback 1: ASCII with replacement characters
    try:
        safe_msg = msg.encode('ascii', errors='replace').decode('ascii')
        print(safe_msg, flush=flush, **kwargs)
    except Exception:
        # Fallback 2: write repr to stderr
        sys.stderr.write(f"[FALLBACK] {repr(msg)}\n")
        sys.stderr.flush()


# Emoji fallback mapping for Windows console
EMOJI_MAP = {
    "🔍": "[SCAN]",
    "🆕": "[NEW]",
    "✅": "[OK]",
    "❌": "[FAIL]",
    "⚠️": "[WARN]",
    "🚀": "[RUN]",
    "🎉": "[DONE]",
    "🤖": "[AI]",
    "📝": "[NOTE]",
    "🔄": "[SYNC]",
    "🔒": "[LOCK]",
}


def emoji(key: str) -> str:
    """Return emoji or ASCII fallback based on console capability."""
    if sys.platform == "win32" and not os.environ.get("WT_SESSION"):
        # Windows Console (not Windows Terminal) - use ASCII
        return EMOJI_MAP.get(key, key)
    return key


# ============================================================================
# Default Templates
# ============================================================================

DEFAULT_SPEC_TEMPLATE = """\
# Spec: [One-liner title]

<!-- source: {tool_name} -->
<!-- created: {timestamp} -->

## 1) One-liner
[What are we building in one sentence?]

## 2) Problem & User
- **Problem**: [What pain point does this solve?]
- **User**: [Who benefits?]
- **Why now**: [Why is this urgent?]

## 3) Scope
### In scope
- [Feature 1]
- [Feature 2]

### Out of scope
- [Explicitly excluded item]

## 4) Constraints
- Platform: [Windows/Linux/macOS]
- Language: [Python/TypeScript/etc.]
- Dependencies: [Existing libs to use]

## 5) Requirements
| ID | Requirement | Priority |
|----|-------------|----------|
| R1 | [Description] | Must |
| R2 | [Description] | Should |

## 6) Acceptance Criteria
- [ ] AC1: [Verifiable criterion]
- [ ] AC2: [Verifiable criterion]

## 7) Test-Green Definition
```bash
# Gate commands that must pass
BUILD_CMD="{build_cmd}"
TEST_CMD="{test_cmd}"
```

## 8) Open Questions
1. [Question that blocks implementation]
"""

DEFAULT_STATE_TEMPLATE = """\
# Execution State

<!-- source: {tool_name} -->
<!-- created: {timestamp} -->

## Definition of Done
- [ ] All acceptance criteria met
- [ ] Gate passes (tests all green)

## Source Docs
- Spec: `.autoworkflow/spec.md`

## Task List
| ID | Task | Status | Verified |
|----|------|--------|----------|
| 1 | [Task description] | pending | - |

## Chosen Commands
- Build: `{build_cmd}`
- Test: `{test_cmd}`

## Last Run
_No gate runs yet._

## Next Step
[What to do next]
"""

DEFAULT_GATE_ENV = """\
# Gate configuration
# Uncomment and set the commands for your project

# BUILD_CMD=npm run build
# TEST_CMD=npm test
# LINT_CMD=npm run lint
# FORMAT_CHECK_CMD=npm run format:check
"""

DEFAULT_MODEL_POLICY = {
    "version": "1.0.0",
    "profiles": {
        "light": {"claude": "haiku", "codex": "gpt-4o-mini"},
        "medium": {"claude": "sonnet", "codex": "gpt-4o"},
        "heavy": {"claude": "opus", "codex": "o1"},
    },
    "rules": [
        {"if": "gate_failed", "then": "heavy", "reason": "Tests failing; use stronger model"},
        {"if": "no_gate_configured", "then": "medium", "reason": "Need workshop first"},
        {"if": "doctor_only", "then": "light", "reason": "Deterministic tooling"},
    ],
    "intents": {
        "doctor": "light",
        "init": "light",
        "implement": "medium",
        "debug": "heavy",
        "refactor": "heavy",
    },
}

DEFAULT_AGENT_CONFIG = {
    "version": "1.0.0",
    "tool_name": TOOL_NAME,
    "auto_init": True,
    "auto_doctor": True,
    "auto_gate": True,
    "ownership": {
        "ttl_minutes": OWNERSHIP_TTL_MINUTES,
        "on_conflict": "prompt",
    },
    "model_policy": {
        "default": "sonnet",
        "intents": {
            "doctor": "sonnet",
            "implement": "sonnet",
            "debug": "opus",
            "refactor": "opus",
        },
    },
    "paths": {
        "shared": SHARED_DIR_NAME,
        "logs": f"{SHARED_DIR_NAME}/{LOGS_SUBDIR}/{CLAUDE_LOGS_SUBDIR}",
    },
}

# ============================================================================
# Data Classes
# ============================================================================

@dataclass(frozen=True)
class HostInfo:
    """Host environment information."""
    os_name: str
    platform_name: str
    python_version: str
    is_wsl: bool


@dataclass
class OwnerInfo:
    """Ownership information for .owner file."""
    tool: str
    session_id: str
    acquired_at: str
    last_activity: str
    ttl_minutes: int = OWNERSHIP_TTL_MINUTES


@dataclass
class GateResult:
    """Result of a gate execution."""
    status: str  # "PASS" or "FAIL"
    exit_code: int
    timestamp: str
    command: str
    output: str
    highlights: list[str] = field(default_factory=list)


@dataclass
class DoctorResult:
    """Result of a doctor diagnosis."""
    timestamp: str
    host_info: HostInfo
    markers: list[str]
    autoworkflow_exists: bool
    gate_configured: bool
    gate_env: dict[str, str]
    issues: list[str]
    recommendations: list[str]


# ============================================================================
# Utility Functions
# ============================================================================

def get_host_info() -> HostInfo:
    """Get host environment information."""
    is_wsl = False
    if os.name == "posix":
        try:
            with open("/proc/version", "r") as f:
                content = f.read().lower()
                is_wsl = "microsoft" in content or "wsl" in content
        except (FileNotFoundError, PermissionError):
            pass

    return HostInfo(
        os_name=os.name,
        platform_name=platform.system().lower(),
        python_version=platform.python_version(),
        is_wsl=is_wsl,
    )


def utc_now_iso() -> str:
    """Get current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def generate_session_id() -> str:
    """Generate a unique session ID."""
    import hashlib
    import uuid
    return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:12]


def parse_iso_timestamp(ts: str) -> datetime | None:
    """Parse ISO 8601 timestamp with compatibility for multiple formats.

    Handles:
    - Standard ISO format: 2025-12-26T07:38:00Z
    - With milliseconds: 2025-12-26T07:38:00.123Z
    - With timezone offset: 2025-12-26T07:38:00+00:00
    """
    if not ts:
        return None

    # Replace Z with +00:00 for fromisoformat compatibility
    ts = ts.replace("Z", "+00:00")

    # Try standard fromisoformat
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        pass

    # Try removing milliseconds if present
    try:
        ts_no_ms = re.sub(r'\.\d+', '', ts)
        return datetime.fromisoformat(ts_no_ms)
    except ValueError:
        pass

    # Try removing timezone offset for older Python versions
    try:
        ts_no_tz = re.sub(r'[+-]\d{2}:\d{2}$', '', ts)
        ts_no_tz = re.sub(r'\.\d+', '', ts_no_tz)
        dt = datetime.fromisoformat(ts_no_tz)
        # Assume UTC if no timezone was present
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def safe_write_text(path: Path, content: str, force: bool = False) -> bool:
    """Safely write text to a file."""
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def redact_secrets(text: str) -> str:
    """Redact sensitive information from text."""
    patterns = [
        (r"(?i)\b(password|passwd|token|secret|api[_-]?key|access[_-]?key)\b(\s*[:=]\s*)([^\s\"']+)",
         r"\1\2***REDACTED***"),
        (r"(?i)\b(bearer)(\s+)([a-z0-9\-\._~\+/]+=*)",
         r"\1\2***REDACTED***"),
        (r"\beyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\b",
         "***REDACTED***"),
    ]
    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)
    return result


def extract_highlights(output: str, max_lines: int = 25) -> list[str]:
    """Extract error highlights from command output."""
    error_patterns = [
        r"\berror\b", r"\bfatal\b", r"\bfailed\b", r"\bexception\b",
        r"\btraceback\b", r"\bassert\b", r"FAIL", r"Error:",
    ]
    combined_pattern = re.compile("|".join(error_patterns), re.IGNORECASE)

    highlights = []
    for line in output.splitlines():
        if combined_pattern.search(line) and len(highlights) < max_lines:
            highlights.append(line.strip())
    return highlights


def detect_project_markers(root: Path) -> list[str]:
    """Detect project type markers."""
    markers = []
    marker_files = [
        "package.json", "pyproject.toml", "setup.py", "requirements.txt",
        "go.mod", "Cargo.toml", "pom.xml", "build.gradle",
        "CMakeLists.txt", "Makefile", ".csproj",
    ]
    marker_dirs = [
        ".github/workflows", ".gitlab-ci.yml", ".circleci",
        "node_modules", "venv", ".venv", "__pycache__",
    ]

    for f in marker_files:
        if (root / f).exists():
            markers.append(f)

    for d in marker_dirs:
        if (root / d).exists():
            markers.append(f"{d}/")

    return markers


# ============================================================================
# Main Class
# ============================================================================

class ClaudeAutoworkflow:
    """Claude Code Autoworkflow - main controller class."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.shared_dir = self.root / SHARED_DIR_NAME
        self.logs_dir = self.shared_dir / LOGS_SUBDIR / CLAUDE_LOGS_SUBDIR
        self.history_dir = self.shared_dir / "history"
        self.tools_dir = self.shared_dir / "tools"
        self.session_id = generate_session_id()

    # ========================================================================
    # Ownership Management
    # ========================================================================

    def _owner_file(self) -> Path:
        return self.shared_dir / ".owner"

    def check_ownership(self) -> tuple[bool, OwnerInfo | None]:
        """Check if we can acquire ownership of the autoworkflow directory.

        Returns: (can_acquire, existing_owner_info)
        """
        owner_file = self._owner_file()

        # Try to read and parse owner file (handles TOCTOU safely)
        try:
            data = json.loads(owner_file.read_text(encoding="utf-8"))
            owner = OwnerInfo(**data)
        except FileNotFoundError:
            # File doesn't exist, we can acquire
            return True, None
        except (json.JSONDecodeError, TypeError, KeyError, UnicodeDecodeError):
            # Corrupted owner file, we can take over
            return True, None

        # Check TTL
        try:
            last_activity_dt = parse_iso_timestamp(owner.last_activity)
            if not last_activity_dt:
                return True, owner  # Can't parse timestamp, can take over

            ttl = timedelta(minutes=owner.ttl_minutes)
            if datetime.now(timezone.utc) - last_activity_dt > ttl:
                return True, owner  # Expired, can take over
        except (ValueError, AttributeError, TypeError):
            return True, owner  # Invalid data, can take over

        # Check if it's us
        if owner.tool == TOOL_NAME:
            return True, owner

        # Conflict with another tool
        return False, owner

    def acquire_ownership(self) -> bool:
        """Acquire ownership of the autoworkflow directory with atomic write.

        Uses atomic rename to prevent concurrent tools from both acquiring ownership.
        """
        can_acquire, existing = self.check_ownership()

        if not can_acquire:
            return False

        owner = OwnerInfo(
            tool=TOOL_NAME,
            session_id=self.session_id,
            acquired_at=utc_now_iso(),
            last_activity=utc_now_iso(),
            ttl_minutes=OWNERSHIP_TTL_MINUTES,
        )

        self.shared_dir.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp file first, then rename
        import tempfile
        owner_file = self._owner_file()
        owner_json = json.dumps(owner.__dict__, indent=2, ensure_ascii=False)

        try:
            # Create temporary file in the same directory (for atomic rename)
            with tempfile.NamedTemporaryFile(
                mode="w",
                dir=str(self.shared_dir),
                prefix=".owner.tmp.",
                suffix=".json",
                delete=False,
                encoding="utf-8"
            ) as tmp:
                tmp.write(owner_json)
                tmp_path = tmp.name

            # Atomic rename (POSIX atomic, Windows needs extra handling)
            try:
                if sys.platform == "win32" and owner_file.exists():
                    # Windows: must remove target before rename
                    owner_file.unlink()
                os.replace(tmp_path, str(owner_file))
                return True
            except Exception as e:
                # Cleanup temp file on error
                try:
                    Path(tmp_path).unlink()
                except Exception:
                    pass
                safe_print(f"{emoji('❌')} Failed to acquire ownership: {e}")
                return False
        except Exception as e:
            safe_print(f"{emoji('❌')} Failed to write ownership file: {e}")
            return False

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        owner_file = self._owner_file()
        if not owner_file.exists():
            return

        try:
            data = json.loads(owner_file.read_text(encoding="utf-8"))
            data["last_activity"] = utc_now_iso()
            owner_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except (json.JSONDecodeError, KeyError):
            pass

    def release_ownership(self) -> None:
        """Release ownership of the autoworkflow directory."""
        owner_file = self._owner_file()
        if owner_file.exists():
            try:
                data = json.loads(owner_file.read_text(encoding="utf-8"))
                if data.get("tool") == TOOL_NAME:
                    owner_file.unlink()
            except (json.JSONDecodeError, KeyError):
                owner_file.unlink()

    # ========================================================================
    # Logging (Isolated Layer)
    # ========================================================================

    def log_event(self, kind: str, message: str, data: dict | None = None) -> None:
        """Log an event to the Claude Code feedback log."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.logs_dir / "feedback.jsonl"

        event = {
            "ts": utc_now_iso(),
            "tool": TOOL_NAME,
            "session": self.session_id,
            "kind": kind,
            "message": message,
            "data": data or {},
        }

        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def log_operation(self, operation: str, result: dict) -> None:
        """Log an operation to the shared history directory."""
        self.history_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        history_file = self.history_dir / f"{timestamp}_{TOOL_NAME}_{operation}.json"

        entry = {
            "tool": TOOL_NAME,
            "session": self.session_id,
            "operation": operation,
            "timestamp": utc_now_iso(),
            "result": result,
        }

        history_file.write_text(
            json.dumps(entry, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    # ========================================================================
    # Detection
    # ========================================================================

    def detect_existing_toolchain(self) -> str | None:
        """Detect if an existing toolchain exists and who created it."""
        if not self.shared_dir.exists():
            return None

        # Check owner file
        owner_file = self._owner_file()
        if owner_file.exists():
            try:
                data = json.loads(owner_file.read_text(encoding="utf-8"))
                return data.get("tool", "unknown")
            except (json.JSONDecodeError, KeyError):
                pass

        # Check for Codex-specific files
        if (self.tools_dir / "autoworkflow.py").exists():
            return "codex"

        # Check for Claude-specific logs
        if self.logs_dir.exists():
            return TOOL_NAME

        return "unknown"

    # ========================================================================
    # Commands
    # ========================================================================

    def cmd_init(self, force: bool = False) -> int:
        """Initialize the autoworkflow directory."""
        existing = self.detect_existing_toolchain()

        if existing == "codex":
            safe_print(f"{emoji('🔍')} 检测到 Codex 工具链，进入混合模式...")
            self._init_logs_only()
        elif existing == TOOL_NAME and not force:
            safe_print(f"{emoji('✅')} Claude Code 工具链已存在")
            print(f"   使用 --force 强制重新初始化")
            return 0
        elif existing and not force:
            safe_print(f"{emoji('⚠️')} 检测到 {existing} 工具链，进入混合模式...")
            self._init_logs_only()
        else:
            safe_print(f"{emoji('🆕')} 创建 Claude Code 工具链...")
            self._init_full(force=force)

        # Acquire ownership
        self.acquire_ownership()
        self.log_event("init", f"Initialized autoworkflow (force={force})")

        safe_print(f"\n{emoji('✅')} 初始化完成！")
        print(f"   共享层: {self.shared_dir}")
        print(f"   日志层: {self.logs_dir}")
        return 0

    def _init_logs_only(self) -> None:
        """Initialize only the Claude Code logs directory (mixed mode)."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Create .gitignore for logs
        gitignore = self.logs_dir / ".gitignore"
        safe_write_text(gitignore, "*\n!.gitignore\n", force=True)

    def _init_full(self, force: bool = False) -> None:
        """Full initialization of the autoworkflow directory."""
        timestamp = utc_now_iso()

        # Create directories
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)

        # Create spec template
        spec_content = DEFAULT_SPEC_TEMPLATE.format(
            tool_name=TOOL_NAME,
            timestamp=timestamp,
            build_cmd="",
            test_cmd="",
        )
        safe_write_text(self.shared_dir / "spec.md", spec_content, force=force)

        # Create state template
        state_content = DEFAULT_STATE_TEMPLATE.format(
            tool_name=TOOL_NAME,
            timestamp=timestamp,
            build_cmd="",
            test_cmd="",
        )
        safe_write_text(self.shared_dir / "state.md", state_content, force=force)

        # Create gate.env
        safe_write_text(self.shared_dir / "gate.env", DEFAULT_GATE_ENV, force=force)

        # Create model-policy.json
        safe_write_text(
            self.shared_dir / "model-policy.json",
            json.dumps(DEFAULT_MODEL_POLICY, indent=2, ensure_ascii=False),
            force=force
        )

        # Create agent-config.json
        safe_write_text(
            self.shared_dir / "agent-config.json",
            json.dumps(DEFAULT_AGENT_CONFIG, indent=2, ensure_ascii=False),
            force=force
        )

        # Create .gitignore
        gitignore_content = """\
# Autoworkflow local files (do not commit)
state.md
doctor.md
.owner
logs/
history/
"""
        safe_write_text(self.shared_dir / ".gitignore", gitignore_content, force=force)

        # Copy this script to tools/
        script_path = Path(__file__).resolve()
        dest_script = self.tools_dir / "claude_autoworkflow.py"
        if not dest_script.exists() or force:
            shutil.copy2(script_path, dest_script)

        # Copy wrapper scripts from templates
        template_dir = script_path.parent.parent / "assets" / "templates" / "tools"
        if template_dir.exists():
            for wrapper in ["cc-aw.ps1", "cc-aw.sh"]:
                src_wrapper = template_dir / wrapper
                dest_wrapper = self.tools_dir / wrapper
                if src_wrapper.exists() and (not dest_wrapper.exists() or force):
                    shutil.copy2(src_wrapper, dest_wrapper)
                    # Make shell script executable on Unix
                    if wrapper.endswith(".sh") and sys.platform != "win32":
                        dest_wrapper.chmod(0o755)

    def cmd_doctor(self, write: bool = False, update_state: bool = False) -> int:
        """Run project diagnosis."""
        self.update_activity()
        host_info = get_host_info()
        markers = detect_project_markers(self.root)

        # Check autoworkflow status
        aw_exists = self.shared_dir.exists()
        gate_env = self._parse_gate_env()
        gate_configured = bool(gate_env.get("TEST_CMD"))

        # Collect issues and recommendations
        issues = []
        recommendations = []

        if not aw_exists:
            issues.append("Autoworkflow not initialized")
            recommendations.append("Run: python claude_autoworkflow.py init")

        if not gate_configured:
            issues.append("Gate not configured (TEST_CMD missing)")
            recommendations.append("Run: python claude_autoworkflow.py set-gate --test \"your test cmd\"")

        if not markers:
            issues.append("No project markers detected")
            recommendations.append("Ensure you're in a valid project directory")

        result = DoctorResult(
            timestamp=utc_now_iso(),
            host_info=host_info,
            markers=markers,
            autoworkflow_exists=aw_exists,
            gate_configured=gate_configured,
            gate_env=gate_env,
            issues=issues,
            recommendations=recommendations,
        )

        # Generate report
        report = self._generate_doctor_report(result)
        safe_print(report)

        if write:
            doctor_file = self.shared_dir / "doctor.md"
            doctor_file.write_text(report, encoding="utf-8")
            safe_print(f"\n{emoji('📝')} 报告已写入: {doctor_file}")

        if update_state:
            self._append_to_state(f"\n## Doctor ({result.timestamp})\n- Issues: {len(issues)}\n- Markers: {', '.join(markers[:5])}\n")

        self.log_event("doctor", f"Doctor completed: {len(issues)} issues", {"markers": markers})
        self.log_operation("doctor", {"issues": issues, "markers": markers})

        return 0 if not issues else 1

    def _generate_doctor_report(self, result: DoctorResult) -> str:
        """Generate a doctor report in Markdown format."""
        report = f"""\
# Autoworkflow Doctor Report

<!-- source: {TOOL_NAME} -->
<!-- timestamp: {result.timestamp} -->

## Host Info
- OS: {result.host_info.os_name}
- Platform: {result.host_info.platform_name}
- Python: {result.host_info.python_version}
- WSL: {'yes' if result.host_info.is_wsl else 'no'}

## Project Markers
{chr(10).join(f'- {m}' for m in result.markers) if result.markers else '- (none detected)'}

## Autoworkflow Status
- Initialized: {'yes' if result.autoworkflow_exists else 'no'}
- Gate configured: {'yes' if result.gate_configured else 'no'}

## Gate Config
{chr(10).join(f'- {k}: `{v}`' for k, v in result.gate_env.items()) if result.gate_env else '- (not configured)'}

## Issues
{chr(10).join(f'- ⚠️ {i}' for i in result.issues) if result.issues else '- ✅ No issues found'}

## Recommendations
{chr(10).join(f'- {r}' for r in result.recommendations) if result.recommendations else '- (none)'}
"""
        return report

    def cmd_set_gate(self, build: str | None, test: str | None,
                     lint: str | None, format_check: str | None,
                     create: bool = False) -> int:
        """Set gate configuration."""
        self.update_activity()
        gate_env_file = self.shared_dir / "gate.env"

        if not gate_env_file.exists() and not create:
            safe_print(f"{emoji('❌')} gate.env 不存在，使用 --create 创建")
            return 1

        # Parse existing
        current = self._parse_gate_env()

        # Update with new values
        if build is not None:
            current["BUILD_CMD"] = build
        if test is not None:
            current["TEST_CMD"] = test
        if lint is not None:
            current["LINT_CMD"] = lint
        if format_check is not None:
            current["FORMAT_CHECK_CMD"] = format_check

        # Write back
        lines = []
        for key in ["BUILD_CMD", "TEST_CMD", "LINT_CMD", "FORMAT_CHECK_CMD"]:
            if key in current and current[key]:
                lines.append(f"{key}={current[key]}")

        gate_env_file.parent.mkdir(parents=True, exist_ok=True)
        gate_env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        safe_print(f"{emoji('✅')} Gate 配置已更新:")
        for line in lines:
            print(f"   {line}")

        self.log_event("set_gate", "Gate config updated", current)
        return 0

    def cmd_gate(self) -> int:
        """Execute gate verification."""
        self.update_activity()
        gate_env = self._parse_gate_env()

        if not gate_env.get("TEST_CMD"):
            safe_print(f"{emoji('❌')} Gate 未配置 (TEST_CMD 缺失)")
            print("   运行: python claude_autoworkflow.py set-gate --test \"your test cmd\"")
            return 1

        host_info = get_host_info()
        steps = [
            ("Build", gate_env.get("BUILD_CMD")),
            ("Test", gate_env.get("TEST_CMD")),
            ("Lint", gate_env.get("LINT_CMD")),
            ("FormatCheck", gate_env.get("FORMAT_CHECK_CMD")),
        ]

        safe_print(f"{emoji('🚀')} 开始 Gate 验证...\n")
        all_passed = True
        all_output = []

        for step_name, cmd in steps:
            if not cmd:
                continue

            print(f"==> {step_name}: {cmd}")
            exit_code, output = self._run_command(cmd)
            all_output.append(f"=== {step_name} ===\n{output}")

            if exit_code != 0:
                safe_print(f"{emoji('❌')} {step_name} 失败 (exit {exit_code})")
                all_passed = False
                break
            else:
                safe_print(f"{emoji('✅')} {step_name} 通过\n")

        # Generate result
        combined_output = "\n\n".join(all_output)
        highlights = extract_highlights(combined_output) if not all_passed else []

        result = GateResult(
            status="PASS" if all_passed else "FAIL",
            exit_code=0 if all_passed else 1,
            timestamp=utc_now_iso(),
            command="gate",
            output=redact_secrets(combined_output),
            highlights=highlights,
        )

        # Append to state
        self._append_gate_to_state(result)

        # Log
        self.log_event("gate", f"Gate {'PASS' if all_passed else 'FAIL'}", {
            "exit_code": result.exit_code,
            "highlights": highlights[:5],
        })
        self.log_operation("gate", {
            "status": result.status,
            "exit_code": result.exit_code,
        })

        if all_passed:
            safe_print(f"\n{emoji('🎉')} Gate 通过！所有检查全绿！")
        else:
            safe_print(f"\n{emoji('❌')} Gate 失败")
            if highlights:
                print("\n关键错误行:")
                for h in highlights[:10]:
                    print(f"  - {h}")

        return 0 if all_passed else 1

    def cmd_recommend_model(self, intent: str) -> int:
        """Recommend a model based on intent and project state."""
        self.update_activity()

        # Load policy
        policy_file = self.shared_dir / "model-policy.json"
        if policy_file.exists():
            policy = json.loads(policy_file.read_text(encoding="utf-8"))
        else:
            policy = DEFAULT_MODEL_POLICY

        # Detect signals
        signals = set()
        gate_env = self._parse_gate_env()

        if not gate_env.get("TEST_CMD"):
            signals.add("no_gate_configured")

        # Check last gate result
        state_file = self.shared_dir / "state.md"
        if state_file.exists():
            state_content = state_file.read_text(encoding="utf-8")
            if "Result: FAIL" in state_content or "Gate 失败" in state_content:
                signals.add("gate_failed")

        if intent in ("doctor", "init"):
            signals.add("doctor_only")

        # Determine profile
        profile = policy.get("intents", {}).get(intent, "medium")

        # Override by rules
        for rule in policy.get("rules", []):
            if rule.get("if") in signals:
                profile = rule.get("then", profile)
                reason = rule.get("reason", "Rule matched")
                break
        else:
            reason = f"Intent-based recommendation for '{intent}'"

        # Get model names
        profiles = policy.get("profiles", {})
        model_info = profiles.get(profile, {"claude": "sonnet", "codex": "gpt-4o"})

        safe_print(f"{emoji('🤖')} 模型推荐 (intent: {intent})")
        print(f"   Profile: {profile}")
        print(f"   Claude: {model_info.get('claude', 'sonnet')}")
        print(f"   Codex: {model_info.get('codex', 'gpt-4o')}")
        print(f"   Reason: {reason}")

        if signals:
            print(f"   Signals: {', '.join(signals)}")

        self.log_event("recommend_model", f"Recommended {profile}", {
            "intent": intent,
            "profile": profile,
            "signals": list(signals),
        })

        return 0

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _parse_gate_env(self) -> dict[str, str]:
        """Parse gate.env file."""
        gate_env_file = self.shared_dir / "gate.env"
        result = {}

        if not gate_env_file.exists():
            return result

        for line in gate_env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if key in ALLOWED_ENV_KEYS:
                    result[key] = value

        return result

    def _run_command(self, cmd: str, timeout: int = 1800) -> tuple[int, str]:
        """Run a shell command and return (exit_code, output).

        Args:
            cmd: Shell command to execute
            timeout: Timeout in seconds (default: 30 min)

        Returns:
            (exit_code, output_text)
        """
        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                cwd=str(self.root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            output_lines = []
            try:
                # Use communicate with timeout for safety
                stdout, _ = proc.communicate(timeout=timeout)
                output_lines = stdout.splitlines(keepends=True)
                for line in output_lines:
                    print(line, end="")
            except subprocess.TimeoutExpired:
                # Kill process after timeout
                proc.kill()
                try:
                    proc.communicate(timeout=5)  # Give it 5 sec to die
                except subprocess.TimeoutExpired:
                    proc.kill()
                error_msg = f"Command timed out after {timeout}s: {cmd}"
                safe_print(f"{emoji('❌')} {error_msg}")
                return 1, error_msg

            return proc.returncode, "".join(output_lines)
        except Exception as e:
            return 1, str(e)

    def _append_to_state(self, section: str) -> None:
        """Append a section to state.md with source identifier."""
        state_file = self.shared_dir / "state.md"

        header = f"<!-- source: {TOOL_NAME} -->\n"
        header += f"<!-- timestamp: {utc_now_iso()} -->\n"

        if state_file.exists():
            with state_file.open("a", encoding="utf-8") as f:
                f.write(f"\n{header}{section}")
        else:
            with state_file.open("w", encoding="utf-8") as f:
                f.write(f"{header}{section}")

    def _append_gate_to_state(self, result: GateResult) -> None:
        """Append gate result to state.md."""
        section = f"""\
## Gate ({result.timestamp})
- Status: {result.status}
- Exit Code: {result.exit_code}
"""

        if result.highlights:
            section += "\n### Highlights\n"
            for h in result.highlights[:15]:
                section += f"- {h}\n"

        # Add tail if failed
        if result.status == "FAIL":
            tail_lines = result.output.splitlines()[-40:]
            section += "\n### Tail (last 40 lines)\n```\n"
            section += "\n".join(tail_lines)
            section += "\n```\n"

        self._append_to_state(section)


# ============================================================================
# CLI
# ============================================================================

def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Claude Code Autoworkflow - 自动化工具链",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--root", "-r",
        type=Path,
        default=Path.cwd(),
        help="项目根目录 (默认: 当前目录)",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"Claude Code Autoworkflow v{TOOL_VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # init
    init_parser = subparsers.add_parser("init", help="初始化工具链")
    init_parser.add_argument("--force", "-f", action="store_true", help="强制覆盖")

    # doctor
    doctor_parser = subparsers.add_parser("doctor", help="项目诊断")
    doctor_parser.add_argument("--write", "-w", action="store_true", help="写入 doctor.md")
    doctor_parser.add_argument("--update-state", "-u", action="store_true", help="更新 state.md")

    # set-gate
    gate_parser = subparsers.add_parser("set-gate", help="配置 Gate")
    gate_parser.add_argument("--build", "-b", help="构建命令")
    gate_parser.add_argument("--test", "-t", help="测试命令")
    gate_parser.add_argument("--lint", "-l", help="Lint 命令")
    gate_parser.add_argument("--format-check", "-f", help="格式检查命令")
    gate_parser.add_argument("--create", "-c", action="store_true", help="创建 gate.env")

    # gate
    subparsers.add_parser("gate", help="执行 Gate 验证")

    # recommend-model
    model_parser = subparsers.add_parser("recommend-model", help="智能模型推荐")
    model_parser.add_argument(
        "--intent", "-i",
        choices=["doctor", "init", "implement", "debug", "refactor"],
        default="implement",
        help="任务意图",
    )

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    aw = ClaudeAutoworkflow(args.root)

    if args.command == "init":
        return aw.cmd_init(force=args.force)
    elif args.command == "doctor":
        return aw.cmd_doctor(write=args.write, update_state=args.update_state)
    elif args.command == "set-gate":
        return aw.cmd_set_gate(
            build=args.build,
            test=args.test,
            lint=args.lint,
            format_check=args.format_check,
            create=args.create,
        )
    elif args.command == "gate":
        return aw.cmd_gate()
    elif args.command == "recommend-model":
        return aw.cmd_recommend_model(intent=args.intent)

    return 0


if __name__ == "__main__":
    sys.exit(main())
