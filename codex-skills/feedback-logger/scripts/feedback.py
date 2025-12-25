from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass


DEFAULT_WATCH_FILES = (
    ".autoworkflow/state.md",
    ".autoworkflow/doctor.md",
    ".autoworkflow/gate.env",
)


DEFAULT_FB_PS1 = """$ErrorActionPreference = "Stop"

$toolDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $toolDir "feedback.py"

if (-not (Test-Path -LiteralPath $script)) {
  throw "Missing $script (run feedback init first)."
}

python $script @args
"""


DEFAULT_FB_SH = """#!/usr/bin/env bash
set -euo pipefail

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="${TOOL_DIR}/feedback.py"

if [[ ! -f "${SCRIPT}" ]]; then
  echo "Missing ${SCRIPT} (run feedback init first)." >&2
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


@dataclass(frozen=True)
class Event:
    ts: str
    kind: str
    message: str
    tags: list[str]
    data: dict


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def repo_root(path: str) -> Path:
    return Path(path).resolve()


def autoworkflow_dir(root: Path) -> Path:
    return root / ".autoworkflow"


def tools_dir(root: Path) -> Path:
    return autoworkflow_dir(root) / "tools"


def logs_dir(root: Path) -> Path:
    return autoworkflow_dir(root) / "logs" / "codex"


def log_path(root: Path) -> Path:
    return logs_dir(root) / "feedback.jsonl"


def pid_path(root: Path) -> Path:
    return logs_dir(root) / "feedback-watch.pid"


def safe_write_text(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line)
        if not line.endswith("\n"):
            f.write("\n")


def redact(text: str) -> str:
    # Keep it conservative: redact obvious "KEY=..." patterns and JWT-like tokens.
    patterns = [
        r"(?i)\b(password|passwd|token|secret|api[_-]?key|access[_-]?key)\b\s*[:=]\s*([^\s\"']+)",
        r"(?i)\b(bearer)\s+([a-z0-9\-\._~\+/]+=*)",
        r"\beyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\b",
    ]
    out = text
    for pat in patterns:
        rx = re.compile(pat)

        def _repl(m: re.Match) -> str:
            if m.lastindex and m.lastindex >= 2:
                return m.group(0).replace(m.group(m.lastindex), "***REDACTED***")
            return "***REDACTED***"

        out = rx.sub(_repl, out)
    return out


def extract_highlights_and_tail(output: str, max_tail_lines: int = 60, max_highlight_lines: int = 25) -> dict:
    output = redact(output)
    lines = output.splitlines()
    tail = lines[-max_tail_lines:] if len(lines) > max_tail_lines else lines

    patterns = [
        r"\berror\b",
        r"\bfatal\b",
        r"\bfailed\b",
        r"\bexception\b",
        r"\btraceback\b",
        r"\bassert\b",
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
            highlights.append(key)
            if len(highlights) >= max_highlight_lines:
                break
    return {"highlights": highlights, "tail": tail}


def write_event(root: Path, event: Event) -> None:
    path = log_path(root)
    append_line(path, json.dumps(event.__dict__, ensure_ascii=False))


def init(root: Path, force: bool) -> None:
    aw = autoworkflow_dir(root)
    td = tools_dir(root)
    ld = logs_dir(root)

    td.mkdir(parents=True, exist_ok=True)
    ld.mkdir(parents=True, exist_ok=True)

    # Copy this script into the repo so any host (Claude/Codex/terminal) can call it.
    src = Path(__file__).resolve()
    dst = td / "feedback.py"
    if force or not dst.exists():
        shutil.copyfile(src, dst)

    safe_write_text(td / "fb.ps1", DEFAULT_FB_PS1, force=force)
    safe_write_text(td / "fb.sh", DEFAULT_FB_SH, force=force)

    # Make sure logs file exists (valid JSONL: no leading blank line).
    lp = log_path(root)
    if force or not lp.exists():
        safe_write_text(lp, "", force=True)

    # Ensure .autoworkflow/.gitignore ignores logs/pid by default (without touching parent repo ignores).
    gitignore_path = aw / ".gitignore"
    existing = gitignore_path.read_text(encoding="utf-8", errors="replace") if gitignore_path.exists() else ""
    needed = ["logs/", "logs/codex/", "logs/codex/feedback.jsonl", "logs/codex/feedback-watch.pid"]
    lines = [ln.rstrip("\n") for ln in existing.splitlines()] if existing else []
    for entry in needed:
        if entry not in lines:
            lines.append(entry)
    safe_write_text(gitignore_path, "\n".join(lines).strip() + "\n", force=True)

    write_event(
        root,
        Event(
            ts=utc_now(),
            kind="init",
            message="feedback logger initialized",
            tags=["init"],
            data={"tools": [".autoworkflow/tools/feedback.py", ".autoworkflow/tools/fb.ps1", ".autoworkflow/tools/fb.sh"]},
        ),
    )


def run_and_capture(cmd: list[str], cwd: Path) -> tuple[int, str]:
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
        try:
            sys.stdout.write(line)
            sys.stdout.flush()
        except UnicodeEncodeError:
            enc = getattr(sys.stdout, "encoding", None) or "utf-8"
            if getattr(sys.stdout, "buffer", None) is not None:
                sys.stdout.buffer.write(line.encode(enc, errors="replace"))
                sys.stdout.buffer.flush()
        out_lines.append(line)
    proc.wait()
    return int(proc.returncode), "".join(out_lines)


def cmd_log(root: Path, message: str, tag: list[str], kind: str) -> None:
    write_event(root, Event(ts=utc_now(), kind=kind, message=message, tags=tag, data={}))


def cmd_wrap(root: Path, cmd: list[str], tag: list[str]) -> int:
    started = utc_now()
    write_event(root, Event(ts=started, kind="wrap_start", message="command start", tags=tag, data={"cmd": cmd}))
    code, output = run_and_capture(cmd, cwd=root)
    ended = utc_now()
    summary = extract_highlights_and_tail(output)
    write_event(
        root,
        Event(
            ts=ended,
            kind="wrap_end",
            message="command end",
            tags=tag,
            data={"cmd": cmd, "exit": code, **summary},
        ),
    )
    return code


def read_pid(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def is_process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if os.name == "nt":
            # Best-effort: tasklist will return non-empty when pid exists.
            proc = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
            return str(pid) in proc.stdout
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def cmd_watch(root: Path, files: list[str], interval: float, once: bool) -> int:
    tracked: dict[Path, tuple[float, int]] = {}
    targets = [root / f for f in files]
    for p in targets:
        try:
            st = p.stat()
            tracked[p] = (st.st_mtime, st.st_size)
        except FileNotFoundError:
            tracked[p] = (0.0, 0)

    write_event(
        root,
        Event(
            ts=utc_now(),
            kind="watch_start",
            message="watch started",
            tags=["watch"],
            data={"files": files, "interval": interval},
        ),
    )

    def on_change(path: Path) -> None:
        tail: list[str] = []
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            tail = content.splitlines()[-40:]
        except Exception:
            tail = []
        write_event(
            root,
            Event(
                ts=utc_now(),
                kind="file_change",
                message=f"changed: {path.as_posix()}",
                tags=["watch"],
                data={"file": str(path), "tail": tail},
            ),
        )

    while True:
        changed_any = False
        for p in targets:
            old_mtime, old_size = tracked.get(p, (0.0, 0))
            try:
                st = p.stat()
                new = (st.st_mtime, st.st_size)
            except FileNotFoundError:
                new = (0.0, 0)
            if new != (old_mtime, old_size):
                tracked[p] = new
                on_change(p)
                changed_any = True
        if once:
            return 0
        time.sleep(interval)


def cmd_start(root: Path, files: list[str], interval: float) -> int:
    pp = pid_path(root)
    existing = read_pid(pp)
    if existing and is_process_alive(existing):
        print(f"watch already running (pid {existing})")
        return 0

    args = [sys.executable, str((tools_dir(root) / "feedback.py").resolve()), "--root", str(root), "watch"]
    for f in files:
        args += ["--file", f]
    args += ["--interval", str(interval)]

    if os.name == "nt":
        creationflags = 0
        if hasattr(subprocess, "DETACHED_PROCESS"):
            creationflags |= subprocess.DETACHED_PROCESS
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP
        proc = subprocess.Popen(
            args,
            cwd=str(root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=True,
        )
    else:
        proc = subprocess.Popen(
            args,
            cwd=str(root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )

    pp.parent.mkdir(parents=True, exist_ok=True)
    pp.write_text(str(proc.pid), encoding="utf-8", newline="\n")
    write_event(root, Event(ts=utc_now(), kind="watch_daemon_start", message="watch daemon started", tags=["watch"], data={"pid": proc.pid}))
    print(f"started watch (pid {proc.pid})")
    return 0


def cmd_stop(root: Path) -> int:
    pp = pid_path(root)
    pid = read_pid(pp)
    if not pid:
        print("no pid file")
        return 0
    if not is_process_alive(pid):
        pp.unlink(missing_ok=True)  # type: ignore[arg-type]
        print(f"stale pid {pid} removed")
        return 0
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
        else:
            os.kill(pid, 15)
        print(f"stopped watch (pid {pid})")
        write_event(root, Event(ts=utc_now(), kind="watch_daemon_stop", message="watch daemon stopped", tags=["watch"], data={"pid": pid}))
    except Exception as e:
        print(f"failed to stop pid {pid}: {e}")
        return 1
    finally:
        try:
            pp.unlink()
        except Exception:
            pass
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="feedback")
    parser.add_argument("--root", default=".", help="Target repo root (default: current directory)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize feedback logger under .autoworkflow/")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing files")

    p_log = sub.add_parser("log", help="Append a manual note to feedback log")
    p_log.add_argument("--message", required=True, help="Message to log")
    p_log.add_argument("--tag", action="append", default=[], help="Tag (repeatable)")
    p_log.add_argument("--kind", default="note", help="Event kind (default: note)")

    p_wrap = sub.add_parser("wrap", help="Run a command and log highlights/tail")
    p_wrap.add_argument("--tag", action="append", default=[], help="Tag (repeatable)")
    p_wrap.add_argument("rest", nargs=argparse.REMAINDER, help="Command after --")

    p_watch = sub.add_parser("watch", help="Watch .autoworkflow files and log changes")
    p_watch.add_argument("--file", action="append", default=[], help="Path to watch (repeatable)")
    p_watch.add_argument("--interval", type=float, default=1.0, help="Polling interval seconds")
    p_watch.add_argument("--once", action="store_true", help="Run one scan and exit")

    p_start = sub.add_parser("start", help="Start background watch")
    p_start.add_argument("--file", action="append", default=[], help="Path to watch (repeatable)")
    p_start.add_argument("--interval", type=float, default=1.0, help="Polling interval seconds")

    sub.add_parser("stop", help="Stop background watch (best-effort)")

    args = parser.parse_args(argv)
    root = repo_root(args.root)

    if args.cmd == "init":
        init(root, force=bool(args.force))
        print(f"initialized: {autoworkflow_dir(root)}")
        return 0

    if args.cmd == "log":
        cmd_log(root, message=args.message, tag=list(args.tag), kind=str(args.kind))
        return 0

    if args.cmd == "wrap":
        rest = list(args.rest)
        if rest[:1] == ["--"]:
            rest = rest[1:]
        if not rest:
            print("missing command (use: wrap -- <cmd...>)", file=sys.stderr)
            return 2
        return cmd_wrap(root, cmd=rest, tag=list(args.tag))

    if args.cmd == "watch":
        files = args.file if args.file else list(DEFAULT_WATCH_FILES)
        return cmd_watch(root, files=files, interval=float(args.interval), once=bool(args.once))

    if args.cmd == "start":
        files = args.file if args.file else list(DEFAULT_WATCH_FILES)
        return cmd_start(root, files=files, interval=float(args.interval))

    if args.cmd == "stop":
        return cmd_stop(root)

    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
