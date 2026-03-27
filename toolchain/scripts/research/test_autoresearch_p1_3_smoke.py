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
from autoresearch_contract import load_contract
from autoresearch_feedback_distill import load_feedback_ledger
from autoresearch_mutation_registry import compute_contract_fingerprint
from autoresearch_round import AutoresearchRoundManager


def build_contract_payload(train_suite: str, validation_suite: str, acceptance_suite: str) -> dict[str, object]:
    return {
        "run_id": "demo-run",
        "label": "Demo",
        "objective": "P1.3 smoke",
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


def write_summary(save_dir: Path, label: str, score: float) -> None:
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


def build_eval_result(score: float) -> dict[str, object]:
    return {
        "repo_path": "/tmp/repo",
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


def make_registry_entry(*, mutation_key: str, attempts: int = 0) -> dict[str, object]:
    return {
        "mutation_key": mutation_key,
        "kind": "text_rephrase",
        "status": "active",
        "target_paths": ["product/memory-side/skills"],
        "allowed_actions": ["edit"],
        "instruction_seed": f"instruction for {mutation_key}",
        "expected_effect": {
            "hypothesis": "Improve train score without validation regression.",
            "primary_metrics": ["avg_total_score"],
            "guard_metrics": ["parse_error_rate"],
        },
        "guardrails": {
            "require_non_empty_diff": True,
            "max_files_touched": 1,
            "extra_frozen_paths": [],
        },
        "origin": {"type": "manual_seed", "ref": "test"},
        "attempts": attempts,
        "last_selected_round": None,
        "last_decision": None,
    }


class AutoresearchP13SmokeTest(unittest.TestCase):
    def test_full_cli_chain_writes_distill_and_reuses_positive_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract_path = root / "contract.json"
            contract_path.write_text(
                json.dumps(build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")),
                encoding="utf-8",
            )

            def fake_baseline_runner(argv: list[str]) -> int:
                save_dir = Path(argv[argv.index("--save-dir") + 1])
                label = "train" if "baseline/train" in str(save_dir) else "validation"
                write_summary(save_dir, label, 9.0 if label == "train" else 8.0)
                return 0

            def fake_lane_runner(
                _self: AutoresearchRoundManager,
                *,
                candidate_worktree: Path,
                suite_files: list[Path],
                save_dir: Path,
            ) -> list[dict[str, object]]:
                del candidate_worktree, suite_files
                if save_dir.name == "train":
                    return [{"suite_file": "train.yaml", "results": [build_eval_result(10.0)]}]
                return [{"suite_file": "validation.yaml", "results": [build_eval_result(8.0)]}]

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ), mock.patch.object(run_autoresearch, "run_skill_suite_main", side_effect=fake_baseline_runner), mock.patch.object(
                AutoresearchRoundManager, "_run_lane_suites", new=fake_lane_runner
            ):
                self.assertEqual(run_autoresearch.main(["init", "--contract", str(contract_path)]), 0)
                self.assertEqual(run_autoresearch.main(["baseline", "--contract", str(contract_path)]), 0)

                contract = load_contract(contract_path, repo_root=root)
                run_dir = root / ".autoworkflow" / "demo-run"
                registry_payload = {
                    "run_id": contract.run_id,
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(contract),
                    "entries": [
                        make_registry_entry(mutation_key="text_rephrase:demo:auto-first"),
                        make_registry_entry(mutation_key="text_rephrase:demo:auto-second"),
                    ],
                }
                (run_dir / "mutation-registry.json").write_text(
                    json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )

                self.assertEqual(run_autoresearch.main(["prepare-round", "--contract", str(contract_path)]), 0)
                first_round_dir = run_dir / "rounds" / "round-001"
                first_candidate = run_dir / "worktrees" / "round-001"
                (first_candidate / "product" / "memory-side" / "skills" / "skill.md").write_text(
                    "candidate change one\n",
                    encoding="utf-8",
                )
                (first_round_dir / "agent-report.md").write_text("# Agent Report\n\nApplied mutation.\n", encoding="utf-8")

                self.assertEqual(run_autoresearch.main(["run-round", "--contract", str(contract_path)]), 0)
                self.assertEqual(run_autoresearch.main(["decide-round", "--contract", str(contract_path)]), 0)

                first_mutation = json.loads((first_round_dir / "mutation.json").read_text(encoding="utf-8"))
                first_distill = json.loads((first_round_dir / "feedback-distill.json").read_text(encoding="utf-8"))
                feedback_ledger = load_feedback_ledger(run_dir / "feedback-ledger.jsonl")

                self.assertEqual(first_mutation["mutation_key"], "text_rephrase:demo:auto-first")
                self.assertEqual(first_distill["signal_strength"], "positive")
                self.assertEqual(len(feedback_ledger), 1)

                self.assertEqual(run_autoresearch.main(["prepare-round", "--contract", str(contract_path)]), 0)
                second_round_dir = run_dir / "rounds" / "round-002"
                second_mutation = json.loads((second_round_dir / "mutation.json").read_text(encoding="utf-8"))

            self.assertEqual(second_mutation["mutation_key"], "text_rephrase:demo:auto-first")

    def test_prepare_round_adaptive_guardrail_prefers_fresh_family_over_regressed_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract_path = root / "contract.json"
            contract_path.write_text(
                json.dumps(build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")),
                encoding="utf-8",
            )

            def fake_baseline_runner(argv: list[str]) -> int:
                save_dir = Path(argv[argv.index("--save-dir") + 1])
                label = "train" if "baseline/train" in str(save_dir) else "validation"
                write_summary(save_dir, label, 9.0 if label == "train" else 8.0)
                return 0

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ), mock.patch.object(run_autoresearch, "run_skill_suite_main", side_effect=fake_baseline_runner):
                self.assertEqual(run_autoresearch.main(["init", "--contract", str(contract_path)]), 0)
                self.assertEqual(run_autoresearch.main(["baseline", "--contract", str(contract_path)]), 0)

                contract = load_contract(contract_path, repo_root=root)
                run_dir = root / ".autoworkflow" / "demo-run"
                registry_payload = {
                    "run_id": contract.run_id,
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(contract),
                    "entries": [
                        make_registry_entry(mutation_key="text_rephrase:demo:regressed-family"),
                        make_registry_entry(mutation_key="text_rephrase:demo:fresh-family", attempts=1),
                    ],
                }
                (run_dir / "mutation-registry.json").write_text(
                    json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )
                feedback_entry = {
                    "feedback_distill_version": 1,
                    "run_id": contract.run_id,
                    "round": 1,
                    "mutation_key": "text_rephrase:demo:regressed-family",
                    "mutation_id": "text_rephrase:demo:regressed-family#a001",
                    "attempt": 1,
                    "decision": "discard",
                    "train_score_delta": 0.2,
                    "validation_score_delta": -0.4,
                    "parse_error_delta": 0.0,
                    "timeout_rate_delta": 0.0,
                    "signal_strength": "mixed",
                    "regression_flags": ["validation_drop"],
                    "dimension_feedback_summary": {
                        "decision_signal": "rejected",
                        "train_score": "improved",
                        "validation_score": "weaker",
                        "stability": "score_regression",
                    },
                    "suggested_adjustments": ["narrow the next retry to protect validation behavior"],
                    "scoreboard_ref": "rounds/round-001/scoreboard.json",
                    "decision_ref": "rounds/round-001/decision.json",
                    "worker_contract_ref": "rounds/round-001/worker-contract.json",
                    "distilled_at": "2026-03-27T00:00:00+00:00",
                }
                (run_dir / "feedback-ledger.jsonl").write_text(json.dumps(feedback_entry) + "\n", encoding="utf-8")

                self.assertEqual(run_autoresearch.main(["prepare-round", "--contract", str(contract_path)]), 0)
                mutation = json.loads((run_dir / "rounds" / "round-001" / "mutation.json").read_text(encoding="utf-8"))

            self.assertEqual(mutation["mutation_key"], "text_rephrase:demo:fresh-family")


if __name__ == "__main__":
    unittest.main()
