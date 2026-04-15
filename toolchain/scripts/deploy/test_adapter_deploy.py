from __future__ import annotations

import contextlib
import io
import os
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
        self.local_root = self.temp_root / "repo-local" / ".agents" / "skills"
        self.global_root = self.temp_root / "global" / "codex" / "skills"

        self.patches = [
            mock.patch.object(adapter_deploy, "LOCAL_TARGET_ROOTS", {"agents": self.local_root}),
        ]
        for patcher in self.patches:
            patcher.start()
        self.addCleanup(self._cleanup_patches)
        self.addCleanup(self.temp_dir.cleanup)

    def _cleanup_patches(self) -> None:
        for patcher in reversed(self.patches):
            patcher.stop()

    def _run_cli(
        self, *argv: object, env: dict[str, str] | None = None
    ) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        env_patch = mock.patch.dict(os.environ, env or {}, clear=False)
        with (
            mock.patch.object(sys, "argv", ["adapter_deploy.py", *map(str, argv)]),
            env_patch,
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            return adapter_deploy.main(), stdout.getvalue(), stderr.getvalue()

    def test_local_creates_target_root(self) -> None:
        code, stdout, stderr = self._run_cli("local", "--backend", "agents")

        self.assertEqual(code, 0, stderr)
        self.assertTrue(self.local_root.is_dir())
        self.assertIn("created target root", stdout)

    def test_local_reuses_existing_target_root(self) -> None:
        self.local_root.mkdir(parents=True, exist_ok=True)

        code, stdout, stderr = self._run_cli("local", "--backend", "agents")

        self.assertEqual(code, 0, stderr)
        self.assertIn("ready target root", stdout)

    def test_global_requires_create_roots_when_missing(self) -> None:
        code, stdout, stderr = self._run_cli(
            "global",
            "--backend",
            "agents",
            "--agents-root",
            self.global_root,
        )

        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("Target root does not exist", stderr)
        self.assertFalse(self.global_root.exists())

    def test_global_creates_target_root_with_create_roots(self) -> None:
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
        self.assertIn("created target root", stdout)

    def test_global_uses_codex_home_when_override_is_missing(self) -> None:
        codex_home = self.temp_root / "codex-home"
        expected_root = codex_home / "skills"

        code, stdout, stderr = self._run_cli(
            "global",
            "--backend",
            "agents",
            "--create-roots",
            env={"CODEX_HOME": str(codex_home)},
        )

        self.assertEqual(code, 0, stderr)
        self.assertTrue(expected_root.is_dir())
        self.assertIn(str(expected_root), stdout)

    def test_verify_reports_missing_target_root(self) -> None:
        code, stdout, stderr = self._run_cli("verify", "--backend", "agents")

        self.assertEqual(code, 1, stderr)
        self.assertIn("missing-target-root", stdout)

    def test_verify_reports_ok_for_existing_target_root(self) -> None:
        self.local_root.mkdir(parents=True, exist_ok=True)

        code, stdout, stderr = self._run_cli("verify", "--backend", "agents")

        self.assertEqual(code, 0, stderr)
        self.assertIn("[agents] ok", stdout)

    def test_rejects_symlinked_target_root_for_deploy_and_verify(self) -> None:
        self.local_root.parent.mkdir(parents=True, exist_ok=True)
        real_root = self.temp_root / "redirected-agents-skills"
        real_root.mkdir(parents=True, exist_ok=True)
        self.local_root.symlink_to(real_root, target_is_directory=True)

        code, stdout, stderr = self._run_cli("local", "--backend", "agents")

        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("must be a real directory, not a symlink", stderr)

        code, stdout, stderr = self._run_cli("verify", "--backend", "agents")

        self.assertEqual(code, 1, stderr)
        self.assertIn("wrong-target-root-type", stdout)
        self.assertIn("must be a real directory, not a symlink", stdout)

    def test_verify_reports_broken_symlinked_target_root(self) -> None:
        self.local_root.parent.mkdir(parents=True, exist_ok=True)
        self.local_root.symlink_to(self.temp_root / "missing-root", target_is_directory=True)

        code, stdout, stderr = self._run_cli("verify", "--backend", "agents")

        self.assertEqual(code, 1, stderr)
        self.assertIn("broken-target-root-symlink", stdout)

    def test_verify_reports_non_directory_target_root(self) -> None:
        self.local_root.parent.mkdir(parents=True, exist_ok=True)
        self.local_root.write_text("not a directory\n", encoding="utf-8")

        code, stdout, stderr = self._run_cli("verify", "--backend", "agents")

        self.assertEqual(code, 1, stderr)
        self.assertIn("wrong-target-root-type", stdout)

    def test_dry_run_does_not_create_root(self) -> None:
        code, stdout, stderr = self._run_cli("local", "--backend", "agents", "--dry-run")

        self.assertEqual(code, 0, stderr)
        self.assertIn("would create target root", stdout)
        self.assertFalse(self.local_root.exists())


if __name__ == "__main__":
    unittest.main()
