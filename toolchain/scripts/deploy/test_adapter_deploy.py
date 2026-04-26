from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import adapter_deploy
import harness_deploy


class AdapterDeployTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temp_dir.name)
        self.source_repo_root = adapter_deploy.REPO_ROOT
        self.fake_repo_root = self.temp_root / "repo"
        self.local_root = self.fake_repo_root / ".agents" / "skills"
        self.override_root = self.temp_root / "custom-root" / "skills"
        self.adapter_dir = (
            self.fake_repo_root / "product" / "harness" / "adapters" / "agents" / "skills"
        )

        self._seed_fake_repo()

        self.patches = [
            mock.patch.object(adapter_deploy, "REPO_ROOT", self.fake_repo_root),
            mock.patch.object(adapter_deploy, "LOCAL_TARGET_ROOTS", {"agents": self.local_root}),
            mock.patch.object(adapter_deploy, "ADAPTER_SKILL_DIRS", {"agents": self.adapter_dir}),
        ]
        for patcher in self.patches:
            patcher.start()
        self.addCleanup(self._cleanup_patches)
        self.addCleanup(self.temp_dir.cleanup)

    def _seed_fake_repo(self) -> None:
        shutil.copytree(
            self.source_repo_root / "product" / "harness" / "adapters",
            self.fake_repo_root / "product" / "harness" / "adapters",
        )
        shutil.copytree(
            self.source_repo_root / "product" / "harness" / "skills",
            self.fake_repo_root / "product" / "harness" / "skills",
        )

    def _cleanup_patches(self) -> None:
        for patcher in reversed(self.patches):
            patcher.stop()

    def _run_cli(
        self, *argv: object, env: dict[str, str] | None = None
    ) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        env_patch = mock.patch.dict("os.environ", env or {}, clear=False)
        with (
            mock.patch.object(sys, "argv", ["adapter_deploy.py", *map(str, argv)]),
            env_patch,
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            return adapter_deploy.main(), stdout.getvalue(), stderr.getvalue()

    def _run_wrapper_cli(self, *argv: object) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            return harness_deploy.main([*map(str, argv)]), stdout.getvalue(), stderr.getvalue()

    def _install(self, *extra_args: object) -> tuple[int, str, str]:
        return self._run_cli("install", "--backend", "agents", *extra_args)

    def _check_paths_exist(self, *extra_args: object) -> tuple[int, str, str]:
        return self._run_cli("check_paths_exist", "--backend", "agents", *extra_args)

    def _verify(self, *extra_args: object) -> tuple[int, str, str]:
        return self._run_cli("verify", "--backend", "agents", *extra_args)

    def _prune_all(self, *extra_args: object) -> tuple[int, str, str]:
        return self._run_cli("prune", "--backend", "agents", "--all", *extra_args)

    def _update(self, *extra_args: object) -> tuple[int, str, str]:
        return self._run_cli("update", "--backend", "agents", *extra_args)

    def _load_json(self, path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _binding(self, skill_id: str) -> adapter_deploy.SkillBinding:
        return next(
            binding
            for binding in adapter_deploy.collect_skill_bindings("agents")
            if binding.skill_id == skill_id
        )

    def _install_plan(self, skill_id: str, root: Path | None = None) -> adapter_deploy.InstallPlan:
        return adapter_deploy.build_install_plan(self._binding(skill_id), root or self.local_root)

    def _runtime_marker_text(self, skill_id: str, root: Path | None = None) -> str:
        plan = self._install_plan(skill_id, root=root)
        return adapter_deploy.runtime_marker_text(
            adapter_deploy.build_runtime_marker(
                plan.binding.backend,
                plan.binding.skill_id,
                plan.payload_version,
                plan.payload_fingerprint,
            )
        )

    def _install_foreign_conflict(self, skill_dir_name: str | None = None) -> Path:
        if skill_dir_name is None:
            skill_dir_name = self._target_dir_for_skill("harness-skill")
        skill_dir = self.local_root / skill_dir_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text("# foreign conflicting skill\n", encoding="utf-8")
        (skill_dir / "payload.json").write_text('{"foreign": true}\n', encoding="utf-8")
        return skill_dir

    def _install_managed_directory(
        self,
        skill_dir_name: str,
        *,
        marker_skill_id: str | None = None,
        backend: str = "agents",
    ) -> Path:
        skill_dir = self.local_root / skill_dir_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        marker = adapter_deploy.build_runtime_marker(
            backend,
            marker_skill_id or skill_dir_name,
            "agents-skill-payload.v1",
            "managed-fingerprint",
        )
        (skill_dir / "aw.marker").write_text(
            adapter_deploy.runtime_marker_text(marker),
            encoding="utf-8",
        )
        return skill_dir

    def _mutate_canonical_skill(self, skill_id: str, extra_text: str = "\n# source drift\n") -> None:
        skill_path = self.fake_repo_root / "product" / "harness" / "skills" / skill_id / "SKILL.md"
        skill_path.write_text(
            skill_path.read_text(encoding="utf-8") + extra_text,
            encoding="utf-8",
        )

    def _mutate_target_dir(self, skill_id: str, target_dir: str) -> None:
        payload_path = self.adapter_dir / skill_id / "payload.json"
        payload = self._load_json(payload_path)
        payload["target_dir"] = target_dir
        payload_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _target_dir_for_skill(self, skill_id: str) -> str:
        payload_path = self.adapter_dir / skill_id / "payload.json"
        payload = self._load_json(payload_path)
        return payload["target_dir"]

    def _remove_target_marker(self, skill_id: str) -> Path:
        target_dir_name = self._target_dir_for_skill(skill_id)
        marker_path = self.local_root / target_dir_name / "aw.marker"
        if marker_path.exists():
            marker_path.unlink()
        return marker_path.parent

    def test_install_creates_target_root_and_installs_agents_payloads(self) -> None:
        code, stdout, stderr = self._install()

        self.assertEqual(code, 0, stderr)
        self.assertTrue(self.local_root.is_dir())
        self.assertIn("created target root", stdout)

        for source_payload_dir in sorted(path for path in self.adapter_dir.iterdir() if path.is_dir()):
            skill_id = source_payload_dir.name
            payload = self._load_json(source_payload_dir / "payload.json")
            target_dir_name = payload["target_dir"]
            target_skill_dir = self.local_root / target_dir_name
            canonical_source = adapter_deploy.payload_canonical_source_metadata(
                payload,
                self._binding(skill_id),
            )
            self.assertTrue(target_skill_dir.is_dir(), target_skill_dir)
            self.assertEqual(
                (target_skill_dir / "payload.json").read_text(encoding="utf-8"),
                (source_payload_dir / "payload.json").read_text(encoding="utf-8"),
            )
            for included_path in canonical_source.included_paths:
                self.assertEqual(
                    (target_skill_dir / included_path).read_text(encoding="utf-8"),
                    (
                        self.fake_repo_root
                        / "product"
                        / "harness"
                        / "skills"
                        / skill_id
                        / included_path
                    ).read_text(encoding="utf-8"),
                )
            self.assertEqual(
                (target_skill_dir / "aw.marker").read_text(encoding="utf-8"),
                self._runtime_marker_text(skill_id),
            )

    def test_harness_deploy_wrapper_diagnose_matches_adapter_diagnose_json(self) -> None:
        adapter_code, adapter_stdout, adapter_stderr = self._run_cli(
            "diagnose",
            "--backend",
            "agents",
            "--json",
        )
        wrapper_code, wrapper_stdout, wrapper_stderr = self._run_wrapper_cli(
            "diagnose",
            "--backend",
            "agents",
            "--json",
        )

        self.assertEqual(adapter_code, 0, adapter_stderr)
        self.assertEqual(wrapper_code, 0, wrapper_stderr)
        self.assertEqual(json.loads(wrapper_stdout), json.loads(adapter_stdout))

    def test_harness_deploy_wrapper_verify_keeps_strict_failure_semantics(self) -> None:
        code, stdout, stderr = self._run_wrapper_cli("verify", "--backend", "agents")

        self.assertEqual(code, 1)
        self.assertIn("missing-target-root", stdout)
        self.assertEqual(stderr, "")

    def test_harness_deploy_wrapper_update_dry_run_matches_adapter_json(self) -> None:
        adapter_code, adapter_stdout, adapter_stderr = self._run_cli(
            "update",
            "--backend",
            "agents",
            "--json",
        )
        wrapper_code, wrapper_stdout, wrapper_stderr = self._run_wrapper_cli(
            "update",
            "--backend",
            "agents",
            "--json",
        )

        self.assertEqual(adapter_code, 0, adapter_stderr)
        self.assertEqual(wrapper_code, 0, wrapper_stderr)
        self.assertEqual(json.loads(wrapper_stdout), json.loads(adapter_stdout))
        self.assertFalse(self.local_root.exists())

    def test_harness_deploy_wrapper_help_exposes_only_current_command_surface(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            harness_deploy.main(["--help"])

        self.assertEqual(raised.exception.code, 0)
        help_text = stdout.getvalue()
        self.assertIn("harness_deploy.py", help_text)
        self.assertIn("diagnose", help_text)
        self.assertIn("verify", help_text)
        self.assertIn("install", help_text)
        self.assertIn("update", help_text)
        self.assertNotIn("claude", help_text.lower())
        self.assertNotIn("opencode", help_text.lower())
        self.assertEqual(stderr.getvalue(), "")

    def test_local_npm_package_metadata_exposes_installer_bin_and_legacy_alias(self) -> None:
        package_path = self.source_repo_root / "toolchain" / "scripts" / "deploy" / "package.json"

        package = json.loads(package_path.read_text(encoding="utf-8"))

        self.assertTrue(package["private"])
        self.assertEqual(package["name"], "aw-installer")
        self.assertEqual(
            package["bin"],
            {
                "aw-installer": "bin/aw-installer.js",
                "aw-harness-deploy": "bin/aw-harness-deploy.js",
            },
        )
        self.assertIn("harness_deploy.py", package["files"])
        self.assertIn("adapter_deploy.py", package["files"])
        self.assertIn("bin/aw-installer.js", package["files"])
        self.assertIn("bin/aw-harness-deploy.js", package["files"])

    def test_root_npm_package_metadata_exposes_self_contained_envelope(self) -> None:
        package_path = self.source_repo_root / "package.json"
        package = json.loads(package_path.read_text(encoding="utf-8"))

        self.assertEqual(package["name"], "aw-installer")
        self.assertNotIn("private", package)
        self.assertEqual(
            package["bin"],
            {
                "aw-installer": "toolchain/scripts/deploy/bin/aw-installer.js",
                "aw-harness-deploy": "toolchain/scripts/deploy/bin/aw-harness-deploy.js",
            },
        )
        self.assertIn("product/harness/skills", package["files"])
        self.assertIn("product/harness/adapters/agents/skills", package["files"])
        self.assertIn("toolchain/scripts/deploy/harness_deploy.py", package["files"])
        self.assertIn("toolchain/scripts/deploy/adapter_deploy.py", package["files"])
        self.assertEqual(
            package["publishConfig"],
            {
                "registry": "https://registry.npmjs.org/",
                "access": "public",
            },
        )
        self.assertIn("toolchain/scripts/deploy/bin/check-root-publish.js", package["files"])
        self.assertEqual(
            package["scripts"]["prepublishOnly"],
            "node toolchain/scripts/deploy/bin/check-root-publish.js",
        )
        self.assertEqual(package["scripts"]["publish:dry-run"], "npm publish --dry-run --json")

    def test_root_npm_publish_guard_allows_publish_dry_run(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.source_repo_root
        guard_path = package_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js"
        env = {
            **os.environ,
            "npm_config_dry_run": "true",
        }

        completed = subprocess.run(
            ["node", str(guard_path)],
            cwd=package_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(completed.stderr, "")

    def test_root_npm_publish_guard_rejects_local_version_for_real_publish(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.source_repo_root
        guard_path = package_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js"
        env = {
            **os.environ,
        }
        env.pop("npm_config_dry_run", None)

        completed = subprocess.run(
            ["node", str(guard_path)],
            cwd=package_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout, "")
        self.assertIn("refusing to publish aw-installer 0.0.0-local", completed.stderr)

    def test_local_npm_installer_bin_help_preserves_current_command_surface(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        bin_path = (
            self.source_repo_root
            / "toolchain"
            / "scripts"
            / "deploy"
            / "bin"
            / "aw-installer.js"
        )

        completed = subprocess.run(
            ["node", str(bin_path), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("harness_deploy.py", completed.stdout)
        self.assertIn("diagnose", completed.stdout)
        self.assertIn("verify", completed.stdout)
        self.assertIn("install", completed.stdout)
        self.assertIn("update", completed.stdout)
        self.assertIn("tui", completed.stdout)
        self.assertEqual(completed.stderr, "")

    def test_local_npm_installer_bin_version_reports_package_version(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        bin_path = (
            self.source_repo_root
            / "toolchain"
            / "scripts"
            / "deploy"
            / "bin"
            / "aw-installer.js"
        )

        completed = subprocess.run(
            ["node", str(bin_path), "--version"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, "aw-installer 0.0.0-local\n")
        self.assertEqual(completed.stderr, "")

    def test_local_npm_installer_no_args_noninteractive_prints_help(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        bin_path = (
            self.source_repo_root
            / "toolchain"
            / "scripts"
            / "deploy"
            / "bin"
            / "aw-installer.js"
        )

        completed = subprocess.run(
            ["node", str(bin_path)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("usage: aw-installer", completed.stdout)
        self.assertIn("tui", completed.stdout)
        self.assertEqual(completed.stderr, "")

    def test_local_npm_installer_tui_refuses_noninteractive_stdio(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        bin_path = (
            self.source_repo_root
            / "toolchain"
            / "scripts"
            / "deploy"
            / "bin"
            / "aw-installer.js"
        )

        completed = subprocess.run(
            ["node", str(bin_path), "tui"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout, "")
        self.assertIn("requires an interactive terminal", completed.stderr)

    def test_local_npm_pack_dry_run_contains_only_package_surface(self) -> None:
        if shutil.which("npm") is None:
            self.skipTest("npm is not available")
        package_root = self.source_repo_root / "toolchain" / "scripts" / "deploy"

        completed = subprocess.run(
            ["npm", "pack", "--dry-run", "--json"],
            cwd=package_root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(len(payload), 1)
        packed_files = {entry["path"] for entry in payload[0]["files"]}
        self.assertEqual(
            packed_files,
            {
                "README.md",
                "adapter_deploy.py",
                "harness_deploy.py",
                "bin/aw-installer.js",
                "bin/aw-harness-deploy.js",
                "package.json",
            },
        )
        self.assertFalse((package_root / payload[0]["filename"]).exists())

    def test_root_npm_pack_dry_run_contains_self_contained_payload_surface(self) -> None:
        if shutil.which("npm") is None:
            self.skipTest("npm is not available")
        package_root = self.source_repo_root

        completed = subprocess.run(
            ["npm", "pack", "--dry-run", "--json"],
            cwd=package_root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(len(payload), 1)
        packed_files = {entry["path"] for entry in payload[0]["files"]}
        for required_path in {
            "package.json",
            "README.md",
            "LICENSE",
            "toolchain/scripts/deploy/adapter_deploy.py",
            "toolchain/scripts/deploy/harness_deploy.py",
            "toolchain/scripts/deploy/bin/aw-installer.js",
            "toolchain/scripts/deploy/bin/check-root-publish.js",
            "product/harness/skills/harness-skill/SKILL.md",
            "product/harness/adapters/agents/skills/harness-skill/payload.json",
        }:
            self.assertIn(required_path, packed_files)
        self.assertFalse(any(path.startswith(".aw/") for path in packed_files))
        self.assertFalse(any(path.startswith(".agents/") for path in packed_files))
        self.assertFalse((package_root / payload[0]["filename"]).exists())

    def test_root_npm_publish_dry_run_preserves_package_surface(self) -> None:
        if shutil.which("npm") is None:
            self.skipTest("npm is not available")
        package_root = self.source_repo_root

        completed = subprocess.run(
            ["npm", "run", "publish:dry-run", "--silent"],
            cwd=package_root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["name"], "aw-installer")
        self.assertEqual(payload["version"], "0.0.0-local")
        packed_files = {entry["path"] for entry in payload["files"]}
        self.assertIn("package.json", packed_files)
        self.assertIn("product/harness/skills/harness-skill/SKILL.md", packed_files)
        self.assertIn("toolchain/scripts/deploy/bin/aw-installer.js", packed_files)
        self.assertFalse((package_root / payload["filename"]).exists())

    def test_local_npm_packed_tarball_bin_help_preserves_current_command_surface(self) -> None:
        if shutil.which("npm") is None:
            self.skipTest("npm is not available")
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.source_repo_root / "toolchain" / "scripts" / "deploy"

        with tempfile.TemporaryDirectory() as package_dir:
            pack_completed = subprocess.run(
                ["npm", "pack", "--json", "--pack-destination", package_dir],
                cwd=package_root,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(pack_completed.returncode, 0, pack_completed.stderr)
            payload = json.loads(pack_completed.stdout)
            self.assertEqual(len(payload), 1)
            package_file = Path(package_dir) / payload[0]["filename"]
            self.assertTrue(package_file.is_file())
            self.assertFalse((package_root / payload[0]["filename"]).exists())

            exec_completed = subprocess.run(
                [
                    "npm",
                    "exec",
                    "--yes",
                    "--package",
                    str(package_file),
                    "--",
                    "aw-installer",
                    "--help",
                ],
                cwd=package_root,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(exec_completed.returncode, 0, exec_completed.stderr)
        self.assertIn("harness_deploy.py", exec_completed.stdout)
        self.assertIn("diagnose", exec_completed.stdout)
        self.assertIn("verify", exec_completed.stdout)
        self.assertIn("install", exec_completed.stdout)
        self.assertIn("update", exec_completed.stdout)
        self.assertIn("tui", exec_completed.stdout)
        self.assertEqual(exec_completed.stderr, "")

    def test_local_npm_packed_tarball_diagnose_uses_repo_root_override(self) -> None:
        if shutil.which("npm") is None:
            self.skipTest("npm is not available")
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.source_repo_root / "toolchain" / "scripts" / "deploy"

        with tempfile.TemporaryDirectory() as package_dir:
            pack_completed = subprocess.run(
                ["npm", "pack", "--json", "--pack-destination", package_dir],
                cwd=package_root,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(pack_completed.returncode, 0, pack_completed.stderr)
            payload = json.loads(pack_completed.stdout)
            package_file = Path(package_dir) / payload[0]["filename"]
            env = {
                **os.environ,
                "AW_HARNESS_REPO_ROOT": str(self.source_repo_root),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            diagnose_completed = subprocess.run(
                [
                    "npm",
                    "exec",
                    "--yes",
                    "--package",
                    str(package_file),
                    "--",
                    "aw-installer",
                    "diagnose",
                    "--backend",
                    "agents",
                    "--json",
                ],
                cwd=package_root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(diagnose_completed.returncode, 0, diagnose_completed.stderr)
        diagnose_payload = json.loads(diagnose_completed.stdout)
        self.assertEqual(diagnose_payload["backend"], "agents")
        self.assertGreater(diagnose_payload["binding_count"], 0)
        self.assertFalse((package_root / payload[0]["filename"]).exists())

    def test_local_npm_packed_tarball_update_dry_run_uses_repo_root_override(self) -> None:
        if shutil.which("npm") is None:
            self.skipTest("npm is not available")
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.source_repo_root / "toolchain" / "scripts" / "deploy"

        with tempfile.TemporaryDirectory() as package_dir:
            pack_completed = subprocess.run(
                ["npm", "pack", "--json", "--pack-destination", package_dir],
                cwd=package_root,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(pack_completed.returncode, 0, pack_completed.stderr)
            payload = json.loads(pack_completed.stdout)
            package_file = Path(package_dir) / payload[0]["filename"]
            env = {
                **os.environ,
                "AW_HARNESS_REPO_ROOT": str(self.source_repo_root),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            update_completed = subprocess.run(
                [
                    "npm",
                    "exec",
                    "--yes",
                    "--package",
                    str(package_file),
                    "--",
                    "aw-installer",
                    "update",
                    "--backend",
                    "agents",
                    "--json",
                ],
                cwd=package_root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(update_completed.returncode, 0, update_completed.stderr)
        update_payload = json.loads(update_completed.stdout)
        self.assertEqual(update_payload["backend"], "agents")
        self.assertEqual(update_payload["blocking_issue_count"], 0)
        self.assertGreater(len(update_payload["planned_target_paths"]), 0)
        self.assertFalse((package_root / payload[0]["filename"]).exists())

    def test_root_npm_packed_tarball_uses_package_source_and_cwd_target_without_override(self) -> None:
        if shutil.which("npm") is None:
            self.skipTest("npm is not available")
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.source_repo_root
        installed_harness_skill = False

        with tempfile.TemporaryDirectory() as package_dir:
            package_dir_path = Path(package_dir)
            target_repo = package_dir_path / "target-repo"
            target_repo.mkdir()
            pack_completed = subprocess.run(
                ["npm", "pack", "--json", "--pack-destination", package_dir],
                cwd=package_root,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(pack_completed.returncode, 0, pack_completed.stderr)
            payload = json.loads(pack_completed.stdout)
            package_file = package_dir_path / payload[0]["filename"]
            env = {
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            env.pop("AW_HARNESS_REPO_ROOT", None)
            env.pop("AW_HARNESS_TARGET_REPO_ROOT", None)
            diagnose_completed = subprocess.run(
                [
                    "npm",
                    "exec",
                    "--yes",
                    "--package",
                    str(package_file),
                    "--",
                    "aw-installer",
                    "diagnose",
                    "--backend",
                    "agents",
                    "--json",
                ],
                cwd=target_repo,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            version_completed = subprocess.run(
                [
                    "npm",
                    "exec",
                    "--yes",
                    "--package",
                    str(package_file),
                    "--",
                    "aw-installer",
                    "--version",
                ],
                cwd=target_repo,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            update_completed = subprocess.run(
                [
                    "npm",
                    "exec",
                    "--yes",
                    "--package",
                    str(package_file),
                    "--",
                    "aw-installer",
                    "update",
                    "--backend",
                    "agents",
                    "--json",
                ],
                cwd=target_repo,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            install_completed = subprocess.run(
                [
                    "npm",
                    "exec",
                    "--yes",
                    "--package",
                    str(package_file),
                    "--",
                    "aw-installer",
                    "install",
                    "--backend",
                    "agents",
                ],
                cwd=target_repo,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            installed_harness_skill = (
                target_repo / ".agents" / "skills" / "aw-harness-skill" / "SKILL.md"
            ).is_file()
            verify_completed = subprocess.run(
                [
                    "npm",
                    "exec",
                    "--yes",
                    "--package",
                    str(package_file),
                    "--",
                    "aw-installer",
                    "verify",
                    "--backend",
                    "agents",
                ],
                cwd=target_repo,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            update_apply_completed = subprocess.run(
                [
                    "npm",
                    "exec",
                    "--yes",
                    "--package",
                    str(package_file),
                    "--",
                    "aw-installer",
                    "update",
                    "--backend",
                    "agents",
                    "--yes",
                ],
                cwd=target_repo,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            update_applied_harness_skill = (
                target_repo / ".agents" / "skills" / "aw-harness-skill" / "SKILL.md"
            ).is_file()

        self.assertEqual(diagnose_completed.returncode, 0, diagnose_completed.stderr)
        diagnose_payload = json.loads(diagnose_completed.stdout)
        self.assertEqual(diagnose_payload["backend"], "agents")
        self.assertGreater(diagnose_payload["binding_count"], 0)
        self.assertEqual(
            diagnose_payload["target_root"],
            str(target_repo / ".agents" / "skills"),
        )
        self.assertNotEqual(diagnose_payload["source_root"], str(target_repo))

        self.assertEqual(version_completed.returncode, 0, version_completed.stderr)
        self.assertEqual(version_completed.stdout, "aw-installer 0.0.0-local\n")
        self.assertEqual(version_completed.stderr, "")

        self.assertEqual(update_completed.returncode, 0, update_completed.stderr)
        update_payload = json.loads(update_completed.stdout)
        self.assertEqual(update_payload["backend"], "agents")
        self.assertEqual(update_payload["blocking_issue_count"], 0)
        self.assertEqual(update_payload["target_root"], str(target_repo / ".agents" / "skills"))
        self.assertNotEqual(update_payload["source_root"], str(target_repo))
        self.assertGreater(len(update_payload["planned_target_paths"]), 0)
        self.assertTrue(
            all(
                path.startswith(str(target_repo / ".agents" / "skills"))
                for path in update_payload["planned_target_paths"]
            )
        )

        self.assertEqual(install_completed.returncode, 0, install_completed.stderr)
        self.assertIn("installed skill harness-skill", install_completed.stdout)
        self.assertTrue(installed_harness_skill)
        self.assertEqual(verify_completed.returncode, 0, verify_completed.stderr)
        self.assertIn("[agents] ok", verify_completed.stdout)
        self.assertEqual(update_apply_completed.returncode, 0, update_apply_completed.stderr)
        self.assertIn("[agents] applying update", update_apply_completed.stdout)
        self.assertIn("installed skill harness-skill", update_apply_completed.stdout)
        self.assertIn("[agents] ok", update_apply_completed.stdout)
        self.assertIn("[agents] update complete", update_apply_completed.stdout)
        self.assertTrue(update_applied_harness_skill)

    def test_install_uses_override_root(self) -> None:
        code, stdout, stderr = self._install("--agents-root", self.override_root)

        self.assertEqual(code, 0, stderr)
        self.assertTrue(self.override_root.is_dir())
        self.assertTrue((self.override_root / "aw-harness-skill").is_dir())
        self.assertIn(str(self.override_root), stdout)
        self.assertFalse(self.local_root.exists())

    def test_update_dry_run_reports_plan_without_mutating(self) -> None:
        code, stdout, stderr = self._update()

        self.assertEqual(code, 0, stderr)
        self.assertIn("[agents] update plan", stdout)
        self.assertIn("sequence: prune --all -> check_paths_exist -> install -> verify", stdout)
        self.assertIn("target paths to write:", stdout)
        self.assertIn("dry-run only; pass --yes to apply update", stdout)
        self.assertFalse(self.local_root.exists())

    def test_update_json_dry_run_reports_machine_readable_plan(self) -> None:
        code, stdout, stderr = self._update("--json")

        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(payload["backend"], "agents")
        self.assertEqual(payload["blocking_issue_count"], 0)
        self.assertEqual(
            payload["operation_sequence"],
            ["prune --all", "check_paths_exist", "install", "verify"],
        )
        self.assertGreater(len(payload["planned_target_paths"]), 0)
        self.assertEqual(stderr, "")
        self.assertFalse(self.local_root.exists())

    def test_update_rejects_json_apply_combo(self) -> None:
        code, stdout, stderr = self._update("--json", "--yes")

        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("update --json is only supported for dry-run plans", stderr)

    def test_update_yes_installs_and_verifies_from_missing_root(self) -> None:
        code, stdout, stderr = self._update("--yes")

        self.assertEqual(code, 0, stderr)
        self.assertTrue((self.local_root / "aw-harness-skill").is_dir())
        self.assertIn("[agents] applying update", stdout)
        self.assertIn("installed skill harness-skill", stdout)
        self.assertIn("[agents] ok", stdout)
        self.assertIn("[agents] update complete", stdout)

    def test_update_yes_refreshes_drifted_managed_install(self) -> None:
        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        self._mutate_canonical_skill("harness-skill", "\n# updated source\n")
        target_wrapper_path = self.local_root / "aw-harness-skill" / "SKILL.md"

        code, stdout, stderr = self._update("--yes")

        self.assertEqual(code, 0, stderr)
        self.assertIn("removed managed skill dir", stdout)
        self.assertEqual(
            target_wrapper_path.read_text(encoding="utf-8"),
            (
                self.fake_repo_root
                / "product"
                / "harness"
                / "skills"
                / "harness-skill"
                / "SKILL.md"
            ).read_text(encoding="utf-8"),
        )
        code, stdout, stderr = self._verify()
        self.assertEqual(code, 0, stderr)

    def test_update_blocks_unrecognized_target_dir_without_writing(self) -> None:
        self.local_root.mkdir(parents=True, exist_ok=True)
        foreign_skill_dir = self._install_foreign_conflict()

        code, stdout, stderr = self._update("--yes")

        self.assertEqual(code, 1)
        self.assertIn("blocking preflight issues: 1", stdout)
        self.assertIn("unrecognized-target-directory", stdout)
        self.assertIn("update blocked", stderr)
        self.assertTrue(foreign_skill_dir.is_dir())
        self.assertFalse((self.local_root / "aw-dispatch-skills").exists())

    def test_update_blocks_foreign_managed_directory_without_writing(self) -> None:
        self.local_root.mkdir(parents=True, exist_ok=True)
        foreign_dir = self._install_managed_directory("foreign-managed", backend="claude")

        code, stdout, stderr = self._update("--yes")

        self.assertEqual(code, 1)
        self.assertIn("foreign-managed-directory", stdout)
        self.assertIn("update blocked", stderr)
        self.assertTrue(foreign_dir.is_dir())
        self.assertFalse((self.local_root / "aw-harness-skill").exists())

    def test_check_paths_exist_reports_ok_when_paths_are_free(self) -> None:
        code, stdout, stderr = self._check_paths_exist()

        self.assertEqual(code, 0, stderr)
        self.assertIn("[agents] ok: no conflicting target paths", stdout)

    def test_check_paths_exist_reports_legacy_directory_occupied(self) -> None:
        # Create an unmanaged directory that matches a legacy_target_dirs entry
        self.local_root.mkdir(parents=True, exist_ok=True)
        (self.local_root / "aw-harness-skill").mkdir()
        legacy_dir = self.local_root / "harness-skill"
        legacy_dir.mkdir()
        (legacy_dir / "SKILL.md").write_text("# unmanaged old skill\n", encoding="utf-8")

        code, stdout, stderr = self._check_paths_exist()

        self.assertEqual(code, 1)
        self.assertIn("legacy directory harness-skill is occupied by unmanaged content", stderr)

    def test_check_paths_exist_lists_all_conflicts(self) -> None:
        self.local_root.mkdir(parents=True, exist_ok=True)
        (self.local_root / "aw-harness-skill").mkdir()
        (self.local_root / "aw-dispatch-skills").mkdir()

        code, stdout, stderr = self._check_paths_exist()

        self.assertEqual(code, 1)
        self.assertIn("target path conflicts:", stderr)
        self.assertIn("harness-skill", stderr)
        self.assertIn("dispatch-skills", stderr)

    def test_check_paths_exist_reports_file_and_broken_symlink_conflicts(self) -> None:
        self.local_root.mkdir(parents=True, exist_ok=True)
        (self.local_root / "aw-harness-skill").write_text("occupied by file\n", encoding="utf-8")
        (self.local_root / "aw-dispatch-skills").symlink_to(
            self.temp_root / "missing-dispatch-skills",
            target_is_directory=True,
        )

        code, stdout, stderr = self._check_paths_exist()

        self.assertEqual(code, 1)
        self.assertIn("harness-skill", stderr)
        self.assertIn("existing target path is a file", stderr)
        self.assertIn("dispatch-skills", stderr)
        self.assertIn("existing target path is a broken symlink", stderr)

    def test_install_fails_on_existing_foreign_conflict_without_writing_other_skills(self) -> None:
        self.local_root.mkdir(parents=True, exist_ok=True)
        foreign_skill_dir = self._install_foreign_conflict()

        code, stdout, stderr = self._install()

        self.assertEqual(code, 1)
        self.assertIn("install blocked by 1 existing target path", stderr)
        self.assertIn("harness-skill", stderr)
        self.assertTrue(foreign_skill_dir.is_dir())
        self.assertFalse((self.local_root / "aw-dispatch-skills").exists())

    def test_install_blocked_by_legacy_directory_occupied(self) -> None:
        # Create an unmanaged directory that matches a legacy_target_dirs entry
        self.local_root.mkdir(parents=True, exist_ok=True)
        legacy_dir = self.local_root / "harness-skill"
        legacy_dir.mkdir()
        (legacy_dir / "SKILL.md").write_text("# unmanaged old skill\n", encoding="utf-8")

        code, stdout, stderr = self._install()

        self.assertEqual(code, 1)
        self.assertIn("install blocked by 1 existing target path", stderr)
        self.assertIn("legacy directory harness-skill is occupied by unmanaged content", stderr)
        self.assertFalse((self.local_root / "aw-harness-skill").exists())
        self.assertFalse((self.local_root / "aw-dispatch-skills").exists())

    def test_install_does_not_incrementally_rewrite_existing_managed_directories(self) -> None:
        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        target_wrapper_path = self.local_root / "aw-harness-skill" / "SKILL.md"
        original_target_wrapper = target_wrapper_path.read_text(encoding="utf-8")
        self._mutate_canonical_skill("harness-skill", "\n# new live source\n")

        code, stdout, stderr = self._install()

        self.assertEqual(code, 1)
        self.assertIn("install blocked by", stderr)
        self.assertIn("harness-skill", stderr)
        self.assertEqual(
            target_wrapper_path.read_text(encoding="utf-8"),
            original_target_wrapper,
        )
        self.assertNotEqual(
            target_wrapper_path.read_text(encoding="utf-8"),
            (
                self.fake_repo_root
                / "product"
                / "harness"
                / "skills"
                / "harness-skill"
                / "SKILL.md"
            ).read_text(encoding="utf-8"),
        )

    def test_install_fails_on_duplicate_target_dir_bindings_before_writing(self) -> None:
        self._mutate_target_dir("dispatch-skills", "aw-harness-skill")

        code, stdout, stderr = self._install()

        self.assertEqual(code, 1)
        self.assertIn(
            "Multiple skills map to the same target_dir for backend agents: aw-harness-skill",
            stderr,
        )
        self.assertFalse((self.local_root / "aw-harness-skill").exists())
        self.assertFalse((self.local_root / "aw-dispatch-skills").exists())

    def test_install_rejects_payload_target_dir_that_escapes_target_root(self) -> None:
        payload_path = self.adapter_dir / "harness-skill" / "payload.json"
        payload = self._load_json(payload_path)
        payload["target_dir"] = "../escaped-skill"
        payload_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        code, stdout, stderr = self._install()

        self.assertEqual(code, 1)
        self.assertIn("payload-contract-invalid", stderr)
        self.assertIn("must not contain '..' path segments", stderr)

    def test_install_rejects_payload_identity_field_mismatches(self) -> None:
        payload_path = self.adapter_dir / "harness-skill" / "payload.json"
        payload = self._load_json(payload_path)
        payload["payload_version"] = "agents-skill-payload.v999"
        payload["backend"] = "claude"
        payload["skill_id"] = "other-skill"
        payload_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        code, stdout, stderr = self._install()

        self.assertEqual(code, 1)
        self.assertIn("payload-contract-invalid", stderr)
        self.assertIn("payload payload_version must be agents-skill-payload.v1", stderr)
        self.assertIn("payload backend must be agents", stderr)
        self.assertIn("payload skill_id must be harness-skill", stderr)

    def test_install_rejects_non_directory_target_root(self) -> None:
        self.local_root.parent.mkdir(parents=True, exist_ok=True)
        self.local_root.write_text("not a directory\n", encoding="utf-8")

        code, stdout, stderr = self._install()

        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("exists but is not a directory", stderr)

    def test_prune_all_removes_only_managed_skill_dirs(self) -> None:
        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        foreign_dir = self._install_foreign_conflict("foreign-skill")

        code, stdout, stderr = self._prune_all()

        self.assertEqual(code, 0, stderr)
        self.assertIn("removed managed skill dir", stdout)
        self.assertTrue(foreign_dir.is_dir())
        self.assertFalse((self.local_root / "aw-harness-skill").exists())
        self.assertFalse((self.local_root / "aw-dispatch-skills").exists())

    def test_prune_all_keeps_foreign_and_invalid_marker_dirs(self) -> None:
        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        foreign_dir = self._install_managed_directory("foreign-managed", backend="claude")
        invalid_dir = self.local_root / "broken-managed"
        invalid_dir.mkdir(parents=True, exist_ok=True)
        (invalid_dir / "aw.marker").write_text("{invalid json\n", encoding="utf-8")

        code, stdout, stderr = self._prune_all()

        self.assertEqual(code, 0, stderr)
        self.assertFalse((self.local_root / "aw-harness-skill").exists())
        self.assertTrue(foreign_dir.is_dir())
        self.assertTrue(invalid_dir.is_dir())

    def test_prune_all_is_noop_when_target_root_is_missing(self) -> None:
        code, stdout, stderr = self._prune_all()

        self.assertEqual(code, 0, stderr)
        self.assertIn("no managed skill dirs found", stdout)

    def test_install_succeeds_after_prune_all_and_check_paths_exist(self) -> None:
        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)

        code, stdout, stderr = self._prune_all()
        self.assertEqual(code, 0, stderr)
        self.assertFalse((self.local_root / "aw-harness-skill").exists())

        code, stdout, stderr = self._check_paths_exist()
        self.assertEqual(code, 0, stderr)

        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        self.assertTrue((self.local_root / "aw-harness-skill").is_dir())

    def test_verify_reports_missing_target_root(self) -> None:
        code, stdout, stderr = self._verify()

        self.assertEqual(code, 1, stderr)
        self.assertIn("missing-target-root", stdout)

    def test_verify_reports_ok_after_install(self) -> None:
        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)

        code, stdout, stderr = self._verify()

        self.assertEqual(code, 0, stderr)
        self.assertIn("[agents] ok", stdout)

    def test_verify_ignores_foreign_backend_marker_dir(self) -> None:
        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        foreign_dir = self._install_managed_directory("foreign-managed", backend="claude")

        code, stdout, stderr = self._verify()

        self.assertEqual(code, 0, stderr)
        self.assertIn("[agents] ok", stdout)
        self.assertTrue(foreign_dir.is_dir())

    def test_verify_reports_unrecognized_target_directory_when_marker_is_missing(self) -> None:
        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        self._remove_target_marker("harness-skill")

        code, stdout, stderr = self._verify()

        self.assertEqual(code, 1, stderr)
        self.assertIn("unrecognized-target-directory", stdout)
        self.assertIn("harness-skill", stdout)

    def test_verify_reports_missing_target_entry_when_skill_dir_is_missing(self) -> None:
        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        shutil.rmtree(self.local_root / "aw-dispatch-skills")

        code, stdout, stderr = self._verify()

        self.assertEqual(code, 1, stderr)
        self.assertIn("missing-target-entry", stdout)
        self.assertIn("dispatch-skills", stdout)

    def test_verify_reports_target_payload_drift_for_modified_target_file(self) -> None:
        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        target_dir_name = self._target_dir_for_skill("repo-status-skill")
        wrapper_path = self.local_root / target_dir_name / "SKILL.md"
        wrapper_path.write_text("# drifted target\n", encoding="utf-8")

        code, stdout, stderr = self._verify()

        self.assertEqual(code, 1, stderr)
        self.assertIn("target-payload-drift", stdout)
        self.assertIn("repo-status-skill", stdout)

    def test_verify_reports_target_payload_drift_for_source_fingerprint_change(self) -> None:
        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        self._mutate_canonical_skill("harness-skill")

        code, stdout, stderr = self._verify()

        self.assertEqual(code, 1, stderr)
        self.assertIn("target-payload-drift", stdout)
        self.assertIn("harness-skill", stdout)

    def test_verify_reports_unexpected_managed_directory(self) -> None:
        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        unexpected_dir = self._install_managed_directory("retired-skill", marker_skill_id="retired-skill")

        code, stdout, stderr = self._verify()

        self.assertEqual(code, 1, stderr)
        self.assertIn("unexpected-managed-directory", stdout)
        self.assertIn(str(unexpected_dir), stdout)

    def test_payload_target_metadata_parses_legacy_target_dirs(self) -> None:
        binding = self._binding("harness-skill")
        payload = self._load_json(binding.payload_path)
        payload["legacy_target_dirs"] = ["old-harness-skill", "very-old-harness-skill"]
        metadata = adapter_deploy.payload_target_metadata(payload, binding)
        self.assertEqual(metadata.legacy_target_dirs, ["old-harness-skill", "very-old-harness-skill"])

    def test_payload_target_metadata_rejects_legacy_dir_with_path_separator(self) -> None:
        binding = self._binding("harness-skill")
        payload = self._load_json(binding.payload_path)
        payload["legacy_target_dirs"] = ["old/harness-skill"]
        with self.assertRaises(adapter_deploy.DeployError) as ctx:
            adapter_deploy.payload_target_metadata(payload, binding)
        self.assertIn("must be single directory names", str(ctx.exception))

    def test_payload_target_metadata_rejects_target_dir_in_legacy_target_dirs(self) -> None:
        binding = self._binding("harness-skill")
        payload = self._load_json(binding.payload_path)
        payload["legacy_target_dirs"] = ["aw-harness-skill"]
        with self.assertRaises(adapter_deploy.DeployError) as ctx:
            adapter_deploy.payload_target_metadata(payload, binding)
        self.assertIn("must not be listed in legacy_target_dirs", str(ctx.exception))

    def test_payload_target_metadata_rejects_legacy_target_dirs_string(self) -> None:
        binding = self._binding("harness-skill")
        payload = self._load_json(binding.payload_path)
        payload["legacy_target_dirs"] = "harness-skill"
        with self.assertRaises(adapter_deploy.DeployError) as ctx:
            adapter_deploy.payload_target_metadata(payload, binding)
        self.assertIn("legacy_target_dirs must be a list of strings", str(ctx.exception))

    def test_payload_target_metadata_rejects_legacy_skill_ids_string(self) -> None:
        binding = self._binding("harness-skill")
        payload = self._load_json(binding.payload_path)
        payload["legacy_skill_ids"] = "old-harness-skill"
        with self.assertRaises(adapter_deploy.DeployError) as ctx:
            adapter_deploy.payload_target_metadata(payload, binding)
        self.assertIn("legacy_skill_ids must be a list of strings", str(ctx.exception))

    def test_payload_target_metadata_parses_legacy_skill_ids(self) -> None:
        binding = self._binding("harness-skill")
        payload = self._load_json(binding.payload_path)
        payload["legacy_skill_ids"] = ["old-harness-skill", "very-old-harness-skill"]
        metadata = adapter_deploy.payload_target_metadata(payload, binding)
        self.assertEqual(metadata.legacy_skill_ids, ["old-harness-skill", "very-old-harness-skill"])

    def test_payload_target_metadata_rejects_skill_id_in_legacy_skill_ids(self) -> None:
        binding = self._binding("harness-skill")
        payload = self._load_json(binding.payload_path)
        payload["legacy_skill_ids"] = ["harness-skill"]
        with self.assertRaises(adapter_deploy.DeployError) as ctx:
            adapter_deploy.payload_target_metadata(payload, binding)
        self.assertIn("must not be listed in legacy_skill_ids", str(ctx.exception))

    def test_install_removes_legacy_managed_directory(self) -> None:
        self._install_managed_directory("old-harness-skill", marker_skill_id="old-harness-skill")
        self.assertTrue((self.local_root / "old-harness-skill").is_dir())

        payload_path = self.adapter_dir / "harness-skill" / "payload.json"
        payload = self._load_json(payload_path)
        payload["legacy_target_dirs"] = ["old-harness-skill"]
        payload["legacy_skill_ids"] = ["old-harness-skill"]
        payload_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        self.assertIn("removed legacy skill dir", stdout)
        self.assertFalse((self.local_root / "old-harness-skill").exists())
        self.assertTrue((self.local_root / "aw-harness-skill").is_dir())

        code, stdout, stderr = self._verify()
        self.assertEqual(code, 0, stderr)
        self.assertIn("[agents] ok", stdout)

    def test_install_removes_legacy_with_current_skill_id_marker(self) -> None:
        self._install_managed_directory("old-harness-skill", marker_skill_id="harness-skill")
        self.assertTrue((self.local_root / "old-harness-skill").is_dir())

        payload_path = self.adapter_dir / "harness-skill" / "payload.json"
        payload = self._load_json(payload_path)
        payload["legacy_target_dirs"] = ["old-harness-skill"]
        payload["legacy_skill_ids"] = ["old-harness-skill"]
        payload_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        self.assertIn("removed legacy skill dir", stdout)
        self.assertFalse((self.local_root / "old-harness-skill").exists())

    def test_install_blocks_on_legacy_directory_with_mismatched_marker(self) -> None:
        self._install_managed_directory("old-harness-skill", marker_skill_id="other-skill")
        self.assertTrue((self.local_root / "old-harness-skill").is_dir())

        payload_path = self.adapter_dir / "harness-skill" / "payload.json"
        payload = self._load_json(payload_path)
        payload["legacy_target_dirs"] = ["old-harness-skill"]
        payload["legacy_skill_ids"] = ["old-harness-skill"]
        payload_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        code, stdout, stderr = self._install()
        self.assertEqual(code, 1, stderr)
        self.assertIn("install blocked by 1 existing target path", stderr)
        self.assertIn("legacy directory old-harness-skill is occupied by unmanaged content", stderr)
        self.assertNotIn("removed legacy skill dir", stdout)
        self.assertTrue((self.local_root / "old-harness-skill").is_dir())
        self.assertFalse((self.local_root / "aw-harness-skill").exists())

    def test_verify_reports_legacy_managed_directory_not_cleaned(self) -> None:
        self._install_managed_directory("old-harness-skill", marker_skill_id="old-harness-skill")
        self.assertTrue((self.local_root / "old-harness-skill").is_dir())

        payload_path = self.adapter_dir / "harness-skill" / "payload.json"
        payload = self._load_json(payload_path)
        payload["legacy_target_dirs"] = ["old-harness-skill"]
        payload["legacy_skill_ids"] = ["old-harness-skill"]
        payload_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        code, stdout, stderr = self._verify()

        self.assertEqual(code, 1, stderr)
        self.assertIn("unexpected-managed-directory", stdout)
        self.assertIn("old-harness-skill", stdout)

    def test_verify_reports_wrong_target_root_type(self) -> None:
        self.local_root.parent.mkdir(parents=True, exist_ok=True)
        self.local_root.write_text("not a directory\n", encoding="utf-8")

        code, stdout, stderr = self._verify()

        self.assertEqual(code, 1, stderr)
        self.assertIn("wrong-target-root-type", stdout)

    def test_rejects_symlinked_target_root_for_install_and_verify(self) -> None:
        self.local_root.parent.mkdir(parents=True, exist_ok=True)
        real_root = self.temp_root / "redirected-agents-skills"
        real_root.mkdir(parents=True, exist_ok=True)
        self.local_root.symlink_to(real_root, target_is_directory=True)

        code, stdout, stderr = self._install()

        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("must be a real directory, not a symlink", stderr)

        code, stdout, stderr = self._verify()

        self.assertEqual(code, 1, stderr)
        self.assertIn("wrong-target-root-type", stdout)
        self.assertIn("must be a real directory, not a symlink", stdout)


if __name__ == "__main__":
    unittest.main()
