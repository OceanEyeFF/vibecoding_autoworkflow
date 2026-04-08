#!/usr/bin/env python3
"""Round execution helpers for autoresearch P0.3/P1.3."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from backend_runner import retry_policy_cli_args
from autoresearch_lane_executor import execute_lane_suites
from autoresearch_contract import (
    HISTORY_COLUMNS,
    AutoresearchContract,
    P2_RUNNER_TASK_TO_TARGET_TASK,
    P2_TARGET_TASK_TO_PROMPT_PATH,
    P2_TARGET_TASK_TO_RUNNER_TASK,
    normalize_repo_path,
    paths_overlap,
    resolve_timeout_seconds,
    resolve_p2_contract_target,
    resolve_suite_files,
)
from autoresearch_mutation_registry import (
    AutoresearchMutationRegistry,
    load_mutation_registry,
    materialize_round_mutation,
    upsert_registry_entry,
    write_mutation_registry,
)
from autoresearch_feedback_distill import (
    build_feedback_distill_payload,
    upsert_feedback_ledger_entry,
    write_feedback_distill,
)
from autoresearch_scoreboard import build_scoreboard, merge_run_summaries, write_scoreboard
from autoresearch_stop import AutoresearchStop
from autoresearch_worker_contract import (
    build_comparison_baseline,
    build_worker_contract_payload,
    compute_worker_contract_sha256,
    default_aggregate_prompt_guidance,
    LEGACY_WORKER_CONTRACT_POLICY,
    load_legacy_worker_contract_payload,
    load_worker_contract_payload,
    validate_legacy_worker_contract_consistency,
    write_worker_contract,
)
from exrepo_runtime import materialize_suite
from common import REPO_ROOT
from worktree_manager import AUTORESEARCH_ROOT, WorktreeManager, candidate_branch_name, champion_branch_name, read_json, write_json
from run_skill_suite import load_suite_manifest, resolve_path_override


MUTATION_REQUIRED_FIELDS = [
    "round",
    "mutation_id",
    "mutation_key",
    "attempt",
    "fingerprint",
    "kind",
    "target_paths",
    "allowed_actions",
    "instruction",
    "expected_effect",
    "guardrails",
]
SUPPORTED_MUTATION_ACTIONS = {"edit", "create", "delete", "rename", "copy"}
EPSILON = 1e-9


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object required: {path}")
    return payload


def _require_non_empty_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Mutation spec field '{field}' must be a non-empty string.")
    return value.strip()


def _require_non_empty_string_list(payload: dict[str, Any], field: str) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list) or not value:
        raise ValueError(f"Mutation spec field '{field}' must be a non-empty array.")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Mutation spec field '{field}' must contain only non-empty strings.")
        normalized.append(item.strip())
    return normalized


def _sha256_file_prefixed(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def load_mutation_payload(path: Path) -> dict[str, Any]:
    payload = _load_json(path.expanduser().resolve())
    missing = [field for field in MUTATION_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"Mutation spec missing required fields: {', '.join(missing)}")
    round_number = payload.get("round")
    if not isinstance(round_number, int) or round_number <= 0:
        raise ValueError("Mutation spec field 'round' must be a positive integer.")
    attempt = payload.get("attempt")
    if not isinstance(attempt, int) or attempt <= 0:
        raise ValueError("Mutation spec field 'attempt' must be a positive integer.")
    payload["mutation_id"] = _require_non_empty_string(payload, "mutation_id")
    payload["mutation_key"] = _require_non_empty_string(payload, "mutation_key")
    payload["fingerprint"] = _require_non_empty_string(payload, "fingerprint")
    payload["kind"] = _require_non_empty_string(payload, "kind")
    payload["instruction"] = _require_non_empty_string(payload, "instruction")
    expected_effect = payload.get("expected_effect")
    if not isinstance(expected_effect, dict):
        raise ValueError("Mutation spec field 'expected_effect' must be an object.")
    hypothesis = expected_effect.get("hypothesis")
    if not isinstance(hypothesis, str) or not hypothesis.strip():
        raise ValueError("Mutation spec expected_effect.hypothesis must be a non-empty string.")
    primary_metrics = expected_effect.get("primary_metrics")
    if not isinstance(primary_metrics, list) or not primary_metrics:
        raise ValueError("Mutation spec expected_effect.primary_metrics must be a non-empty array.")
    guard_metrics = expected_effect.get("guard_metrics")
    if guard_metrics is not None and not isinstance(guard_metrics, list):
        raise ValueError("Mutation spec expected_effect.guard_metrics must be an array.")
    payload["expected_effect"] = {
        "hypothesis": hypothesis.strip(),
        "primary_metrics": [str(item).strip() for item in primary_metrics if str(item).strip()],
        "guard_metrics": [str(item).strip() for item in (guard_metrics or []) if str(item).strip()],
    }
    guardrails = payload.get("guardrails")
    if not isinstance(guardrails, dict):
        raise ValueError("Mutation spec field 'guardrails' must be an object.")
    max_files_touched = guardrails.get("max_files_touched")
    if not isinstance(max_files_touched, int) or max_files_touched <= 0:
        raise ValueError("Mutation spec guardrails.max_files_touched must be a positive integer.")
    extra_frozen_paths = guardrails.get("extra_frozen_paths")
    if extra_frozen_paths is not None and not isinstance(extra_frozen_paths, list):
        raise ValueError("Mutation spec guardrails.extra_frozen_paths must be an array.")
    payload["guardrails"] = {
        "require_non_empty_diff": bool(guardrails.get("require_non_empty_diff")),
        "max_files_touched": int(max_files_touched),
        "extra_frozen_paths": [str(item).strip() for item in (extra_frozen_paths or []) if str(item).strip()],
    }
    payload["target_paths"] = _require_non_empty_string_list(payload, "target_paths")
    payload["allowed_actions"] = [
        value.lower() for value in _require_non_empty_string_list(payload, "allowed_actions")
    ]
    return payload


def _lane_map(scoreboard: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lanes = scoreboard.get("lanes") or []
    return {
        str(lane.get("lane_name")): lane
        for lane in lanes
        if isinstance(lane, dict) and lane.get("lane_name")
    }


def _float_metric(lane: dict[str, Any], key: str) -> float:
    value = lane.get(key)
    return float(value) if isinstance(value, (int, float)) else 0.0


def _status_to_action(status: str) -> str:
    if status == "??":
        return "create"
    code = next((char for char in status if char not in {" ", "?"}), "")
    mapping = {
        "A": "create",
        "M": "edit",
        "T": "edit",
        "D": "delete",
        "R": "rename",
        "C": "copy",
    }
    if code == "U":
        raise RuntimeError("Unmerged candidate changes are not supported.")
    action = mapping.get(code)
    if action is None:
        raise RuntimeError(f"Unsupported candidate change status: {status}")
    return action


def _parse_status_paths(status: str, raw_paths: str) -> list[PurePosixPath]:
    path_values = [raw_paths]
    if "R" in status or "C" in status:
        if " -> " not in raw_paths:
            raise RuntimeError(f"Unable to parse renamed/copied path from status line: {status} {raw_paths}")
        path_values = raw_paths.split(" -> ", 1)
    return [PurePosixPath(Path(value).as_posix()) for value in path_values]


def _parse_name_status_paths(status: str, raw_paths: list[str]) -> list[PurePosixPath]:
    expects_pair = "R" in status or "C" in status
    expected = 2 if expects_pair else 1
    if len(raw_paths) != expected:
        raise RuntimeError(f"Unable to parse diff paths from status line: {status} {' '.join(raw_paths)}")
    return [PurePosixPath(Path(value).as_posix()) for value in raw_paths]


def _posix_is_under(base: PurePosixPath, target: PurePosixPath) -> bool:
    if base == target:
        return True
    base_parts = base.parts
    target_parts = target.parts
    return base_parts == target_parts[: len(base_parts)]


def _history_rows(history_path: Path) -> list[dict[str, str]]:
    if not history_path.is_file():
        return []
    lines = [line for line in history_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) <= 1:
        return []
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) != len(HISTORY_COLUMNS):
            continue
        rows.append(dict(zip(HISTORY_COLUMNS, parts, strict=True)))
    return rows


def append_history_round_row(
    history_path: Path,
    *,
    round_number: int,
    kind: str,
    base_sha: str,
    candidate_sha: str,
    train_score: float,
    validation_score: float,
    train_parse_error_rate: float,
    validation_parse_error_rate: float,
    decision: str,
    notes: str,
) -> None:
    values = {
        "round": str(round_number),
        "kind": kind,
        "base_sha": base_sha,
        "candidate_sha": candidate_sha,
        "train_score": f"{train_score:.6f}",
        "validation_score": f"{validation_score:.6f}",
        "train_parse_error_rate": f"{train_parse_error_rate:.6f}",
        "validation_parse_error_rate": f"{validation_parse_error_rate:.6f}",
        "decision": decision,
        "notes": notes,
    }
    row = "\t".join(values[column] for column in HISTORY_COLUMNS)
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(row + "\n")


class AutoresearchRoundManager:
    """Own P0.3 round files, evaluation runs, and keep/discard decisions."""

    def __init__(
        self,
        *,
        repo_root: Path = REPO_ROOT,
        autoresearch_root: Path = AUTORESEARCH_ROOT,
        python_executable: str = sys.executable,
        worktree_manager: WorktreeManager | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.autoresearch_root = autoresearch_root.resolve()
        self.python_executable = python_executable
        self.worktree_manager = worktree_manager or WorktreeManager(
            repo_root=self.repo_root,
            autoresearch_root=self.autoresearch_root,
        )

    def run_dir(self, run_id: str) -> Path:
        return self.worktree_manager.run_dir(run_id)

    def mutation_path(self, run_id: str, round_number: int) -> Path:
        return self.worktree_manager.round_dir(run_id, round_number) / "mutation.json"

    def round_scoreboard_path(self, run_id: str, round_number: int) -> Path:
        return self.worktree_manager.round_dir(run_id, round_number) / "scoreboard.json"

    def decision_path(self, run_id: str, round_number: int) -> Path:
        return self.worktree_manager.round_dir(run_id, round_number) / "decision.json"

    def agent_report_path(self, run_id: str, round_number: int) -> Path:
        return self.worktree_manager.round_dir(run_id, round_number) / "agent-report.md"

    def worker_contract_path(self, run_id: str, round_number: int) -> Path:
        return self.worktree_manager.round_dir(run_id, round_number) / "worker-contract.json"

    def feedback_distill_path(self, run_id: str, round_number: int) -> Path:
        return self.worktree_manager.round_dir(run_id, round_number) / "feedback-distill.json"

    def replay_dir(self, run_id: str, round_number: int) -> Path:
        return self.worktree_manager.round_dir(run_id, round_number) / "replay"

    def replay_scoreboard_path(self, run_id: str, round_number: int) -> Path:
        return self.replay_dir(run_id, round_number) / "scoreboard.json"

    def feedback_ledger_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "feedback-ledger.jsonl"

    def baseline_scoreboard_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "scoreboard.json"

    def history_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "history.tsv"

    def mutation_registry_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "mutation-registry.json"

    def round_authority_ref(self, run_id: str, round_number: int) -> str:
        return self.worktree_manager.round_authority_ref(run_id, round_number)

    def _normalize_contract_paths(self, values: list[str]) -> list[PurePosixPath]:
        return [normalize_repo_path(value, self.repo_root) for value in values]

    def _validate_mutation_scope(self, contract: AutoresearchContract, mutation_payload: dict[str, Any]) -> None:
        target_paths = self._normalize_contract_paths([str(value) for value in mutation_payload["target_paths"]])
        mutable_paths = self._normalize_contract_paths(contract.mutable_paths)
        frozen_paths = self._normalize_contract_paths(contract.frozen_paths)
        p2_target = resolve_p2_contract_target(contract, repo_root=self.repo_root)
        unsupported_actions = sorted(set(mutation_payload["allowed_actions"]) - SUPPORTED_MUTATION_ACTIONS)
        if unsupported_actions:
            raise ValueError(
                "Mutation spec allowed_actions contain unsupported values: " + ", ".join(unsupported_actions)
            )
        if p2_target is not None:
            _target_task, target_prompt_path = p2_target
            if target_paths != [target_prompt_path]:
                raise ValueError(
                    "P2 mutation target_paths must be exactly [contract.target_prompt_path]: "
                    f"{target_prompt_path.as_posix()}"
                )
        for target_path in target_paths:
            if not any(_posix_is_under(base=mutable_path, target=target_path) for mutable_path in mutable_paths):
                raise ValueError(
                    "Mutation target_paths must stay within contract.mutable_paths: "
                    f"{target_path.as_posix()}"
                )
            if any(paths_overlap(target_path, frozen_path) for frozen_path in frozen_paths):
                raise ValueError(
                    "Mutation target_paths must not overlap contract.frozen_paths: "
                    f"{target_path.as_posix()}"
                )

    def _collect_candidate_worktree_changes(self, candidate_worktree: Path) -> list[dict[str, Any]]:
        completed = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=candidate_worktree,
            check=True,
            capture_output=True,
            text=True,
        )
        changes: list[dict[str, Any]] = []
        for raw_line in completed.stdout.splitlines():
            if not raw_line.strip():
                continue
            status = raw_line[:2]
            raw_paths = raw_line[3:]
            changes.append(
                {
                    "status": status,
                    "action": _status_to_action(status),
                    "paths": _parse_status_paths(status, raw_paths),
                }
            )
        return changes

    def _collect_candidate_committed_changes(self, candidate_worktree: Path, *, base_sha: str) -> list[dict[str, Any]]:
        completed = subprocess.run(
            ["git", "diff", "--name-status", "--find-renames", "--find-copies", f"{base_sha}..HEAD"],
            cwd=candidate_worktree,
            check=True,
            capture_output=True,
            text=True,
        )
        changes: list[dict[str, Any]] = []
        for raw_line in completed.stdout.splitlines():
            if not raw_line.strip():
                continue
            parts = raw_line.split("\t")
            status = parts[0]
            paths = parts[1:]
            changes.append(
                {
                    "status": status,
                    "action": _status_to_action(status),
                    "paths": _parse_name_status_paths(status, paths),
                }
            )
        return changes

    def _validate_candidate_changes(
        self,
        contract: AutoresearchContract,
        mutation_payload: dict[str, Any],
        *,
        candidate_worktree: Path,
        base_sha: str,
    ) -> None:
        allowed_actions = set(str(value) for value in mutation_payload["allowed_actions"])
        target_paths = self._normalize_contract_paths([str(value) for value in mutation_payload["target_paths"]])
        frozen_paths = self._normalize_contract_paths(contract.frozen_paths)
        guardrails = mutation_payload.get("guardrails") or {}
        if not isinstance(guardrails, dict):
            raise RuntimeError("Mutation guardrails must be an object.")
        extra_frozen_paths = self._normalize_contract_paths([str(value) for value in guardrails.get("extra_frozen_paths") or []])
        max_files_touched = int(guardrails.get("max_files_touched") or 0)
        require_non_empty_diff = bool(guardrails.get("require_non_empty_diff"))
        changes = self._collect_candidate_committed_changes(candidate_worktree, base_sha=base_sha)
        changes.extend(self._collect_candidate_worktree_changes(candidate_worktree))
        touched_paths: set[str] = set()
        for change in changes:
            action = str(change["action"])
            if action not in allowed_actions:
                rendered_paths = ", ".join(path.as_posix() for path in change["paths"])
                raise RuntimeError(f"Candidate change action is not allowed: {action} for {rendered_paths}")
            for changed_path in change["paths"]:
                touched_paths.add(changed_path.as_posix())
                if not any(paths_overlap(target_path, changed_path) for target_path in target_paths):
                    raise RuntimeError(
                        "Candidate change escapes mutation target_paths: "
                        f"{changed_path.as_posix()}"
                    )
                if any(paths_overlap(changed_path, frozen_path) for frozen_path in frozen_paths):
                    raise RuntimeError(f"Candidate change touches frozen path: {changed_path.as_posix()}")
                if any(paths_overlap(changed_path, frozen_path) for frozen_path in extra_frozen_paths):
                    raise RuntimeError(f"Candidate change touches frozen guardrail path: {changed_path.as_posix()}")
        if require_non_empty_diff and not touched_paths:
            raise RuntimeError("Candidate diff must be non-empty when require_non_empty_diff is enabled.")
        if max_files_touched <= 0:
            raise RuntimeError("Mutation guardrails.max_files_touched must be a positive integer.")
        if len(touched_paths) > max_files_touched:
            raise RuntimeError(
                "Candidate diff touches too many files for guardrails.max_files_touched: "
                f"{len(touched_paths)} > {max_files_touched}"
            )

    def _load_authoritative_mutation(
        self,
        contract: AutoresearchContract,
        round_number: int,
    ) -> tuple[AutoresearchMutationRegistry, dict[str, Any], dict[str, Any], dict[str, float | None], list[str], dict[str, Any]]:
        (
            _authority_oid,
            _authority,
            frozen_registry_entry,
            frozen_mutation_payload,
            frozen_comparison_baseline,
            frozen_recent_feedback_excerpt,
            frozen_aggregate_prompt_guidance,
        ) = self._load_round_authority(contract, round_number)
        registry_path = self.mutation_registry_path(contract.run_id)
        if not registry_path.is_file():
            raise FileNotFoundError(f"Missing mutation registry: {registry_path}")
        registry = load_mutation_registry(registry_path, contract=contract, repo_root=self.repo_root)
        selected_entries = [
            entry for entry in registry.entries if int(entry.get("last_selected_round") or 0) == round_number
        ]
        if len(selected_entries) != 1:
            raise RuntimeError(
                "Mutation registry must contain exactly one entry selected for the active round. "
                f"round={round_number} matches={len(selected_entries)}"
            )
        entry = selected_entries[0]
        attempts = entry.get("attempts")
        if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts <= 0:
            raise RuntimeError("Registry entry attempts must be a positive integer for the active round.")
        if entry != frozen_registry_entry:
            raise RuntimeError("mutation-registry.json does not match frozen round authority snapshot.")
        mutation_payload = materialize_round_mutation(entry=entry, round_number=round_number, attempt=attempts)
        if mutation_payload != frozen_mutation_payload:
            raise RuntimeError("Materialized mutation does not match frozen round authority snapshot.")
        mutation_path = self.mutation_path(contract.run_id, round_number)
        if not mutation_path.is_file():
            raise FileNotFoundError(f"Missing mutation file: {mutation_path}")
        round_payload = read_json(self.worktree_manager.round_path(contract.run_id, round_number))
        recorded_mutation_sha256 = str(round_payload.get("mutation_sha256") or "")
        if not recorded_mutation_sha256:
            raise RuntimeError("Missing mutation_sha256 in round.json for the active round.")
        actual_mutation_sha256 = _sha256_file_prefixed(mutation_path)
        if actual_mutation_sha256 != recorded_mutation_sha256:
            raise RuntimeError("mutation.json does not match hash recorded in round.json.")
        actual_mutation = load_mutation_payload(mutation_path)
        if actual_mutation != frozen_mutation_payload:
            raise RuntimeError("mutation.json does not match frozen round authority snapshot.")
        return (
            registry,
            entry,
            frozen_mutation_payload,
            frozen_comparison_baseline,
            frozen_recent_feedback_excerpt,
            frozen_aggregate_prompt_guidance,
        )

    def validate_p2_preflight(self, contract: AutoresearchContract) -> None:
        resolved_target = resolve_p2_contract_target(contract, repo_root=self.repo_root)
        if resolved_target is None:
            return
        target_task, target_prompt_path = resolved_target
        expected_backend = contract.expected_backend
        expected_judge_backend = contract.expected_judge_backend
        expected_runner_task = next(
            runner_task for runner_task, mapped_target in P2_RUNNER_TASK_TO_TARGET_TASK.items() if mapped_target == target_task
        )
        suite_files = resolve_suite_files(contract)
        for lane_name, paths in suite_files.items():
            for suite_path in paths:
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
                                    else (self.repo_root / P2_TARGET_TASK_TO_PROMPT_PATH[P2_RUNNER_TASK_TO_TARGET_TASK[resolved_task]]).resolve()
                                ),
                            }
                        )
                for spec in resolved_specs:
                    if str(spec["task"]) != expected_runner_task:
                        raise ValueError(
                            f"P2 suite {lane_name} must only cover target_task={target_task}: {suite_path}"
                        )
                    prompt_path = Path(str(spec["prompt_file"])).resolve()
                    if prompt_path != (self.repo_root / target_prompt_path).resolve():
                        raise ValueError(
                            "P2 suite prompt_file must resolve to target_prompt_path: "
                            f"{suite_path}"
                        )
                    if (
                        str(spec["backend"]) != expected_backend
                        or str(spec["judge_backend"]) != expected_judge_backend
                    ):
                        raise ValueError(
                            "P2 suite must enforce the contract backend pair for every run: "
                            f"{suite_path} ({expected_backend} -> {expected_judge_backend})"
                        )

    def _write_registry_decision_state(
        self,
        contract: AutoresearchContract,
        *,
        registry: AutoresearchMutationRegistry,
        entry: dict[str, Any],
        decision: str,
    ) -> None:
        updated_entry = dict(entry)
        updated_entry["last_decision"] = decision
        max_attempts_raw = contract.payload.get("max_candidate_attempts_per_round")
        if isinstance(max_attempts_raw, bool) or not isinstance(max_attempts_raw, int) or max_attempts_raw <= 0:
            raise ValueError("contract.payload.max_candidate_attempts_per_round must be a positive integer.")
        if int(updated_entry.get("attempts") or 0) >= max_attempts_raw:
            updated_entry["status"] = "exhausted"
        updated_registry = upsert_registry_entry(registry=registry, entry=updated_entry)
        registry_payload = dict(updated_registry.payload)
        registry_payload["entries"] = updated_registry.entries
        write_mutation_registry(self.mutation_registry_path(contract.run_id), registry_payload)

    def ensure_prepare_allowed(self, contract: AutoresearchContract, mutation_payload: dict[str, Any]) -> None:
        baseline_scoreboard = self.baseline_scoreboard_path(contract.run_id)
        if not baseline_scoreboard.is_file():
            raise FileNotFoundError("Baseline scoreboard missing. Run baseline before prepare-round.")
        next_round = self.worktree_manager.next_round_number(contract.run_id)
        if next_round > int(contract.payload["max_rounds"]):
            raise AutoresearchStop(
                kind="max_rounds_reached",
                message=(
                    f"Stop gate triggered: next round {next_round} exceeds "
                    f"max_rounds={contract.payload['max_rounds']} for run {contract.run_id}."
                ),
            )
        expected_round = int(mutation_payload["round"])
        if expected_round != next_round:
            raise ValueError(
                f"Mutation spec round={expected_round} does not match next round {next_round} for run {contract.run_id}"
            )
        self._validate_mutation_scope(contract, mutation_payload)

    def _ensure_round_worker_contract(
        self,
        contract: AutoresearchContract,
        *,
        round_payload: dict[str, Any],
        mutation_payload: dict[str, Any],
        comparison_baseline: dict[str, float | None],
        recent_feedback_excerpt: list[str],
        aggregate_prompt_guidance: dict[str, Any] | None = None,
        rewrite: bool = False,
    ) -> Path:
        run_id = contract.run_id
        round_number = int(round_payload["round"])
        round_path = self.worktree_manager.round_path(run_id, round_number)
        stored_round = read_json(round_path)
        mutation_sha256 = str(stored_round.get("mutation_sha256") or "")
        if not mutation_sha256:
            raise RuntimeError("Missing mutation_sha256 in round.json; stage mutation before worker contract.")
        materialized_at = str(stored_round.get("worker_contract_materialized_at") or "").strip()
        if not materialized_at:
            materialized_at = now_iso()
            stored_round["worker_contract_materialized_at"] = materialized_at
        worker_path = self.worker_contract_path(run_id, round_number)
        expected_payload = build_worker_contract_payload(
            contract=contract,
            mutation_payload=mutation_payload,
            round_payload=stored_round,
            agent_report_path=self.agent_report_path(run_id, round_number),
            comparison_baseline=comparison_baseline,
            recent_feedback_excerpt=recent_feedback_excerpt,
            aggregate_prompt_guidance=aggregate_prompt_guidance or default_aggregate_prompt_guidance(),
            materialized_at=materialized_at,
        )
        if rewrite or not worker_path.is_file():
            write_worker_contract(worker_path, expected_payload)
        stored_round["worker_contract_sha256"] = compute_worker_contract_sha256(worker_path)
        write_json(round_path, stored_round)
        return worker_path

    def stage_worker_contract(
        self,
        contract: AutoresearchContract,
        *,
        round_payload: dict[str, Any],
        mutation_payload: dict[str, Any],
        comparison_baseline: dict[str, float | None],
        recent_feedback_excerpt: list[str],
        aggregate_prompt_guidance: dict[str, Any] | None = None,
    ) -> Path:
        return self._ensure_round_worker_contract(
            contract,
            round_payload=round_payload,
            mutation_payload=mutation_payload,
            comparison_baseline=comparison_baseline,
            recent_feedback_excerpt=recent_feedback_excerpt,
            aggregate_prompt_guidance=aggregate_prompt_guidance,
        )

    def _discover_active_prepare_round(self, run_id: str) -> int | None:
        rounds_root = self.worktree_manager.rounds_root(run_id)
        if not rounds_root.is_dir():
            return None
        candidates: list[int] = []
        for path in sorted(rounds_root.iterdir()):
            if not path.is_dir() or not path.name.startswith("round-"):
                continue
            try:
                round_number = int(path.name.split("-", 1)[1])
            except ValueError:
                continue
            round_path = self.worktree_manager.round_path(run_id, round_number)
            if not round_path.is_file():
                continue
            round_payload = read_json(round_path)
            state = str(round_payload.get("state") or "")
            if state not in {"prepared", "candidate_active"}:
                continue
            if not self.worktree_manager.ref_exists(self.round_authority_ref(run_id, round_number)):
                continue
            candidates.append(round_number)
        if not candidates:
            return None
        if len(candidates) > 1:
            raise RuntimeError(
                "Multiple prepared/candidate_active rounds exist without a usable runtime.json. "
                "Run cleanup-round before starting a new round."
            )
        return candidates[0]

    def reconcile_prepare_state(self, contract: AutoresearchContract) -> dict[str, Any] | None:
        runtime_path = self.worktree_manager.runtime_path(contract.run_id)
        if runtime_path.is_file():
            runtime = read_json(runtime_path)
            active_round = runtime.get("active_round")
            if active_round is None:
                return None
            round_number = int(active_round)
        else:
            discovered_round = self._discover_active_prepare_round(contract.run_id)
            if discovered_round is None:
                return None
            round_number = discovered_round
            round_path = self.worktree_manager.round_path(contract.run_id, round_number)
            if not round_path.is_file():
                raise RuntimeError(
                    "Discovered an active round authority snapshot but round.json is missing. Run cleanup-round."
                )
            round_payload = read_json(round_path)
            champion_branch = champion_branch_name(contract.run_id)
            if not self.worktree_manager.branch_exists(champion_branch):
                raise RuntimeError(
                    "Missing champion branch while reconstructing runtime.json for active round recovery."
                )
            runtime = {
                "run_id": contract.run_id,
                "champion_branch": champion_branch,
                "champion_sha": self.worktree_manager.ref_sha(champion_branch),
                "active_round": round_number,
                "active_candidate_branch": str(round_payload.get("candidate_branch") or candidate_branch_name(contract.run_id, round_number)),
                "active_candidate_worktree": str(self.worktree_manager.candidate_worktree_path(contract.run_id, round_number)),
            }
            self.worktree_manager.save_runtime(contract.run_id, runtime)

        round_path = self.worktree_manager.round_path(contract.run_id, round_number)
        if not round_path.is_file():
            raise RuntimeError("runtime.json points to an active round but round.json is missing. Run cleanup-round.")
        round_payload = read_json(round_path)
        if str(round_payload.get("state") or "") not in {"prepared", "candidate_active"}:
            return None
        authority_ref = self.round_authority_ref(contract.run_id, round_number)
        if not self.worktree_manager.ref_exists(authority_ref):
            raise RuntimeError(
                "Active round exists without a frozen round authority snapshot. "
                "Run cleanup-round before starting a new round."
            )
        (
            _authority_oid,
            _authority,
            registry_entry,
            mutation_payload,
            comparison_baseline,
            recent_feedback_excerpt,
            aggregate_prompt_guidance,
        ) = self._load_round_authority(contract, round_number)
        mutation_path = self.mutation_path(contract.run_id, round_number)
        rewrite_mutation = True
        if mutation_path.is_file():
            try:
                rewrite_mutation = load_mutation_payload(mutation_path) != mutation_payload
            except Exception:
                rewrite_mutation = True
        if rewrite_mutation:
            write_json(mutation_path, mutation_payload)
        round_payload = read_json(round_path)
        round_payload["mutation_sha256"] = _sha256_file_prefixed(mutation_path)
        write_json(round_path, round_payload)

        registry_path = self.mutation_registry_path(contract.run_id)
        if not registry_path.is_file():
            raise RuntimeError(
                "Missing mutation registry while recovering an active round. "
                "Cannot losslessly reconstruct the candidate pool; run cleanup-round first."
            )
        registry = load_mutation_registry(registry_path, contract=contract, repo_root=self.repo_root)
        updated_registry = upsert_registry_entry(registry=registry, entry=registry_entry)
        registry_payload = dict(updated_registry.payload)
        registry_payload["entries"] = updated_registry.entries
        write_mutation_registry(registry_path, registry_payload)

        worker_path = self._ensure_round_worker_contract(
            contract,
            round_payload=round_payload,
            mutation_payload=mutation_payload,
            comparison_baseline=comparison_baseline,
            recent_feedback_excerpt=recent_feedback_excerpt,
            aggregate_prompt_guidance=aggregate_prompt_guidance,
            rewrite=True,
        )
        return {
            "round": round_number,
            "mutation_path": mutation_path,
            "worker_contract_path": worker_path,
            "registry_path": registry_path,
        }

    def stage_mutation(self, run_id: str, round_number: int, mutation_payload: dict[str, Any]) -> Path:
        mutation_path = self.mutation_path(run_id, round_number)
        write_json(mutation_path, mutation_payload)
        round_path = self.worktree_manager.round_path(run_id, round_number)
        round_payload = read_json(round_path)
        round_payload["mutation_sha256"] = _sha256_file_prefixed(mutation_path)
        write_json(round_path, round_payload)
        return mutation_path

    def stage_round_authority(
        self,
        run_id: str,
        round_number: int,
        *,
        registry_entry: dict[str, Any],
        mutation_payload: dict[str, Any],
        comparison_baseline: dict[str, float | None],
        recent_feedback_excerpt: list[str],
        aggregate_prompt_guidance: dict[str, Any] | None = None,
    ) -> str:
        authority_payload = {
            "run_id": run_id,
            "round": round_number,
            "registry_entry": registry_entry,
            "mutation_payload": mutation_payload,
            "comparison_baseline": dict(comparison_baseline),
            "recent_feedback_excerpt": list(recent_feedback_excerpt),
            "aggregate_prompt_guidance": dict(aggregate_prompt_guidance or default_aggregate_prompt_guidance()),
        }
        return self.worktree_manager.write_round_authority(run_id, round_number, authority_payload)

    def _load_round_authority(
        self,
        contract: AutoresearchContract,
        round_number: int,
    ) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, float | None], list[str], dict[str, Any]]:
        authority_oid, authority = self.worktree_manager.read_round_authority(contract.run_id, round_number)
        if str(authority.get("run_id") or "") != contract.run_id:
            raise RuntimeError("round authority snapshot run_id does not match the active contract.")
        if int(authority.get("round") or 0) != round_number:
            raise RuntimeError("round authority snapshot round does not match the active round.")
        registry_entry = authority.get("registry_entry")
        mutation_payload = authority.get("mutation_payload")
        comparison_baseline = authority.get("comparison_baseline")
        recent_feedback_excerpt = authority.get("recent_feedback_excerpt") or []
        aggregate_prompt_guidance = authority.get("aggregate_prompt_guidance") or default_aggregate_prompt_guidance()
        if not isinstance(registry_entry, dict) or not isinstance(mutation_payload, dict):
            raise RuntimeError("round authority snapshot must contain registry_entry and mutation_payload objects.")
        if not isinstance(comparison_baseline, dict):
            raise RuntimeError("round authority snapshot must contain comparison_baseline.")
        if not isinstance(recent_feedback_excerpt, list):
            raise RuntimeError("round authority snapshot recent_feedback_excerpt must be a list.")
        if not isinstance(aggregate_prompt_guidance, dict):
            raise RuntimeError("round authority snapshot aggregate_prompt_guidance must be an object.")
        excerpt = [str(item).strip() for item in recent_feedback_excerpt if str(item).strip()]
        return (
            authority_oid,
            authority,
            registry_entry,
            mutation_payload,
            dict(comparison_baseline),
            excerpt,
            dict(aggregate_prompt_guidance),
        )

    def run_round(self, contract: AutoresearchContract) -> dict[str, Any]:
        active = self.worktree_manager.load_active_round(contract.run_id)
        round_payload = active["round"]
        round_number = int(round_payload["round"])
        if str(round_payload.get("state")) != "candidate_active":
            raise RuntimeError("run-round requires the active round to be in candidate_active state.")
        round_dir = self.worktree_manager.round_dir(contract.run_id, round_number)
        _registry, _registry_entry, mutation_payload, comparison_baseline, recent_feedback_excerpt, aggregate_prompt_guidance = (
            self._load_authoritative_mutation(contract, round_number)
        )
        mutation_path = self.mutation_path(contract.run_id, round_number)
        worker_path = self.worker_contract_path(contract.run_id, round_number)
        if not worker_path.is_file():
            raise FileNotFoundError(f"Missing worker contract: {worker_path}")
        recorded_worker_contract_sha256 = str(round_payload.get("worker_contract_sha256") or "")
        if recorded_worker_contract_sha256:
            worker_contract = load_worker_contract_payload(worker_path)
            actual_worker_contract_sha256 = compute_worker_contract_sha256(worker_path)
            if actual_worker_contract_sha256 != recorded_worker_contract_sha256:
                raise RuntimeError("worker-contract.json does not match hash recorded in round.json.")
            worker_contract_version = int(worker_contract.get("worker_contract_version") or 0)
            expected_worker_contract = build_worker_contract_payload(
                contract=contract,
                mutation_payload=mutation_payload,
                round_payload=round_payload,
                agent_report_path=self.agent_report_path(contract.run_id, round_number),
                comparison_baseline=comparison_baseline,
                recent_feedback_excerpt=recent_feedback_excerpt,
                aggregate_prompt_guidance=aggregate_prompt_guidance,
                materialized_at=str(round_payload.get("worker_contract_materialized_at") or ""),
                worker_contract_version=worker_contract_version,
            )
            if worker_contract != expected_worker_contract:
                raise RuntimeError("worker-contract.json does not match authoritative round/mutation/worktree state.")
        else:
            print(f"[P1] legacy_worker_contract_mode: {LEGACY_WORKER_CONTRACT_POLICY}")
            worker_contract = load_legacy_worker_contract_payload(worker_path)
            mutation_sha256 = str(round_payload.get("mutation_sha256") or "")
            if not mutation_sha256:
                raise RuntimeError("Missing mutation_sha256 in round.json for the active round.")
            validate_legacy_worker_contract_consistency(
                worker_contract=worker_contract,
                round_payload=round_payload,
                mutation_payload=mutation_payload,
                worktree_payload=active["worktree"],
                mutation_sha256=mutation_sha256,
            )

        if int(mutation_payload["round"]) != round_number:
            raise ValueError(
                f"Mutation spec round={mutation_payload['round']} does not match active round {round_number}."
            )
        self._validate_mutation_scope(contract, mutation_payload)
        agent_report = self.agent_report_path(contract.run_id, round_number)
        if not agent_report.is_file():
            raise FileNotFoundError(f"Missing agent report: {agent_report}")
        worktree_payload = active["worktree"]
        candidate_worktree = Path(str(worktree_payload["path"]))
        self._validate_candidate_changes(
            contract,
            mutation_payload,
            candidate_worktree=candidate_worktree,
            base_sha=str(round_payload["base_sha"]),
        )

        round_payload["state"] = "evaluating"
        write_json(self.worktree_manager.round_path(contract.run_id, round_number), round_payload)

        mutation_id = str(mutation_payload["mutation_id"])
        capture = self.worktree_manager.capture_candidate_commit(
            contract.run_id,
            message=f"autoresearch round {round_number:03d}: {mutation_id}",
        )
        round_payload = capture["round"]
        worktree_payload = capture["worktree"]
        candidate_worktree = Path(str(worktree_payload["path"]))

        suites = resolve_suite_files(contract)
        train_summaries = self._run_lane_suites(
            candidate_worktree=candidate_worktree,
            contract=contract,
            suite_files=suites["train"],
            save_dir=round_dir / "train",
        )
        validation_summaries = self._run_lane_suites(
            candidate_worktree=candidate_worktree,
            contract=contract,
            suite_files=suites["validation"],
            save_dir=round_dir / "validation",
        )

        lane_summaries = {
            "train": merge_run_summaries(train_summaries),
            "validation": merge_run_summaries(validation_summaries),
        }
        baseline_scoreboard = read_json(self.baseline_scoreboard_path(contract.run_id))
        scoreboard = build_scoreboard(
            run_id=contract.run_id,
            baseline_sha=str(baseline_scoreboard["baseline_sha"]),
            lane_summaries=lane_summaries,
        )
        scoreboard["rounds_completed"] = int(baseline_scoreboard.get("rounds_completed") or 0)
        scoreboard["best_round"] = int(baseline_scoreboard.get("best_round") or 0)
        write_scoreboard(self.round_scoreboard_path(contract.run_id, round_number), scoreboard)

        round_payload["state"] = "evaluated"
        round_payload["candidate_sha"] = str(worktree_payload.get("candidate_sha") or round_payload.get("candidate_sha"))
        round_payload["evaluated_at"] = now_iso()
        write_json(self.worktree_manager.round_path(contract.run_id, round_number), round_payload)
        return {
            "round": round_payload,
            "worktree": worktree_payload,
            "scoreboard": scoreboard,
            "mutation": mutation_payload,
        }

    def decide_round(self, contract: AutoresearchContract) -> dict[str, Any]:
        active = self.worktree_manager.load_active_round(contract.run_id)
        round_payload = active["round"]
        worktree_payload = active["worktree"]
        round_number = int(round_payload["round"])
        if str(round_payload.get("state")) != "evaluated":
            raise RuntimeError("decide-round requires the active round to be in evaluated state.")
        registry, registry_entry, mutation_payload, _comparison_baseline, _recent_feedback_excerpt, _aggregate_prompt_guidance = (
            self._load_authoritative_mutation(contract, round_number)
        )
        baseline_scoreboard = read_json(self.baseline_scoreboard_path(contract.run_id))
        round_scoreboard = read_json(self.round_scoreboard_path(contract.run_id, round_number))
        decision_payload = self._build_decision(
            contract=contract,
            round_payload=round_payload,
            mutation_payload=mutation_payload,
            baseline_scoreboard=baseline_scoreboard,
            round_scoreboard=round_scoreboard,
        )
        replay = self._evaluate_replay(
            contract=contract,
            round_number=round_number,
            round_payload=round_payload,
            worktree_payload=worktree_payload,
            baseline_scoreboard=baseline_scoreboard,
            round_scoreboard=round_scoreboard,
            decision_payload=decision_payload,
        )
        if replay is not None:
            decision_payload["provisional_decision"] = decision_payload["decision"]
            decision_payload["replay"] = replay
            if replay["status"] != "passed":
                decision_payload["decision"] = "discard"
                reasons = list(decision_payload.get("reasons") or [])
                replay_reason = str(replay.get("reason") or "replay_failed").strip()
                if replay_reason and replay_reason not in reasons:
                    reasons.append(replay_reason)
                decision_payload["reasons"] = reasons
        write_json(self.decision_path(contract.run_id, round_number), decision_payload)
        feedback_distill = build_feedback_distill_payload(
            run_dir=self.run_dir(contract.run_id),
            round_dir=self.worktree_manager.round_dir(contract.run_id, round_number),
            mutation_payload=mutation_payload,
            decision_payload=decision_payload,
            baseline_scoreboard=baseline_scoreboard,
            round_scoreboard=round_scoreboard,
        )
        write_feedback_distill(self.feedback_distill_path(contract.run_id, round_number), feedback_distill)
        upsert_feedback_ledger_entry(self.feedback_ledger_path(contract.run_id), feedback_distill)

        if decision_payload["decision"] == "keep":
            lifecycle = self.worktree_manager.promote_round(contract.run_id)
        else:
            lifecycle = self.worktree_manager.discard_round(contract.run_id)

        self._append_history(contract.run_id, decision_payload)
        self._update_baseline_scoreboard(
            contract.run_id,
            baseline_scoreboard,
            decision_payload=decision_payload,
            round_scoreboard=round_scoreboard,
        )
        self._write_registry_decision_state(
            contract,
            registry=registry,
            entry=registry_entry,
            decision=str(decision_payload["decision"]),
        )
        return {
            "decision": decision_payload,
            "lifecycle": lifecycle,
        }

    def _evaluate_replay(
        self,
        *,
        contract: AutoresearchContract,
        round_number: int,
        round_payload: dict[str, Any],
        worktree_payload: dict[str, Any],
        baseline_scoreboard: dict[str, Any],
        round_scoreboard: dict[str, Any],
        decision_payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        if str(decision_payload.get("decision") or "") != "keep":
            return None
        baseline_validation = _float_metric(_lane_map(baseline_scoreboard).get("validation", {}), "avg_total_score")
        round_validation = _float_metric(_lane_map(round_scoreboard).get("validation", {}), "avg_total_score")
        if round_validation <= baseline_validation + EPSILON:
            return None
        self.validate_p2_preflight(contract)

        candidate_worktree = Path(str(worktree_payload["path"]))
        replay_dir = self.replay_dir(contract.run_id, round_number)
        if replay_dir.exists():
            shutil.rmtree(replay_dir)
        replay_dir.mkdir(parents=True, exist_ok=True)
        try:
            suites = resolve_suite_files(contract)
            train_summaries = self._run_lane_suites(
                candidate_worktree=candidate_worktree,
                contract=contract,
                suite_files=suites["train"],
                save_dir=replay_dir / "train",
            )
            validation_summaries = self._run_lane_suites(
                candidate_worktree=candidate_worktree,
                contract=contract,
                suite_files=suites["validation"],
                save_dir=replay_dir / "validation",
            )
        except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as exc:
            return {
                "status": "failed",
                "reason": "replay_execution_failed",
                "error": str(exc),
            }

        lane_summaries = {
            "train": merge_run_summaries(train_summaries),
            "validation": merge_run_summaries(validation_summaries),
        }
        replay_scoreboard = build_scoreboard(
            run_id=contract.run_id,
            baseline_sha=str(round_payload.get("base_sha") or baseline_scoreboard.get("baseline_sha") or ""),
            lane_summaries=lane_summaries,
        )
        replay_scoreboard["rounds_completed"] = int(baseline_scoreboard.get("rounds_completed") or 0)
        replay_scoreboard["best_round"] = int(baseline_scoreboard.get("best_round") or 0)
        write_scoreboard(self.replay_scoreboard_path(contract.run_id, round_number), replay_scoreboard)

        replay_validation = _float_metric(_lane_map(replay_scoreboard).get("validation", {}), "avg_total_score")
        if replay_validation + EPSILON < round_validation:
            return {
                "status": "failed",
                "reason": "replay_validation_regression",
                "champion_validation_score": baseline_validation,
                "round_validation_score": round_validation,
                "replay_validation_score": replay_validation,
                "scoreboard_ref": "replay/scoreboard.json",
            }
        return {
            "status": "passed",
            "reason": "replay_validation_non_regression",
            "champion_validation_score": baseline_validation,
            "round_validation_score": round_validation,
            "replay_validation_score": replay_validation,
            "scoreboard_ref": "replay/scoreboard.json",
        }

    def _run_lane_suites(
        self,
        *,
        candidate_worktree: Path,
        contract: AutoresearchContract,
        suite_files: list[Path],
        save_dir: Path,
    ) -> list[dict[str, Any]]:
        timeout_seconds = resolve_timeout_seconds(contract)
        materialized_output_dir = save_dir.parent / "materialized-suites" / save_dir.name

        def _run_suite(suite_file: Path) -> None:
            resolved_suite = self._resolve_candidate_suite(candidate_worktree, suite_file)
            materialized_suite = materialize_suite(
                resolved_suite,
                materialized_output_dir,
                repo_root=self.repo_root,
            )
            cmd = [
                self.python_executable,
                str(candidate_worktree / "toolchain" / "scripts" / "research" / "run_skill_suite.py"),
                "--suite",
                str(materialized_suite),
                "--save-dir",
                str(save_dir),
                "--timeout",
                str(timeout_seconds),
                *retry_policy_cli_args(contract.retry_policy),
            ]
            completed = subprocess.run(
                cmd,
                cwd=candidate_worktree,
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                stderr = completed.stderr.strip()
                raise RuntimeError(f"Candidate suite failed: {materialized_suite}\n{stderr}")

        return execute_lane_suites(suite_files, save_dir, run_suite=_run_suite)

    def _resolve_candidate_suite(self, candidate_worktree: Path, suite_file: Path) -> Path:
        resolved_suite = suite_file.expanduser().resolve()
        try:
            relative = resolved_suite.relative_to(self.repo_root)
        except ValueError:
            return resolved_suite
        candidate_suite = (candidate_worktree / relative).resolve()
        if candidate_suite.is_file():
            return candidate_suite
        return resolved_suite

    def _build_decision(
        self,
        *,
        contract: AutoresearchContract,
        round_payload: dict[str, Any],
        mutation_payload: dict[str, Any],
        baseline_scoreboard: dict[str, Any],
        round_scoreboard: dict[str, Any],
    ) -> dict[str, Any]:
        baseline_lanes = _lane_map(baseline_scoreboard)
        round_lanes = _lane_map(round_scoreboard)

        baseline_train = baseline_lanes.get("train", {})
        baseline_validation = baseline_lanes.get("validation", {})
        round_train = round_lanes.get("train", {})
        round_validation = round_lanes.get("validation", {})

        checks = {
            "train_score_improved": _float_metric(round_train, "avg_total_score")
            > _float_metric(baseline_train, "avg_total_score") + EPSILON,
            "validation_score_non_regression": _float_metric(round_validation, "avg_total_score") + EPSILON
            >= _float_metric(baseline_validation, "avg_total_score"),
            "train_pass_rate_non_regression": _float_metric(round_train, "pass_rate") + EPSILON
            >= _float_metric(baseline_train, "pass_rate"),
            "validation_pass_rate_non_regression": _float_metric(round_validation, "pass_rate") + EPSILON
            >= _float_metric(baseline_validation, "pass_rate"),
            "train_parse_error_non_regression": _float_metric(round_train, "parse_error_rate")
            <= _float_metric(baseline_train, "parse_error_rate") + EPSILON,
            "validation_parse_error_non_regression": _float_metric(round_validation, "parse_error_rate")
            <= _float_metric(baseline_validation, "parse_error_rate") + EPSILON,
            "train_timeout_non_regression": _float_metric(round_train, "timeout_rate")
            <= _float_metric(baseline_train, "timeout_rate") + EPSILON,
            "validation_timeout_non_regression": _float_metric(round_validation, "timeout_rate")
            <= _float_metric(baseline_validation, "timeout_rate") + EPSILON,
        }
        qualitative_veto = False
        decision = "keep" if all(checks.values()) and not qualitative_veto else "discard"
        reasons = [name for name, passed in checks.items() if not passed]
        if qualitative_veto:
            reasons.append("qualitative_veto")

        return {
            "round": int(round_payload["round"]),
            "run_id": contract.run_id,
            "decision": decision,
            "base_sha": str(round_payload["base_sha"]),
            "candidate_sha": str(round_payload.get("candidate_sha") or round_payload["base_sha"]),
            "mutation_id": str(mutation_payload["mutation_id"]),
            "kind": str(mutation_payload["kind"]),
            "target_paths": mutation_payload["target_paths"],
            "allowed_actions": mutation_payload["allowed_actions"],
            "expected_effect": dict(mutation_payload["expected_effect"]),
            "qualitative_veto_checks": list(contract.payload.get("qualitative_veto_checks") or []),
            "qualitative_veto_triggered": qualitative_veto,
            "checks": checks,
            "reasons": reasons,
            "baseline": {
                "train": baseline_train,
                "validation": baseline_validation,
            },
            "round_metrics": {
                "train": round_train,
                "validation": round_validation,
            },
            "decided_at": now_iso(),
        }

    def _append_history(self, run_id: str, decision_payload: dict[str, Any]) -> None:
        round_metrics = decision_payload["round_metrics"]
        train = round_metrics["train"]
        validation = round_metrics["validation"]
        append_history_round_row(
            self.history_path(run_id),
            round_number=int(decision_payload["round"]),
            kind=str(decision_payload["kind"]),
            base_sha=str(decision_payload["base_sha"]),
            candidate_sha=str(decision_payload["candidate_sha"]),
            train_score=_float_metric(train, "avg_total_score"),
            validation_score=_float_metric(validation, "avg_total_score"),
            train_parse_error_rate=_float_metric(train, "parse_error_rate"),
            validation_parse_error_rate=_float_metric(validation, "parse_error_rate"),
            decision=str(decision_payload["decision"]),
            notes=f"mutation_id={decision_payload['mutation_id']}",
        )

    def _update_baseline_scoreboard(
        self,
        run_id: str,
        scoreboard: dict[str, Any],
        *,
        decision_payload: dict[str, Any],
        round_scoreboard: dict[str, Any],
    ) -> None:
        rows = _history_rows(self.history_path(run_id))
        if decision_payload["decision"] == "keep":
            scoreboard["baseline_sha"] = str(decision_payload["candidate_sha"])
            scoreboard["lanes"] = list(round_scoreboard.get("lanes") or [])
            scoreboard["repo_tasks"] = list(round_scoreboard.get("repo_tasks") or [])
        scoreboard["rounds_completed"] = sum(1 for row in rows if row.get("decision") in {"keep", "discard"})
        scoreboard["best_round"] = self._best_round(rows)
        scoreboard["generated_at"] = now_iso()
        write_scoreboard(self.baseline_scoreboard_path(run_id), scoreboard)

    def _best_round(self, rows: list[dict[str, str]]) -> int:
        best_round = 0
        best_score = float("-inf")
        for row in rows:
            decision = row.get("decision")
            if decision not in {"baseline", "keep"}:
                continue
            try:
                validation_score = float(row.get("validation_score") or "0")
                round_number = int(row.get("round") or "0")
            except ValueError:
                continue
            if validation_score >= best_score:
                best_score = validation_score
                best_round = round_number
        return best_round
