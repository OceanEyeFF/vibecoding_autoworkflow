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

        self.patches = [
            mock.patch.object(adapter_deploy, "PRODUCT_ROOT", self.product_root),
            mock.patch.object(
                adapter_deploy,
                "PRODUCT_PARTITIONS",
                ("memory-side", "task-interface"),
            ),
            mock.patch.object(adapter_deploy, "LOCAL_TARGET_ROOTS", {"agents": self.local_root}),
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
        self.assertEqual((target_alpha / "SKILL.md").read_text(encoding="utf-8"), "alpha-v1")
        self.assertIn("symlinked", stdout)

        self._skill_source("memory-side", "alpha").joinpath("SKILL.md").write_text(
            "alpha-v2",
            encoding="utf-8",
        )

        code, stdout, stderr = self._run_cli("local", "--backend", "agents")

        self.assertEqual(code, 0, stderr)
        self.assertEqual((target_alpha / "SKILL.md").read_text(encoding="utf-8"), "alpha-v2")
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
        self.assertEqual((target_alpha / "SKILL.md").read_text(encoding="utf-8"), "alpha-v1")
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
        self.assertEqual((target_alpha / "SKILL.md").read_text(encoding="utf-8"), "alpha-v2")
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

        code, stdout, stderr = self._run_cli("local", "--backend", "agents", "--prune")
        self.assertEqual(code, 0, stderr)
        self.assertFalse((self.local_root / "beta").exists())

        code, stdout, stderr = self._run_cli("verify", "--backend", "agents")
        self.assertEqual(code, 0, stderr)
        self.assertIn("[agents] ok", stdout)

    def test_verify_reports_local_drift_issue_codes(self) -> None:
        code, _, stderr = self._run_cli("local", "--backend", "agents")
        self.assertEqual(code, 0, stderr)

        target_alpha = self.local_root / "alpha"
        target_alpha.unlink()
        target_alpha.write_text("not-a-symlink\n", encoding="utf-8")

        broken = self.local_root / "beta"
        broken.unlink()
        broken.symlink_to("missing-beta", target_is_directory=True)

        unexpected = self.local_root / "unexpected"
        unexpected.mkdir(parents=True, exist_ok=True)
        (unexpected / "SKILL.md").write_text("orphan\n", encoding="utf-8")

        code, stdout, stderr = self._run_cli("verify", "--backend", "agents")

        self.assertEqual(code, 1, stderr)
        self.assertIn("wrong-target-type", stdout)
        self.assertIn("broken-symlink", stdout)
        self.assertIn("wrong-symlink-target", stdout)
        self.assertIn("unexpected-target-entry", stdout)

    def test_verify_reports_global_drift_issue_codes(self) -> None:
        code, _, stderr = self._run_cli(
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
            "--create-roots",
        )
        self.assertEqual(code, 0, stderr)

        target_alpha = self.global_root / "alpha"
        (target_alpha / "SKILL.md").unlink()
        (target_alpha / "extra.txt").write_text("extra\n", encoding="utf-8")

        target_beta = self.global_root / "beta"
        shutil.rmtree(target_beta)
        target_beta.symlink_to("alpha", target_is_directory=True)

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
        self.assertIn("missing-target-file", stdout)
        self.assertIn("unexpected-target-file", stdout)
        self.assertIn("wrong-target-type", stdout)

    def test_build_is_noop_for_current_source_partitions(self) -> None:
        code, stdout, stderr = self._run_cli("build", "--backend", "agents")

        self.assertEqual(code, 0, stderr)
        self.assertIn("no build step required", stdout)


if __name__ == "__main__":
    unittest.main()
