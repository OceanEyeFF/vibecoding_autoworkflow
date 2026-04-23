from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autoresearch_contract import HISTORY_COLUMNS, history_header, load_contract, resolve_p2_contract_target


def build_contract_payload(
    *,
    suite_name: str = "lane.yaml",
    mutable_paths: list[str] | None = None,
    target_task: str | None = None,
    target_prompt_path: str | None = None,
    worker_backend: str | None = None,
    worker_model: str | None = None,
    expected_backend: str | None = None,
    expected_judge_backend: str | None = None,
    retry_policy: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "run_id": "p0-1-demo",
        "label": "P0.1 Demo",
        "objective": "Improve baseline quality.",
        "target_surface": "memory-side",
        "mutable_paths": mutable_paths or ["product/harness/skills"],
        "frozen_paths": ["docs"],
        "train_suites": [suite_name],
        "validation_suites": [suite_name],
        "acceptance_suites": [suite_name],
        "primary_metrics": ["avg_total_score"],
        "guard_metrics": ["parse_error_rate"],
        "qualitative_veto_checks": ["manual_review"],
        "max_rounds": 3,
        "max_candidate_attempts_per_round": 2,
        "timeout_policy": {"seconds": 300},
        "promotion_policy": {"mode": "manual"},
    }
    if target_task is not None:
        payload["target_task"] = target_task
    if target_prompt_path is not None:
        payload["target_prompt_path"] = target_prompt_path
    if worker_backend is not None:
        payload["worker_backend"] = worker_backend
    if worker_model is not None:
        payload["worker_model"] = worker_model
    if expected_backend is not None:
        payload["expected_backend"] = expected_backend
    if expected_judge_backend is not None:
        payload["expected_judge_backend"] = expected_judge_backend
    if retry_policy is not None:
        payload["retry_policy"] = retry_policy
    return payload


class AutoresearchContractTest(unittest.TestCase):
    def test_history_header_matches_fixed_column_order(self) -> None:
        self.assertEqual(history_header(), "\t".join(HISTORY_COLUMNS))

    def test_load_contract_validates_schema_and_suite_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lane.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(build_contract_payload()), encoding="utf-8")

            contract = load_contract(contract_path, repo_root=Path.cwd())
            self.assertEqual(contract.run_id, "p0-1-demo")

    def test_load_contract_rejects_missing_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lane.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            payload = build_contract_payload()
            payload.pop("run_id")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaises(Exception):
                load_contract(contract_path, repo_root=Path.cwd())

    def test_load_contract_rejects_overlapping_mutable_and_frozen_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lane.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            payload = build_contract_payload()
            payload["mutable_paths"] = ["product/harness"]
            payload["frozen_paths"] = ["product/harness/skills"]
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "overlap"):
                load_contract(contract_path, repo_root=Path.cwd())

    def test_load_contract_rejects_missing_suite_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(build_contract_payload()), encoding="utf-8")

            with self.assertRaisesRegex(FileNotFoundError, "Suite manifest not found"):
                load_contract(contract_path, repo_root=Path.cwd())

    def test_load_contract_accepts_optional_p2_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lane.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            prompt_path = root / "toolchain" / "scripts" / "research" / "tasks" / "context-routing-skill-prompt.md"
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text("prompt\n", encoding="utf-8")
            contract_path = root / "contract.json"
            contract_path.write_text(
                json.dumps(
                    build_contract_payload(
                        mutable_paths=["autoresearch/src/tasks/context-routing-skill-prompt.md"],
                        target_task="context-routing-skill",
                        target_prompt_path="autoresearch/src/tasks/context-routing-skill-prompt.md",
                    )
                ),
                encoding="utf-8",
            )

            contract = load_contract(contract_path, repo_root=root)

            self.assertEqual(contract.target_task, "context-routing-skill")
            self.assertEqual(
                contract.target_prompt_path,
                "autoresearch/src/tasks/context-routing-skill-prompt.md",
            )

    def test_load_contract_defaults_worker_backend_expected_backends_and_retry_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lane.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(build_contract_payload()), encoding="utf-8")

            contract = load_contract(contract_path, repo_root=root)

            self.assertEqual(contract.worker_backend, "codex")
            self.assertIsNone(contract.worker_model)
            self.assertEqual(contract.expected_backend, "codex")
            self.assertEqual(contract.expected_judge_backend, "codex")
            self.assertEqual(contract.retry_policy.max_attempts, 3)
            self.assertEqual(contract.retry_policy.backoff_seconds, 3.0)
            self.assertEqual(
                list(contract.retry_policy.retry_on),
                ["timeout", "nonzero_returncode", "empty_output_parse_error", "transient_disconnect"],
            )

    def test_load_contract_accepts_explicit_backend_and_retry_policy_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lane.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract_path = root / "contract.json"
            contract_path.write_text(
                json.dumps(
                    build_contract_payload(
                        worker_backend="claude",
                        worker_model="claude-opus",
                        expected_backend="claude",
                        expected_judge_backend="claude",
                        retry_policy={
                            "max_attempts": 5,
                            "backoff_seconds": 1,
                            "retry_on": ["timeout", "transient_disconnect"],
                        },
                    )
                ),
                encoding="utf-8",
            )

            contract = load_contract(contract_path, repo_root=root)

            self.assertEqual(contract.worker_backend, "claude")
            self.assertEqual(contract.worker_model, "claude-opus")
            self.assertEqual(contract.expected_backend, "claude")
            self.assertEqual(contract.expected_judge_backend, "claude")
            self.assertEqual(contract.retry_policy.max_attempts, 5)
            self.assertEqual(contract.retry_policy.backoff_seconds, 1.0)
            self.assertEqual(list(contract.retry_policy.retry_on), ["timeout", "transient_disconnect"])

    def test_load_contract_rejects_invalid_retry_policy_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lane.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract_path = root / "contract.json"
            contract_path.write_text(
                json.dumps(
                    build_contract_payload(
                        retry_policy={
                            "max_attempts": 2,
                            "backoff_seconds": 1,
                            "retry_on": ["timeout", "not-real"],
                        }
                    )
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(Exception, "retry_on"):
                load_contract(contract_path, repo_root=root)

    def test_resolve_p2_contract_target_rejects_mismatched_prompt_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lane.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract_path = root / "contract.json"
            contract_path.write_text(
                json.dumps(
                    build_contract_payload(
                        mutable_paths=["autoresearch/src/tasks/context-routing-skill-prompt.md"],
                        target_task="context-routing-skill",
                        target_prompt_path="autoresearch/src/tasks/knowledge-base-skill-prompt.md",
                    )
                ),
                encoding="utf-8",
            )

            contract = load_contract(contract_path, repo_root=root)

            with self.assertRaisesRegex(ValueError, "fixed task mapping"):
                resolve_p2_contract_target(contract, repo_root=root)


if __name__ == "__main__":
    unittest.main()
