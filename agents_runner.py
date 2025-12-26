"""
agents_runner.py
Official-style orchestrator using Codex MCP + Agents SDK patterns (lightweight stub).

Flows:
 1) Plan review (must approve) -> Gate (test-green) guarded in PM logic.
 2) Uses existing autoworkflow.py to keep repo-local gate/spec/plan flow.
 3) Emits trace-like JSONL under .autoworkflow/trace/.

Note: This is a minimal runner without full Agents SDK dependency
to stay self-contained. Replace stubs with official SDK classes when available.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

ROOT = Path(__file__).resolve().parent
AW = ROOT / "codex-skills" / "feature-shipper" / "scripts" / "autoworkflow.py"
TRACE_DIR = ROOT / ".autoworkflow" / "trace"


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
    aw = ensure_aw(repo)
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    log: List[Dict[str, Any]] = []
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    trace_path = TRACE_DIR / f"runner-trace-{ts}.jsonl"

    # Plan review (must approve unless allow_unreviewed)
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
    parser = argparse.ArgumentParser(description="Codex Agents runner (plan review + gate with guardrails)")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--allow-unreviewed", action="store_true", help="Skip plan review guard")
    args = parser.parse_args()
    repo = Path(args.root).resolve()
    return orchestrate(repo, allow_unreviewed=bool(args.allow_unreviewed))


if __name__ == "__main__":
    raise SystemExit(main())
