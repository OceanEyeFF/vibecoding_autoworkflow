from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autoresearch_scoreboard import build_lane_scoreboard, build_repo_task_rows, build_scoreboard


class AutoresearchScoreboardTest(unittest.TestCase):
    def test_lane_aggregation_computes_rates_and_average(self) -> None:
        summary = {
            "suite_file": "memory-side-train.v1.yaml",
            "results": [
                {
                    "phase": "eval",
                    "repo_path": "/tmp/typer",
                    "task": "context-routing",
                    "backend": "claude",
                    "judge_backend": "claude",
                    "returncode": 0,
                    "timed_out": False,
                    "parse_error": None,
                    "structured_output": {"total_score": 10, "overall": "Good", "dimension_feedback": {}},
                },
                {
                    "phase": "eval",
                    "repo_path": "/tmp/typer",
                    "task": "knowledge-base",
                    "backend": "claude",
                    "judge_backend": "claude",
                    "returncode": 0,
                    "timed_out": True,
                    "parse_error": "timed out",
                    "structured_output": {"total_score": 7, "overall": "Okay", "dimension_feedback": {}},
                },
            ],
        }

        lane = build_lane_scoreboard("train", summary)
        self.assertEqual(lane["repos_total"], 1)
        self.assertEqual(lane["tasks_total"], 2)
        self.assertAlmostEqual(lane["pass_rate"], 0.5)
        self.assertAlmostEqual(lane["timeout_rate"], 0.5)
        self.assertAlmostEqual(lane["parse_error_rate"], 0.5)
        self.assertAlmostEqual(lane["avg_total_score"], 8.5)

    def test_repo_task_rows_keep_eval_structured_fields(self) -> None:
        summary = {
            "suite_file": "memory-side-validation.v1.yaml",
            "results": [
                {
                    "phase": "eval",
                    "repo_path": "/tmp/zustand",
                    "task": "writeback-cleanup",
                    "backend": "claude",
                    "judge_backend": "claude",
                    "returncode": 0,
                    "timed_out": False,
                    "parse_error": None,
                    "structured_output": {
                        "total_score": 9,
                        "overall": "Good",
                        "dimension_feedback": {"cleanup_quality": {"what_worked": "x", "needs_improvement": "y"}},
                    },
                }
            ],
        }
        rows = build_repo_task_rows("validation", summary)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["repo"], "zustand")
        self.assertEqual(rows[0]["task"], "writeback-cleanup")
        self.assertEqual(rows[0]["phase"], "eval")
        self.assertEqual(rows[0]["total_score"], 9.0)

    def test_build_scoreboard_uses_train_and_validation_lanes(self) -> None:
        train = {
            "suite_file": "train",
            "results": [],
        }
        validation = {
            "suite_file": "validation",
            "results": [],
        }
        scoreboard = build_scoreboard(
            run_id="demo-run",
            baseline_sha="abc123",
            lane_summaries={"train": train, "validation": validation},
        )
        self.assertEqual(scoreboard["run_id"], "demo-run")
        self.assertEqual(scoreboard["baseline_sha"], "abc123")
        self.assertEqual([lane["lane_name"] for lane in scoreboard["lanes"]], ["train", "validation"])


if __name__ == "__main__":
    unittest.main()
