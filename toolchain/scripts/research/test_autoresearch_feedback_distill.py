from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autoresearch_feedback_distill import (
    build_feedback_distill_payload,
    feedback_family_priority,
    load_feedback_ledger,
    upsert_feedback_ledger_entry,
)


def build_scoreboard(*, train_score: float, validation_score: float, parse_error: float = 0.0, timeout: float = 0.0, pass_rate: float = 1.0) -> dict[str, object]:
    return {
        "run_id": "demo-run",
        "generated_at": "2026-03-27T00:00:00+00:00",
        "baseline_sha": "base",
        "rounds_completed": 0,
        "best_round": 0,
        "lanes": [
            {
                "lane_name": "train",
                "suite_file": "train.yaml",
                "backend": "claude",
                "judge_backend": "claude",
                "repos_total": 1,
                "tasks_total": 1,
                "pass_rate": pass_rate,
                "timeout_rate": timeout,
                "parse_error_rate": parse_error,
                "avg_total_score": train_score,
            },
            {
                "lane_name": "validation",
                "suite_file": "validation.yaml",
                "backend": "claude",
                "judge_backend": "claude",
                "repos_total": 1,
                "tasks_total": 1,
                "pass_rate": pass_rate,
                "timeout_rate": timeout,
                "parse_error_rate": parse_error,
                "avg_total_score": validation_score,
            },
        ],
        "repo_tasks": [],
    }


class AutoresearchFeedbackDistillTest(unittest.TestCase):
    def test_build_feedback_distill_payload_computes_mixed_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "demo-run"
            round_dir = run_dir / "rounds" / "round-001"
            round_dir.mkdir(parents=True, exist_ok=True)
            (round_dir / "decision.json").write_text("{}\n", encoding="utf-8")
            (round_dir / "scoreboard.json").write_text("{}\n", encoding="utf-8")
            (round_dir / "worker-contract.json").write_text("{}\n", encoding="utf-8")

            payload = build_feedback_distill_payload(
                run_dir=run_dir,
                round_dir=round_dir,
                mutation_payload={
                    "mutation_key": "text_rephrase:demo:intro-tighten-v1",
                    "mutation_id": "text_rephrase:demo:intro-tighten-v1#a001",
                    "attempt": 1,
                },
                decision_payload={
                    "run_id": "demo-run",
                    "round": 1,
                    "decision": "discard",
                },
                baseline_scoreboard=build_scoreboard(train_score=9.0, validation_score=8.0),
                round_scoreboard=build_scoreboard(train_score=10.0, validation_score=7.5),
                distilled_at="2026-03-27T00:00:00+00:00",
            )

        self.assertEqual(payload["decision"], "discard")
        self.assertEqual(payload["signal_strength"], "mixed")
        self.assertAlmostEqual(payload["train_score_delta"], 1.0)
        self.assertAlmostEqual(payload["validation_score_delta"], -0.5)
        self.assertIn("validation_drop", payload["regression_flags"])
        self.assertEqual(payload["scoreboard_ref"], "rounds/round-001/scoreboard.json")

    def test_upsert_feedback_ledger_replaces_same_round_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "feedback-ledger.jsonl"
            first = {
                "feedback_distill_version": 1,
                "run_id": "demo-run",
                "round": 2,
                "mutation_key": "k",
                "mutation_id": "k#a002",
                "attempt": 2,
                "decision": "discard",
                "train_score_delta": 0.5,
                "validation_score_delta": -0.2,
                "parse_error_delta": 0.0,
                "timeout_rate_delta": 0.0,
                "signal_strength": "mixed",
                "regression_flags": ["validation_drop"],
                "dimension_feedback_summary": {},
                "suggested_adjustments": [],
                "scoreboard_ref": "rounds/round-002/scoreboard.json",
                "decision_ref": "rounds/round-002/decision.json",
                "worker_contract_ref": "rounds/round-002/worker-contract.json",
                "distilled_at": "2026-03-27T00:00:00+00:00",
            }
            second = dict(first)
            second["decision"] = "keep"
            second["signal_strength"] = "positive"
            second["validation_score_delta"] = 0.1
            upsert_feedback_ledger_entry(ledger_path, first)
            upsert_feedback_ledger_entry(ledger_path, second)

            entries = load_feedback_ledger(ledger_path)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["decision"], "keep")
        self.assertEqual(entries[0]["signal_strength"], "positive")

    def test_feedback_family_priority_tracks_recent_signal(self) -> None:
        ledger = [
            {
                "feedback_distill_version": 1,
                "run_id": "demo-run",
                "round": 1,
                "mutation_key": "positive",
                "mutation_id": "positive#a001",
                "attempt": 1,
                "decision": "keep",
                "train_score_delta": 1.0,
                "validation_score_delta": 0.0,
                "parse_error_delta": 0.0,
                "timeout_rate_delta": 0.0,
                "signal_strength": "positive",
                "regression_flags": [],
                "dimension_feedback_summary": {},
                "suggested_adjustments": [],
                "scoreboard_ref": "rounds/round-001/scoreboard.json",
                "decision_ref": "rounds/round-001/decision.json",
                "worker_contract_ref": "rounds/round-001/worker-contract.json",
                "distilled_at": "2026-03-27T00:00:00+00:00",
            },
            {
                "feedback_distill_version": 1,
                "run_id": "demo-run",
                "round": 1,
                "mutation_key": "negative",
                "mutation_id": "negative#a001",
                "attempt": 1,
                "decision": "discard",
                "train_score_delta": -0.2,
                "validation_score_delta": -0.1,
                "parse_error_delta": 0.0,
                "timeout_rate_delta": 0.0,
                "signal_strength": "negative",
                "regression_flags": ["validation_drop"],
                "dimension_feedback_summary": {},
                "suggested_adjustments": [],
                "scoreboard_ref": "rounds/round-001/scoreboard.json",
                "decision_ref": "rounds/round-001/decision.json",
                "worker_contract_ref": "rounds/round-001/worker-contract.json",
                "distilled_at": "2026-03-27T00:00:00+00:00",
            },
            {
                "feedback_distill_version": 1,
                "run_id": "demo-run",
                "round": 2,
                "mutation_key": "negative",
                "mutation_id": "negative#a002",
                "attempt": 2,
                "decision": "discard",
                "train_score_delta": -0.1,
                "validation_score_delta": -0.2,
                "parse_error_delta": 0.0,
                "timeout_rate_delta": 0.0,
                "signal_strength": "negative",
                "regression_flags": ["validation_drop"],
                "dimension_feedback_summary": {},
                "suggested_adjustments": [],
                "scoreboard_ref": "rounds/round-002/scoreboard.json",
                "decision_ref": "rounds/round-002/decision.json",
                "worker_contract_ref": "rounds/round-002/worker-contract.json",
                "distilled_at": "2026-03-27T00:00:00+00:00",
            },
        ]

        self.assertEqual(feedback_family_priority(ledger, mutation_key="positive"), (0, "recent_positive_signal"))
        self.assertEqual(
            feedback_family_priority(ledger, mutation_key="negative"),
            (4, "sustained_regression_deprioritized"),
        )
        self.assertEqual(feedback_family_priority(ledger, mutation_key="fresh"), (1, "no_feedback_history"))


if __name__ == "__main__":
    unittest.main()
