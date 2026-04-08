from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autoresearch_contract import history_header
from autoresearch_prepare_round_stop import prepare_round_stop_reason
from autoresearch_mutation_registry import AutoresearchMutationRegistry


def write_history_rows(run_dir: Path, rows: list[dict[str, str]]) -> None:
    lines = [history_header()]
    for row in rows:
        lines.append(
            "\t".join(
                [
                    row["round"],
                    row["kind"],
                    row["base_sha"],
                    row["candidate_sha"],
                    row["train_score"],
                    row["validation_score"],
                    row["train_parse_error_rate"],
                    row["validation_parse_error_rate"],
                    row["decision"],
                    row["notes"],
                ]
            )
        )
    (run_dir / "history.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_registry(entries: list[dict[str, object]]) -> AutoresearchMutationRegistry:
    payload = {
        "run_id": "demo-run",
        "registry_version": 1,
        "contract_fingerprint": "fingerprint",
        "entries": entries,
    }
    return AutoresearchMutationRegistry(
        source_path=Path("/tmp/mutation-registry.json"),
        payload=payload,
        run_id="demo-run",
        registry_version=1,
        contract_fingerprint="fingerprint",
        entries=entries,
    )


class PrepareRoundStopReasonTest(unittest.TestCase):
    def test_returns_none_when_no_stop_gate_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            write_history_rows(
                run_dir,
                [
                    {
                        "round": "0",
                        "kind": "baseline",
                        "base_sha": "baseline",
                        "candidate_sha": "-",
                        "train_score": "9.000000",
                        "validation_score": "8.000000",
                        "train_parse_error_rate": "0.000000",
                        "validation_parse_error_rate": "0.000000",
                        "decision": "baseline",
                        "notes": "",
                    }
                ],
            )
            registry = build_registry(
                [
                    {
                        "mutation_key": "text_rephrase:demo:intro-tighten-v1",
                        "status": "active",
                        "attempts": 0,
                    }
                ]
            )

            stop_info = prepare_round_stop_reason(run_dir=run_dir, registry=registry)

        self.assertIsNone(stop_info)

    def test_stops_after_three_rounds_without_new_validation_champion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            write_history_rows(
                run_dir,
                [
                    {
                        "round": "0",
                        "kind": "baseline",
                        "base_sha": "baseline",
                        "candidate_sha": "-",
                        "train_score": "9.000000",
                        "validation_score": "8.000000",
                        "train_parse_error_rate": "0.000000",
                        "validation_parse_error_rate": "0.000000",
                        "decision": "baseline",
                        "notes": "",
                    },
                    {
                        "round": "1",
                        "kind": "text_rephrase",
                        "base_sha": "baseline",
                        "candidate_sha": "sha-1",
                        "train_score": "9.500000",
                        "validation_score": "8.000000",
                        "train_parse_error_rate": "0.000000",
                        "validation_parse_error_rate": "0.000000",
                        "decision": "discard",
                        "notes": "",
                    },
                    {
                        "round": "2",
                        "kind": "instruction_reorder",
                        "base_sha": "sha-1",
                        "candidate_sha": "sha-2",
                        "train_score": "9.600000",
                        "validation_score": "8.000000",
                        "train_parse_error_rate": "0.000000",
                        "validation_parse_error_rate": "0.000000",
                        "decision": "keep",
                        "notes": "",
                    },
                    {
                        "round": "3",
                        "kind": "instruction_reorder",
                        "base_sha": "sha-2",
                        "candidate_sha": "sha-3",
                        "train_score": "9.700000",
                        "validation_score": "7.900000",
                        "train_parse_error_rate": "0.000000",
                        "validation_parse_error_rate": "0.000000",
                        "decision": "discard",
                        "notes": "",
                    },
                ],
            )

            stop_info = prepare_round_stop_reason(run_dir=run_dir, registry=None)

        self.assertEqual(
            stop_info,
            (
                "no_new_validation_champion",
                "Stop gate triggered: 3 consecutive completed rounds without a new validation champion.",
            ),
        )

    def test_stops_when_all_active_entries_have_attempts_without_keep(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            write_history_rows(
                run_dir,
                [
                    {
                        "round": "0",
                        "kind": "baseline",
                        "base_sha": "baseline",
                        "candidate_sha": "-",
                        "train_score": "9.000000",
                        "validation_score": "8.000000",
                        "train_parse_error_rate": "0.000000",
                        "validation_parse_error_rate": "0.000000",
                        "decision": "baseline",
                        "notes": "",
                    },
                    {
                        "round": "1",
                        "kind": "text_rephrase",
                        "base_sha": "baseline",
                        "candidate_sha": "sha-1",
                        "train_score": "9.500000",
                        "validation_score": "7.500000",
                        "train_parse_error_rate": "0.000000",
                        "validation_parse_error_rate": "0.000000",
                        "decision": "discard",
                        "notes": "",
                    },
                ],
            )
            registry = build_registry(
                [
                    {
                        "mutation_key": "text_rephrase:demo:intro-tighten-v1",
                        "status": "active",
                        "attempts": 1,
                    },
                    {
                        "mutation_key": "instruction_reorder:demo:sections-v1",
                        "status": "active",
                        "attempts": 2,
                    },
                ]
            )

            stop_info = prepare_round_stop_reason(run_dir=run_dir, registry=registry)

        self.assertEqual(
            stop_info,
            (
                "mutation_families_exhausted_without_keep",
                "Stop gate triggered: all active mutation families have been tried at least once and the run has no final keep.",
            ),
        )

    def test_final_keep_disables_mutation_family_stop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            write_history_rows(
                run_dir,
                [
                    {
                        "round": "0",
                        "kind": "baseline",
                        "base_sha": "baseline",
                        "candidate_sha": "-",
                        "train_score": "9.000000",
                        "validation_score": "8.000000",
                        "train_parse_error_rate": "0.000000",
                        "validation_parse_error_rate": "0.000000",
                        "decision": "baseline",
                        "notes": "",
                    },
                    {
                        "round": "1",
                        "kind": "text_rephrase",
                        "base_sha": "baseline",
                        "candidate_sha": "sha-1",
                        "train_score": "9.500000",
                        "validation_score": "8.200000",
                        "train_parse_error_rate": "0.000000",
                        "validation_parse_error_rate": "0.000000",
                        "decision": "keep",
                        "notes": "",
                    },
                ],
            )
            registry = build_registry(
                [
                    {
                        "mutation_key": "text_rephrase:demo:intro-tighten-v1",
                        "status": "active",
                        "attempts": 1,
                    }
                ]
            )

            stop_info = prepare_round_stop_reason(run_dir=run_dir, registry=registry)

        self.assertIsNone(stop_info)


if __name__ == "__main__":
    unittest.main()
