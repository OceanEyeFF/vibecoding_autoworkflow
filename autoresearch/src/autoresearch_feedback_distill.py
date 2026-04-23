#!/usr/bin/env python3
"""Deterministic feedback distillation and adaptive-family helpers for autoresearch."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import AUTORESEARCH_SCHEMAS_ROOT


AUTORESEARCH_FEEDBACK_DISTILL_SCHEMA_PATH = AUTORESEARCH_SCHEMAS_ROOT / "autoresearch-feedback-distill.schema.json"
AUTORESEARCH_FEEDBACK_LEDGER_SCHEMA_PATH = AUTORESEARCH_SCHEMAS_ROOT / "autoresearch-feedback-ledger.schema.json"
FEEDBACK_DISTILL_VERSION = 2
FEEDBACK_LEDGER_VERSION = 2
EPSILON = 1e-9
MAX_EVIDENCE_ITEMS = 2

CONTEXT_ROUTING_DIMENSION_ADJUSTMENTS = {
    "path_contraction": {
        "weaker": "tighten the initial read list and cap follow-up drilling after the first entrypoint pass",
        "improved": "preserve the tighter initial read list and ordered first-pass path selection",
    },
    "entry_point_identification": {
        "weaker": "justify why each first-read file is an entrypoint before expanding to nearby modules",
        "improved": "keep anchoring the route card around clearly justified entrypoint files",
    },
    "avoidance_of_over_scanning": {
        "weaker": "name explicit no-read zones and a hard stop condition to prevent broad scanning",
        "improved": "preserve the explicit no-read zones and hard stop condition",
    },
    "execution_usability": {
        "weaker": "tie next actions and open questions to exact repo-relative paths",
        "improved": "keep the route card actionable by pairing next steps with exact repo-relative paths",
    },
}

LEGACY_LEDGER_REQUIRED_FIELDS = (
    "feedback_distill_version",
    "run_id",
    "round",
    "mutation_key",
    "mutation_id",
    "attempt",
    "decision",
    "train_score_delta",
    "validation_score_delta",
    "parse_error_delta",
    "timeout_rate_delta",
    "signal_strength",
    "regression_flags",
    "dimension_feedback_summary",
    "suggested_adjustments",
    "scoreboard_ref",
    "decision_ref",
    "worker_contract_ref",
    "distilled_at",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _lane_map(scoreboard: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lanes = scoreboard.get("lanes") or []
    return {
        str(lane.get("lane_name")): lane
        for lane in lanes
        if isinstance(lane, dict) and lane.get("lane_name")
    }


def _repo_task_map(scoreboard: dict[str, Any]) -> dict[tuple[str, str, str], dict[str, Any]]:
    repo_tasks = scoreboard.get("repo_tasks") or []
    mapping: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in repo_tasks:
        if not isinstance(row, dict):
            continue
        lane_name = str(row.get("lane_name") or "").strip()
        repo = str(row.get("repo") or "").strip()
        task = str(row.get("task") or "").strip()
        if not lane_name or not repo or not task:
            continue
        mapping[(lane_name, repo, task)] = row
    return mapping


def _lane_metric(lane: dict[str, Any] | None, key: str) -> float:
    if not isinstance(lane, dict):
        return 0.0
    value = lane.get(key)
    return float(value) if isinstance(value, (int, float)) else 0.0


def _relative_ref(path: Path, *, run_dir: Path) -> str:
    return path.expanduser().resolve().relative_to(run_dir.expanduser().resolve()).as_posix()


def _trim_sentence(value: object) -> str:
    text = " ".join(str(value or "").strip().split())
    if len(text) <= 160:
        return text
    return text[:157].rstrip() + "..."


def _score_direction(delta: float, *, positive_label: str, negative_label: str) -> str:
    if delta > EPSILON:
        return positive_label
    if delta < -EPSILON:
        return negative_label
    return "stable"


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


def _dimension_feedback_summary(
    *,
    decision: str,
    train_score_delta: float,
    validation_score_delta: float,
    parse_error_delta: float,
    timeout_rate_delta: float,
    regression_flags: list[str],
) -> dict[str, str]:
    summary = {
        "decision_signal": "accepted" if decision == "keep" else "rejected",
        "train_score": _score_direction(
            train_score_delta,
            positive_label="improved",
            negative_label="weaker",
        ),
        "validation_score": _score_direction(
            validation_score_delta,
            positive_label="improved",
            negative_label="weaker",
        ),
        "stability": "stable",
    }
    if parse_error_delta > EPSILON:
        summary["stability"] = "parse_error_regression"
    elif timeout_rate_delta > EPSILON:
        summary["stability"] = "timeout_regression"
    elif regression_flags:
        summary["stability"] = "score_regression"
    return summary


def _suggested_adjustments(
    *,
    decision: str,
    regression_flags: list[str],
    dimension_feedback_summary: dict[str, str],
) -> list[str]:
    adjustments: list[str] = []
    if decision == "keep":
        adjustments.append("reuse this family with a similarly narrow edit scope")
    if "validation_drop" in regression_flags:
        adjustments.append("narrow the next retry to protect validation behavior")
    if "train_drop" in regression_flags:
        adjustments.append("revisit the instruction seed before retrying this family")
    if "validation_parse_error_increase" in regression_flags or "train_parse_error_increase" in regression_flags:
        adjustments.append("reduce formatting churn to avoid parse-error regressions")
    if "validation_timeout_increase" in regression_flags or "train_timeout_increase" in regression_flags:
        adjustments.append("reduce scope and output size to avoid timeout regressions")
    if not adjustments and dimension_feedback_summary.get("validation_score") == "weaker":
        adjustments.append("keep the promising idea but tighten the changed surface before retrying")
    return adjustments[:3]


def _default_aggregate_prompt_guidance(*, status: str = "no_prior_feedback") -> dict[str, Any]:
    return {
        "aggregate_direction": "mixed",
        "aggregate_suggested_adjustments": [],
        "top_regression_repos": [],
        "top_improvement_repos": [],
        "dominant_dimension_signals": [],
        "generation_status": status,
    }


def _lane_guardrail_regression(
    *,
    lane_name: str,
    regression_flags: list[str],
) -> bool:
    lane_prefix = f"{lane_name}_"
    return any(str(flag).startswith(lane_prefix) for flag in regression_flags)


def _missing_round_prompt_adjustments(*, task: str) -> list[str]:
    if task != "context-routing":
        return []
    return [
        "reduce scope and formatting churn until the route card restores structured eval output",
        "re-anchor the route card on the smallest valid entrypoint set before expanding",
    ]


def _missing_round_evidence_excerpt(*, lane_name: str) -> list[str]:
    return [f"{lane_name}: round scoreboard did not emit a structured eval row for this repo/task pair."]


def _repo_guidance_profile(
    *,
    score_delta: float,
    lane_guardrail_regression: bool,
) -> tuple[str, str, bool, str]:
    if score_delta < -EPSILON:
        return ("negative", "weaker", True, "weaker")
    if score_delta > EPSILON:
        if lane_guardrail_regression:
            return ("mixed", "improved", False, "improved")
        return ("positive", "improved", False, "improved")
    if lane_guardrail_regression:
        return ("mixed", "stable", True, "weaker")
    return ("mixed", "stable", False, "improved")


def _ranked_dimension_names(
    *,
    dimension_feedback: dict[str, dict[str, str]],
    field: str,
) -> list[str]:
    ranked: list[tuple[int, str]] = []
    for dimension, feedback in dimension_feedback.items():
        text = str(feedback.get(field) or "").strip()
        if not text:
            continue
        ranked.append((len(text), str(dimension)))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [dimension for _length, dimension in ranked]


def _derive_dimension_signals(
    *,
    dimension_feedback: dict[str, dict[str, str]],
    score_delta: float,
) -> dict[str, str]:
    if not dimension_feedback:
        return {}
    signals = {
        dimension: "stable"
        for dimension in sorted(dimension_feedback)
    }
    if score_delta > EPSILON:
        focus = _ranked_dimension_names(dimension_feedback=dimension_feedback, field="what_worked")[:1]
        for dimension in focus:
            signals[dimension] = "improved"
        return signals
    if score_delta < -EPSILON:
        focus = _ranked_dimension_names(dimension_feedback=dimension_feedback, field="needs_improvement")[:1]
        for dimension in focus:
            signals[dimension] = "weaker"
        return signals
    return signals


def _combine_adjustments(*groups: list[str]) -> list[str]:
    combined: list[str] = []
    for group in groups:
        for item in group:
            text = str(item).strip()
            if text and text not in combined:
                combined.append(text)
            if len(combined) >= 3:
                return combined
    return combined


def _aggregate_adjustment_priority_groups(
    *,
    aggregate_direction: str,
    fallback_adjustments: list[str],
    aggregate_adjustments: list[str],
) -> tuple[list[str], list[str]]:
    if aggregate_direction == "negative" and fallback_adjustments:
        return fallback_adjustments, aggregate_adjustments
    return aggregate_adjustments, fallback_adjustments


def _dimension_feedback_map(row: dict[str, Any]) -> dict[str, dict[str, str]]:
    feedback = row.get("dimension_feedback") or {}
    if not isinstance(feedback, dict):
        return {}
    result: dict[str, dict[str, str]] = {}
    for key, value in feedback.items():
        if not isinstance(value, dict):
            continue
        result[str(key)] = {
            "what_worked": _trim_sentence(value.get("what_worked")),
            "needs_improvement": _trim_sentence(value.get("needs_improvement")),
        }
    return result


def _repo_prompt_adjustments(
    *,
    task: str,
    preferred_signal: str,
    dimension_signals: dict[str, str],
) -> list[str]:
    if task != "context-routing":
        return []
    adjustments: list[str] = []
    fallback_signal = "improved" if preferred_signal == "weaker" else "weaker"
    for signal in (preferred_signal, fallback_signal):
        for dimension in sorted(dimension_signals):
            if dimension_signals.get(dimension) != signal:
                continue
            mapping = CONTEXT_ROUTING_DIMENSION_ADJUSTMENTS.get(dimension, {})
            adjustment = str(mapping.get(signal) or "").strip()
            if adjustment and adjustment not in adjustments:
                adjustments.append(adjustment)
            if len(adjustments) >= 3:
                return adjustments
    return adjustments


def _repo_evidence_excerpt(
    *,
    prefer_needs_improvement: bool,
    dimension_feedback: dict[str, dict[str, str]],
) -> list[str]:
    field = "needs_improvement" if prefer_needs_improvement else "what_worked"
    evidence: list[str] = []
    ranked_dimensions = _ranked_dimension_names(dimension_feedback=dimension_feedback, field=field)
    if not ranked_dimensions:
        ranked_dimensions = sorted(dimension_feedback)
    for dimension in ranked_dimensions:
        text = str(dimension_feedback[dimension].get(field) or "").strip()
        if not text:
            continue
        evidence.append(f"{dimension}: {text}")
        if len(evidence) >= MAX_EVIDENCE_ITEMS:
            break
    return evidence


def build_repo_prompt_guidance(
    *,
    baseline_scoreboard: dict[str, Any],
    round_scoreboard: dict[str, Any],
    decision: str,
    regression_flags: list[str],
) -> list[dict[str, Any]]:
    baseline_repo_tasks = _repo_task_map(baseline_scoreboard)
    round_repo_tasks = _repo_task_map(round_scoreboard)
    guidance_rows: list[dict[str, Any]] = []

    for key in sorted(set(baseline_repo_tasks) | set(round_repo_tasks)):
        lane_name, repo, task = key
        round_row = round_repo_tasks.get(key)
        baseline_row = baseline_repo_tasks.get(key)
        round_total_score = float(round_row.get("total_score") or 0.0) if round_row else None
        baseline_total_score = float(baseline_row.get("total_score") or 0.0) if baseline_row else None

        if baseline_row is None:
            if round_row is None:
                continue
            guidance_rows.append(
                {
                    "lane_name": lane_name,
                    "repo": repo,
                    "task": task,
                    "baseline_total_score": None,
                    "round_total_score": round_total_score,
                    "score_delta": None,
                    "signal_strength": "mixed",
                    "dimension_signals": {},
                    "prompt_adjustments": [],
                    "evidence_excerpt": [],
                    "generation_status": "missing_baseline_row",
                }
            )
            continue

        if round_row is None:
            guidance_rows.append(
                {
                    "lane_name": lane_name,
                    "repo": repo,
                    "task": task,
                    "baseline_total_score": baseline_total_score,
                    "round_total_score": None,
                    "score_delta": None,
                    "signal_strength": "negative",
                    "dimension_signals": {},
                    "prompt_adjustments": _missing_round_prompt_adjustments(task=task),
                    "evidence_excerpt": _missing_round_evidence_excerpt(lane_name=lane_name),
                    "generation_status": "missing_round_row",
                }
            )
            continue

        score_delta = round_total_score - baseline_total_score
        if task != "context-routing":
            guidance_rows.append(
                {
                    "lane_name": lane_name,
                    "repo": repo,
                    "task": task,
                    "baseline_total_score": baseline_total_score,
                    "round_total_score": round_total_score,
                    "score_delta": score_delta,
                    "signal_strength": "mixed",
                    "dimension_signals": {},
                    "prompt_adjustments": [],
                    "evidence_excerpt": [],
                    "generation_status": "unsupported_task",
                }
            )
            continue

        round_dimension_feedback = _dimension_feedback_map(round_row)
        lane_guardrail_regression = decision == "discard" and _lane_guardrail_regression(
            lane_name=lane_name,
            regression_flags=regression_flags,
        )
        repo_signal_strength, _, prefer_needs_improvement, preferred_signal = _repo_guidance_profile(
            score_delta=score_delta,
            lane_guardrail_regression=lane_guardrail_regression,
        )
        dimension_signals = _derive_dimension_signals(
            dimension_feedback=round_dimension_feedback,
            score_delta=score_delta,
        )
        guidance_rows.append(
            {
                "lane_name": lane_name,
                "repo": repo,
                "task": task,
                "baseline_total_score": baseline_total_score,
                "round_total_score": round_total_score,
                "score_delta": score_delta,
                "signal_strength": repo_signal_strength,
                "dimension_signals": dimension_signals,
                "prompt_adjustments": _repo_prompt_adjustments(
                    task=task,
                    preferred_signal=preferred_signal,
                    dimension_signals=dimension_signals,
                ),
                "evidence_excerpt": _repo_evidence_excerpt(
                    prefer_needs_improvement=prefer_needs_improvement,
                    dimension_feedback=round_dimension_feedback,
                ),
                "generation_status": "generated",
            }
        )
    return guidance_rows


def build_aggregate_prompt_guidance(
    repo_prompt_guidance: list[dict[str, Any]],
    *,
    decision: str,
    signal_strength: str,
) -> dict[str, Any]:
    actionable = [
        row
        for row in repo_prompt_guidance
        if isinstance(row, dict) and str(row.get("generation_status") or "") in {"generated", "missing_round_row"}
    ]
    if not actionable:
        status_pool = {
            str(row.get("generation_status") or "")
            for row in repo_prompt_guidance
            if isinstance(row, dict)
        }
        if status_pool == {"unsupported_task"}:
            return _default_aggregate_prompt_guidance(status="unsupported_task_only")
        if status_pool == {"missing_baseline_row"}:
            return _default_aggregate_prompt_guidance(status="missing_baseline_only")
        return _default_aggregate_prompt_guidance(status="no_repo_guidance")

    negative_count = sum(1 for row in actionable if str(row.get("signal_strength") or "") == "negative")
    positive_count = sum(1 for row in actionable if str(row.get("signal_strength") or "") == "positive")
    if negative_count > positive_count:
        aggregate_direction = "negative"
    elif positive_count > negative_count and negative_count == 0:
        aggregate_direction = "positive"
    else:
        aggregate_direction = signal_strength if signal_strength in {"positive", "mixed", "negative"} else "mixed"

    negative_rows = [
        (
            0 if row.get("score_delta") is None else 1,
            float(row.get("score_delta") or 0.0),
            str(row.get("repo") or ""),
        )
        for row in actionable
        if str(row.get("signal_strength") or "") == "negative"
    ]
    positive_rows = [
        (
            float(row.get("score_delta") or 0.0),
            str(row.get("repo") or ""),
        )
        for row in actionable
        if str(row.get("signal_strength") or "") == "positive"
    ]
    negative_rows.sort(key=lambda item: (item[0], item[1], item[2]))
    positive_rows.sort(key=lambda item: (item[0], item[1]), reverse=True)
    negative_rows = _dedupe_ranked_repos(negative_rows, repo_index=2)
    positive_rows = _dedupe_ranked_repos(positive_rows, repo_index=1)
    top_regression_repos = [repo for _priority, _delta, repo in negative_rows][:3]
    top_improvement_repos = [repo for _delta, repo in positive_rows][:3]

    dominant_counter: Counter[tuple[str, str]] = Counter()
    repo_counter: dict[tuple[str, str], set[str]] = {}
    for row in actionable:
        repo = str(row.get("repo") or "")
        signals = row.get("dimension_signals") or {}
        if not isinstance(signals, dict):
            continue
        for dimension, value in signals.items():
            signal = str(value or "").strip()
            if signal == "stable":
                continue
            key = (str(dimension), signal)
            dominant_counter[key] += 1
            repo_counter.setdefault(key, set()).add(repo)

    dominant_dimension_signals: list[dict[str, Any]] = []
    for (dimension, signal), count in dominant_counter.most_common(3):
        dominant_dimension_signals.append(
            {
                "dimension": dimension,
                "signal": signal,
                "count": count,
                "repos": sorted(repo_counter.get((dimension, signal), set()))[:3],
            }
        )

    adjustments: list[str] = []
    for item in dominant_dimension_signals:
        mapping = CONTEXT_ROUTING_DIMENSION_ADJUSTMENTS.get(str(item["dimension"]), {})
        signal = str(item["signal"])
        adjustment = str(mapping.get(signal) or "").strip()
        if adjustment and adjustment not in adjustments:
            adjustments.append(adjustment)
    if decision == "keep" and aggregate_direction == "positive":
        positive_adjustment = "reuse the winning guidance pattern without widening prompt scope"
        if positive_adjustment not in adjustments:
            adjustments.insert(0, positive_adjustment)

    return {
        "aggregate_direction": aggregate_direction,
        "aggregate_suggested_adjustments": adjustments[:3],
        "top_regression_repos": top_regression_repos,
        "top_improvement_repos": top_improvement_repos,
        "dominant_dimension_signals": dominant_dimension_signals,
        "generation_status": "generated",
    }


def _latest_adjustments(entry: dict[str, Any]) -> list[str]:
    aggregate = entry.get("aggregate_prompt_guidance") or {}
    if isinstance(aggregate, dict):
        adjustments = [
            str(item).strip()
            for item in (aggregate.get("aggregate_suggested_adjustments") or [])
            if str(item).strip()
        ]
        if adjustments:
            return adjustments
    return [
        str(item).strip()
        for item in (entry.get("suggested_adjustments") or [])
        if str(item).strip()
    ]


def _dedupe_ranked_repos(rows: list[tuple[Any, ...]], *, repo_index: int) -> list[tuple[Any, ...]]:
    deduped: list[tuple[Any, ...]] = []
    seen: set[str] = set()
    for row in rows:
        repo = str(row[repo_index] or "").strip()
        if not repo or repo in seen:
            continue
        seen.add(repo)
        deduped.append(row)
    return deduped


def latest_aggregate_prompt_guidance(feedback_ledger: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(
        (entry for entry in feedback_ledger if isinstance(entry, dict)),
        key=lambda item: (int(item.get("round") or 0), str(item.get("mutation_id") or "")),
        reverse=True,
    )
    for entry in ordered:
        aggregate = entry.get("aggregate_prompt_guidance") or {}
        if isinstance(aggregate, dict):
            aggregate_adjustments = [
                str(item).strip()
                for item in (aggregate.get("aggregate_suggested_adjustments") or [])
                if str(item).strip()
            ]
            if str(aggregate.get("generation_status") or "") == "generated":
                return dict(aggregate)
            if aggregate_adjustments:
                direction = str(aggregate.get("aggregate_direction") or entry.get("signal_strength") or "mixed").strip()
                return {
                    "aggregate_direction": direction if direction in {"positive", "mixed", "negative"} else "mixed",
                    "aggregate_suggested_adjustments": aggregate_adjustments[:3],
                    "top_regression_repos": [],
                    "top_improvement_repos": [],
                    "dominant_dimension_signals": [],
                    "generation_status": "generated",
                }
        legacy_adjustments = [
            str(item).strip()
            for item in (entry.get("suggested_adjustments") or [])
            if str(item).strip()
        ]
        if legacy_adjustments:
            return {
                "aggregate_direction": str(entry.get("signal_strength") or "mixed"),
                "aggregate_suggested_adjustments": legacy_adjustments[:3],
                "top_regression_repos": [],
                "top_improvement_repos": [],
                "dominant_dimension_signals": [],
                "generation_status": "generated",
            }
    return _default_aggregate_prompt_guidance()


def build_recent_feedback_excerpt(
    feedback_ledger: list[dict[str, Any]],
    *,
    limit: int = 2,
) -> list[str]:
    if limit <= 0:
        raise ValueError("recent feedback excerpt limit must be positive.")
    ordered = sorted(
        (entry for entry in feedback_ledger if isinstance(entry, dict)),
        key=lambda item: (int(item.get("round") or 0), str(item.get("mutation_id") or "")),
        reverse=True,
    )
    excerpt: list[str] = []
    for entry in ordered[:limit]:
        mutation_key = str(entry.get("mutation_key") or "").strip()
        decision = str(entry.get("decision") or "").strip()
        signal = str(entry.get("signal_strength") or "").strip()
        flags = [str(flag).strip() for flag in (entry.get("regression_flags") or []) if str(flag).strip()]
        adjustments = _latest_adjustments(entry)
        summary = entry.get("dimension_feedback_summary") or {}
        aggregate = entry.get("aggregate_prompt_guidance") or {}
        summary_bits: list[str] = []
        if isinstance(summary, dict):
            for key in ("train_score", "validation_score", "stability"):
                value = str(summary.get(key) or "").strip()
                if value:
                    summary_bits.append(f"{key}={value}")
        parts = [
            f"round={int(entry.get('round') or 0)}",
            f"mutation={mutation_key}",
            f"decision={decision}",
            f"signal={signal}",
        ]
        if flags:
            parts.append("flags=" + ",".join(flags))
        if isinstance(aggregate, dict):
            direction = str(aggregate.get("aggregate_direction") or "").strip()
            if direction:
                parts.append(f"aggregate={direction}")
        if summary_bits:
            parts.append("summary=" + ",".join(summary_bits))
        if adjustments:
            parts.append("next=" + adjustments[0])
        excerpt.append(" | ".join(parts))
    return excerpt


def _validate_with_schema(payload: dict[str, Any], schema_path: Path) -> None:
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError("jsonschema is required to validate autoresearch feedback payloads.") from exc

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=payload, schema=schema)


def validate_feedback_distill_payload(payload: dict[str, Any]) -> None:
    _validate_with_schema(payload, AUTORESEARCH_FEEDBACK_DISTILL_SCHEMA_PATH)


def validate_feedback_ledger_entry(payload: dict[str, Any]) -> None:
    _validate_with_schema(payload, AUTORESEARCH_FEEDBACK_LEDGER_SCHEMA_PATH)


def validate_legacy_feedback_ledger_entry(payload: dict[str, Any]) -> None:
    missing = [field for field in LEGACY_LEDGER_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError("Legacy feedback ledger entry missing required fields: " + ", ".join(missing))
    if int(payload.get("feedback_distill_version") or 0) != 1:
        raise ValueError("Legacy feedback ledger entry must have feedback_distill_version == 1.")


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
        if int(payload.get("feedback_ledger_version") or 0) == FEEDBACK_LEDGER_VERSION:
            validate_feedback_ledger_entry(payload)
        else:
            validate_legacy_feedback_ledger_entry(payload)
        entries.append(payload)
    return entries


def build_feedback_ledger_entry(distill_payload: dict[str, Any]) -> dict[str, Any]:
    aggregate_prompt_guidance = dict(distill_payload.get("aggregate_prompt_guidance") or _default_aggregate_prompt_guidance())
    persisted_adjustments = _combine_adjustments(
        list(distill_payload.get("suggested_adjustments") or []),
        list(aggregate_prompt_guidance.get("aggregate_suggested_adjustments") or []),
    )
    if persisted_adjustments:
        aggregate_prompt_guidance["aggregate_suggested_adjustments"] = persisted_adjustments
    payload = {
        "feedback_ledger_version": FEEDBACK_LEDGER_VERSION,
        "run_id": str(distill_payload["run_id"]),
        "round": int(distill_payload["round"]),
        "mutation_key": str(distill_payload["mutation_key"]),
        "mutation_id": str(distill_payload["mutation_id"]),
        "attempt": int(distill_payload["attempt"]),
        "decision": str(distill_payload["decision"]),
        "train_score_delta": float(distill_payload["train_score_delta"]),
        "validation_score_delta": float(distill_payload["validation_score_delta"]),
        "parse_error_delta": float(distill_payload["parse_error_delta"]),
        "timeout_rate_delta": float(distill_payload["timeout_rate_delta"]),
        "signal_strength": str(distill_payload["signal_strength"]),
        "regression_flags": list(distill_payload.get("regression_flags") or []),
        "dimension_feedback_summary": dict(distill_payload.get("dimension_feedback_summary") or {}),
        "aggregate_prompt_guidance": aggregate_prompt_guidance,
        "scoreboard_ref": str(distill_payload["scoreboard_ref"]),
        "decision_ref": str(distill_payload["decision_ref"]),
        "worker_contract_ref": str(distill_payload["worker_contract_ref"]),
        "distilled_at": str(distill_payload["distilled_at"]),
    }
    validate_feedback_ledger_entry(payload)
    return payload


def upsert_feedback_ledger_entry(path: Path, payload: dict[str, Any]) -> None:
    if int(payload.get("feedback_ledger_version") or 0) == FEEDBACK_LEDGER_VERSION:
        entry = dict(payload)
        validate_feedback_ledger_entry(entry)
    else:
        validate_feedback_distill_payload(payload)
        entry = build_feedback_ledger_entry(payload)

    resolved = path.expanduser().resolve()
    existing = load_feedback_ledger(resolved)
    entry_key = (
        str(entry["run_id"]),
        int(entry["round"]),
        str(entry["mutation_id"]),
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
    filtered.append(entry)
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
    signal_strength = _signal_strength(
        decision=decision,
        train_score_delta=train_score_delta,
        regression_flags=regression_flags,
    )
    dimension_feedback_summary = _dimension_feedback_summary(
        decision=decision,
        train_score_delta=train_score_delta,
        validation_score_delta=validation_score_delta,
        parse_error_delta=parse_error_delta,
        timeout_rate_delta=timeout_rate_delta,
        regression_flags=regression_flags,
    )
    repo_prompt_guidance = build_repo_prompt_guidance(
        baseline_scoreboard=baseline_scoreboard,
        round_scoreboard=round_scoreboard,
        decision=decision,
        regression_flags=regression_flags,
    )
    aggregate_prompt_guidance = build_aggregate_prompt_guidance(
        repo_prompt_guidance,
        decision=decision,
        signal_strength=signal_strength,
    )
    fallback_adjustments = _suggested_adjustments(
        decision=decision,
        regression_flags=regression_flags,
        dimension_feedback_summary=dimension_feedback_summary,
    )
    aggregate_adjustments = list(aggregate_prompt_guidance.get("aggregate_suggested_adjustments") or [])
    primary_adjustments, secondary_adjustments = _aggregate_adjustment_priority_groups(
        aggregate_direction=str(aggregate_prompt_guidance.get("aggregate_direction") or ""),
        fallback_adjustments=fallback_adjustments,
        aggregate_adjustments=aggregate_adjustments,
    )
    suggested_adjustments = _combine_adjustments(primary_adjustments, secondary_adjustments)
    if suggested_adjustments:
        aggregate_prompt_guidance["aggregate_suggested_adjustments"] = suggested_adjustments
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
        "signal_strength": signal_strength,
        "regression_flags": regression_flags,
        "dimension_feedback_summary": dimension_feedback_summary,
        "suggested_adjustments": suggested_adjustments,
        "repo_prompt_guidance": repo_prompt_guidance,
        "aggregate_prompt_guidance": aggregate_prompt_guidance,
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
    latest_flags = {
        str(flag).strip()
        for flag in (latest.get("regression_flags") or [])
        if str(flag).strip()
    }
    latest_adjustments = _latest_adjustments(latest)
    negative_streak = 0
    for entry in reversed(family_entries):
        if str(entry.get("signal_strength") or "").strip().lower() != "negative":
            break
        negative_streak += 1
    guardrail_flags = {
        "validation_drop",
        "validation_pass_rate_drop",
        "validation_parse_error_increase",
        "train_parse_error_increase",
        "validation_timeout_increase",
        "train_timeout_increase",
    }
    has_guardrail_regression = bool(latest_flags & guardrail_flags)

    if latest_signal == "positive":
        return 0, "recent_positive_signal"
    if latest_signal == "mixed":
        if has_guardrail_regression:
            return 3, "guardrail_capped_mixed_retry"
        if latest_adjustments:
            return 2, "guided_mixed_retry"
        return 2, "mixed_signal_retry"
    if negative_streak >= 2:
        return 5, "sustained_regression_deprioritized"
    if has_guardrail_regression:
        return 4, "guardrail_blocked_retry"
    return 3, "latest_negative_signal"
