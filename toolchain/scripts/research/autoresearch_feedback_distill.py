#!/usr/bin/env python3
"""Deterministic feedback distillation and adaptive-family helpers for autoresearch P1.3."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import SCHEMAS_ROOT


AUTORESEARCH_FEEDBACK_DISTILL_SCHEMA_PATH = SCHEMAS_ROOT / "autoresearch-feedback-distill.schema.json"
FEEDBACK_DISTILL_VERSION = 1
EPSILON = 1e-9


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _lane_map(scoreboard: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lanes = scoreboard.get("lanes") or []
    return {
        str(lane.get("lane_name")): lane
        for lane in lanes
        if isinstance(lane, dict) and lane.get("lane_name")
    }


def _lane_metric(lane: dict[str, Any] | None, key: str) -> float:
    if not isinstance(lane, dict):
        return 0.0
    value = lane.get(key)
    return float(value) if isinstance(value, (int, float)) else 0.0


def _relative_ref(path: Path, *, run_dir: Path) -> str:
    return path.expanduser().resolve().relative_to(run_dir.expanduser().resolve()).as_posix()


def _compute_regression_flags(
    *,
    baseline_scoreboard: dict[str, Any],
    round_scoreboard: dict[str, Any],
) -> list[str]:
    baseline_lanes = _lane_map(baseline_scoreboard)
    round_lanes = _lane_map(round_scoreboard)
    baseline_train = baseline_lanes.get("train", {})
    baseline_validation = baseline_lanes.get("validation", {})
    round_train = round_lanes.get("train", {})
    round_validation = round_lanes.get("validation", {})

    flags: list[str] = []
    if _lane_metric(round_train, "avg_total_score") + EPSILON < _lane_metric(baseline_train, "avg_total_score"):
        flags.append("train_drop")
    if _lane_metric(round_validation, "avg_total_score") + EPSILON < _lane_metric(
        baseline_validation, "avg_total_score"
    ):
        flags.append("validation_drop")
    if _lane_metric(round_train, "pass_rate") + EPSILON < _lane_metric(baseline_train, "pass_rate"):
        flags.append("train_pass_rate_drop")
    if _lane_metric(round_validation, "pass_rate") + EPSILON < _lane_metric(baseline_validation, "pass_rate"):
        flags.append("validation_pass_rate_drop")
    if _lane_metric(round_train, "parse_error_rate") > _lane_metric(baseline_train, "parse_error_rate") + EPSILON:
        flags.append("train_parse_error_increase")
    if _lane_metric(round_validation, "parse_error_rate") > _lane_metric(
        baseline_validation, "parse_error_rate"
    ) + EPSILON:
        flags.append("validation_parse_error_increase")
    if _lane_metric(round_train, "timeout_rate") > _lane_metric(baseline_train, "timeout_rate") + EPSILON:
        flags.append("train_timeout_increase")
    if _lane_metric(round_validation, "timeout_rate") > _lane_metric(
        baseline_validation, "timeout_rate"
    ) + EPSILON:
        flags.append("validation_timeout_increase")
    return flags


def _signal_strength(
    *,
    decision: str,
    train_score_delta: float,
    regression_flags: list[str],
) -> str:
    if decision == "keep":
        return "positive"
    if train_score_delta > EPSILON:
        return "mixed"
    if regression_flags:
        return "negative"
    return "mixed"


def validate_feedback_distill_payload(payload: dict[str, Any]) -> None:
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError("jsonschema is required to validate autoresearch feedback distill payloads.") from exc

    schema = json.loads(AUTORESEARCH_FEEDBACK_DISTILL_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=payload, schema=schema)


def load_feedback_distill_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"feedback distill payload must be a JSON object: {path}")
    validate_feedback_distill_payload(payload)
    return payload


def write_feedback_distill(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    validate_feedback_distill_payload(payload)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def load_feedback_ledger(path: Path) -> list[dict[str, Any]]:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        return []
    entries: list[dict[str, Any]] = []
    for line in resolved.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"feedback ledger line must be a JSON object: {path}")
        validate_feedback_distill_payload(payload)
        entries.append(payload)
    return entries


def upsert_feedback_ledger_entry(path: Path, payload: dict[str, Any]) -> None:
    validate_feedback_distill_payload(payload)
    resolved = path.expanduser().resolve()
    existing = load_feedback_ledger(resolved)
    entry_key = (
        str(payload["run_id"]),
        int(payload["round"]),
        str(payload["mutation_id"]),
    )
    filtered = [
        item
        for item in existing
        if (
            str(item.get("run_id") or ""),
            int(item.get("round") or 0),
            str(item.get("mutation_id") or ""),
        )
        != entry_key
    ]
    filtered.append(payload)
    filtered.sort(key=lambda item: (int(item["round"]), str(item["mutation_id"])))
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8") as handle:
        for item in filtered:
            handle.write(json.dumps(item, ensure_ascii=True, sort_keys=True) + "\n")


def build_feedback_distill_payload(
    *,
    run_dir: Path,
    round_dir: Path,
    mutation_payload: dict[str, Any],
    decision_payload: dict[str, Any],
    baseline_scoreboard: dict[str, Any],
    round_scoreboard: dict[str, Any],
    distilled_at: str | None = None,
) -> dict[str, Any]:
    run_dir = run_dir.expanduser().resolve()
    round_dir = round_dir.expanduser().resolve()

    baseline_lanes = _lane_map(baseline_scoreboard)
    round_lanes = _lane_map(round_scoreboard)
    baseline_train = baseline_lanes.get("train", {})
    baseline_validation = baseline_lanes.get("validation", {})
    round_train = round_lanes.get("train", {})
    round_validation = round_lanes.get("validation", {})

    train_score_delta = _lane_metric(round_train, "avg_total_score") - _lane_metric(baseline_train, "avg_total_score")
    validation_score_delta = _lane_metric(round_validation, "avg_total_score") - _lane_metric(
        baseline_validation, "avg_total_score"
    )
    parse_error_delta = max(
        _lane_metric(round_train, "parse_error_rate") - _lane_metric(baseline_train, "parse_error_rate"),
        _lane_metric(round_validation, "parse_error_rate") - _lane_metric(baseline_validation, "parse_error_rate"),
    )
    timeout_rate_delta = max(
        _lane_metric(round_train, "timeout_rate") - _lane_metric(baseline_train, "timeout_rate"),
        _lane_metric(round_validation, "timeout_rate") - _lane_metric(baseline_validation, "timeout_rate"),
    )
    regression_flags = _compute_regression_flags(
        baseline_scoreboard=baseline_scoreboard,
        round_scoreboard=round_scoreboard,
    )
    decision = str(decision_payload["decision"])
    payload: dict[str, Any] = {
        "feedback_distill_version": FEEDBACK_DISTILL_VERSION,
        "run_id": str(decision_payload.get("run_id") or baseline_scoreboard.get("run_id") or ""),
        "round": int(decision_payload["round"]),
        "mutation_key": str(mutation_payload["mutation_key"]),
        "mutation_id": str(mutation_payload["mutation_id"]),
        "attempt": int(mutation_payload["attempt"]),
        "decision": decision,
        "train_score_delta": train_score_delta,
        "validation_score_delta": validation_score_delta,
        "parse_error_delta": parse_error_delta,
        "timeout_rate_delta": timeout_rate_delta,
        "signal_strength": _signal_strength(
            decision=decision,
            train_score_delta=train_score_delta,
            regression_flags=regression_flags,
        ),
        "regression_flags": regression_flags,
        "dimension_feedback_summary": {},
        "suggested_adjustments": [],
        "scoreboard_ref": _relative_ref(round_dir / "scoreboard.json", run_dir=run_dir),
        "decision_ref": _relative_ref(round_dir / "decision.json", run_dir=run_dir),
        "worker_contract_ref": _relative_ref(round_dir / "worker-contract.json", run_dir=run_dir),
        "distilled_at": str(distilled_at or now_iso()),
    }
    validate_feedback_distill_payload(payload)
    return payload


def feedback_family_priority(
    feedback_ledger: list[dict[str, Any]],
    *,
    mutation_key: str,
) -> tuple[int, str]:
    family_entries = sorted(
        (
            entry
            for entry in feedback_ledger
            if str(entry.get("mutation_key") or "").strip() == mutation_key
        ),
        key=lambda item: (int(item.get("round") or 0), str(item.get("mutation_id") or "")),
    )
    if not family_entries:
        return 1, "no_feedback_history"

    latest = family_entries[-1]
    latest_signal = str(latest.get("signal_strength") or "").strip().lower()
    negative_streak = 0
    for entry in reversed(family_entries):
        if str(entry.get("signal_strength") or "").strip().lower() != "negative":
            break
        negative_streak += 1

    if latest_signal == "positive":
        return 0, "recent_positive_signal"
    if latest_signal == "mixed":
        return 2, "mixed_signal_retry"
    if negative_streak >= 2:
        return 4, "sustained_regression_deprioritized"
    return 3, "latest_negative_signal"
