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
        "kind": "text_rephrase",
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
    subprocess.run(
        ["git", "update-ref", "refs/heads/champion/demo-run", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def current_head_sha(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


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
            init_git_repo(root)
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
                run_autoresearch, "REPO_ROOT", root
            ), mock.patch.object(run_autoresearch, "run_skill_suite_main", side_effect=fake_runner):
                head_sha = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=root,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                exit_code = run_autoresearch.main(["baseline", "--contract", str(contract_path)])

            self.assertEqual(exit_code, 0)
            self.assertEqual(call_counter["count"], 2)
            run_dir = root / ".autoworkflow" / "demo-run"
            self.assertTrue((run_dir / "scoreboard.json").is_file())
            scoreboard = json.loads((run_dir / "scoreboard.json").read_text(encoding="utf-8"))
            runtime = json.loads((run_dir / "runtime.json").read_text(encoding="utf-8"))
            self.assertEqual(scoreboard["baseline_sha"], head_sha)
            self.assertEqual(runtime["champion_sha"], head_sha)
            history_lines = (run_dir / "history.tsv").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(history_lines), 2)
            self.assertIn("\tbaseline\t", history_lines[1])
            champion_ref = subprocess.run(
                ["git", "show-ref", "--verify", "--quiet", "refs/heads/champion/demo-run"],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(champion_ref.returncode, 0)
            self.assertEqual(
                subprocess.run(
                    ["git", "rev-parse", "refs/heads/champion/demo-run"],
                    cwd=root,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip(),
                head_sha,
            )

    def test_baseline_refreshes_champion_branch_after_head_advanced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")

            def fake_runner(argv: list[str]) -> int:
                save_dir = Path(argv[argv.index("--save-dir") + 1])
                label = "train" if "baseline/train" in str(save_dir) else "validation"
                write_summary(save_dir, label, 9 if label == "train" else 8)
                return 0

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ), mock.patch.object(run_autoresearch, "run_skill_suite_main", side_effect=fake_runner):
                init_code = run_autoresearch.main(["init", "--contract", str(contract_path)])
                (root / "README.md").write_text("advanced\n", encoding="utf-8")
                subprocess.run(["git", "add", "README.md"], cwd=root, check=True, capture_output=True, text=True)
                subprocess.run(["git", "commit", "-q", "-m", "advance"], cwd=root, check=True, capture_output=True, text=True)
                advanced_sha = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=root,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                baseline_code = run_autoresearch.main(["baseline", "--contract", str(contract_path)])

            self.assertEqual(init_code, 0)
            self.assertEqual(baseline_code, 0)
            run_dir = root / ".autoworkflow" / "demo-run"
            runtime = json.loads((run_dir / "runtime.json").read_text(encoding="utf-8"))
            scoreboard = json.loads((run_dir / "scoreboard.json").read_text(encoding="utf-8"))
            champion_ref = subprocess.run(
                ["git", "show-ref", "--verify", "--quiet", "refs/heads/champion/demo-run"],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(runtime["champion_sha"], advanced_sha)
            self.assertEqual(scoreboard["baseline_sha"], advanced_sha)
            self.assertEqual(champion_ref.returncode, 0)
            self.assertEqual(
                subprocess.run(
                    ["git", "rev-parse", "refs/heads/champion/demo-run"],
                    cwd=root,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip(),
                advanced_sha,
            )
            self.assertEqual(runtime["active_round"], None)
            self.assertEqual(runtime["active_candidate_branch"], None)
            self.assertEqual(runtime["active_candidate_worktree"], None)

    def test_prepare_round_fails_closed_when_runtime_scoreboard_tampered_and_champion_branch_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")

            def fake_runner(argv: list[str]) -> int:
                save_dir = Path(argv[argv.index("--save-dir") + 1])
                label = "train" if "baseline/train" in str(save_dir) else "validation"
                write_summary(save_dir, label, 9 if label == "train" else 8)
                return 0

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ), mock.patch.object(run_autoresearch, "run_skill_suite_main", side_effect=fake_runner):
                init_code = run_autoresearch.main(["init", "--contract", str(contract_path)])
                baseline_code = run_autoresearch.main(["baseline", "--contract", str(contract_path)])
                baseline_sha = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=root,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                (root / "README.md").write_text("advanced\n", encoding="utf-8")
                subprocess.run(["git", "add", "README.md"], cwd=root, check=True, capture_output=True, text=True)
                subprocess.run(["git", "commit", "-q", "-m", "advance"], cwd=root, check=True, capture_output=True, text=True)
                advanced_sha = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=root,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()

                run_dir = root / ".autoworkflow" / "demo-run"
                registry_payload = {
                    "run_id": "demo-run",
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(load_contract(contract_path, repo_root=root)),
                    "entries": [
                        {
                            "mutation_key": "text_rephrase:demo:intro-tighten-v1",
                            "kind": "text_rephrase",
                            "status": "active",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "Tighten skill wording.",
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
                            "attempts": 0,
                            "last_selected_round": None,
                            "last_decision": None,
                        }
                    ],
                }
                (run_dir / "mutation-registry.json").write_text(
                    json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )

                runtime_path = run_dir / "runtime.json"
                runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))
                runtime_payload["champion_sha"] = advanced_sha
                runtime_path.write_text(json.dumps(runtime_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

                scoreboard_path = run_dir / "scoreboard.json"
                scoreboard_payload = json.loads(scoreboard_path.read_text(encoding="utf-8"))
                scoreboard_payload["baseline_sha"] = advanced_sha
                scoreboard_path.write_text(
                    json.dumps(scoreboard_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )

                subprocess.run(
                    ["git", "branch", "-D", "champion/demo-run"],
                    cwd=root,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                prepare_code = run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])

            self.assertEqual(init_code, 0)
            self.assertEqual(baseline_code, 0)
            self.assertEqual(prepare_code, 1)
            run_dir = root / ".autoworkflow" / "demo-run"
            runtime = json.loads((run_dir / "runtime.json").read_text(encoding="utf-8"))
            scoreboard = json.loads((run_dir / "scoreboard.json").read_text(encoding="utf-8"))
            champion_ref = subprocess.run(
                ["git", "show-ref", "--verify", "--quiet", "refs/heads/champion/demo-run"],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(scoreboard["baseline_sha"], advanced_sha)
            self.assertEqual(runtime["champion_sha"], advanced_sha)
            self.assertEqual(champion_ref.returncode, 1)
            self.assertFalse((run_dir / "rounds" / "round-001").exists())
            self.assertNotEqual(baseline_sha, advanced_sha)

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
                "baseline_sha": current_head_sha(root),
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

                contract_obj = load_contract(contract_path, repo_root=root)
                mutation_key = "text_rephrase:demo:intro-tighten-v1"
                registry_payload = {
                    "run_id": contract_obj.run_id,
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(contract_obj),
                    "entries": [
                        {
                            "mutation_key": mutation_key,
                            "kind": "text_rephrase",
                            "status": "active",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "Tighten skill wording.",
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
                            "attempts": 0,
                            "last_selected_round": None,
                            "last_decision": None,
                        }
                    ],
                }
                (run_dir / "mutation-registry.json").write_text(
                    json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )

                prepare_code = run_autoresearch.main(
                    ["prepare-round", "--contract", str(contract_path), "--mutation-key", mutation_key]
                )

                self.assertEqual(init_code, 0)
                self.assertEqual(prepare_code, 0)

                round_dir = run_dir / "rounds" / "round-001"
                candidate_worktree = run_dir / "worktrees" / "round-001"
                self.assertTrue((run_dir / "runtime.json").is_file())
                self.assertTrue((round_dir / "round.json").is_file())
                self.assertTrue((round_dir / "worktree.json").is_file())
                self.assertTrue((round_dir / "mutation.json").is_file())
                self.assertTrue((round_dir / "worker-contract.json").is_file())
                self.assertTrue(candidate_worktree.is_dir())

                round_payload = json.loads((round_dir / "round.json").read_text(encoding="utf-8"))
                self.assertTrue(round_payload.get("worker_contract_sha256"))

                registry_after = json.loads((run_dir / "mutation-registry.json").read_text(encoding="utf-8"))
                self.assertEqual(registry_after["entries"][0]["attempts"], 1)
                self.assertEqual(registry_after["entries"][0]["last_selected_round"], 1)

                discard_code = run_autoresearch.main(["discard-round", "--contract", str(contract_path)])

            self.assertEqual(discard_code, 0)
            runtime = json.loads((root / ".autoworkflow" / "demo-run" / "runtime.json").read_text(encoding="utf-8"))
            self.assertIsNone(runtime["active_round"])
            self.assertFalse(candidate_worktree.exists())

    def test_prepare_round_with_legacy_mutation_imports_into_registry(self) -> None:
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
                "baseline_sha": current_head_sha(root),
                "rounds_completed": 0,
                "best_round": 0,
                "lanes": [],
                "repo_tasks": [],
            }

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                init_code = run_autoresearch.main(["init", "--contract", str(contract_path)])
                run_dir = root / ".autoworkflow" / "demo-run"
                (run_dir / "scoreboard.json").write_text(json.dumps(scoreboard), encoding="utf-8")
                prepare_code = run_autoresearch.main(
                    ["prepare-round", "--contract", str(contract_path), "--mutation", str(mutation_path)]
                )

            self.assertEqual(init_code, 0)
            self.assertEqual(prepare_code, 0)
            registry = json.loads((root / ".autoworkflow" / "demo-run" / "mutation-registry.json").read_text(encoding="utf-8"))
            self.assertEqual(len(registry["entries"]), 1)
            self.assertEqual(registry["entries"][0]["origin"]["type"], "manual_import")
            self.assertEqual(registry["entries"][0]["attempts"], 1)
            round_dir = root / ".autoworkflow" / "demo-run" / "rounds" / "round-001"
            self.assertTrue((round_dir / "worker-contract.json").is_file())
            round_payload = json.loads((round_dir / "round.json").read_text(encoding="utf-8"))
            self.assertTrue(round_payload.get("worker_contract_sha256"))
            round_mutation = json.loads(
                (root / ".autoworkflow" / "demo-run" / "rounds" / "round-001" / "mutation.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(round_mutation["mutation_key"], "imported:text_rephrase:mut-001")
            self.assertEqual(round_mutation["attempt"], 1)

    def test_prepare_round_with_mutation_key_increments_attempt_on_second_prepare(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            scoreboard = {
                "run_id": "demo-run",
                "generated_at": "2026-03-26T00:00:00+00:00",
                "baseline_sha": current_head_sha(root),
                "rounds_completed": 0,
                "best_round": 0,
                "lanes": [],
                "repo_tasks": [],
            }

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                init_code = run_autoresearch.main(["init", "--contract", str(contract_path)])
                run_dir = root / ".autoworkflow" / "demo-run"
                (run_dir / "scoreboard.json").write_text(json.dumps(scoreboard), encoding="utf-8")

                contract_obj = load_contract(contract_path, repo_root=root)
                mutation_key = "text_rephrase:demo:intro-tighten-v1"
                registry_payload = {
                    "run_id": contract_obj.run_id,
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(contract_obj),
                    "entries": [
                        {
                            "mutation_key": mutation_key,
                            "kind": "text_rephrase",
                            "status": "active",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "Tighten skill wording.",
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
                            "attempts": 0,
                            "last_selected_round": None,
                            "last_decision": None,
                        }
                    ],
                }
                (run_dir / "mutation-registry.json").write_text(
                    json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )

                first_prepare = run_autoresearch.main(
                    ["prepare-round", "--contract", str(contract_path), "--mutation-key", mutation_key]
                )
                first_discard = run_autoresearch.main(["discard-round", "--contract", str(contract_path)])
                second_prepare = run_autoresearch.main(
                    ["prepare-round", "--contract", str(contract_path), "--mutation-key", mutation_key]
                )

            self.assertEqual(init_code, 0)
            self.assertEqual(first_prepare, 0)
            self.assertEqual(first_discard, 0)
            self.assertEqual(second_prepare, 0)
            registry_after = json.loads((root / ".autoworkflow" / "demo-run" / "mutation-registry.json").read_text(encoding="utf-8"))
            self.assertEqual(registry_after["entries"][0]["attempts"], 2)
            self.assertEqual(registry_after["entries"][0]["last_selected_round"], 2)
            round_mutation = json.loads(
                (root / ".autoworkflow" / "demo-run" / "rounds" / "round-002" / "mutation.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(round_mutation["attempt"], 2)

    def test_prepare_round_auto_selects_next_entry_from_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            scoreboard = {
                "run_id": "demo-run",
                "generated_at": "2026-03-26T00:00:00+00:00",
                "baseline_sha": current_head_sha(root),
                "rounds_completed": 0,
                "best_round": 0,
                "lanes": [],
                "repo_tasks": [],
            }

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                init_code = run_autoresearch.main(["init", "--contract", str(contract_path)])
                run_dir = root / ".autoworkflow" / "demo-run"
                (run_dir / "scoreboard.json").write_text(json.dumps(scoreboard), encoding="utf-8")

                contract_obj = load_contract(contract_path, repo_root=root)
                registry_payload = {
                    "run_id": contract_obj.run_id,
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(contract_obj),
                    "entries": [
                        {
                            "mutation_key": "text_rephrase:demo:first",
                            "kind": "text_rephrase",
                            "status": "active",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "First mutation.",
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
                            "attempts": 0,
                            "last_selected_round": None,
                            "last_decision": None,
                        },
                        {
                            "mutation_key": "text_rephrase:demo:second",
                            "kind": "text_rephrase",
                            "status": "active",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "Second mutation.",
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
                            "attempts": 0,
                            "last_selected_round": None,
                            "last_decision": None,
                        },
                    ],
                }
                (run_dir / "mutation-registry.json").write_text(
                    json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )

                prepare_code = run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])

            self.assertEqual(init_code, 0)
            self.assertEqual(prepare_code, 0)
            round_mutation = json.loads(
                (root / ".autoworkflow" / "demo-run" / "rounds" / "round-001" / "mutation.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(round_mutation["mutation_key"], "text_rephrase:demo:first")

    def test_prepare_round_auto_select_skips_disabled_first_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            scoreboard = {
                "run_id": "demo-run",
                "generated_at": "2026-03-26T00:00:00+00:00",
                "baseline_sha": current_head_sha(root),
                "rounds_completed": 0,
                "best_round": 0,
                "lanes": [],
                "repo_tasks": [],
            }

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                init_code = run_autoresearch.main(["init", "--contract", str(contract_path)])
                run_dir = root / ".autoworkflow" / "demo-run"
                (run_dir / "scoreboard.json").write_text(json.dumps(scoreboard), encoding="utf-8")

                contract_obj = load_contract(contract_path, repo_root=root)
                registry_payload = {
                    "run_id": contract_obj.run_id,
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(contract_obj),
                    "entries": [
                        {
                            "mutation_key": "text_rephrase:demo:disabled",
                            "kind": "text_rephrase",
                            "status": "disabled",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "Disabled mutation.",
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
                            "attempts": 0,
                            "last_selected_round": None,
                            "last_decision": None,
                        },
                        {
                            "mutation_key": "text_rephrase:demo:active",
                            "kind": "text_rephrase",
                            "status": "active",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "Active mutation.",
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
                            "attempts": 0,
                            "last_selected_round": None,
                            "last_decision": None,
                        },
                    ],
                }
                (run_dir / "mutation-registry.json").write_text(
                    json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )

                prepare_code = run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])

            self.assertEqual(init_code, 0)
            self.assertEqual(prepare_code, 0)
            round_mutation = json.loads(
                (root / ".autoworkflow" / "demo-run" / "rounds" / "round-001" / "mutation.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(round_mutation["mutation_key"], "text_rephrase:demo:active")

    def test_prepare_round_auto_select_errors_when_all_entries_unselectable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            scoreboard = {
                "run_id": "demo-run",
                "generated_at": "2026-03-26T00:00:00+00:00",
                "baseline_sha": current_head_sha(root),
                "rounds_completed": 0,
                "best_round": 0,
                "lanes": [],
                "repo_tasks": [],
            }

            stderr = io.StringIO()
            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ), mock.patch("sys.stderr", stderr):
                init_code = run_autoresearch.main(["init", "--contract", str(contract_path)])
                run_dir = root / ".autoworkflow" / "demo-run"
                (run_dir / "scoreboard.json").write_text(json.dumps(scoreboard), encoding="utf-8")

                contract_obj = load_contract(contract_path, repo_root=root)
                registry_payload = {
                    "run_id": contract_obj.run_id,
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(contract_obj),
                    "entries": [
                        {
                            "mutation_key": "text_rephrase:demo:exhausted",
                            "kind": "text_rephrase",
                            "status": "active",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "Exhausted mutation.",
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
                            "attempts": 2,
                            "last_selected_round": None,
                            "last_decision": None,
                        }
                    ],
                }
                (run_dir / "mutation-registry.json").write_text(
                    json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )

                prepare_code = run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])

            self.assertEqual(init_code, 0)
            self.assertEqual(prepare_code, 1)
            self.assertIn("No selectable mutation entries", stderr.getvalue())

    def test_prepare_round_mutation_key_overrides_auto_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            scoreboard = {
                "run_id": "demo-run",
                "generated_at": "2026-03-26T00:00:00+00:00",
                "baseline_sha": current_head_sha(root),
                "rounds_completed": 0,
                "best_round": 0,
                "lanes": [],
                "repo_tasks": [],
            }

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                init_code = run_autoresearch.main(["init", "--contract", str(contract_path)])
                run_dir = root / ".autoworkflow" / "demo-run"
                (run_dir / "scoreboard.json").write_text(json.dumps(scoreboard), encoding="utf-8")

                contract_obj = load_contract(contract_path, repo_root=root)
                registry_payload = {
                    "run_id": contract_obj.run_id,
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(contract_obj),
                    "entries": [
                        {
                            "mutation_key": "text_rephrase:demo:auto-would-pick-this",
                            "kind": "text_rephrase",
                            "status": "active",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "First mutation.",
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
                            "attempts": 0,
                            "last_selected_round": None,
                            "last_decision": None,
                        },
                        {
                            "mutation_key": "text_rephrase:demo:explicit",
                            "kind": "text_rephrase",
                            "status": "active",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "Second mutation.",
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
                            "attempts": 0,
                            "last_selected_round": None,
                            "last_decision": None,
                        },
                    ],
                }
                (run_dir / "mutation-registry.json").write_text(
                    json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )

                prepare_code = run_autoresearch.main(
                    [
                        "prepare-round",
                        "--contract",
                        str(contract_path),
                        "--mutation-key",
                        "text_rephrase:demo:explicit",
                    ]
                )

            self.assertEqual(init_code, 0)
            self.assertEqual(prepare_code, 0)
            round_mutation = json.loads(
                (root / ".autoworkflow" / "demo-run" / "rounds" / "round-001" / "mutation.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(round_mutation["mutation_key"], "text_rephrase:demo:explicit")


if __name__ == "__main__":
    unittest.main()
