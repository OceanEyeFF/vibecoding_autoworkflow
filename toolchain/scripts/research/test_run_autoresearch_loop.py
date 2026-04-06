from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_autoresearch
import run_autoresearch_loop
from backend_runner import build_retry_policy
from autoresearch_contract import load_contract
from autoresearch_mutation_registry import compute_contract_fingerprint
from autoresearch_round import AutoresearchRoundManager
from autoresearch_stop import AutoresearchStop
from worktree_manager import read_json, write_json


def build_p2_contract_payload(train_suite: str, validation_suite: str, acceptance_suite: str) -> dict[str, object]:
    prompt_path = "toolchain/scripts/research/tasks/context-routing-skill-prompt.md"
    return {
        "run_id": "demo-run",
        "label": "P2 Loop Demo",
        "objective": "P2 loop smoke",
        "target_surface": "research prompt",
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
        "initial prompt\n",
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


def write_suite_manifest(path: Path) -> None:
    path.write_text(
        "version: 1\n"
        "defaults:\n"
        "  backend: codex\n"
        "  judge_backend: codex\n"
        "  with_eval: true\n"
        "runs:\n"
        "  - repo: .\n"
        "    task: context-routing\n",
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


def make_registry_entry(*, mutation_key: str) -> dict[str, object]:
    return {
        "mutation_key": mutation_key,
        "kind": "text_rephrase",
        "status": "active",
        "target_paths": ["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
        "allowed_actions": ["edit"],
        "instruction_seed": f"instruction for {mutation_key}",
        "expected_effect": {
            "hypothesis": "Improve score without regression.",
            "primary_metrics": ["avg_total_score"],
            "guard_metrics": ["parse_error_rate", "timeout_rate"],
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


class RunAutoresearchLoopTest(unittest.TestCase):
    def test_build_backend_context_normalizes_opencode_output_format(self) -> None:
        args = SimpleNamespace(
            permission_mode="bypassPermissions",
            output_format="text",
            sandbox="workspace-write",
            full_auto=True,
            codex_reasoning_effort="high",
        )

        context = run_autoresearch_loop.build_backend_context(args, "opencode")

        self.assertEqual(
            context,
            {
                "output_format": "default",
            },
        )

    def test_execute_worker_phase_uses_configured_backend_and_writes_retry_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate_worktree = root / "candidate"
            candidate_worktree.mkdir(parents=True, exist_ok=True)
            worker_contract_path = root / "worker-contract.json"
            worker_contract = {
                "candidate_worktree": str(candidate_worktree),
                "round": 1,
                "mutation_key": "demo",
                "objective": "Improve prompt",
                "target_surface": "prompt",
                "instruction": "Tighten wording.",
                "target_paths": ["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
            }
            worker_contract_path.write_text(json.dumps(worker_contract), encoding="utf-8")

            args = run_autoresearch_loop.parse_args(
                [
                    "--contract",
                    str(root / "contract.json"),
                    "--worker-backend",
                    "claude",
                    "--worker-model",
                    "claude-opus",
                ]
            )
            contract = SimpleNamespace(
                worker_backend="codex",
                worker_model=None,
                retry_policy=build_retry_policy(max_attempts=3, backoff_seconds=0),
                payload={"timeout_policy": {"seconds": 120}},
            )

            class FakeBackend:
                backend_id = "claude"

                def healthcheck(self) -> tuple[bool, str]:
                    return True, "claude"

            class FakeAttempt:
                def __init__(self, payload: dict[str, object]) -> None:
                    self.payload = payload

                def to_dict(self) -> dict[str, object]:
                    return dict(self.payload)

            fake_result = SimpleNamespace(
                backend_id="claude",
                command=["claude", "-p", "prompt"],
                returncode=0,
                timed_out=False,
                raw_stdout="raw",
                raw_stderr="",
                final_message="worker summary",
                failure_reason=None,
                attempt_count=3,
                final_attempt=3,
                attempts=[
                    FakeAttempt(
                        {
                            "attempt": 1,
                            "returncode": None,
                            "timed_out": True,
                            "failure_reason": "timeout",
                            "parse_error": None,
                            "raw_stdout_excerpt": None,
                            "raw_stderr_excerpt": None,
                            "started_at": "2026-03-26T00:00:00+00:00",
                            "finished_at": "2026-03-26T00:00:01+00:00",
                            "elapsed_seconds": 1.0,
                        }
                    ),
                    FakeAttempt(
                        {
                            "attempt": 2,
                            "returncode": 1,
                            "timed_out": False,
                            "failure_reason": "transient_disconnect",
                            "parse_error": None,
                            "raw_stdout_excerpt": "temporary",
                            "raw_stderr_excerpt": "temporary",
                            "started_at": "2026-03-26T00:00:02+00:00",
                            "finished_at": "2026-03-26T00:00:03+00:00",
                            "elapsed_seconds": 1.0,
                        }
                    ),
                    FakeAttempt(
                        {
                            "attempt": 3,
                            "returncode": 0,
                            "timed_out": False,
                            "failure_reason": None,
                            "parse_error": None,
                            "raw_stdout_excerpt": "worker summary",
                            "raw_stderr_excerpt": None,
                            "started_at": "2026-03-26T00:00:04+00:00",
                            "finished_at": "2026-03-26T00:00:05+00:00",
                            "elapsed_seconds": 1.0,
                        }
                    ),
                ],
                started_at="2026-03-26T00:00:04+00:00",
                finished_at="2026-03-26T00:00:05+00:00",
                elapsed_seconds=1.0,
                backend_context={"permission_mode": "bypassPermissions", "output_format": "text"},
            )

            with mock.patch.object(run_autoresearch_loop, "build_backend", return_value=FakeBackend()) as mocked_backend, mock.patch.object(
                run_autoresearch_loop, "run_phase", return_value=fake_result
            ):
                result = run_autoresearch_loop.execute_worker_phase(
                    args=args,
                    contract=contract,
                    worker_contract_path=worker_contract_path,
                    worker_contract=worker_contract,
                )

            self.assertIs(result, fake_result)
            mocked_backend.assert_called_once_with("claude", args)
            meta = json.loads((root / "worker.meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["backend"], "claude")
            self.assertEqual(meta["attempt_count"], 3)
            self.assertEqual(meta["final_attempt"], 3)
            self.assertEqual(len(meta["attempts"]), 3)

    def test_build_worker_prompt_renders_aggregate_guidance(self) -> None:
        worker_contract = {
            "round": 1,
            "mutation_key": "text_rephrase:demo:first",
            "objective": "P2 loop smoke",
            "target_surface": "research prompt",
            "instruction": "Tighten the prompt.",
            "target_paths": ["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
            "comparison_baseline": {"train_score": 9.0, "validation_score": 8.0},
            "recent_feedback_excerpt": ["round=1 | mutation=seed | decision=discard | signal=mixed"],
            "aggregate_prompt_guidance": {
                "aggregate_direction": "negative",
                "aggregate_suggested_adjustments": [
                    "tighten the initial read list and cap follow-up drilling after the first entrypoint pass"
                ],
                "top_regression_repos": ["typer"],
                "top_improvement_repos": [],
                "dominant_dimension_signals": [],
                "generation_status": "generated",
            },
        }

        prompt = run_autoresearch_loop.build_worker_prompt(Path("/tmp/worker-contract.json"), worker_contract)

        self.assertIn("Aggregate prompt guidance:", prompt)
        self.assertIn("- direction: negative", prompt)
        self.assertIn(
            "- next: tighten the initial read list and cap follow-up drilling after the first entrypoint pass",
            prompt,
        )

    def test_build_worker_prompt_skips_placeholder_aggregate_guidance(self) -> None:
        worker_contract = {
            "round": 1,
            "mutation_key": "text_rephrase:demo:first",
            "objective": "P2 loop smoke",
            "target_surface": "research prompt",
            "instruction": "Tighten the prompt.",
            "target_paths": ["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
            "comparison_baseline": {"train_score": 9.0, "validation_score": 8.0},
            "recent_feedback_excerpt": [],
            "aggregate_prompt_guidance": {
                "aggregate_direction": "mixed",
                "aggregate_suggested_adjustments": [],
                "top_regression_repos": [],
                "top_improvement_repos": [],
                "dominant_dimension_signals": [],
                "generation_status": "no_prior_feedback",
            },
        }

        prompt = run_autoresearch_loop.build_worker_prompt(Path("/tmp/worker-contract.json"), worker_contract)

        self.assertNotIn("Aggregate prompt guidance:", prompt)
        self.assertNotIn("- direction: mixed", prompt)

    def test_loop_runs_one_round_writes_agent_report_and_stops_on_stop_gate(self) -> None:
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
            ), mock.patch.object(run_autoresearch_loop, "REPO_ROOT", root), mock.patch.object(
                run_autoresearch, "run_skill_suite_main", side_effect=fake_baseline_runner
            ):
                contract = load_contract(contract_path, repo_root=root)
                run_dir = root / ".autoworkflow" / contract.run_id
                seed_path = root / "registry-seed.json"
                seed_path.write_text(
                    json.dumps(
                        {
                            "registry_version": 1,
                            "entries": [make_registry_entry(mutation_key="text_rephrase:demo:first")],
                        },
                        ensure_ascii=True,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )

                original_prepare = run_autoresearch_loop.cmd_prepare_round
                prepare_calls: list[tuple[str | None, Path | None]] = []

                def prepare_side_effect(contract_path_arg: Path, *, mutation_key: str | None, mutation_path: Path | None) -> int:
                    prepare_calls.append((mutation_key, mutation_path))
                    if len(prepare_calls) == 1:
                        return original_prepare(contract_path_arg, mutation_key=mutation_key, mutation_path=mutation_path)
                    raise AutoresearchStop(kind="synthetic_stop", message="Stop gate triggered: synthetic test stop.")

                def fake_worker(*, args, contract, worker_contract_path: Path, worker_contract: dict[str, object]):
                    del args, contract, worker_contract_path
                    candidate_worktree = Path(str(worker_contract["candidate_worktree"]))
                    prompt_path = candidate_worktree / str(worker_contract["target_paths"][0])
                    prompt_path.write_text("mutated prompt\n", encoding="utf-8")
                    return SimpleNamespace(
                        backend_id="codex",
                        attempt_count=1,
                        final_attempt=1,
                        final_message=(
                            "## Scope\n- Edited target prompt.\n\n## Mutation Applied\n- Tightened wording.\n\n"
                            "## Expected Effect\n- Better routing.\n\n## Validation Notes\n- Scope only.\n"
                        ),
                    )

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
                    self.assertTrue(candidate_worktree.is_dir())
                    if "replay" in str(save_dir):
                        score = 10.0 if save_dir.name == "train" else 9.0
                    else:
                        score = 10.0 if save_dir.name == "train" else 9.0
                    return [{"suite_file": save_dir.name + ".yaml", "results": [build_eval_result(score)]}]

                with mock.patch.object(run_autoresearch_loop, "cmd_prepare_round", side_effect=prepare_side_effect), mock.patch.object(
                    run_autoresearch_loop, "execute_worker_phase", side_effect=fake_worker
                ), mock.patch.object(AutoresearchRoundManager, "_run_lane_suites", new=fake_lane_runner):
                    stdout = io.StringIO()
                    with mock.patch("sys.stdout", stdout):
                        exit_code = run_autoresearch_loop.main(
                            [
                                "--contract",
                                str(contract_path),
                                "--registry-seed",
                                str(seed_path),
                                "--mutation-key",
                                "text_rephrase:demo:first",
                            ]
                        )

                self.assertEqual(exit_code, 0)
                self.assertEqual(prepare_calls, [("text_rephrase:demo:first", None), (None, None)])
                stdout_value = stdout.getvalue()
                self.assertIn("loop_status: stopped", stdout_value)
                self.assertIn("stop_kind: synthetic_stop", stdout_value)
                self.assertIn("rounds_completed_in_loop: 1", stdout_value)
                round_dir = run_dir / "rounds" / "round-001"
                agent_report = (round_dir / "agent-report.md").read_text(encoding="utf-8")
                self.assertIn("Worker Summary", agent_report)
                self.assertIn("Edited `toolchain/scripts/research/tasks/context-routing-skill-prompt.md`.", agent_report)
                decision = json.loads((round_dir / "decision.json").read_text(encoding="utf-8"))
                self.assertEqual(decision["decision"], "keep")
                registry = json.loads((run_dir / "mutation-registry.json").read_text(encoding="utf-8"))
                self.assertEqual(registry["run_id"], contract.run_id)
                self.assertEqual(registry["contract_fingerprint"], compute_contract_fingerprint(contract))
                self.assertEqual(len(registry["entries"]), 1)
                self.assertEqual(registry["entries"][0]["attempts"], 1)
                self.assertEqual(registry["entries"][0]["last_decision"], "keep")

    def test_loop_rejects_non_p2_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract_payload = {
                "run_id": "demo-run",
                "label": "Non-P2",
                "objective": "Demo",
                "target_surface": "memory-side",
                "mutable_paths": ["product/memory-side/skills"],
                "frozen_paths": ["docs/knowledge"],
                "train_suites": ["train.yaml"],
                "validation_suites": ["validation.yaml"],
                "acceptance_suites": ["acceptance.yaml"],
                "primary_metrics": ["avg_total_score"],
                "guard_metrics": ["parse_error_rate"],
                "qualitative_veto_checks": [],
                "max_rounds": 3,
                "max_candidate_attempts_per_round": 2,
                "timeout_policy": {"seconds": 120},
                "promotion_policy": {"mode": "manual"},
            }
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract_payload), encoding="utf-8")

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                exit_code = run_autoresearch_loop.main(["--contract", str(contract_path)])

            self.assertEqual(exit_code, 1)

    def test_validate_worker_diff_detects_out_of_scope_staged_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "in-scope.txt").write_text("in\n", encoding="utf-8")
            (root / "out-of-scope.txt").write_text("out\n", encoding="utf-8")
            subprocess.run(["git", "add", "in-scope.txt", "out-of-scope.txt"], cwd=root, check=True, capture_output=True, text=True)
            subprocess.run(["git", "commit", "-q", "-m", "seed scope files"], cwd=root, check=True, capture_output=True, text=True)

            (root / "out-of-scope.txt").write_text("out changed\n", encoding="utf-8")
            subprocess.run(["git", "add", "out-of-scope.txt"], cwd=root, check=True, capture_output=True, text=True)

            worker_contract = {
                "candidate_worktree": str(root),
                "target_paths": ["in-scope.txt"],
                "guardrails": {"require_non_empty_diff": True, "max_files_touched": 1},
            }
            with self.assertRaisesRegex(RuntimeError, "out-of-scope"):
                run_autoresearch_loop._validate_worker_diff(worker_contract)

    def test_loop_recovers_prepared_round_and_continues(self) -> None:
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

            def fake_worker(*, args, contract, worker_contract_path: Path, worker_contract: dict[str, object]):
                del args, contract, worker_contract_path
                candidate_worktree = Path(str(worker_contract["candidate_worktree"]))
                prompt_path = candidate_worktree / str(worker_contract["target_paths"][0])
                prompt_path.write_text("mutated prompt from prepared\n", encoding="utf-8")
                return SimpleNamespace(
                    backend_id="codex",
                    attempt_count=1,
                    final_attempt=1,
                    final_message=(
                        "## Scope\n- Edited target prompt.\n\n## Mutation Applied\n- Prepared recovery mutation.\n\n"
                        "## Expected Effect\n- Resume loop.\n\n## Validation Notes\n- Scope only.\n"
                    ),
                )

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
                self.assertTrue(candidate_worktree.is_dir())
                score = 10.0 if save_dir.name == "train" else 9.0
                return [{"suite_file": save_dir.name + ".yaml", "results": [build_eval_result(score)]}]

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ), mock.patch.object(run_autoresearch_loop, "REPO_ROOT", root), mock.patch.object(
                run_autoresearch, "run_skill_suite_main", side_effect=fake_baseline_runner
            ):
                contract = load_contract(contract_path, repo_root=root)
                run_dir = root / ".autoworkflow" / contract.run_id
                seed_path = root / "registry-seed.json"
                seed_path.write_text(
                    json.dumps(
                        {
                            "registry_version": 1,
                            "entries": [make_registry_entry(mutation_key="text_rephrase:demo:first")],
                        },
                        ensure_ascii=True,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )

                run_autoresearch_loop._ensure_initialized(contract_path)
                run_autoresearch_loop._ensure_baseline(contract_path, run_dir)
                run_autoresearch_loop._ensure_registry_seed(contract, run_dir, seed_path)
                run_autoresearch_loop.cmd_prepare_round(
                    contract_path,
                    mutation_key="text_rephrase:demo:first",
                    mutation_path=None,
                )

                manager = run_autoresearch_loop.build_worktree_manager()
                round_path = manager.round_path(contract.run_id, 1)
                round_payload = read_json(round_path)
                round_payload["state"] = "prepared"
                round_payload["candidate_sha"] = None
                write_json(round_path, round_payload)

                def stop_on_next_prepare(*_args, **_kwargs) -> int:
                    raise AutoresearchStop(kind="synthetic_stop", message="Stop gate triggered: synthetic test stop.")

                with mock.patch.object(run_autoresearch_loop, "cmd_prepare_round", side_effect=stop_on_next_prepare), mock.patch.object(
                    run_autoresearch_loop, "execute_worker_phase", side_effect=fake_worker
                ), mock.patch.object(AutoresearchRoundManager, "_run_lane_suites", new=fake_lane_runner):
                    stdout = io.StringIO()
                    with mock.patch("sys.stdout", stdout):
                        exit_code = run_autoresearch_loop.main(
                            [
                                "--contract",
                                str(contract_path),
                                "--registry-seed",
                                str(seed_path),
                            ]
                        )

                self.assertEqual(exit_code, 0)
                stdout_value = stdout.getvalue()
                self.assertIn("loop_status: stopped", stdout_value)
                self.assertIn("stop_kind: synthetic_stop", stdout_value)
                self.assertIn("rounds_completed_in_loop: 1", stdout_value)
                decision = json.loads((run_dir / "rounds" / "round-001" / "decision.json").read_text(encoding="utf-8"))
                self.assertEqual(decision["decision"], "keep")
                final_round_payload = read_json(round_path)
                self.assertNotEqual(str(final_round_payload.get("state") or ""), "prepared")


if __name__ == "__main__":
    unittest.main()
