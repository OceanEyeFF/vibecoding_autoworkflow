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
from common import REPO_ROOT, SCHEMAS_ROOT


AUTORESEARCH_WORKER_CONTRACT_SCHEMA_PATH = SCHEMAS_ROOT / "autoresearch-worker-contract.schema.json"
WORKER_CONTRACT_VERSION = 1


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


def _baseline_summary(scoreboard: dict[str, Any] | None) -> dict[str, Any] | None:
    if not scoreboard:
        return None
    lanes = scoreboard.get("lanes")
    if not isinstance(lanes, list):
        return None
    summary: dict[str, Any] = {}
    for lane in lanes:
        if not isinstance(lane, dict):
            continue
        name = lane.get("lane_name")
        if not isinstance(name, str) or not name:
            continue
        summary[name] = {
            "avg_total_score": lane.get("avg_total_score"),
            "pass_rate": lane.get("pass_rate"),
            "timeout_rate": lane.get("timeout_rate"),
            "parse_error_rate": lane.get("parse_error_rate"),
            "suite_file": lane.get("suite_file"),
            "backend": lane.get("backend"),
            "judge_backend": lane.get("judge_backend"),
        }
    return summary or None


def build_worker_contract_payload(
    *,
    contract: AutoresearchContract,
    contract_path: Path,
    mutation_path: Path,
    mutation_payload: dict[str, Any],
    mutation_sha256: str,
    round_payload: dict[str, Any],
    worktree_payload: dict[str, Any],
    agent_report_path: Path,
    baseline_scoreboard: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # All paths are serialized as absolute strings to keep agent consumption independent of CWD.
    payload: dict[str, Any] = {
        "worker_contract_version": WORKER_CONTRACT_VERSION,
        "run_id": str(contract.run_id),
        "round": int(round_payload["round"]),
        "mutation_id": str(mutation_payload["mutation_id"]),
        "mutation_key": str(mutation_payload["mutation_key"]),
        "attempt": int(mutation_payload["attempt"]),
        "fingerprint": str(mutation_payload["fingerprint"]),
        "kind": str(mutation_payload["kind"]),
        "instruction": str(mutation_payload["instruction"]),
        "target_paths": list(mutation_payload["target_paths"]),
        "allowed_actions": list(mutation_payload["allowed_actions"]),
        "guardrails": dict(mutation_payload.get("guardrails") or {}),
        "expected_effect": dict(mutation_payload.get("expected_effect") or {}),
        "base_sha": str(round_payload["base_sha"]),
        "candidate_branch": str(round_payload["candidate_branch"]),
        "candidate_worktree": str(round_payload["candidate_worktree"]),
        "agent_report_path": str(agent_report_path.expanduser().resolve()),
        "mutation_path": str(mutation_path.expanduser().resolve()),
        "contract_path": str(contract_path.expanduser().resolve()),
        "mutation_sha256": str(mutation_sha256),
        "previous_feedback_excerpt": None,
        "authority_note": (
            "worker-contract.json is an agent-facing envelope only. "
            "Authority remains: contract.json + mutation-registry.json + mutation.json hash + git diff validation."
        ),
    }
    baseline = _baseline_summary(baseline_scoreboard)
    if baseline is not None:
        payload["baseline_summary"] = baseline
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
    mutation_sha256: str,
) -> None:
    # Minimal consistency checks needed to prevent "envelope drift".
    checks: list[tuple[str, object, object]] = [
        ("round", worker_contract.get("round"), int(round_payload.get("round"))),
        ("mutation_key", worker_contract.get("mutation_key"), mutation_payload.get("mutation_key")),
        ("fingerprint", worker_contract.get("fingerprint"), mutation_payload.get("fingerprint")),
        ("candidate_worktree", worker_contract.get("candidate_worktree"), round_payload.get("candidate_worktree")),
        ("mutation_sha256", worker_contract.get("mutation_sha256"), mutation_sha256),
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

