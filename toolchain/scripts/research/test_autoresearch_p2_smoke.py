from __future__ import annotations

import io
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
from autoresearch_mutation_registry import compute_contract_fingerprint
from autoresearch_round import AutoresearchRoundManager


def build_p2_contract_payload(train_suite: str, validation_suite: str, acceptance_suite: str) -> dict[str, object]:
    prompt_path = "toolchain/scripts/research/tasks/context-routing-skill-prompt.md"
    return {
        "run_id": "demo-run",
        "label": "P2 Demo",
        "objective": "P2 deterministic orchestration smoke",
        "target_surface": "memory-side",
        "mutable_paths": [prompt_path],
        "frozen_paths": ["docs/knowledge"],
        "train_suites": [train_suite],
        "validation_suites": [validation_suite],
        "acceptance_suites": [acceptance_suite],
        "primary_metrics": ["avg_total_score"],
        "guard_metrics": ["parse_error_rate", "timeout_rate"],
        "qualitative_veto_checks": [],
        "max_rounds": 3,
        "max_candidate_attempts_per_round": 2,
        "timeout_policy": {"seconds": 120},
        "promotion_policy": {"mode": "manual"},
        "target_task": "context-routing-skill",
        "target_prompt_path": prompt_path,
    }


def init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "tester"], cwd=root, check=True, capture_output=True, text=True)
    (root / ".gitignore").write_text(".autoworkflow/\n", encoding="utf-8")
    (root / "README.md").write_text("initial\n", encoding="utf-8")
    (root / "docs" / "knowledge").mkdir(parents=True, exist_ok=True)
    (root / "toolchain" / "scripts" / "research" / "tasks").mkdir(parents=True, exist_ok=True)
    (root / "toolchain" / "scripts" / "research" / "tasks" / "context-routing-skill-prompt.md").write_text(
        "initial p2 prompt\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", ".gitignore", "README.md", "docs", "toolchain"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "update-ref", "refs/heads/champion/demo-run", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def write_suite_manifest(path: Path, *, prompt_file: str | None = None) -> None:
    prompt_line = f"    prompt_file: {prompt_file}\n" if prompt_file is not None else ""
    path.write_text(
        "version: 1\n"
        "defaults:\n"
        "  backend: codex\n"
        "  judge_backend: codex\n"
        "  with_eval: true\n"
        "runs:\n"
        "  - repo: .\n"
        "    task: context-routing\n"
        f"{prompt_line}",
        encoding="utf-8",
    )


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
                "backend": "codex",
                "judge_backend": "codex",
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
        "backend": "codex",
        "judge_backend": "codex",
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


def make_registry_entry(*, mutation_key: str, attempts: int = 0, last_decision: str | None = None) -> dict[str, object]:
    return {
        "mutation_key": mutation_key,
        "kind": "text_rephrase",
        "status": "active",
        "target_paths": ["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
        "allowed_actions": ["edit"],
        "instruction_seed": f"instruction for {mutation_key}",
        "expected_effect": {
            "hypothesis": "Improve train score without validation regression.",
            "primary_metrics": ["avg_total_score"],
            "guard_metrics": ["parse_error_rate", "timeout_rate"],
        },
        "guardrails": {
            "require_non_empty_diff": True,
            "max_files_touched": 1,
            "extra_frozen_paths": [],
        },
        "origin": {"type": "manual_seed", "ref": "test"},
        "attempts": attempts,
        "last_selected_round": 1 if attempts > 0 else None,
        "last_decision": last_decision,
    }


class AutoresearchP2OrchestrationSmokeTest(unittest.TestCase):
    def test_p2_cli_orchestration_emits_decision_and_replay_artifacts_with_mocked_lane_runs(self) -> None:
        # This is an orchestration smoke: CLI + artifacts + decision/replay wiring.
        # It intentionally mocks lane execution, so it is NOT an end-to-end proof of
        # candidate-side subprocess execution (run_skill_suite.py) correctness.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            write_suite_manifest(root / "train.yaml")
            write_suite_manifest(root / "validation.yaml")
            write_suite_manifest(root / "acceptance.yaml")
            contract_path = root / "contract.json"
            contract_path.write_text(
                json.dumps(build_p2_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")),
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
                run_dir = root / ".autoworkflow" / contract.run_id
                registry_payload = {
                    "run_id": contract.run_id,
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(contract),
                    "entries": [
                        make_registry_entry(mutation_key="text_rephrase:demo:p2-first"),
                        make_registry_entry(mutation_key="text_rephrase:demo:p2-second"),
                    ],
                }
                (run_dir / "mutation-registry.json").write_text(
                    json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )

                self.assertEqual(run_autoresearch.main(["prepare-round", "--contract", str(contract_path)]), 0)
                round_dir = run_dir / "rounds" / "round-001"
                expected_candidate_worktree = run_dir / "worktrees" / "round-001"
                prompt_path = (
                    expected_candidate_worktree
                    / "toolchain"
                    / "scripts"
                    / "research"
                    / "tasks"
                    / "context-routing-skill-prompt.md"
                )
                prompt_path.write_text("candidate p2 prompt\n", encoding="utf-8")
                (round_dir / "agent-report.md").write_text("# Agent Report\n\nApplied P2 prompt mutation.\n", encoding="utf-8")

                expected_non_replay_dirs = {round_dir / "train", round_dir / "validation"}
                expected_replay_dirs = {round_dir / "replay" / "train", round_dir / "replay" / "validation"}
                lane_calls: list[Path] = []

                def fake_lane_runner(
                    _self: AutoresearchRoundManager,
                    *,
                    candidate_worktree: Path,
                    contract,
                    suite_files: list[Path],
                    save_dir: Path,
                ) -> list[dict[str, object]]:
                    del contract
                    del suite_files
                    self.assertEqual(candidate_worktree.resolve(), expected_candidate_worktree.resolve())
                    lane_calls.append(save_dir)
                    if len(lane_calls) <= 2:
                        self.assertIn(save_dir, expected_non_replay_dirs)
                        score = 10.0 if save_dir.name == "train" else 9.0
                    else:
                        self.assertIn(save_dir, expected_replay_dirs)
                        score = 10.1 if save_dir.name == "train" else 9.0
                    return [{"suite_file": save_dir.name + ".yaml", "results": [build_eval_result(score)]}]

                with mock.patch.object(AutoresearchRoundManager, "_run_lane_suites", new=fake_lane_runner):
                    self.assertEqual(run_autoresearch.main(["run-round", "--contract", str(contract_path)]), 0)
                    self.assertEqual(run_autoresearch.main(["decide-round", "--contract", str(contract_path)]), 0)

                decision = json.loads((round_dir / "decision.json").read_text(encoding="utf-8"))
                replay_scoreboard = json.loads((round_dir / "replay" / "scoreboard.json").read_text(encoding="utf-8"))
                baseline_scoreboard = json.loads((run_dir / "scoreboard.json").read_text(encoding="utf-8"))

            self.assertEqual(decision["provisional_decision"], "keep")
            self.assertEqual(decision["decision"], "keep")
            self.assertEqual(decision["replay"]["status"], "passed")
            self.assertEqual(decision["replay"]["reason"], "replay_validation_non_regression")
            self.assertEqual(replay_scoreboard["lanes"][1]["avg_total_score"], 9.0)
            self.assertEqual(baseline_scoreboard["baseline_sha"], decision["candidate_sha"])


if __name__ == "__main__":
    unittest.main()
