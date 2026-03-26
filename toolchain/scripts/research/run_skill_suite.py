#!/usr/bin/env python3
"""Run repo-local skill prompts and optional evals across multiple backends."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backends import BACKEND_IDS, build_backend
from common import (
    EVAL_SCORE_DIMENSIONS,
    RUN_SUMMARY_SCHEMA_PATH,
    RunResult,
    RunSpec,
    SUITES_ROOT,
    TASK_PROMPTS,
    build_eval_prompt,
    write_eval_result_schema,
    ensure_run_dir,
    parse_json_object,
    parse_rubric_text,
    read_prompt,
    resolve_eval_prompts,
    resolve_repo,
    resolve_tasks,
    slugify,
    normalize_eval_payload,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run research skill prompts and optional eval rubrics against repositories "
            "under .exrepos/ or explicit repository paths."
        )
    )
    scope_group = parser.add_mutually_exclusive_group(required=True)
    scope_group.add_argument(
        "--repo",
        help="Repository name under .exrepos/ or an explicit repository path.",
    )
    scope_group.add_argument(
        "--suite",
        help="Suite manifest path or a file name under toolchain/evals/fixtures/suites/.",
    )
    parser.add_argument(
        "--backend",
        choices=BACKEND_IDS,
        help="Backend used for skill execution. Required outside suite mode.",
    )
    parser.add_argument(
        "--judge-backend",
        choices=BACKEND_IDS,
        help="Backend used for eval judging. Defaults to --backend.",
    )
    parser.add_argument(
        "--task",
        choices=[*TASK_PROMPTS.keys(), "all"],
        help="Which skill prompt to run. Defaults to all when --repo is used.",
    )
    parser.add_argument(
        "--with-eval",
        action="store_true",
        help="After each skill run, evaluate the captured output with the matching eval prompt.",
    )
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Override the prompt file. Only valid with a single --task.",
    )
    parser.add_argument(
        "--eval-prompt-file",
        type=Path,
        help="Override the eval prompt file. Only valid with --with-eval and a single --task.",
    )
    parser.add_argument(
        "--model",
        help="Optional model override for skill execution.",
    )
    parser.add_argument(
        "--eval-model",
        help="Optional model override for eval judging. Defaults to --model.",
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
        help="Optional directory for saved prompts, final answers, raw outputs, metadata, and summary.",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help=(
            "Number of spec pipelines to run concurrently. "
            "Each pipeline still runs skill then eval sequentially. Defaults to 1."
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
    parser.add_argument(
        "--opencode-bin",
        default="opencode",
        help="Reserved OpenCode executable name. Defaults to 'opencode'.",
    )
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    if args.jobs < 1:
        raise ValueError("--jobs must be at least 1.")

    if args.suite:
        forbidden = []
        if args.backend is not None:
            forbidden.append("--backend")
        if args.judge_backend is not None:
            forbidden.append("--judge-backend")
        if args.task is not None:
            forbidden.append("--task")
        if args.with_eval:
            forbidden.append("--with-eval")
        if args.prompt_file is not None:
            forbidden.append("--prompt-file")
        if args.eval_prompt_file is not None:
            forbidden.append("--eval-prompt-file")
        if forbidden:
            joined = ", ".join(forbidden)
            raise ValueError(f"{joined} are not supported together with --suite.")
        return

    if args.backend is None:
        raise ValueError("--backend is required with --repo.")
    if args.eval_prompt_file is not None and not args.with_eval:
        raise ValueError("--eval-prompt-file requires --with-eval.")
    if args.eval_model is not None and not args.with_eval:
        raise ValueError("--eval-model requires --with-eval.")
    if args.eval_timeout is not None and not args.with_eval:
        raise ValueError("--eval-timeout requires --with-eval.")
    if args.judge_backend is not None and not args.with_eval:
        raise ValueError("--judge-backend requires --with-eval.")


def resolve_suite_path(suite_value: str) -> Path:
    explicit = Path(suite_value).expanduser()
    if explicit.exists():
        return explicit.resolve()

    for candidate in (explicit, explicit.with_suffix(".yaml"), explicit.with_suffix(".yml"), explicit.with_suffix(".json")):
        suite_path = SUITES_ROOT / candidate.name
        if suite_path.exists():
            return suite_path.resolve()

    raise FileNotFoundError(f"Suite manifest not found: {suite_value}")


def load_suite_manifest(path: Path) -> dict[str, Any]:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("YAML suite manifests require PyYAML to be installed.") from exc

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Suite manifest must be a mapping: {path}")
    return data


def resolve_suite_repo(repo_value: str, suite_dir: Path) -> Path:
    try:
        return resolve_repo(repo_value)
    except FileNotFoundError:
        candidate = (suite_dir / repo_value).expanduser()
        if candidate.exists():
            return candidate.resolve()
        raise


def resolve_path_override(value: Any, base_dir: Path) -> Path | None:
    if value is None:
        return None
    candidate = Path(str(value)).expanduser()
    if candidate.is_absolute():
        return candidate
    resolved = (base_dir / candidate).resolve()
    return resolved


def resolve_direct_specs(args: argparse.Namespace) -> tuple[list[RunSpec], Path | None, str]:
    repo_path = resolve_repo(args.repo)
    tasks = resolve_tasks(args.task, args.prompt_file)
    eval_prompts = resolve_eval_prompts(tasks, args.eval_prompt_file, args.with_eval)
    judge_backend = args.judge_backend or args.backend
    specs = [
        RunSpec(
            repo_path=repo_path,
            task=task_name,
            prompt_file=prompt_file,
            eval_prompt_file=eval_prompts.get(task_name),
            backend=args.backend,
            judge_backend=judge_backend,
            with_eval=args.with_eval,
        )
        for task_name, prompt_file in tasks
    ]
    return specs, None, repo_path.name


def resolve_suite_specs(args: argparse.Namespace) -> tuple[list[RunSpec], Path, str]:
    suite_path = resolve_suite_path(args.suite)
    manifest = load_suite_manifest(suite_path)
    version = manifest.get("version", 1)
    if version != 1:
        raise ValueError(f"Unsupported suite manifest version: {version}")

    defaults = manifest.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise ValueError("Suite manifest 'defaults' must be a mapping when present.")
    runs = manifest.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("Suite manifest must define a non-empty 'runs' list.")

    specs: list[RunSpec] = []
    for index, run_entry in enumerate(runs, start=1):
        if not isinstance(run_entry, dict):
            raise ValueError(f"Suite run #{index} must be a mapping.")

        repo_value = run_entry.get("repo")
        if not repo_value:
            raise ValueError(f"Suite run #{index} is missing 'repo'.")
        backend = str(run_entry.get("backend") or defaults.get("backend") or "")
        if not backend:
            raise ValueError(f"Suite run #{index} is missing 'backend'.")
        judge_backend = str(run_entry.get("judge_backend") or defaults.get("judge_backend") or backend)
        with_eval = bool(run_entry.get("with_eval", defaults.get("with_eval", False)))
        task_name = str(run_entry.get("task") or "all")

        prompt_override = resolve_path_override(run_entry.get("prompt_file"), suite_path.parent)
        eval_prompt_override = resolve_path_override(run_entry.get("eval_prompt_file"), suite_path.parent)

        repo_path = resolve_suite_repo(str(repo_value), suite_path.parent)
        tasks = resolve_tasks(task_name, prompt_override)
        eval_prompts = resolve_eval_prompts(tasks, eval_prompt_override, with_eval)
        for resolved_task, prompt_file in tasks:
            specs.append(
                RunSpec(
                    repo_path=repo_path,
                    task=resolved_task,
                    prompt_file=prompt_file,
                    eval_prompt_file=eval_prompts.get(resolved_task),
                    backend=backend,
                    judge_backend=judge_backend,
                    with_eval=with_eval,
                )
            )

    return specs, suite_path, suite_path.stem


def build_backend_registry(specs: list[RunSpec], args: argparse.Namespace) -> dict[str, Any]:
    registry: dict[str, Any] = {}
    backend_ids = {spec.backend for spec in specs}
    backend_ids.update(spec.judge_backend for spec in specs if spec.with_eval)
    for backend_id in sorted(backend_ids):
        backend = build_backend(backend_id, args)
        healthy, message = backend.healthcheck()
        if not healthy:
            raise RuntimeError(f"{backend_id} backend unavailable: {message}")
        registry[backend_id] = backend
    return registry


def run_backend_prompt(
    backend,
    spec: RunSpec,
    phase: str,
    prompt_file: Path,
    prompt_text: str,
    model: str | None,
    timeout: int,
    schema_file: Path | None,
) -> RunResult:
    if phase == "skill":
        invocation = backend.build_skill_command(prompt_text=prompt_text, repo_path=spec.repo_path, model=model)
    else:
        invocation = backend.build_eval_command(
            prompt_text=prompt_text,
            repo_path=spec.repo_path,
            model=model,
            schema_path=schema_file,
        )

    started_at_dt = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    try:
        completed = subprocess.run(
            invocation.command,
            cwd=spec.repo_path,
            input=invocation.stdin_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        returncode = completed.returncode
        raw_stdout = coerce_process_output(completed.stdout)
        raw_stderr = coerce_process_output(completed.stderr)
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        returncode = None
        raw_stdout = coerce_process_output(exc.stdout)
        raw_stderr = coerce_process_output(exc.stderr)
        timed_out = True
    finally:
        finished_at_dt = datetime.now(timezone.utc)
        elapsed_seconds = time.perf_counter() - started_perf

    final_message = ""
    try:
        final_message = backend.extract_final_message(invocation, raw_stdout)
    finally:
        cleanup_backend_artifacts(invocation.cleanup_paths)

    result = RunResult(
        task=spec.task,
        phase=phase,
        backend=spec.backend,
        judge_backend=spec.judge_backend,
        repo_path=spec.repo_path,
        prompt_file=prompt_file.resolve(),
        prompt_text=prompt_text,
        command=invocation.command,
        returncode=returncode,
        raw_stdout=raw_stdout,
        raw_stderr=raw_stderr,
        final_message=final_message,
        elapsed_seconds=elapsed_seconds,
        timed_out=timed_out,
        started_at=started_at_dt.isoformat(),
        finished_at=finished_at_dt.isoformat(),
        schema_file=schema_file.resolve() if schema_file else None,
    )
    if phase == "eval":
        structured_output, parse_error = parse_eval_output(spec, final_message or raw_stdout)
        result.structured_output = structured_output
        result.parse_error = parse_error
    return result


def coerce_process_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def cleanup_backend_artifacts(paths: list[Path]) -> None:
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            continue


def parse_eval_output(spec: RunSpec, raw_text: str) -> tuple[dict[str, Any] | None, str | None]:
    expected_dimension_count = len(EVAL_SCORE_DIMENSIONS[spec.task])
    if not raw_text.strip():
        return None, "Eval phase produced no usable output."

    payload = parse_json_object(raw_text)
    if payload is not None:
        normalized = normalize_eval_payload(
            task_name=spec.task,
            repo_name=spec.repo_path.name,
            backend=spec.backend,
            judge_backend=spec.judge_backend,
            payload=payload,
        )
        if not normalized["scores"]:
            return normalized, "Structured eval output did not contain any recognized score keys."
        if len(normalized["dimension_feedback"]) != expected_dimension_count:
            return normalized, "Structured eval output did not contain complete dimension feedback."
        return normalized, None

    text_payload = parse_rubric_text(spec.task, raw_text)
    normalized = normalize_eval_payload(
        task_name=spec.task,
        repo_name=spec.repo_path.name,
        backend=spec.backend,
        judge_backend=spec.judge_backend,
        payload=text_payload,
    )
    if not normalized["scores"]:
        return normalized, "Eval output did not contain any parsed rubric scores."
    if len(normalized["dimension_feedback"]) != expected_dimension_count:
        return normalized, "Eval output did not contain complete dimension feedback."
    return normalized, None


def print_result(result: RunResult) -> None:
    if result.timed_out:
        status = "timeout"
    elif result.returncode == 0 and result.parse_error is None:
        status = "ok"
    else:
        status = "failed"

    print(f"=== {result.repo_path.name} :: {result.task} [{result.phase}] ===")
    print(f"backend: {result.backend}")
    if result.phase == "eval":
        print(f"judge_backend: {result.judge_backend}")
    print(f"prompt_file: {result.prompt_file}")
    print(f"status: {status}")
    print(f"elapsed_seconds: {result.elapsed_seconds:.2f}")
    print(f"command: {result.command_preview}")

    display_text = result.final_message or result.raw_stdout
    if display_text:
        print()
        print(display_text.rstrip())
    if result.raw_stdout and result.final_message and result.raw_stdout.strip() != result.final_message.strip():
        print()
        print("--- raw stdout ---")
        print(result.raw_stdout.rstrip())
    if result.raw_stderr:
        print()
        print("--- raw stderr ---")
        print(result.raw_stderr.rstrip())
    if result.parse_error:
        print()
        print(f"parse_error: {result.parse_error}")
    print()


def artifact_stem(result: RunResult, sequence: int) -> str:
    stem = f"{sequence:02d}.{slugify(result.repo_path.name)}.{slugify(result.task)}"
    if result.phase == "skill":
        return f"{stem}.skill.{slugify(result.backend)}"
    return f"{stem}.eval.{slugify(result.backend)}-judge-{slugify(result.judge_backend)}"


def schema_artifact_name(spec: RunSpec, sequence: int) -> str:
    stem = f"{sequence:02d}.{slugify(spec.repo_path.name)}.{slugify(spec.task)}"
    return f"{stem}.eval-schema.{slugify(spec.judge_backend)}.json"


def prepare_eval_schema_file(spec: RunSpec, run_dir: Path | None, sequence: int) -> tuple[Path, Path | None]:
    if run_dir is None:
        handle = tempfile.NamedTemporaryFile(prefix="research-eval-schema-", suffix=".json", delete=False)
        handle.close()
        schema_path = Path(handle.name)
        write_eval_result_schema(spec.task, schema_path)
        return schema_path, schema_path

    schema_path = run_dir / schema_artifact_name(spec, sequence)
    write_eval_result_schema(spec.task, schema_path)
    return schema_path, None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def save_result(run_dir: Path, result: RunResult, sequence: int) -> dict[str, str]:
    stem = artifact_stem(result, sequence)
    response_text = (result.final_message or result.raw_stdout).rstrip()

    prompt_path = run_dir / f"{stem}.prompt.txt"
    response_path = run_dir / f"{stem}.response.md"
    final_path = run_dir / f"{stem}.final.txt"
    stdout_path = run_dir / f"{stem}.raw.stdout.txt"
    stderr_path = run_dir / f"{stem}.raw.stderr.txt"
    legacy_stderr_path = run_dir / f"{stem}.stderr.txt"
    meta_path = run_dir / f"{stem}.meta.json"

    prompt_path.write_text(result.prompt_text + "\n", encoding="utf-8")
    response_path.write_text(response_text + ("\n" if response_text else ""), encoding="utf-8")
    final_path.write_text(result.final_message + ("\n" if result.final_message else ""), encoding="utf-8")
    stdout_path.write_text(result.raw_stdout, encoding="utf-8")
    if result.raw_stderr:
        stderr_path.write_text(result.raw_stderr, encoding="utf-8")
        legacy_stderr_path.write_text(result.raw_stderr, encoding="utf-8")

    artifacts = {
        "prompt": prompt_path.name,
        "response": response_path.name,
        "final": final_path.name,
        "raw_stdout": stdout_path.name,
        "meta": meta_path.name,
    }
    if result.raw_stderr:
        artifacts["raw_stderr"] = stderr_path.name
        artifacts["stderr"] = legacy_stderr_path.name
    if result.schema_file is not None and result.schema_file.parent == run_dir:
        artifacts["schema"] = result.schema_file.name

    if result.structured_output is not None:
        structured_path = run_dir / f"{stem}.structured.json"
        write_json(structured_path, result.structured_output)
        artifacts["structured_output"] = structured_path.name

    meta = {
        "task": result.task,
        "phase": result.phase,
        "backend": result.backend,
        "judge_backend": result.judge_backend,
        "repo_path": str(result.repo_path),
        "prompt_file": str(result.prompt_file),
        "command": result.command,
        "returncode": result.returncode,
        "timed_out": result.timed_out,
        "elapsed_seconds": result.elapsed_seconds,
        "started_at": result.started_at,
        "finished_at": result.finished_at,
        "schema_file": str(result.schema_file) if result.schema_file else None,
        "parse_error": result.parse_error,
        "artifacts": artifacts,
    }
    if result.structured_output is not None:
        meta["structured_output"] = result.structured_output
    write_json(meta_path, meta)
    return artifacts


def save_summary(
    run_dir: Path,
    suite_path: Path | None,
    results: list[tuple[RunResult, dict[str, str] | None]],
) -> None:
    summary = {
        "runner": "run_skill_suite.py",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "suite_file": str(suite_path) if suite_path else None,
        "summary_schema": str(RUN_SUMMARY_SCHEMA_PATH),
        "results": [
            {
                "repo_path": str(result.repo_path),
                "task": result.task,
                "phase": result.phase,
                "backend": result.backend,
                "judge_backend": result.judge_backend,
                "prompt_file": str(result.prompt_file),
                "returncode": result.returncode,
                "timed_out": result.timed_out,
                "elapsed_seconds": result.elapsed_seconds,
                "started_at": result.started_at,
                "finished_at": result.finished_at,
                "schema_file": str(result.schema_file) if result.schema_file else None,
                "parse_error": result.parse_error,
                "structured_output": result.structured_output,
                "artifacts": artifacts or {},
            }
            for result, artifacts in results
        ],
    }
    write_json(run_dir / "run-summary.json", summary)


def result_is_success(result: RunResult) -> bool:
    if result.timed_out or result.returncode != 0:
        return False
    if result.phase == "eval" and result.structured_output is None:
        return False
    if result.parse_error:
        return False
    return True


def run_spec_pipeline(
    spec: RunSpec,
    spec_index: int,
    *,
    args: argparse.Namespace,
    backend_registry: dict[str, Any],
    run_dir: Path | None,
) -> list[tuple[RunResult, dict[str, str] | None]]:
    results: list[tuple[RunResult, dict[str, str] | None]] = []
    prompt_text = read_prompt(spec.prompt_file)
    skill_result = run_backend_prompt(
        backend=backend_registry[spec.backend],
        spec=spec,
        phase="skill",
        prompt_file=spec.prompt_file,
        prompt_text=prompt_text,
        model=args.model,
        timeout=args.timeout,
        schema_file=None,
    )
    skill_artifacts = save_result(run_dir, skill_result, spec_index * 2 - 1) if run_dir else None
    results.append((skill_result, skill_artifacts))

    if not spec.with_eval or spec.eval_prompt_file is None:
        return results

    judge_backend = backend_registry[spec.judge_backend]
    schema_file = None
    schema_cleanup = None
    if judge_backend.supports_json_schema:
        schema_file, schema_cleanup = prepare_eval_schema_file(spec, run_dir, spec_index * 2)
    eval_prompt_text = build_eval_prompt(
        eval_prompt_file=spec.eval_prompt_file,
        skill_result=skill_result,
        structured_output=judge_backend.supports_json_schema,
    )
    try:
        eval_result = run_backend_prompt(
            backend=judge_backend,
            spec=spec,
            phase="eval",
            prompt_file=spec.eval_prompt_file,
            prompt_text=eval_prompt_text,
            model=args.eval_model or args.model,
            timeout=args.eval_timeout or args.timeout,
            schema_file=schema_file,
        )
    finally:
        if schema_cleanup is not None:
            schema_cleanup.unlink(missing_ok=True)
    eval_artifacts = save_result(run_dir, eval_result, spec_index * 2) if run_dir else None
    results.append((eval_result, eval_artifacts))
    return results


def execute_specs(
    specs: list[RunSpec],
    *,
    args: argparse.Namespace,
    backend_registry: dict[str, Any],
    run_dir: Path | None,
) -> list[tuple[RunResult, dict[str, str] | None]]:
    if not specs:
        return []

    max_workers = min(args.jobs, len(specs))
    if max_workers == 1:
        ordered_results: list[tuple[RunResult, dict[str, str] | None]] = []
        for spec_index, spec in enumerate(specs, start=1):
            ordered_results.extend(
                run_spec_pipeline(
                    spec,
                    spec_index,
                    args=args,
                    backend_registry=backend_registry,
                    run_dir=run_dir,
                )
            )
        return ordered_results

    futures: list[Future[list[tuple[RunResult, dict[str, str] | None]]]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for spec_index, spec in enumerate(specs, start=1):
            futures.append(
                executor.submit(
                    run_spec_pipeline,
                    spec,
                    spec_index,
                    args=args,
                    backend_registry=backend_registry,
                    run_dir=run_dir,
                )
            )

        ordered_results = []
        for future in futures:
            ordered_results.extend(future.result())
        return ordered_results


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        validate_args(args)
        if args.suite:
            specs, suite_path, run_label = resolve_suite_specs(args)
        else:
            specs, suite_path, run_label = resolve_direct_specs(args)
        backend_registry = build_backend_registry(specs, args)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    run_dir = ensure_run_dir(args.save_dir, run_label)
    results = execute_specs(
        specs,
        args=args,
        backend_registry=backend_registry,
        run_dir=run_dir,
    )

    for result, _ in results:
        print_result(result)

    if run_dir is not None:
        save_summary(run_dir, suite_path, results)
        print(f"saved_results: {run_dir}")

    return 0 if all(result_is_success(result) for result, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
