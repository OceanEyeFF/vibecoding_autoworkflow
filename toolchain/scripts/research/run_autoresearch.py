#!/usr/bin/env python3
"""Autoresearch entrypoint for P0.1 baseline, P0.2 worktree shell, and P0.3 round loop."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from autoresearch_contract import HISTORY_COLUMNS, history_header, load_contract, resolve_suite_files
from autoresearch_round import AutoresearchRoundManager
from autoresearch_scoreboard import build_scoreboard, load_run_summary, merge_run_summaries, write_scoreboard
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
from worktree_manager import read_json
from common import REPO_ROOT, slugify
from run_skill_suite import main as run_skill_suite_main
from worktree_manager import WorktreeManager


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


def sync_runtime_to_baseline(run_id: str, base_sha: str) -> None:
    manager = build_worktree_manager()
    runtime = manager.load_runtime(run_id)
    if runtime.get("active_round") is not None:
        raise RuntimeError("Cannot run baseline while an active round exists.")
    champion_branch = str(runtime["champion_branch"])
    if manager.branch_exists(champion_branch):
        champion_sha = manager.ref_sha(champion_branch)
        if champion_sha != base_sha:
            raise RuntimeError(
                "Baseline HEAD does not match the existing champion branch. "
                f"baseline={base_sha} champion={champion_sha}"
            )
    runtime["champion_sha"] = base_sha
    runtime["active_round"] = None
    runtime["active_candidate_branch"] = None
    runtime["active_candidate_worktree"] = None
    manager.save_runtime(run_id, runtime)


def _capture_new_summary(save_dir: Path, before: set[Path]) -> Path:
    after = {path for path in save_dir.iterdir() if path.is_dir()}
    new_dirs = sorted(after - before)
    if len(new_dirs) == 1:
        summary = new_dirs[0] / "run-summary.json"
        if summary.is_file():
            return summary
    candidates = sorted((path / "run-summary.json" for path in after), key=lambda item: item.stat().st_mtime)
    candidates = [path for path in candidates if path.is_file()]
    if not candidates:
        raise FileNotFoundError(f"No run-summary.json found under {save_dir}")
    return candidates[-1]


def run_lane_suites(suite_files: list[Path], save_dir: Path) -> list[dict[str, object]]:
    save_dir.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, object]] = []
    for suite_file in suite_files:
        before = {path for path in save_dir.iterdir() if path.is_dir()}
        exit_code = run_skill_suite_main(["--suite", str(suite_file), "--save-dir", str(save_dir)])
        if exit_code != 0:
            raise RuntimeError(f"Suite failed: {suite_file}")
        summary_path = _capture_new_summary(save_dir, before)
        summaries.append(load_run_summary(summary_path))
    return summaries


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
    contract = load_contract(contract_path, repo_root=REPO_ROOT)
    run_dir = run_dir_for_id(contract.run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    write_canonical_contract(run_dir, contract.payload)
    ensure_history_file(run_dir / "history.tsv")
    build_worktree_manager().load_runtime(contract.run_id)
    print(f"initialized_run: {run_dir}")
    return 0


def cmd_baseline(contract_path: Path) -> int:
    contract = load_contract(contract_path, repo_root=REPO_ROOT)
    run_dir = run_dir_for_id(contract.run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    write_canonical_contract(run_dir, contract.payload)

    history_path = run_dir / "history.tsv"
    ensure_history_file(history_path)

    base_sha = resolve_head_sha()
    sync_runtime_to_baseline(contract.run_id, base_sha)

    suites = resolve_suite_files(contract)
    train_summaries = run_lane_suites(suites["train"], run_dir / "baseline" / "train")
    validation_summaries = run_lane_suites(suites["validation"], run_dir / "baseline" / "validation")
    lane_summaries = {
        "train": merge_run_summaries(train_summaries),
        "validation": merge_run_summaries(validation_summaries),
    }
    scoreboard = build_scoreboard(run_id=contract.run_id, baseline_sha=base_sha, lane_summaries=lane_summaries)
    write_scoreboard(run_dir / "scoreboard.json", scoreboard)

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
    contract = load_contract(contract_path, repo_root=REPO_ROOT)
    run_dir = run_dir_for_id(contract.run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    write_canonical_contract(run_dir, contract.payload)
    ensure_history_file(run_dir / "history.tsv")
    round_manager = build_round_manager()
    manager = build_worktree_manager()
    next_round = manager.next_round_number(contract.run_id)

    registry_path = run_dir / "mutation-registry.json"
    registry = (
        load_mutation_registry(registry_path, contract=contract, repo_root=REPO_ROOT)
        if registry_path.is_file()
        else None
    )

    if mutation_key is not None:
        if registry is None:
            raise FileNotFoundError(f"Missing mutation registry: {registry_path}")
        entry = find_registry_entry(registry, mutation_key)
    else:
        if mutation_path is None:
            if registry is None:
                raise FileNotFoundError(
                    "Missing mutation registry and no mutation specified. "
                    f"Expected: {registry_path} (or pass --mutation-key / --mutation)"
                )
            selection = select_next_mutation_entry(registry, contract=contract)
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
    attempt = attempts_raw + 1
    mutation_payload = materialize_round_mutation(entry=entry, round_number=next_round, attempt=attempt)
    round_manager.ensure_prepare_allowed(contract, mutation_payload)
    result = manager.prepare_round(contract.run_id)
    round_payload = result["round"]
    round_number = int(round_payload["round"])
    round_manager.stage_mutation(contract.run_id, round_number, mutation_payload)

    baseline_scoreboard = read_json(run_dir / "scoreboard.json")
    worker_contract_path = round_manager.stage_worker_contract(
        contract,
        contract_path=run_dir / "contract.json",
        round_payload=round_payload,
        worktree_payload=result["worktree"],
        mutation_payload=mutation_payload,
        baseline_scoreboard=baseline_scoreboard,
    )

    # Write back the updated registry attempts/selection bookkeeping.
    entry["attempts"] = attempt
    entry["last_selected_round"] = round_number
    registry_payload = dict(registry.payload)
    registry_payload["entries"] = registry.entries
    write_mutation_registry(registry_path, registry_payload)

    print(f"prepared_round: {round_payload['round']}")
    print(f"candidate_branch: {round_payload['candidate_branch']}")
    print(f"candidate_worktree: {round_payload['candidate_worktree']}")
    print(f"mutation_path: {round_manager.mutation_path(contract.run_id, round_number)}")
    print(f"worker_contract_path: {worker_contract_path}")
    print(f"agent_report_path: {round_manager.agent_report_path(contract.run_id, round_number)}")
    return 0


def cmd_run_round(contract_path: Path) -> int:
    contract = load_contract(contract_path, repo_root=REPO_ROOT)
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
    contract = load_contract(contract_path, repo_root=REPO_ROOT)
    result = build_round_manager().decide_round(contract)
    decision = result["decision"]
    print(f"decided_round: {decision['round']}")
    print(f"decision: {decision['decision']}")
    print(f"candidate_sha: {decision['candidate_sha']}")
    return 0


def cmd_promote_round(contract_path: Path) -> int:
    contract = load_contract(contract_path, repo_root=REPO_ROOT)
    result = build_worktree_manager().promote_round(contract.run_id)
    runtime = result["runtime"]
    print(f"promoted_round: {result['round']['round']}")
    print(f"champion_sha: {runtime['champion_sha']}")
    return 0


def cmd_discard_round(contract_path: Path) -> int:
    contract = load_contract(contract_path, repo_root=REPO_ROOT)
    result = build_worktree_manager().discard_round(contract.run_id)
    print(f"discarded_round: {result['round']['round']}")
    return 0


def cmd_cleanup_round(contract_path: Path) -> int:
    contract = load_contract(contract_path, repo_root=REPO_ROOT)
    result = build_worktree_manager().cleanup_round(contract.run_id)
    print(f"cleaned_round: {result['round']['round']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        if args.command == "init":
            return cmd_init(args.contract)
        if args.command == "baseline":
            return cmd_baseline(args.contract)
        if args.command == "prepare-round":
            return cmd_prepare_round(
                args.contract,
                mutation_key=getattr(args, "mutation_key", None),
                mutation_path=getattr(args, "mutation", None),
            )
        if args.command == "run-round":
            return cmd_run_round(args.contract)
        if args.command == "decide-round":
            return cmd_decide_round(args.contract)
        if args.command == "promote-round":
            return cmd_promote_round(args.contract)
        if args.command == "discard-round":
            return cmd_discard_round(args.contract)
        if args.command == "cleanup-round":
            return cmd_cleanup_round(args.contract)
    except (FileNotFoundError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
