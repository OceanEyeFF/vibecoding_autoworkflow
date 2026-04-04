#!/usr/bin/env python3
"""Thin P2 autoresearch loop wrapper for continuous single-prompt Codex rounds."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from autoresearch_contract import resolve_p2_contract_target
from autoresearch_mutation_registry import (
    build_registry_payload,
    canonicalize_mutation_entry,
    write_mutation_registry,
)
from autoresearch_stop import AutoresearchStop
from autoresearch_worker_contract import load_worker_contract_payload
from backends import CODEX_REASONING_EFFORTS, build_backend
from run_autoresearch import (
    REPO_ROOT,
    build_worktree_manager,
    cmd_baseline,
    cmd_decide_round,
    cmd_init,
    cmd_prepare_round,
    cmd_run_round,
    load_contract_for_cli,
    read_runtime_if_present,
    run_dir_for_id,
)
from run_skill_suite import cleanup_backend_artifacts, coerce_process_output
from worktree_manager import read_json, write_json


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the lightweight P2 single-prompt Codex autoresearch loop continuously until "
            "prepare-round stop gates or max_rounds halt further progress."
        )
    )
    parser.add_argument("--contract", type=Path, required=True, help="Path to autoresearch contract JSON.")
    first_round_group = parser.add_mutually_exclusive_group(required=False)
    first_round_group.add_argument(
        "--mutation-key",
        type=str,
        help="Optional mutation key override for the first prepared round only.",
    )
    first_round_group.add_argument(
        "--mutation",
        type=Path,
        help="Optional manual mutation spec for the first prepared round only.",
    )
    parser.add_argument(
        "--registry-seed",
        type=Path,
        help=(
            "Optional registry seed JSON used to initialize the run-local mutation-registry.json "
            "when it does not already exist."
        ),
    )
    parser.add_argument(
        "--model",
        help="Optional model override passed to the Codex worker for prompt mutation.",
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
        "--codex-reasoning-effort",
        choices=CODEX_REASONING_EFFORTS,
        default="high",
        help="Codex reasoning effort. Defaults to high.",
    )
    return parser.parse_args(argv if argv is not None else sys.argv[1:])


def _ensure_p2_contract(contract: Any) -> None:
    if resolve_p2_contract_target(contract) is None:
        raise ValueError("run_autoresearch_loop.py only supports P2 single-prompt contracts.")


def _git_output(repo_path: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _changed_files(candidate_worktree: Path) -> list[str]:
    changed_unstaged = [
        line.strip()
        for line in _git_output(candidate_worktree, "diff", "--name-only", "--relative").splitlines()
        if line.strip()
    ]
    changed_staged = [
        line.strip()
        for line in _git_output(candidate_worktree, "diff", "--name-only", "--relative", "--cached").splitlines()
        if line.strip()
    ]
    untracked = [
        line.strip()
        for line in _git_output(candidate_worktree, "ls-files", "--others", "--exclude-standard").splitlines()
        if line.strip()
    ]
    seen: set[str] = set()
    ordered: list[str] = []
    for path in [*changed_unstaged, *changed_staged, *untracked]:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def _validate_worker_diff(worker_contract: dict[str, Any]) -> list[str]:
    candidate_worktree = Path(str(worker_contract["candidate_worktree"])).expanduser().resolve()
    changed_files = _changed_files(candidate_worktree)
    target_paths = [str(path) for path in worker_contract.get("target_paths") or []]
    guardrails = dict(worker_contract.get("guardrails") or {})

    extra_files = [path for path in changed_files if path not in target_paths]
    if extra_files:
        raise RuntimeError(
            "Worker changed out-of-scope files: " + ", ".join(extra_files)
        )

    max_files_touched = guardrails.get("max_files_touched")
    if isinstance(max_files_touched, int) and max_files_touched > 0 and len(changed_files) > max_files_touched:
        raise RuntimeError(
            f"Worker changed {len(changed_files)} files, exceeding max_files_touched={max_files_touched}."
        )

    if bool(guardrails.get("require_non_empty_diff")) and not changed_files:
        raise RuntimeError("Worker produced no diff but the mutation requires a non-empty diff.")

    return changed_files


def build_worker_prompt(worker_contract_path: Path, worker_contract: dict[str, Any]) -> str:
    comparison_baseline = dict(worker_contract.get("comparison_baseline") or {})
    recent_feedback_excerpt = [str(item).strip() for item in worker_contract.get("recent_feedback_excerpt") or [] if str(item).strip()]
    aggregate_prompt_guidance = dict(worker_contract.get("aggregate_prompt_guidance") or {})
    target_paths = [str(path) for path in worker_contract.get("target_paths") or []]
    prompt_lines = [
        "You are executing one autoresearch worker round inside a candidate worktree.",
        "",
        "Read only what you need to mutate the target prompt file within the allowed scope.",
        "",
        f"Worker contract path: {worker_contract_path}",
        f"Round: {worker_contract['round']}",
        f"Mutation key: {worker_contract['mutation_key']}",
        f"Objective: {worker_contract['objective']}",
        f"Target surface: {worker_contract['target_surface']}",
        "",
        "Mutation instruction:",
        str(worker_contract["instruction"]),
        "",
        "Allowed target paths:",
    ]
    prompt_lines.extend(f"- {path}" for path in target_paths)
    prompt_lines.extend(
        [
            "",
            "Guardrails:",
            "- Only edit the allowed target path(s).",
            "- Do not create or modify any other file.",
            "- Keep the diff minimal and local to the mutation instruction.",
            "- Use exact repo-relative paths when the prompt needs path examples or contracts.",
            "- Do not write agent-report.md; the loop wrapper will write it after you finish.",
            "",
            "Comparison baseline:",
            f"- train_score: {comparison_baseline.get('train_score')}",
            f"- validation_score: {comparison_baseline.get('validation_score')}",
        ]
    )
    if recent_feedback_excerpt:
        prompt_lines.append("")
        prompt_lines.append("Recent feedback excerpt:")
        prompt_lines.extend(f"- {item}" for item in recent_feedback_excerpt)
    if aggregate_prompt_guidance:
        prompt_lines.append("")
        prompt_lines.append("Aggregate prompt guidance:")
        direction = str(aggregate_prompt_guidance.get("aggregate_direction") or "").strip()
        if direction:
            prompt_lines.append(f"- direction: {direction}")
        adjustments = [
            str(item).strip()
            for item in (aggregate_prompt_guidance.get("aggregate_suggested_adjustments") or [])
            if str(item).strip()
        ]
        if adjustments:
            prompt_lines.extend(f"- next: {item}" for item in adjustments[:3])
    prompt_lines.extend(
        [
            "",
            "Your task:",
            "1. Inspect the current target prompt file and the smallest amount of nearby repo evidence you need.",
            "2. Apply one scoped prompt mutation aligned with the mutation instruction.",
            "3. Leave all non-target files untouched.",
            "4. Respond with concise markdown using exactly these sections:",
            "   - Scope",
            "   - Mutation Applied",
            "   - Expected Effect",
            "   - Validation Notes",
        ]
    )
    return "\n".join(prompt_lines).strip() + "\n"


def run_codex_worker(*, args: argparse.Namespace, worker_contract_path: Path, worker_contract: dict[str, Any]) -> str:
    backend = build_backend("codex", args)
    healthy, message = backend.healthcheck()
    if not healthy:
        raise RuntimeError(f"codex backend unavailable: {message}")

    candidate_worktree = Path(str(worker_contract["candidate_worktree"])).expanduser().resolve()
    prompt_text = build_worker_prompt(worker_contract_path, worker_contract)
    invocation = backend.build_skill_command(prompt_text=prompt_text, repo_path=candidate_worktree, model=args.model)
    try:
        completed = subprocess.run(
            invocation.command,
            cwd=candidate_worktree,
            input=invocation.stdin_text,
            capture_output=True,
            text=True,
            check=False,
        )
        raw_stdout = coerce_process_output(completed.stdout)
        raw_stderr = coerce_process_output(completed.stderr)
        if completed.returncode != 0:
            stderr = raw_stderr.strip() or raw_stdout.strip() or f"exit code {completed.returncode}"
            raise RuntimeError(f"Codex worker failed: {stderr}")
        return backend.extract_final_message(invocation, raw_stdout)
    finally:
        cleanup_backend_artifacts(invocation.cleanup_paths)


def write_agent_report(
    *,
    agent_report_path: Path,
    worker_contract: dict[str, Any],
    worker_summary: str,
    changed_files: list[str],
) -> None:
    lines = [
        "# Agent Report",
        "",
        "## Scope",
    ]
    if changed_files:
        lines.extend(f"- Edited `{path}`." for path in changed_files)
    else:
        lines.append("- No files changed.")
    lines.extend(
        [
            "",
            "## Worker Contract",
            f"- round: `{worker_contract['round']}`",
            f"- mutation_key: `{worker_contract['mutation_key']}`",
            "",
            "## Worker Summary",
            worker_summary.strip() or "No summary returned by Codex worker.",
        ]
    )
    agent_report_path.parent.mkdir(parents=True, exist_ok=True)
    agent_report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _ensure_initialized(contract_path: Path) -> None:
    cmd_init(contract_path)


def _ensure_baseline(contract_path: Path, run_dir: Path) -> None:
    if (run_dir / "scoreboard.json").is_file():
        return
    cmd_baseline(contract_path)


def _ensure_registry_seed(contract: Any, run_dir: Path, seed_path: Path | None) -> None:
    if seed_path is None:
        return
    registry_path = run_dir / "mutation-registry.json"
    if registry_path.exists():
        return

    payload = json.loads(seed_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Registry seed must be a JSON object.")
    entries_raw = payload.get("entries")
    if not isinstance(entries_raw, list) or not entries_raw:
        raise ValueError("Registry seed must contain a non-empty 'entries' array.")

    canonical_entries = [
        canonicalize_mutation_entry(entry, repo_root=REPO_ROOT, contract=contract)
        for entry in entries_raw
    ]
    registry_payload = build_registry_payload(
        contract=contract,
        entries=canonical_entries,
        registry_version=payload.get("registry_version", 1),
    )
    write_mutation_registry(registry_path, registry_payload)


def _execute_worker_for_active_round(args: argparse.Namespace, contract: Any) -> tuple[int, list[str]]:
    manager = build_worktree_manager()
    active = manager.load_active_round(contract.run_id)
    round_payload = active["round"]
    state = str(round_payload.get("state") or "")
    if state != "candidate_active":
        raise RuntimeError(f"Active round is not ready for worker mutation: state={state}")
    round_number = int(round_payload["round"])
    round_dir = manager.round_dir(contract.run_id, round_number)
    worker_contract_path = round_dir / "worker-contract.json"
    worker_contract = load_worker_contract_payload(worker_contract_path)
    worker_summary = run_codex_worker(args=args, worker_contract_path=worker_contract_path, worker_contract=worker_contract)
    changed_files = _validate_worker_diff(worker_contract)
    write_agent_report(
        agent_report_path=Path(str(worker_contract["agent_report_path"])),
        worker_contract=worker_contract,
        worker_summary=worker_summary,
        changed_files=changed_files,
    )
    return round_number, changed_files


def _read_active_round_state(contract: Any) -> str | None:
    runtime = read_runtime_if_present(build_worktree_manager(), contract.run_id)
    if runtime is None or runtime.get("active_round") is None:
        return None
    active_round = int(runtime["active_round"])
    round_path = build_worktree_manager().round_path(contract.run_id, active_round)
    round_payload = read_json(round_path)
    return str(round_payload.get("state") or "")


def _recover_prepared_active_round(contract: Any) -> str:
    manager = build_worktree_manager()
    runtime = read_runtime_if_present(manager, contract.run_id)
    if runtime is None or runtime.get("active_round") is None:
        raise RuntimeError("Missing runtime active_round while recovering prepared round.")

    round_number = int(runtime["active_round"])
    round_path = manager.round_path(contract.run_id, round_number)
    if not round_path.is_file():
        raise RuntimeError("Active round is missing round.json. Run cleanup-round before retrying.")
    round_payload = read_json(round_path)
    state = str(round_payload.get("state") or "")
    if state != "prepared":
        return state

    worktree_path_record = manager.worktree_path_record(contract.run_id, round_number)
    if not worktree_path_record.is_file():
        raise RuntimeError("Active round is missing worktree.json. Run cleanup-round before retrying.")
    worktree_payload = read_json(worktree_path_record)

    candidate_branch = str(
        round_payload.get("candidate_branch")
        or worktree_payload.get("candidate_branch")
        or runtime.get("active_candidate_branch")
        or ""
    )
    candidate_worktree_raw = str(
        round_payload.get("candidate_worktree")
        or worktree_payload.get("path")
        or runtime.get("active_candidate_worktree")
        or ""
    )
    candidate_worktree = Path(candidate_worktree_raw).expanduser().resolve() if candidate_worktree_raw else Path()
    if not candidate_branch or not manager.branch_exists(candidate_branch):
        raise RuntimeError(
            "Active round is in prepared state but candidate branch is missing. Run cleanup-round before retrying."
        )
    if not candidate_worktree.is_dir():
        raise RuntimeError(
            "Active round is in prepared state but candidate worktree is missing. Run cleanup-round before retrying."
        )

    candidate_sha = manager.ref_sha(candidate_branch)
    round_payload["state"] = "candidate_active"
    round_payload["candidate_sha"] = candidate_sha
    round_payload["candidate_branch"] = candidate_branch
    round_payload["candidate_worktree"] = str(candidate_worktree)
    write_json(round_path, round_payload)

    worktree_payload = dict(worktree_payload)
    worktree_payload["path"] = str(candidate_worktree)
    worktree_payload["candidate_branch"] = candidate_branch
    worktree_payload["candidate_sha"] = candidate_sha
    write_json(worktree_path_record, worktree_payload)
    runtime["active_candidate_branch"] = candidate_branch
    runtime["active_candidate_worktree"] = str(candidate_worktree)
    manager.save_runtime(contract.run_id, runtime)
    return "candidate_active"


def run_loop(args: argparse.Namespace) -> int:
    contract = load_contract_for_cli(args.contract, enforce_p2_preflight=True)
    _ensure_p2_contract(contract)
    run_dir = run_dir_for_id(contract.run_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    _ensure_initialized(args.contract)
    _ensure_baseline(args.contract, run_dir)
    _ensure_registry_seed(contract, run_dir, args.registry_seed)

    first_prepare = True
    rounds_completed = 0
    while True:
        active_state = _read_active_round_state(contract)
        if active_state is None:
            try:
                cmd_prepare_round(
                    args.contract,
                    mutation_key=args.mutation_key if first_prepare else None,
                    mutation_path=args.mutation if first_prepare else None,
                )
            except AutoresearchStop as exc:
                print("loop_status: stopped")
                print(f"stop_kind: {exc.kind}")
                print(f"stop_reason: {exc.message}")
                print(f"rounds_completed_in_loop: {rounds_completed}")
                return 0
            first_prepare = False
            active_state = _read_active_round_state(contract)
        else:
            first_prepare = False

        if active_state == "prepared":
            active_state = _recover_prepared_active_round(contract)

        if active_state == "candidate_active":
            round_number, changed_files = _execute_worker_for_active_round(args, contract)
            print(f"worker_round: {round_number}")
            print("worker_changed_files: " + (", ".join(changed_files) if changed_files else "-"))
            cmd_run_round(args.contract)
            active_state = _read_active_round_state(contract)

        if active_state == "evaluated":
            cmd_decide_round(args.contract)
            rounds_completed += 1
            continue

        if active_state is None:
            continue

        raise RuntimeError(f"Unsupported active round state in loop wrapper: {active_state}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return run_loop(args)
    except (FileNotFoundError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
