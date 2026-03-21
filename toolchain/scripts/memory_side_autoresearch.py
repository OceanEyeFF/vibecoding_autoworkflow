#!/usr/bin/env python3
"""Minimal Auto Research-style benchmark runner for Memory Side adapters."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_ROOT = REPO_ROOT / "toolchain" / "evals" / "memory-side"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / ".autoworkflow" / "memory-side-autoresearch"
DEFAULT_PROGRAM = EVAL_ROOT / "program.md"
DEFAULT_SCENARIOS = EVAL_ROOT / "scenarios.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_scenarios(path: Path) -> dict[str, dict[str, Any]]:
    data = load_json(path)
    return {item["id"]: item for item in data["scenarios"]}


def build_prompt(program_text: str, scenario: dict[str, Any], backend: str) -> str:
    adapter_path = {
        "codex": f".agents/skills/{scenario['skill']}/",
        "claude": f".claude/skills/{scenario['skill']}/",
    }[backend]

    prompt_lines = [
        program_text.strip(),
        "",
        "## Benchmark Run",
        f"backend: {backend}",
        f"scenario_id: {scenario['id']}",
        f"skill: {scenario['skill']}",
        f"adapter_path: {adapter_path}",
        "",
        "## Run Mode",
        "This is an evaluation-only run.",
        "Do not edit files.",
        "Do not install dependencies.",
        "Do not create commits.",
        "Read only the minimum repo files needed.",
        "Use the repo-local adapter skill for the target backend.",
        "Return only a JSON object matching the supplied schema.",
        "Do not wrap the JSON in markdown fences.",
        "",
        "## Scenario",
        f"title: {scenario['title']}",
        f"goal: {scenario['goal']}",
        "user_request:",
        scenario["user_request"],
    ]
    return "\n".join(prompt_lines) + "\n"


def build_codex_command(
    prompt: str,
    response_path: Path,
    schema_path: Path,
    model: str | None,
) -> list[str]:
    cmd = [
        "codex",
        "exec",
        "-C",
        str(REPO_ROOT),
        "-s",
        "read-only",
        "--skip-git-repo-check",
        "--output-schema",
        str(schema_path),
        "-o",
        str(response_path),
    ]
    if model:
        cmd.extend(["-m", model])
    cmd.append(prompt)
    return cmd


def build_claude_command(
    prompt: str,
    schema_path: Path,
    model: str | None,
) -> list[str]:
    schema_text = schema_path.read_text(encoding="utf-8")
    cmd = [
        "claude",
        "-p",
        "--output-format",
        "text",
        "--no-session-persistence",
        "--permission-mode",
        "dontAsk",
        "--tools",
        "Read,Grep,Glob,Bash",
        "--json-schema",
        schema_text,
    ]
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)
    return cmd


def try_parse_json(raw_text: str) -> tuple[Any | None, str | None]:
    try:
        return json.loads(raw_text), None
    except json.JSONDecodeError as exc:
        return None, str(exc)


def run_command(
    cmd: list[str],
    stdout_path: Path,
    stderr_path: Path,
    timeout_sec: int,
) -> tuple[int | None, float, str | None]:
    started = time.time()
    timeout_error = None
    with stdout_path.open("w", encoding="utf-8") as stdout_file:
        with stderr_path.open("w", encoding="utf-8") as stderr_file:
            try:
                completed = subprocess.run(
                    cmd,
                    cwd=REPO_ROOT,
                    text=True,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    timeout=timeout_sec,
                    check=False,
                )
                return completed.returncode, time.time() - started, timeout_error
            except subprocess.TimeoutExpired:
                timeout_error = f"Timed out after {timeout_sec} seconds"
                return None, time.time() - started, timeout_error


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_scenario(
    backend: str,
    scenario: dict[str, Any],
    program_path: Path,
    output_root: Path,
    timeout_sec: int,
    model: str | None,
    dry_run: bool,
) -> dict[str, Any]:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = ensure_dir(output_root / f"{timestamp}-{backend.lower()}-{scenario['id'].lower()}")
    prompt_path = run_dir / "prompt.txt"
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    response_path = run_dir / "response.txt"
    parsed_path = run_dir / "parsed.json"
    manifest_path = run_dir / "manifest.json"

    program_text = program_path.read_text(encoding="utf-8")
    prompt = build_prompt(program_text, scenario, backend)
    prompt_path.write_text(prompt, encoding="utf-8")

    schema_path = EVAL_ROOT / scenario["schema_file"]
    if backend == "codex":
        cmd = build_codex_command(prompt, response_path, schema_path, model)
    elif backend == "claude":
        cmd = build_claude_command(prompt, schema_path, model)
    else:
        raise ValueError(f"Unsupported backend: {backend}")

    manifest: dict[str, Any] = {
        "backend": backend,
        "scenario_id": scenario["id"],
        "skill": scenario["skill"],
        "title": scenario["title"],
        "goal": scenario["goal"],
        "program_path": str(program_path.relative_to(REPO_ROOT)),
        "schema_path": str(schema_path.relative_to(REPO_ROOT)),
        "prompt_path": str(prompt_path.relative_to(REPO_ROOT)),
        "stdout_path": str(stdout_path.relative_to(REPO_ROOT)),
        "stderr_path": str(stderr_path.relative_to(REPO_ROOT)),
        "response_path": str(response_path.relative_to(REPO_ROOT)),
        "parsed_path": str(parsed_path.relative_to(REPO_ROOT)),
        "command": cmd,
        "dry_run": dry_run,
    }

    if dry_run:
        manifest["status"] = "dry-run"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return manifest

    returncode, duration_sec, timeout_error = run_command(
        cmd,
        stdout_path,
        stderr_path,
        timeout_sec,
    )

    if backend == "claude":
        raw_response = stdout_path.read_text(encoding="utf-8")
        response_path.write_text(raw_response, encoding="utf-8")
    else:
        raw_response = response_path.read_text(encoding="utf-8") if response_path.exists() else ""

    parsed_output, parse_error = try_parse_json(raw_response)
    if parsed_output is not None:
        parsed_path.write_text(
            json.dumps(parsed_output, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if timeout_error is not None:
        status = "timeout"
    elif returncode != 0:
        status = "failed"
    elif parse_error is not None:
        status = "invalid-output"
    else:
        status = "completed"

    manifest.update(
        {
            "status": status,
            "exit_code": returncode,
            "duration_sec": round(duration_sec, 3),
            "timeout_error": timeout_error,
            "response_bytes": len(raw_response.encode("utf-8")),
            "json_parse_error": parse_error,
        }
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def print_scenarios(scenarios: dict[str, dict[str, Any]]) -> None:
    for scenario_id in sorted(scenarios):
        item = scenarios[scenario_id]
        print(f"{item['id']}\t{item['skill']}\t{item['title']}")


def resolve_scenario_ids(
    scenarios: dict[str, dict[str, Any]],
    requested_ids: list[str],
    run_all: bool,
) -> list[str]:
    if run_all:
        return sorted(scenarios)
    if not requested_ids:
        raise SystemExit("No scenarios selected. Use --scenario or --all-scenarios.")
    missing = [item for item in requested_ids if item not in scenarios]
    if missing:
        raise SystemExit(f"Unknown scenario ids: {', '.join(missing)}")
    return requested_ids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Auto Research-style Memory Side benchmark scenarios."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available scenarios")
    list_parser.add_argument(
        "--scenarios",
        type=Path,
        default=DEFAULT_SCENARIOS,
        help="Path to the scenario catalog JSON file.",
    )

    run_parser = subparsers.add_parser("run", help="Run one or more scenarios")
    run_parser.add_argument(
        "--backend",
        choices=["codex", "claude"],
        action="append",
        required=True,
        help="Backend to run. Repeat to run multiple backends.",
    )
    run_parser.add_argument(
        "--scenario",
        action="append",
        default=[],
        help="Scenario id to run. Repeatable.",
    )
    run_parser.add_argument(
        "--all-scenarios",
        action="store_true",
        help="Run every scenario in the catalog.",
    )
    run_parser.add_argument(
        "--scenarios",
        type=Path,
        default=DEFAULT_SCENARIOS,
        help="Path to the scenario catalog JSON file.",
    )
    run_parser.add_argument(
        "--program",
        type=Path,
        default=DEFAULT_PROGRAM,
        help="Path to the editable benchmark program.md file.",
    )
    run_parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Directory where run artifacts are stored.",
    )
    run_parser.add_argument(
        "--timeout-sec",
        type=int,
        default=600,
        help="Per-run timeout in seconds.",
    )
    run_parser.add_argument(
        "--model",
        help="Optional model override passed to the backend CLI.",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write prompts and manifests without executing the backend command.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenarios = load_scenarios(args.scenarios)

    if args.command == "list":
        print_scenarios(scenarios)
        return 0

    scenario_ids = resolve_scenario_ids(
        scenarios,
        requested_ids=args.scenario,
        run_all=args.all_scenarios,
    )

    output_root = ensure_dir(args.output_root)
    manifests = []
    for backend in args.backend:
        for scenario_id in scenario_ids:
            manifest = run_scenario(
                backend=backend,
                scenario=scenarios[scenario_id],
                program_path=args.program,
                output_root=output_root,
                timeout_sec=args.timeout_sec,
                model=args.model,
                dry_run=args.dry_run,
            )
            manifests.append(manifest)
            status = manifest["status"]
            print(f"{backend}\t{scenario_id}\t{status}\t{manifest['response_path']}")

    summary_path = ensure_dir(output_root) / "last-run-summary.json"
    summary_path.write_text(
        json.dumps(manifests, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
