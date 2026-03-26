#!/usr/bin/env python3
"""Minimal deterministic mutation selector for autoresearch P1.1.

Hard constraints (by design):
- No adaptive scheduling
- No state machine / last_decision dependency
- Deterministic selection from the run-local mutation registry
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from autoresearch_contract import AutoresearchContract
from autoresearch_mutation_registry import AutoresearchMutationRegistry


@dataclass(frozen=True)
class MutationSelection:
    entry: dict[str, Any]
    mutation_key: str
    attempt: int


def _require_int(value: object, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Expected integer for {field}.")
    return value


def select_next_mutation_entry(
    registry: AutoresearchMutationRegistry,
    *,
    contract: AutoresearchContract,
) -> MutationSelection:
    """Select the next mutation entry using a deterministic P1.1 policy.

    Rules:
    - only consider `status == "active"`
    - skip entries where `attempts >= contract.payload["max_candidate_attempts_per_round"]`
    - sort by `attempts` ascending
    - tie-break by registry original order
    - then by `fingerprint` as a stable final tie-break
    """

    max_attempts_raw = contract.payload.get("max_candidate_attempts_per_round")
    max_attempts = _require_int(max_attempts_raw, field="contract.payload.max_candidate_attempts_per_round")
    if max_attempts <= 0:
        raise ValueError("contract.payload.max_candidate_attempts_per_round must be a positive integer.")

    candidates: list[tuple[int, int, str, dict[str, Any]]] = []
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
        candidates.append((attempts, idx, fingerprint, entry))

    if not candidates:
        raise RuntimeError(
            "No selectable mutation entries found (need status=active and attempts below max_candidate_attempts_per_round)."
        )

    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    entry = candidates[0][3]
    mutation_key = str(entry.get("mutation_key") or "").strip()
    if not mutation_key:
        raise ValueError("Selected mutation entry is missing mutation_key.")
    attempts = _require_int(entry.get("attempts", 0), field="selected_entry.attempts")
    return MutationSelection(entry=entry, mutation_key=mutation_key, attempt=attempts + 1)

