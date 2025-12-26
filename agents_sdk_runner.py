"""
agents_sdk_runner.py
--------------------
Targets the official Agents SDK + Codex MCP server pattern.

Behavior:
- Attempt to import `openai` Agents SDK. If unavailable, print guidance and exit non-zero.
- Start Codex MCP server via stdio (npx codex mcp-server).
- Define a minimal multi-agent plan:
  PM -> (plan review) -> Tester(gate) with guard that plan must be approved unless --allow-unreviewed.
- Persist a trace-like JSONL to .autoworkflow/trace/.

This file is a stepping stone: replace stubs with actual Agents SDK `Runner`, `Agent` definitions
when SDK is available in the environment.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

ROOT = Path(__file__).resolve().parent
AW = ROOT / "codex-skills" / "feature-shipper" / "scripts" / "autoworkflow.py"
TRACE_DIR = ROOT / ".autoworkflow" / "trace"


def ensure_sdk() -> None:
    try:
        import openai  # noqa: F401
    except Exception:
        print("[agents-sdk-runner] OpenAI Agents SDK 未安装。请运行：pip install openai", file=sys.stderr)
        sys.exit(2)


def run(cmd: List[str], cwd: Path, title: str) -> Dict[str, Any]:
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    out_lines: List[str] = []
    assert proc.stdout
    for line in proc.stdout:
        sys.stdout.write(line)
        out_lines.append(line)
    proc.wait()
    return {"step": title, "cmd": cmd, "exit": proc.returncode, "output": "".join(out_lines)}


def ensure_aw(repo: Path) -> Path:
    tool = repo / ".autoworkflow" / "tools" / "autoworkflow.py"
    if tool.exists():
        return tool
    if AW.exists():
        return AW
    raise FileNotFoundError("autoworkflow.py not found; run autoworkflow init first.")


def orchestrate(repo: Path, allow_unreviewed: bool) -> int:
    ensure_sdk()
    # Note: Here we would wire the official Runner with MCP. For now we reuse aw tools to enforce guards.
    aw = ensure_aw(repo)
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    log: List[Dict[str, Any]] = []
    ts = datetime.utcnow().isoformat()
    trace_path = TRACE_DIR / f"sdk-trace-{ts}.jsonl"

    result = run([sys.executable, str(aw), "--root", str(repo), "plan", "review"], repo, "plan review")
    log.append(result)
    if result["exit"] != 0 and not allow_unreviewed:
        with trace_path.open("w", encoding="utf-8") as f:
            for item in log:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"[trace] {trace_path}")
        return result["exit"]

    gate_cmd = [sys.executable, str(aw), "--root", str(repo), "gate"]
    if allow_unreviewed:
        gate_cmd.append("--allow-unreviewed")
    result = run(gate_cmd, repo, "gate")
    log.append(result)

    with trace_path.open("w", encoding="utf-8") as f:
        for item in log:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[trace] {trace_path}")
    return result["exit"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Agents SDK runner (placeholder until official Runner wired)")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--allow-unreviewed", action="store_true", help="Skip plan review guard")
    args = parser.parse_args()
    repo = Path(args.root).resolve()
    return orchestrate(repo, allow_unreviewed=bool(args.allow_unreviewed))


if __name__ == "__main__":
    raise SystemExit(main())
