#!/usr/bin/env python3
"""Thin wrapper for the live backend acceptance matrix."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from run_skill_suite import main as run_skill_suite_main


MATRIX_LANES = (
    ("codex", "codex"),
    ("claude", "codex"),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the live backend acceptance matrix against a repo. "
            "This is a real-backend acceptance path, not a cheap deterministic regression."
        )
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository name under .exrepos/ or an explicit repository path.",
    )
    parser.add_argument(
        "--model",
        help="Optional model override for skill execution.",
    )
    parser.add_argument(
        "--eval-model",
        help="Optional model override for Codex judging. Defaults to --model.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Per-task timeout in seconds. Defaults to 300.",
    )
    parser.add_argument(
        "--eval-timeout",
        type=int,
        help="Per-task timeout for eval judging in seconds. Defaults to --timeout.",
    )
    parser.add_argument(
        "--save-dir",
        type=Path,
        help="Optional directory for saved prompts, outputs, metadata, and summary.",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help=(
            "Number of spec pipelines to run concurrently after the temporary suite is generated. "
            "Defaults to 1."
        ),
    )
    parser.add_argument(
        "--claude-bin",
        default="claude",
        help="Claude executable to invoke. Defaults to 'claude'.",
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
        "--codex-bin",
        default="codex",
        help="Codex executable to invoke. Defaults to 'codex'.",
    )
    parser.add_argument(
        "--sandbox",
        default="workspace-write",
        choices=("read-only", "workspace-write", "danger-full-access"),
        help="Codex sandbox mode. Defaults to workspace-write.",
    )
    parser.add_argument(
        "--full-auto",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use Codex full-auto mode. Defaults to enabled.",
    )
    return parser.parse_args(argv)


def build_suite_manifest(repo: str) -> dict[str, object]:
    return {
        "version": 1,
        "defaults": {
            "with_eval": True,
        },
        "runs": [
            {
                "repo": repo,
                "backend": backend,
                "judge_backend": judge_backend,
                "task": "all",
            }
            for backend, judge_backend in MATRIX_LANES
        ],
    }


def write_temp_suite_file(manifest: dict[str, object]) -> Path:
    handle = tempfile.NamedTemporaryFile(
        prefix="backend-acceptance-matrix-",
        suffix=".json",
        delete=False,
    )
    with handle:
        handle.write((json.dumps(manifest, ensure_ascii=True, indent=2) + "\n").encode("utf-8"))
    return Path(handle.name)


def build_forward_args(args: argparse.Namespace, suite_path: Path) -> list[str]:
    forwarded = [
        "--suite",
        str(suite_path),
        "--timeout",
        str(args.timeout),
        "--jobs",
        str(args.jobs),
        "--claude-bin",
        args.claude_bin,
        "--permission-mode",
        args.permission_mode,
        "--output-format",
        args.output_format,
        "--codex-bin",
        args.codex_bin,
        "--sandbox",
        args.sandbox,
        "--full-auto" if args.full_auto else "--no-full-auto",
    ]
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
    suite_path = write_temp_suite_file(build_suite_manifest(args.repo))
    try:
        return run_skill_suite_main(build_forward_args(args, suite_path))
    finally:
        suite_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
