from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from exrepo_runtime import (  # noqa: E402
    materialize_suite,
    resolve_materialized_suite_path,
    resolve_tmp_exrepos_root,
)
from run_skill_suite import load_suite_manifest  # noqa: E402


class ExrepoRuntimeTest(unittest.TestCase):
    def test_resolve_tmp_exrepos_root_defaults_to_os_tmp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo-a"
            resolved = resolve_tmp_exrepos_root(repo_root=repo_root)

            self.assertTrue(resolved.is_absolute())
            self.assertEqual(resolved.parent, Path("/tmp").resolve(strict=False))

    def test_resolve_tmp_exrepos_root_is_stable_for_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp) / "os-tmp"
            repo_root = Path(tmp) / "repo-a"
            other_repo_root = Path(tmp) / "repo-b"

            first = resolve_tmp_exrepos_root(repo_root=repo_root, temp_root=temp_root)
            second = resolve_tmp_exrepos_root(repo_root=repo_root, temp_root=temp_root)
            other = resolve_tmp_exrepos_root(repo_root=other_repo_root, temp_root=temp_root)

            self.assertTrue(first.is_absolute())
            self.assertEqual(first, second)
            self.assertEqual(first.parent, temp_root.resolve(strict=False))
            self.assertNotEqual(first, other)

    def test_materialize_yaml_suite_rewrites_exrepo_repo_and_prompt_paths_without_mutating_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite_dir = root / "suites"
            prompt_dir = suite_dir / "prompts"
            prompt_dir.mkdir(parents=True, exist_ok=True)
            prompt_path = prompt_dir / "task.md"
            eval_prompt_path = prompt_dir / "eval.md"
            prompt_path.write_text("prompt\n", encoding="utf-8")
            eval_prompt_path.write_text("eval\n", encoding="utf-8")
            source_suite = suite_dir / "train.yaml"
            source_text = (
                "version: 1\n"
                "defaults:\n"
                "  backend: codex\n"
                "  judge_backend: codex\n"
                "  with_eval: true\n"
                "runs:\n"
                "  - repo: typer\n"
                "    task: context-routing\n"
                "    prompt_file: prompts/task.md\n"
                "    eval_prompt_file: prompts/eval.md\n"
            )
            source_suite.write_text(source_text, encoding="utf-8")

            exrepo_root = root / "tmp-exrepos"
            materialized = materialize_suite(source_suite, root / "artifacts", exrepo_root=exrepo_root)

            self.assertEqual(source_suite.read_text(encoding="utf-8"), source_text)
            self.assertNotEqual(materialized, source_suite)
            self.assertEqual(materialized, resolve_materialized_suite_path(source_suite, root / "artifacts"))

            manifest = load_suite_manifest(materialized)
            run_entry = manifest["runs"][0]
            self.assertEqual(run_entry["repo"], str((exrepo_root / "typer").resolve(strict=False)))
            self.assertEqual(run_entry["prompt_file"], str(prompt_path.resolve(strict=False)))
            self.assertEqual(run_entry["eval_prompt_file"], str(eval_prompt_path.resolve(strict=False)))

    def test_materialize_json_suite_rewrites_path_like_repo_to_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite_dir = root / "json-suite"
            suite_dir.mkdir(parents=True, exist_ok=True)
            prompt_path = root / "prompt.md"
            prompt_path.write_text("prompt\n", encoding="utf-8")
            source_suite = suite_dir / "validation.json"
            source_suite.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "defaults": {
                            "backend": "codex",
                            "judge_backend": "codex",
                            "with_eval": False,
                        },
                        "runs": [
                            {
                                "repo": ".",
                                "task": "context-routing",
                                "prompt_file": str(prompt_path),
                            }
                        ],
                    },
                    ensure_ascii=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            materialized = materialize_suite(source_suite, root / "artifacts", exrepo_root=root / "tmp-exrepos")

            manifest = load_suite_manifest(materialized)
            run_entry = manifest["runs"][0]
            self.assertEqual(run_entry["repo"], str(suite_dir.resolve(strict=False)))
            self.assertEqual(run_entry["prompt_file"], str(prompt_path.resolve(strict=False)))

    def test_materialize_suite_keeps_absolute_repo_absolute(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            absolute_repo = (root / "already-absolute").resolve(strict=False)
            source_suite = root / "train.yaml"
            source_suite.write_text(
                "version: 1\n"
                "defaults:\n"
                "  backend: codex\n"
                "runs:\n"
                f"  - repo: {absolute_repo}\n"
                "    task: context-routing\n",
                encoding="utf-8",
            )

            materialized = materialize_suite(source_suite, root / "artifacts", exrepo_root=root / "tmp-exrepos")

            manifest = load_suite_manifest(materialized)
            run_entry = manifest["runs"][0]
            self.assertEqual(run_entry["repo"], str(absolute_repo))

    def test_materialize_suite_uses_explicit_repo_root_anchor_when_exrepo_root_is_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite_dir = root / "suites"
            suite_dir.mkdir(parents=True, exist_ok=True)
            source_suite = suite_dir / "train.yaml"
            source_suite.write_text(
                "version: 1\n"
                "defaults:\n"
                "  backend: codex\n"
                "runs:\n"
                "  - repo: typer\n"
                "    task: context-routing\n",
                encoding="utf-8",
            )
            repo_root = root / "canonical-repo"
            materialized = materialize_suite(source_suite, root / "artifacts", repo_root=repo_root)

            manifest = load_suite_manifest(materialized)
            run_entry = manifest["runs"][0]
            expected_root = resolve_tmp_exrepos_root(repo_root=repo_root)
            self.assertEqual(run_entry["repo"], str((expected_root / "typer").resolve(strict=False)))

    def test_materialize_suite_requires_anchor_when_exrepo_root_is_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_suite = root / "train.yaml"
            source_suite.write_text(
                "version: 1\n"
                "defaults:\n"
                "  backend: codex\n"
                "runs:\n"
                "  - repo: typer\n"
                "    task: context-routing\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "either exrepo_root or repo_root"):
                materialize_suite(source_suite, root / "artifacts")


if __name__ == "__main__":
    unittest.main()
