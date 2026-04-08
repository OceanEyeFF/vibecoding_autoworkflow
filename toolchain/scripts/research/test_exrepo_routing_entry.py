from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from exrepo_routing_entry import (  # noqa: E402
    ROUTING_ENTRY_FALLBACK_MARKER,
    STATUS_INVALID,
    STATUS_MISSING,
    STATUS_USABLE,
    classify_context_routing_repo_skill,
    collect_context_routing_suite_repo_skill_report,
    prompt_allows_exrepo_routing_fallback,
)


def write_skill_wrapper(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class ExrepoRoutingEntryTest(unittest.TestCase):
    def test_classify_returns_usable_repo_skill_when_canonical_paths_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / ".exrepos" / "fmt"
            (repo / "product" / "memory-side" / "skills" / "context-routing-skill").mkdir(parents=True, exist_ok=True)
            (repo / "product" / "memory-side" / "skills" / "context-routing-skill" / "SKILL.md").write_text(
                "canonical\n",
                encoding="utf-8",
            )
            (repo / "docs" / "knowledge" / "memory-side").mkdir(parents=True, exist_ok=True)
            write_skill_wrapper(
                repo / ".agents" / "skills" / "context-routing-skill" / "SKILL.md",
                "## Canonical Sources\n"
                "1. `product/memory-side/skills/context-routing-skill/SKILL.md`\n"
                "2. `docs/knowledge/memory-side/`\n",
            )

            payload = classify_context_routing_repo_skill(repo, repo_root=root)

            assert payload is not None
            self.assertEqual(payload["status"], STATUS_USABLE)
            self.assertEqual(payload["missing_paths"], [])

    def test_classify_accepts_singular_canonical_source_heading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / ".exrepos" / "fmt"
            (repo / "product" / "memory-side" / "skills" / "context-routing-skill").mkdir(parents=True, exist_ok=True)
            (repo / "product" / "memory-side" / "skills" / "context-routing-skill" / "SKILL.md").write_text(
                "canonical\n",
                encoding="utf-8",
            )
            (repo / "docs" / "knowledge" / "memory-side").mkdir(parents=True, exist_ok=True)
            write_skill_wrapper(
                repo / ".agents" / "skills" / "context-routing-skill" / "SKILL.md",
                "## Canonical Source\n"
                "1. `product/memory-side/skills/context-routing-skill/SKILL.md`\n"
                "2. `docs/knowledge/memory-side/`\n",
            )

            payload = classify_context_routing_repo_skill(repo, repo_root=root)

            assert payload is not None
            self.assertEqual(payload["status"], STATUS_USABLE)
            self.assertEqual(payload["missing_paths"], [])

    def test_classify_returns_missing_repo_skill_when_skill_mount_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / ".exrepos" / "trackers"
            repo.mkdir(parents=True, exist_ok=True)

            payload = classify_context_routing_repo_skill(repo, repo_root=root)

            assert payload is not None
            self.assertEqual(payload["status"], STATUS_MISSING)

    def test_classify_returns_invalid_repo_skill_wrapper_when_canonical_paths_do_not_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / ".exrepos" / "typer"
            repo.mkdir(parents=True, exist_ok=True)
            write_skill_wrapper(
                repo / ".agents" / "skills" / "context-routing-skill" / "SKILL.md",
                "## Canonical Sources\n"
                "1. `product/memory-side/skills/context-routing-skill/SKILL.md`\n"
                "2. `docs/knowledge/memory-side/overview.md`\n",
            )

            payload = classify_context_routing_repo_skill(repo, repo_root=root)

            assert payload is not None
            self.assertEqual(payload["status"], STATUS_INVALID)
            self.assertEqual(
                payload["missing_paths"],
                [
                    "product/memory-side/skills/context-routing-skill/SKILL.md",
                    "docs/knowledge/memory-side/overview.md",
                ],
            )

    def test_collect_suite_report_only_includes_exrepos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exrepo = root / ".exrepos" / "fmt"
            exrepo.mkdir(parents=True, exist_ok=True)
            non_exrepo = root / "other-repo"
            non_exrepo.mkdir(parents=True, exist_ok=True)
            suite = root / "train.yaml"
            suite.write_text(
                "version: 1\n"
                "defaults:\n"
                "  backend: codex\n"
                "  judge_backend: codex\n"
                "  with_eval: true\n"
                "runs:\n"
                f"  - repo: {exrepo}\n"
                "    task: context-routing\n"
                f"  - repo: {non_exrepo}\n"
                "    task: context-routing\n",
                encoding="utf-8",
            )

            report = collect_context_routing_suite_repo_skill_report([suite], repo_root=root)

            self.assertEqual(len(report), 1)
            self.assertEqual(report[0]["repo"], "fmt")

    def test_classify_accepts_repo_under_tmp_exrepos_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tmp_exrepos_root = root / "tmp-exrepos"
            repo = tmp_exrepos_root / "typer"
            (repo / "product" / "memory-side" / "skills" / "context-routing-skill").mkdir(parents=True, exist_ok=True)
            (repo / "product" / "memory-side" / "skills" / "context-routing-skill" / "SKILL.md").write_text(
                "canonical\n",
                encoding="utf-8",
            )
            (repo / "docs" / "knowledge" / "memory-side").mkdir(parents=True, exist_ok=True)
            write_skill_wrapper(
                repo / ".agents" / "skills" / "context-routing-skill" / "SKILL.md",
                "## Canonical Sources\n"
                "1. `product/memory-side/skills/context-routing-skill/SKILL.md`\n"
                "2. `docs/knowledge/memory-side/`\n",
            )

            payload = classify_context_routing_repo_skill(
                repo,
                repo_root=root,
                tmp_exrepos_root=tmp_exrepos_root,
            )

            assert payload is not None
            self.assertEqual(payload["status"], STATUS_USABLE)
            self.assertEqual(payload["repo"], "typer")

    def test_collect_suite_report_includes_tmp_exrepos_for_bare_repo_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tmp_exrepos_root = root / "tmp-exrepos"
            repo = tmp_exrepos_root / "typer"
            repo.mkdir(parents=True, exist_ok=True)
            suite = root / "train.yaml"
            suite.write_text(
                "version: 1\n"
                "defaults:\n"
                "  backend: codex\n"
                "  judge_backend: codex\n"
                "  with_eval: true\n"
                "runs:\n"
                "  - repo: typer\n"
                "    task: context-routing\n",
                encoding="utf-8",
            )

            with mock.patch("common.TMP_EXREPOS_ROOT", tmp_exrepos_root), mock.patch(
                "common.EXREPOS_ROOT",
                root / ".exrepos",
            ):
                report = collect_context_routing_suite_repo_skill_report(
                    [suite],
                    repo_root=root,
                    tmp_exrepos_root=tmp_exrepos_root,
                )

            self.assertEqual(len(report), 1)
            self.assertEqual(report[0]["repo"], "typer")

    def test_prompt_fallback_marker_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prompt = Path(tmp) / "prompt.md"
            prompt.write_text(ROUTING_ENTRY_FALLBACK_MARKER + "\nroute\n", encoding="utf-8")

            self.assertTrue(prompt_allows_exrepo_routing_fallback(prompt))


if __name__ == "__main__":
    unittest.main()
