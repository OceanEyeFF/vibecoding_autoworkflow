#!/usr/bin/env python3
"""Worker contract envelope for agent-facing execution.

This module is intentionally limited to:
- worker-contract schema validation
- deterministic build from round/contract/mutation/worktree artifacts
- file hashing (tamper detection)

It does NOT own scheduler/selector logic, keep/discard rules, or worktree lifecycle.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from autoresearch_contract import AutoresearchContract
from autoresearch_mutation_registry import compute_contract_fingerprint
from common import SCHEMAS_ROOT


AUTORESEARCH_WORKER_CONTRACT_SCHEMA_PATH = SCHEMAS_ROOT / "autoresearch-worker-contract.schema.json"
WORKER_CONTRACT_VERSION = 2
LEGACY_WORKER_CONTRACT_VERSION = 1
LEGACY_WORKER_CONTRACT_POLICY = "transition_compat_weak_checks"

LEGACY_WORKER_CONTRACT_REQUIRED_FIELDS = (
    "worker_contract_version",
    "run_id",
    "round",
    "mutation_id",
    "mutation_key",
    "attempt",
    "fingerprint",
    "kind",
    "instruction",
    "target_paths",
    "allowed_actions",
    "guardrails",
    "expected_effect",
    "base_sha",
    "candidate_branch",
    "candidate_worktree",
    "agent_report_path",
    "mutation_path",
    "contract_path",
    "mutation_sha256",
    "previous_feedback_excerpt",
    "authority_note",
)


def _sha256_file_prefixed(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object required: {path}")
    return payload


def validate_worker_contract_payload(payload: dict[str, Any]) -> None:
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError("jsonschema is required to validate autoresearch worker contracts.") from exc

    schema = json.loads(AUTORESEARCH_WORKER_CONTRACT_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=payload, schema=schema)


def load_worker_contract_payload(path: Path) -> dict[str, Any]:
    payload = _load_json(path.expanduser().resolve())
    validate_worker_contract_payload(payload)
    return payload


def validate_legacy_worker_contract_payload(payload: dict[str, Any]) -> None:
    required_fields = [field for field in LEGACY_WORKER_CONTRACT_REQUIRED_FIELDS if field not in payload]
    if required_fields:
        raise ValueError(
            "Legacy worker contract missing required fields: " + ", ".join(required_fields)
        )
    version = payload.get("worker_contract_version")
    if version != LEGACY_WORKER_CONTRACT_VERSION:
        raise ValueError("Legacy worker contract must have worker_contract_version == 1.")

    if not isinstance(payload.get("run_id"), str) or not str(payload["run_id"]).strip():
        raise ValueError("Legacy worker contract field 'run_id' must be a non-empty string.")
    if not isinstance(payload.get("round"), int) or int(payload["round"]) < 1:
        raise ValueError("Legacy worker contract field 'round' must be a positive integer.")
    if not isinstance(payload.get("mutation_key"), str) or not str(payload["mutation_key"]).strip():
        raise ValueError("Legacy worker contract field 'mutation_key' must be a non-empty string.")
    if not isinstance(payload.get("candidate_worktree"), str) or not str(payload["candidate_worktree"]).strip():
        raise ValueError("Legacy worker contract field 'candidate_worktree' must be a non-empty string.")
    if not isinstance(payload.get("candidate_branch"), str) or not str(payload["candidate_branch"]).strip():
        raise ValueError("Legacy worker contract field 'candidate_branch' must be a non-empty string.")
    if not isinstance(payload.get("base_sha"), str) or not str(payload["base_sha"]).strip():
        raise ValueError("Legacy worker contract field 'base_sha' must be a non-empty string.")
    if not isinstance(payload.get("mutation_sha256"), str) or not str(payload["mutation_sha256"]).strip():
        raise ValueError("Legacy worker contract field 'mutation_sha256' must be a non-empty string.")


def load_legacy_worker_contract_payload(path: Path) -> dict[str, Any]:
    payload = _load_json(path.expanduser().resolve())
    validate_legacy_worker_contract_payload(payload)
    return payload


def compute_worker_contract_sha256(path: Path) -> str:
    return _sha256_file_prefixed(path.expanduser().resolve())


def _lane_metric(lane: dict[str, Any] | None, key: str) -> float | None:
    if not isinstance(lane, dict):
        return None
    value = lane.get(key)
    return float(value) if isinstance(value, (int, float)) else None


def _comparison_baseline(scoreboard: dict[str, Any] | None) -> dict[str, float | None] | None:
    if not scoreboard:
        return None
    lanes = scoreboard.get("lanes")
    lane_map: dict[str, dict[str, Any]] = {}
    if isinstance(lanes, list):
        for lane in lanes:
            if not isinstance(lane, dict):
                continue
            name = lane.get("lane_name")
            if isinstance(name, str) and name:
                lane_map[name] = lane
    train_lane = lane_map.get("train")
    validation_lane = lane_map.get("validation")
    return {
        "train_score": _lane_metric(train_lane, "avg_total_score"),
        "validation_score": _lane_metric(validation_lane, "avg_total_score"),
    }


def build_comparison_baseline(scoreboard: dict[str, Any] | None) -> dict[str, float | None]:
    comparison_baseline = _comparison_baseline(scoreboard)
    if comparison_baseline is None:
        raise ValueError("baseline_scoreboard is required to build worker-contract comparison_baseline.")
    return comparison_baseline


def default_aggregate_prompt_guidance(*, status: str = "no_prior_feedback") -> dict[str, Any]:
    return {
        "aggregate_direction": "mixed",
        "aggregate_suggested_adjustments": [],
        "top_regression_repos": [],
        "top_improvement_repos": [],
        "dominant_dimension_signals": [],
        "generation_status": status,
    }


def build_worker_contract_payload(
    *,
    contract: AutoresearchContract,
    mutation_payload: dict[str, Any],
    round_payload: dict[str, Any],
    agent_report_path: Path,
    comparison_baseline: dict[str, float | None] | None = None,
    recent_feedback_excerpt: list[str] | None = None,
    aggregate_prompt_guidance: dict[str, Any] | None = None,
    materialized_at: str | None = None,
) -> dict[str, Any]:
    resolved_materialized_at = str(materialized_at or round_payload.get("worker_contract_materialized_at") or "").strip()
    if not resolved_materialized_at:
        raise ValueError("worker contract materialized_at must be provided by round authority.")
    if comparison_baseline is None:
        raise ValueError("comparison_baseline is required to build worker-contract payload.")
    excerpt = [str(item).strip() for item in (recent_feedback_excerpt or []) if str(item).strip()]
    aggregate_guidance = dict(aggregate_prompt_guidance or default_aggregate_prompt_guidance())
    # All paths are serialized as absolute strings to keep agent consumption independent of CWD.
    payload: dict[str, Any] = {
        "worker_contract_version": WORKER_CONTRACT_VERSION,
        "run_id": str(contract.run_id),
        "round": int(round_payload["round"]),
        "mutation_id": str(mutation_payload["mutation_id"]),
        "mutation_key": str(mutation_payload["mutation_key"]),
        "attempt": int(mutation_payload["attempt"]),
        "base_sha": str(round_payload["base_sha"]),
        "candidate_branch": str(round_payload["candidate_branch"]),
        "candidate_worktree": str(round_payload["candidate_worktree"]),
        "agent_report_path": str(agent_report_path.expanduser().resolve()),
        "target_paths": list(mutation_payload["target_paths"]),
        "allowed_actions": list(mutation_payload["allowed_actions"]),
        "guardrails": dict(mutation_payload.get("guardrails") or {}),
        "instruction": str(mutation_payload["instruction"]),
        "expected_effect": dict(mutation_payload.get("expected_effect") or {}),
        "objective": str(contract.payload["objective"]),
        "target_surface": str(contract.payload["target_surface"]),
        "comparison_baseline": dict(comparison_baseline),
        "recent_feedback_excerpt": excerpt,
        "aggregate_prompt_guidance": aggregate_guidance,
        "contract_fingerprint": compute_contract_fingerprint(contract),
        "mutation_fingerprint": str(mutation_payload["fingerprint"]),
        "materialized_at": resolved_materialized_at,
    }
    validate_worker_contract_payload(payload)
    return payload


def write_worker_contract(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    validate_worker_contract_payload(payload)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def validate_worker_contract_consistency(
    *,
    worker_contract: dict[str, Any],
    round_payload: dict[str, Any],
    mutation_payload: dict[str, Any],
    worktree_payload: dict[str, Any],
) -> None:
    # Minimal consistency checks needed to prevent "envelope drift".
    checks: list[tuple[str, object, object]] = [
        ("round", worker_contract.get("round"), int(round_payload.get("round"))),
        ("mutation_key", worker_contract.get("mutation_key"), mutation_payload.get("mutation_key")),
        ("mutation_fingerprint", worker_contract.get("mutation_fingerprint"), mutation_payload.get("fingerprint")),
        ("candidate_worktree", worker_contract.get("candidate_worktree"), round_payload.get("candidate_worktree")),
        ("candidate_branch", worker_contract.get("candidate_branch"), round_payload.get("candidate_branch")),
        ("base_sha", worker_contract.get("base_sha"), round_payload.get("base_sha")),
    ]
    for field, actual, expected in checks:
        if actual != expected:
            raise RuntimeError(f"worker-contract.json field mismatch: {field}: {actual!r} != {expected!r}")

    # Ensure the recorded worktree path matches the active worktree record too.
    if str(worker_contract.get("candidate_worktree")) != str(worktree_payload.get("path")):
        raise RuntimeError(
            "worker-contract.json candidate_worktree does not match worktree.json path: "
            f"{worker_contract.get('candidate_worktree')!r} != {worktree_payload.get('path')!r}"
        )


def validate_legacy_worker_contract_consistency(
    *,
    worker_contract: dict[str, Any],
    round_payload: dict[str, Any],
    mutation_payload: dict[str, Any],
    worktree_payload: dict[str, Any],
    mutation_sha256: str,
) -> None:
    checks: list[tuple[str, object, object]] = [
        ("round", worker_contract.get("round"), int(round_payload.get("round"))),
        ("mutation_key", worker_contract.get("mutation_key"), mutation_payload.get("mutation_key")),
        ("fingerprint", worker_contract.get("fingerprint"), mutation_payload.get("fingerprint")),
        ("mutation_sha256", worker_contract.get("mutation_sha256"), mutation_sha256),
        ("candidate_worktree", worker_contract.get("candidate_worktree"), round_payload.get("candidate_worktree")),
        ("candidate_branch", worker_contract.get("candidate_branch"), round_payload.get("candidate_branch")),
        ("base_sha", worker_contract.get("base_sha"), round_payload.get("base_sha")),
    ]
    for field, actual, expected in checks:
        if actual != expected:
            raise RuntimeError(f"legacy worker-contract.json field mismatch: {field}: {actual!r} != {expected!r}")

    if str(worker_contract.get("candidate_worktree")) != str(worktree_payload.get("path")):
        raise RuntimeError(
            "legacy worker-contract.json candidate_worktree does not match worktree.json path: "
            f"{worker_contract.get('candidate_worktree')!r} != {worktree_payload.get('path')!r}"
        )
