from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autoresearch_feedback_distill import (
    build_feedback_distill_payload,
    build_recent_feedback_excerpt,
    feedback_family_priority,
    latest_aggregate_prompt_guidance,
    load_feedback_ledger,
    upsert_feedback_ledger_entry,
)


def build_repo_task(
    *,
    lane_name: str,
    repo: str,
    task: str,
    total_score: float,
    needs_improvement: str = "Could narrow the path list further.",
) -> dict[str, object]:
    return {
        "lane_name": lane_name,
        "repo": repo,
        "task": task,
        "phase": "eval",
        "total_score": total_score,
        "overall": "Good",
        "dimension_feedback": {
            "path_contraction": {
                "what_worked": "Kept the initial read list narrow.",
                "needs_improvement": needs_improvement,
            },
            "entry_point_identification": {
                "what_worked": "Selected the entry files directly.",
                "needs_improvement": "Could explain why the first files are entry points.",
            },
        },
    }


def build_scoreboard(
    *,
    train_score: float,
    validation_score: float,
    parse_error: float = 0.0,
    timeout: float = 0.0,
    pass_rate: float = 1.0,
    repo_tasks: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "run_id": "demo-run",
        "generated_at": "2026-03-27T00:00:00+00:00",
        "baseline_sha": "base",
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
                "timeout_rate": timeout,
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
                "timeout_rate": timeout,
                "parse_error_rate": parse_error,
                "avg_total_score": validation_score,
            },
        ],
        "repo_tasks": list(repo_tasks or []),
    }


def build_ledger_entry(
    *,
    mutation_key: str,
    round_number: int,
    mutation_id: str,
    decision: str,
    signal_strength: str,
    regression_flags: list[str] | None = None,
    aggregate_direction: str = "mixed",
    aggregate_suggested_adjustments: list[str] | None = None,
) -> dict[str, object]:
    return {
        "feedback_ledger_version": 2,
        "run_id": "demo-run",
        "round": round_number,
        "mutation_key": mutation_key,
        "mutation_id": mutation_id,
        "attempt": 1,
        "decision": decision,
        "train_score_delta": 0.5,
        "validation_score_delta": -0.2 if decision == "discard" else 0.2,
        "parse_error_delta": 0.0,
        "timeout_rate_delta": 0.0,
        "signal_strength": signal_strength,
        "regression_flags": list(regression_flags or []),
        "dimension_feedback_summary": {"validation_score": "weaker" if decision == "discard" else "improved"},
        "aggregate_prompt_guidance": {
            "aggregate_direction": aggregate_direction,
            "aggregate_suggested_adjustments": list(
                aggregate_suggested_adjustments or ["narrow the next retry to protect validation behavior"]
            ),
            "top_regression_repos": ["typer"] if decision == "discard" else [],
            "top_improvement_repos": ["typer"] if decision == "keep" else [],
            "dominant_dimension_signals": [
                {
                    "dimension": "path_contraction",
                    "signal": "weaker" if decision == "discard" else "improved",
                    "count": 1,
                    "repos": ["typer"],
                }
            ],
            "generation_status": "generated",
        },
        "scoreboard_ref": f"rounds/round-{round_number:03d}/scoreboard.json",
        "decision_ref": f"rounds/round-{round_number:03d}/decision.json",
        "worker_contract_ref": f"rounds/round-{round_number:03d}/worker-contract.json",
        "distilled_at": "2026-03-27T00:00:00+00:00",
    }


