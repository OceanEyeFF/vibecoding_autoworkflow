from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autoresearch_contract import history_header, load_contract
from autoresearch_feedback_distill import load_feedback_ledger
from autoresearch_mutation_registry import (
    build_registry_payload,
    compute_mutation_fingerprint,
    find_registry_entry,
    materialize_round_mutation,
    load_mutation_registry,
    write_mutation_registry,
)
from autoresearch_round import AutoresearchRoundManager
from autoresearch_scoreboard import write_scoreboard
from autoresearch_worker_contract import (
    build_comparison_baseline,
    build_worker_contract_payload,
    compute_worker_contract_sha256,
    write_worker_contract,
)
from worktree_manager import WorktreeManager, champion_branch_name, read_json


def build_contract_payload(
    train_suite: str,
    validation_suite: str,
    acceptance_suite: str,
    *,
    mutable_paths: list[str] | None = None,
    target_task: str | None = None,
    target_prompt_path: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "run_id": "demo-run",
        "label": "Demo",
        "objective": "Round execution",
        "target_surface": "memory-side",
        "mutable_paths": mutable_paths or ["product/memory-side/skills"],
        "frozen_paths": ["docs/knowledge"],
        "train_suites": [train_suite],
        "validation_suites": [validation_suite],
        "acceptance_suites": [acceptance_suite],
        "primary_metrics": ["avg_total_score"],
        "guard_metrics": ["parse_error_rate", "timeout_rate"],
        "qualitative_veto_checks": [],
        "max_rounds": 3,
        "max_candidate_attempts_per_round": 1,
        "timeout_policy": {"seconds": 120},
        "promotion_policy": {"mode": "script"},
    }
    if target_task is not None:
        payload["target_task"] = target_task
    if target_prompt_path is not None:
        payload["target_prompt_path"] = target_prompt_path
    return payload


def build_mutation_payload(round_number: int = 1, mutation_id: str = "mut-001") -> dict[str, object]:
    return {
        "round": round_number,
        "mutation_id": mutation_id,
        "mutation_key": "text_rephrase:demo:intro-tighten-v1",
        "attempt": 1,
        "fingerprint": "sha256:test",
        "kind": "text_rephrase",
        "target_paths": ["product/memory-side/skills"],
        "allowed_actions": ["edit"],
        "instruction": "Tighten skill wording.",
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
    }


def build_registry_entry(
    mutation_payload: dict[str, object],
    *,
    status: str = "active",
    attempts: int = 1,
    last_selected_round: int = 1,
    last_decision: str | None = None,
) -> dict[str, object]:
    return {
        "mutation_key": mutation_payload["mutation_key"],
        "kind": mutation_payload["kind"],
        "status": status,
        "target_paths": list(mutation_payload["target_paths"]),
        "allowed_actions": list(mutation_payload["allowed_actions"]),
        "instruction_seed": mutation_payload["instruction"],
        "expected_effect": dict(mutation_payload["expected_effect"]),
        "guardrails": dict(mutation_payload["guardrails"]),
        "origin": {"type": "manual_seed", "ref": "test"},
        "attempts": attempts,
        "last_selected_round": last_selected_round,
        "last_decision": last_decision,
    }


def build_scoreboard(
    train_score: float,
    validation_score: float,
    *,
    parse_error: float = 0.0,
    pass_rate: float = 1.0,
    timeout_rate: float = 0.0,
    baseline_sha: str = "baseline-sha",
) -> dict[str, object]:
    return {
        "run_id": "demo-run",
        "generated_at": "2026-03-26T00:00:00+00:00",
        "baseline_sha": baseline_sha,
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
                "timeout_rate": timeout_rate,
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
                "timeout_rate": timeout_rate,
                "parse_error_rate": parse_error,
                "avg_total_score": validation_score,
            },
        ],
        "repo_tasks": [],
    }


def build_recent_feedback_excerpt() -> list[str]:
    return ["round=1 | mutation=text_rephrase:demo:intro-tighten-v1 | decision=discard | signal=mixed"]


class AutoresearchRoundManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.repo_root = self.root / "repo"
        self.repo_root.mkdir(parents=True, exist_ok=True)

        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "tester")
        (self.repo_root / ".gitignore").write_text(".autoworkflow/\n", encoding="utf-8")
        (self.repo_root / "README.md").write_text("initial\n", encoding="utf-8")
        (self.repo_root / "product" / "memory-side" / "skills").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "docs" / "knowledge").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "initial skill\n",
            encoding="utf-8",
        )
        (self.repo_root / "product" / "memory-side" / "skills" / "secondary.md").write_text(
            "initial secondary skill\n",
            encoding="utf-8",
        )
        (self.repo_root / "docs" / "knowledge" / "README.md").write_text("frozen\n", encoding="utf-8")
        (self.repo_root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
        (self.repo_root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
        (self.repo_root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
        self._git("add", ".")
        self._git("commit", "-q", "-m", "init")
        if subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", "refs/heads/master"],
            cwd=self.repo_root,
            check=False,
            capture_output=True,
            text=True,
        ).returncode != 0:
            self._git("branch", "master")

        self.worktree_manager = WorktreeManager(
            repo_root=self.repo_root,
            autoresearch_root=self.repo_root / ".autoworkflow" / "autoresearch",
        )
        self.round_manager = AutoresearchRoundManager(
            repo_root=self.repo_root,
            autoresearch_root=self.repo_root / ".autoworkflow" / "autoresearch",
            worktree_manager=self.worktree_manager,
        )

        contract_payload = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
        self.contract_path = self.repo_root / "contract.json"
        self.contract_path.write_text(json.dumps(contract_payload), encoding="utf-8")
        self.contract = load_contract(self.contract_path, repo_root=self.repo_root)
        self.run_dir = self.worktree_manager.run_dir(self.contract.run_id)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "contract.json").write_text(json.dumps(contract_payload), encoding="utf-8")
        (self.run_dir / "history.tsv").write_text(history_header() + "\n", encoding="utf-8")
        head_sha = self._git_output("rev-parse", "HEAD")
        write_scoreboard(self.run_dir / "scoreboard.json", build_scoreboard(9.0, 8.0, baseline_sha=head_sha))
        self.worktree_manager.initialize_runtime(self.contract.run_id)
        self.worktree_manager.refresh_champion_branch(self.contract.run_id, head_sha)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _git(self, *args: str, cwd: Path | None = None) -> None:
        subprocess.run(
            ["git", *args],
            cwd=cwd or self.repo_root,
            check=True,
            capture_output=True,
            text=True,
        )

    def _git_output(self, *args: str, cwd: Path | None = None) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=cwd or self.repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    def _prepare_active_round(self, mutation_payload: dict[str, object] | None = None) -> tuple[Path, Path]:
        mutation_payload = dict(mutation_payload or build_mutation_payload())
        self.round_manager.ensure_prepare_allowed(self.contract, mutation_payload)
        result = self.worktree_manager.prepare_round(self.contract.run_id)
        round_number = int(result["round"]["round"])
        registry_entry = build_registry_entry(mutation_payload, last_selected_round=round_number)
        registry_entry["fingerprint"] = compute_mutation_fingerprint(registry_entry)
        mutation_payload = materialize_round_mutation(
            entry=registry_entry,
            round_number=round_number,
            attempt=int(registry_entry["attempts"]),
        )
        self.round_manager.stage_mutation(self.contract.run_id, round_number, mutation_payload)
        registry_payload = build_registry_payload(contract=self.contract, entries=[registry_entry])
        write_mutation_registry(self.run_dir / "mutation-registry.json", registry_payload)
        registry = load_mutation_registry(self.run_dir / "mutation-registry.json", contract=self.contract, repo_root=self.repo_root)
        registry_entry = find_registry_entry(registry, str(registry_entry["mutation_key"]))
        comparison_baseline = build_comparison_baseline(read_json(self.run_dir / "scoreboard.json"))
        recent_feedback_excerpt = build_recent_feedback_excerpt()
        self.round_manager.stage_round_authority(
            self.contract.run_id,
            round_number,
            registry_entry=registry_entry,
            mutation_payload=mutation_payload,
            comparison_baseline=comparison_baseline,
            recent_feedback_excerpt=recent_feedback_excerpt,
        )
        # Stage a worker contract envelope, as run-round now requires it.
        round_payload = read_json(self.worktree_manager.round_path(self.contract.run_id, round_number))
        worker_payload = build_worker_contract_payload(
            contract=self.contract,
            mutation_payload=mutation_payload,
            round_payload=round_payload,
            agent_report_path=self.round_manager.agent_report_path(self.contract.run_id, round_number),
            comparison_baseline=comparison_baseline,
            recent_feedback_excerpt=recent_feedback_excerpt,
            materialized_at="2026-03-27T00:00:00+00:00",
        )
        worker_path = self.round_manager.worker_contract_path(self.contract.run_id, round_number)
        write_worker_contract(worker_path, worker_payload)
        round_payload["worker_contract_materialized_at"] = worker_payload["materialized_at"]
        round_payload["worker_contract_sha256"] = compute_worker_contract_sha256(worker_path)
        (self.worktree_manager.round_path(self.contract.run_id, round_number)).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        agent_report = self.round_manager.agent_report_path(self.contract.run_id, round_number)
        agent_report.write_text("# Agent Report\n\nApplied mutation.\n", encoding="utf-8")
        candidate_worktree = Path(str(result["worktree"]["path"]))
        return candidate_worktree, agent_report

    def test_run_round_writes_round_scoreboard_and_captures_candidate_sha(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate change\n",
            encoding="utf-8",
        )

        def fake_lane_runner(*, candidate_worktree: Path, suite_files: list[Path], save_dir: Path) -> list[dict[str, object]]:
            if "train" in str(save_dir):
                return [{"suite_file": "train.yaml", "results": [self._eval_result(10.0)]}]
            return [{"suite_file": "validation.yaml", "results": [self._eval_result(8.5)]}]

        self.round_manager._run_lane_suites = fake_lane_runner  # type: ignore[method-assign]
        result = self.round_manager.run_round(self.contract)

        round_payload = read_json(self.worktree_manager.round_path(self.contract.run_id, 1))
        scoreboard = read_json(self.round_manager.round_scoreboard_path(self.contract.run_id, 1))

        self.assertEqual(result["round"]["state"], "evaluated")
        self.assertEqual(round_payload["state"], "evaluated")
        self.assertNotEqual(round_payload["candidate_sha"], round_payload["base_sha"])
        self.assertEqual(scoreboard["lanes"][0]["avg_total_score"], 10.0)
        self.assertEqual(scoreboard["lanes"][1]["avg_total_score"], 8.5)

    def test_run_round_uses_frozen_worker_contract_comparison_baseline(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate change\n",
            encoding="utf-8",
        )
        tampered_scoreboard = build_scoreboard(99.0, 99.0, baseline_sha=self._git_output("rev-parse", "HEAD"))
        write_scoreboard(self.run_dir / "scoreboard.json", tampered_scoreboard)

        def fake_lane_runner(*, candidate_worktree: Path, suite_files: list[Path], save_dir: Path) -> list[dict[str, object]]:
            if "train" in str(save_dir):
                return [{"suite_file": "train.yaml", "results": [self._eval_result(10.0)]}]
            return [{"suite_file": "validation.yaml", "results": [self._eval_result(8.5)]}]

        self.round_manager._run_lane_suites = fake_lane_runner  # type: ignore[method-assign]
        result = self.round_manager.run_round(self.contract)

        self.assertEqual(result["round"]["state"], "evaluated")

    def test_run_round_accepts_legacy_worker_contract_without_round_hashes(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "legacy candidate change\n",
            encoding="utf-8",
        )

        round_path = self.worktree_manager.round_path(self.contract.run_id, 1)
        round_payload = read_json(round_path)
        mutation_path = self.round_manager.mutation_path(self.contract.run_id, 1)
        mutation_payload = read_json(mutation_path)
        worker_path = self.round_manager.worker_contract_path(self.contract.run_id, 1)
        legacy_worker_payload = {
            "worker_contract_version": 1,
            "run_id": self.contract.run_id,
            "round": round_payload["round"],
            "mutation_id": mutation_payload["mutation_id"],
            "mutation_key": mutation_payload["mutation_key"],
            "attempt": mutation_payload["attempt"],
            "fingerprint": mutation_payload["fingerprint"],
            "kind": mutation_payload["kind"],
            "instruction": mutation_payload["instruction"],
            "target_paths": list(mutation_payload["target_paths"]),
            "allowed_actions": list(mutation_payload["allowed_actions"]),
            "guardrails": dict(mutation_payload["guardrails"]),
            "expected_effect": dict(mutation_payload["expected_effect"]),
            "base_sha": round_payload["base_sha"],
            "candidate_branch": round_payload["candidate_branch"],
            "candidate_worktree": round_payload["candidate_worktree"],
            "agent_report_path": str(self.round_manager.agent_report_path(self.contract.run_id, 1)),
            "mutation_path": str(mutation_path),
            "contract_path": str(self.run_dir / "contract.json"),
            "mutation_sha256": round_payload["mutation_sha256"],
            "previous_feedback_excerpt": None,
            "authority_note": (
                "worker-contract.json is an agent-facing envelope only. "
                "Authority remains: contract.json + mutation-registry.json + mutation.json hash + git diff validation."
            ),
        }
        worker_path.write_text(json.dumps(legacy_worker_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        round_payload.pop("worker_contract_materialized_at", None)
        round_payload.pop("worker_contract_sha256", None)
        round_path.write_text(json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

        def fake_lane_runner(*, candidate_worktree: Path, suite_files: list[Path], save_dir: Path) -> list[dict[str, object]]:
            if "train" in str(save_dir):
                return [{"suite_file": "train.yaml", "results": [self._eval_result(10.0)]}]
            return [{"suite_file": "validation.yaml", "results": [self._eval_result(8.5)]}]

        self.round_manager._run_lane_suites = fake_lane_runner  # type: ignore[method-assign]
        result = self.round_manager.run_round(self.contract)

        refreshed_round = read_json(round_path)
        scoreboard = read_json(self.round_manager.round_scoreboard_path(self.contract.run_id, 1))
        self.assertEqual(result["round"]["state"], "evaluated")
        self.assertEqual(refreshed_round["state"], "evaluated")
        self.assertEqual(scoreboard["lanes"][0]["avg_total_score"], 10.0)
        self.assertEqual(scoreboard["lanes"][1]["avg_total_score"], 8.5)

    def test_prepare_round_requires_baseline_scoreboard(self) -> None:
        (self.run_dir / "scoreboard.json").unlink()
        with self.assertRaisesRegex(FileNotFoundError, "Baseline scoreboard missing"):
            self.round_manager.ensure_prepare_allowed(self.contract, build_mutation_payload())

    def test_prepare_round_rejects_target_path_outside_mutable_paths(self) -> None:
        mutation_payload = build_mutation_payload()
        mutation_payload["target_paths"] = ["docs/knowledge"]
        with self.assertRaisesRegex(ValueError, "Mutation target_paths must stay within contract.mutable_paths"):
            self.round_manager.ensure_prepare_allowed(self.contract, mutation_payload)

    def test_prepare_round_rejects_parent_target_path_that_widens_mutable_scope(self) -> None:
        mutation_payload = build_mutation_payload()
        mutation_payload["target_paths"] = ["product/memory-side"]
        with self.assertRaisesRegex(ValueError, "Mutation target_paths must stay within contract.mutable_paths"):
            self.round_manager.ensure_prepare_allowed(self.contract, mutation_payload)

    def test_prepare_round_rejects_p2_target_paths_not_equal_to_target_prompt_path(self) -> None:
        contract_payload = build_contract_payload(
            "train.yaml",
            "validation.yaml",
            "acceptance.yaml",
            mutable_paths=["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
            target_task="context-routing-skill",
            target_prompt_path="toolchain/scripts/research/tasks/context-routing-skill-prompt.md",
        )
        self.contract_path.write_text(json.dumps(contract_payload), encoding="utf-8")
        self.contract = load_contract(self.contract_path, repo_root=self.repo_root)
        (self.run_dir / "contract.json").write_text(json.dumps(contract_payload), encoding="utf-8")

        mutation_payload = build_mutation_payload()
        mutation_payload["target_paths"] = ["toolchain/scripts/research/tasks/knowledge-base-skill-prompt.md"]

        with self.assertRaisesRegex(ValueError, "exactly \\[contract.target_prompt_path\\]"):
            self.round_manager.ensure_prepare_allowed(self.contract, mutation_payload)

    def test_run_round_requires_agent_report(self) -> None:
        mutation_payload = build_mutation_payload()
        self.round_manager.ensure_prepare_allowed(self.contract, mutation_payload)
        self.worktree_manager.prepare_round(self.contract.run_id)
        registry_entry = build_registry_entry(mutation_payload, last_selected_round=1)
        registry_entry["fingerprint"] = compute_mutation_fingerprint(registry_entry)
        mutation_payload = materialize_round_mutation(entry=registry_entry, round_number=1, attempt=1)
        self.round_manager.stage_mutation(self.contract.run_id, 1, mutation_payload)
        registry_payload = build_registry_payload(contract=self.contract, entries=[registry_entry])
        write_mutation_registry(self.run_dir / "mutation-registry.json", registry_payload)
        registry = load_mutation_registry(self.run_dir / "mutation-registry.json", contract=self.contract, repo_root=self.repo_root)
        registry_entry = find_registry_entry(registry, str(registry_entry["mutation_key"]))
        comparison_baseline = build_comparison_baseline(read_json(self.run_dir / "scoreboard.json"))
        self.round_manager.stage_round_authority(
            self.contract.run_id,
            1,
            registry_entry=registry_entry,
            mutation_payload=mutation_payload,
            comparison_baseline=comparison_baseline,
            recent_feedback_excerpt=[],
        )
        # Stage worker contract but intentionally omit agent-report.md to exercise that failure path.
        round_payload = read_json(self.worktree_manager.round_path(self.contract.run_id, 1))
        worker_payload = build_worker_contract_payload(
            contract=self.contract,
            mutation_payload=mutation_payload,
            round_payload=round_payload,
            agent_report_path=self.round_manager.agent_report_path(self.contract.run_id, 1),
            comparison_baseline=comparison_baseline,
            recent_feedback_excerpt=[],
            materialized_at="2026-03-27T00:00:00+00:00",
        )
        worker_path = self.round_manager.worker_contract_path(self.contract.run_id, 1)
        write_worker_contract(worker_path, worker_payload)
        round_payload["worker_contract_materialized_at"] = worker_payload["materialized_at"]
        round_payload["worker_contract_sha256"] = compute_worker_contract_sha256(worker_path)
        (self.worktree_manager.round_path(self.contract.run_id, 1)).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(FileNotFoundError, "Missing agent report"):
            self.round_manager.run_round(self.contract)

    def test_run_round_rejects_change_outside_mutation_targets(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "README.md").write_text("escaped\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "escapes mutation target_paths"):
            self.round_manager.run_round(self.contract)

    def test_run_round_rejects_committed_change_outside_mutation_targets(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "README.md").write_text("escaped committed change\n", encoding="utf-8")
        self._git("add", "README.md", cwd=candidate_worktree)
        self._git("commit", "-q", "-m", "escaped committed change", cwd=candidate_worktree)
        candidate_sha = self._git_output("rev-parse", "HEAD", cwd=candidate_worktree)
        round_payload = read_json(self.worktree_manager.round_path(self.contract.run_id, 1))
        round_payload["candidate_sha"] = candidate_sha
        (self.worktree_manager.round_path(self.contract.run_id, 1)).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        worktree_payload = read_json(self.worktree_manager.worktree_path_record(self.contract.run_id, 1))
        worktree_payload["candidate_sha"] = candidate_sha
        (self.worktree_manager.worktree_path_record(self.contract.run_id, 1)).write_text(
            json.dumps(worktree_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(RuntimeError, "escapes mutation target_paths"):
            self.round_manager.run_round(self.contract)

    def test_run_round_rejects_disallowed_create_action(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "new-skill.md").write_text(
            "new file\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(RuntimeError, "action is not allowed: create"):
            self.round_manager.run_round(self.contract)

    def test_run_round_rejects_tampered_round_identity_even_with_hashes(self) -> None:
        _candidate_worktree, _ = self._prepare_active_round()
        round_dir = self.worktree_manager.round_dir(self.contract.run_id, 1)
        round_payload = read_json(self.worktree_manager.round_path(self.contract.run_id, 1))
        worktree_payload = read_json(self.worktree_manager.worktree_path_record(self.contract.run_id, 1))
        round_payload["base_sha"] = "sha256:tampered"
        (self.worktree_manager.round_path(self.contract.run_id, 1)).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        worktree_payload["path"] = str(self.root / "malicious" / "round-001")
        (self.worktree_manager.worktree_path_record(self.contract.run_id, 1)).write_text(
            json.dumps(worktree_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(RuntimeError, "deterministic (git authority|candidate identity)"):
            self.round_manager.run_round(self.contract)

    def test_run_round_requires_worker_contract(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate change\n",
            encoding="utf-8",
        )
        (self.round_manager.worker_contract_path(self.contract.run_id, 1)).unlink()
        with self.assertRaisesRegex(FileNotFoundError, "Missing worker contract"):
            self.round_manager.run_round(self.contract)

    def test_run_round_rejects_tampered_worker_contract(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate change\n",
            encoding="utf-8",
        )
        worker_path = self.round_manager.worker_contract_path(self.contract.run_id, 1)
        payload = json.loads(worker_path.read_text(encoding="utf-8"))
        payload["instruction"] = "tampered"
        worker_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "hash recorded in round.json"):
            self.round_manager.run_round(self.contract)

    def test_run_round_rejects_value_preserving_worker_contract_rewrite(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate change\n",
            encoding="utf-8",
        )
        worker_path = self.round_manager.worker_contract_path(self.contract.run_id, 1)
        worker_payload = json.loads(worker_path.read_text(encoding="utf-8"))
        worker_path.write_text(json.dumps(worker_payload, ensure_ascii=True) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "hash recorded in round.json"):
            self.round_manager.run_round(self.contract)

    def test_run_round_rejects_tampered_frozen_round_authority(self) -> None:
        mutation_payload = build_mutation_payload()
        mutation_payload["target_paths"] = ["product/memory-side/skills/skill.md"]
        candidate_worktree, _ = self._prepare_active_round(mutation_payload)
        (candidate_worktree / "product" / "memory-side" / "skills" / "secondary.md").write_text(
            "candidate change\n",
            encoding="utf-8",
        )
        self.assertTrue(
            self.worktree_manager.ref_exists(
                self.worktree_manager.round_authority_ref(self.contract.run_id, 1)
            )
        )

        registry_path = self.run_dir / "mutation-registry.json"
        registry = load_mutation_registry(registry_path, contract=self.contract, repo_root=self.repo_root)
        registry_payload = dict(registry.payload)
        registry_entry = registry_payload["entries"][0]
        registry_entry["target_paths"] = ["product/memory-side/skills"]
        registry_entry["fingerprint_basis"]["target_paths"] = ["product/memory-side/skills"]
        registry_entry["fingerprint"] = compute_mutation_fingerprint(registry_entry)
        write_mutation_registry(registry_path, registry_payload)

        mutation_path = self.round_manager.mutation_path(self.contract.run_id, 1)
        tampered_mutation = read_json(mutation_path)
        tampered_mutation["target_paths"] = ["product/memory-side/skills"]
        tampered_mutation["fingerprint"] = registry_entry["fingerprint"]
        mutation_path.write_text(json.dumps(tampered_mutation, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

        round_payload = read_json(self.worktree_manager.round_path(self.contract.run_id, 1))
        round_payload["mutation_sha256"] = f"sha256:{hashlib.sha256(mutation_path.read_bytes()).hexdigest()}"
        self.worktree_manager.round_path(self.contract.run_id, 1).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

        worker_payload = build_worker_contract_payload(
            contract=self.contract,
            mutation_payload=tampered_mutation,
            round_payload=round_payload,
            agent_report_path=self.round_manager.agent_report_path(self.contract.run_id, 1),
            comparison_baseline=build_comparison_baseline(read_json(self.run_dir / "scoreboard.json")),
            recent_feedback_excerpt=[],
            materialized_at="2026-03-27T00:00:00+00:00",
        )
        worker_path = self.round_manager.worker_contract_path(self.contract.run_id, 1)
        write_worker_contract(worker_path, worker_payload)
        round_payload["worker_contract_materialized_at"] = worker_payload["materialized_at"]
        round_payload["worker_contract_sha256"] = compute_worker_contract_sha256(worker_path)
        self.worktree_manager.round_path(self.contract.run_id, 1).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(RuntimeError, "frozen round authority snapshot"):
            self.round_manager.run_round(self.contract)

    def test_run_round_rejects_value_preserving_mutation_rewrite(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate change\n",
            encoding="utf-8",
        )
        mutation_path = self.round_manager.mutation_path(self.contract.run_id, 1)
        mutation_payload = json.loads(mutation_path.read_text(encoding="utf-8"))
        mutation_path.write_text(json.dumps(mutation_payload, ensure_ascii=True) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "mutation.json does not match hash recorded in round.json"):
            self.round_manager.run_round(self.contract)

    def test_run_round_rejects_empty_diff_when_required(self) -> None:
        self._prepare_active_round()

        with self.assertRaisesRegex(RuntimeError, "Candidate diff must be non-empty"):
            self.round_manager.run_round(self.contract)

    def test_run_round_rejects_too_many_touched_files_guardrail(self) -> None:
        mutation_payload = build_mutation_payload()
        mutation_payload["guardrails"] = {
            "require_non_empty_diff": True,
            "max_files_touched": 1,
            "extra_frozen_paths": [],
        }
        candidate_worktree, _ = self._prepare_active_round(mutation_payload)
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate change one\n",
            encoding="utf-8",
        )
        (candidate_worktree / "product" / "memory-side" / "skills" / "secondary.md").write_text(
            "candidate change two\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(RuntimeError, "too many files"):
            self.round_manager.run_round(self.contract)

    def test_run_round_rejects_extra_frozen_guardrail_path(self) -> None:
        mutation_payload = build_mutation_payload()
        mutation_payload["guardrails"] = {
            "require_non_empty_diff": True,
            "max_files_touched": 2,
            "extra_frozen_paths": ["product/memory-side/skills/skill.md"],
        }
        candidate_worktree, _ = self._prepare_active_round(mutation_payload)
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate frozen path change\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(RuntimeError, "frozen guardrail path"):
            self.round_manager.run_round(self.contract)

    def test_decide_round_keeps_candidate_and_updates_history(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate keep\n",
            encoding="utf-8",
        )
        capture = self.worktree_manager.capture_candidate_commit(
            self.contract.run_id,
            message="candidate keep",
        )
        round_payload = capture["round"]
        round_payload["state"] = "evaluated"
        (self.worktree_manager.round_path(self.contract.run_id, 1)).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        write_scoreboard(self.round_manager.round_scoreboard_path(self.contract.run_id, 1), build_scoreboard(10.0, 8.0))

        result = self.round_manager.decide_round(self.contract)

        runtime = read_json(self.worktree_manager.runtime_path(self.contract.run_id))
        baseline_scoreboard = read_json(self.run_dir / "scoreboard.json")
        feedback_distill = read_json(self.round_manager.feedback_distill_path(self.contract.run_id, 1))
        feedback_ledger = load_feedback_ledger(self.round_manager.feedback_ledger_path(self.contract.run_id))
        history_lines = (self.run_dir / "history.tsv").read_text(encoding="utf-8").strip().splitlines()

        self.assertEqual(result["decision"]["decision"], "keep")
        self.assertIsInstance(result["decision"]["expected_effect"], dict)
        self.assertIsNone(runtime["active_round"])
        self.assertEqual(self._git_output("rev-parse", champion_branch_name(self.contract.run_id)), result["decision"]["candidate_sha"])
        self.assertEqual(baseline_scoreboard["baseline_sha"], result["decision"]["candidate_sha"])
        self.assertEqual(baseline_scoreboard["lanes"][0]["avg_total_score"], 10.0)
        self.assertEqual(baseline_scoreboard["lanes"][1]["avg_total_score"], 8.0)
        self.assertEqual(baseline_scoreboard["rounds_completed"], 1)
        self.assertEqual(baseline_scoreboard["best_round"], 1)
        self.assertEqual(feedback_distill["decision"], "keep")
        self.assertEqual(feedback_distill["signal_strength"], "positive")
        self.assertEqual(len(feedback_ledger), 1)
        self.assertEqual(feedback_ledger[0]["mutation_id"], result["decision"]["mutation_id"])
        self.assertEqual(len(history_lines), 2)
        self.assertIn("\tkeep\t", history_lines[1])
        registry_after = read_json(self.run_dir / "mutation-registry.json")
        self.assertEqual(registry_after["entries"][0]["last_decision"], "keep")
        self.assertEqual(registry_after["entries"][0]["status"], "exhausted")

    def test_decide_round_rejects_moved_candidate_branch_after_evaluation(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate keep\n",
            encoding="utf-8",
        )
        capture = self.worktree_manager.capture_candidate_commit(
            self.contract.run_id,
            message="candidate keep",
        )
        round_payload = capture["round"]
        round_payload["state"] = "evaluated"
        (self.worktree_manager.round_path(self.contract.run_id, 1)).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        write_scoreboard(self.round_manager.round_scoreboard_path(self.contract.run_id, 1), build_scoreboard(10.0, 8.0))

        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate retarget\n",
            encoding="utf-8",
        )
        self._git("add", "product/memory-side/skills/skill.md", cwd=candidate_worktree)
        self._git("commit", "-q", "-m", "retarget candidate", cwd=candidate_worktree)

        with self.assertRaisesRegex(RuntimeError, "pinned round candidate_sha"):
            self.round_manager.decide_round(self.contract)

    def test_decide_round_ignores_tampered_runtime_champion_branch(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate retarget guard\n",
            encoding="utf-8",
        )
        capture = self.worktree_manager.capture_candidate_commit(
            self.contract.run_id,
            message="candidate retarget guard",
        )
        round_payload = capture["round"]
        round_payload["state"] = "evaluated"
        (self.worktree_manager.round_path(self.contract.run_id, 1)).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        write_scoreboard(self.round_manager.round_scoreboard_path(self.contract.run_id, 1), build_scoreboard(10.0, 8.0))

        runtime_path = self.worktree_manager.runtime_path(self.contract.run_id)
        runtime_payload = read_json(runtime_path)
        master_before = self._git_output("rev-parse", "master")
        champion_before = self._git_output("rev-parse", champion_branch_name(self.contract.run_id))
        runtime_payload["champion_branch"] = "master"
        runtime_payload["champion_sha"] = master_before
        runtime_path.write_text(json.dumps(runtime_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

        result = self.round_manager.decide_round(self.contract)

        self.assertEqual(self._git_output("rev-parse", "master"), master_before)
        self.assertEqual(
            self._git_output("rev-parse", champion_branch_name(self.contract.run_id)),
            result["decision"]["candidate_sha"],
        )
        self.assertNotEqual(self._git_output("rev-parse", champion_branch_name(self.contract.run_id)), champion_before)

    def test_decide_round_discards_validation_regression(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate discard\n",
            encoding="utf-8",
        )
        capture = self.worktree_manager.capture_candidate_commit(
            self.contract.run_id,
            message="candidate discard",
        )
        round_payload = capture["round"]
        round_payload["state"] = "evaluated"
        (self.worktree_manager.round_path(self.contract.run_id, 1)).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        write_scoreboard(self.round_manager.round_scoreboard_path(self.contract.run_id, 1), build_scoreboard(10.0, 7.0))

        result = self.round_manager.decide_round(self.contract)

        runtime = read_json(self.worktree_manager.runtime_path(self.contract.run_id))
        baseline_scoreboard = read_json(self.run_dir / "scoreboard.json")
        feedback_distill = read_json(self.round_manager.feedback_distill_path(self.contract.run_id, 1))
        history_lines = (self.run_dir / "history.tsv").read_text(encoding="utf-8").strip().splitlines()

        self.assertEqual(result["decision"]["decision"], "discard")
        self.assertIsNone(runtime["active_round"])
        self.assertEqual(baseline_scoreboard["rounds_completed"], 1)
        self.assertEqual(baseline_scoreboard["best_round"], 0)
        self.assertEqual(feedback_distill["signal_strength"], "mixed")
        self.assertIn("validation_drop", feedback_distill["regression_flags"])
        self.assertEqual(len(history_lines), 2)
        self.assertIn("\tdiscard\t", history_lines[1])
        registry_after = read_json(self.run_dir / "mutation-registry.json")
        self.assertEqual(registry_after["entries"][0]["last_decision"], "discard")
        self.assertEqual(registry_after["entries"][0]["status"], "exhausted")

    def test_decide_round_replays_only_when_replay_keeps_round_validation_stable(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate keep with replay\n",
            encoding="utf-8",
        )
        capture = self.worktree_manager.capture_candidate_commit(
            self.contract.run_id,
            message="candidate keep with replay",
        )
        round_payload = capture["round"]
        round_payload["state"] = "evaluated"
        (self.worktree_manager.round_path(self.contract.run_id, 1)).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        write_scoreboard(self.round_manager.round_scoreboard_path(self.contract.run_id, 1), build_scoreboard(10.0, 9.0))
        replay_root = self.round_manager.replay_dir(self.contract.run_id, 1)
        (replay_root / "train").mkdir(parents=True, exist_ok=True)
        (replay_root / "train" / "stale.txt").write_text("stale\n", encoding="utf-8")
        (replay_root / "validation").mkdir(parents=True, exist_ok=True)
        (replay_root / "validation" / "stale.txt").write_text("stale\n", encoding="utf-8")

        lane_results = [
            [{"suite_file": "train.yaml", "results": [self._eval_result(10.5)]}],
            [{"suite_file": "validation.yaml", "results": [self._eval_result(9.1)]}],
        ]

        def fake_replay_runner(*, candidate_worktree: Path, suite_files: list[Path], save_dir: Path) -> list[dict[str, object]]:
            self.assertIn("/replay/", save_dir.as_posix())
            self.assertFalse((save_dir / "stale.txt").exists())
            return lane_results.pop(0)

        self.round_manager._run_lane_suites = fake_replay_runner  # type: ignore[method-assign]

        result = self.round_manager.decide_round(self.contract)

        baseline_scoreboard = read_json(self.run_dir / "scoreboard.json")
        replay_scoreboard = read_json(self.round_manager.replay_scoreboard_path(self.contract.run_id, 1))
        self.assertEqual(result["decision"]["decision"], "keep")
        self.assertEqual(result["decision"]["provisional_decision"], "keep")
        self.assertEqual(result["decision"]["replay"]["status"], "passed")
        self.assertEqual(replay_scoreboard["lanes"][1]["avg_total_score"], 9.1)
        self.assertEqual(baseline_scoreboard["baseline_sha"], result["decision"]["candidate_sha"])

    def test_decide_round_replay_failure_discards_candidate_without_promotion(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        original_champion_sha = self._git_output("rev-parse", champion_branch_name(self.contract.run_id))
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate replay failure\n",
            encoding="utf-8",
        )
        capture = self.worktree_manager.capture_candidate_commit(
            self.contract.run_id,
            message="candidate replay failure",
        )
        round_payload = capture["round"]
        round_payload["state"] = "evaluated"
        (self.worktree_manager.round_path(self.contract.run_id, 1)).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        write_scoreboard(self.round_manager.round_scoreboard_path(self.contract.run_id, 1), build_scoreboard(10.0, 9.0))
        replay_root = self.round_manager.replay_dir(self.contract.run_id, 1)
        (replay_root / "train").mkdir(parents=True, exist_ok=True)
        (replay_root / "train" / "stale.txt").write_text("stale\n", encoding="utf-8")
        (replay_root / "validation").mkdir(parents=True, exist_ok=True)
        (replay_root / "validation" / "stale.txt").write_text("stale\n", encoding="utf-8")

        lane_results = [
            [{"suite_file": "train.yaml", "results": [self._eval_result(10.5)]}],
            [{"suite_file": "validation.yaml", "results": [self._eval_result(7.5)]}],
        ]

        def fake_replay_runner(*, candidate_worktree: Path, suite_files: list[Path], save_dir: Path) -> list[dict[str, object]]:
            self.assertIn("/replay/", save_dir.as_posix())
            self.assertFalse((save_dir / "stale.txt").exists())
            return lane_results.pop(0)

        self.round_manager._run_lane_suites = fake_replay_runner  # type: ignore[method-assign]

        result = self.round_manager.decide_round(self.contract)

        baseline_scoreboard = read_json(self.run_dir / "scoreboard.json")
        feedback_distill = read_json(self.round_manager.feedback_distill_path(self.contract.run_id, 1))
        self.assertEqual(result["decision"]["provisional_decision"], "keep")
        self.assertEqual(result["decision"]["decision"], "discard")
        self.assertEqual(result["decision"]["replay"]["status"], "failed")
        self.assertEqual(result["decision"]["replay"]["reason"], "replay_validation_regression")
        self.assertEqual(self._git_output("rev-parse", champion_branch_name(self.contract.run_id)), original_champion_sha)
        self.assertEqual(baseline_scoreboard["baseline_sha"], original_champion_sha)
        self.assertEqual(feedback_distill["decision"], "discard")

    def test_decide_round_replay_failure_triggers_on_round_validation_drop_even_if_above_champion(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate replay threshold\n",
            encoding="utf-8",
        )
        capture = self.worktree_manager.capture_candidate_commit(
            self.contract.run_id,
            message="candidate replay threshold",
        )
        round_payload = capture["round"]
        round_payload["state"] = "evaluated"
        (self.worktree_manager.round_path(self.contract.run_id, 1)).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        write_scoreboard(self.round_manager.round_scoreboard_path(self.contract.run_id, 1), build_scoreboard(10.0, 9.0))

        lane_results = [
            [{"suite_file": "train.yaml", "results": [self._eval_result(10.2)]}],
            [{"suite_file": "validation.yaml", "results": [self._eval_result(8.5)]}],
        ]

        def fake_replay_runner(*, candidate_worktree: Path, suite_files: list[Path], save_dir: Path) -> list[dict[str, object]]:
            return lane_results.pop(0)

        self.round_manager._run_lane_suites = fake_replay_runner  # type: ignore[method-assign]

        result = self.round_manager.decide_round(self.contract)

        self.assertEqual(result["decision"]["provisional_decision"], "keep")
        self.assertEqual(result["decision"]["decision"], "discard")
        self.assertEqual(result["decision"]["replay"]["status"], "failed")
        self.assertEqual(result["decision"]["replay"]["reason"], "replay_validation_regression")
        self.assertEqual(result["decision"]["replay"]["round_validation_score"], 9.0)
        self.assertEqual(result["decision"]["replay"]["replay_validation_score"], 8.5)

    def test_decide_round_replay_output_surfaces_provisional_and_replay_fields(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate replay final check\n",
            encoding="utf-8",
        )
        capture = self.worktree_manager.capture_candidate_commit(
            self.contract.run_id,
            message="candidate replay final",
        )
        round_payload = capture["round"]
        round_payload["state"] = "evaluated"
        (self.worktree_manager.round_path(self.contract.run_id, 1)).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        write_scoreboard(self.round_manager.round_scoreboard_path(self.contract.run_id, 1), build_scoreboard(10.0, 9.5))
        replay_root = self.round_manager.replay_dir(self.contract.run_id, 1)
        (replay_root / "train").mkdir(parents=True, exist_ok=True)
        (replay_root / "validation").mkdir(parents=True, exist_ok=True)

        lane_results = [
            [{"suite_file": "train.yaml", "results": [self._eval_result(10.5)]}],
            [{"suite_file": "validation.yaml", "results": [self._eval_result(9.5)]}],
        ]

        def fake_replay_runner(*, candidate_worktree: Path, suite_files: list[Path], save_dir: Path) -> list[dict[str, object]]:
            self.assertIn("/replay/", save_dir.as_posix())
            return lane_results.pop(0)

        self.round_manager._run_lane_suites = fake_replay_runner  # type: ignore[method-assign]

        result = self.round_manager.decide_round(self.contract)

        decision = result["decision"]
        replay = decision["replay"]
        replay_scoreboard = read_json(self.round_manager.replay_scoreboard_path(self.contract.run_id, 1))

        self.assertEqual(decision["decision"], "keep")
        self.assertEqual(decision["provisional_decision"], "keep")
        self.assertEqual(replay["status"], "passed")
        self.assertEqual(replay["reason"], "replay_validation_non_regression")
        self.assertEqual(replay["scoreboard_ref"], "replay/scoreboard.json")
        self.assertEqual(replay["round_validation_score"], 9.5)
        self.assertEqual(replay["replay_validation_score"], 9.5)
        self.assertGreaterEqual(replay_scoreboard["lanes"][1]["avg_total_score"], 9.5)
    def test_decide_round_replay_needed_enforces_p2_preflight_before_replay(self) -> None:
        prompt_path = "toolchain/scripts/research/tasks/context-routing-skill-prompt.md"
        (self.repo_root / prompt_path).parent.mkdir(parents=True, exist_ok=True)
        (self.repo_root / prompt_path).write_text("prompt\n", encoding="utf-8")
        self._git("add", prompt_path)
        self._git("commit", "-q", "-m", "add p2 prompt")
        head_sha = self._git_output("rev-parse", "HEAD")
        runtime = self.worktree_manager.load_runtime(self.contract.run_id)
        runtime["champion_sha"] = head_sha
        self.worktree_manager.save_runtime(self.contract.run_id, runtime)
        self.worktree_manager.refresh_champion_branch(self.contract.run_id, head_sha)
        contract_payload = build_contract_payload(
            "train.yaml",
            "validation.yaml",
            "acceptance.yaml",
            mutable_paths=[prompt_path],
            target_task="context-routing-skill",
            target_prompt_path=prompt_path,
        )
        self.contract_path.write_text(json.dumps(contract_payload), encoding="utf-8")
        self.contract = load_contract(self.contract_path, repo_root=self.repo_root)
        (self.run_dir / "contract.json").write_text(json.dumps(contract_payload), encoding="utf-8")
        write_scoreboard(
            self.run_dir / "scoreboard.json",
            build_scoreboard(9.0, 8.0, baseline_sha=head_sha),
        )

        def write_codex_suite(path: Path) -> None:
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

        write_codex_suite(self.repo_root / "train.yaml")
        write_codex_suite(self.repo_root / "validation.yaml")
        write_codex_suite(self.repo_root / "acceptance.yaml")

        mutation_payload = build_mutation_payload()
        mutation_payload["target_paths"] = [prompt_path]
        candidate_worktree, _ = self._prepare_active_round(mutation_payload)
        (candidate_worktree / prompt_path).parent.mkdir(parents=True, exist_ok=True)
        (candidate_worktree / prompt_path).write_text("candidate change\n", encoding="utf-8")

        replay_attempts: list[str] = []

        def fake_replay_runner(*, candidate_worktree: Path, suite_files: list[Path], save_dir: Path) -> list[dict[str, object]]:
            replay_attempts.append(save_dir.as_posix())
            if len(replay_attempts) > 2:
                raise AssertionError("replay should not run when P2 preflight fails")
            if "train" in str(save_dir):
                return [{"suite_file": "train.yaml", "results": [self._eval_result(10.0)]}]
            return [{"suite_file": "validation.yaml", "results": [self._eval_result(9.5)]}]

        self.round_manager._run_lane_suites = fake_replay_runner  # type: ignore[method-assign]
        self.round_manager.run_round(self.contract)

        (self.repo_root / "train.yaml").write_text(
            "version: 1\n"
            "defaults:\n"
            "  backend: claude\n"
            "  judge_backend: claude\n"
            "  with_eval: true\n"
            "runs:\n"
            "  - repo: .\n"
            "    task: context-routing\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "P2 suite must enforce codex -> codex"):
            self.round_manager.decide_round(self.contract)

        self.assertEqual(len(replay_attempts), 2)

    def test_decide_round_compares_against_current_champion_scoreboard(self) -> None:
        first_candidate, _ = self._prepare_active_round()
        (first_candidate / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate keep round one\n",
            encoding="utf-8",
        )
        capture = self.worktree_manager.capture_candidate_commit(
            self.contract.run_id,
            message="candidate keep round one",
        )
        first_round = capture["round"]
        first_round["state"] = "evaluated"
        (self.worktree_manager.round_path(self.contract.run_id, 1)).write_text(
            json.dumps(first_round, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        write_scoreboard(self.round_manager.round_scoreboard_path(self.contract.run_id, 1), build_scoreboard(10.0, 8.0))

        first_result = self.round_manager.decide_round(self.contract)
        first_champion_sha = str(first_result["decision"]["candidate_sha"])

        second_mutation = build_mutation_payload(round_number=2, mutation_id="mut-002")
        self.round_manager.ensure_prepare_allowed(self.contract, second_mutation)
        second_prepare = self.worktree_manager.prepare_round(self.contract.run_id)
        second_registry_entry = build_registry_entry(second_mutation, last_selected_round=2)
        second_registry_entry["fingerprint"] = compute_mutation_fingerprint(second_registry_entry)
        second_mutation = materialize_round_mutation(entry=second_registry_entry, round_number=2, attempt=1)
        self.round_manager.stage_mutation(self.contract.run_id, 2, second_mutation)
        second_registry_payload = build_registry_payload(contract=self.contract, entries=[second_registry_entry])
        write_mutation_registry(self.run_dir / "mutation-registry.json", second_registry_payload)
        second_registry = load_mutation_registry(
            self.run_dir / "mutation-registry.json", contract=self.contract, repo_root=self.repo_root
        )
        second_registry_entry = find_registry_entry(second_registry, str(second_registry_entry["mutation_key"]))
        self.round_manager.stage_round_authority(
            self.contract.run_id,
            2,
            registry_entry=second_registry_entry,
            mutation_payload=second_mutation,
            comparison_baseline=build_comparison_baseline(read_json(self.run_dir / "scoreboard.json")),
            recent_feedback_excerpt=[],
        )
        second_round_dir = self.worktree_manager.round_dir(self.contract.run_id, 2)
        (second_round_dir / "agent-report.md").write_text("# Agent Report\n\nApplied mutation.\n", encoding="utf-8")
        second_candidate = Path(str(second_prepare["worktree"]["path"]))
        (second_candidate / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate discard round two\n",
            encoding="utf-8",
        )
        second_capture = self.worktree_manager.capture_candidate_commit(
            self.contract.run_id,
            message="candidate discard round two",
        )
        second_round = second_capture["round"]
        second_round["state"] = "evaluated"
        (self.worktree_manager.round_path(self.contract.run_id, 2)).write_text(
            json.dumps(second_round, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        write_scoreboard(self.round_manager.round_scoreboard_path(self.contract.run_id, 2), build_scoreboard(9.0, 8.0))

        second_result = self.round_manager.decide_round(self.contract)

        baseline_scoreboard = read_json(self.run_dir / "scoreboard.json")
        self.assertEqual(second_result["decision"]["decision"], "discard")
        self.assertIn("train_score_improved", second_result["decision"]["reasons"])
        self.assertEqual(baseline_scoreboard["baseline_sha"], first_champion_sha)
        self.assertEqual(baseline_scoreboard["lanes"][0]["avg_total_score"], 10.0)
        self.assertEqual(baseline_scoreboard["rounds_completed"], 2)
        self.assertEqual(baseline_scoreboard["best_round"], 1)

    def test_decide_round_discards_parse_error_regression(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate parse regression\n",
            encoding="utf-8",
        )
        capture = self.worktree_manager.capture_candidate_commit(
            self.contract.run_id,
            message="candidate parse regression",
        )
        round_payload = capture["round"]
        round_payload["state"] = "evaluated"
        (self.worktree_manager.round_path(self.contract.run_id, 1)).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        write_scoreboard(
            self.round_manager.round_scoreboard_path(self.contract.run_id, 1),
            build_scoreboard(10.0, 8.0, parse_error=0.25),
        )

        result = self.round_manager.decide_round(self.contract)

        self.assertEqual(result["decision"]["decision"], "discard")
        self.assertIn("train_parse_error_non_regression", result["decision"]["reasons"])

    def test_decide_round_discards_pass_rate_regression(self) -> None:
        candidate_worktree, _ = self._prepare_active_round()
        (candidate_worktree / "product" / "memory-side" / "skills" / "skill.md").write_text(
            "candidate hard fail regression\n",
            encoding="utf-8",
        )
        capture = self.worktree_manager.capture_candidate_commit(
            self.contract.run_id,
            message="candidate hard fail regression",
        )
        round_payload = capture["round"]
        round_payload["state"] = "evaluated"
        (self.worktree_manager.round_path(self.contract.run_id, 1)).write_text(
            json.dumps(round_payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        write_scoreboard(
            self.round_manager.round_scoreboard_path(self.contract.run_id, 1),
            build_scoreboard(10.0, 8.0, pass_rate=0.5),
        )

        result = self.round_manager.decide_round(self.contract)

        self.assertEqual(result["decision"]["decision"], "discard")
        self.assertIn("train_pass_rate_non_regression", result["decision"]["reasons"])

    def _eval_result(self, total_score: float) -> dict[str, object]:
        return {
            "repo_path": str(self.repo_root),
            "task": "context-routing",
            "phase": "eval",
            "backend": "claude",
            "judge_backend": "claude",
            "prompt_file": str(self.repo_root / "prompt.md"),
            "returncode": 0,
            "timed_out": False,
            "elapsed_seconds": 1.0,
            "started_at": "2026-03-26T00:00:00+00:00",
            "finished_at": "2026-03-26T00:00:01+00:00",
            "schema_file": None,
            "parse_error": None,
            "structured_output": {
                "total_score": total_score,
                "overall": "Good",
                "dimension_feedback": {},
            },
            "artifacts": {},
        }


if __name__ == "__main__":
    unittest.main()
