#!/usr/bin/env python3
"""Autoresearch entrypoint for P0.1-P1.3 baseline, worktree, round, and feedback flows."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from backend_runner import retry_policy_cli_args
from autoresearch_contract import (
    HISTORY_COLUMNS,
    P2_RUNNER_TASK_TO_TARGET_TASK,
    P2_TARGET_TASK_TO_RUNNER_TASK,
    P2_TARGET_TASK_TO_PROMPT_PATH,
    history_header,
    load_contract,
    resolve_timeout_seconds,
    resolve_p2_contract_target,
    resolve_suite_files,
)
from autoresearch_status import refresh_status_indexes
from autoresearch_lane_executor import execute_lane_suites
from autoresearch_round import AutoresearchRoundManager
from autoresearch_scoreboard import build_scoreboard, merge_run_summaries, write_scoreboard
from autoresearch_mutation_registry import (
    build_registry_payload,
    find_registry_entry,
    import_manual_mutation_as_registry_entry,
    load_mutation_registry,
    materialize_round_mutation,
    upsert_registry_entry,
    write_mutation_registry,
)
from autoresearch_selector import select_next_mutation_entry
from autoresearch_prepare_round_stop import prepare_round_stop_reason
from autoresearch_feedback_distill import (
    build_recent_feedback_excerpt,
    latest_aggregate_prompt_guidance,
    load_feedback_ledger,
)
from autoresearch_stop import AutoresearchStop, format_stop_status
from autoresearch_worker_contract import build_comparison_baseline
from exrepo_routing_entry import (
    STATUS_USABLE,
    build_context_routing_capability_report_payload,
    collect_context_routing_suite_repo_skill_report,
    format_context_routing_capability_lines,
    prompt_allows_exrepo_routing_fallback,
    write_context_routing_capability_report,
)
from exrepo_runtime import materialize_suite
from worktree_manager import read_json
from common import REPO_ROOT, slugify
from run_skill_suite import load_suite_manifest, main as run_skill_suite_main, resolve_path_override
from worktree_manager import WorktreeManager, champion_branch_name


AUTORESEARCH_ROOT = REPO_ROOT / ".autoworkflow" / "autoresearch"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run autoresearch P0.1 baseline data-plane, P0.2 worktree shell, and P0.3 round loop flows."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize autoresearch run state from a contract.")
    init_parser.add_argument("--contract", type=Path, required=True, help="Path to autoresearch contract JSON.")

    baseline_parser = subparsers.add_parser("baseline", help="Run baseline train/validation suites and aggregate.")
    baseline_parser.add_argument("--contract", type=Path, required=True, help="Path to autoresearch contract JSON.")

    prepare_parser = subparsers.add_parser(
        "prepare-round",
        help="Create one candidate branch/worktree and write round runtime state.",
    )
    prepare_parser.add_argument("--contract", type=Path, required=True, help="Path to autoresearch contract JSON.")
    prepare_group = prepare_parser.add_mutually_exclusive_group(required=False)
    prepare_group.add_argument(
        "--mutation-key",
        type=str,
        help="Mutation key to materialize from the run-local mutation-registry.json.",
    )
    prepare_group.add_argument(
        "--mutation",
        type=Path,
        help="Path to a manual mutation JSON spec (legacy-compatible; imported into the registry).",
    )

    run_round_parser = subparsers.add_parser(
        "run-round",
        help="Commit candidate edits, run train/validation suites from the candidate worktree, and write round artifacts.",
    )
    run_round_parser.add_argument("--contract", type=Path, required=True, help="Path to autoresearch contract JSON.")

    decide_parser = subparsers.add_parser(
        "decide-round",
        help="Apply fixed keep/discard rules, write decision.json, and promote or discard the active candidate.",
    )
    decide_parser.add_argument("--contract", type=Path, required=True, help="Path to autoresearch contract JSON.")

    promote_parser = subparsers.add_parser(
        "promote-round",
        help="Fast-forward champion to the active candidate and clean up candidate state.",
    )
    promote_parser.add_argument("--contract", type=Path, required=True, help="Path to autoresearch contract JSON.")

    discard_parser = subparsers.add_parser(
        "discard-round",
        help="Discard the active candidate by removing its branch/worktree without revert noise.",
    )
    discard_parser.add_argument("--contract", type=Path, required=True, help="Path to autoresearch contract JSON.")

    cleanup_parser = subparsers.add_parser(
        "cleanup-round",
        help="Recover from an interrupted active round by cleaning recorded candidate state.",
    )
    cleanup_parser.add_argument("--contract", type=Path, required=True, help="Path to autoresearch contract JSON.")

    subparsers.add_parser(
        "refresh-status",
        help="Rebuild aggregate run and per-skill status indexes under .autoworkflow/autoresearch/.",
    )
    return parser.parse_args(argv)


def run_dir_for_id(run_id: str) -> Path:
    return AUTORESEARCH_ROOT / slugify(run_id)


def ensure_history_file(history_path: Path) -> None:
    if history_path.exists():
        return
    history_path.write_text(history_header() + "\n", encoding="utf-8")


def write_canonical_contract(run_dir: Path, payload: dict[str, object]) -> None:
    (run_dir / "contract.json").write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def resolve_head_sha() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def build_worktree_manager() -> WorktreeManager:
    return WorktreeManager(repo_root=REPO_ROOT, autoresearch_root=AUTORESEARCH_ROOT)


def build_round_manager() -> AutoresearchRoundManager:
    return AutoresearchRoundManager(repo_root=REPO_ROOT, autoresearch_root=AUTORESEARCH_ROOT)


def _default_prompt_path_for_runner_task(task_name: str) -> Path:
    runner_task = P2_TARGET_TASK_TO_RUNNER_TASK.get(task_name, task_name)
    target_task = P2_RUNNER_TASK_TO_TARGET_TASK.get(runner_task)
    if target_task is None:
        raise ValueError(f"P2 suite task is not supported: {task_name}")
    return (REPO_ROOT / P2_TARGET_TASK_TO_PROMPT_PATH[target_task]).resolve()


def _iter_suite_specs_for_p2(suite_path: Path) -> list[dict[str, Any]]:
    manifest = load_suite_manifest(suite_path)
    version = manifest.get("version", 1)
    if version != 1:
        raise ValueError(f"Unsupported suite manifest version for P2 preflight: {version}")
    defaults = manifest.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise ValueError("Suite manifest 'defaults' must be a mapping when present.")
    runs = manifest.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("Suite manifest must define a non-empty 'runs' list.")

    resolved_specs: list[dict[str, Any]] = []
    for index, run_entry in enumerate(runs, start=1):
        if not isinstance(run_entry, dict):
            raise ValueError(f"Suite run #{index} must be a mapping.")
        task_name = str(run_entry.get("task") or "all").strip()
        backend = str(run_entry.get("backend") or defaults.get("backend") or "").strip()
        judge_backend = str(run_entry.get("judge_backend") or defaults.get("judge_backend") or backend).strip()
        if not backend:
            raise ValueError(f"Suite run #{index} is missing 'backend'.")
        prompt_override = resolve_path_override(run_entry.get("prompt_file"), suite_path.parent)
        if task_name == "all":
            if prompt_override is not None:
                raise ValueError("P2 suite preflight does not allow prompt_file override with task=all.")
            task_names = sorted(P2_RUNNER_TASK_TO_TARGET_TASK)
        else:
            task_names = [P2_TARGET_TASK_TO_RUNNER_TASK.get(task_name, task_name)]
        for resolved_task in task_names:
            resolved_specs.append(
                {
                    "task": resolved_task,
                    "backend": backend,
                    "judge_backend": judge_backend,
                    "prompt_file": (
                        prompt_override.resolve()
                        if prompt_override is not None
                        else _default_prompt_path_for_runner_task(resolved_task)
                    ),
                }
            )
    return resolved_specs


def _validate_p2_preflight(contract) -> None:
    build_round_manager().validate_p2_preflight(contract)


def load_contract_for_cli(path: Path, *, enforce_p2_preflight: bool) -> Any:
    contract = load_contract(path, repo_root=REPO_ROOT)
    if enforce_p2_preflight:
        _validate_p2_preflight(contract)
    return contract


def read_runtime_if_present(manager: WorktreeManager, run_id: str) -> dict[str, object] | None:
    runtime_path = manager.runtime_path(run_id)
    if not runtime_path.is_file():
        return None
    return read_json(runtime_path)


def sync_runtime_to_baseline(run_id: str, base_sha: str) -> None:
    manager = build_worktree_manager()
    runtime = manager.load_runtime(run_id)
    if runtime.get("active_round") is not None:
        raise RuntimeError("Cannot run baseline while an active round exists.")
    runtime["champion_branch"] = champion_branch_name(run_id)
    runtime["champion_sha"] = base_sha
    runtime["active_round"] = None
    runtime["active_candidate_branch"] = None
    runtime["active_candidate_worktree"] = None
    manager.save_runtime(run_id, runtime)


def run_lane_suites(
    suite_files: list[Path],
    save_dir: Path,
    *,
    timeout_seconds: int,
    retry_policy,
) -> list[dict[str, object]]:
    def _run_suite(suite_file: Path) -> None:
        exit_code = run_skill_suite_main(
            [
                "--suite",
                str(suite_file),
                "--save-dir",
                str(save_dir),
                "--timeout",
                str(timeout_seconds),
                *retry_policy_cli_args(retry_policy),
            ]
        )
        if exit_code != 0:
            raise RuntimeError(f"Suite failed: {suite_file}")

    return execute_lane_suites(suite_files, save_dir, run_suite=_run_suite)


def materialize_lane_suites(
    suite_files: list[Path],
    output_dir: Path,
    *,
    repo_root: Path = REPO_ROOT,
) -> list[Path]:
    return [materialize_suite(suite_file, output_dir, repo_root=repo_root) for suite_file in suite_files]


def _run_context_routing_exrepo_preflight(
    contract,
    *,
    suite_files: list[Path],
    run_dir: Path,
) -> None:
    resolved_target = resolve_p2_contract_target(contract)
    if resolved_target is None:
        return
    target_task, target_prompt_path = resolved_target
    if target_task != "context-routing-skill":
        return

    prompt_path = (REPO_ROOT / target_prompt_path).resolve()
    capabilities = collect_context_routing_suite_repo_skill_report(suite_files, repo_root=REPO_ROOT)
    if not capabilities:
        return
    report_payload = build_context_routing_capability_report_payload(
        prompt_path=prompt_path,
        capabilities=capabilities,
    )
    report_path = run_dir / "routing-entry-capability.json"
    write_context_routing_capability_report(report_path, report_payload)
    for line in format_context_routing_capability_lines(capabilities):
        print(line)

    if prompt_allows_exrepo_routing_fallback(prompt_path):
        return

    blocking = [
        item
        for item in capabilities
        if str(item.get("status") or "").strip() != STATUS_USABLE
    ]
    if blocking:
        details = ", ".join(f"{item['repo']}={item['status']}" for item in blocking)
        raise RuntimeError(
            "Exrepo routing-entry preflight failed: "
            f"{details}. See {report_path}"
        )


def append_history_baseline_row(
    history_path: Path,
    *,
    base_sha: str,
    train_score: float,
    validation_score: float,
    train_parse_error_rate: float,
    validation_parse_error_rate: float,
) -> None:
    values = {
        "round": "0",
        "kind": "baseline",
        "base_sha": base_sha,
        "candidate_sha": "-",
        "train_score": f"{train_score:.6f}",
        "validation_score": f"{validation_score:.6f}",
        "train_parse_error_rate": f"{train_parse_error_rate:.6f}",
        "validation_parse_error_rate": f"{validation_parse_error_rate:.6f}",
        "decision": "baseline",
        "notes": "",
    }
    row = "\t".join(values[column] for column in HISTORY_COLUMNS)
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(row + "\n")


def cmd_init(contract_path: Path) -> int:
    contract = load_contract_for_cli(contract_path, enforce_p2_preflight=True)
    run_dir = run_dir_for_id(contract.run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    write_canonical_contract(run_dir, contract.payload)
    ensure_history_file(run_dir / "history.tsv")
    build_worktree_manager().load_runtime(contract.run_id)
    print(f"initialized_run: {run_dir}")
    return 0


def cmd_baseline(contract_path: Path) -> int:
    contract = load_contract_for_cli(contract_path, enforce_p2_preflight=True)
    run_dir = run_dir_for_id(contract.run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    write_canonical_contract(run_dir, contract.payload)

    history_path = run_dir / "history.tsv"
    ensure_history_file(history_path)

    base_sha = resolve_head_sha()
    sync_runtime_to_baseline(contract.run_id, base_sha)

    suites = resolve_suite_files(contract)
    timeout_seconds = resolve_timeout_seconds(contract)
    retry_policy = contract.retry_policy
    _run_context_routing_exrepo_preflight(
        contract,
        suite_files=[*suites["train"], *suites["validation"]],
        run_dir=run_dir,
    )
    materialized_root = run_dir / "baseline" / "materialized-suites"
    materialized_train_suites = materialize_lane_suites(
        suites["train"],
        materialized_root / "train",
        repo_root=REPO_ROOT,
    )
    materialized_validation_suites = materialize_lane_suites(
        suites["validation"],
        materialized_root / "validation",
        repo_root=REPO_ROOT,
    )
    train_summaries = run_lane_suites(
        materialized_train_suites,
        run_dir / "baseline" / "train",
        timeout_seconds=timeout_seconds,
        retry_policy=retry_policy,
    )
    validation_summaries = run_lane_suites(
        materialized_validation_suites,
        run_dir / "baseline" / "validation",
        timeout_seconds=timeout_seconds,
        retry_policy=retry_policy,
    )
    lane_summaries = {
        "train": merge_run_summaries(train_summaries),
        "validation": merge_run_summaries(validation_summaries),
    }
    scoreboard = build_scoreboard(run_id=contract.run_id, baseline_sha=base_sha, lane_summaries=lane_summaries)
    write_scoreboard(run_dir / "scoreboard.json", scoreboard)
    build_worktree_manager().refresh_champion_branch(contract.run_id, base_sha)

    train_lane = next((lane for lane in scoreboard["lanes"] if lane["lane_name"] == "train"), {})
    validation_lane = next((lane for lane in scoreboard["lanes"] if lane["lane_name"] == "validation"), {})
    append_history_baseline_row(
        history_path,
        base_sha=base_sha,
        train_score=float(train_lane.get("avg_total_score") or 0.0),
        validation_score=float(validation_lane.get("avg_total_score") or 0.0),
        train_parse_error_rate=float(train_lane.get("parse_error_rate") or 0.0),
        validation_parse_error_rate=float(validation_lane.get("parse_error_rate") or 0.0),
    )
    print(f"baseline_completed: {run_dir}")
    return 0


def cmd_prepare_round(
    contract_path: Path,
    *,
    mutation_key: str | None,
    mutation_path: Path | None,
) -> int:
    contract = load_contract_for_cli(contract_path, enforce_p2_preflight=True)
    run_dir = run_dir_for_id(contract.run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    write_canonical_contract(run_dir, contract.payload)
    ensure_history_file(run_dir / "history.tsv")
    round_manager = build_round_manager()
    manager = build_worktree_manager()
    baseline_scoreboard = read_json(run_dir / "scoreboard.json")
    recovery = round_manager.reconcile_prepare_state(contract)
    if recovery is not None:
        print(
            "[P1] prepare_recovery: reconciled active round {}, restored mutation/worker artifacts and verified registry bookkeeping".format(
                recovery["round"]
            )
        )

    registry_path = run_dir / "mutation-registry.json"
    registry = (
        load_mutation_registry(registry_path, contract=contract, repo_root=REPO_ROOT)
        if registry_path.is_file()
        else None
    )
    feedback_ledger = load_feedback_ledger(run_dir / "feedback-ledger.jsonl")
    runtime = read_runtime_if_present(manager, contract.run_id)
    if runtime is None or runtime.get("active_round") is None:
        stop_info = prepare_round_stop_reason(run_dir=run_dir, registry=registry)
        if stop_info is not None:
            kind, stop_reason = stop_info
            raise AutoresearchStop(kind=kind, message=stop_reason)
    selection = None

    if mutation_key is not None:
        if registry is None:
            raise FileNotFoundError(f"Missing mutation registry: {registry_path}")
        try:
            entry = find_registry_entry(registry, mutation_key)
        except KeyError as exc:
            message = str(exc.args[0]) if exc.args else "mutation_key not found in registry."
            raise RuntimeError(message) from exc
    else:
        if mutation_path is None:
            if registry is None:
                raise FileNotFoundError(
                    "Missing mutation registry and no mutation specified. "
                    f"Expected: {registry_path} (or pass --mutation-key / --mutation)"
                )
            selection = select_next_mutation_entry(
                registry,
                contract=contract,
                runtime=runtime,
                comparison_baseline=baseline_scoreboard,
                feedback_ledger=feedback_ledger,
            )
            entry = selection.entry
        else:
            manual_payload = json.loads(mutation_path.read_text(encoding="utf-8"))
            if not isinstance(manual_payload, dict):
                raise ValueError("Manual mutation spec must be a JSON object.")
            imported = import_manual_mutation_as_registry_entry(
                manual_payload,
                contract=contract,
                repo_root=REPO_ROOT,
                origin_ref=str(mutation_path),
            )
            if registry is None:
                registry_payload = build_registry_payload(contract=contract, entries=[imported])
                write_mutation_registry(registry_path, registry_payload)
                registry = load_mutation_registry(registry_path, contract=contract, repo_root=REPO_ROOT)
            else:
                registry = upsert_registry_entry(registry=registry, entry=imported)
                registry_payload = dict(registry.payload)
                registry_payload["entries"] = registry.entries
                write_mutation_registry(registry_path, registry_payload)
                registry = load_mutation_registry(registry_path, contract=contract, repo_root=REPO_ROOT)
            entry = find_registry_entry(registry, str(imported.get("mutation_key") or ""))

    if str(entry.get("status")) != "active":
        raise RuntimeError(f"Selected mutation_key is not active: {entry.get('mutation_key')}")

    max_attempts_raw = contract.payload.get("max_candidate_attempts_per_round")
    if isinstance(max_attempts_raw, bool) or not isinstance(max_attempts_raw, int) or max_attempts_raw <= 0:
        raise ValueError("contract.payload.max_candidate_attempts_per_round must be a positive integer.")
    attempts_raw = entry.get("attempts") or 0
    if isinstance(attempts_raw, bool) or not isinstance(attempts_raw, int) or attempts_raw < 0:
        raise ValueError("Registry entry attempts must be a non-negative integer.")
    if attempts_raw >= max_attempts_raw:
        raise RuntimeError(f"Selected mutation_key has exhausted attempts: {entry.get('mutation_key')}")
    next_round = manager.next_round_number(contract.run_id)
    attempt = selection.attempt if selection is not None else attempts_raw + 1
    mutation_payload = materialize_round_mutation(entry=entry, round_number=next_round, attempt=attempt)
    round_manager.ensure_prepare_allowed(contract, mutation_payload)
    result = manager.prepare_round(contract.run_id)
    round_payload = result["round"]
    round_number = int(round_payload["round"])
    round_manager.stage_mutation(contract.run_id, round_number, mutation_payload)

    # Write back the updated registry attempts/selection bookkeeping.
    entry["attempts"] = attempt
    entry["last_selected_round"] = round_number
    comparison_baseline = build_comparison_baseline(baseline_scoreboard)
    recent_feedback_excerpt = build_recent_feedback_excerpt(feedback_ledger)
    aggregate_prompt_guidance = latest_aggregate_prompt_guidance(feedback_ledger)
    round_manager.stage_round_authority(
        contract.run_id,
        round_number,
        registry_entry=dict(entry),
        mutation_payload=mutation_payload,
        comparison_baseline=comparison_baseline,
        recent_feedback_excerpt=recent_feedback_excerpt,
        aggregate_prompt_guidance=aggregate_prompt_guidance,
    )
    print("[P1] authority_snapshot: round_authority staged for round {}".format(round_number))
    worker_contract_path = round_manager.stage_worker_contract(
        contract,
        round_payload=round_payload,
        mutation_payload=mutation_payload,
        comparison_baseline=comparison_baseline,
        recent_feedback_excerpt=recent_feedback_excerpt,
        aggregate_prompt_guidance=aggregate_prompt_guidance,
    )
    registry_payload = dict(registry.payload)
    registry_payload["entries"] = registry.entries
    write_mutation_registry(registry_path, registry_payload)
    print("[P1] registry_writeback: mutation_registry.json updated, attempts={}, last_selected_round={}".format(
        entry["attempts"], round_number))
    print(f"prepared_round: {round_payload['round']}")
    print(f"candidate_branch: {round_payload['candidate_branch']}")
    print(f"candidate_worktree: {round_payload['candidate_worktree']}")
    print(f"mutation_path: {round_manager.mutation_path(contract.run_id, round_number)}")
    print(f"worker_contract_path: {worker_contract_path}")
    print(f"agent_report_path: {round_manager.agent_report_path(contract.run_id, round_number)}")
    if selection is not None:
        print(f"scheduler_reason: {selection.scheduler_reason}")
        print(f"selection_reason: {selection.selection_reason}")
    return 0


def cmd_run_round(contract_path: Path) -> int:
    contract = load_contract_for_cli(contract_path, enforce_p2_preflight=True)
    result = build_round_manager().run_round(contract)
    round_payload = result["round"]
    scoreboard = result["scoreboard"]
    train_lane = next((lane for lane in scoreboard["lanes"] if lane["lane_name"] == "train"), {})
    validation_lane = next((lane for lane in scoreboard["lanes"] if lane["lane_name"] == "validation"), {})
    print(f"ran_round: {round_payload['round']}")
    print(f"candidate_sha: {round_payload['candidate_sha']}")
    print(f"train_score: {float(train_lane.get('avg_total_score') or 0.0):.6f}")
    print(f"validation_score: {float(validation_lane.get('avg_total_score') or 0.0):.6f}")
    return 0


def cmd_decide_round(contract_path: Path) -> int:
    contract = load_contract_for_cli(contract_path, enforce_p2_preflight=False)
    result = build_round_manager().decide_round(contract)
    decision = result["decision"]
    print(f"decided_round: {decision['round']}")
    print(f"decision: {decision['decision']}")
    print(f"candidate_sha: {decision['candidate_sha']}")
    return 0


def cmd_promote_round(contract_path: Path) -> int:
    contract = load_contract_for_cli(contract_path, enforce_p2_preflight=True)
    result = build_worktree_manager().promote_round(contract.run_id)
    runtime = result["runtime"]
    print(f"promoted_round: {result['round']['round']}")
    print(f"champion_sha: {runtime['champion_sha']}")
    return 0


def cmd_discard_round(contract_path: Path) -> int:
    contract = load_contract_for_cli(contract_path, enforce_p2_preflight=False)
    result = build_worktree_manager().discard_round(contract.run_id)
    print(f"discarded_round: {result['round']['round']}")
    return 0


def cmd_cleanup_round(contract_path: Path) -> int:
    contract = load_contract_for_cli(contract_path, enforce_p2_preflight=False)
    result = build_worktree_manager().cleanup_round(contract.run_id)
    print(f"cleaned_round: {result['round']['round']}")
    return 0


def cmd_refresh_status() -> int:
    run_index_path, skill_index_path = refresh_status_indexes(
        autoresearch_root=AUTORESEARCH_ROOT,
        repo_root=REPO_ROOT,
    )
    print(f"run_status_index: {run_index_path}")
    print(f"skill_training_status: {skill_index_path}")
    return 0


def _refresh_status_indexes_best_effort(command: str) -> None:
    try:
        refresh_status_indexes(
            autoresearch_root=AUTORESEARCH_ROOT,
            repo_root=REPO_ROOT,
        )
    except (FileNotFoundError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(
            f"warning: status index refresh skipped after {command}: {exc}",
            file=sys.stderr,
        )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        exit_code: int | None = None
        if args.command == "init":
            exit_code = cmd_init(args.contract)
        elif args.command == "baseline":
            exit_code = cmd_baseline(args.contract)
        elif args.command == "prepare-round":
            exit_code = cmd_prepare_round(
                args.contract,
                mutation_key=getattr(args, "mutation_key", None),
                mutation_path=getattr(args, "mutation", None),
            )
        elif args.command == "run-round":
            exit_code = cmd_run_round(args.contract)
        elif args.command == "decide-round":
            exit_code = cmd_decide_round(args.contract)
        elif args.command == "promote-round":
            exit_code = cmd_promote_round(args.contract)
        elif args.command == "discard-round":
            exit_code = cmd_discard_round(args.contract)
        elif args.command == "cleanup-round":
            exit_code = cmd_cleanup_round(args.contract)
        elif args.command == "refresh-status":
            exit_code = cmd_refresh_status()
        if exit_code is None:
            raise RuntimeError(f"Unsupported command: {args.command}")
        if exit_code == 0 and args.command != "refresh-status":
            _refresh_status_indexes_best_effort(args.command)
        return exit_code
    except AutoresearchStop as exc:
        print(f"{format_stop_status(args.command)}: stopped")
        print(f"stop_kind: {exc.kind}")
        print(f"stop_reason: {exc.message}")
        if args.command != "refresh-status":
            _refresh_status_indexes_best_effort(args.command)
        return 0
    except (FileNotFoundError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
