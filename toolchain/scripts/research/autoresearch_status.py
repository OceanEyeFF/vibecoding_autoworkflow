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


def _read_json_best_effort(path: Path) -> dict[str, Any] | None:
    try:
        return _read_json(path)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


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


def _discover_interrupted_round(run_dir: Path) -> tuple[int | None, str | None]:
    rounds_root = run_dir / "rounds"
    if not rounds_root.is_dir():
        return None, None
    interrupted_rounds: list[tuple[int, str]] = []
    for round_dir in sorted((path for path in rounds_root.iterdir() if path.is_dir()), key=_round_dir_sort_key):
        round_payload = _read_json(round_dir / "round.json")
        if not round_payload:
            continue
        state = str(round_payload.get("state") or "").strip()
        if state not in {"prepared", "candidate_active", "evaluating", "evaluated"}:
            continue
        round_number_raw = round_payload.get("round")
        try:
            round_number = int(round_number_raw)
        except (TypeError, ValueError):
            continue
        interrupted_rounds.append((round_number, state))
    if not interrupted_rounds:
        return None, None
    if len(interrupted_rounds) > 1:
        return interrupted_rounds[-1][0], "cleanup_required_multiple_active_rounds"
    round_number, state = interrupted_rounds[0]
    return round_number, f"{state}_recovery_required"


def _round_state(run_dir: Path, runtime: dict[str, Any] | None) -> tuple[int | None, str | None]:
    if runtime:
        active_round = runtime.get("active_round")
        if active_round is not None:
            round_number = int(active_round)
            round_payload = _read_json(run_dir / "rounds" / f"round-{round_number:03d}" / "round.json")
            if round_payload:
                return round_number, str(round_payload.get("state") or "").strip() or None
            return round_number, "cleanup_required_missing_round_json"
    return _discover_interrupted_round(run_dir)


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


def _latest_decision_best_effort(run_dir: Path) -> tuple[str | None, int | None, str | None]:
    try:
        return _latest_decision(run_dir)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None, None, None


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


def _summarize_malformed_run(run_dir: Path, *, repo_root: Path, error: Exception) -> dict[str, str | None]:
    contract = _read_json_best_effort(run_dir / "contract.json")
    runtime = _read_json_best_effort(run_dir / "runtime.json")
    scoreboard = _read_json_best_effort(run_dir / "scoreboard.json")
    latest_decision, _latest_decision_round, latest_decision_at = _latest_decision_best_effort(run_dir)
    run_id = str((contract or {}).get("run_id") or run_dir.name).strip() or run_dir.name
    target_task = str((contract or {}).get("target_task") or "").strip() or None
    activity_at = _activity_at(
        contract=contract,
        runtime=runtime,
        scoreboard=scoreboard,
        latest_decision_at=latest_decision_at,
    )
    return {
        "run_id": run_id,
        "run_dir": _relative_path(run_dir, repo_root=repo_root),
        "target_task": target_task,
        "activity_at": activity_at,
        "error": str(error),
    }


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
    if max_rounds is not None and max_rounds > 0 and rounds_completed >= max_rounds:
        return "max_rounds_reached"
    if not has_scoreboard:
        if rounds_completed > 0:
            return "awaiting_next_round"
        return "awaiting_baseline"
    if rounds_completed > 0:
        return "awaiting_next_round"
    return "baseline_completed"


def _run_has_recorded_artifacts(
    run_dir: Path,
    *,
    runtime: dict[str, Any] | None,
    scoreboard: dict[str, Any] | None,
    history_rows: list[dict[str, str]],
    latest_decision: str | None,
    active_round_state: str | None,
) -> bool:
    if runtime is not None or scoreboard is not None or history_rows:
        return True
    if latest_decision is not None or active_round_state is not None:
        return True
    rounds_root = run_dir / "rounds"
    return rounds_root.is_dir() and any(path.is_dir() for path in rounds_root.iterdir())


