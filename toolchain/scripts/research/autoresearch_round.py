#!/usr/bin/env python3
"""Round execution helpers for autoresearch P0.3."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from autoresearch_contract import (
    HISTORY_COLUMNS,
    AutoresearchContract,
    normalize_repo_path,
    paths_overlap,
    resolve_suite_files,
)
from autoresearch_scoreboard import build_scoreboard, load_run_summary, merge_run_summaries, write_scoreboard
from common import REPO_ROOT
from worktree_manager import AUTORESEARCH_ROOT, WorktreeManager, read_json, write_json


MUTATION_REQUIRED_FIELDS = [
    "round",
    "mutation_id",
    "kind",
    "target_paths",
    "allowed_actions",
    "instruction",
    "expected_effect",
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


def load_mutation_payload(path: Path) -> dict[str, Any]:
    payload = _load_json(path.expanduser().resolve())
    missing = [field for field in MUTATION_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"Mutation spec missing required fields: {', '.join(missing)}")
    round_number = payload.get("round")
    if not isinstance(round_number, int) or round_number <= 0:
        raise ValueError("Mutation spec field 'round' must be a positive integer.")
    payload["mutation_id"] = _require_non_empty_string(payload, "mutation_id")
    payload["kind"] = _require_non_empty_string(payload, "kind")
    payload["instruction"] = _require_non_empty_string(payload, "instruction")
    payload["expected_effect"] = _require_non_empty_string(payload, "expected_effect")
    payload["target_paths"] = _require_non_empty_string_list(payload, "target_paths")
    payload["allowed_actions"] = [
        value.lower() for value in _require_non_empty_string_list(payload, "allowed_actions")
    ]
    return payload


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

    def baseline_scoreboard_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "scoreboard.json"

    def history_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "history.tsv"

    def _normalize_contract_paths(self, values: list[str]) -> list[PurePosixPath]:
        return [normalize_repo_path(value, self.repo_root) for value in values]

    def _validate_mutation_scope(self, contract: AutoresearchContract, mutation_payload: dict[str, Any]) -> None:
        target_paths = self._normalize_contract_paths([str(value) for value in mutation_payload["target_paths"]])
        mutable_paths = self._normalize_contract_paths(contract.mutable_paths)
        frozen_paths = self._normalize_contract_paths(contract.frozen_paths)
        unsupported_actions = sorted(set(mutation_payload["allowed_actions"]) - SUPPORTED_MUTATION_ACTIONS)
        if unsupported_actions:
            raise ValueError(
                "Mutation spec allowed_actions contain unsupported values: " + ", ".join(unsupported_actions)
            )
        for target_path in target_paths:
            if not any(paths_overlap(mutable_path, target_path) for mutable_path in mutable_paths):
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
        changes = self._collect_candidate_committed_changes(candidate_worktree, base_sha=base_sha)
        changes.extend(self._collect_candidate_worktree_changes(candidate_worktree))
        for change in changes:
            action = str(change["action"])
            if action not in allowed_actions:
                rendered_paths = ", ".join(path.as_posix() for path in change["paths"])
                raise RuntimeError(f"Candidate change action is not allowed: {action} for {rendered_paths}")
            for changed_path in change["paths"]:
                if not any(paths_overlap(target_path, changed_path) for target_path in target_paths):
                    raise RuntimeError(
                        "Candidate change escapes mutation target_paths: "
                        f"{changed_path.as_posix()}"
                    )
                if any(paths_overlap(changed_path, frozen_path) for frozen_path in frozen_paths):
                    raise RuntimeError(f"Candidate change touches frozen path: {changed_path.as_posix()}")

    def ensure_prepare_allowed(self, contract: AutoresearchContract, mutation_payload: dict[str, Any]) -> None:
        baseline_scoreboard = self.baseline_scoreboard_path(contract.run_id)
        if not baseline_scoreboard.is_file():
            raise FileNotFoundError("Baseline scoreboard missing. Run baseline before prepare-round.")
        next_round = self.worktree_manager.next_round_number(contract.run_id)
        if next_round > int(contract.payload["max_rounds"]):
            raise RuntimeError(
                f"Next round {next_round} exceeds max_rounds={contract.payload['max_rounds']} for run {contract.run_id}"
            )
        expected_round = int(mutation_payload["round"])
        if expected_round != next_round:
            raise ValueError(
                f"Mutation spec round={expected_round} does not match next round {next_round} for run {contract.run_id}"
            )
        self._validate_mutation_scope(contract, mutation_payload)

    def stage_mutation(self, run_id: str, round_number: int, mutation_payload: dict[str, Any]) -> Path:
        mutation_path = self.mutation_path(run_id, round_number)
        write_json(mutation_path, mutation_payload)
        return mutation_path

    def run_round(self, contract: AutoresearchContract) -> dict[str, Any]:
        active = self.worktree_manager.load_active_round(contract.run_id)
        round_payload = active["round"]
        worktree_payload = active["worktree"]
        round_number = int(round_payload["round"])
        if str(round_payload.get("state")) != "candidate_active":
            raise RuntimeError("run-round requires the active round to be in candidate_active state.")
        round_dir = self.worktree_manager.round_dir(contract.run_id, round_number)
        mutation_payload = read_json(self.mutation_path(contract.run_id, round_number))
        agent_report = self.agent_report_path(contract.run_id, round_number)
        if not agent_report.is_file():
            raise FileNotFoundError(f"Missing agent report: {agent_report}")
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
            suite_files=suites["train"],
            save_dir=round_dir / "train",
        )
        validation_summaries = self._run_lane_suites(
            candidate_worktree=candidate_worktree,
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
        round_number = int(round_payload["round"])
        if str(round_payload.get("state")) != "evaluated":
            raise RuntimeError("decide-round requires the active round to be in evaluated state.")
        mutation_payload = read_json(self.mutation_path(contract.run_id, round_number))
        baseline_scoreboard = read_json(self.baseline_scoreboard_path(contract.run_id))
        round_scoreboard = read_json(self.round_scoreboard_path(contract.run_id, round_number))
        decision_payload = self._build_decision(
            contract=contract,
            round_payload=round_payload,
            mutation_payload=mutation_payload,
            baseline_scoreboard=baseline_scoreboard,
            round_scoreboard=round_scoreboard,
        )
        write_json(self.decision_path(contract.run_id, round_number), decision_payload)

        if decision_payload["decision"] == "keep":
            lifecycle = self.worktree_manager.promote_round(contract.run_id)
        else:
            lifecycle = self.worktree_manager.discard_round(contract.run_id)

        self._append_history(contract.run_id, decision_payload)
        self._update_baseline_scoreboard(contract.run_id, baseline_scoreboard)
        return {
            "decision": decision_payload,
            "lifecycle": lifecycle,
        }

    def _run_lane_suites(
        self,
        *,
        candidate_worktree: Path,
        suite_files: list[Path],
        save_dir: Path,
    ) -> list[dict[str, Any]]:
        save_dir.mkdir(parents=True, exist_ok=True)
        summaries: list[dict[str, Any]] = []
        for suite_file in suite_files:
            before = {path for path in save_dir.iterdir() if path.is_dir()}
            resolved_suite = self._resolve_candidate_suite(candidate_worktree, suite_file)
            cmd = [
                self.python_executable,
                str(candidate_worktree / "toolchain" / "scripts" / "research" / "run_skill_suite.py"),
                "--suite",
                str(resolved_suite),
                "--save-dir",
                str(save_dir),
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
                raise RuntimeError(f"Candidate suite failed: {resolved_suite}\n{stderr}")
            summary_path = _capture_new_summary(save_dir, before)
            summaries.append(load_run_summary(summary_path))
        return summaries

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
            "decision": decision,
            "base_sha": str(round_payload["base_sha"]),
            "candidate_sha": str(round_payload.get("candidate_sha") or round_payload["base_sha"]),
            "mutation_id": str(mutation_payload["mutation_id"]),
            "kind": str(mutation_payload["kind"]),
            "target_paths": mutation_payload["target_paths"],
            "allowed_actions": mutation_payload["allowed_actions"],
            "expected_effect": str(mutation_payload["expected_effect"]),
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

    def _update_baseline_scoreboard(self, run_id: str, scoreboard: dict[str, Any]) -> None:
        rows = _history_rows(self.history_path(run_id))
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