class AutoresearchFeedbackDistillTest(unittest.TestCase):
    def test_build_feedback_distill_payload_computes_repo_guidance_and_aggregate(self) -> None:
        baseline_repo_tasks = [
            build_repo_task(lane_name="validation", repo="typer", task="context-routing", total_score=9.5),
        ]
        round_repo_tasks = [
            build_repo_task(
                lane_name="validation",
                repo="typer",
                task="context-routing",
                total_score=8.0,
                needs_improvement="Read list is a bit long and could be further narrowed after initial entrypoint skim.",
            ),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "demo-run"
            round_dir = run_dir / "rounds" / "round-001"
            round_dir.mkdir(parents=True, exist_ok=True)
            (round_dir / "decision.json").write_text("{}\n", encoding="utf-8")
            (round_dir / "scoreboard.json").write_text("{}\n", encoding="utf-8")
            (round_dir / "worker-contract.json").write_text("{}\n", encoding="utf-8")

            payload = build_feedback_distill_payload(
                run_dir=run_dir,
                round_dir=round_dir,
                mutation_payload={
                    "mutation_key": "text_rephrase:demo:intro-tighten-v1",
                    "mutation_id": "text_rephrase:demo:intro-tighten-v1#a001",
                    "attempt": 1,
                },
                decision_payload={
                    "run_id": "demo-run",
                    "round": 1,
                    "decision": "discard",
                },
                baseline_scoreboard=build_scoreboard(
                    train_score=9.0,
                    validation_score=8.0,
                    repo_tasks=baseline_repo_tasks,
                ),
                round_scoreboard=build_scoreboard(
                    train_score=10.0,
                    validation_score=7.5,
                    repo_tasks=round_repo_tasks,
                ),
                distilled_at="2026-03-27T00:00:00+00:00",
            )

        self.assertEqual(payload["feedback_distill_version"], 2)
        self.assertEqual(payload["signal_strength"], "mixed")
        self.assertTrue(payload["repo_prompt_guidance"])
        repo_guidance = payload["repo_prompt_guidance"][0]
        self.assertEqual(repo_guidance["generation_status"], "generated")
        self.assertEqual(repo_guidance["dimension_signals"]["path_contraction"], "weaker")
        self.assertTrue(repo_guidance["prompt_adjustments"])
        self.assertTrue(repo_guidance["evidence_excerpt"])
        aggregate = payload["aggregate_prompt_guidance"]
        self.assertEqual(aggregate["aggregate_direction"], "negative")
        self.assertIn("typer", aggregate["top_regression_repos"])
        self.assertTrue(payload["suggested_adjustments"])

    def test_build_feedback_distill_payload_marks_unsupported_task(self) -> None:
        repo_tasks = [
            build_repo_task(lane_name="validation", repo="repo-a", task="knowledge-base", total_score=8.0),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "demo-run"
            round_dir = run_dir / "rounds" / "round-001"
            round_dir.mkdir(parents=True, exist_ok=True)
            (round_dir / "decision.json").write_text("{}\n", encoding="utf-8")
            (round_dir / "scoreboard.json").write_text("{}\n", encoding="utf-8")
            (round_dir / "worker-contract.json").write_text("{}\n", encoding="utf-8")

            payload = build_feedback_distill_payload(
                run_dir=run_dir,
                round_dir=round_dir,
                mutation_payload={
                    "mutation_key": "k",
                    "mutation_id": "k#a001",
                    "attempt": 1,
                },
                decision_payload={"run_id": "demo-run", "round": 1, "decision": "discard"},
                baseline_scoreboard=build_scoreboard(train_score=9.0, validation_score=8.0, repo_tasks=repo_tasks),
                round_scoreboard=build_scoreboard(train_score=8.5, validation_score=7.5, repo_tasks=repo_tasks),
                distilled_at="2026-03-27T00:00:00+00:00",
            )

        self.assertEqual(payload["repo_prompt_guidance"][0]["generation_status"], "unsupported_task")
        self.assertEqual(payload["aggregate_prompt_guidance"]["generation_status"], "unsupported_task_only")

    def test_build_feedback_distill_payload_guardrail_discard_does_not_emit_positive_repo_guidance(self) -> None:
        baseline_repo_tasks = [
            build_repo_task(lane_name="validation", repo="typer", task="context-routing", total_score=8.0),
        ]
        round_repo_tasks = [
            build_repo_task(
                lane_name="validation",
                repo="typer",
                task="context-routing",
                total_score=8.5,
                needs_improvement="Formatting churn made the route card harder to reuse safely.",
            ),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "demo-run"
            round_dir = run_dir / "rounds" / "round-001"
            round_dir.mkdir(parents=True, exist_ok=True)
            (round_dir / "decision.json").write_text("{}\n", encoding="utf-8")
            (round_dir / "scoreboard.json").write_text("{}\n", encoding="utf-8")
            (round_dir / "worker-contract.json").write_text("{}\n", encoding="utf-8")

            payload = build_feedback_distill_payload(
                run_dir=run_dir,
                round_dir=round_dir,
                mutation_payload={
                    "mutation_key": "k",
                    "mutation_id": "k#a001",
                    "attempt": 1,
                },
                decision_payload={"run_id": "demo-run", "round": 1, "decision": "discard"},
                baseline_scoreboard=build_scoreboard(
                    train_score=9.0,
                    validation_score=8.0,
                    parse_error=0.0,
                    repo_tasks=baseline_repo_tasks,
                ),
                round_scoreboard=build_scoreboard(
                    train_score=9.0,
                    validation_score=8.0,
                    parse_error=0.2,
                    repo_tasks=round_repo_tasks,
                ),
                distilled_at="2026-03-27T00:00:00+00:00",
            )

        repo_guidance = payload["repo_prompt_guidance"][0]
        self.assertEqual(repo_guidance["signal_strength"], "negative")
        self.assertEqual(repo_guidance["dimension_signals"]["path_contraction"], "weaker")
        self.assertTrue(repo_guidance["evidence_excerpt"])
        self.assertTrue(
            any(
                "Formatting churn made the route card harder to reuse safely." in excerpt
                for excerpt in repo_guidance["evidence_excerpt"]
            )
        )
        aggregate = payload["aggregate_prompt_guidance"]
        self.assertEqual(aggregate["aggregate_direction"], "negative")
        self.assertIn("typer", aggregate["top_regression_repos"])
        self.assertFalse(aggregate["top_improvement_repos"])

    def test_upsert_feedback_ledger_replaces_same_round_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "feedback-ledger.jsonl"
            first = build_ledger_entry(
                mutation_key="k",
                round_number=2,
                mutation_id="k#a002",
                decision="discard",
                signal_strength="mixed",
                regression_flags=["validation_drop"],
            )
            second = build_ledger_entry(
                mutation_key="k",
                round_number=2,
                mutation_id="k#a002",
                decision="keep",
                signal_strength="positive",
                aggregate_direction="positive",
                aggregate_suggested_adjustments=["reuse the winning guidance pattern without widening prompt scope"],
            )
            upsert_feedback_ledger_entry(ledger_path, first)
            upsert_feedback_ledger_entry(ledger_path, second)

            entries = load_feedback_ledger(ledger_path)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["decision"], "keep")
        self.assertEqual(entries[0]["feedback_ledger_version"], 2)
        self.assertEqual(entries[0]["aggregate_prompt_guidance"]["aggregate_direction"], "positive")

    def test_feedback_family_priority_tracks_recent_signal(self) -> None:
        ledger = [
            build_ledger_entry(
                mutation_key="positive",
                round_number=1,
                mutation_id="positive#a001",
                decision="keep",
                signal_strength="positive",
                aggregate_direction="positive",
                aggregate_suggested_adjustments=["reuse the winning guidance pattern without widening prompt scope"],
            ),
            build_ledger_entry(
                mutation_key="negative",
                round_number=1,
                mutation_id="negative#a001",
                decision="discard",
                signal_strength="negative",
                regression_flags=["validation_drop"],
            ),
            build_ledger_entry(
                mutation_key="negative",
                round_number=2,
                mutation_id="negative#a002",
                decision="discard",
                signal_strength="negative",
                regression_flags=["validation_drop"],
            ),
        ]

        self.assertEqual(feedback_family_priority(ledger, mutation_key="positive"), (0, "recent_positive_signal"))
        self.assertEqual(feedback_family_priority(ledger, mutation_key="negative"), (5, "sustained_regression_deprioritized"))
        self.assertEqual(feedback_family_priority(ledger, mutation_key="fresh"), (1, "no_feedback_history"))

    def test_build_recent_feedback_excerpt_uses_latest_entries(self) -> None:
        ledger = [
            build_ledger_entry(
                mutation_key="k1",
                round_number=1,
                mutation_id="k1#a001",
                decision="discard",
                signal_strength="mixed",
                regression_flags=["validation_drop"],
            ),
            build_ledger_entry(
                mutation_key="k2",
                round_number=2,
                mutation_id="k2#a001",
                decision="keep",
                signal_strength="positive",
                aggregate_direction="positive",
                aggregate_suggested_adjustments=["reuse the winning guidance pattern without widening prompt scope"],
            ),
        ]

        excerpt = build_recent_feedback_excerpt(ledger)

        self.assertEqual(len(excerpt), 2)
        self.assertIn("round=2", excerpt[0])
        self.assertIn("aggregate=positive", excerpt[0])
        self.assertIn("next=reuse the winning guidance pattern", excerpt[0])
        self.assertIn("flags=validation_drop", excerpt[1])

    def test_latest_aggregate_prompt_guidance_skips_placeholder_entries(self) -> None:
        actionable = build_ledger_entry(
            mutation_key="k1",
            round_number=1,
            mutation_id="k1#a001",
            decision="discard",
            signal_strength="mixed",
            regression_flags=["validation_drop"],
        )
        placeholder = build_ledger_entry(
            mutation_key="k2",
            round_number=2,
            mutation_id="k2#a001",
            decision="discard",
            signal_strength="mixed",
        )
        placeholder["aggregate_prompt_guidance"] = {
            "aggregate_direction": "mixed",
            "aggregate_suggested_adjustments": [],
            "top_regression_repos": [],
            "top_improvement_repos": [],
            "dominant_dimension_signals": [],
            "generation_status": "no_repo_guidance",
        }

        aggregate = latest_aggregate_prompt_guidance([actionable, placeholder])

        self.assertEqual(aggregate["generation_status"], "generated")
        self.assertTrue(aggregate["aggregate_suggested_adjustments"])

    def test_load_feedback_ledger_accepts_legacy_v1_entry(self) -> None:
        legacy_entry = {
            "feedback_distill_version": 1,
            "run_id": "demo-run",
            "round": 1,
            "mutation_key": "legacy",
            "mutation_id": "legacy#a001",
            "attempt": 1,
            "decision": "discard",
            "train_score_delta": 0.5,
            "validation_score_delta": -0.2,
            "parse_error_delta": 0.0,
            "timeout_rate_delta": 0.0,
            "signal_strength": "mixed",
            "regression_flags": ["validation_drop"],
            "dimension_feedback_summary": {"validation_score": "weaker"},
            "suggested_adjustments": ["narrow the next retry to protect validation behavior"],
            "scoreboard_ref": "rounds/round-001/scoreboard.json",
            "decision_ref": "rounds/round-001/decision.json",
            "worker_contract_ref": "rounds/round-001/worker-contract.json",
            "distilled_at": "2026-03-27T00:00:00+00:00",
        }
        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "feedback-ledger.jsonl"
            ledger_path.write_text(json.dumps(legacy_entry) + "\n", encoding="utf-8")
            entries = load_feedback_ledger(ledger_path)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["feedback_distill_version"], 1)


if __name__ == "__main__":
    unittest.main()
