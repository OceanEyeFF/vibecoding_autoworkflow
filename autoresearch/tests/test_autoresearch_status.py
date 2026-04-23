from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from autoresearch_status import build_status_index_payloads, refresh_status_indexes, render_operator_summary


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def write_history(path: Path, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "round\tkind\tbase_sha\tcandidate_sha\ttrain_score\tvalidation_score\ttrain_parse_error_rate\tvalidation_parse_error_rate\tdecision\tnotes",
                *rows,
            ]
        )
        + "\n",
        encoding="utf-8",
    )


class AutoresearchStatusTest(unittest.TestCase):
    def test_refresh_status_indexes_builds_run_and_skill_views(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autoresearch_root = root / ".autoworkflow" / "autoresearch"

            for skill_path in (
                root / "product" / "memory-side" / "skills" / "context-routing-skill" / "SKILL.md",
                root / "product" / "memory-side" / "skills" / "knowledge-base-skill" / "SKILL.md",
                root / "product" / "memory-side" / "skills" / "writeback-cleanup-skill" / "SKILL.md",
                root / "product" / "task-interface" / "skills" / "task-contract-skill" / "SKILL.md",
            ):
                skill_path.parent.mkdir(parents=True, exist_ok=True)
                skill_path.write_text("# skill\n", encoding="utf-8")

            context_run = autoresearch_root / "demo-context"
            write_json(
                context_run / "contract.json",
                {
                    "run_id": "demo-context",
                    "target_task": "context-routing-skill",
                    "target_prompt_path": "autoresearch/src/tasks/context-routing-skill-prompt.md",
                    "worker_backend": "claude",
                    "expected_backend": "claude",
                    "expected_judge_backend": "claude",
                    "max_rounds": 3,
                },
            )
            write_json(
                context_run / "runtime.json",
                {
                    "run_id": "demo-context",
                    "champion_sha": "abc123",
                    "active_round": None,
                    "updated_at": "2026-04-08T10:00:00+00:00",
                },
            )
            write_json(
                context_run / "scoreboard.json",
                {
                    "run_id": "demo-context",
                    "generated_at": "2026-04-08T10:00:00+00:00",
                    "baseline_sha": "abc123",
                    "rounds_completed": 1,
                    "best_round": 1,
                    "lanes": [
                        {
                            "lane_name": "train",
                            "backend": "claude",
                            "judge_backend": "claude",
                            "avg_total_score": 11.5,
                            "pass_rate": 1.0,
                            "parse_error_rate": 0.0,
                        },
                        {
                            "lane_name": "validation",
                            "backend": "claude",
                            "judge_backend": "claude",
                            "avg_total_score": 12.0,
                            "pass_rate": 1.0,
                            "parse_error_rate": 0.0,
                        },
                    ],
                },
            )
            write_json(
                context_run / "rounds" / "round-001" / "decision.json",
                {
                    "round": 1,
                    "decision": "keep",
                    "decided_at": "2026-04-08T10:00:00+00:00",
                },
            )
            write_history(
                context_run / "history.tsv",
                [
                    "0\tbaseline\tabc123\t-\t10.000000\t10.500000\t0.000000\t0.000000\tbaseline\t",
                    "1\ttext_rephrase\tabc123\tdef456\t11.500000\t12.000000\t0.000000\t0.000000\tkeep\tmutation_id=mut-001",
                ],
            )

            kb_run = autoresearch_root / "demo-kb"
            write_json(
                kb_run / "contract.json",
                {
                    "run_id": "demo-kb",
                    "target_task": "knowledge-base-skill",
                    "target_prompt_path": "autoresearch/src/tasks/knowledge-base-skill-prompt.md",
                    "worker_backend": "codex",
                    "expected_backend": "codex",
                    "expected_judge_backend": "codex",
                    "max_rounds": 2,
                },
            )
            write_json(
                kb_run / "runtime.json",
                {
                    "run_id": "demo-kb",
                    "champion_sha": "999999",
                    "active_round": 2,
                    "updated_at": "2026-04-08T11:00:00+00:00",
                },
            )
            write_json(
                kb_run / "scoreboard.json",
                {
                    "run_id": "demo-kb",
                    "generated_at": "2026-04-08T09:00:00+00:00",
                    "baseline_sha": "999999",
                    "rounds_completed": 0,
                    "best_round": 0,
                    "lanes": [
                        {
                            "lane_name": "train",
                            "backend": "codex",
                            "judge_backend": "codex",
                            "avg_total_score": 8.0,
                            "pass_rate": 1.0,
                            "parse_error_rate": 0.0,
                        },
                        {
                            "lane_name": "validation",
                            "backend": "codex",
                            "judge_backend": "codex",
                            "avg_total_score": 7.5,
                            "pass_rate": 1.0,
                            "parse_error_rate": 0.0,
                        },
                    ],
                },
            )
            write_json(
                kb_run / "rounds" / "round-002" / "round.json",
                {
                    "round": 2,
                    "state": "candidate_active",
                },
            )
            write_history(
                kb_run / "history.tsv",
                ["0\tbaseline\t999999\t-\t8.000000\t7.500000\t0.000000\t0.000000\tbaseline\t"],
            )

            run_index_path, skill_index_path = refresh_status_indexes(
                autoresearch_root=autoresearch_root,
                repo_root=root,
            )

            run_index = json.loads(run_index_path.read_text(encoding="utf-8"))
            skill_index = json.loads(skill_index_path.read_text(encoding="utf-8"))

            self.assertEqual(run_index["runs"][0]["run_id"], "demo-kb")
            self.assertEqual(run_index["runs"][0]["training_status"], "round_candidate_active")
            self.assertEqual(run_index["runs"][1]["run_id"], "demo-context")
            self.assertEqual(run_index["runs"][1]["training_status"], "awaiting_next_round")

            skills = {entry["skill_id"]: entry for entry in skill_index["skills"]}
            self.assertEqual(skills["context-routing-skill"]["training_status"], "awaiting_next_round")
            self.assertEqual(skills["context-routing-skill"]["latest_run_id"], "demo-context")
            self.assertEqual(skills["knowledge-base-skill"]["training_status"], "round_candidate_active")
            self.assertEqual(skills["task-contract-skill"]["training_status"], "not_started")

    def test_refresh_status_indexes_preserves_interrupted_active_round_states(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autoresearch_root = root / ".autoworkflow" / "autoresearch"

            for skill_path in (
                root / "product" / "memory-side" / "skills" / "context-routing-skill" / "SKILL.md",
                root / "product" / "memory-side" / "skills" / "knowledge-base-skill" / "SKILL.md",
            ):
                skill_path.parent.mkdir(parents=True, exist_ok=True)
                skill_path.write_text("# skill\n", encoding="utf-8")

            missing_round_run = autoresearch_root / "demo-missing-round"
            write_json(
                missing_round_run / "contract.json",
                {
                    "run_id": "demo-missing-round",
                    "target_task": "context-routing-skill",
                    "target_prompt_path": "autoresearch/src/tasks/context-routing-skill-prompt.md",
                    "worker_backend": "codex",
                    "expected_backend": "codex",
                    "expected_judge_backend": "codex",
                    "max_rounds": 3,
                },
            )
            write_json(
                missing_round_run / "runtime.json",
                {
                    "run_id": "demo-missing-round",
                    "champion_sha": "aaa111",
                    "active_round": 2,
                    "updated_at": "2026-04-09T10:00:00+00:00",
                },
            )
            write_json(
                missing_round_run / "scoreboard.json",
                {
                    "run_id": "demo-missing-round",
                    "generated_at": "2026-04-09T09:00:00+00:00",
                    "baseline_sha": "aaa111",
                    "rounds_completed": 1,
                    "best_round": 1,
                    "lanes": [
                        {"lane_name": "train", "avg_total_score": 9.0},
                        {"lane_name": "validation", "avg_total_score": 9.5},
                    ],
                },
            )
            write_history(
                missing_round_run / "history.tsv",
                [
                    "0\tbaseline\taaa111\t-\t8.500000\t8.750000\t0.000000\t0.000000\tbaseline\t",
                    "1\ttext_rephrase\taaa111\tbbb222\t9.000000\t9.500000\t0.000000\t0.000000\tdiscard\tmutation_id=mut-001",
                ],
            )

            recovered_round_run = autoresearch_root / "demo-recovered-round"
            write_json(
                recovered_round_run / "contract.json",
                {
                    "run_id": "demo-recovered-round",
                    "target_task": "knowledge-base-skill",
                    "target_prompt_path": "autoresearch/src/tasks/knowledge-base-skill-prompt.md",
                    "worker_backend": "claude",
                    "expected_backend": "claude",
                    "expected_judge_backend": "claude",
                    "max_rounds": 3,
                },
            )
            write_json(
                recovered_round_run / "scoreboard.json",
                {
                    "run_id": "demo-recovered-round",
                    "generated_at": "2026-04-09T08:00:00+00:00",
                    "baseline_sha": "ccc333",
                    "rounds_completed": 0,
                    "best_round": 0,
                    "lanes": [
                        {"lane_name": "train", "avg_total_score": 7.0},
                        {"lane_name": "validation", "avg_total_score": 7.25},
                    ],
                },
            )
            write_json(
                recovered_round_run / "rounds" / "round-001" / "round.json",
                {
                    "round": 1,
                    "state": "prepared",
                },
            )
            write_history(
                recovered_round_run / "history.tsv",
                ["0\tbaseline\tccc333\t-\t7.000000\t7.250000\t0.000000\t0.000000\tbaseline\t"],
            )

            run_index_path, skill_index_path = refresh_status_indexes(
                autoresearch_root=autoresearch_root,
                repo_root=root,
            )

            run_index = json.loads(run_index_path.read_text(encoding="utf-8"))
            skill_index = json.loads(skill_index_path.read_text(encoding="utf-8"))

            runs = {entry["run_id"]: entry for entry in run_index["runs"]}
            self.assertEqual(
                runs["demo-missing-round"]["training_status"],
                "round_cleanup_required_missing_round_json",
            )
            self.assertEqual(runs["demo-missing-round"]["active_round"], 2)
            self.assertEqual(
                runs["demo-recovered-round"]["training_status"],
                "round_prepared_recovery_required",
            )
            self.assertEqual(runs["demo-recovered-round"]["active_round"], 1)

            skills = {entry["skill_id"]: entry for entry in skill_index["skills"]}
            self.assertEqual(
                skills["context-routing-skill"]["training_status"],
                "round_cleanup_required_missing_round_json",
            )
            self.assertEqual(
                skills["knowledge-base-skill"]["training_status"],
                "round_prepared_recovery_required",
            )

    def test_refresh_status_indexes_discovers_evaluated_round_when_runtime_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autoresearch_root = root / ".autoworkflow" / "autoresearch"

            skill_path = root / "product" / "memory-side" / "skills" / "knowledge-base-skill" / "SKILL.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text("# skill\n", encoding="utf-8")

            run_dir = autoresearch_root / "demo-evaluated"
            write_json(
                run_dir / "contract.json",
                {
                    "run_id": "demo-evaluated",
                    "target_task": "knowledge-base-skill",
                    "target_prompt_path": "autoresearch/src/tasks/knowledge-base-skill-prompt.md",
                    "worker_backend": "codex",
                    "expected_backend": "codex",
                    "expected_judge_backend": "codex",
                    "max_rounds": 3,
                },
            )
            write_json(
                run_dir / "scoreboard.json",
                {
                    "run_id": "demo-evaluated",
                    "generated_at": "2026-04-09T11:00:00+00:00",
                    "baseline_sha": "123abc",
                    "rounds_completed": 0,
                    "best_round": 0,
                    "lanes": [
                        {"lane_name": "train", "avg_total_score": 8.5},
                        {"lane_name": "validation", "avg_total_score": 8.0},
                    ],
                },
            )
            write_json(
                run_dir / "rounds" / "round-001" / "round.json",
                {
                    "round": 1,
                    "state": "evaluated",
                },
            )

            run_index_path, skill_index_path = refresh_status_indexes(
                autoresearch_root=autoresearch_root,
                repo_root=root,
            )
            run_index = json.loads(run_index_path.read_text(encoding="utf-8"))
            skill_index = json.loads(skill_index_path.read_text(encoding="utf-8"))

            self.assertEqual(run_index["runs"][0]["training_status"], "round_evaluated_recovery_required")
            self.assertEqual(run_index["runs"][0]["active_round"], 1)
            skills = {entry["skill_id"]: entry for entry in skill_index["skills"]}
            self.assertEqual(skills["knowledge-base-skill"]["training_status"], "round_evaluated_recovery_required")

    def test_render_operator_summary_highlights_latest_and_action_needed_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autoresearch_root = root / ".autoworkflow" / "autoresearch"

            for skill_path in (
                root / "product" / "memory-side" / "skills" / "context-routing-skill" / "SKILL.md",
                root / "product" / "memory-side" / "skills" / "knowledge-base-skill" / "SKILL.md",
                root / "product" / "memory-side" / "skills" / "writeback-cleanup-skill" / "SKILL.md",
                root / "product" / "task-interface" / "skills" / "task-contract-skill" / "SKILL.md",
            ):
                skill_path.parent.mkdir(parents=True, exist_ok=True)
                skill_path.write_text("# skill\n", encoding="utf-8")

            waiting_run = autoresearch_root / "demo-context"
            write_json(
                waiting_run / "contract.json",
                {
                    "run_id": "demo-context",
                    "target_task": "context-routing-skill",
                    "target_prompt_path": "autoresearch/src/tasks/context-routing-skill-prompt.md",
                    "worker_backend": "claude",
                    "expected_backend": "claude",
                    "expected_judge_backend": "claude",
                    "max_rounds": 3,
                },
            )
            write_json(
                waiting_run / "runtime.json",
                {
                    "run_id": "demo-context",
                    "champion_sha": "abc123",
                    "active_round": None,
                    "updated_at": "2026-04-08T10:00:00+00:00",
                },
            )
            write_json(
                waiting_run / "scoreboard.json",
                {
                    "run_id": "demo-context",
                    "generated_at": "2026-04-08T10:00:00+00:00",
                    "baseline_sha": "abc123",
                    "rounds_completed": 1,
                    "best_round": 1,
                    "lanes": [
                        {"lane_name": "train", "avg_total_score": 11.5},
                        {"lane_name": "validation", "avg_total_score": 12.0},
                    ],
                },
            )
            write_json(
                waiting_run / "rounds" / "round-001" / "decision.json",
                {
                    "round": 1,
                    "decision": "keep",
                    "decided_at": "2026-04-08T10:00:00+00:00",
                },
            )

            active_run = autoresearch_root / "demo-active"
            write_json(
                active_run / "contract.json",
                {
                    "run_id": "demo-active",
                    "target_task": "knowledge-base-skill",
                    "target_prompt_path": "autoresearch/src/tasks/knowledge-base-skill-prompt.md",
                    "worker_backend": "codex",
                    "expected_backend": "codex",
                    "expected_judge_backend": "codex",
                    "max_rounds": 2,
                },
            )
            write_json(
                active_run / "runtime.json",
                {
                    "run_id": "demo-active",
                    "champion_sha": "999999",
                    "active_round": 2,
                    "updated_at": "2026-04-09T11:00:00+00:00",
                },
            )
            write_json(
                active_run / "scoreboard.json",
                {
                    "run_id": "demo-active",
                    "generated_at": "2026-04-09T09:00:00+00:00",
                    "baseline_sha": "999999",
                    "rounds_completed": 0,
                    "best_round": 0,
                    "lanes": [
                        {"lane_name": "train", "avg_total_score": 8.0},
                        {"lane_name": "validation", "avg_total_score": 7.5},
                    ],
                },
            )
            write_json(
                active_run / "rounds" / "round-002" / "round.json",
                {
                    "round": 2,
                    "state": "candidate_active",
                },
            )

            cleanup_run = autoresearch_root / "demo-cleanup"
            write_json(
                cleanup_run / "contract.json",
                {
                    "run_id": "demo-cleanup",
                    "target_task": "writeback-cleanup-skill",
                    "target_prompt_path": "autoresearch/src/tasks/writeback-cleanup-skill-prompt.md",
                    "worker_backend": "codex",
                    "expected_backend": "codex",
                    "expected_judge_backend": "codex",
                    "max_rounds": 3,
                },
            )
            write_json(
                cleanup_run / "runtime.json",
                {
                    "run_id": "demo-cleanup",
                    "champion_sha": "aaa111",
                    "active_round": 3,
                    "updated_at": "2026-04-09T12:00:00+00:00",
                },
            )
            write_json(
                cleanup_run / "scoreboard.json",
                {
                    "run_id": "demo-cleanup",
                    "generated_at": "2026-04-09T08:00:00+00:00",
                    "baseline_sha": "aaa111",
                    "rounds_completed": 1,
                    "best_round": 1,
                    "lanes": [
                        {"lane_name": "train", "avg_total_score": 9.0},
                        {"lane_name": "validation", "avg_total_score": 9.5},
                    ],
                },
            )

            summary = render_operator_summary(
                autoresearch_root=autoresearch_root,
                repo_root=root,
            )

            self.assertIn("latest_run: demo-cleanup [cleanup-required / round_cleanup_required_missing_round_json]", summary)
            self.assertIn("context-routing-skill", summary)
            self.assertIn("awaiting_next_round", summary)
            self.assertIn("knowledge-base-skill", summary)
            self.assertIn("round_candidate_active", summary)
            self.assertIn("writeback-cleanup-skill", summary)
            self.assertIn("cleanup-round first", summary)
            self.assertIn("action_needed_runs", summary)
            self.assertIn("demo-active", summary)
            self.assertIn("demo-cleanup", summary)

    def test_render_operator_summary_guides_evaluated_rounds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autoresearch_root = root / ".autoworkflow" / "autoresearch"

            skill_path = root / "product" / "memory-side" / "skills" / "knowledge-base-skill" / "SKILL.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text("# skill\n", encoding="utf-8")

            run_dir = autoresearch_root / "demo-evaluated"
            write_json(
                run_dir / "contract.json",
                {
                    "run_id": "demo-evaluated",
                    "target_task": "knowledge-base-skill",
                    "target_prompt_path": "autoresearch/src/tasks/knowledge-base-skill-prompt.md",
                    "worker_backend": "codex",
                    "expected_backend": "codex",
                    "expected_judge_backend": "codex",
                    "max_rounds": 2,
                },
            )
            write_json(
                run_dir / "runtime.json",
                {
                    "run_id": "demo-evaluated",
                    "champion_sha": "999999",
                    "active_round": 2,
                    "updated_at": "2026-04-09T11:00:00+00:00",
                },
            )
            write_json(
                run_dir / "scoreboard.json",
                {
                    "run_id": "demo-evaluated",
                    "generated_at": "2026-04-09T09:00:00+00:00",
                    "baseline_sha": "999999",
                    "rounds_completed": 0,
                    "best_round": 0,
                    "lanes": [
                        {"lane_name": "train", "avg_total_score": 8.0},
                        {"lane_name": "validation", "avg_total_score": 7.5},
                    ],
                },
            )
            write_json(
                run_dir / "rounds" / "round-002" / "round.json",
                {
                    "round": 2,
                    "state": "evaluated",
                },
            )

            summary = render_operator_summary(
                autoresearch_root=autoresearch_root,
                repo_root=root,
            )

            self.assertIn("round_evaluated", summary)
            self.assertIn("decide-round next, or cleanup-round if the round is no longer usable", summary)

    def test_render_operator_summary_treats_accepted_round_as_cleanup_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autoresearch_root = root / ".autoworkflow" / "autoresearch"

            skill_path = root / "product" / "memory-side" / "skills" / "knowledge-base-skill" / "SKILL.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text("# skill\n", encoding="utf-8")

            run_dir = autoresearch_root / "demo-accepted"
            write_json(
                run_dir / "contract.json",
                {
                    "run_id": "demo-accepted",
                    "target_task": "knowledge-base-skill",
                    "target_prompt_path": "autoresearch/src/tasks/knowledge-base-skill-prompt.md",
                    "worker_backend": "codex",
                    "expected_backend": "codex",
                    "expected_judge_backend": "codex",
                    "max_rounds": 2,
                },
            )
            write_json(
                run_dir / "runtime.json",
                {
                    "run_id": "demo-accepted",
                    "champion_sha": "999999",
                    "active_round": 2,
                    "updated_at": "2026-04-09T11:00:00+00:00",
                },
            )
            write_json(
                run_dir / "scoreboard.json",
                {
                    "run_id": "demo-accepted",
                    "generated_at": "2026-04-09T09:00:00+00:00",
                    "baseline_sha": "999999",
                    "rounds_completed": 1,
                    "best_round": 1,
                    "lanes": [
                        {"lane_name": "train", "avg_total_score": 8.0},
                        {"lane_name": "validation", "avg_total_score": 7.5},
                    ],
                },
            )
            write_json(
                run_dir / "rounds" / "round-002" / "round.json",
                {
                    "round": 2,
                    "state": "accepted",
                },
            )

            summary = render_operator_summary(
                autoresearch_root=autoresearch_root,
                repo_root=root,
            )

            self.assertIn("latest_run: demo-accepted [cleanup-required / round_accepted]", summary)
            self.assertIn("cleanup-round first", summary)

    def test_render_operator_summary_guides_prepared_rounds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autoresearch_root = root / ".autoworkflow" / "autoresearch"

            skill_path = root / "product" / "memory-side" / "skills" / "knowledge-base-skill" / "SKILL.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text("# skill\n", encoding="utf-8")

            run_dir = autoresearch_root / "demo-prepared"
            write_json(
                run_dir / "contract.json",
                {
                    "run_id": "demo-prepared",
                    "target_task": "knowledge-base-skill",
                    "target_prompt_path": "autoresearch/src/tasks/knowledge-base-skill-prompt.md",
                    "worker_backend": "codex",
                    "expected_backend": "codex",
                    "expected_judge_backend": "codex",
                    "max_rounds": 2,
                },
            )
            write_json(
                run_dir / "runtime.json",
                {
                    "run_id": "demo-prepared",
                    "champion_sha": "999999",
                    "active_round": 1,
                    "updated_at": "2026-04-09T11:00:00+00:00",
                },
            )
            write_json(
                run_dir / "scoreboard.json",
                {
                    "run_id": "demo-prepared",
                    "generated_at": "2026-04-09T09:00:00+00:00",
                    "baseline_sha": "999999",
                    "rounds_completed": 0,
                    "best_round": 0,
                    "lanes": [
                        {"lane_name": "train", "avg_total_score": 8.0},
                        {"lane_name": "validation", "avg_total_score": 7.5},
                    ],
                },
            )
            write_json(
                run_dir / "rounds" / "round-001" / "round.json",
                {
                    "round": 1,
                    "state": "prepared",
                },
            )

            summary = render_operator_summary(
                autoresearch_root=autoresearch_root,
                repo_root=root,
            )

            self.assertIn("round_prepared", summary)
            self.assertIn("continue active round or cleanup-round", summary)

    def test_build_status_payloads_surface_malformed_skill_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autoresearch_root = root / ".autoworkflow" / "autoresearch"

            skill_path = root / "product" / "memory-side" / "skills" / "context-routing-skill" / "SKILL.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text("# skill\n", encoding="utf-8")

            broken_run = autoresearch_root / "broken-run"
            write_json(
                broken_run / "contract.json",
                {
                    "run_id": "broken-run",
                    "target_task": "context-routing-skill",
                    "target_prompt_path": "autoresearch/src/tasks/context-routing-skill-prompt.md",
                    "worker_backend": "codex",
                    "expected_backend": "codex",
                    "expected_judge_backend": "codex",
                },
            )
            write_json(
                broken_run / "runtime.json",
                {
                    "run_id": "broken-run",
                    "active_round": 1,
                    "updated_at": "2026-04-09T12:00:00+00:00",
                },
            )
            write_json(
                broken_run / "scoreboard.json",
                {
                    "run_id": "broken-run",
                    "generated_at": "2026-04-09T11:00:00+00:00",
                    "lanes": 1,
                },
            )

            run_index, skill_index = build_status_index_payloads(
                autoresearch_root=autoresearch_root,
                repo_root=root,
                strict=False,
            )

            self.assertEqual(len(run_index["runs"]), 0)
            self.assertEqual(len(run_index["malformed_runs"]), 1)
            self.assertEqual(run_index["malformed_runs"][0]["run_id"], "broken-run")
            self.assertEqual(run_index["malformed_runs"][0]["target_task"], "context-routing-skill")

            skills = {entry["skill_id"]: entry for entry in skill_index["skills"]}
            self.assertEqual(skills["context-routing-skill"]["training_status"], "malformed_run_present")
            self.assertEqual(skills["context-routing-skill"]["latest_run_id"], "broken-run")
            self.assertEqual(skills["context-routing-skill"]["malformed_runs_total"], 1)
            self.assertIn("iterable", skills["context-routing-skill"]["latest_malformed_error"])

    def test_missing_scoreboard_still_uses_history_to_surface_progressed_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autoresearch_root = root / ".autoworkflow" / "autoresearch"

            skill_path = root / "product" / "memory-side" / "skills" / "context-routing-skill" / "SKILL.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text("# skill\n", encoding="utf-8")

            run_dir = autoresearch_root / "history-only-run"
            write_json(
                run_dir / "contract.json",
                {
                    "run_id": "history-only-run",
                    "target_task": "context-routing-skill",
                    "target_prompt_path": "autoresearch/src/tasks/context-routing-skill-prompt.md",
                    "worker_backend": "codex",
                    "expected_backend": "codex",
                    "expected_judge_backend": "codex",
                    "max_rounds": 3,
                },
            )
            write_history(
                run_dir / "history.tsv",
                [
                    "0\tbaseline\taaa111\t-\t8.000000\t8.100000\t0.000000\t0.000000\tbaseline\t",
                    "1\ttext_rephrase\taaa111\tbbb222\t8.500000\t8.700000\t0.000000\t0.000000\tkeep\tmutation_id=mut-001",
                ],
            )
            write_json(
                run_dir / "rounds" / "round-001" / "decision.json",
                {
                    "round": 1,
                    "decision": "keep",
                    "decided_at": "2026-04-09T12:00:00+00:00",
                },
            )

            run_index, skill_index = build_status_index_payloads(
                autoresearch_root=autoresearch_root,
                repo_root=root,
                strict=False,
            )

            self.assertEqual(run_index["runs"][0]["run_id"], "history-only-run")
            self.assertEqual(run_index["runs"][0]["training_status"], "awaiting_next_round")
            self.assertEqual(run_index["runs"][0]["rounds_completed"], 1)
            skills = {entry["skill_id"]: entry for entry in skill_index["skills"]}
            self.assertEqual(skills["context-routing-skill"]["training_status"], "awaiting_next_round")
            self.assertEqual(skills["context-routing-skill"]["latest_run_id"], "history-only-run")

    def test_contractless_run_directory_with_artifacts_is_quarantined_as_malformed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autoresearch_root = root / ".autoworkflow" / "autoresearch"

            skill_path = root / "product" / "memory-side" / "skills" / "context-routing-skill" / "SKILL.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text("# skill\n", encoding="utf-8")

            run_dir = autoresearch_root / "contractless-run"
            write_json(
                run_dir / "runtime.json",
                {
                    "run_id": "contractless-run",
                    "active_round": 1,
                    "updated_at": "2026-04-09T12:00:00+00:00",
                },
            )
            write_json(
                run_dir / "scoreboard.json",
                {
                    "run_id": "contractless-run",
                    "generated_at": "2026-04-09T11:00:00+00:00",
                    "rounds_completed": 0,
                    "best_round": 0,
                    "lanes": [],
                },
            )

            run_index, skill_index = build_status_index_payloads(
                autoresearch_root=autoresearch_root,
                repo_root=root,
                strict=False,
            )

            self.assertEqual(run_index["runs"], [])
            self.assertEqual(run_index["malformed_runs"][0]["run_id"], "contractless-run")
            self.assertIn("Missing contract.json", run_index["malformed_runs"][0]["error"])
            skills = {entry["skill_id"]: entry for entry in skill_index["skills"]}
            self.assertEqual(skills["context-routing-skill"]["training_status"], "not_started")
            summary = render_operator_summary(
                autoresearch_root=autoresearch_root,
                repo_root=root,
            )
            self.assertIn("contractless-run", summary)
            self.assertIn("malformed_run_present", summary)

    def test_refresh_status_indexes_writes_malformed_runs_instead_of_failing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autoresearch_root = root / ".autoworkflow" / "autoresearch"

            skill_path = root / "product" / "memory-side" / "skills" / "context-routing-skill" / "SKILL.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text("# skill\n", encoding="utf-8")

            broken_run = autoresearch_root / "broken-run"
            write_json(
                broken_run / "contract.json",
                {
                    "run_id": "broken-run",
                    "target_task": "context-routing-skill",
                    "updated_at": "2026-04-09T12:00:00+00:00",
                },
            )
            write_json(
                broken_run / "scoreboard.json",
                {
                    "run_id": "broken-run",
                    "generated_at": "2026-04-09T11:00:00+00:00",
                    "lanes": 1,
                },
            )

            run_index_path, skill_index_path = refresh_status_indexes(
                autoresearch_root=autoresearch_root,
                repo_root=root,
            )

            run_index = json.loads(run_index_path.read_text(encoding="utf-8"))
            skill_index = json.loads(skill_index_path.read_text(encoding="utf-8"))
            self.assertEqual(run_index["runs"], [])
            self.assertEqual(run_index["malformed_runs"][0]["run_id"], "broken-run")
            skills = {entry["skill_id"]: entry for entry in skill_index["skills"]}
            self.assertEqual(skills["context-routing-skill"]["training_status"], "malformed_run_present")

    def test_render_operator_summary_skips_type_error_runs_and_marks_skill_for_repair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autoresearch_root = root / ".autoworkflow" / "autoresearch"

            skill_path = root / "product" / "memory-side" / "skills" / "context-routing-skill" / "SKILL.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text("# skill\n", encoding="utf-8")

            healthy_run = autoresearch_root / "demo-run"
            write_json(
                healthy_run / "contract.json",
                {
                    "run_id": "demo-run",
                    "target_task": "context-routing-skill",
                    "target_prompt_path": "autoresearch/src/tasks/context-routing-skill-prompt.md",
                    "worker_backend": "codex",
                    "expected_backend": "codex",
                    "expected_judge_backend": "codex",
                    "max_rounds": 2,
                },
            )
            write_json(
                healthy_run / "runtime.json",
                {
                    "run_id": "demo-run",
                    "champion_sha": "abc123",
                    "active_round": None,
                    "updated_at": "2026-04-09T10:00:00+00:00",
                },
            )
            write_json(
                healthy_run / "scoreboard.json",
                {
                    "run_id": "demo-run",
                    "generated_at": "2026-04-09T09:00:00+00:00",
                    "baseline_sha": "abc123",
                    "rounds_completed": 1,
                    "best_round": 1,
                    "lanes": [
                        {"lane_name": "train", "avg_total_score": 8.0},
                        {"lane_name": "validation", "avg_total_score": 7.5},
                    ],
                },
            )

            broken_run = autoresearch_root / "broken-run"
            write_json(
                broken_run / "contract.json",
                {
                    "run_id": "broken-run",
                    "target_task": "context-routing-skill",
                    "target_prompt_path": "autoresearch/src/tasks/context-routing-skill-prompt.md",
                    "worker_backend": "codex",
                    "expected_backend": "codex",
                    "expected_judge_backend": "codex",
                    "updated_at": "2026-04-09T12:00:00+00:00",
                },
            )
            write_json(
                broken_run / "scoreboard.json",
                {
                    "run_id": "broken-run",
                    "generated_at": "2026-04-09T12:00:00+00:00",
                    "lanes": 1,
                },
            )

            summary = render_operator_summary(
                autoresearch_root=autoresearch_root,
                repo_root=root,
            )

            self.assertIn("malformed_runs_skipped: 1", summary)
            self.assertIn("broken-run", summary)
            self.assertIn("malformed_run_present", summary)
            self.assertIn("inspect malformed run artifacts, then repair or cleanup-round", summary)
            self.assertNotIn("init + baseline when ready", summary)

    def test_render_operator_summary_uses_latest_malformed_run_for_latest_and_action_needed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autoresearch_root = root / ".autoworkflow" / "autoresearch"

            skill_path = root / "product" / "memory-side" / "skills" / "context-routing-skill" / "SKILL.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text("# skill\n", encoding="utf-8")

            healthy_run = autoresearch_root / "healthy-run"
            write_json(
                healthy_run / "contract.json",
                {
                    "run_id": "healthy-run",
                    "target_task": "context-routing-skill",
                    "updated_at": "2026-04-09T10:00:00+00:00",
                },
            )
            write_json(
                healthy_run / "scoreboard.json",
                {
                    "run_id": "healthy-run",
                    "generated_at": "2026-04-09T10:00:00+00:00",
                    "rounds_completed": 1,
                    "best_round": 1,
                    "lanes": [
                        {"lane_name": "train", "avg_total_score": 8.0},
                        {"lane_name": "validation", "avg_total_score": 7.5},
                    ],
                },
            )

            broken_run = autoresearch_root / "broken-run"
            write_json(
                broken_run / "contract.json",
                {
                    "run_id": "broken-run",
                    "target_task": "context-routing-skill",
                    "updated_at": "2026-04-09T12:00:00+00:00",
                },
            )
            write_json(
                broken_run / "scoreboard.json",
                {
                    "run_id": "broken-run",
                    "generated_at": "2026-04-09T12:00:00+00:00",
                    "lanes": 1,
                },
            )

            summary = render_operator_summary(
                autoresearch_root=autoresearch_root,
                repo_root=root,
            )

            self.assertIn("latest_run: broken-run [cleanup-required / malformed_run_present]", summary)
            self.assertIn("action_needed_runs", summary)
            self.assertIn("broken-run", summary)
            self.assertIn("malformed_run_present", summary)

    def test_render_operator_summary_still_skips_malformed_runs_when_decision_json_is_also_bad(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autoresearch_root = root / ".autoworkflow" / "autoresearch"

            skill_path = root / "product" / "memory-side" / "skills" / "context-routing-skill" / "SKILL.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text("# skill\n", encoding="utf-8")

            broken_run = autoresearch_root / "broken-run"
            write_json(
                broken_run / "contract.json",
                {
                    "run_id": "broken-run",
                    "target_task": "context-routing-skill",
                    "updated_at": "2026-04-09T12:00:00+00:00",
                },
            )
            write_json(
                broken_run / "scoreboard.json",
                {
                    "run_id": "broken-run",
                    "generated_at": "2026-04-09T11:00:00+00:00",
                    "lanes": 1,
                },
            )
            (broken_run / "rounds" / "round-001").mkdir(parents=True, exist_ok=True)
            (broken_run / "rounds" / "round-001" / "decision.json").write_text(
                "{not-json}\n",
                encoding="utf-8",
            )

            summary = render_operator_summary(
                autoresearch_root=autoresearch_root,
                repo_root=root,
            )

            self.assertIn("malformed_runs_skipped: 1", summary)
            self.assertIn("broken-run", summary)
            self.assertIn("malformed_run_present", summary)