def summarize_run(run_dir: Path, *, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    contract = _read_json(run_dir / "contract.json")
    runtime = _read_json(run_dir / "runtime.json")
    scoreboard = _read_json(run_dir / "scoreboard.json")
    history_rows = _history_rows(run_dir / "history.tsv")
    latest_decision, latest_decision_round, latest_decision_at = _latest_decision(run_dir)
    active_round, active_round_state = _round_state(run_dir, runtime)
    if contract is None and _run_has_recorded_artifacts(
        run_dir,
        runtime=runtime,
        scoreboard=scoreboard,
        history_rows=history_rows,
        latest_decision=latest_decision,
        active_round_state=active_round_state,
    ):
        raise RuntimeError("Missing contract.json for run directory with recorded artifacts.")

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
    summaries, _errors = collect_run_summaries_best_effort(
        autoresearch_root=autoresearch_root,
        repo_root=repo_root,
        strict=True,
    )
    return summaries


def collect_run_summaries_best_effort(
    *,
    autoresearch_root: Path = AUTORESEARCH_ROOT,
    repo_root: Path = REPO_ROOT,
    strict: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    if not autoresearch_root.exists():
        return [], []
    summaries: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for run_dir in sorted(path for path in autoresearch_root.iterdir() if path.is_dir()):
        if run_dir.name == "__pycache__":
            continue
        try:
            summaries.append(summarize_run(run_dir, repo_root=repo_root))
        except (FileNotFoundError, RuntimeError, TypeError, ValueError) as exc:
            if strict:
                raise
            errors.append(_summarize_malformed_run(run_dir, repo_root=repo_root, error=exc))
    summaries.sort(
        key=lambda item: (
            str(item.get("activity_at") or ""),
            str(item.get("run_id") or ""),
        ),
        reverse=True,
    )
    return summaries, errors


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
    malformed_runs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    skills = []
    by_skill: dict[str, list[dict[str, Any]]] = {}
    for summary in run_summaries:
        target_task = str(summary.get("target_task") or "").strip()
        if not target_task:
            continue
        by_skill.setdefault(target_task, []).append(summary)
    malformed_by_skill: dict[str, list[dict[str, Any]]] = {}
    for malformed in malformed_runs or []:
        target_task = str(malformed.get("target_task") or "").strip()
        if not target_task:
            continue
        malformed_by_skill.setdefault(target_task, []).append(malformed)

    def _sort_latest(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        items.sort(
            key=lambda item: (
                str(item.get("activity_at") or ""),
                str(item.get("run_id") or ""),
            ),
            reverse=True,
        )
        return items

    for entry in _canonical_skill_entries(repo_root=repo_root):
        skill_id = entry["skill_id"]
        runs = _sort_latest(list(by_skill.get(skill_id, [])))
        malformed_for_skill = _sort_latest(list(malformed_by_skill.get(skill_id, [])))
        tracked = skill_id in P2_TARGET_TASK_TO_RUNNER_TASK
        latest = runs[0] if runs else None
        latest_malformed = malformed_for_skill[0] if malformed_for_skill else None
        malformed_newer_than_healthy = False
        if latest_malformed is not None:
            malformed_key = (
                str(latest_malformed.get("activity_at") or ""),
                str(latest_malformed.get("run_id") or ""),
            )
            healthy_key = (
                str(latest.get("activity_at") or "") if latest is not None else "",
                str(latest.get("run_id") or "") if latest is not None else "",
            )
            malformed_newer_than_healthy = latest is None or malformed_key >= healthy_key
        payload: dict[str, Any] = {
            **entry,
            "autoresearch_tracking": "tracked" if tracked else "not_supported_by_autoresearch",
            "runs_total": len(runs),
            "run_ids": [str(run["run_id"]) for run in runs],
            "malformed_runs_total": len(malformed_for_skill),
            "malformed_run_ids": [str(run["run_id"]) for run in malformed_for_skill],
        }
        if not tracked:
            payload["training_status"] = "not_supported_by_autoresearch"
        elif malformed_newer_than_healthy and latest_malformed is not None:
            payload.update(
                {
                    "training_status": "malformed_run_present",
                    "latest_run_id": latest_malformed["run_id"],
                    "latest_run_dir": latest_malformed["run_dir"],
                    "latest_activity_at": latest_malformed["activity_at"],
                    "latest_malformed_error": latest_malformed["error"],
                }
            )
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


def build_status_index_payloads(
    *,
    autoresearch_root: Path = AUTORESEARCH_ROOT,
    repo_root: Path = REPO_ROOT,
    strict: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    run_summaries, malformed_runs = collect_run_summaries_best_effort(
        autoresearch_root=autoresearch_root,
        repo_root=repo_root,
        strict=strict,
    )
    run_index_payload = {
        "generated_at": now_iso(),
        "autoresearch_root": _relative_path(autoresearch_root, repo_root=repo_root),
        "runs": run_summaries,
        "malformed_runs": malformed_runs,
    }
    skill_payload = build_skill_training_status(
        run_summaries,
        autoresearch_root=autoresearch_root,
        repo_root=repo_root,
        malformed_runs=malformed_runs,
    )
    return run_index_payload, skill_payload


def classify_operator_signal(training_status: str | None) -> str:
    status = str(training_status or "").strip()
    if not status:
        return "unknown"
    if "cleanup_required" in status:
        return "cleanup-required"
    if status.endswith("_recovery_required"):
        return "recovery"
    if status.startswith("round_"):
        return "active"
    if status == "max_rounds_reached":
        return "terminal"
    if status == "not_supported_by_autoresearch":
        return "unsupported"
    if status == "malformed_run_present":
        return "cleanup-required"
    if status in {"not_started", "awaiting_baseline", "baseline_completed", "awaiting_next_round"}:
        return "waiting"
    return "unknown"


def summarize_operator_action(item: dict[str, Any]) -> str:
    training_status = str(item.get("training_status") or "").strip()
    if "cleanup_required" in training_status:
        return "cleanup-round first"
    if training_status in {"round_evaluating", "round_evaluating_recovery_required"}:
        return "wait for run-round to finish, or inspect and cleanup-round if stuck"
    if training_status in {"round_evaluated", "round_evaluated_recovery_required"}:
        return "decide-round next, or cleanup-round if the round is no longer usable"
    if training_status.endswith("_recovery_required"):
        return "inspect round state, then recover or cleanup-round"
    if training_status == "round_candidate_active":
        return "continue active round, then run-round/decide-round, or cleanup-round"
    if training_status == "round_prepared":
        return "continue active round or cleanup-round"
    if training_status == "awaiting_baseline":
        return "run baseline"
    if training_status in {"baseline_completed", "awaiting_next_round"}:
        return "prepare-round when ready"
    if training_status == "not_started":
        return "init + baseline when ready"
    if training_status == "max_rounds_reached":
        return "terminal; inspect results or start a new run"
    if training_status == "malformed_run_present":
        return "inspect malformed run artifacts, then repair or cleanup-round"
    if training_status == "not_supported_by_autoresearch":
        return "not tracked by autoresearch"
    return "-"


def _stringify_cell(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    text = str(value).strip()
    return text or "-"


def _format_table(columns: list[tuple[str, str]], rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "(none)"
    headers = [header for header, _key in columns]
    widths = [len(header) for header in headers]
    rendered_rows: list[list[str]] = []
    for row in rows:
        rendered = [_stringify_cell(row.get(key)) for _header, key in columns]
        rendered_rows.append(rendered)
        for index, cell in enumerate(rendered):
            widths[index] = max(widths[index], len(cell))
    lines = ["  ".join(header.ljust(widths[index]) for index, header in enumerate(headers))]
    lines.append("  ".join("-" * widths[index] for index in range(len(widths))))
    for rendered in rendered_rows:
        lines.append("  ".join(cell.ljust(widths[index]) for index, cell in enumerate(rendered)))
    return "\n".join(lines)


def _operator_run_rows(
    runs: list[dict[str, Any]],
    malformed_runs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        rows.append(
            {
                "run_id": run.get("run_id"),
                "signal": classify_operator_signal(run.get("training_status")),
                "status": run.get("training_status"),
                "active_round": run.get("active_round"),
                "latest_decision": run.get("latest_decision"),
                "next_action": summarize_operator_action(run),
                "activity_at": run.get("activity_at"),
                "run_dir": run.get("run_dir"),
            }
        )
    for malformed in malformed_runs:
        rows.append(
            {
                "run_id": malformed.get("run_id"),
                "signal": "cleanup-required",
                "status": "malformed_run_present",
                "active_round": None,
                "latest_decision": None,
                "next_action": "inspect malformed run artifacts, then repair or cleanup-round",
                "activity_at": malformed.get("activity_at"),
                "run_dir": malformed.get("run_dir"),
            }
        )
    rows.sort(
        key=lambda item: (
            str(item.get("activity_at") or ""),
            str(item.get("run_id") or ""),
        ),
        reverse=True,
    )
    return rows


def render_operator_summary(
    *,
    autoresearch_root: Path = AUTORESEARCH_ROOT,
    repo_root: Path = REPO_ROOT,
) -> str:
    run_index_payload, skill_payload = build_status_index_payloads(
        autoresearch_root=autoresearch_root,
        repo_root=repo_root,
        strict=False,
    )
    runs = list(run_index_payload.get("runs") or [])
    malformed_runs = list(run_index_payload.get("malformed_runs") or [])
    operator_runs = _operator_run_rows(runs, malformed_runs)
    latest_run = operator_runs[0] if operator_runs else None
    tracked_skills = []
    for skill in skill_payload.get("skills") or []:
        if str(skill.get("autoresearch_tracking") or "").strip() != "tracked":
            continue
        latest_run_id = skill.get("latest_run_id")
        rounds_completed = skill.get("rounds_completed")
        max_rounds = skill.get("max_rounds")
        if latest_run_id is None:
            rounds_display = "-"
        elif max_rounds is None:
            rounds_display = _stringify_cell(rounds_completed)
        else:
            rounds_display = f"{_stringify_cell(rounds_completed)}/{_stringify_cell(max_rounds)}"
        tracked_skills.append(
            {
                "skill": skill.get("skill_id"),
                "signal": classify_operator_signal(skill.get("training_status")),
                "status": skill.get("training_status"),
                "latest_run": latest_run_id,
                "rounds": rounds_display,
                "latest_decision": skill.get("latest_decision"),
                "next_action": summarize_operator_action(skill),
            }
        )
    action_needed_runs = []
    for run in operator_runs:
        signal = str(run.get("signal") or "").strip()
        if signal not in {"active", "recovery", "cleanup-required"}:
            continue
        action_needed_runs.append(run)

    lines = [
        "autoresearch_status_summary",
        f"autoresearch_root: {run_index_payload['autoresearch_root']}",
        f"generated_at: {run_index_payload['generated_at']}",
        f"malformed_runs_skipped: {len(malformed_runs)}",
    ]
    if latest_run is None:
        lines.append("latest_run: -")
    else:
        lines.append(
            "latest_run: "
            f"{_stringify_cell(latest_run.get('run_id'))} "
            f"[{_stringify_cell(latest_run.get('signal'))} / "
            f"{_stringify_cell(latest_run.get('status'))}]"
        )
    lines.extend(
        [
            "",
            "tracked_skills",
            _format_table(
                [
                    ("skill", "skill"),
                    ("signal", "signal"),
                    ("status", "status"),
                    ("latest_run", "latest_run"),
                    ("rounds", "rounds"),
                    ("latest_decision", "latest_decision"),
                    ("next_action", "next_action"),
                ],
                tracked_skills,
            ),
            "",
            "action_needed_runs",
            _format_table(
                [
                    ("run_id", "run_id"),
                    ("signal", "signal"),
                    ("status", "status"),
                    ("active_round", "active_round"),
                    ("latest_decision", "latest_decision"),
                    ("next_action", "next_action"),
                ],
                action_needed_runs,
            ),
        ]
    )
    if malformed_runs:
        lines.extend(
            [
                "",
                "malformed_runs",
                _format_table(
                    [
                        ("run_dir", "run_dir"),
                        ("error", "error"),
                    ],
                    malformed_runs,
                ),
            ]
        )
    return "\n".join(lines)


def refresh_status_indexes(
    *,
    autoresearch_root: Path = AUTORESEARCH_ROOT,
    repo_root: Path = REPO_ROOT,
) -> tuple[Path, Path]:
    root = autoresearch_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    run_index_payload, skill_payload = build_status_index_payloads(
        autoresearch_root=root,
        repo_root=repo_root,
        strict=False,
    )
    run_index_path = root / RUN_STATUS_INDEX_NAME
    run_index_path.write_text(json.dumps(run_index_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    skill_index_path = root / SKILL_TRAINING_STATUS_NAME
    skill_index_path.write_text(json.dumps(skill_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return run_index_path, skill_index_path
