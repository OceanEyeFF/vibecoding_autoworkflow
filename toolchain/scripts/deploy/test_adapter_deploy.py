from __future__ import annotations

import contextlib
import io
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
        self._create_skill("harness-operations", "simple-workflow", "workflow-v1")

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

    def test_verify_bootstraps_local_root_and_missing_entries(self) -> None:
        code, stdout, stderr = self._run_cli("verify", "--backend", "agents")
        self.assertEqual(code, 0, stderr)
        self.assertIn("[agents] ok", stdout)
        self.assertTrue(self.local_root.is_dir())
        self.assertTrue((self.local_root / "alpha").is_symlink())
        self.assertTrue((self.local_root / "simple-workflow").is_symlink())

        target_beta = self.local_root / "beta"
        target_beta.unlink()

        code, stdout, stderr = self._run_cli("verify", "--backend", "agents")
        self.assertEqual(code, 0, stderr)
        self.assertIn("[agents] ok", stdout)
        self.assertTrue(target_beta.is_symlink())

    def test_verify_bootstraps_local_entries_with_copy_fallback_when_symlinks_fail(self) -> None:
        original_symlink_to = Path.symlink_to

        def flaky_symlink(path: Path, target: Path, target_is_directory: bool = False) -> None:
            if path.parent == self.local_root:
                raise OSError("symlink not permitted")
            original_symlink_to(path, target, target_is_directory=target_is_directory)

        with mock.patch.object(Path, "symlink_to", autospec=True, side_effect=flaky_symlink):
            code, stdout, stderr = self._run_cli("verify", "--backend", "agents")

        self.assertEqual(code, 0, stderr)
        self.assertIn("[agents] ok", stdout)
        self.assertTrue((self.local_root / "alpha").is_dir())
        self.assertFalse((self.local_root / "alpha").is_symlink())
        self.assertEqual(
            (self.local_root / "alpha" / "SKILL.md").read_text(encoding="utf-8"),
            "alpha-v1",
        )

    def test_verify_reports_local_drift_issue_codes(self) -> None:
        code, _, stderr = self._run_cli("local", "--backend", "agents")
        self.assertEqual(code, 0, stderr)

        target_alpha = self.local_root / "alpha"
        target_task = self.local_root / "task-contract-skill"
        target_workflow = self.local_root / "simple-workflow"

        with self.subTest("new partition target is deployed"):
            self.assertTrue(target_workflow.is_symlink())
            self.assertEqual(
                (target_workflow / "SKILL.md").read_text(encoding="utf-8"),
                "workflow-v1",
            )

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


if __name__ == "__main__":
    unittest.main()
