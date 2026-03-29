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
from autoresearch_contract import history_header, load_contract
from autoresearch_mutation_registry import compute_contract_fingerprint, load_mutation_registry
from exrepo_routing_entry import (
    ROUTING_ENTRY_FALLBACK_MARKER,
    STATUS_USABLE,
    classify_context_routing_repo_skill,
)


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
        "objective": "Baseline aggregation",
        "target_surface": "memory-side",
        "mutable_paths": mutable_paths or ["product/memory-side/skills"],
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
    if target_task is not None:
        payload["target_task"] = target_task
    if target_prompt_path is not None:
        payload["target_prompt_path"] = target_prompt_path
    return payload


def init_p2_prompt_tree(root: Path) -> None:
    prompt_dir = root / "toolchain" / "scripts" / "research" / "tasks"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "context-routing-skill-prompt.md",
        "knowledge-base-skill-prompt.md",
        "task-contract-skill-prompt.md",
        "writeback-cleanup-skill-prompt.md",
    ):
        (prompt_dir / name).write_text(f"{name}\n", encoding="utf-8")


def write_suite_manifest(
    path: Path,
    *,
    task: str,
    backend: str,
    judge_backend: str,
    prompt_file: str | None = None,
    repo: str = ".",
) -> None:
    prompt_line = f"    prompt_file: {prompt_file}\n" if prompt_file is not None else ""
    path.write_text(
        "version: 1\n"
        "defaults:\n"
        f"  backend: {backend}\n"
        f"  judge_backend: {judge_backend}\n"
        "  with_eval: true\n"
        "runs:\n"
        f"  - repo: {repo}\n"
        f"    task: {task}\n"
        f"{prompt_line}",
        encoding="utf-8",
    )


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


def write_history_rows(run_dir: Path, rows: list[dict[str, str]]) -> None:
    lines = [history_header()]
    for row in rows:
        lines.append(
            "\t".join(
                [
                    row["round"],
                    row["kind"],
                    row["base_sha"],
                    row["candidate_sha"],
                    row["train_score"],
                    row["validation_score"],
                    row["train_parse_error_rate"],
                    row["validation_parse_error_rate"],
                    row["decision"],
                    row["notes"],
                ]
            )
        )
    (run_dir / "history.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")


