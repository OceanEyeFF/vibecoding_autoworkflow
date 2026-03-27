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


def build_worker_contract_payload(
    *,
    contract: AutoresearchContract,
    mutation_payload: dict[str, Any],
    round_payload: dict[str, Any],
    agent_report_path: Path,
    baseline_scoreboard: dict[str, Any] | None = None,
    materialized_at: str | None = None,
) -> dict[str, Any]:
    resolved_materialized_at = str(materialized_at or round_payload.get("worker_contract_materialized_at") or "").strip()
    if not resolved_materialized_at:
        raise ValueError("worker contract materialized_at must be provided by round authority.")
    comparison_baseline = _comparison_baseline(baseline_scoreboard)
    if comparison_baseline is None:
        raise ValueError("baseline_scoreboard is required to build worker-contract comparison_baseline.")
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
        "comparison_baseline": comparison_baseline,
        "recent_feedback_excerpt": [],
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
