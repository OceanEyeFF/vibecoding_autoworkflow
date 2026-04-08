from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autoresearch_lane_executor import capture_new_summary, execute_lane_suites


def write_summary(run_dir: Path, *, suite_file: str) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run-summary.json").write_text(
        json.dumps(
            {
                "runner": "run_skill_suite.py",
                "generated_at": "2026-03-26T00:00:00+00:00",
                "suite_file": suite_file,
                "results": [],
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


class LaneExecutorTest(unittest.TestCase):
    def test_capture_new_summary_prefers_new_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            save_dir = Path(tmp)
            existing = save_dir / "20260326T000000Z-old"
            write_summary(existing, suite_file="old.yaml")
            before = {existing}
            new_run = save_dir / "20260326T000001Z-new"
            write_summary(new_run, suite_file="new.yaml")

            summary_path = capture_new_summary(save_dir, before)

        self.assertEqual(summary_path, new_run / "run-summary.json")

    def test_capture_new_summary_falls_back_to_latest_available_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            save_dir = Path(tmp)
            first = save_dir / "20260326T000000Z-first"
            second = save_dir / "20260326T000001Z-second"
            write_summary(first, suite_file="first.yaml")
            write_summary(second, suite_file="second.yaml")
            os.utime(first / "run-summary.json", (1, 1))
            os.utime(second / "run-summary.json", (2, 2))

            summary_path = capture_new_summary(save_dir, set())

        self.assertEqual(summary_path, second / "run-summary.json")

    def test_capture_new_summary_raises_when_no_candidates_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            save_dir = Path(tmp)

            with self.assertRaises(FileNotFoundError):
                capture_new_summary(save_dir, set())

    def test_execute_lane_suites_runs_each_suite_and_loads_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            save_dir = Path(tmp) / "lane"
            suite_files = [Path("train.yaml"), Path("validation.yaml")]
            invoked: list[Path] = []

            def fake_run_suite(suite_file: Path) -> None:
                invoked.append(suite_file)
                run_dir = save_dir / f"20260326T00000{len(invoked)}Z-{suite_file.stem}"
                write_summary(run_dir, suite_file=suite_file.name)

            summaries = execute_lane_suites(suite_files, save_dir, run_suite=fake_run_suite)

        self.assertEqual(invoked, suite_files)
        self.assertEqual([summary["suite_file"] for summary in summaries], ["train.yaml", "validation.yaml"])


if __name__ == "__main__":
    unittest.main()