class RunAutoresearchTest(unittest.TestCase):
    def test_classify_context_routing_repo_skill_reports_usable_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exrepo = root / ".exrepos" / "fmt"
            skill_dir = exrepo / ".agents" / "skills" / "context-routing-skill"
            skill_dir.mkdir(parents=True, exist_ok=True)
            (exrepo / "product" / "memory-side" / "skills" / "context-routing-skill").mkdir(parents=True, exist_ok=True)
            (exrepo / "docs" / "knowledge" / "memory-side").mkdir(parents=True, exist_ok=True)
            (exrepo / "product" / "memory-side" / "skills" / "context-routing-skill" / "SKILL.md").write_text(
                "canonical\n",
                encoding="utf-8",
            )
            (exrepo / "product" / "memory-side" / "skills" / "context-routing-skill" / "references").mkdir(
                parents=True,
                exist_ok=True,
            )
            (exrepo / "product" / "memory-side" / "skills" / "context-routing-skill" / "references" / "entrypoints.md").write_text(
                "entrypoints\n",
                encoding="utf-8",
            )
            (exrepo / "docs" / "knowledge" / "memory-side" / "overview.md").write_text("overview\n", encoding="utf-8")
            (skill_dir / "SKILL.md").write_text(
                "## Canonical Sources\n"
                "1. `product/memory-side/skills/context-routing-skill/SKILL.md`\n"
                "2. `product/memory-side/skills/context-routing-skill/references/entrypoints.md`\n"
                "3. `docs/knowledge/memory-side/overview.md`\n",
                encoding="utf-8",
            )

            capability = classify_context_routing_repo_skill(exrepo, repo_root=root)

            self.assertIsNotNone(capability)
            self.assertEqual(capability["status"], STATUS_USABLE)
            self.assertEqual(capability["missing_paths"], [])

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

    def test_init_accepts_valid_p2_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            init_p2_prompt_tree(root)
            write_suite_manifest(root / "train.yaml", task="context-routing", backend="codex", judge_backend="codex")
            write_suite_manifest(root / "validation.yaml", task="context-routing", backend="codex", judge_backend="codex")
            write_suite_manifest(root / "acceptance.yaml", task="context-routing", backend="codex", judge_backend="codex")
            contract = build_contract_payload(
                "train.yaml",
                "validation.yaml",
                "acceptance.yaml",
                mutable_paths=["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
                target_task="context-routing-skill",
                target_prompt_path="toolchain/scripts/research/tasks/context-routing-skill-prompt.md",
            )
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                exit_code = run_autoresearch.main(["init", "--contract", str(contract_path)])

            self.assertEqual(exit_code, 0)

    def test_init_rejects_p2_suite_backend_not_codex(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            init_p2_prompt_tree(root)
            write_suite_manifest(root / "train.yaml", task="context-routing", backend="claude", judge_backend="codex")
            write_suite_manifest(root / "validation.yaml", task="context-routing", backend="codex", judge_backend="codex")
            write_suite_manifest(root / "acceptance.yaml", task="context-routing", backend="codex", judge_backend="codex")
            contract = build_contract_payload(
                "train.yaml",
                "validation.yaml",
                "acceptance.yaml",
                mutable_paths=["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
                target_task="context-routing-skill",
                target_prompt_path="toolchain/scripts/research/tasks/context-routing-skill-prompt.md",
            )
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                exit_code = run_autoresearch.main(["init", "--contract", str(contract_path)])

            self.assertEqual(exit_code, 1)

    def test_init_rejects_p2_suite_task_outside_target_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            init_p2_prompt_tree(root)
            write_suite_manifest(root / "train.yaml", task="knowledge-base", backend="codex", judge_backend="codex")
            write_suite_manifest(root / "validation.yaml", task="context-routing", backend="codex", judge_backend="codex")
            write_suite_manifest(root / "acceptance.yaml", task="context-routing", backend="codex", judge_backend="codex")
            contract = build_contract_payload(
                "train.yaml",
                "validation.yaml",
                "acceptance.yaml",
                mutable_paths=["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
                target_task="context-routing-skill",
                target_prompt_path="toolchain/scripts/research/tasks/context-routing-skill-prompt.md",
            )
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                exit_code = run_autoresearch.main(["init", "--contract", str(contract_path)])

            self.assertEqual(exit_code, 1)

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

    def test_baseline_rejects_invalid_exrepo_routing_entry_without_fallback_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            init_p2_prompt_tree(root)
            exrepo = root / ".exrepos" / "typer"
            skill_dir = exrepo / ".agents" / "skills" / "context-routing-skill"
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_path = skill_dir / "SKILL.md"
            skill_path.write_text(
                "## Canonical Sources\n"
                "1. `product/memory-side/skills/context-routing-skill/SKILL.md`\n"
                "2. `docs/knowledge/memory-side/overview.md`\n",
                encoding="utf-8",
            )
            write_suite_manifest(
                root / "train.yaml",
                task="context-routing",
                backend="codex",
                judge_backend="codex",
                repo=str(exrepo),
            )
            write_suite_manifest(
                root / "validation.yaml",
                task="context-routing",
                backend="codex",
                judge_backend="codex",
                repo=str(exrepo),
            )
            write_suite_manifest(
                root / "acceptance.yaml",
                task="context-routing",
                backend="codex",
                judge_backend="codex",
                repo=str(exrepo),
            )
            contract = build_contract_payload(
                "train.yaml",
                "validation.yaml",
                "acceptance.yaml",
                mutable_paths=["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
                target_task="context-routing-skill",
                target_prompt_path="toolchain/scripts/research/tasks/context-routing-skill-prompt.md",
            )
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ), mock.patch.object(run_autoresearch, "run_skill_suite_main") as mocked_runner:
                stderr = io.StringIO()
                with mock.patch("sys.stderr", stderr):
                    exit_code = run_autoresearch.main(["baseline", "--contract", str(contract_path)])

            self.assertEqual(exit_code, 1)
            mocked_runner.assert_not_called()
            self.assertIn("invalid_repo_skill_wrapper", stderr.getvalue())
            run_dir = root / ".autoworkflow" / "demo-run"
            report = json.loads((run_dir / "routing-entry-capability.json").read_text(encoding="utf-8"))
            self.assertFalse(report["prompt_allows_repo_skill_fallback"])
            self.assertEqual(report["capabilities"][0]["status"], "invalid_repo_skill_wrapper")

    def test_baseline_allows_reported_exrepo_routing_issues_when_prompt_has_fallback_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            init_p2_prompt_tree(root)
            prompt_path = root / "toolchain" / "scripts" / "research" / "tasks" / "context-routing-skill-prompt.md"
            prompt_path.write_text(
                ROUTING_ENTRY_FALLBACK_MARKER + "\n"
                "Use repo-local skill conditionally.\n",
                encoding="utf-8",
            )
            exrepo = root / ".exrepos" / "trackers"
            exrepo.mkdir(parents=True, exist_ok=True)
            write_suite_manifest(
                root / "train.yaml",
                task="context-routing",
                backend="codex",
                judge_backend="codex",
                repo=str(exrepo),
            )
            write_suite_manifest(
                root / "validation.yaml",
                task="context-routing",
                backend="codex",
                judge_backend="codex",
                repo=str(exrepo),
            )
            write_suite_manifest(
                root / "acceptance.yaml",
                task="context-routing",
                backend="codex",
                judge_backend="codex",
                repo=str(exrepo),
            )
            contract = build_contract_payload(
                "train.yaml",
                "validation.yaml",
                "acceptance.yaml",
                mutable_paths=["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
                target_task="context-routing-skill",
                target_prompt_path="toolchain/scripts/research/tasks/context-routing-skill-prompt.md",
            )
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
                exit_code = run_autoresearch.main(["baseline", "--contract", str(contract_path)])

            self.assertEqual(exit_code, 0)
            run_dir = root / ".autoworkflow" / "demo-run"
            report = json.loads((run_dir / "routing-entry-capability.json").read_text(encoding="utf-8"))
            self.assertTrue(report["prompt_allows_repo_skill_fallback"])
            self.assertEqual(report["capabilities"][0]["status"], "missing_repo_skill")

    def test_baseline_preflight_ignores_acceptance_only_exrepo_capability_issues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            init_p2_prompt_tree(root)
            train_repo = root / ".exrepos" / "fmt"
            train_skill_dir = train_repo / ".agents" / "skills" / "context-routing-skill"
            train_skill_dir.mkdir(parents=True, exist_ok=True)
            (train_repo / "product" / "memory-side" / "skills" / "context-routing-skill").mkdir(parents=True, exist_ok=True)
            (train_repo / "product" / "memory-side" / "skills" / "context-routing-skill" / "SKILL.md").write_text(
                "canonical\n",
                encoding="utf-8",
            )
            (train_repo / "docs" / "knowledge" / "memory-side").mkdir(parents=True, exist_ok=True)
            (train_skill_dir / "SKILL.md").write_text(
                "## Canonical Sources\n"
                "1. `product/memory-side/skills/context-routing-skill/SKILL.md`\n"
                "2. `docs/knowledge/memory-side/`\n",
                encoding="utf-8",
            )

            acceptance_repo = root / ".exrepos" / "JUCE"
            acceptance_repo.mkdir(parents=True, exist_ok=True)

            write_suite_manifest(
                root / "train.yaml",
                task="context-routing",
                backend="codex",
                judge_backend="codex",
                repo=str(train_repo),
            )
            write_suite_manifest(
                root / "validation.yaml",
                task="context-routing",
                backend="codex",
                judge_backend="codex",
                repo=str(train_repo),
            )
            write_suite_manifest(
                root / "acceptance.yaml",
                task="context-routing",
                backend="codex",
                judge_backend="codex",
                repo=str(acceptance_repo),
            )
            contract = build_contract_payload(
                "train.yaml",
                "validation.yaml",
                "acceptance.yaml",
                mutable_paths=["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
                target_task="context-routing-skill",
                target_prompt_path="toolchain/scripts/research/tasks/context-routing-skill-prompt.md",
            )
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
                exit_code = run_autoresearch.main(["baseline", "--contract", str(contract_path)])

            self.assertEqual(exit_code, 0)
            run_dir = root / ".autoworkflow" / "demo-run"
            report = json.loads((run_dir / "routing-entry-capability.json").read_text(encoding="utf-8"))
            self.assertEqual([item["repo"] for item in report["capabilities"]], ["fmt"])

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

    def test_discard_round_allows_p2_recovery_even_if_suite_manifests_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            init_p2_prompt_tree(root)
            write_suite_manifest(root / "train.yaml", task="context-routing", backend="codex", judge_backend="codex")
            write_suite_manifest(root / "validation.yaml", task="context-routing", backend="codex", judge_backend="codex")
            write_suite_manifest(root / "acceptance.yaml", task="context-routing", backend="codex", judge_backend="codex")
            contract = build_contract_payload(
                "train.yaml",
                "validation.yaml",
                "acceptance.yaml",
                mutable_paths=["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
                target_task="context-routing-skill",
                target_prompt_path="toolchain/scripts/research/tasks/context-routing-skill-prompt.md",
            )
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            scoreboard = {
                "run_id": "demo-run",
                "generated_at": "2026-03-26T00:00:00+00:00",
                "baseline_sha": current_head_sha(root),
                "rounds_completed": 0,
                "best_round": 0,
                "lanes": [
                    {"lane_name": "train", "avg_total_score": 9.0},
                    {"lane_name": "validation", "avg_total_score": 8.0},
                ],
                "repo_tasks": [],
            }

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                self.assertEqual(run_autoresearch.main(["init", "--contract", str(contract_path)]), 0)
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
                            "target_paths": ["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
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
                self.assertEqual(
                    run_autoresearch.main(["prepare-round", "--contract", str(contract_path), "--mutation-key", mutation_key]),
                    0,
                )
                candidate_worktree = run_dir / "worktrees" / "round-001"
                write_suite_manifest(root / "train.yaml", task="context-routing", backend="claude", judge_backend="claude")

                discard_code = run_autoresearch.main(["discard-round", "--contract", str(contract_path)])

            self.assertEqual(discard_code, 0)
            runtime = json.loads((root / ".autoworkflow" / "demo-run" / "runtime.json").read_text(encoding="utf-8"))
            self.assertIsNone(runtime["active_round"])
            self.assertFalse(candidate_worktree.exists())

    def test_cleanup_round_allows_p2_recovery_even_if_suite_manifests_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            init_p2_prompt_tree(root)
            write_suite_manifest(root / "train.yaml", task="context-routing", backend="codex", judge_backend="codex")
            write_suite_manifest(root / "validation.yaml", task="context-routing", backend="codex", judge_backend="codex")
            write_suite_manifest(root / "acceptance.yaml", task="context-routing", backend="codex", judge_backend="codex")
            contract = build_contract_payload(
                "train.yaml",
                "validation.yaml",
                "acceptance.yaml",
                mutable_paths=["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
                target_task="context-routing-skill",
                target_prompt_path="toolchain/scripts/research/tasks/context-routing-skill-prompt.md",
            )
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            scoreboard = {
                "run_id": "demo-run",
                "generated_at": "2026-03-26T00:00:00+00:00",
                "baseline_sha": current_head_sha(root),
                "rounds_completed": 0,
                "best_round": 0,
                "lanes": [
                    {"lane_name": "train", "avg_total_score": 9.0},
                    {"lane_name": "validation", "avg_total_score": 8.0},
                ],
                "repo_tasks": [],
            }

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                self.assertEqual(run_autoresearch.main(["init", "--contract", str(contract_path)]), 0)
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
                            "target_paths": ["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
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
                self.assertEqual(
                    run_autoresearch.main(["prepare-round", "--contract", str(contract_path), "--mutation-key", mutation_key]),
                    0,
                )
                candidate_worktree = run_dir / "worktrees" / "round-001"
                write_suite_manifest(root / "train.yaml", task="context-routing", backend="claude", judge_backend="claude")

                cleanup_code = run_autoresearch.main(["cleanup-round", "--contract", str(contract_path)])

            self.assertEqual(cleanup_code, 0)
            runtime = json.loads((root / ".autoworkflow" / "demo-run" / "runtime.json").read_text(encoding="utf-8"))
            self.assertIsNone(runtime["active_round"])
            self.assertFalse(candidate_worktree.exists())

    def test_decide_round_skips_p2_preflight_when_replay_is_not_needed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            init_p2_prompt_tree(root)
            write_suite_manifest(root / "train.yaml", task="context-routing", backend="claude", judge_backend="claude")
            write_suite_manifest(root / "validation.yaml", task="context-routing", backend="claude", judge_backend="claude")
            write_suite_manifest(root / "acceptance.yaml", task="context-routing", backend="claude", judge_backend="claude")
            contract = build_contract_payload(
                "train.yaml",
                "validation.yaml",
                "acceptance.yaml",
                mutable_paths=["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
                target_task="context-routing-skill",
                target_prompt_path="toolchain/scripts/research/tasks/context-routing-skill-prompt.md",
            )
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")

            fake_round_manager = mock.Mock()
            fake_round_manager.decide_round.return_value = {
                "decision": {"round": 1, "decision": "keep", "candidate_sha": "abc123"}
            }
            stdout = io.StringIO()

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ), mock.patch.object(run_autoresearch, "build_round_manager", return_value=fake_round_manager), mock.patch(
                "sys.stdout", stdout
            ):
                exit_code = run_autoresearch.main(["decide-round", "--contract", str(contract_path)])

            self.assertEqual(exit_code, 0)
            fake_round_manager.decide_round.assert_called_once()
            self.assertIn("decided_round: 1", stdout.getvalue())

    def test_promote_round_enforces_p2_guard_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            init_p2_prompt_tree(root)
            write_suite_manifest(root / "train.yaml", task="context-routing", backend="claude", judge_backend="claude")
            write_suite_manifest(root / "validation.yaml", task="context-routing", backend="claude", judge_backend="claude")
            write_suite_manifest(root / "acceptance.yaml", task="context-routing", backend="claude", judge_backend="claude")
            contract = build_contract_payload(
                "train.yaml",
                "validation.yaml",
                "acceptance.yaml",
                mutable_paths=["toolchain/scripts/research/tasks/context-routing-skill-prompt.md"],
                target_task="context-routing-skill",
                target_prompt_path="toolchain/scripts/research/tasks/context-routing-skill-prompt.md",
            )
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")

            fake_worktree_manager = mock.Mock()
            stderr = io.StringIO()

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ), mock.patch.object(run_autoresearch, "build_worktree_manager", return_value=fake_worktree_manager), mock.patch(
                "sys.stderr", stderr
            ):
                exit_code = run_autoresearch.main(["promote-round", "--contract", str(contract_path)])

            self.assertEqual(exit_code, 1)
            self.assertIn("P2 suite", stderr.getvalue())
            fake_worktree_manager.promote_round.assert_not_called()

    def test_prepare_round_reconciles_registry_and_worker_contract_for_active_round(self) -> None:
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
                "lanes": [
                    {"lane_name": "train", "avg_total_score": 9.0},
                    {"lane_name": "validation", "avg_total_score": 8.0},
                ],
                "repo_tasks": [],
            }

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                self.assertEqual(run_autoresearch.main(["init", "--contract", str(contract_path)]), 0)
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
                self.assertEqual(
                    run_autoresearch.main(["prepare-round", "--contract", str(contract_path), "--mutation-key", mutation_key]),
                    0,
                )

                registry_after = json.loads((run_dir / "mutation-registry.json").read_text(encoding="utf-8"))
                registry_after["entries"][0]["attempts"] = 0
                registry_after["entries"][0]["last_selected_round"] = None
                (run_dir / "mutation-registry.json").write_text(
                    json.dumps(registry_after, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )
                worker_path = run_dir / "rounds" / "round-001" / "worker-contract.json"
                worker_path.unlink()
                (run_dir / "runtime.json").unlink()

                prepare_code = run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])

            self.assertEqual(prepare_code, 1)
            repaired_registry = json.loads((run_dir / "mutation-registry.json").read_text(encoding="utf-8"))
            self.assertEqual(repaired_registry["entries"][0]["attempts"], 1)
            self.assertEqual(repaired_registry["entries"][0]["last_selected_round"], 1)
            self.assertTrue(worker_path.is_file())
            runtime = json.loads((run_dir / "runtime.json").read_text(encoding="utf-8"))
            self.assertEqual(runtime["active_round"], 1)
            self.assertEqual(runtime["active_candidate_branch"], "candidate/demo-run/r001")

    def test_prepare_round_recovery_fails_closed_when_registry_missing(self) -> None:
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
                "lanes": [
                    {"lane_name": "train", "avg_total_score": 9.0},
                    {"lane_name": "validation", "avg_total_score": 8.0},
                ],
                "repo_tasks": [],
            }

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                self.assertEqual(run_autoresearch.main(["init", "--contract", str(contract_path)]), 0)
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
                self.assertEqual(
                    run_autoresearch.main(["prepare-round", "--contract", str(contract_path), "--mutation-key", mutation_key]),
                    0,
                )

                (run_dir / "mutation-registry.json").unlink()
                prepare_code = run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])

            self.assertEqual(prepare_code, 1)
            self.assertFalse((run_dir / "mutation-registry.json").exists())

    def test_prepare_round_worker_contract_includes_recent_feedback_excerpt(self) -> None:
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
                "rounds_completed": 1,
                "best_round": 1,
                "lanes": [
                    {"lane_name": "train", "avg_total_score": 9.0},
                    {"lane_name": "validation", "avg_total_score": 8.0},
                ],
                "repo_tasks": [],
            }
            feedback_entry = {
                "feedback_distill_version": 1,
                "run_id": "demo-run",
                "round": 1,
                "mutation_key": "seed",
                "mutation_id": "seed#a001",
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

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                self.assertEqual(run_autoresearch.main(["init", "--contract", str(contract_path)]), 0)
                run_dir = root / ".autoworkflow" / "demo-run"
                (run_dir / "scoreboard.json").write_text(json.dumps(scoreboard), encoding="utf-8")
                (run_dir / "feedback-ledger.jsonl").write_text(json.dumps(feedback_entry) + "\n", encoding="utf-8")

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

                self.assertEqual(
                    run_autoresearch.main(["prepare-round", "--contract", str(contract_path), "--mutation-key", mutation_key]),
                    0,
                )

            worker_payload = json.loads(
                (root / ".autoworkflow" / "demo-run" / "rounds" / "round-001" / "worker-contract.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(worker_payload["recent_feedback_excerpt"])
            self.assertIn("validation_drop", worker_payload["recent_feedback_excerpt"][0])

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

    def test_prepare_round_stops_second_prepare_after_first_discard_when_no_keep_exists(self) -> None:
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
                stderr = io.StringIO()
                with mock.patch("sys.stderr", stderr):
                    second_prepare = run_autoresearch.main(
                        ["prepare-round", "--contract", str(contract_path), "--mutation-key", mutation_key]
                    )

            self.assertEqual(init_code, 0)
            self.assertEqual(first_prepare, 0)
            self.assertEqual(first_discard, 0)
            self.assertEqual(second_prepare, 1)
            self.assertIn("all active mutation families have been tried at least once", stderr.getvalue())
            registry_after = json.loads((root / ".autoworkflow" / "demo-run" / "mutation-registry.json").read_text(encoding="utf-8"))
            self.assertEqual(registry_after["entries"][0]["attempts"], 1)
            self.assertEqual(registry_after["entries"][0]["last_selected_round"], 1)

    def test_prepare_round_stop_reason_triggers_before_selector_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
            contract_path = root / "contract.json"
            contract["max_candidate_attempts_per_round"] = 2
            contract_path.write_text(json.dumps(contract), encoding="utf-8")

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                self.assertEqual(run_autoresearch.main(["init", "--contract", str(contract_path)]), 0)
                run_dir = root / ".autoworkflow" / "demo-run"
                scoreboard_payload = {
                    "run_id": "demo-run",
                    "generated_at": "2026-03-26T00:00:00+00:00",
                    "baseline_sha": current_head_sha(root),
                    "rounds_completed": 0,
                    "best_round": 0,
                    "lanes": [],
                    "repo_tasks": [],
                }
                (run_dir / "scoreboard.json").write_text(json.dumps(scoreboard_payload), encoding="utf-8")
                registry = {
                    "run_id": "demo-run",
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(load_contract(contract_path, repo_root=root)),
                    "entries": [
                        {
                            "mutation_key": "text_rephrase:demo:stop-gate",
                            "kind": "text_rephrase",
                            "status": "active",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "tighten",
                            "expected_effect": {
                                "hypothesis": "Improve train score",
                                "primary_metrics": ["avg_total_score"],
                                "guard_metrics": ["parse_error_rate"],
                            },
                            "guardrails": {
                                "require_non_empty_diff": True,
                                "max_files_touched": 1,
                                "extra_frozen_paths": [],
                            },
                            "origin": {"type": "manual_seed", "ref": "test"},
                            "attempts": 1,
                            "last_selected_round": 1,
                            "last_decision": "discard",
                        }
                    ],
                }
                (run_dir / "mutation-registry.json").write_text(json.dumps(registry, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
                stderr = io.StringIO()
                with mock.patch("sys.stderr", stderr), mock.patch.object(
                    run_autoresearch, "select_next_mutation_entry", side_effect=AssertionError("selector should not run")
                ):
                    code = run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])

        self.assertEqual(code, 1)
        stderr_value = stderr.getvalue()
        stop_message = (
            "Stop gate triggered: all active mutation families have been tried at least once "
            "and the run has no final keep."
        )
        self.assertIn(stop_message, stderr_value)
        self.assertNotIn("No selectable mutation entries found", stderr_value)

    def test_prepare_round_reports_selector_error_when_no_active_entries(self) -> None:
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
                self.assertEqual(run_autoresearch.main(["init", "--contract", str(contract_path)]), 0)
                run_dir = root / ".autoworkflow" / "demo-run"
                scoreboard_payload = {
                    "run_id": "demo-run",
                    "generated_at": "2026-03-26T00:00:00+00:00",
                    "baseline_sha": current_head_sha(root),
                    "rounds_completed": 0,
                    "best_round": 0,
                    "lanes": [],
                    "repo_tasks": [],
                }
                (run_dir / "scoreboard.json").write_text(json.dumps(scoreboard_payload), encoding="utf-8")
                registry_payload = {
                    "run_id": "demo-run",
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(
                        load_contract(contract_path, repo_root=root)
                    ),
                    "entries": [
                        {
                            "mutation_key": "text_rephrase:demo:inactive",
                            "kind": "text_rephrase",
                            "status": "disabled",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "inactive entry only",
                            "expected_effect": {
                                "hypothesis": "No active work",
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
                stderr = io.StringIO()
                with mock.patch("sys.stderr", stderr):
                    code = run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])

        self.assertEqual(code, 1)
        stderr_value = stderr.getvalue()
        self.assertIn("No selectable mutation entries found", stderr_value)
        self.assertNotIn("Stop gate triggered", stderr_value)

    def test_prepare_round_stops_after_three_completed_rounds_without_new_validation_champion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            baseline_sha = current_head_sha(root)

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                self.assertEqual(run_autoresearch.main(["init", "--contract", str(contract_path)]), 0)
                run_dir = root / ".autoworkflow" / "demo-run"
                (run_dir / "scoreboard.json").write_text(
                    json.dumps(
                        {
                            "run_id": "demo-run",
                            "generated_at": "2026-03-26T00:00:00+00:00",
                            "baseline_sha": baseline_sha,
                            "rounds_completed": 3,
                            "best_round": 0,
                            "lanes": [],
                            "repo_tasks": [],
                        }
                    ),
                    encoding="utf-8",
                )
                write_history_rows(
                    run_dir,
                    [
                        {
                            "round": "0",
                            "kind": "baseline",
                            "base_sha": baseline_sha,
                            "candidate_sha": "-",
                            "train_score": "9.000000",
                            "validation_score": "8.000000",
                            "train_parse_error_rate": "0.000000",
                            "validation_parse_error_rate": "0.000000",
                            "decision": "baseline",
                            "notes": "",
                        },
                        {
                            "round": "1",
                            "kind": "text_rephrase",
                            "base_sha": baseline_sha,
                            "candidate_sha": "sha-round-1",
                            "train_score": "10.000000",
                            "validation_score": "8.000000",
                            "train_parse_error_rate": "0.000000",
                            "validation_parse_error_rate": "0.000000",
                            "decision": "keep",
                            "notes": "mutation_id=a",
                        },
                        {
                            "round": "2",
                            "kind": "text_rephrase",
                            "base_sha": "sha-round-1",
                            "candidate_sha": "sha-round-2",
                            "train_score": "9.000000",
                            "validation_score": "7.500000",
                            "train_parse_error_rate": "0.000000",
                            "validation_parse_error_rate": "0.000000",
                            "decision": "discard",
                            "notes": "mutation_id=b",
                        },
                        {
                            "round": "3",
                            "kind": "instruction_reorder",
                            "base_sha": "sha-round-1",
                            "candidate_sha": "sha-round-3",
                            "train_score": "9.500000",
                            "validation_score": "8.000000",
                            "train_parse_error_rate": "0.000000",
                            "validation_parse_error_rate": "0.000000",
                            "decision": "discard",
                            "notes": "mutation_id=c",
                        },
                    ],
                )
                stderr = io.StringIO()
                with mock.patch("sys.stderr", stderr):
                    prepare_code = run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])

            self.assertEqual(prepare_code, 1)
            self.assertIn("3 consecutive completed rounds without a new validation champion", stderr.getvalue())

    def test_prepare_round_stops_when_all_active_entries_tried_once_without_keep(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            baseline_sha = current_head_sha(root)

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                self.assertEqual(run_autoresearch.main(["init", "--contract", str(contract_path)]), 0)
                run_dir = root / ".autoworkflow" / "demo-run"
                (run_dir / "scoreboard.json").write_text(
                    json.dumps(
                        {
                            "run_id": "demo-run",
                            "generated_at": "2026-03-26T00:00:00+00:00",
                            "baseline_sha": baseline_sha,
                            "rounds_completed": 1,
                            "best_round": 0,
                            "lanes": [],
                            "repo_tasks": [],
                        }
                    ),
                    encoding="utf-8",
                )
                write_history_rows(
                    run_dir,
                    [
                        {
                            "round": "0",
                            "kind": "baseline",
                            "base_sha": baseline_sha,
                            "candidate_sha": "-",
                            "train_score": "9.000000",
                            "validation_score": "8.000000",
                            "train_parse_error_rate": "0.000000",
                            "validation_parse_error_rate": "0.000000",
                            "decision": "baseline",
                            "notes": "",
                        },
                        {
                            "round": "1",
                            "kind": "text_rephrase",
                            "base_sha": baseline_sha,
                            "candidate_sha": "sha-round-1",
                            "train_score": "9.500000",
                            "validation_score": "7.500000",
                            "train_parse_error_rate": "0.000000",
                            "validation_parse_error_rate": "0.000000",
                            "decision": "discard",
                            "notes": "mutation_id=a",
                        },
                    ],
                )
                contract_obj = load_contract(contract_path, repo_root=root)
                registry_payload = {
                    "run_id": contract_obj.run_id,
                    "registry_version": 1,
                    "contract_fingerprint": compute_contract_fingerprint(contract_obj),
                    "entries": [
                        {
                            "mutation_key": "text_rephrase:demo:intro-tighten-v1",
                            "kind": "text_rephrase",
                            "status": "active",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "Tighten wording.",
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
                            "attempts": 1,
                            "last_selected_round": 1,
                            "last_decision": "discard",
                        },
                        {
                            "mutation_key": "instruction_reorder:demo:sections-v1",
                            "kind": "instruction_reorder",
                            "status": "active",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "Reorder sections.",
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
                            "attempts": 1,
                            "last_selected_round": 1,
                            "last_decision": "discard",
                        },
                    ],
                }
                (run_dir / "mutation-registry.json").write_text(
                    json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )
                stderr = io.StringIO()
                with mock.patch("sys.stderr", stderr):
                    prepare_code = run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])

            self.assertEqual(prepare_code, 1)
            self.assertIn("all active mutation families have been tried at least once", stderr.getvalue())

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

    def test_prepare_round_auto_select_skips_pending_duplicate_fingerprint_with_runtime_lookup_only(self) -> None:
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
                registry_path = run_dir / "mutation-registry.json"
                registry_path.write_text(
                    json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )
                registry = load_mutation_registry(registry_path, contract=contract_obj, repo_root=root)
                pending_round_dir = run_dir / "rounds" / "round-009"
                pending_round_dir.mkdir(parents=True, exist_ok=True)
                (pending_round_dir / "mutation.json").write_text(
                    json.dumps({"fingerprint": registry.entries[0]["fingerprint"]}, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )

                with mock.patch.object(
                    run_autoresearch,
                    "read_runtime_if_present",
                    return_value={"active_round": 9},
                ), mock.patch.object(run_autoresearch.WorktreeManager, "next_round_number", return_value=1):
                    prepare_code = run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])

            self.assertEqual(init_code, 0)
            self.assertEqual(prepare_code, 0)
            round_mutation = json.loads(
                (root / ".autoworkflow" / "demo-run" / "rounds" / "round-001" / "mutation.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(round_mutation["mutation_key"], "text_rephrase:demo:second")

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
            self.assertIn("all active mutation families have been tried at least once", stderr.getvalue())

    def test_prepare_round_missing_registry_does_not_initialize_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            run_dir = root / ".autoworkflow" / "demo-run"
            run_dir.mkdir(parents=True, exist_ok=True)
            scoreboard = {
                "run_id": "demo-run",
                "generated_at": "2026-03-26T00:00:00+00:00",
                "baseline_sha": current_head_sha(root),
                "rounds_completed": 0,
                "best_round": 0,
                "lanes": [],
                "repo_tasks": [],
            }
            (run_dir / "scoreboard.json").write_text(json.dumps(scoreboard), encoding="utf-8")

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                prepare_code = run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])

            self.assertEqual(prepare_code, 1)
            self.assertFalse((run_dir / "runtime.json").exists())

    def test_prepare_round_invalid_mutation_key_does_not_initialize_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_git_repo(root)
            (root / "train.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "validation.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            (root / "acceptance.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
            contract = build_contract_payload("train.yaml", "validation.yaml", "acceptance.yaml")
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            run_dir = root / ".autoworkflow" / "demo-run"
            run_dir.mkdir(parents=True, exist_ok=True)
            scoreboard = {
                "run_id": "demo-run",
                "generated_at": "2026-03-26T00:00:00+00:00",
                "baseline_sha": current_head_sha(root),
                "rounds_completed": 0,
                "best_round": 0,
                "lanes": [],
                "repo_tasks": [],
            }
            (run_dir / "scoreboard.json").write_text(json.dumps(scoreboard), encoding="utf-8")
            registry_payload = {
                "run_id": "demo-run",
                "registry_version": 1,
                "contract_fingerprint": compute_contract_fingerprint(load_contract(contract_path, repo_root=root)),
                "entries": [
                    {
                        "mutation_key": "text_rephrase:demo:available",
                        "kind": "text_rephrase",
                        "status": "active",
                        "target_paths": ["product/memory-side/skills"],
                        "allowed_actions": ["edit"],
                        "instruction_seed": "Available mutation.",
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

            with mock.patch.object(run_autoresearch, "AUTORESEARCH_ROOT", root / ".autoworkflow"), mock.patch.object(
                run_autoresearch, "REPO_ROOT", root
            ):
                prepare_code = run_autoresearch.main(
                    ["prepare-round", "--contract", str(contract_path), "--mutation-key", "text_rephrase:demo:missing"]
                )

            self.assertEqual(prepare_code, 1)
            self.assertFalse((run_dir / "runtime.json").exists())

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

    def test_prepare_round_auto_select_skips_pending_duplicate_fingerprint_with_active_candidate_identity(self) -> None:
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
                            "mutation_key": "text_rephrase:demo:duplicate",
                            "kind": "text_rephrase",
                            "status": "active",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "Duplicate mutation.",
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
                            "mutation_key": "text_rephrase:demo:fresh",
                            "kind": "text_rephrase",
                            "status": "active",
                            "target_paths": ["product/memory-side/skills"],
                            "allowed_actions": ["edit"],
                            "instruction_seed": "Fresh mutation.",
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
                registry_path = run_dir / "mutation-registry.json"
                registry_path.write_text(
                    json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )
                registry = load_mutation_registry(registry_path, contract=contract_obj, repo_root=root)
                pending_round_dir = run_dir / "rounds" / "round-009"
                pending_round_dir.mkdir(parents=True, exist_ok=True)
                (pending_round_dir / "mutation.json").write_text(
                    json.dumps({"fingerprint": registry.entries[0]["fingerprint"]}, ensure_ascii=True) + "\n",
                    encoding="utf-8",
                )

                with mock.patch.object(
                    run_autoresearch,
                    "read_runtime_if_present",
                    return_value={
                        "active_round": 9,
                        "active_candidate_branch": "candidate/demo-run/r009",
                        "active_candidate_worktree": str(run_dir / "worktrees" / "round-009"),
                    },
                ), mock.patch.object(run_autoresearch.WorktreeManager, "next_round_number", return_value=1):
                    prepare_code = run_autoresearch.main(["prepare-round", "--contract", str(contract_path)])

            self.assertEqual(init_code, 0)
            self.assertEqual(prepare_code, 0)
            round_mutation = json.loads(
                (root / ".autoworkflow" / "demo-run" / "rounds" / "round-001" / "mutation.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(round_mutation["mutation_key"], "text_rephrase:demo:fresh")


if __name__ == "__main__":
    unittest.main()
