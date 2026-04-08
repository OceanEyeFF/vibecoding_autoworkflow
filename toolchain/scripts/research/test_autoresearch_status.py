from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from autoresearch_status import refresh_status_indexes


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
                root / "product" / "harness-operations" / "skills" / "simple-workflow" / "SKILL.md",
            ):
                skill_path.parent.mkdir(parents=True, exist_ok=True)
                skill_path.write_text("# skill\n", encoding="utf-8")

            context_run = autoresearch_root / "demo-context"
            write_json(
                context_run / "contract.json",
                {
                    "run_id": "demo-context",
                    "target_task": "context-routing-skill",
                    "target_prompt_path": "toolchain/scripts/research/tasks/context-routing-skill-prompt.md",
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
                    "target_prompt_path": "toolchain/scripts/research/tasks/knowledge-base-skill-prompt.md",
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
            self.assertEqual(
                skills["simple-workflow"]["training_status"],
                "not_supported_by_autoresearch",
            )
