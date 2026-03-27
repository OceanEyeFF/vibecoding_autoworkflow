from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autoresearch_contract import load_contract
from autoresearch_worker_contract import (
    build_worker_contract_payload,
    compute_worker_contract_sha256,
    load_worker_contract_payload,
    validate_worker_contract_consistency,
    write_worker_contract,
)


def build_contract_payload(*, suite_name: str = "lane.yaml") -> dict[str, object]:
    return {
        "run_id": "p1-1-demo",
        "label": "P1.1 Demo",
        "objective": "Worker contract",
        "target_surface": "memory-side",
        "mutable_paths": ["product/memory-side/skills"],
        "frozen_paths": ["docs/knowledge"],
        "train_suites": [suite_name],
        "validation_suites": [suite_name],
        "acceptance_suites": [suite_name],
        "primary_metrics": ["avg_total_score"],
        "guard_metrics": ["parse_error_rate", "timeout_rate"],
        "qualitative_veto_checks": [],
        "max_rounds": 3,
        "max_candidate_attempts_per_round": 1,
        "timeout_policy": {"seconds": 120},
        "promotion_policy": {"mode": "script"},
    }


def build_scoreboard() -> dict[str, object]:
    return {
        "run_id": "p1-1-demo",
        "generated_at": "2026-03-27T00:00:00+00:00",
        "baseline_sha": "base",
        "rounds_completed": 0,
        "best_round": 0,
        "lanes": [
            {
                "lane_name": "train",
                "avg_total_score": 9.0,
            },
            {
                "lane_name": "validation",
                "avg_total_score": 8.0,
            },
        ],
        "repo_tasks": [],
    }


class AutoresearchWorkerContractTest(unittest.TestCase):
    def test_build_and_validate_worker_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lane.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(build_contract_payload()), encoding="utf-8")
            contract = load_contract(contract_path, repo_root=root)

            round_payload = {
                "round": 1,
                "base_sha": "base",
                "candidate_branch": "candidate/x/r001",
                "candidate_worktree": str(root / "wt"),
            }
            worktree_payload = {"path": str(root / "wt")}
            mutation_path = root / "mutation.json"
            mutation_payload = {
                "round": 1,
                "mutation_id": "k#a001",
                "mutation_key": "k",
                "attempt": 1,
                "fingerprint": "sha256:fp",
                "kind": "text_rephrase",
                "target_paths": ["product/memory-side/skills"],
                "allowed_actions": ["edit"],
                "instruction": "Do the thing.",
                "expected_effect": {
                    "hypothesis": "Improve.",
                    "primary_metrics": ["avg_total_score"],
                    "guard_metrics": ["parse_error_rate"],
                },
                "guardrails": {"require_non_empty_diff": True, "max_files_touched": 1, "extra_frozen_paths": []},
            }
            mutation_path.write_text(json.dumps(mutation_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
            worker_payload = build_worker_contract_payload(
                contract=contract,
                mutation_payload=mutation_payload,
                round_payload=round_payload,
                agent_report_path=root / "agent-report.md",
                baseline_scoreboard=build_scoreboard(),
                materialized_at="2026-03-27T00:00:00+00:00",
            )
            worker_path = root / "worker-contract.json"
            write_worker_contract(worker_path, worker_payload)
            loaded = load_worker_contract_payload(worker_path)
            self.assertEqual(loaded["run_id"], contract.run_id)
            self.assertEqual(loaded["mutation_key"], "k")
            self.assertEqual(loaded["objective"], "Worker contract")
            self.assertEqual(loaded["target_surface"], "memory-side")
            self.assertEqual(loaded["comparison_baseline"]["train_score"], 9.0)
            self.assertEqual(loaded["mutation_fingerprint"], "sha256:fp")
            self.assertTrue(compute_worker_contract_sha256(worker_path).startswith("sha256:"))

    def test_write_worker_contract_rejects_legacy_extra_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lane.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(build_contract_payload()), encoding="utf-8")
            contract = load_contract(contract_path, repo_root=root)
            worker_payload = build_worker_contract_payload(
                contract=contract,
                mutation_payload={
                    "round": 1,
                    "mutation_id": "k#a001",
                    "mutation_key": "k",
                    "attempt": 1,
                    "fingerprint": "sha256:fp",
                    "target_paths": ["product/memory-side/skills"],
                    "allowed_actions": ["edit"],
                    "instruction": "Do the thing.",
                    "expected_effect": {
                        "hypothesis": "Improve.",
                        "primary_metrics": ["avg_total_score"],
                        "guard_metrics": ["parse_error_rate"],
                    },
                    "guardrails": {"require_non_empty_diff": True, "max_files_touched": 1, "extra_frozen_paths": []},
                },
                round_payload={
                    "round": 1,
                    "base_sha": "base",
                    "candidate_branch": "candidate/x/r001",
                    "candidate_worktree": str(root / "wt"),
                },
                agent_report_path=root / "agent-report.md",
                baseline_scoreboard=build_scoreboard(),
                materialized_at="2026-03-27T00:00:00+00:00",
            )
            worker_payload["mutation_path"] = "/tmp/legacy.json"

            with self.assertRaisesRegex(Exception, "Additional properties are not allowed"):
                write_worker_contract(root / "worker-contract.json", worker_payload)

    def test_validate_worker_contract_consistency_detects_drift(self) -> None:
        worker_contract = {
            "round": 1,
            "mutation_key": "k",
            "mutation_fingerprint": "sha256:fp",
            "candidate_worktree": "/tmp/wt",
            "candidate_branch": "b",
            "base_sha": "s",
        }
        round_payload = {"round": 1, "candidate_worktree": "/tmp/wt", "candidate_branch": "b", "base_sha": "s"}
        mutation_payload = {"mutation_key": "k", "fingerprint": "sha256:fp"}
        worktree_payload = {"path": "/tmp/wt"}
        validate_worker_contract_consistency(
            worker_contract=worker_contract,
            round_payload=round_payload,
            mutation_payload=mutation_payload,
            worktree_payload=worktree_payload,
        )
        with self.assertRaisesRegex(RuntimeError, "field mismatch"):
            validate_worker_contract_consistency(
                worker_contract=dict(worker_contract) | {"mutation_key": "other"},
                round_payload=round_payload,
                mutation_payload=mutation_payload,
                worktree_payload=worktree_payload,
            )


if __name__ == "__main__":
    unittest.main()
