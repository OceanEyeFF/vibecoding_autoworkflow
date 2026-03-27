#!/usr/bin/env python3
"""Minimal deterministic mutation selector for autoresearch P1.2.

Hard constraints (by design):
- No adaptive scheduling
- No feedback distillation / scheduler behavior
- Deterministic selection from the run-local mutation registry
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from autoresearch_contract import AutoresearchContract
from autoresearch_mutation_registry import AutoresearchMutationRegistry


@dataclass(frozen=True)
class MutationSelection:
    entry: dict[str, Any]
    mutation_key: str
    attempt: int
    selection_reason: str
    selection_index: int


def _require_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Expected integer for {field}.")
    return value


def _load_pending_round_fingerprint(
    registry: AutoresearchMutationRegistry,
    *,
    runtime: dict[str, Any] | None,
) -> str | None:
    if runtime is None:
        return None
    if not isinstance(runtime, dict):
        raise ValueError("runtime must be a JSON object when provided to the selector.")
    active_round = runtime.get("active_round")
    if active_round is None:
        return None
    round_number = _require_int(active_round, field="runtime.active_round")
    if round_number <= 0:
        return None
    run_dir = registry.source_path.expanduser().resolve().parent
    mutation_path = run_dir / "rounds" / f"round-{round_number:03d}" / "mutation.json"
    if not mutation_path.is_file():
        return None
    payload = json.loads(mutation_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    fingerprint = str(payload.get("fingerprint") or "").strip()
    return fingerprint or None


def select_next_mutation_entry(
    registry: AutoresearchMutationRegistry,
    *,
    contract: AutoresearchContract,
    runtime: dict[str, Any] | None = None,
    comparison_baseline: dict[str, Any] | None = None,
) -> MutationSelection:
    """Select the next mutation entry using a deterministic P1.2 policy.

    Rules:
    - only consider `status == "active"`
    - skip entries where `attempts >= contract.payload["max_candidate_attempts_per_round"]`
    - skip entries whose fingerprint conflicts with the current pending round
    - sort by `attempts` ascending
    - tie-break by registry original order
    """
    if comparison_baseline is not None and not isinstance(comparison_baseline, dict):
        raise ValueError("comparison_baseline must be a JSON object when provided to the selector.")

    max_attempts_raw = contract.payload.get("max_candidate_attempts_per_round")
    max_attempts = _require_int(max_attempts_raw, field="contract.payload.max_candidate_attempts_per_round")
    if max_attempts <= 0:
        raise ValueError("contract.payload.max_candidate_attempts_per_round must be a positive integer.")

    pending_fingerprint = _load_pending_round_fingerprint(registry, runtime=runtime)

    ranked_candidates: list[tuple[int, int, str, dict[str, Any]]] = []
    selectable_candidates: list[tuple[int, int, str, dict[str, Any]]] = []
    for idx, entry in enumerate(registry.entries):
        status = str(entry.get("status") or "").strip().lower()
        if status != "active":
            continue
        attempts_raw = entry.get("attempts", 0)
        attempts = _require_int(attempts_raw, field=f"registry.entries[{idx}].attempts")
        if attempts < 0:
            raise ValueError("registry entry attempts must be non-negative.")
        if attempts >= max_attempts:
            continue
        fingerprint = str(entry.get("fingerprint") or "")
        mutation_key = str(entry.get("mutation_key") or "").strip()
        candidate = (attempts, idx, mutation_key, entry)
        ranked_candidates.append(candidate)
        if pending_fingerprint is not None and fingerprint == pending_fingerprint:
            continue
        selectable_candidates.append(candidate)

    if not selectable_candidates:
        raise RuntimeError(
            "No selectable mutation entries found (need status=active and attempts below max_candidate_attempts_per_round)."
        )

    ranked_candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    selectable_candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    attempts, selection_index, _mutation_key_sort, entry = selectable_candidates[0]
    mutation_key = str(entry.get("mutation_key") or "").strip()
    if not mutation_key:
        raise ValueError("Selected mutation entry is missing mutation_key.")
    selection_reason = (
        "skip_duplicate_fingerprint"
        if selectable_candidates[0] != ranked_candidates[0]
        else "lowest_attempt_count"
    )
    return MutationSelection(
        entry=entry,
        mutation_key=mutation_key,
        attempt=attempts + 1,
        selection_reason=selection_reason,
        selection_index=selection_index,
    )
