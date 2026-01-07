#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AW-Kernel 日志查询工具

用于查询和分析 Agent 执行日志，无需安装 jq。

使用方式：
  python query-logs.py                     # 查看最近 10 条日志
  python query-logs.py --agent code-analyzer  # 按 Agent 过滤
  python query-logs.py --kind error        # 按事件类型过滤
  python query-logs.py --stats             # 查看统计信息
  python query-logs.py --format csv        # 导出为 CSV
  python query-logs.py --help              # 查看帮助
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


# Default log file path
DEFAULT_LOG_PATH = ".autoworkflow/logs/claude-code/feedback.jsonl"


def load_logs(log_path: Path) -> list[dict[str, Any]]:
    """Load logs from JSONL file."""
    if not log_path.exists():
        return []

    logs = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            logs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return logs


def filter_logs(
    logs: list[dict[str, Any]],
    agent: str | None = None,
    kind: str | None = None,
    session: str | None = None,
    date: str | None = None,
) -> list[dict[str, Any]]:
    """Filter logs by criteria."""
    result = logs

    if agent:
        result = [log for log in result if log.get("agent") == agent]

    if kind:
        result = [log for log in result if log.get("kind") == kind]

    if session:
        result = [log for log in result if log.get("session") == session]

    if date:
        if date == "today":
            date_str = datetime.now().strftime("%Y-%m-%d")
        elif date == "yesterday":
            date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            date_str = date
        result = [log for log in result if log.get("ts", "").startswith(date_str)]

    return result


def format_log(log: dict[str, Any], pretty: bool = True) -> str:
    """Format a single log entry."""
    if pretty:
        return json.dumps(log, ensure_ascii=False, indent=2)
    else:
        return json.dumps(log, ensure_ascii=False)


def format_csv(logs: list[dict[str, Any]]) -> str:
    """Format logs as CSV."""
    if not logs:
        return ""

    # CSV header
    headers = ["ts", "agent", "kind", "status", "duration_ms", "task", "summary", "error"]
    lines = [",".join(headers)]

    for log in logs:
        row = []
        for h in headers:
            value = log.get(h, "")
            if value is None:
                value = ""
            # Escape quotes and wrap in quotes if contains comma
            value = str(value).replace('"', '""')
            if "," in value or '"' in value or "\n" in value:
                value = f'"{value}"'
            row.append(value)
        lines.append(",".join(row))

    return "\n".join(lines)


def compute_stats(logs: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute statistics from logs."""
    stats = {
        "total_entries": len(logs),
        "agents": defaultdict(lambda: {"calls": 0, "errors": 0, "total_duration_ms": 0}),
        "kinds": defaultdict(int),
        "status": defaultdict(int),
    }

    for log in logs:
        agent = log.get("agent", "unknown")
        kind = log.get("kind", "unknown")
        status = log.get("status")
        duration = log.get("duration_ms", 0)

        stats["kinds"][kind] += 1

        if kind == "agent_start":
            stats["agents"][agent]["calls"] += 1
        elif kind == "agent_end":
            stats["agents"][agent]["total_duration_ms"] += duration or 0
            if status:
                stats["status"][status] += 1
        elif kind == "error":
            stats["agents"][agent]["errors"] += 1

    # Calculate averages
    for agent, data in stats["agents"].items():
        if data["calls"] > 0:
            data["avg_duration_ms"] = round(data["total_duration_ms"] / data["calls"], 2)
        else:
            data["avg_duration_ms"] = 0

    return stats


def print_stats(stats: dict[str, Any]) -> None:
    """Print statistics in a readable format."""
    print("=" * 50)
    print("AW-Kernel Agent 日志统计")
    print("=" * 50)
    print(f"\n总日志条目: {stats['total_entries']}")

    print("\n--- 事件类型分布 ---")
    for kind, count in sorted(stats["kinds"].items()):
        print(f"  {kind}: {count}")

    print("\n--- 执行状态分布 ---")
    for status, count in sorted(stats["status"].items()):
        print(f"  {status}: {count}")

    print("\n--- Agent 调用统计 ---")
    print(f"  {'Agent':<25} {'调用次数':<10} {'错误次数':<10} {'平均耗时(ms)':<15}")
    print("  " + "-" * 60)
    for agent, data in sorted(stats["agents"].items()):
        print(f"  {agent:<25} {data['calls']:<10} {data['errors']:<10} {data['avg_duration_ms']:<15}")

    print("\n" + "=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="AW-Kernel 日志查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                          查看最近 10 条日志
  %(prog)s --agent code-analyzer    查询 code-analyzer 的日志
  %(prog)s --kind error             查询所有错误日志
  %(prog)s --stats                  查看统计信息
  %(prog)s --date today             查询今天的日志
  %(prog)s --format csv > logs.csv  导出为 CSV
        """
    )

    parser.add_argument(
        "--path", "-p",
        default=DEFAULT_LOG_PATH,
        help=f"日志文件路径 (默认: {DEFAULT_LOG_PATH})"
    )
    parser.add_argument(
        "--agent", "-a",
        help="按 Agent 名称过滤"
    )
    parser.add_argument(
        "--kind", "-k",
        choices=["agent_start", "agent_end", "error"],
        help="按事件类型过滤"
    )
    parser.add_argument(
        "--session", "-s",
        help="按 Session ID 过滤"
    )
    parser.add_argument(
        "--date", "-d",
        help="按日期过滤 (格式: YYYY-MM-DD, 或 'today', 'yesterday')"
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=10,
        help="显示最近 N 条日志 (默认: 10, 0 表示全部)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="显示统计信息"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "jsonl", "csv", "pretty"],
        default="pretty",
        help="输出格式 (默认: pretty)"
    )
    parser.add_argument(
        "--no-pretty",
        action="store_true",
        help="禁用美化输出 (等同于 --format jsonl)"
    )

    args = parser.parse_args()

    # Load logs
    log_path = Path(args.path)
    logs = load_logs(log_path)

    if not logs:
        print(f"未找到日志文件或日志为空: {log_path}", file=sys.stderr)
        return 1

    # Filter logs
    filtered = filter_logs(
        logs,
        agent=args.agent,
        kind=args.kind,
        session=args.session,
        date=args.date,
    )

    # Show stats if requested
    if args.stats:
        stats = compute_stats(filtered)
        print_stats(stats)
        return 0

    # Limit results
    if args.limit > 0:
        filtered = filtered[-args.limit:]

    # Output
    if args.no_pretty:
        args.format = "jsonl"

    if args.format == "csv":
        print(format_csv(filtered))
    elif args.format == "jsonl":
        for log in filtered:
            print(format_log(log, pretty=False))
    elif args.format == "json":
        print(json.dumps(filtered, ensure_ascii=False, indent=2))
    else:  # pretty
        for log in filtered:
            print(format_log(log, pretty=True))
            print()  # Empty line between entries

    return 0


if __name__ == "__main__":
    sys.exit(main())
