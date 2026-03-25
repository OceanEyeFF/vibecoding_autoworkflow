#!/usr/bin/env python3
"""Run repo-local Claude skill prompts against example repositories."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
EXREPOS_ROOT = REPO_ROOT / ".exrepos"
TASKS_ROOT = Path(__file__).resolve().parent / "tasks"
TASK_PROMPTS = {
    "context-routing": TASKS_ROOT / "context-routing-skill-prompt.md",
    "knowledge-base": TASKS_ROOT / "knowledge-base-skill-prompt.md",
    "task-contract": TASKS_ROOT / "task-contract-skill-prompt.md",
    "writeback-cleanup": TASKS_ROOT / "writeback-cleanup-skill-prompt.md",
}


@dataclass
class TaskResult:
    task: str
    prompt_file: Path
    prompt_text: str
    command: list[str]
    returncode: int | None
    stdout: str
    stderr: str
    elapsed_seconds: float
    timed_out: bool
    started_at: str
    finished_at: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Claude non-interactive skill prompts against a repository under .exrepos/."
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository name under .exrepos/ or an explicit repository path.",
    )
    parser.add_argument(
        "--task",
        choices=[*TASK_PROMPTS.keys(), "all"],
        default="all",
        help="Which skill prompt to run. Defaults to all.",
    )
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Override the prompt file. Only valid when --task is a single task.",
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
        "--save-dir",
        type=Path,
        help="Optional directory for saved prompts, responses, stderr, and metadata.",
    )
    return parser.parse_args()


def resolve_repo(repo_value: str) -> Path:
    repo_path = Path(repo_value).expanduser()
    if repo_path.exists():
        return repo_path.resolve()

    repo_path = EXREPOS_ROOT / repo_value
    if repo_path.exists():
        return repo_path.resolve()

    raise FileNotFoundError(f"Repository not found: {repo_value}")


def resolve_tasks(task_name: str, prompt_override: Path | None) -> list[tuple[str, Path]]:
    if task_name == "all":
        if prompt_override is not None:
            raise ValueError("--prompt-file can only be used with a single --task.")
        return list(TASK_PROMPTS.items())

    prompt_file = prompt_override.resolve() if prompt_override else TASK_PROMPTS[task_name]
    if not prompt_file.is_file():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    return [(task_name, prompt_file)]


def read_prompt(prompt_file: Path) -> str:
    return prompt_file.read_text(encoding="utf-8").strip()


def build_command(
    claude_bin: str,
    permission_mode: str,
    output_format: str,
    model: str | None,
    prompt_text: str,
) -> list[str]:
    command = [
        claude_bin,
        "-p",
        "--permission-mode",
        permission_mode,
        "--output-format",
        output_format,
    ]
    if model:
        command.extend(["--model", model])
    command.append(prompt_text)
    return command


def run_task(
    repo_path: Path,
    task_name: str,
    prompt_file: Path,
    args: argparse.Namespace,
) -> TaskResult:
    prompt_text = read_prompt(prompt_file)
    command = build_command(
        claude_bin=args.claude_bin,
        permission_mode=args.permission_mode,
        output_format=args.output_format,
        model=args.model,
        prompt_text=prompt_text,
    )
    started_at_dt = datetime.now(timezone.utc)

    try:
        completed = subprocess.run(
            command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=args.timeout,
            check=False,
        )
        finished_at_dt = datetime.now(timezone.utc)
        return TaskResult(
            task=task_name,
            prompt_file=prompt_file.resolve(),
            prompt_text=prompt_text,
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            elapsed_seconds=(finished_at_dt - started_at_dt).total_seconds(),
            timed_out=False,
            started_at=started_at_dt.isoformat(),
            finished_at=finished_at_dt.isoformat(),
        )
    except subprocess.TimeoutExpired as exc:
        finished_at_dt = datetime.now(timezone.utc)
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        return TaskResult(
            task=task_name,
            prompt_file=prompt_file.resolve(),
            prompt_text=prompt_text,
            command=command,
            returncode=None,
            stdout=stdout,
            stderr=stderr,
            elapsed_seconds=(finished_at_dt - started_at_dt).total_seconds(),
            timed_out=True,
            started_at=started_at_dt.isoformat(),
            finished_at=finished_at_dt.isoformat(),
        )


def slugify(value: str) -> str:
    return "".join(char if char.isalnum() or char in ("-", "_") else "-" for char in value)


def ensure_run_dir(save_dir: Path | None, repo_name: str) -> Path | None:
    if save_dir is None:
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = save_dir.expanduser().resolve() / f"{timestamp}-{slugify(repo_name)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def save_result(run_dir: Path, result: TaskResult) -> None:
    stem = slugify(result.task)
    (run_dir / f"{stem}.prompt.txt").write_text(result.prompt_text + "\n", encoding="utf-8")
    (run_dir / f"{stem}.response.md").write_text(result.stdout, encoding="utf-8")
    if result.stderr:
        (run_dir / f"{stem}.stderr.txt").write_text(result.stderr, encoding="utf-8")

    meta = {
        "task": result.task,
        "prompt_file": str(result.prompt_file),
        "command": result.command,
        "command_preview": shlex.join(result.command),
        "returncode": result.returncode,
        "timed_out": result.timed_out,
        "elapsed_seconds": result.elapsed_seconds,
        "started_at": result.started_at,
        "finished_at": result.finished_at,
    }
    (run_dir / f"{stem}.meta.json").write_text(
        json.dumps(meta, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def print_result(result: TaskResult) -> None:
    status = "timeout" if result.timed_out else ("ok" if result.returncode == 0 else "failed")
    print(f"=== {result.task} ===")
    print(f"prompt_file: {result.prompt_file}")
    print(f"status: {status}")
    print(f"elapsed_seconds: {result.elapsed_seconds:.2f}")
    print(f"command: {shlex.join(result.command)}")
    if result.stdout:
        print()
        print(result.stdout.rstrip())
    if result.stderr:
        print()
        print("--- stderr ---")
        print(result.stderr.rstrip())
    print()


def save_summary(run_dir: Path, repo_path: Path, results: list[TaskResult]) -> None:
    summary = {
        "repo_path": str(repo_path),
        "results": [
            {
                "task": result.task,
                "prompt_file": str(result.prompt_file),
                "returncode": result.returncode,
                "timed_out": result.timed_out,
                "elapsed_seconds": result.elapsed_seconds,
                "started_at": result.started_at,
                "finished_at": result.finished_at,
            }
            for result in results
        ],
    }
    (run_dir / "run-summary.json").write_text(
        json.dumps(summary, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()

    try:
        repo_path = resolve_repo(args.repo)
        tasks = resolve_tasks(args.task, args.prompt_file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    run_dir = ensure_run_dir(args.save_dir, repo_path.name)
    results: list[TaskResult] = []

    for task_name, prompt_file in tasks:
        try:
            result = run_task(repo_path, task_name, prompt_file, args)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        results.append(result)
        print_result(result)
        if run_dir is not None:
            save_result(run_dir, result)

    if run_dir is not None:
        save_summary(run_dir, repo_path, results)
        print(f"saved_results: {run_dir}")

    return 0 if all(not result.timed_out and result.returncode == 0 for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
