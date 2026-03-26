from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autoresearch_contract import AutoresearchContract
from autoresearch_mutation_registry import AutoresearchMutationRegistry
from autoresearch_selector import select_next_mutation_entry


def build_contract(max_attempts: int) -> AutoresearchContract:
    payload: dict[str, object] = {"run_id": "demo-run", "max_candidate_attempts_per_round": max_attempts}
    return AutoresearchContract(
        source_path=Path("contract.json"),
        payload=payload,
        run_id="demo-run",
        train_suites=[],
        validation_suites=[],
        acceptance_suites=[],
        mutable_paths=[],
        frozen_paths=[],
    )


def build_registry(entries: list[dict[str, object]]) -> AutoresearchMutationRegistry:
    return AutoresearchMutationRegistry(
        source_path=Path("mutation-registry.json"),
        payload={},
        run_id="demo-run",
        registry_version=1,
        contract_fingerprint="sha256:deadbeef",
        entries=[dict(item) for item in entries],
    )


class SelectorTest(unittest.TestCase):
    def test_selects_lowest_attempts_then_registry_order(self) -> None:
        contract = build_contract(max_attempts=2)
        registry = build_registry(
            [
                {
                    "mutation_key": "k1",
                    "status": "active",
                    "attempts": 0,
                    "fingerprint": "sha256:bbb",
                },
                {
                    "mutation_key": "k2",
                    "status": "active",
                    "attempts": 0,
                    "fingerprint": "sha256:aaa",
                },
                {
                    "mutation_key": "k3",
                    "status": "active",
                    "attempts": 1,
                    "fingerprint": "sha256:ccc",
                },
            ]
        )

        selection = select_next_mutation_entry(registry, contract=contract)
        self.assertEqual(selection.mutation_key, "k1")
        self.assertEqual(selection.attempt, 1)

    def test_skips_disabled_and_exhausted_attempts(self) -> None:
        contract = build_contract(max_attempts=2)
        registry = build_registry(
            [
                {
                    "mutation_key": "exhausted",
                    "status": "active",
                    "attempts": 2,
                    "fingerprint": "sha256:111",
                },
                {
                    "mutation_key": "disabled",
                    "status": "disabled",
                    "attempts": 0,
                    "fingerprint": "sha256:222",
                },
                {
                    "mutation_key": "ok",
                    "status": "ACTIVE",
                    "attempts": 1,
                    "fingerprint": "sha256:333",
                },
            ]
        )

        selection = select_next_mutation_entry(registry, contract=contract)
        self.assertEqual(selection.mutation_key, "ok")
        self.assertEqual(selection.attempt, 2)

    def test_raises_when_no_selectable_entries(self) -> None:
        contract = build_contract(max_attempts=1)
        registry = build_registry(
            [
                {"mutation_key": "a", "status": "disabled", "attempts": 0, "fingerprint": "sha256:a"},
                {"mutation_key": "b", "status": "active", "attempts": 1, "fingerprint": "sha256:b"},
            ]
        )
        with self.assertRaises(RuntimeError):
            select_next_mutation_entry(registry, contract=contract)


if __name__ == "__main__":
    unittest.main()

