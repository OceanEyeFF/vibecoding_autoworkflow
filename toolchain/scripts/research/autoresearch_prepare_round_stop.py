from __future__ import annotations

from pathlib import Path
from typing import Any

from autoresearch_contract import HISTORY_COLUMNS
from autoresearch_mutation_registry import AutoresearchMutationRegistry


EPSILON = 1e-9
MAX_STALE_ROUNDS = 3


def history_rows(history_path: Path) -> list[dict[str, str]]:
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


def has_final_keep(history_path: Path) -> bool:
    return any(str(row.get("decision") or "") == "keep" for row in history_rows(history_path))


def rounds_since_new_validation_champion(history_path: Path) -> int:
    champion_validation: float | None = None
    stale_rounds = 0
    for row in history_rows(history_path):
        decision = str(row.get("decision") or "").strip()
        try:
            validation_score = float(row.get("validation_score") or "0")
        except ValueError:
            continue
        if decision == "baseline":
            champion_validation = validation_score
            stale_rounds = 0
            continue
        if decision not in {"keep", "discard"}:
            continue
        if decision == "keep" and champion_validation is not None and validation_score > champion_validation + EPSILON:
            champion_validation = validation_score
            stale_rounds = 0
            continue
        stale_rounds += 1
    return stale_rounds


def prepare_round_stop_reason(
    *,
    run_dir: Path,
    registry: AutoresearchMutationRegistry | None,
) -> tuple[str, str] | None:
    history_path = run_dir / "history.tsv"
    stale_rounds = rounds_since_new_validation_champion(history_path)
    if stale_rounds >= MAX_STALE_ROUNDS:
        return (
            "no_new_validation_champion",
            f"Stop gate triggered: {MAX_STALE_ROUNDS} consecutive completed rounds without a new validation champion.",
        )

    if registry is None:
        return None
    active_entries: list[dict[str, Any]] = [
        entry
        for entry in registry.entries
        if str(entry.get("status") or "").strip().lower() == "active"
    ]
    if active_entries and not has_final_keep(history_path):
        if all(int(entry.get("attempts") or 0) > 0 for entry in active_entries):
            return (
                "mutation_families_exhausted_without_keep",
                "Stop gate triggered: all active mutation families have been tried at least once "
                "and the run has no final keep.",
            )
    return None
