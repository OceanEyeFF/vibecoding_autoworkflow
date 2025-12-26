"""
agents_workflow.py
-------------------
Minimal orchestrator aligned with OpenAI Codex Agents SDK guidance.

Responsibilities
 - Start Codex MCP server (stdio) when not running.
 - Run a simple PM → plan review → gate sequence (reuse autoworkflow.py tools).
 - Produce a trace-like log file for CI/debugging.

Note: This is a lightweight shell orchestrator to keep the repo self-contained.
Replace with the official Agents SDK Runner when available in your environment.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AW = ROOT / "codex-skills" / "feature-shipper" / "scripts" / "autoworkflow.py"


def run(cmd: list[str], cwd: Path, title: str) -> tuple[int, str]:
    proc = subprocess.Popen(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out_lines: list[str] = []
    assert proc.stdout
    for line in proc.stdout:
        sys.stdout.write(line)
        out_lines.append(line)
    proc.wait()
    return proc.returncode, "".join(out_lines)


def ensure_aw_exists(repo: Path) -> Path:
    tool = repo / ".autoworkflow" / "tools" / "autoworkflow.py"
    if tool.exists():
        return tool
    if AW.exists():
        return AW
    raise FileNotFoundError("autoworkflow.py not found; run init first.")


def orchestrate(repo: Path, allow_unreviewed: bool) -> int:
    aw = ensure_aw_exists(repo)
    log: list[dict] = []
    trace_dir = repo / ".autoworkflow" / "trace"
    trace_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    trace_path = trace_dir / f"trace-{ts}.jsonl"

    def step(name: str, cmd: list[str]) -> int:
        code, out = run(cmd, cwd=repo, title=name)
        log.append({"step": name, "cmd": cmd, "exit": code, "output": out})
        return code

    # plan review
    code = step("plan review", [sys.executable, str(aw), "--root", str(repo), "plan", "review"])
    if code != 0:
        pass  # still proceed; gate guard will block unless allow_unreviewed

    gate_cmd = [
        sys.executable,
        str(aw),
        "--root",
        str(repo),
        "gate",
    ]
    if allow_unreviewed:
        gate_cmd.append("--allow-unreviewed")

    code = step("gate", gate_cmd)

    with trace_path.open("w", encoding="utf-8") as f:
        for item in log:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[trace] {trace_path}")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description="Orchestrate plan review + gate with Codex autoworkflow tools")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--allow-unreviewed", action="store_true", help="Skip plan guard")
    args = parser.parse_args()
    repo = Path(args.root).resolve()
    return orchestrate(repo, allow_unreviewed=bool(args.allow_unreviewed))


if __name__ == "__main__":
    raise SystemExit(main())
