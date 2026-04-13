from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import init_harness_project


class InitHarnessProjectTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.template_path = self.repo_root / init_harness_project.TEMPLATE_RELATIVE_PATH
        self.template_path.parent.mkdir(parents=True, exist_ok=True)
        self.template_path.write_text(
            (
                "version: 1\n"
                "contract:\n"
                "  commands:\n"
                "    scope_gate: python3 toolchain/scripts/test/harness_scope_gate.py --harness-file .autoworkflow/harness.yaml\n"
                "    backfill_gate: python3 toolchain/scripts/test/gate_status_backfill.py --workflow-id pending --gate scope_gate --status passed --state-file .autoworkflow/state/harness-review-loop.json --closeout-root .autoworkflow/closeout\n"
                "    smoke_gate: python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --agents-root .autoworkflow/smoke/agents/skills --create-roots --prune && python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend agents --agents-root .autoworkflow/smoke/agents/skills\n"
                "runtime:\n"
                "  repo_root: __REPO_ROOT__\n"
                "  state_file: .autoworkflow/state/harness-review-loop.json\n"
                "  contract_file: .autoworkflow/contracts/pending.json\n"
                "  closeout_root: .autoworkflow/closeout\n"
                "  smoke_agents_root: .autoworkflow/smoke/agents/skills\n"
            ),
            encoding="utf-8",
        )

        self.addCleanup(self.temp_dir.cleanup)

    def _run_cli(self, *argv: object) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(sys, "argv", ["init_harness_project.py", *map(str, argv)]),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            return init_harness_project.main(), stdout.getvalue(), stderr.getvalue()

    def test_init_creates_runtime_dirs_and_harness_file(self) -> None:
        code, stdout, stderr = self._run_cli("--repo-root", self.repo_root)
        self.assertEqual(code, 0, stderr)
        self.assertIn("wrote harness config", stdout)

        harness_file = self.repo_root / ".autoworkflow" / "harness.yaml"
        self.assertTrue(harness_file.exists())
        self.assertIn(str(self.repo_root), harness_file.read_text(encoding="utf-8"))
        self.assertTrue((self.repo_root / ".autoworkflow" / "state").is_dir())
        self.assertTrue((self.repo_root / ".autoworkflow" / "contracts").is_dir())
        self.assertTrue((self.repo_root / ".autoworkflow" / "closeout").is_dir())
        self.assertTrue((self.repo_root / ".autoworkflow" / "smoke" / "agents" / "skills").is_dir())

    def test_init_skips_existing_file_without_force_but_repairs_runtime_dirs(self) -> None:
        harness_file = self.repo_root / ".autoworkflow" / "harness.yaml"
        harness_file.parent.mkdir(parents=True, exist_ok=True)
        harness_file.write_text("existing: true\n", encoding="utf-8")

        code, stdout, stderr = self._run_cli("--repo-root", self.repo_root)
        self.assertEqual(code, 0, stderr)
        self.assertIn("already exists", stdout)
        self.assertEqual(harness_file.read_text(encoding="utf-8"), "existing: true\n")
        self.assertTrue((self.repo_root / ".autoworkflow" / "state").is_dir())
        self.assertTrue((self.repo_root / ".autoworkflow" / "contracts").is_dir())
        self.assertTrue((self.repo_root / ".autoworkflow" / "closeout").is_dir())
        self.assertTrue((self.repo_root / ".autoworkflow" / "smoke" / "agents" / "skills").is_dir())

    def test_init_force_overwrites_existing_file(self) -> None:
        harness_file = self.repo_root / ".autoworkflow" / "harness.yaml"
        harness_file.parent.mkdir(parents=True, exist_ok=True)
        harness_file.write_text("existing: true\n", encoding="utf-8")

        code, stdout, stderr = self._run_cli("--repo-root", self.repo_root, "--force")
        self.assertEqual(code, 0, stderr)
        self.assertIn("wrote harness config", stdout)
        self.assertIn("version: 1", harness_file.read_text(encoding="utf-8"))

    def test_init_dry_run_does_not_write_files(self) -> None:
        code, stdout, stderr = self._run_cli("--repo-root", self.repo_root, "--dry-run")
        self.assertEqual(code, 0, stderr)
        self.assertIn("would create directory", stdout)
        self.assertIn("would create harness config", stdout)
        self.assertFalse((self.repo_root / ".autoworkflow").exists())

    def test_init_fails_when_harness_file_path_is_directory(self) -> None:
        harness_dir = self.repo_root / ".autoworkflow" / "harness.yaml"
        harness_dir.mkdir(parents=True, exist_ok=True)

        code, _, stderr = self._run_cli("--repo-root", self.repo_root)
        self.assertEqual(code, 1)
        self.assertIn("harness config path is a directory", stderr)

        force_code, _, force_stderr = self._run_cli("--repo-root", self.repo_root, "--force")
        self.assertEqual(force_code, 1)
        self.assertIn("harness config path is a directory", force_stderr)

    def test_init_fails_when_runtime_root_collides_with_file(self) -> None:
        runtime_root = self.repo_root / ".autoworkflow"
        runtime_root.write_text("not-a-directory\n", encoding="utf-8")

        code, _, stderr = self._run_cli("--repo-root", self.repo_root)
        self.assertEqual(code, 1)
        self.assertIn("Path exists but is not a directory", stderr)

    def test_init_with_custom_relative_harness_file_keeps_runtime_paths_aligned(self) -> None:
        harness_file = Path("custom-runtime") / "harness" / "config.yaml"

        code, stdout, stderr = self._run_cli(
            "--repo-root",
            self.repo_root,
            "--harness-file",
            harness_file,
        )
        self.assertEqual(code, 0, stderr)
        self.assertIn("wrote harness config", stdout)

        resolved_harness_file = self.repo_root / harness_file
        self.assertTrue(resolved_harness_file.exists())
        self.assertTrue((self.repo_root / "custom-runtime" / "harness" / "state").is_dir())
        self.assertTrue((self.repo_root / "custom-runtime" / "harness" / "contracts").is_dir())
        self.assertTrue((self.repo_root / "custom-runtime" / "harness" / "closeout").is_dir())
        self.assertTrue((self.repo_root / "custom-runtime" / "harness" / "smoke" / "agents" / "skills").is_dir())

        rendered = resolved_harness_file.read_text(encoding="utf-8")
        self.assertIn(
            "state_file: custom-runtime/harness/state/harness-review-loop.json",
            rendered,
        )
        self.assertIn(
            "--state-file custom-runtime/harness/state/harness-review-loop.json",
            rendered,
        )
        self.assertIn(
            "--harness-file custom-runtime/harness/config.yaml",
            rendered,
        )
        self.assertIn(
            "--closeout-root custom-runtime/harness/closeout",
            rendered,
        )
        self.assertIn(
            "closeout_root: custom-runtime/harness/closeout",
            rendered,
        )
        self.assertIn(
            "smoke_agents_root: custom-runtime/harness/smoke/agents/skills",
            rendered,
        )
        self.assertIn(
            "--agents-root custom-runtime/harness/smoke/agents/skills",
            rendered,
        )
        self.assertNotIn("--agents-root .autoworkflow/smoke/agents/skills", rendered)

    def test_init_rejects_relative_harness_file_that_escapes_repo_root(self) -> None:
        code, _, stderr = self._run_cli(
            "--repo-root",
            self.repo_root,
            "--harness-file",
            Path("..") / "outside" / "harness.yaml",
        )
        self.assertEqual(code, 1)
        self.assertIn("relative harness config path escapes repo root", stderr)
        self.assertFalse((self.repo_root.parent / "outside" / "harness.yaml").exists())

    def test_init_with_absolute_harness_file_outside_repo_uses_absolute_runtime_paths(self) -> None:
        with tempfile.TemporaryDirectory() as external_dir:
            external_root = Path(external_dir)
            harness_file = external_root / "config" / "harness.yaml"

            code, _, stderr = self._run_cli(
                "--repo-root",
                self.repo_root,
                "--harness-file",
                harness_file,
            )
            self.assertEqual(code, 0, stderr)

            rendered = harness_file.read_text(encoding="utf-8")
            self.assertIn(
                f"state_file: {external_root / 'config' / 'state' / 'harness-review-loop.json'}",
                rendered,
            )
            self.assertIn(
                f"contract_file: {external_root / 'config' / 'contracts' / 'pending.json'}",
                rendered,
            )
            self.assertIn(
                f"closeout_root: {external_root / 'config' / 'closeout'}",
                rendered,
            )
            self.assertIn(
                f"smoke_agents_root: {external_root / 'config' / 'smoke' / 'agents' / 'skills'}",
                rendered,
            )

    def test_init_uses_template_from_target_repo_root(self) -> None:
        target_repo = self.repo_root / "other-repo"
        target_template = target_repo / init_harness_project.TEMPLATE_RELATIVE_PATH
        target_template.parent.mkdir(parents=True, exist_ok=True)
        target_template.write_text(
            (
                "version: 1\n"
                "contract:\n"
                "  commands:\n"
                "    custom_marker: from-target-repo\n"
                "runtime:\n"
                "  repo_root: __REPO_ROOT__\n"
                "  state_file: .autoworkflow/state/harness-review-loop.json\n"
                "  contract_file: .autoworkflow/contracts/pending.json\n"
                "  closeout_root: .autoworkflow/closeout\n"
                "  smoke_agents_root: .autoworkflow/smoke/agents/skills\n"
            ),
            encoding="utf-8",
        )

        code, _, stderr = self._run_cli("--repo-root", target_repo)
        self.assertEqual(code, 0, stderr)

        harness_file = target_repo / ".autoworkflow" / "harness.yaml"
        rendered = harness_file.read_text(encoding="utf-8")
        self.assertIn("custom_marker: from-target-repo", rendered)
        self.assertIn(str(target_repo.resolve()), rendered)


if __name__ == "__main__":
    unittest.main()
