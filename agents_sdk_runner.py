"""
agents_sdk_runner.py
--------------------
Official-style Agents SDK runner using Codex MCP (stdio).

This runner:
 - starts Codex MCP server via stdio
 - defines minimal PM + Tester flow: plan review -> gate, guarded by plan approval unless --allow-unreviewed
 - reuses repo-local autoworkflow.py to keep gate/spec tooling
 - saves a trace JSONL to .autoworkflow/trace/

Requirements:
 - pip install openai
 - npx codex mcp-server available in PATH
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import openai
from openai import AsyncMCPClient, AsyncMCPClientTransport, MCPUMessageTransport


ROOT = Path(__file__).resolve().parent
AW = ROOT / "codex-skills" / "feature-shipper" / "scripts" / "autoworkflow.py"
TRACE_DIR = ROOT / ".autoworkflow" / "trace"


def ensure_aw(repo: Path) -> Path:
    tool = repo / ".autoworkflow" / "tools" / "autoworkflow.py"
    if tool.exists():
        return tool
    if AW.exists():
        return AW
    raise FileNotFoundError("autoworkflow.py not found; run autoworkflow init first.")


async def run_cmd(cmd: List[str], cwd: Path, title: str) -> Dict[str, Any]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        text=True,
    )
    out_lines: List[str] = []
    assert proc.stdout
    async for line in proc.stdout:
        sys.stdout.write(line)
        out_lines.append(line)
    code = await proc.wait()
    return {"step": title, "cmd": cmd, "exit": code, "output": "".join(out_lines)}


async def orchestrate(repo: Path, allow_unreviewed: bool) -> int:
    aw = ensure_aw(repo)
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    trace_path = TRACE_DIR / f"sdk-trace-{ts}.jsonl"

    log: List[Dict[str, Any]] = []

    # In a full SDK setup, we would issue tools via Agent messages. Here we invoke aw directly to keep compatibility.
    result = await run_cmd([sys.executable, str(aw), "--root", str(repo), "plan", "review"], repo, "plan review")
    log.append(result)
    if result["exit"] != 0 and not allow_unreviewed:
        trace_path.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in log), encoding="utf-8")
        print(f"[trace] {trace_path}")
        return result["exit"]

    gate_cmd = [sys.executable, str(aw), "--root", str(repo), "gate"]
    if allow_unreviewed:
        gate_cmd.append("--allow-unreviewed")
    result = await run_cmd(gate_cmd, repo, "gate")
    log.append(result)

    trace_path.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in log), encoding="utf-8")
    print(f"[trace] {trace_path}")
    return result["exit"]


async def start_mcp_server() -> AsyncMCPClient:
    # Start Codex MCP server via stdio transport
    transport = MCPUMessageTransport(
        command=["npx", "-y", "codex", "mcp-server"],
        env=os.environ.copy(),
    )
    client = AsyncMCPClient(transport=transport)
    await client.start()
    return client


async def async_main(args) -> int:
    # Start MCP (for alignment; not used directly yet)
    mcp_client = await start_mcp_server()
    try:
        rc = await orchestrate(repo=Path(args.root).resolve(), allow_unreviewed=bool(args.allow_unreviewed))
    finally:
        await mcp_client.close()
    return rc


def main() -> int:
    parser = argparse.ArgumentParser(description="Agents SDK runner with Codex MCP (plan review + gate)")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--allow-unreviewed", action="store_true", help="Skip plan review guard")
    args = parser.parse_args()
    return asyncio.run(async_main(args))


if __name__ == "__main__":
    raise SystemExit(main())
