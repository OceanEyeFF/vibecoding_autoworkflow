#!/usr/bin/env python3
"""Aggregate run-level and skill-level autoresearch status artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from autoresearch_contract import P2_TARGET_TASK_TO_RUNNER_TASK
from common import REPO_ROOT


AUTORESEARCH_ROOT = REPO_ROOT / ".autoworkflow" / "autoresearch"
RUN_STATUS_INDEX_NAME = "run-status-index.json"
SKILL_TRAINING_STATUS_NAME = "skill-training-status.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object required: {path}")
    return payload


def _history_rows(history_path: Path) -> list[dict[str, str]]:
    if not history_path.is_file():
        return []
    lines = [line for line in history_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) <= 1:
        return []
    header = lines[0].split("\t")
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) != len(header):
            continue
        rows.append(dict(zip(header, parts, strict=True)))
    return rows


def _relative_path(path: Path, *, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _round_dir_sort_key(path: Path) -> tuple[int, str]:
    suffix = path.name.removeprefix("round-")
    try:
        return int(suffix), path.name
    except ValueError:
        return 0, path.name


def _round_state(run_dir: Path, runtime: dict[str, Any] | None) -> tuple[int | None, str | None]:
    if not runtime:
        return None, None
    active_round = runtime.get("active_round")
    if active_round is None:
        return None, None
    round_number = int(active_round)
    round_payload = _read_json(run_dir / "rounds" / f"round-{round_number:03d}" / "round.json")
    return round_number, (str(round_payload.get("state") or "").strip() if round_payload else None)


def _latest_decision(run_dir: Path) -> tuple[str | None, int | None, str | None]:
    rounds_root = run_dir / "rounds"
    if not rounds_root.is_dir():
        return None, None, None
    latest_round = None
    latest_payload = None
    for round_dir in sorted((path for path in rounds_root.iterdir() if path.is_dir()), key=_round_dir_sort_key):
        decision_payload = _read_json(round_dir / "decision.json")
        if not decision_payload:
            continue
        latest_round = int(decision_payload.get("round") or 0)
        latest_payload = decision_payload
    if latest_payload is None:
        return None, None, None
    decided_at = str(latest_payload.get("decided_at") or "").strip() or None
    return str(latest_payload.get("decision") or "").strip() or None, latest_round, decided_at


def _lane_metrics(scoreboard: dict[str, Any] | None, lane_name: str) -> dict[str, Any]:
    if not scoreboard:
        return {}
    for lane in scoreboard.get("lanes") or []:
        if isinstance(lane, dict) and str(lane.get("lane_name") or "").strip() == lane_name:
            return lane
    return {}


def _activity_at(
    *,
    contract: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
    scoreboard: dict[str, Any] | None,
    latest_decision_at: str | None,
) -> str | None:
    candidates = [
        str(runtime.get("updated_at") or "").strip() if runtime else "",
        str(scoreboard.get("generated_at") or "").strip() if scoreboard else "",
        latest_decision_at or "",
        str(contract.get("updated_at") or "").strip() if contract else "",
    ]
    values = sorted(candidate for candidate in candidates if candidate)
    return values[-1] if values else None


def _derive_training_status(
    *,
    has_contract: bool,
    has_scoreboard: bool,
    rounds_completed: int,
    max_rounds: int | None,
    active_round_state: str | None,
) -> str:
    if not has_contract:
        return "unknown"
    if active_round_state:
        return f"round_{active_round_state}"
    if not has_scoreboard:
        return "awaiting_baseline"
    if max_rounds is not None and max_rounds > 0 and rounds_completed >= max_rounds:
        return "max_rounds_reached"
    if rounds_completed > 0:
        return "awaiting_next_round"
    return "baseline_completed"


def summarize_run(run_dir: Path, *, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    contract = _read_json(run_dir / "contract.json")
    runtime = _read_json(run_dir / "runtime.json")
    scoreboard = _read_json(run_dir / "scoreboard.json")
    history_rows = _history_rows(run_dir / "history.tsv")
    latest_decision, latest_decision_round, latest_decision_at = _latest_decision(run_dir)
    active_round, active_round_state = _round_state(run_dir, runtime)

    run_id = str((contract or {}).get("run_id") or run_dir.name).strip() or run_dir.name
    tracked_target = str((contract or {}).get("target_task") or "").strip() or None
    max_rounds_raw = (contract or {}).get("max_rounds")
    max_rounds = int(max_rounds_raw) if isinstance(max_rounds_raw, int) else None
    rounds_completed = 0
    best_round = 0
    if scoreboard:
        rounds_completed = int(scoreboard.get("rounds_completed") or 0)
        best_round = int(scoreboard.get("best_round") or 0)
    elif history_rows:
        rounds_completed = sum(1 for row in history_rows if row.get("decision") in {"keep", "discard"})

    train_lane = _lane_metrics(scoreboard, "train")
    validation_lane = _lane_metrics(scoreboard, "validation")
    activity_at = _activity_at(
        contract=contract,
        runtime=runtime,
        scoreboard=scoreboard,
        latest_decision_at=latest_decision_at,
    )
    training_status = _derive_training_status(
        has_contract=contract is not None,
        has_scoreboard=scoreboard is not None,
        rounds_completed=rounds_completed,
        max_rounds=max_rounds,
        active_round_state=active_round_state,
    )

    return {
        "run_id": run_id,
        "run_dir": _relative_path(run_dir, repo_root=repo_root),
        "target_task": tracked_target,
        "target_prompt_path": (str(contract.get("target_prompt_path") or "").strip() or None) if contract else None,
        "worker_backend": (str(contract.get("worker_backend") or "").strip() or None) if contract else None,
        "expected_backend": (str(contract.get("expected_backend") or "").strip() or None) if contract else None,
        "expected_judge_backend": (
            str(contract.get("expected_judge_backend") or "").strip() or None
        ) if contract else None,
        "tracking_scope": "p2_targeted" if tracked_target in P2_TARGET_TASK_TO_RUNNER_TASK else "non_targeted",
        "training_status": training_status,
        "activity_at": activity_at,
        "max_rounds": max_rounds,
        "rounds_completed": rounds_completed,
        "best_round": best_round,
        "active_round": active_round,
        "active_round_state": active_round_state,
        "latest_decision": latest_decision,
        "latest_decision_round": latest_decision_round,
        "history_rows": len(history_rows),
        "champion_sha": (str(runtime.get("champion_sha") or "").strip() or None) if runtime else None,
        "baseline_sha": (str(scoreboard.get("baseline_sha") or "").strip() or None) if scoreboard else None,
        "train_backend": (str(train_lane.get("backend") or "").strip() or None),
        "train_judge_backend": (str(train_lane.get("judge_backend") or "").strip() or None),
        "train_score": float(train_lane.get("avg_total_score") or 0.0) if train_lane else None,
        "train_pass_rate": float(train_lane.get("pass_rate") or 0.0) if train_lane else None,
        "train_parse_error_rate": float(train_lane.get("parse_error_rate") or 0.0) if train_lane else None,
        "validation_backend": (str(validation_lane.get("backend") or "").strip() or None),
        "validation_judge_backend": (str(validation_lane.get("judge_backend") or "").strip() or None),
        "validation_score": float(validation_lane.get("avg_total_score") or 0.0) if validation_lane else None,
        "validation_pass_rate": float(validation_lane.get("pass_rate") or 0.0) if validation_lane else None,
        "validation_parse_error_rate": float(validation_lane.get("parse_error_rate") or 0.0)
        if validation_lane
        else None,
    }


def collect_run_summaries(
    *,
    autoresearch_root: Path = AUTORESEARCH_ROOT,
    repo_root: Path = REPO_ROOT,
) -> list[dict[str, Any]]:
    if not autoresearch_root.exists():
        return []
    summaries = []
    for run_dir in sorted(path for path in autoresearch_root.iterdir() if path.is_dir()):
        if run_dir.name == "__pycache__":
            continue
        summaries.append(summarize_run(run_dir, repo_root=repo_root))
    summaries.sort(
        key=lambda item: (
            str(item.get("activity_at") or ""),
            str(item.get("run_id") or ""),
        ),
        reverse=True,
    )
    return summaries


def _canonical_skill_entries(*, repo_root: Path) -> list[dict[str, str]]:
    entries = []
    for path in sorted(repo_root.glob("product/*/skills/*/SKILL.md")):
        skill_id = path.parent.name
        partition = path.parents[2].name
        entries.append(
            {
                "skill_id": skill_id,
                "partition": partition,
                "canonical_skill_path": _relative_path(path, repo_root=repo_root),
            }
        )
    return entries


def build_skill_training_status(
    run_summaries: list[dict[str, Any]],
    *,
    autoresearch_root: Path = AUTORESEARCH_ROOT,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    skills = []
    by_skill: dict[str, list[dict[str, Any]]] = {}
    for summary in run_summaries:
        target_task = str(summary.get("target_task") or "").strip()
        if not target_task:
            continue
        by_skill.setdefault(target_task, []).append(summary)

    for entry in _canonical_skill_entries(repo_root=repo_root):
        skill_id = entry["skill_id"]
        runs = by_skill.get(skill_id, [])
        tracked = skill_id in P2_TARGET_TASK_TO_RUNNER_TASK
        latest = runs[0] if runs else None
        payload: dict[str, Any] = {
            **entry,
            "autoresearch_tracking": "tracked" if tracked else "not_supported_by_autoresearch",
            "runs_total": len(runs),
            "run_ids": [str(run["run_id"]) for run in runs],
        }
        if not tracked:
            payload["training_status"] = "not_supported_by_autoresearch"
        elif latest is None:
            payload["training_status"] = "not_started"
        else:
            payload.update(
                {
                    "training_status": latest["training_status"],
                    "latest_run_id": latest["run_id"],
                    "latest_run_dir": latest["run_dir"],
                    "latest_activity_at": latest["activity_at"],
                    "worker_backend": latest["worker_backend"],
                    "expected_backend": latest["expected_backend"],
                    "expected_judge_backend": latest["expected_judge_backend"],
                    "rounds_completed": latest["rounds_completed"],
                    "max_rounds": latest["max_rounds"],
                    "best_round": latest["best_round"],
                    "latest_decision": latest["latest_decision"],
                    "active_round": latest["active_round"],
                    "active_round_state": latest["active_round_state"],
                    "train_score": latest["train_score"],
                    "validation_score": latest["validation_score"],
                    "train_pass_rate": latest["train_pass_rate"],
                    "validation_pass_rate": latest["validation_pass_rate"],
                    "train_parse_error_rate": latest["train_parse_error_rate"],
                    "validation_parse_error_rate": latest["validation_parse_error_rate"],
                    "champion_sha": latest["champion_sha"],
                }
            )
        skills.append(payload)

    return {
        "generated_at": now_iso(),
        "autoresearch_root": _relative_path(autoresearch_root, repo_root=repo_root),
        "skills": skills,
    }


def refresh_status_indexes(
    *,
    autoresearch_root: Path = AUTORESEARCH_ROOT,
    repo_root: Path = REPO_ROOT,
) -> tuple[Path, Path]:
    root = autoresearch_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    run_summaries = collect_run_summaries(autoresearch_root=root, repo_root=repo_root)
    run_index_payload = {
        "generated_at": now_iso(),
        "autoresearch_root": _relative_path(root, repo_root=repo_root),
        "runs": run_summaries,
    }
    run_index_path = root / RUN_STATUS_INDEX_NAME
    run_index_path.write_text(json.dumps(run_index_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    skill_payload = build_skill_training_status(
        run_summaries,
        autoresearch_root=root,
        repo_root=repo_root,
    )
    skill_index_path = root / SKILL_TRAINING_STATUS_NAME
    skill_index_path.write_text(json.dumps(skill_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return run_index_path, skill_index_path
