"""
agents_sdk_runner.py
--------------------
基于 OpenAI Agents SDK + Codex MCP (stdio) 的官方样例风格 Runner。

目标（本仓库“功能等价”口径）：
- MCP server 可启动（并可用于 Codex 工具调用）
- 多 Agent handoff（Manager -> Executor）
- 复用 repo-local autoworkflow（plan review -> gate）作为验收闭环
- 产出可审计 trace：.autoworkflow/trace/*.jsonl

依赖（按官方文档）：
- pip install --upgrade openai openai-agents python-dotenv
- npx -y codex mcp-server 可用
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
AW = ROOT / "codex-skills" / "feature-shipper" / "scripts" / "autoworkflow.py"


@dataclass(frozen=True)
class RunnerConfig:
    repo: Path
    allow_unreviewed: bool
    approval_policy: str
    sandbox: str
    mode: str
    model: str
    max_turns: int


def _import_agents_sdk() -> tuple[Any, Any, Any, Any, str]:
    try:
        from agents import Agent, Runner, set_default_openai_api  # type: ignore
        from agents.mcp import MCPServerStdio  # type: ignore

        try:
            from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX  # type: ignore

            handoff_prefix = str(RECOMMENDED_PROMPT_PREFIX)
        except Exception:
            handoff_prefix = ""

        return Agent, Runner, set_default_openai_api, MCPServerStdio, handoff_prefix
    except Exception as exc:  # pragma: no cover
        msg = "\n".join(
            [
                "缺少 Agents SDK 依赖，无法运行 agents_sdk_runner.py。",
                "请先安装（官方文档）：",
                "  python -m pip install --upgrade openai openai-agents python-dotenv",
                f"原始错误: {exc}",
            ]
        )
        raise RuntimeError(msg) from exc


def ensure_aw(repo: Path) -> Path:
    tool = repo / ".autoworkflow" / "tools" / "autoworkflow.py"
    if tool.exists():
        return tool
    if AW.exists():
        return AW
    raise FileNotFoundError("autoworkflow.py not found; run autoworkflow init first.")


async def run_cmd(cmd: list[str], cwd: Path, title: str) -> dict[str, Any]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    out_lines: list[str] = []
    assert proc.stdout
    async for chunk in proc.stdout:
        line = chunk.decode(errors="replace")
        sys.stdout.write(line)
        out_lines.append(line)
    code = await proc.wait()
    return {"step": title, "cmd": cmd, "exit": code, "output": "".join(out_lines)}


def _new_trace_path(repo: Path) -> Path:
    trace_dir = repo / ".autoworkflow" / "trace"
    trace_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return trace_dir / f"sdk-trace-{ts}.jsonl"


async def orchestrate_local(cfg: RunnerConfig) -> int:
    aw = ensure_aw(cfg.repo)
    trace_path = _new_trace_path(cfg.repo)
    log: list[dict[str, Any]] = []

    result = await run_cmd([sys.executable, str(aw), "--root", str(cfg.repo), "plan", "review"], cfg.repo, "plan review")
    log.append(result)
    if result["exit"] != 0 and not cfg.allow_unreviewed:
        trace_path.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in log), encoding="utf-8")
        print(f"[trace] {trace_path}")
        return result["exit"]

    gate_cmd = [sys.executable, str(aw), "--root", str(cfg.repo), "gate"]
    if cfg.allow_unreviewed:
        gate_cmd.append("--allow-unreviewed")
    result = await run_cmd(gate_cmd, cfg.repo, "gate")
    log.append(result)

    trace_path.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in log), encoding="utf-8")
    print(f"[trace] {trace_path}")
    return result["exit"]


async def orchestrate_sdk(cfg: RunnerConfig) -> int:
    Agent, Runner, set_default_openai_api, MCPServerStdio, handoff_prefix = _import_agents_sdk()

    # optional .env support (keep non-fatal)
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(override=True)
    except Exception:
        pass

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("缺少环境变量 OPENAI_API_KEY，无法运行 --mode sdk（需要可用的 API Key）。")
    set_default_openai_api(api_key)

    trace_path = _new_trace_path(cfg.repo)
    log: list[dict[str, Any]] = []

    # 1) Start MCP server (stdio)
    async with MCPServerStdio(
        name="Codex CLI",
        params={
            "command": "npx",
            "args": ["-y", "codex", "mcp-server"],
        },
        client_session_timeout_seconds=360000,
    ) as codex_mcp_server:
        log.append({"step": "mcp start", "cmd": ["npx", "-y", "codex", "mcp-server"], "exit": 0})

        # 2) Multi-agent handoff (Manager -> Executor)
        handoff_line = handoff_prefix.strip()
        executor_instructions = [
            "你是一个执行型工程助手，只做两件事：plan review -> gate。",
            "你必须通过 MCP 工具 `codex` 来运行命令，不要直接假设命令结果。",
            "当调用 `codex` 工具时，务必显式传入：",
            f'- "approval-policy": "{cfg.approval_policy}"',
            f'- "sandbox": "{cfg.sandbox}"',
            f'- "cwd": "{str(cfg.repo)}"',
            "运行的命令为：",
            "1) python .autoworkflow/tools/autoworkflow.py --root . plan review",
            "2) python .autoworkflow/tools/autoworkflow.py --root . gate (若允许跳过审查则加 --allow-unreviewed)",
            "除非明确被要求，否则不要编辑任何文件。",
        ]
        if handoff_line:
            executor_instructions.insert(0, handoff_line)

        executor = Agent(
            name="Workflow Executor",
            instructions="\n".join(executor_instructions),
            model=cfg.model,
            mcp_servers=[codex_mcp_server],
        )

        manager_instructions = [
            "你负责把任务交接给执行者。",
            "输出一段非常短的执行指令（不超过 8 行），然后 handoff 给 Workflow Executor。",
            "不要自己调用 codex 工具。",
        ]
        if handoff_line:
            manager_instructions.insert(0, handoff_line)

        manager = Agent(
            name="Workflow Manager",
            instructions="\n".join(manager_instructions),
            model=cfg.model,
            handoffs=[executor],
        )

        allow_flag = " --allow-unreviewed" if cfg.allow_unreviewed else ""
        prompt = "\n".join(
            [
                "在目标仓库内跑通 plan review -> gate，并把关键输出原样返回。",
                f"仓库路径: {cfg.repo}",
                "命令：",
                "  python .autoworkflow/tools/autoworkflow.py --root . plan review",
                f"  python .autoworkflow/tools/autoworkflow.py --root . gate{allow_flag}",
            ]
        )

        try:
            try:
                result = await Runner.run(manager, prompt, max_turns=cfg.max_turns)
            except TypeError:
                result = await Runner.run(manager, prompt)

            final_output = getattr(result, "final_output", None)
            log.append({"step": "sdk run", "exit": 0, "result": final_output if final_output is not None else str(result)})
        except Exception as exc:
            log.append({"step": "sdk run", "exit": 1, "error": str(exc)})
            trace_path.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in log), encoding="utf-8")
            print(f"[trace] {trace_path}")
            return 1

    trace_path.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in log), encoding="utf-8")
    print(f"[trace] {trace_path}")
    return 0


async def orchestrate_mcp_smoke(cfg: RunnerConfig) -> int:
    _Agent, _Runner, _set_default_openai_api, MCPServerStdio, _handoff_prefix = _import_agents_sdk()

    trace_path = _new_trace_path(cfg.repo)
    log: list[dict[str, Any]] = []

    try:
        async with MCPServerStdio(
            name="Codex CLI",
            params={
                "command": "npx",
                "args": ["-y", "codex", "mcp-server"],
            },
            client_session_timeout_seconds=120,
        ):
            log.append({"step": "mcp smoke", "cmd": ["npx", "-y", "codex", "mcp-server"], "exit": 0})
    except Exception as exc:
        log.append({"step": "mcp smoke", "exit": 1, "error": str(exc)})
        trace_path.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in log), encoding="utf-8")
        print(f"[trace] {trace_path}")
        return 1

    trace_path.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in log), encoding="utf-8")
    print(f"[trace] {trace_path}")
    return 0


async def async_main(cfg: RunnerConfig) -> int:
    if cfg.mode == "local":
        return await orchestrate_local(cfg)
    if cfg.mode == "mcp-smoke":
        return await orchestrate_mcp_smoke(cfg)
    if cfg.mode == "sdk":
        return await orchestrate_sdk(cfg)
    raise ValueError(f"Unknown mode: {cfg.mode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Agents SDK runner with Codex MCP (plan review + gate)")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--allow-unreviewed", action="store_true", help="Skip plan review guard")
    parser.add_argument(
        "--mode",
        choices=["local", "mcp-smoke", "sdk"],
        default="sdk",
        help="Runner mode: sdk (Agents SDK + MCP), mcp-smoke (start/stop MCP), or local (subprocess fallback)",
    )
    parser.add_argument("--approval-policy", default="never", help="Codex MCP tool approval-policy")
    parser.add_argument("--sandbox", default="workspace-write", help="Codex MCP tool sandbox")
    parser.add_argument("--model", default="gpt-5", help="Agents SDK model name")
    parser.add_argument("--max-turns", type=int, default=30, help="Max turns for Agents SDK Runner.run")
    args = parser.parse_args()

    cfg = RunnerConfig(
        repo=Path(args.root).resolve(),
        allow_unreviewed=bool(args.allow_unreviewed),
        approval_policy=str(args.approval_policy),
        sandbox=str(args.sandbox),
        mode=str(args.mode),
        model=str(args.model),
        max_turns=int(args.max_turns),
    )
    try:
        return asyncio.run(async_main(cfg))
    except RuntimeError as exc:
        # dependency missing / environment issue
        print(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
