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


def build_contract_payload(train_suite: str, validation_suite: str, acceptance_suite: str) -> dict[str, object]:
    return {
        "run_id": "demo-run",
        "label": "Demo",
        "objective": "P1.1 smoke",
        "target_surface": "memory-side",
        "mutable_paths": ["product/harness/skills"],
        "frozen_paths": ["docs"],
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
    (root / "product" / "harness" / "skills").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "product" / "harness" / "skills" / "skill.md").write_text("initial skill\n", encoding="utf-8")
    (root / "docs" / "README.md").write_text("frozen\n", encoding="utf-8")
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


def write_minimal_suite(path: Path) -> None:
    path.write_text(
        "version: 1\n"
        "defaults:\n"
        "  backend: claude\n"
        "runs:\n"
        "  - repo: typer\n"
        "    task: context-routing\n",
        encoding="utf-8",
    )


def make_registry_entry(*, mutation_key: str, status: str = "active", attempts: int = 0) -> dict[str, object]:
    return {
        "mutation_key": mutation_key,
        "kind": "text_rephrase",
        "status": status,
        "target_paths": ["product/harness/skills"],
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


class AutoresearchP11SmokeTest(unittest.TestCase):
    def test_full_cli_chain_auto_select_to_decide_keep(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            write_minimal_suite(root / "train.yaml")
            write_minimal_suite(root / "validation.yaml")
            write_minimal_suite(root / "acceptance.yaml")
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
                contract,
                suite_files: list[Path],
                save_dir: Path,
            ) -> list[dict[str, object]]:
                del candidate_worktree, contract, suite_files
                if save_dir.name == "train":
                    return [{"suite_file": "train.yaml", "results": [build_eval_result(10.0)]}]
                return [{"suite_file": "validation.yaml", "results": [build_eval_result(8.0)]}]

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ), mock.patch.object(run_autoresearch, "run_skill_suite_main", side_effect=fake_baseline_runner), mock.patch.object(
                AutoresearchRoundManager, "_run_lane_suites", new=fake_lane_runner
            ):
                init_code = run_autoresearch.main(["init", "--contract", str(contract_path)])
                baseline_code = run_autoresearch.main(["baseline", "--contract", str(contract_path)])

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

                prepare_code = run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])
                round_dir = run_dir / "rounds" / "round-001"
                candidate_worktree = run_dir / "worktrees" / "round-001"
                (candidate_worktree / "product" / "harness" / "skills" / "skill.md").write_text(
                    "candidate change\n",
                    encoding="utf-8",
                )
                (round_dir / "agent-report.md").write_text("# Agent Report\n\nApplied mutation.\n", encoding="utf-8")

                run_code = run_autoresearch.main(["run-round", "--contract", str(contract_path)])
                decide_code = run_autoresearch.main(["decide-round", "--contract", str(contract_path)])

            self.assertEqual(init_code, 0)
            self.assertEqual(baseline_code, 0)
            self.assertEqual(prepare_code, 0)
            self.assertEqual(run_code, 0)
            self.assertEqual(decide_code, 0)

            decision_payload = json.loads((run_dir / "rounds" / "round-001" / "decision.json").read_text(encoding="utf-8"))
            self.assertEqual(decision_payload["decision"], "keep")
            mutation_payload = json.loads((run_dir / "rounds" / "round-001" / "mutation.json").read_text(encoding="utf-8"))
            self.assertEqual(mutation_payload["mutation_key"], "text_rephrase:demo:auto-first")

    def test_prepare_round_mutation_key_overrides_auto_in_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            write_minimal_suite(root / "train.yaml")
            write_minimal_suite(root / "validation.yaml")
            write_minimal_suite(root / "acceptance.yaml")
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
                run_autoresearch.main(["init", "--contract", str(contract_path)])
                run_autoresearch.main(["baseline", "--contract", str(contract_path)])
                contract = load_contract(contract_path, repo_root=root)
                run_dir = root / ".autoworkflow" / "demo-run"
                registry_payload = {
                    "run_id": contract.run_id,
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(contract),
                    "entries": [
                        make_registry_entry(mutation_key="text_rephrase:demo:auto-would-pick"),
                        make_registry_entry(mutation_key="text_rephrase:demo:explicit"),
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

            self.assertEqual(prepare_code, 0)
            selected = json.loads(
                (root / ".autoworkflow" / "demo-run" / "rounds" / "round-001" / "mutation.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(selected["mutation_key"], "text_rephrase:demo:explicit")

    def test_prepare_round_fails_when_all_entries_unselectable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            write_minimal_suite(root / "train.yaml")
            write_minimal_suite(root / "validation.yaml")
            write_minimal_suite(root / "acceptance.yaml")
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

            stdout = io.StringIO()
            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ), mock.patch.object(run_autoresearch, "run_skill_suite_main", side_effect=fake_baseline_runner), mock.patch(
                "sys.stdout", stdout
            ):
                run_autoresearch.main(["init", "--contract", str(contract_path)])
                run_autoresearch.main(["baseline", "--contract", str(contract_path)])
                contract = load_contract(contract_path, repo_root=root)
                run_dir = root / ".autoworkflow" / "demo-run"
                registry_payload = {
                    "run_id": contract.run_id,
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(contract),
                    "entries": [
                        make_registry_entry(mutation_key="text_rephrase:demo:disabled", status="disabled"),
                        make_registry_entry(mutation_key="text_rephrase:demo:exhausted", attempts=2),
                    ],
                }
                (run_dir / "mutation-registry.json").write_text(
                    json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )
                prepare_code = run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])

            self.assertEqual(prepare_code, 0)
            stdout_value = stdout.getvalue()
            self.assertIn("prepare_round_status: stopped", stdout_value)
            self.assertIn("stop_kind: mutation_families_exhausted_without_keep", stdout_value)

    def test_run_round_rejects_tampered_worker_contract_in_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            write_minimal_suite(root / "train.yaml")
            write_minimal_suite(root / "validation.yaml")
            write_minimal_suite(root / "acceptance.yaml")
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

            stderr = io.StringIO()
            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ), mock.patch.object(run_autoresearch, "run_skill_suite_main", side_effect=fake_baseline_runner), mock.patch(
                "sys.stderr", stderr
            ):
                run_autoresearch.main(["init", "--contract", str(contract_path)])
                run_autoresearch.main(["baseline", "--contract", str(contract_path)])
                contract = load_contract(contract_path, repo_root=root)
                run_dir = root / ".autoworkflow" / "demo-run"
                registry_payload = {
                    "run_id": contract.run_id,
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(contract),
                    "entries": [make_registry_entry(mutation_key="text_rephrase:demo:auto-first")],
                }
                (run_dir / "mutation-registry.json").write_text(
                    json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )
                run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])

                round_dir = run_dir / "rounds" / "round-001"
                candidate_worktree = run_dir / "worktrees" / "round-001"
                (candidate_worktree / "product" / "harness" / "skills" / "skill.md").write_text(
                    "candidate change\n",
                    encoding="utf-8",
                )
                (round_dir / "agent-report.md").write_text("# Agent Report\n\nApplied mutation.\n", encoding="utf-8")
                worker_contract_path = round_dir / "worker-contract.json"
                worker_payload = json.loads(worker_contract_path.read_text(encoding="utf-8"))
                worker_payload["instruction"] = "tampered"
                worker_contract_path.write_text(
                    json.dumps(worker_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )
                run_code = run_autoresearch.main(["run-round", "--contract", str(contract_path)])

            self.assertEqual(run_code, 1)
            self.assertIn("hash recorded in round.json", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
