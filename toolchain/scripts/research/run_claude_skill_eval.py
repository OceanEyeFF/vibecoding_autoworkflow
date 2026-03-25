#!/usr/bin/env python3
"""Compatibility shell for the legacy Claude-only research runner."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from run_skill_suite import main as run_skill_suite_main


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Claude non-interactive skill prompts and optional rubric evals "
            "against a repository under .exrepos/."
        )
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository name under .exrepos/ or an explicit repository path.",
    )
    parser.add_argument(
        "--task",
        choices=("context-routing", "knowledge-base", "task-contract", "writeback-cleanup", "all"),
        default="all",
        help="Which skill prompt to run. Defaults to all.",
    )
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Override the prompt file. Only valid when --task is a single task.",
    )
    parser.add_argument(
        "--with-eval",
        action="store_true",
        help="After each skill run, evaluate the captured output with the matching eval prompt.",
    )
    parser.add_argument(
        "--eval-prompt-file",
        type=Path,
        help="Override the eval prompt file. Only valid with --with-eval and a single --task.",
    )
    parser.add_argument(
        "--claude-bin",
        default="claude",
        help="Claude executable to invoke. Defaults to 'claude'.",
    )
    parser.add_argument(
        "--model",
        help="Optional Claude model override.",
    )
    parser.add_argument(
        "--permission-mode",
        default="bypassPermissions",
        help="Claude permission mode. Defaults to bypassPermissions.",
    )
    parser.add_argument(
        "--output-format",
        default="text",
        choices=("text", "json", "stream-json"),
        help="Claude output format. Defaults to text.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Per-task timeout in seconds. Defaults to 300.",
    )
    parser.add_argument(
        "--eval-model",
        help="Optional Claude model override for the eval phase. Defaults to --model.",
    )
    parser.add_argument(
        "--eval-timeout",
        type=int,
        help="Per-task timeout for the eval phase in seconds. Defaults to --timeout.",
    )
    parser.add_argument(
        "--save-dir",
        type=Path,
        help="Optional directory for saved prompts, final answers, raw outputs, and metadata.",
    )
    return parser.parse_args(argv)


def build_forward_args(args: argparse.Namespace) -> list[str]:
    forwarded = [
        "--backend",
        "claude",
        "--repo",
        args.repo,
        "--task",
        args.task,
        "--claude-bin",
        args.claude_bin,
        "--permission-mode",
        args.permission_mode,
        "--output-format",
        args.output_format,
        "--timeout",
        str(args.timeout),
    ]
    if args.prompt_file is not None:
        forwarded.extend(["--prompt-file", str(args.prompt_file)])
    if args.with_eval:
        forwarded.append("--with-eval")
        forwarded.extend(["--judge-backend", "claude"])
    if args.eval_prompt_file is not None:
        forwarded.extend(["--eval-prompt-file", str(args.eval_prompt_file)])
    if args.model:
        forwarded.extend(["--model", args.model])
    if args.eval_model:
        forwarded.extend(["--eval-model", args.eval_model])
    if args.eval_timeout is not None:
        forwarded.extend(["--eval-timeout", str(args.eval_timeout)])
    if args.save_dir is not None:
        forwarded.extend(["--save-dir", str(args.save_dir)])
    return forwarded


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    return run_skill_suite_main(build_forward_args(args))


if __name__ == "__main__":
    raise SystemExit(main())
