from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autoresearch_contract import HISTORY_COLUMNS, history_header, load_contract


def build_contract_payload(*, suite_name: str = "lane.yaml") -> dict[str, object]:
    return {
        "run_id": "p0-1-demo",
        "label": "P0.1 Demo",
        "objective": "Improve baseline quality.",
        "target_surface": "memory-side",
        "mutable_paths": ["product/memory-side/skills"],
        "frozen_paths": ["docs/knowledge"],
        "train_suites": [suite_name],
        "validation_suites": [suite_name],
        "acceptance_suites": [suite_name],
        "primary_metrics": ["avg_total_score"],
        "guard_metrics": ["parse_error_rate"],
        "qualitative_veto_checks": ["manual_review"],
        "max_rounds": 3,
        "max_candidate_attempts_per_round": 2,
        "timeout_policy": {"seconds": 300},
        "promotion_policy": {"mode": "manual"},
    }


class AutoresearchContractTest(unittest.TestCase):
    def test_history_header_matches_fixed_column_order(self) -> None:
        self.assertEqual(history_header(), "\t".join(HISTORY_COLUMNS))

    def test_load_contract_validates_schema_and_suite_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lane.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(build_contract_payload()), encoding="utf-8")

            contract = load_contract(contract_path, repo_root=Path.cwd())
            self.assertEqual(contract.run_id, "p0-1-demo")

    def test_load_contract_rejects_missing_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lane.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            payload = build_contract_payload()
            payload.pop("run_id")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaises(Exception):
                load_contract(contract_path, repo_root=Path.cwd())

    def test_load_contract_rejects_overlapping_mutable_and_frozen_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lane.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            payload = build_contract_payload()
            payload["mutable_paths"] = ["product/memory-side"]
            payload["frozen_paths"] = ["product/memory-side/skills"]
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "overlap"):
                load_contract(contract_path, repo_root=Path.cwd())

    def test_load_contract_rejects_missing_suite_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(build_contract_payload()), encoding="utf-8")

            with self.assertRaisesRegex(FileNotFoundError, "Suite manifest not found"):
                load_contract(contract_path, repo_root=Path.cwd())


if __name__ == "__main__":
    unittest.main()
