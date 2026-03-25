#!/usr/bin/env python3
"""Run repo-local Claude skill prompts and optional rubric evals against example repositories."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
EXREPOS_ROOT = REPO_ROOT / ".exrepos"
TASKS_ROOT = Path(__file__).resolve().parent / "tasks"
EVAL_PROMPTS_ROOT = REPO_ROOT / "toolchain" / "evals" / "prompts"
TASK_PROMPTS = {
    "context-routing": TASKS_ROOT / "context-routing-skill-prompt.md",
    "knowledge-base": TASKS_ROOT / "knowledge-base-skill-prompt.md",
    "task-contract": TASKS_ROOT / "task-contract-skill-prompt.md",
    "writeback-cleanup": TASKS_ROOT / "writeback-cleanup-skill-prompt.md",
}
EVAL_PROMPTS = {
    "context-routing": EVAL_PROMPTS_ROOT / "context-routing-skills-prompts.md",
    "knowledge-base": EVAL_PROMPTS_ROOT / "knowledge-base-skill-prompt.md",
    "task-contract": EVAL_PROMPTS_ROOT / "task-contract-skill-prompt.md",
    "writeback-cleanup": EVAL_PROMPTS_ROOT / "writeback-cleanup-skill-prompt.md",
}
TEST_OUTPUT_PLACEHOLDER = "{{TEST_OUTPUT}}"


@dataclass
class RunResult:
    task: str
    phase: str
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
        help="Optional directory for saved prompts, responses, evals, stderr, and metadata.",
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


def resolve_eval_prompts(
    tasks: list[tuple[str, Path]],
    eval_prompt_override: Path | None,
    with_eval: bool,
) -> dict[str, Path]:
    if not with_eval:
        if eval_prompt_override is not None:
            raise ValueError("--eval-prompt-file requires --with-eval.")
        return {}

    if eval_prompt_override is not None and len(tasks) != 1:
        raise ValueError("--eval-prompt-file can only be used with a single --task.")

    eval_prompts: dict[str, Path] = {}
    for task_name, _ in tasks:
        eval_prompt = eval_prompt_override.resolve() if eval_prompt_override else EVAL_PROMPTS[task_name]
        if not eval_prompt.is_file():
            raise FileNotFoundError(f"Eval prompt file not found: {eval_prompt}")
        eval_prompts[task_name] = eval_prompt
    return eval_prompts


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


def run_prompt(
    repo_path: Path,
    task_name: str,
    phase: str,
    prompt_file: Path,
    prompt_text: str,
    claude_bin: str,
    permission_mode: str,
    output_format: str,
    model: str | None,
    timeout: int,
) -> RunResult:
    command = build_command(
        claude_bin=claude_bin,
        permission_mode=permission_mode,
        output_format=output_format,
        model=model,
        prompt_text=prompt_text,
    )
    started_at_dt = datetime.now(timezone.utc)

    try:
        completed = subprocess.run(
            command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        finished_at_dt = datetime.now(timezone.utc)
        return RunResult(
            task=task_name,
            phase=phase,
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
        return RunResult(
            task=task_name,
            phase=phase,
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


def artifact_stem(result: RunResult) -> str:
    stem = slugify(result.task)
    if result.phase == "skill":
        return stem
    return f"{stem}.{slugify(result.phase)}"


def save_result(run_dir: Path, result: RunResult) -> None:
    stem = artifact_stem(result)
    (run_dir / f"{stem}.prompt.txt").write_text(result.prompt_text + "\n", encoding="utf-8")
    (run_dir / f"{stem}.response.md").write_text(result.stdout, encoding="utf-8")
    if result.stderr:
        (run_dir / f"{stem}.stderr.txt").write_text(result.stderr, encoding="utf-8")

    meta = {
        "task": result.task,
        "phase": result.phase,
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


def print_result(result: RunResult) -> None:
    status = "timeout" if result.timed_out else ("ok" if result.returncode == 0 else "failed")
    print(f"=== {result.task} [{result.phase}] ===")
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


def longest_backtick_run(text: str) -> int:
    runs = re.findall(r"`+", text)
    return max((len(run) for run in runs), default=0)


def render_text_block(text: str) -> str:
    fence = "`" * max(3, longest_backtick_run(text) + 1)
    body = text.rstrip("\n")
    return f"{fence}text\n{body}\n{fence}"


def inject_test_output(eval_prompt_text: str, test_output: str) -> str:
    placeholder_block = f"```text\n{TEST_OUTPUT_PLACEHOLDER}\n```"
    rendered_block = render_text_block(test_output)
    if placeholder_block in eval_prompt_text:
        return eval_prompt_text.replace(placeholder_block, rendered_block)
    return eval_prompt_text.replace(TEST_OUTPUT_PLACEHOLDER, test_output)


def build_eval_prompt(eval_prompt_file: Path, skill_result: RunResult) -> str:
    eval_prompt_text = read_prompt(eval_prompt_file)
    return inject_test_output(eval_prompt_text, skill_result.stdout.rstrip())


def save_summary(run_dir: Path, repo_path: Path, results: list[RunResult]) -> None:
    summary = {
        "repo_path": str(repo_path),
        "results": [
            {
                "task": result.task,
                "phase": result.phase,
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
        eval_prompts = resolve_eval_prompts(tasks, args.eval_prompt_file, args.with_eval)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    run_dir = ensure_run_dir(args.save_dir, repo_path.name)
    results: list[RunResult] = []

    for task_name, prompt_file in tasks:
        try:
            prompt_text = read_prompt(prompt_file)
            result = run_prompt(
                repo_path=repo_path,
                task_name=task_name,
                phase="skill",
                prompt_file=prompt_file,
                prompt_text=prompt_text,
                claude_bin=args.claude_bin,
                permission_mode=args.permission_mode,
                output_format=args.output_format,
                model=args.model,
                timeout=args.timeout,
            )
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        results.append(result)
        print_result(result)
        if run_dir is not None:
            save_result(run_dir, result)

        if args.with_eval:
            eval_prompt_file = eval_prompts[task_name]
            eval_prompt_text = build_eval_prompt(eval_prompt_file, result)
            eval_result = run_prompt(
                repo_path=repo_path,
                task_name=task_name,
                phase="eval",
                prompt_file=eval_prompt_file,
                prompt_text=eval_prompt_text,
                claude_bin=args.claude_bin,
                permission_mode=args.permission_mode,
                output_format=args.output_format,
                model=args.eval_model or args.model,
                timeout=args.eval_timeout or args.timeout,
            )
            results.append(eval_result)
            print_result(eval_result)
            if run_dir is not None:
                save_result(run_dir, eval_result)

    if run_dir is not None:
        save_summary(run_dir, repo_path, results)
        print(f"saved_results: {run_dir}")

    return 0 if all(not result.timed_out and result.returncode == 0 for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
