from __future__ import annotations

import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import adapter_deploy


class AdapterDeployTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temp_dir.name)
        self.product_root = self.temp_root / "product"
        self.local_root = self.temp_root / "repo-local" / ".agents" / "skills"
        self.global_root = self.temp_root / "global" / "codex" / "skills"

        self._create_skill("memory-side", "alpha", "alpha-v1")
        self._create_skill("memory-side", "beta", "beta-v1")
        self._create_skill("task-interface", "task-contract-skill", "task-v1")
        self._create_harness_header_skill("simple-workflow", prompt_body="workflow-v1")

        self.patches = [
            mock.patch.object(adapter_deploy, "PRODUCT_ROOT", self.product_root),
            mock.patch.object(
                adapter_deploy,
                "PRODUCT_PARTITIONS",
                ("memory-side", "task-interface", "harness-operations"),
            ),
            mock.patch.object(
                adapter_deploy,
                "LOCAL_TARGET_ROOTS",
                {"agents": self.local_root},
            ),
        ]
        for patcher in self.patches:
            patcher.start()
        self.addCleanup(self._cleanup_patches)
        self.addCleanup(self.temp_dir.cleanup)

    def _cleanup_patches(self) -> None:
        for patcher in reversed(self.patches):
            patcher.stop()

    def _create_skill(self, partition: str, name: str, body: str) -> Path:
        skill_dir = self.product_root / partition / "adapters" / "agents" / "skills" / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
        return skill_dir

    def _skill_source(self, partition: str, name: str) -> Path:
        return self.product_root / partition / "adapters" / "agents" / "skills" / name

    def _create_harness_header_skill(self, name: str, prompt_body: str = "prompt-v1") -> Path:
        adapter_dir = (
            self.product_root
            / "harness-operations"
            / "adapters"
            / "agents"
            / "skills"
            / name
        )
        adapter_dir.mkdir(parents=True, exist_ok=True)
        (adapter_dir / "header.yaml").write_text(
            f"name: {name}\ndescription: harness adapter {name}\n",
            encoding="utf-8",
        )
        meta_dir = adapter_dir / "agents"
        meta_dir.mkdir(parents=True, exist_ok=True)
        (meta_dir / "openai.yaml").write_text("version: 1\n", encoding="utf-8")

        canonical_root = self.product_root / "harness-operations" / "skills"
        canonical_skill_dir = canonical_root / name
        canonical_skill_dir.mkdir(parents=True, exist_ok=True)
        (canonical_skill_dir / "prompt.md").write_text(prompt_body, encoding="utf-8")
        references_dir = canonical_skill_dir / "references"
        references_dir.mkdir(parents=True, exist_ok=True)
        (references_dir / "entrypoints.md").write_text(
            f"entrypoints for {name}\n",
            encoding="utf-8",
        )
        (references_dir / "bindings.md").write_text(
            f"bindings for {name}\n",
            encoding="utf-8",
        )
        (canonical_root / "harness-standard.md").write_text("shared-standard-v1", encoding="utf-8")
        return adapter_dir

    def _run_cli(self, *argv: object) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(sys, "argv", ["adapter_deploy.py", *map(str, argv)]),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            return adapter_deploy.main(), stdout.getvalue(), stderr.getvalue()

    def test_local_deploy_to_empty_target_and_redeploy_after_source_update(self) -> None:
        target_alpha = self.local_root / "alpha"

        code, stdout, stderr = self._run_cli("local", "--backend", "agents")

        self.assertEqual(code, 0, stderr)
        self.assertTrue(self.local_root.is_dir())
        self.assertTrue(target_alpha.is_symlink())
        self.assertEqual(
            (target_alpha / "SKILL.md").read_text(encoding="utf-8"),
            "alpha-v1",
        )
        self.assertIn("symlinked", stdout)

        self._skill_source("memory-side", "alpha").joinpath("SKILL.md").write_text(
            "alpha-v2",
            encoding="utf-8",
        )

        code, stdout, stderr = self._run_cli("local", "--backend", "agents")

        self.assertEqual(code, 0, stderr)
        self.assertEqual(
            (target_alpha / "SKILL.md").read_text(encoding="utf-8"),
            "alpha-v2",
        )
        self.assertIn("symlinked", stdout)

        code, stdout, stderr = self._run_cli("verify", "--backend", "agents")
        self.assertEqual(code, 0, stderr)
        self.assertIn("[agents] ok", stdout)

    def test_global_deploy_to_empty_target_and_redeploy_after_source_update(self) -> None:
        target_alpha = self.global_root / "alpha"

        code, stdout, stderr = self._run_cli(
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
            "--create-roots",
        )

        self.assertEqual(code, 0, stderr)
        self.assertTrue(self.global_root.is_dir())
        self.assertTrue(target_alpha.is_dir())
        self.assertFalse(target_alpha.is_symlink())
        self.assertEqual(
            (target_alpha / "SKILL.md").read_text(encoding="utf-8"),
            "alpha-v1",
        )
        self.assertIn("copied", stdout)

        self._skill_source("memory-side", "alpha").joinpath("SKILL.md").write_text(
            "alpha-v2",
            encoding="utf-8",
        )

        code, stdout, stderr = self._run_cli(
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
            "--create-roots",
        )

        self.assertEqual(code, 0, stderr)
        self.assertEqual(
            (target_alpha / "SKILL.md").read_text(encoding="utf-8"),
            "alpha-v2",
        )
        self.assertIn("copied", stdout)

        code, stdout, stderr = self._run_cli(
            "verify",
            "--target",
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
        )
        self.assertEqual(code, 0, stderr)
        self.assertIn("[agents] ok", stdout)

    def test_local_prune_clears_stale_targets_after_source_deletion(self) -> None:
        code, _, stderr = self._run_cli("local", "--backend", "agents")
        self.assertEqual(code, 0, stderr)

        shutil.rmtree(self._skill_source("memory-side", "beta"))

        code, stdout, stderr = self._run_cli("verify", "--backend", "agents")
        self.assertEqual(code, 1, stderr)
        self.assertIn("unexpected-target-entry", stdout)
        self.assertTrue((self.local_root / "beta").is_symlink())

        code, stdout, stderr = self._run_cli(
            "local",
            "--backend",
            "agents",
            "--prune",
        )
        self.assertEqual(code, 0, stderr)
        self.assertFalse((self.local_root / "beta").exists())
        self.assertFalse((self.local_root / "beta").is_symlink())

        code, stdout, stderr = self._run_cli("verify", "--backend", "agents")
        self.assertEqual(code, 0, stderr)
        self.assertIn("[agents] ok", stdout)

    def test_global_prune_clears_stale_targets_after_source_deletion(self) -> None:
        code, _, stderr = self._run_cli(
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
            "--create-roots",
        )
        self.assertEqual(code, 0, stderr)

        shutil.rmtree(self._skill_source("memory-side", "beta"))

        code, stdout, stderr = self._run_cli(
            "verify",
            "--target",
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
        )
        self.assertEqual(code, 1, stderr)
        self.assertIn("unexpected-target-entry", stdout)
        self.assertTrue((self.global_root / "beta").exists())

        code, stdout, stderr = self._run_cli(
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
            "--create-roots",
            "--prune",
        )
        self.assertEqual(code, 0, stderr)
        self.assertFalse((self.global_root / "beta").exists())

        code, stdout, stderr = self._run_cli(
            "verify",
            "--target",
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
        )
        self.assertEqual(code, 0, stderr)
        self.assertIn("[agents] ok", stdout)

    def test_verify_reports_local_drift_issue_codes(self) -> None:
        with self.subTest("missing target root"):
            code, stdout, stderr = self._run_cli("verify", "--backend", "agents")
            self.assertEqual(code, 1, stderr)
            self.assertIn("missing-target-root", stdout)

        code, _, stderr = self._run_cli("local", "--backend", "agents")
        self.assertEqual(code, 0, stderr)

        target_alpha = self.local_root / "alpha"
        target_beta = self.local_root / "beta"
        target_task = self.local_root / "task-contract-skill"
        target_workflow = self.local_root / "simple-workflow"

        with self.subTest("missing target entry"):
            target_beta.unlink()
            code, stdout, stderr = self._run_cli("verify", "--backend", "agents")
            self.assertEqual(code, 1, stderr)
            self.assertIn("missing-target-entry", stdout)
            restore_code, _, restore_stderr = self._run_cli("local", "--backend", "agents")
            self.assertEqual(restore_code, 0, restore_stderr)

        with self.subTest("new partition target is deployed"):
            self.assertTrue(target_workflow.is_symlink())
            self.assertIn("workflow-v1", (target_workflow / "SKILL.md").read_text(encoding="utf-8"))

        with self.subTest("unexpected target entry"):
            extra = self.local_root / "stale-skill"
            extra.symlink_to("../missing-source", target_is_directory=True)
            code, stdout, stderr = self._run_cli("verify", "--backend", "agents")
            self.assertEqual(code, 1, stderr)
            self.assertIn("unexpected-target-entry", stdout)
            extra.unlink()

        with self.subTest("broken symlink"):
            target_alpha.unlink()
            target_alpha.symlink_to("../missing-source", target_is_directory=True)
            code, stdout, stderr = self._run_cli("verify", "--backend", "agents")
            self.assertEqual(code, 1, stderr)
            self.assertIn("broken-symlink", stdout)
            self.assertIn("wrong-symlink-target", stdout)
            restore_code, _, restore_stderr = self._run_cli("local", "--backend", "agents")
            self.assertEqual(restore_code, 0, restore_stderr)

        with self.subTest("wrong target type"):
            target_task.unlink()
            target_task.mkdir()
            code, stdout, stderr = self._run_cli("verify", "--backend", "agents")
            self.assertEqual(code, 1, stderr)
            self.assertIn("wrong-target-type", stdout)

    def test_verify_reports_global_drift_issue_codes(self) -> None:
        with self.subTest("missing target root"):
            code, stdout, stderr = self._run_cli(
                "verify",
                "--target",
                "global",
                "--backend",
                "agents",
                "--agents-root",
                self.global_root,
            )
            self.assertEqual(code, 1, stderr)
            self.assertIn("missing-target-root", stdout)

        code, _, stderr = self._run_cli(
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
            "--create-roots",
        )
        self.assertEqual(code, 0, stderr)

        with self.subTest("unexpected target entry"):
            (self.global_root / "stale-skill").mkdir()
            code, stdout, stderr = self._run_cli(
                "verify",
                "--target",
                "global",
                "--backend",
                "agents",
                "--agents-root",
                self.global_root,
            )
            self.assertEqual(code, 1, stderr)
            self.assertIn("unexpected-target-entry", stdout)
            shutil.rmtree(self.global_root / "stale-skill")

        with self.subTest("missing target entry"):
            shutil.rmtree(self.global_root / "beta")
            code, stdout, stderr = self._run_cli(
                "verify",
                "--target",
                "global",
                "--backend",
                "agents",
                "--agents-root",
                self.global_root,
            )
            self.assertEqual(code, 1, stderr)
            self.assertIn("missing-target-entry", stdout)
            restore_code, _, restore_stderr = self._run_cli(
                "global",
                "--backend",
                "agents",
                "--agents-root",
                self.global_root,
                "--create-roots",
            )
            self.assertEqual(restore_code, 0, restore_stderr)

        with self.subTest("wrong target type"):
            shutil.rmtree(self.global_root / "task-contract-skill")
            (self.global_root / "task-contract-skill").write_text("not-a-dir", encoding="utf-8")
            code, stdout, stderr = self._run_cli(
                "verify",
                "--target",
                "global",
                "--backend",
                "agents",
                "--agents-root",
                self.global_root,
            )
            self.assertEqual(code, 1, stderr)
            self.assertIn("wrong-target-type", stdout)

    def test_build_assembles_harness_header_skill_and_deploys_local_mount(self) -> None:
        self._create_harness_header_skill("review-loop-workflow", prompt_body="review-loop-prompt-v1")
        build_root = self.temp_root / "build-sources"

        code, stdout, stderr = self._run_cli(
            "build",
            "--backend",
            "agents",
            "--build-root",
            build_root,
        )
        self.assertEqual(code, 0, stderr)
        self.assertIn("assembled", stdout)

        built_skill = build_root / "agents" / "review-loop-workflow" / "SKILL.md"
        self.assertTrue(built_skill.exists())
        rendered = built_skill.read_text(encoding="utf-8")
        self.assertIn("name: review-loop-workflow", rendered)
        self.assertIn("shared-standard-v1", rendered)
        self.assertIn("review-loop-prompt-v1", rendered)
        self.assertTrue((build_root / "agents" / "review-loop-workflow" / "agents" / "openai.yaml").exists())
        self.assertTrue(
            (build_root / "agents" / "review-loop-workflow" / "references" / "entrypoints.md").exists()
        )
        self.assertTrue(
            (build_root / "agents" / "review-loop-workflow" / "references" / "bindings.md").exists()
        )

        code, _, stderr = self._run_cli(
            "local",
            "--backend",
            "agents",
            "--build-root",
            build_root,
        )
        self.assertEqual(code, 0, stderr)
        self.assertTrue((self.local_root / "review-loop-workflow").is_symlink())
        self.assertEqual(
            (self.local_root / "review-loop-workflow" / "SKILL.md").read_text(encoding="utf-8"),
            rendered,
        )

    def test_deploy_fails_when_harness_adapter_header_is_missing(self) -> None:
        broken_skill = (
            self.product_root
            / "harness-operations"
            / "adapters"
            / "agents"
            / "skills"
            / "broken-workflow"
        )
        broken_skill.mkdir(parents=True, exist_ok=True)

        code, _, stderr = self._run_cli("local", "--backend", "agents")
        self.assertEqual(code, 1)
        self.assertIn("Missing harness adapter header", stderr)

    def test_verify_global_does_not_require_build_sources_for_harness_skill(self) -> None:
        self._create_harness_header_skill("review-loop-workflow", prompt_body="review-loop-prompt-v1")
        build_root = self.temp_root / "build-sources"

        deploy_code, _, deploy_stderr = self._run_cli(
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
            "--build-root",
            build_root,
            "--create-roots",
        )
        self.assertEqual(deploy_code, 0, deploy_stderr)
        shutil.rmtree(build_root)

        verify_code, verify_stdout, verify_stderr = self._run_cli(
            "verify",
            "--target",
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
            "--build-root",
            build_root,
        )
        self.assertEqual(verify_code, 0, verify_stderr)
        self.assertIn("[agents] ok", verify_stdout)
        self.assertNotIn("missing-build-source", verify_stdout)

    def test_verify_global_detects_stale_harness_copy_when_build_snapshot_changes(self) -> None:
        build_root = self.temp_root / "build-sources"
        prompt_path = (
            self.product_root
            / "harness-operations"
            / "skills"
            / "simple-workflow"
            / "prompt.md"
        )

        deploy_code, _, deploy_stderr = self._run_cli(
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
            "--build-root",
            build_root,
            "--create-roots",
        )
        self.assertEqual(deploy_code, 0, deploy_stderr)

        prompt_path.write_text("workflow-v2", encoding="utf-8")

        verify_code, verify_stdout, verify_stderr = self._run_cli(
            "verify",
            "--target",
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
            "--build-root",
            build_root,
        )
        self.assertEqual(verify_code, 1, verify_stderr)
        self.assertIn("stale-target-file", verify_stdout)
        self.assertIn("simple-workflow/SKILL.md", verify_stdout)

    def test_verify_local_detects_missing_harness_reference_files(self) -> None:
        build_root = self.temp_root / "build-sources"

        build_code, _, build_stderr = self._run_cli(
            "build",
            "--backend",
            "agents",
            "--build-root",
            build_root,
        )
        self.assertEqual(build_code, 0, build_stderr)

        deploy_code, _, deploy_stderr = self._run_cli(
            "local",
            "--backend",
            "agents",
            "--build-root",
            build_root,
        )
        self.assertEqual(deploy_code, 0, deploy_stderr)

        (build_root / "agents" / "simple-workflow" / "references" / "entrypoints.md").unlink()
        verify_code, verify_stdout, verify_stderr = self._run_cli(
            "verify",
            "--backend",
            "agents",
            "--build-root",
            build_root,
        )
        self.assertEqual(verify_code, 1, verify_stderr)
        self.assertIn("missing-build-source-file", verify_stdout)
        self.assertIn("simple-workflow/references/entrypoints.md", verify_stdout)

    def test_verify_global_detects_missing_harness_reference_files(self) -> None:
        build_root = self.temp_root / "build-sources"

        deploy_code, _, deploy_stderr = self._run_cli(
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
            "--build-root",
            build_root,
            "--create-roots",
        )
        self.assertEqual(deploy_code, 0, deploy_stderr)

        (self.global_root / "simple-workflow" / "references" / "entrypoints.md").unlink()
        verify_code, verify_stdout, verify_stderr = self._run_cli(
            "verify",
            "--target",
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
            "--build-root",
            build_root,
        )
        self.assertEqual(verify_code, 1, verify_stderr)
        self.assertIn("missing-target-file", verify_stdout)
        self.assertIn("simple-workflow/references/entrypoints.md", verify_stdout)

    def test_verify_local_detects_stale_harness_build_outputs(self) -> None:
        build_root = self.temp_root / "build-sources"
        prompt_path = (
            self.product_root
            / "harness-operations"
            / "skills"
            / "simple-workflow"
            / "prompt.md"
        )

        build_code, _, build_stderr = self._run_cli(
            "build",
            "--backend",
            "agents",
            "--build-root",
            build_root,
        )
        self.assertEqual(build_code, 0, build_stderr)

        deploy_code, _, deploy_stderr = self._run_cli(
            "local",
            "--backend",
            "agents",
            "--build-root",
            build_root,
        )
        self.assertEqual(deploy_code, 0, deploy_stderr)

        prompt_path.write_text("workflow-v2", encoding="utf-8")
        verify_code, verify_stdout, verify_stderr = self._run_cli(
            "verify",
            "--backend",
            "agents",
            "--build-root",
            build_root,
        )
        self.assertEqual(verify_code, 1, verify_stderr)
        self.assertIn("stale-build-source-file", verify_stdout)
        self.assertIn("simple-workflow/SKILL.md", verify_stdout)

    def test_verify_local_rejects_canonical_harness_mount_when_build_output_missing(self) -> None:
        build_root = self.temp_root / "build-sources"
        self.local_root.mkdir(parents=True, exist_ok=True)

        for partition, source_root in adapter_deploy.source_roots_for("agents"):
            for source_path in sorted(path for path in source_root.iterdir() if path.is_dir()):
                target_path = self.local_root / source_path.name
                if partition == "harness-operations":
                    mount_source = self.product_root / "harness-operations" / "skills" / source_path.name
                else:
                    mount_source = source_path
                target_path.symlink_to(
                    Path(os.path.relpath(mount_source, start=target_path.parent)),
                    target_is_directory=True,
                )

        verify_code, verify_stdout, verify_stderr = self._run_cli(
            "verify",
            "--backend",
            "agents",
            "--build-root",
            build_root,
        )
        self.assertEqual(verify_code, 1, verify_stderr)
        self.assertIn("missing-build-source", verify_stdout)

    def test_verify_local_rejects_canonical_harness_mount_when_build_output_exists(self) -> None:
        build_root = self.temp_root / "build-sources"
        self.local_root.mkdir(parents=True, exist_ok=True)

        for partition, source_root in adapter_deploy.source_roots_for("agents"):
            for source_path in sorted(path for path in source_root.iterdir() if path.is_dir()):
                target_path = self.local_root / source_path.name
                if partition == "harness-operations":
                    mount_source = self.product_root / "harness-operations" / "skills" / source_path.name
                else:
                    mount_source = source_path
                target_path.symlink_to(
                    Path(os.path.relpath(mount_source, start=target_path.parent)),
                    target_is_directory=True,
                )

        build_code, _, build_stderr = self._run_cli(
            "build",
            "--backend",
            "agents",
            "--build-root",
            build_root,
        )
        self.assertEqual(build_code, 0, build_stderr)

        verify_code, verify_stdout, verify_stderr = self._run_cli(
            "verify",
            "--backend",
            "agents",
            "--build-root",
            build_root,
        )
        self.assertEqual(verify_code, 1, verify_stderr)
        self.assertIn("wrong-symlink-target", verify_stdout)

    def test_verify_does_not_build_harness_sources(self) -> None:
        self._create_harness_header_skill("review-loop-workflow", prompt_body="review-loop-prompt-v1")
        build_root = self.temp_root / "build-sources"
        self.local_root.mkdir(parents=True, exist_ok=True)

        code, stdout, stderr = self._run_cli(
            "verify",
            "--backend",
            "agents",
            "--build-root",
            build_root,
        )

        self.assertEqual(code, 1, stderr)
        self.assertIn("missing-build-source", stdout)
        self.assertFalse((build_root / "agents" / "review-loop-workflow").exists())


if __name__ == "__main__":
    unittest.main()
