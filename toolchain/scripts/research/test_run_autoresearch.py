from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_autoresearch


def build_contract_payload(train_suite: str, validation_suite: str, acceptance_suite: str) -> dict[str, object]:
    return {
        "run_id": "demo-run",
        "label": "Demo",
        "objective": "Baseline aggregation",
        "target_surface": "memory-side",
        "mutable_paths": ["product/memory-side/skills"],
        "frozen_paths": ["docs/knowledge"],
        "train_suites": [train_suite],
        "validation_suites": [validation_suite],
        "acceptance_suites": [acceptance_suite],
        "primary_metrics": ["avg_total_score"],
        "guard_metrics": ["parse_error_rate"],
        "qualitative_veto_checks": [],
        "max_rounds": 3,
        "max_candidate_attempts_per_round": 2,
        "timeout_policy": {"seconds": 120},
        "promotion_policy": {"mode": "manual"},
    }


def build_mutation_payload(round_number: int = 1, mutation_id: str = "mut-001") -> dict[str, object]:
    return {
        "round": round_number,
        "mutation_id": mutation_id,
        "kind": "prompt_rewrite",
        "target_paths": ["product/memory-side/skills"],
        "allowed_actions": ["edit"],
        "instruction": "Tighten skill wording.",
        "expected_effect": "Improve train score without validation regression.",
    }


def write_summary(save_dir: Path, label: str, score: int) -> None:
    run_dir = save_dir / f"20260326T000000Z-{label}"
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "runner": "run_skill_suite.py",
        "generated_at": "2026-03-26T00:00:00+00:00",
        "suite_file": f"{label}.yaml",
        "results": [
            {
                "repo_path": f"/tmp/{label}",
                "task": "context-routing",
                "phase": "eval",
                "backend": "claude",
                "judge_backend": "claude",
                "prompt_file": "/tmp/prompt.md",
                "returncode": 0,
                "timed_out": False,
                "elapsed_seconds": 1.0,
                "started_at": "2026-03-26T00:00:00+00:00",
                "finished_at": "2026-03-26T00:00:01+00:00",
                "schema_file": None,
                "parse_error": None,
                "structured_output": {
                    "total_score": score,
                    "overall": "Good",
                    "dimension_feedback": {},
                },
                "artifacts": {},
            }
        ],
    }
    (run_dir / "run-summary.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")


def init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "tester"], cwd=root, check=True, capture_output=True, text=True)
    (root / ".gitignore").write_text(".autoworkflow/\n", encoding="utf-8")
    (root / "README.md").write_text("initial\n", encoding="utf-8")
    (root / "product" / "memory-side" / "skills").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "knowledge").mkdir(parents=True, exist_ok=True)
    (root / "product" / "memory-side" / "skills" / "skill.md").write_text("initial skill\n", encoding="utf-8")
    (root / "docs" / "knowledge" / "README.md").write_text("frozen\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore", "README.md", "product", "docs"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True, capture_output=True, text=True)


class RunAutoresearchTest(unittest.TestCase):
    def test_init_writes_contract_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                exit_code = run_autoresearch.main(["init", "--contract", str(contract_path)])

            self.assertEqual(exit_code, 0)
            run_dir = root / ".autoworkflow" / "demo-run"
            self.assertTrue((run_dir / "contract.json").is_file())
            self.assertTrue((run_dir / "runtime.json").is_file())
            history = (run_dir / "history.tsv").read_text(encoding="utf-8")
            self.assertIn("round\tkind\tbase_sha", history)

    def test_baseline_delegates_to_runner_and_writes_scoreboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")

            call_counter = {"count": 0}

            def fake_runner(argv: list[str]) -> int:
                call_counter["count"] += 1
                save_dir = Path(argv[argv.index("--save-dir") + 1])
                label = "train" if "baseline/train" in str(save_dir) else "validation"
                write_summary(save_dir, label, 9 if label == "train" else 8)
                return 0

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", Path.cwd()
            ), mock.patch.object(run_autoresearch, "run_skill_suite_main", side_effect=fake_runner), mock.patch.object(
                run_autoresearch, "resolve_head_sha", return_value="abc123"
            ):
                exit_code = run_autoresearch.main(["baseline", "--contract", str(contract_path)])

            self.assertEqual(exit_code, 0)
            self.assertEqual(call_counter["count"], 2)
            run_dir = root / ".autoworkflow" / "demo-run"
            self.assertTrue((run_dir / "scoreboard.json").is_file())
            scoreboard = json.loads((run_dir / "scoreboard.json").read_text(encoding="utf-8"))
            self.assertEqual(scoreboard["baseline_sha"], "abc123")
            history_lines = (run_dir / "history.tsv").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(history_lines), 2)
            self.assertIn("\tbaseline\t", history_lines[1])

    def test_prepare_round_and_discard_round_via_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            mutation_path = root / "mutation.json"
            mutation_path.write_text(json.dumps(build_mutation_payload()), encoding="utf-8")
            scoreboard = {
                "run_id": "demo-run",
                "generated_at": "2026-03-26T00:00:00+00:00",
                "baseline_sha": "abc123",
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
                        "pass_rate": 1.0,
                        "timeout_rate": 0.0,
                        "parse_error_rate": 0.0,
                        "avg_total_score": 9.0,
                    },
                    {
                        "lane_name": "validation",
                        "suite_file": "validation.yaml",
                        "backend": "claude",
                        "judge_backend": "claude",
                        "repos_total": 1,
                        "tasks_total": 1,
                        "pass_rate": 1.0,
                        "timeout_rate": 0.0,
                        "parse_error_rate": 0.0,
                        "avg_total_score": 8.0,
                    },
                ],
                "repo_tasks": [],
            }

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                init_code = run_autoresearch.main(["init", "--contract", str(contract_path)])
                run_dir = root / ".autoworkflow" / "demo-run"
                (run_dir / "scoreboard.json").parent.mkdir(parents=True, exist_ok=True)
                (run_dir / "scoreboard.json").write_text(json.dumps(scoreboard), encoding="utf-8")
                prepare_code = run_autoresearch.main(
                    ["prepare-round", "--contract", str(contract_path), "--mutation", str(mutation_path)]
                )

                self.assertEqual(init_code, 0)
                self.assertEqual(prepare_code, 0)

                round_dir = run_dir / "rounds" / "round-001"
                candidate_worktree = run_dir / "worktrees" / "round-001"
                self.assertTrue((run_dir / "runtime.json").is_file())
                self.assertTrue((round_dir / "round.json").is_file())
                self.assertTrue((round_dir / "worktree.json").is_file())
                self.assertTrue((round_dir / "mutation.json").is_file())
                self.assertTrue(candidate_worktree.is_dir())

                discard_code = run_autoresearch.main(["discard-round", "--contract", str(contract_path)])

            self.assertEqual(discard_code, 0)
            runtime = json.loads((root / ".autoworkflow" / "demo-run" / "runtime.json").read_text(encoding="utf-8"))
            self.assertIsNone(runtime["active_round"])
            self.assertFalse(candidate_worktree.exists())


if __name__ == "__main__":
    unittest.main()
