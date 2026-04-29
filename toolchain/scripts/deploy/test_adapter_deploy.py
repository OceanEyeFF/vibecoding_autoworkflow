from __future__ import annotations

import contextlib
import errno
import io
import json
import os
import select
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import adapter_deploy
import harness_deploy


class AdapterDeployTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temp_dir.name)
        self.source_repo_root = Path(__file__).resolve().parents[3]
        self.fake_repo_root = self.temp_root / "repo"
        self.local_root = self.fake_repo_root / ".agents" / "skills"
        self.claude_local_root = self.fake_repo_root / ".claude" / "skills"
        self.override_root = self.temp_root / "custom-root" / "skills"
        self.claude_override_root = self.temp_root / "custom-claude-root" / "skills"
        self.npm_state_root = self.temp_root / "npm-state"
        self.npm_state_root.mkdir(parents=True)
        (self.npm_state_root / "cache").mkdir()
        (self.npm_state_root / "tmp").mkdir()
        (self.npm_state_root / "npmrc").write_text(
            "audit=false\nfund=false\nupdate-notifier=false\n",
            encoding="utf-8",
        )
        self.npm_env_patch = mock.patch.dict(
            os.environ,
            {
                "NPM_CONFIG_CACHE": str(self.npm_state_root / "cache"),
                "NPM_CONFIG_USERCONFIG": str(self.npm_state_root / "npmrc"),
                "TMPDIR": str(self.npm_state_root / "tmp"),
            },
            clear=False,
        )
        self.npm_env_patch.start()
        self.addCleanup(self.npm_env_patch.stop)
        self.adapter_dir = (
            self.fake_repo_root / "product" / "harness" / "adapters" / "agents" / "skills"
        )
        self.claude_adapter_dir = (
            self.fake_repo_root / "product" / "harness" / "adapters" / "claude" / "skills"
        )

        self._seed_fake_repo()
        self.context = adapter_deploy.build_deploy_context(
            self.fake_repo_root,
            self.fake_repo_root,
        )

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

    def _run_cli(
        self, *argv: object, env: dict[str, str] | None = None
    ) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        command_env = self._deploy_env()
        if env is not None:
            command_env.update(env)
        env_patch = mock.patch.dict("os.environ", command_env, clear=False)
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
        env_patch = mock.patch.dict("os.environ", self._deploy_env(), clear=False)
        with (
            env_patch,
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            return harness_deploy.main([*map(str, argv)]), stdout.getvalue(), stderr.getvalue()

    def _deploy_env(self) -> dict[str, str]:
        return {
            "AW_HARNESS_REPO_ROOT": str(self.fake_repo_root),
            "AW_HARNESS_TARGET_REPO_ROOT": str(self.fake_repo_root),
        }

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

    def _claude_install(self, *extra_args: object) -> tuple[int, str, str]:
        return self._run_cli("install", "--backend", "claude", *extra_args)

    def _claude_verify(self, *extra_args: object) -> tuple[int, str, str]:
        return self._run_cli("verify", "--backend", "claude", *extra_args)

    def _claude_update(self, *extra_args: object) -> tuple[int, str, str]:
        return self._run_cli("update", "--backend", "claude", *extra_args)

    def _load_json(self, path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _release_package_metadata(self, version: str, *, channel: str | None = None) -> dict[str, object]:
        prerelease = version.split("-", 1)[1] if "-" in version else ""
        approved_channel = channel
        if approved_channel is None:
            if "canary" in prerelease.split("."):
                approved_channel = "canary"
            elif prerelease.startswith(("alpha", "beta", "rc")):
                approved_channel = "next"
            else:
                approved_channel = "latest"
        return {
            "name": "aw-installer",
            "version": version,
            "awInstallerRelease": {
                "realPublishApproval": "approved",
                "approvedVersion": version,
                "approvedGitTag": f"v{version}",
                "approvedChannel": approved_channel,
            },
        }

    def _binding(self, skill_id: str, backend: str = "agents") -> adapter_deploy.SkillBinding:
        return next(
            binding
            for binding in adapter_deploy.collect_skill_bindings(backend, self.context)
            if binding.skill_id == skill_id
        )

    def _install_plan(
        self,
        skill_id: str,
        root: Path | None = None,
        backend: str = "agents",
    ) -> adapter_deploy.InstallPlan:
        if root is None:
            root = self.local_root if backend == "agents" else self.claude_local_root
        return adapter_deploy.build_install_plan(
            self._binding(skill_id, backend=backend),
            root,
            self.context,
        )

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

    def _fake_github_archive_bytes(self) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for path in sorted(self.fake_repo_root.rglob("*")):
                if path.is_file():
                    archive.write(path, Path("repo-master") / path.relative_to(self.fake_repo_root))
        return buffer.getvalue()

    def _fake_urlopen_response(self, payload: bytes):
        class Response:
            def __init__(self_inner):
                self_inner.stream = io.BytesIO(payload)

            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, exc_type, exc, traceback):
                return False

            def read(self_inner, size: int = -1):
                return self_inner.stream.read(size)

        return Response()

    def _fake_sleeping_python_bin(self) -> Path:
        fake_bin = self.temp_root / "fake-python-bin"
        fake_bin.mkdir()
        fake_python = fake_bin / "python3"
        fake_python.write_text("#!/usr/bin/env sh\nsleep 1\n", encoding="utf-8")
        fake_python.chmod(0o755)
        return fake_bin

    def _fake_python_fallback_bin(self) -> Path:
        fake_bin = self.temp_root / "fake-python-fallback-bin"
        fake_bin.mkdir()
        fake_python = fake_bin / "python"
        fake_python.write_text(
            "#!/bin/sh\nprintf 'fake-python %s\\n' \"$*\"\n",
            encoding="utf-8",
        )
        fake_python.chmod(0o755)
        return fake_bin

    def _remove_target_marker(self, skill_id: str) -> Path:
        target_dir_name = self._target_dir_for_skill(skill_id)
        marker_path = self.local_root / target_dir_name / "aw.marker"
        if marker_path.exists():
            marker_path.unlink()
        return marker_path.parent

    def _run_installer_tui_script(
        self,
        steps: list[tuple[str, str]],
        *,
        target_repo: Path | None = None,
        env_overrides: dict[str, str] | None = None,
        timeout_seconds: float = 90.0,
    ) -> tuple[int, str]:
        if not hasattr(os, "openpty"):
            self.skipTest("PTY support is not available")
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
        if target_repo is None:
            target_repo = self.temp_root / "tui-target"
        target_repo.mkdir(parents=True, exist_ok=True)
        env = {
            **os.environ,
            "AW_HARNESS_REPO_ROOT": str(self.source_repo_root),
            "AW_HARNESS_TARGET_REPO_ROOT": str(target_repo),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        if env_overrides is not None:
            env.update(env_overrides)

        master_fd, slave_fd = os.openpty()
        process: subprocess.Popen[bytes] | None = None
        output_parts: list[str] = []
        try:
            process = subprocess.Popen(
                ["node", str(bin_path), "tui"],
                cwd=self.source_repo_root,
                env=env,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                close_fds=True,
            )
            os.close(slave_fd)
            slave_fd = -1

            step_index = 0
            search_pos = 0
            deadline = time.monotonic() + timeout_seconds
            while time.monotonic() < deadline:
                ready, _, _ = select.select([master_fd], [], [], 0.05)
                if ready:
                    try:
                        chunk = os.read(master_fd, 4096)
                    except OSError as exc:
                        if exc.errno == errno.EIO:
                            break
                        raise
                    if not chunk:
                        break
                    output_parts.append(chunk.decode("utf-8", errors="replace"))

                output = "".join(output_parts)
                while step_index < len(steps):
                    pattern, response = steps[step_index]
                    match_index = output.find(pattern, search_pos)
                    if match_index == -1:
                        break
                    search_pos = match_index + len(pattern)
                    if response:
                        os.write(master_fd, response.encode("utf-8"))
                    step_index += 1

                if process.poll() is not None:
                    break

            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
                self.fail(
                    "timed out waiting for aw-installer tui; output so far:\n"
                    + "".join(output_parts)
                )

            while True:
                ready, _, _ = select.select([master_fd], [], [], 0)
                if not ready:
                    break
                try:
                    chunk = os.read(master_fd, 4096)
                except OSError as exc:
                    if exc.errno == errno.EIO:
                        break
                    raise
                if not chunk:
                    break
                output_parts.append(chunk.decode("utf-8", errors="replace"))

            return process.returncode or 0, "".join(output_parts)
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            if slave_fd != -1:
                os.close(slave_fd)
            os.close(master_fd)

    def test_install_creates_target_root_and_installs_agents_payloads(self) -> None:
        code, stdout, stderr = self._install()

        self.assertEqual(code, 0, stderr)
        self.assertTrue(self.local_root.is_dir())
        self.assertFalse(self.claude_local_root.exists())
        self.assertIn("created target root", stdout)

        for source_payload_dir in sorted(path for path in self.adapter_dir.iterdir() if path.is_dir()):
            skill_id = source_payload_dir.name
            payload = self._load_json(source_payload_dir / "payload.json")
            target_dir_name = payload["target_dir"]
            target_skill_dir = self.local_root / target_dir_name
            canonical_source = adapter_deploy.payload_canonical_source_metadata(
                payload,
                self._binding(skill_id),
                self.context,
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

    def test_backend_choices_include_claude(self) -> None:
        args = adapter_deploy.parse_args(["diagnose", "--backend", "claude"])

        self.assertEqual(args.backend, "claude")
        self.assertIn("claude", adapter_deploy.SUPPORTED_BACKENDS)

    def test_claude_default_target_root_is_claude_skills(self) -> None:
        code, stdout, stderr = self._run_cli(
            "diagnose",
            "--backend",
            "claude",
            "--json",
        )

        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(payload["backend"], "claude")
        self.assertEqual(payload["target_root"], str(self.claude_local_root))
        self.assertEqual(
            payload["binding_count"],
            1,
        )
        self.assertFalse(self.local_root.exists())

    def test_claude_install_verify_and_update_dry_run_use_claude_payloads(self) -> None:
        install_code, install_stdout, install_stderr = self._claude_install()
        verify_code, verify_stdout, verify_stderr = self._claude_verify()
        update_code, update_stdout, update_stderr = self._claude_update()
        update_json_code, update_json_stdout, update_json_stderr = self._claude_update("--json")

        self.assertEqual(install_code, 0, install_stderr)
        self.assertIn("installed skill set-harness-goal-skill", install_stdout)
        target_skill_dir = self.claude_local_root / "aw-set-harness-goal-skill"
        self.assertTrue((target_skill_dir / "SKILL.md").is_file())
        payload = self._load_json(
            target_skill_dir / "payload.json"
        )
        self.assertEqual(payload["backend"], "claude")
        self.assertEqual(payload["skill_id"], "set-harness-goal-skill")
        self.assertEqual(payload["payload_version"], "claude-skill-payload.v1")
        marker = self._load_json(target_skill_dir / "aw.marker")
        self.assertEqual(marker["backend"], "claude")
        self.assertEqual(marker["skill_id"], "set-harness-goal-skill")
        self.assertEqual(marker["payload_version"], "claude-skill-payload.v1")
        self.assertFalse(self.local_root.exists())

        self.assertEqual(verify_code, 0, verify_stderr)
        self.assertIn("[claude] ok", verify_stdout)

        self.assertEqual(update_code, 0, update_stderr)
        self.assertIn("[claude] update plan", update_stdout)
        self.assertIn(str(target_skill_dir), update_stdout)
        self.assertIn("dry-run only; pass --yes to apply update", update_stdout)

        self.assertEqual(update_json_code, 0, update_json_stderr)
        update_payload = json.loads(update_json_stdout)
        self.assertEqual(update_payload["backend"], "claude")
        self.assertEqual(update_payload["target_root"], str(self.claude_local_root))
        self.assertEqual(update_payload["blocking_issue_count"], 0)
        self.assertTrue(
            all(
                path.startswith(str(self.claude_local_root))
                for path in update_payload["planned_target_paths"]
            )
        )

    def test_claude_root_override_is_used_without_touching_agents_root(self) -> None:
        code, stdout, stderr = self._claude_install("--claude-root", self.claude_override_root)

        self.assertEqual(code, 0, stderr)
        self.assertTrue((self.claude_override_root / "aw-set-harness-goal-skill").is_dir())
        self.assertIn(str(self.claude_override_root), stdout)
        self.assertFalse(self.claude_local_root.exists())
        self.assertFalse(self.local_root.exists())

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

    def test_adapter_main_fails_if_parsed_mode_has_no_handler(self) -> None:
        with mock.patch.dict(adapter_deploy.MODE_HANDLERS, {"verify": None}):
            code, stdout, stderr = self._verify()

        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("Unsupported mode after parsing: verify", stderr)

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

    def test_cli_derives_runtime_context_from_env_after_import(self) -> None:
        target_repo = self.temp_root / "env-target"

        code, stdout, stderr = self._run_cli(
            "diagnose",
            "--backend",
            "agents",
            "--json",
            env={
                "AW_HARNESS_REPO_ROOT": str(self.fake_repo_root),
                "AW_HARNESS_TARGET_REPO_ROOT": str(target_repo),
            },
        )

        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(payload["source_root"], str(self.fake_repo_root))
        self.assertEqual(payload["target_root"], str(target_repo / ".agents" / "skills"))
        self.assertFalse(self.local_root.exists())

    def test_cli_rejects_sensitive_target_repo_root_env_override(self) -> None:
        code, stdout, stderr = self._run_cli(
            "diagnose",
            "--backend",
            "agents",
            "--json",
            env={
                "AW_HARNESS_REPO_ROOT": str(self.fake_repo_root),
                "AW_HARNESS_TARGET_REPO_ROOT": "/etc",
            },
        )

        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("Target repo root is protected", stderr)
        self.assertIn("/etc", stderr)

    def test_target_repo_root_validation_rejects_home_credential_dirs(self) -> None:
        with self.assertRaisesRegex(adapter_deploy.DeployError, "protected"):
            adapter_deploy.validate_target_repo_root(
                Path.home() / ".ssh" / "repo",
                self.fake_repo_root,
            )

    def test_source_repo_root_validation_rejects_sensitive_paths(self) -> None:
        with self.assertRaisesRegex(adapter_deploy.DeployError, "Source repo root is protected"):
            adapter_deploy.validate_source_repo_root(Path("/etc"))

    def test_normalize_relative_wrappers_use_explicit_context(self) -> None:
        with self.assertRaisesRegex(adapter_deploy.DeployError, "canonical skill directory"):
            adapter_deploy.normalize_relative_canonical_path(
                "/tmp/payload",
                field_name="canonical_path",
                skill_id="demo-skill",
            )
        with self.assertRaisesRegex(adapter_deploy.DeployError, "repository root"):
            adapter_deploy.normalize_relative_repo_path(
                "C:/payload",
                field_name="repo_path",
                skill_id="demo-skill",
            )

    def test_target_repo_root_validation_allows_container_cwd_under_usr(self) -> None:
        container_root = Path("/usr/src/app")

        with mock.patch.object(Path, "cwd", return_value=container_root):
            self.assertEqual(
                adapter_deploy.validate_target_repo_root(container_root, self.fake_repo_root),
                container_root,
            )

    def test_target_repo_root_validation_rejects_exact_system_roots(self) -> None:
        for target_root in (Path("/usr"), Path("/etc")):
            with self.subTest(target_root=target_root):
                with self.assertRaisesRegex(adapter_deploy.DeployError, "protected"):
                    adapter_deploy.validate_target_repo_root(target_root, self.fake_repo_root)

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
        self.assertIn("product/harness/adapters/claude/skills", package["files"])
        self.assertIn("toolchain/scripts/deploy/harness_deploy.py", package["files"])
        self.assertIn("toolchain/scripts/deploy/adapter_deploy.py", package["files"])
        self.assertEqual(
            package["publishConfig"],
            {
                "registry": "https://registry.npmjs.org/",
                "access": "public",
            },
        )
        self.assertEqual(
            package["repository"],
            {
                "type": "git",
                "url": "https://github.com/OceanEyeFF/vibecoding_autoworkflow",
            },
        )
        self.assertIn("toolchain/scripts/deploy/bin/check-root-publish.js", package["files"])
        self.assertIn("toolchain/scripts/deploy/bin/publish-dry-run.js", package["files"])
        self.assertEqual(
            package["scripts"]["prepublishOnly"],
            "node toolchain/scripts/deploy/bin/check-root-publish.js",
        )
        self.assertEqual(
            package["scripts"]["publish:dry-run"],
            "node toolchain/scripts/deploy/bin/publish-dry-run.js",
        )
        self.assertEqual(
            package["awInstallerRelease"],
            {
                "realPublishApproval": "approved",
                "approvedVersion": "0.4.1-rc.1",
                "approvedGitTag": "v0.4.1-rc.1",
                "approvedChannel": "next",
            },
        )
        scaffold_package = json.loads(
            (self.source_repo_root / "toolchain" / "scripts" / "deploy" / "package.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(scaffold_package["version"], package["version"])

    def test_aw_installer_uses_async_spawn_wrapper(self) -> None:
        installer_path = (
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "aw-installer.js"
        )

        installer_source = installer_path.read_text(encoding="utf-8")

        self.assertIn('const { spawn } = require("node:child_process");', installer_source)
        self.assertNotIn("spawnSync", installer_source)
        self.assertIn("AbortController", installer_source)
        self.assertIn('await runWrapper(["update", "--backend", "agents", "--yes"])', installer_source)

    def test_root_npm_publish_guard_can_be_imported_without_running_checks(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        guard_path = (
            self.source_repo_root
            / "toolchain"
            / "scripts"
            / "deploy"
            / "bin"
            / "check-root-publish.js"
        )

        completed = subprocess.run(
            [
                "node",
                "-e",
                (
                    f"const guard = require({json.dumps(str(guard_path))}); "
                    "console.log(guard.deriveReleaseChannelFromTag('v1.2.3', '1.2.3', ''));"
                ),
            ],
            cwd=self.temp_root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, "latest\n")
        self.assertEqual(completed.stderr, "")

    def test_root_npm_publish_dry_run_resolves_allowed_release_channel(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        script_path = (
            self.source_repo_root
            / "toolchain"
            / "scripts"
            / "deploy"
            / "bin"
            / "publish-dry-run.js"
        )

        completed = subprocess.run(
            [
                "node",
                "-e",
                (
                    f"const dryRun = require({json.dumps(str(script_path))}); "
                    "console.log(dryRun.resolveReleaseChannel({npm_config_tag: 'canary'}));"
                ),
            ],
            cwd=self.temp_root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, "canary\n")
        self.assertEqual(completed.stderr, "")

    def test_root_npm_publish_dry_run_rejects_unsupported_release_channel(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        script_path = (
            self.source_repo_root
            / "toolchain"
            / "scripts"
            / "deploy"
            / "bin"
            / "publish-dry-run.js"
        )
        env = {
            **os.environ,
            "AW_INSTALLER_RELEASE_CHANNEL": "next;echo injected",
        }

        completed = subprocess.run(
            ["node", str(script_path)],
            cwd=self.source_repo_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout, "")
        self.assertIn("unsupported aw-installer release channel", completed.stderr)

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

    def test_root_npm_publish_guard_rejects_scaffold_version_drift(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.temp_root / "release-package-root"
        guard_dir = package_root / "toolchain" / "scripts" / "deploy" / "bin"
        guard_dir.mkdir(parents=True)
        guard_path = guard_dir / "check-root-publish.js"
        shutil.copy2(
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js",
            guard_path,
        )
        (package_root / "package.json").write_text(
            json.dumps({"name": "aw-installer", "version": "1.2.3"}),
            encoding="utf-8",
        )
        (guard_dir.parent / "package.json").write_text(
            json.dumps({"name": "aw-installer", "version": "1.2.4"}),
            encoding="utf-8",
        )
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

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout, "")
        self.assertIn("does not match local scaffold package version 1.2.4", completed.stderr)

    def test_root_npm_publish_guard_rejects_scaffold_packlist_drift(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.temp_root / "release-package-root"
        guard_dir = package_root / "toolchain" / "scripts" / "deploy" / "bin"
        guard_dir.mkdir(parents=True)
        guard_path = guard_dir / "check-root-publish.js"
        shutil.copy2(
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js",
            guard_path,
        )
        (package_root / "package.json").write_text(
            json.dumps(
                {
                    "name": "aw-installer",
                    "version": "1.2.3",
                    "files": ["toolchain/scripts/deploy/adapter_deploy.py"],
                }
            ),
            encoding="utf-8",
        )
        (guard_dir.parent / "package.json").write_text(
            json.dumps(
                {
                    "name": "aw-installer",
                    "version": "1.2.3",
                    "files": ["adapter_deploy.py", "harness_deploy.py"],
                }
            ),
            encoding="utf-8",
        )
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

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout, "")
        self.assertIn("root package files must cover every local scaffold package file", completed.stderr)

    def test_root_npm_publish_guard_rejects_local_version_for_real_publish(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.temp_root / "local-release-package-root"
        guard_dir = package_root / "toolchain" / "scripts" / "deploy" / "bin"
        guard_dir.mkdir(parents=True)
        guard_path = guard_dir / "check-root-publish.js"
        shutil.copy2(
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js",
            guard_path,
        )
        (package_root / "package.json").write_text(
            json.dumps({"name": "aw-installer", "version": "0.0.0-local", "files": []}),
            encoding="utf-8",
        )
        (guard_dir.parent / "package.json").write_text(
            json.dumps({"name": "aw-installer", "version": "0.0.0-local", "private": True}),
            encoding="utf-8",
        )
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

    def test_root_npm_publish_guard_rejects_package_json_override_for_real_publish(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.source_repo_root
        guard_path = package_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js"
        package_path = self.temp_root / "release-package.json"
        package_path.write_text(
            json.dumps({"name": "aw-installer", "version": "1.2.3"}),
            encoding="utf-8",
        )
        env = {
            **os.environ,
            "AW_INSTALLER_PACKAGE_JSON": str(package_path),
            "AW_INSTALLER_PUBLISH_APPROVED": "1",
            "AW_INSTALLER_RELEASE_CHANNEL": "latest",
            "AW_INSTALLER_RELEASE_GIT_TAG": "v1.2.3",
            "CI": "true",
            "npm_config_tag": "latest",
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
        self.assertIn("AW_INSTALLER_PACKAGE_JSON override is not supported", completed.stderr)

    def test_root_npm_publish_guard_rejects_nonlocal_without_approval(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.temp_root / "release-package-root"
        guard_dir = package_root / "toolchain" / "scripts" / "deploy" / "bin"
        guard_dir.mkdir(parents=True)
        guard_path = guard_dir / "check-root-publish.js"
        shutil.copy2(
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js",
            guard_path,
        )
        package_path = package_root / "package.json"
        package_path.write_text(
            json.dumps({"name": "aw-installer", "version": "1.2.3"}),
            encoding="utf-8",
        )
        env = {
            **os.environ,
            "CI": "true",
            "AW_INSTALLER_RELEASE_CHANNEL": "latest",
            "npm_config_tag": "latest",
            "AW_INSTALLER_RELEASE_GIT_TAG": "v1.2.3",
        }
        env.pop("npm_config_dry_run", None)
        env.pop("AW_INSTALLER_PUBLISH_APPROVED", None)

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
        self.assertIn("AW_INSTALLER_PUBLISH_APPROVED=1", completed.stderr)

    def test_root_npm_publish_guard_rejects_blocked_preflight_metadata_for_real_publish(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.temp_root / "release-package-root"
        guard_dir = package_root / "toolchain" / "scripts" / "deploy" / "bin"
        guard_dir.mkdir(parents=True)
        guard_path = guard_dir / "check-root-publish.js"
        shutil.copy2(
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js",
            guard_path,
        )
        package_path = package_root / "package.json"
        package_path.write_text(
            json.dumps(
                {
                    "name": "aw-installer",
                    "version": "0.4.0-rc.1",
                    "awInstallerRelease": {"realPublishApproval": "blocked-until-P0-019"},
                }
            ),
            encoding="utf-8",
        )
        env = {
            **os.environ,
            "AW_INSTALLER_PUBLISH_APPROVED": "1",
            "AW_INSTALLER_RELEASE_GIT_TAG": "v0.4.0-rc.1",
            "CI": "true",
            "npm_config_tag": "next",
        }
        env.pop("npm_config_dry_run", None)
        env.pop("AW_INSTALLER_RELEASE_CHANNEL", None)

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
        self.assertIn("realPublishApproval must be approved", completed.stderr)

    def test_root_npm_publish_guard_accepts_current_approved_rc_metadata(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.source_repo_root
        guard_path = package_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js"
        env = {
            **os.environ,
            "AW_INSTALLER_PUBLISH_APPROVED": "1",
            "AW_INSTALLER_RELEASE_GIT_TAG": "v0.4.1-rc.1",
            "CI": "true",
            "npm_config_tag": "next",
        }
        env.pop("npm_config_dry_run", None)
        env.pop("AW_INSTALLER_RELEASE_CHANNEL", None)

        completed = subprocess.run(
            ["node", str(guard_path)],
            cwd=package_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(completed.stderr, "")

    def test_root_npm_publish_guard_rejects_stale_approved_version_metadata(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.temp_root / "release-package-root"
        guard_dir = package_root / "toolchain" / "scripts" / "deploy" / "bin"
        guard_dir.mkdir(parents=True)
        guard_path = guard_dir / "check-root-publish.js"
        shutil.copy2(
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js",
            guard_path,
        )
        package_path = package_root / "package.json"
        metadata = self._release_package_metadata("1.2.4")
        metadata["awInstallerRelease"]["approvedVersion"] = "1.2.3"
        package_path.write_text(json.dumps(metadata), encoding="utf-8")
        env = {
            **os.environ,
            "AW_INSTALLER_PUBLISH_APPROVED": "1",
            "AW_INSTALLER_RELEASE_CHANNEL": "latest",
            "AW_INSTALLER_RELEASE_GIT_TAG": "v1.2.4",
            "CI": "true",
            "npm_config_tag": "latest",
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
        self.assertIn("approvedVersion 1.2.3 must match 1.2.4", completed.stderr)

    def test_root_npm_publish_guard_rejects_missing_version_bound_metadata(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.temp_root / "release-package-root"
        guard_dir = package_root / "toolchain" / "scripts" / "deploy" / "bin"
        guard_dir.mkdir(parents=True)
        guard_path = guard_dir / "check-root-publish.js"
        shutil.copy2(
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js",
            guard_path,
        )
        package_path = package_root / "package.json"
        package_path.write_text(
            json.dumps(
                {
                    "name": "aw-installer",
                    "version": "1.2.4",
                    "awInstallerRelease": {"realPublishApproval": "approved"},
                }
            ),
            encoding="utf-8",
        )
        env = {
            **os.environ,
            "AW_INSTALLER_PUBLISH_APPROVED": "1",
            "AW_INSTALLER_RELEASE_CHANNEL": "latest",
            "AW_INSTALLER_RELEASE_GIT_TAG": "v1.2.4",
            "CI": "true",
            "npm_config_tag": "latest",
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
        self.assertIn("approvedVersion <missing-version> must match 1.2.4", completed.stderr)

    def test_root_npm_publish_guard_rejects_stale_approved_tag_metadata(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.temp_root / "release-package-root"
        guard_dir = package_root / "toolchain" / "scripts" / "deploy" / "bin"
        guard_dir.mkdir(parents=True)
        guard_path = guard_dir / "check-root-publish.js"
        shutil.copy2(
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js",
            guard_path,
        )
        package_path = package_root / "package.json"
        metadata = self._release_package_metadata("1.2.4")
        metadata["awInstallerRelease"]["approvedGitTag"] = "v1.2.3"
        package_path.write_text(json.dumps(metadata), encoding="utf-8")
        env = {
            **os.environ,
            "AW_INSTALLER_PUBLISH_APPROVED": "1",
            "AW_INSTALLER_RELEASE_CHANNEL": "latest",
            "AW_INSTALLER_RELEASE_GIT_TAG": "v1.2.4",
            "CI": "true",
            "npm_config_tag": "latest",
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
        self.assertIn("approvedGitTag v1.2.3 must match v1.2.4", completed.stderr)

    def test_root_npm_publish_guard_rejects_stale_approved_channel_metadata(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.temp_root / "release-package-root"
        guard_dir = package_root / "toolchain" / "scripts" / "deploy" / "bin"
        guard_dir.mkdir(parents=True)
        guard_path = guard_dir / "check-root-publish.js"
        shutil.copy2(
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js",
            guard_path,
        )
        package_path = package_root / "package.json"
        metadata = self._release_package_metadata("1.2.4")
        metadata["awInstallerRelease"]["approvedChannel"] = "next"
        package_path.write_text(json.dumps(metadata), encoding="utf-8")
        env = {
            **os.environ,
            "AW_INSTALLER_PUBLISH_APPROVED": "1",
            "AW_INSTALLER_RELEASE_CHANNEL": "latest",
            "AW_INSTALLER_RELEASE_GIT_TAG": "v1.2.4",
            "CI": "true",
            "npm_config_tag": "latest",
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
        self.assertIn("approvedChannel next must match latest", completed.stderr)

    def test_root_npm_publish_guard_allows_approved_latest_release_metadata(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.temp_root / "release-package-root"
        guard_dir = package_root / "toolchain" / "scripts" / "deploy" / "bin"
        guard_dir.mkdir(parents=True)
        guard_path = guard_dir / "check-root-publish.js"
        shutil.copy2(
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js",
            guard_path,
        )
        package_path = package_root / "package.json"
        package_path.write_text(
            json.dumps(self._release_package_metadata("1.2.3")),
            encoding="utf-8",
        )
        env = {
            **os.environ,
            "AW_INSTALLER_PUBLISH_APPROVED": "1",
            "AW_INSTALLER_RELEASE_CHANNEL": "latest",
            "AW_INSTALLER_RELEASE_GIT_TAG": "v1.2.3",
            "CI": "true",
            "npm_config_tag": "latest",
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

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(completed.stderr, "")

    def test_root_npm_publish_guard_derives_next_channel_from_release_tag(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.temp_root / "release-package-root"
        guard_dir = package_root / "toolchain" / "scripts" / "deploy" / "bin"
        guard_dir.mkdir(parents=True)
        guard_path = guard_dir / "check-root-publish.js"
        shutil.copy2(
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js",
            guard_path,
        )
        package_path = package_root / "package.json"
        package_path.write_text(
            json.dumps(self._release_package_metadata("1.3.0-rc.1")),
            encoding="utf-8",
        )
        env = {
            **os.environ,
            "AW_INSTALLER_PUBLISH_APPROVED": "1",
            "AW_INSTALLER_RELEASE_GIT_TAG": "v1.3.0-rc.1",
            "CI": "true",
            "npm_config_tag": "next",
        }
        env.pop("npm_config_dry_run", None)
        env.pop("AW_INSTALLER_RELEASE_CHANNEL", None)

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

    def test_root_npm_publish_guard_rejects_channel_dist_tag_mismatch(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.temp_root / "release-package-root"
        guard_dir = package_root / "toolchain" / "scripts" / "deploy" / "bin"
        guard_dir.mkdir(parents=True)
        guard_path = guard_dir / "check-root-publish.js"
        shutil.copy2(
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "check-root-publish.js",
            guard_path,
        )
        package_path = package_root / "package.json"
        package_path.write_text(
            json.dumps(self._release_package_metadata("1.3.0-beta.1")),
            encoding="utf-8",
        )
        env = {
            **os.environ,
            "AW_INSTALLER_PUBLISH_APPROVED": "1",
            "AW_INSTALLER_RELEASE_CHANNEL": "next",
            "AW_INSTALLER_RELEASE_GIT_TAG": "v1.3.0-beta.1",
            "CI": "true",
            "npm_config_tag": "latest",
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
        self.assertIn("npm dist-tag latest does not match release channel next", completed.stderr)

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
        self.assertEqual(completed.stdout, "aw-installer 0.4.1-rc.1\n")
        self.assertEqual(completed.stderr, "")

    def test_local_npm_installer_bin_version_prefers_root_package_metadata(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.temp_root / "version-root"
        bin_dir = package_root / "toolchain" / "scripts" / "deploy" / "bin"
        bin_dir.mkdir(parents=True)
        shutil.copy2(
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "aw-installer.js",
            bin_dir / "aw-installer.js",
        )
        (package_root / "package.json").write_text(
            json.dumps({"name": "aw-installer", "version": "9.8.7"}),
            encoding="utf-8",
        )
        deploy_package_path = package_root / "toolchain" / "scripts" / "deploy" / "package.json"
        deploy_package_path.write_text(
            json.dumps({"name": "aw-installer", "version": "0.0.0-local", "private": True}),
            encoding="utf-8",
        )

        completed = subprocess.run(
            ["node", str(bin_dir / "aw-installer.js"), "--version"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, "aw-installer 9.8.7\n")
        self.assertEqual(completed.stderr, "")

    def test_local_npm_installer_bin_version_fallback_has_depth_limit(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        package_root = self.temp_root / "version-depth-root"
        bin_dir = package_root.joinpath(*(["nested"] * 24), "bin")
        bin_dir.mkdir(parents=True)
        shutil.copy2(
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "aw-installer.js",
            bin_dir / "aw-installer.js",
        )

        completed = subprocess.run(
            ["node", str(bin_dir / "aw-installer.js"), "--version"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout, "")
        self.assertIn("within 20 parent directories", completed.stderr)

    def test_local_npm_installer_try_read_version_failures_return_empty_result(self) -> None:
        installer_path = (
            self.source_repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "aw-installer.js"
        )

        installer_source = installer_path.read_text(encoding="utf-8")

        self.assertIn("function tryReadPackageVersionAt(candidate)", installer_source)
        self.assertIn("} catch (error) {\n    return \"\";\n  }", installer_source)

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

    def test_node_deploy_wrappers_ignore_python_env_overrides(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        target_repo = self.temp_root / "python-env-target"
        env = {
            **os.environ,
            "AW_HARNESS_REPO_ROOT": str(self.fake_repo_root),
            "AW_HARNESS_TARGET_REPO_ROOT": str(target_repo),
            "PYTHON": str(self.temp_root / "missing-python"),
            "PYTHON3": str(self.temp_root / "missing-python3"),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        wrappers = [
            self.source_repo_root
            / "toolchain"
            / "scripts"
            / "deploy"
            / "bin"
            / "aw-installer.js",
            self.source_repo_root
            / "toolchain"
            / "scripts"
            / "deploy"
            / "bin"
            / "aw-harness-deploy.js",
        ]

        for wrapper in wrappers:
            completed = subprocess.run(
                ["node", str(wrapper), "diagnose", "--backend", "agents", "--json"],
                cwd=self.source_repo_root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["target_root"], str(target_repo / ".agents" / "skills"))

    def test_node_deploy_wrappers_fall_back_to_python_when_python3_is_missing(self) -> None:
        node_path = shutil.which("node")
        if node_path is None:
            self.skipTest("node is not available")
        fake_bin = self._fake_python_fallback_bin()
        env = {
            **os.environ,
            "PATH": str(fake_bin),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        wrappers = [
            self.source_repo_root
            / "toolchain"
            / "scripts"
            / "deploy"
            / "bin"
            / "aw-installer.js",
            self.source_repo_root
            / "toolchain"
            / "scripts"
            / "deploy"
            / "bin"
            / "aw-harness-deploy.js",
        ]

        for wrapper in wrappers:
            with self.subTest(wrapper=wrapper.name):
                completed = subprocess.run(
                    [node_path, str(wrapper), "diagnose", "--backend", "agents", "--json"],
                    cwd=self.source_repo_root,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("fake-python", completed.stdout)
                self.assertIn("harness_deploy.py diagnose --backend agents --json", completed.stdout)

    def test_node_deploy_wrappers_time_out_stalled_python_processes(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("node is not available")
        fake_bin = self._fake_sleeping_python_bin()
        wrappers = [
            self.source_repo_root
            / "toolchain"
            / "scripts"
            / "deploy"
            / "bin"
            / "aw-installer.js",
            self.source_repo_root
            / "toolchain"
            / "scripts"
            / "deploy"
            / "bin"
            / "aw-harness-deploy.js",
        ]
        env = {
            **os.environ,
            "AW_INSTALLER_WRAPPER_TIMEOUT_MS": "10",
            "PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
            "PYTHONDONTWRITEBYTECODE": "1",
        }

        for wrapper in wrappers:
            with self.subTest(wrapper=wrapper.name):
                completed = subprocess.run(
                    ["node", str(wrapper), "diagnose", "--backend", "agents", "--json"],
                    cwd=self.source_repo_root,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )

                self.assertEqual(completed.returncode, 1)
                self.assertEqual(completed.stdout, "")
                self.assertIn("timed out after 1s", completed.stderr)

    def test_local_npm_installer_tui_shows_update_plan_before_apply_confirmation(self) -> None:
        target_repo = self.temp_root / "tui-plan-target"

        code, output = self._run_installer_tui_script(
            [
                ("Select an action:", "1\n"),
                ("Step 3: Type yes", "no\n"),
                ("Update cancelled.", "\n"),
                ("Select an action:", "6\n"),
            ],
            target_repo=target_repo,
        )

        self.assertEqual(code, 0, output)
        diagnose_index = output.find("Step 1: Diagnose current agents install.")
        plan_index = output.find("[agents] update plan")
        confirmation_index = output.find("Step 3: Type yes")
        self.assertNotEqual(diagnose_index, -1, output)
        self.assertNotEqual(plan_index, -1, output)
        self.assertNotEqual(confirmation_index, -1, output)
        self.assertLess(diagnose_index, plan_index)
        self.assertLess(plan_index, confirmation_index)
        self.assertIn("dry-run only; pass --yes to apply update", output)
        self.assertIn("Update cancelled.", output)
        self.assertNotIn("[agents] applying update", output)
        self.assertFalse((target_repo / ".agents" / "skills").exists())

    def test_local_npm_installer_tui_guided_flow_is_primary_menu_action(self) -> None:
        target_repo = self.temp_root / "tui-guided-target"

        code, output = self._run_installer_tui_script(
            [
                ("Select an action:", "1\n"),
                ("Step 3: Type yes", "no\n"),
                ("Update cancelled.", "\n"),
                ("Select an action:", "6\n"),
            ],
            target_repo=target_repo,
        )

        self.assertEqual(code, 0, output)
        self.assertIn("1. Guided update flow", output)
        self.assertIn("5. Show CLI help", output)
        self.assertNotIn("Re-run guided update flow", output)
        self.assertIn("Guided update flow", output)
        self.assertIn("Step 1: Diagnose current agents install.", output)
        self.assertIn("Step 2: Review update dry-run plan.", output)
        self.assertIn("Step 3: Type yes to apply update via prune --all -> check_paths_exist -> install -> verify", output)
        self.assertIn("Update cancelled.", output)
        self.assertNotIn("[agents] applying update", output)
        self.assertFalse((target_repo / ".agents" / "skills").exists())

    def test_local_npm_installer_tui_guided_flow_apply_runs_update_and_verify(self) -> None:
        target_repo = self.temp_root / "tui-guided-apply-target"

        code, output = self._run_installer_tui_script(
            [
                ("Select an action:", "1\n"),
                ("Step 3: Type yes", "yes\n"),
                ("Press Enter to return to the installer menu", "\n"),
                ("Select an action:", "6\n"),
            ],
            target_repo=target_repo,
        )

        self.assertEqual(code, 0, output)
        self.assertIn("Step 4: Applying update and running strict verify.", output)
        self.assertIn("[agents] applying update", output)
        self.assertIn("[agents] update complete", output)
        self.assertTrue((target_repo / ".agents" / "skills").is_dir())

    def test_local_npm_installer_tui_guided_flow_stops_after_failed_diagnose(self) -> None:
        target_repo = self.temp_root / "tui-diagnose-failure-target"

        code, output = self._run_installer_tui_script(
            [
                ("Select an action:", "1\n"),
                ("Continue with update dry-run anyway?", "no\n"),
                ("Update cancelled.", "\n"),
                ("Select an action:", "6\n"),
            ],
            target_repo=target_repo,
            env_overrides={"AW_HARNESS_TARGET_REPO_ROOT": "/etc"},
        )

        self.assertEqual(code, 0, output)
        self.assertIn("Diagnose failed; update may not succeed as expected.", output)
        self.assertIn("Update cancelled.", output)
        self.assertNotIn("[agents] update plan", output)
        self.assertFalse((target_repo / ".agents" / "skills").exists())

    def test_target_root_scans_raise_deploy_error_for_iterdir_failures(self) -> None:
        target_root = self.temp_root / "scan-failure-target"
        target_root.mkdir()
        prune_args = adapter_deploy.parse_args(
            ["prune", "--backend", "agents", "--agents-root", str(target_root)]
        )

        with mock.patch.object(Path, "iterdir", side_effect=PermissionError("denied")):
            with self.assertRaisesRegex(adapter_deploy.DeployError, "unexpected managed target dirs"):
                adapter_deploy.unexpected_managed_target_dirs("agents", target_root, set())
            with self.assertRaisesRegex(adapter_deploy.DeployError, "managed install dirs"):
                adapter_deploy.managed_install_dirs("agents", target_root)
            with self.assertRaisesRegex(adapter_deploy.DeployError, "update target entry issues"):
                adapter_deploy.collect_update_target_entry_issues("agents", target_root, set())
            with self.assertRaisesRegex(adapter_deploy.DeployError, "managed install pruning"):
                adapter_deploy.prune_all_managed_target_dirs("agents", prune_args, self.context)

    def test_agents_root_override_is_validated_with_protected_root_guardrails(self) -> None:
        code, _, stderr = self._run_cli(
            "diagnose",
            "--backend",
            "agents",
            "--agents-root",
            "/etc",
            "--json",
        )

        self.assertEqual(code, 1)
        self.assertIn("Target repo root is protected", stderr)
        self.assertIn("/etc", stderr)

    def test_update_plan_summary_reuses_bindings_and_target_root_scan(self) -> None:
        code, _, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        args = adapter_deploy.parse_args(["update", "--backend", "agents"])

        with (
            mock.patch.object(
                adapter_deploy,
                "collect_skill_bindings",
                wraps=adapter_deploy.collect_skill_bindings,
            ) as collect_bindings,
            mock.patch.object(
                adapter_deploy,
                "iter_target_root_children",
                wraps=adapter_deploy.iter_target_root_children,
            ) as iter_children,
        ):
            summary = adapter_deploy.update_plan_summary("agents", args, self.context)

        self.assertEqual(summary["blocking_issue_count"], 0)
        self.assertEqual(collect_bindings.call_count, 1)
        self.assertEqual(iter_children.call_count, 1)

    def test_update_apply_failure_prints_recovery_hint(self) -> None:
        code, _, stderr = self._install()
        self.assertEqual(code, 0, stderr)

        with mock.patch.object(
            adapter_deploy,
            "install_backend_payloads",
            side_effect=adapter_deploy.DeployError("install exploded"),
        ):
            code, stdout, stderr = self._update("--yes")

        self.assertEqual(code, 1)
        self.assertIn("[agents] applying update", stdout)
        self.assertIn("install exploded", stderr)
        self.assertIn("recovery: the update may be partially applied", stderr)
        self.assertIn("aw-installer update --backend agents --yes", stderr)

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
            "product/harness/adapters/claude/skills/set-harness-goal-skill/payload.json",
        }:
            self.assertIn(required_path, packed_files)
        self.assertFalse(any(path.startswith(".aw/") for path in packed_files))
        self.assertFalse(any(path.startswith(".agents/") for path in packed_files))
        self.assertFalse(any(path.startswith(".claude/") for path in packed_files))
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
        self.assertEqual(payload["version"], "0.4.1-rc.1")
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

    def test_adapter_cli_rejects_source_root_override_without_payload_source(self) -> None:
        source_root = self.temp_root / "not-a-harness-checkout"
        target_repo = self.temp_root / "target-repo"
        source_root.mkdir()
        (target_repo / ".agents" / "skills").mkdir(parents=True)
        script_path = self.source_repo_root / "toolchain" / "scripts" / "deploy" / "adapter_deploy.py"
        env = {
            **os.environ,
            "AW_HARNESS_REPO_ROOT": str(source_root),
            "AW_HARNESS_TARGET_REPO_ROOT": str(target_repo),
            "PYTHONDONTWRITEBYTECODE": "1",
        }

        verify_completed = subprocess.run(
            [sys.executable, str(script_path), "verify", "--backend", "agents"],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        diagnose_completed = subprocess.run(
            [sys.executable, str(script_path), "diagnose", "--backend", "agents", "--json"],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(verify_completed.returncode, 1)
        self.assertEqual(verify_completed.stdout, "")
        self.assertIn("is not a Harness payload source", verify_completed.stderr)
        self.assertNotIn("[agents] ok", verify_completed.stdout)

        self.assertEqual(diagnose_completed.returncode, 1)
        self.assertEqual(diagnose_completed.stdout, "")
        self.assertIn("is not a Harness payload source", diagnose_completed.stderr)

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
            with tarfile.open(package_file, "r:gz") as package_tar:
                installer_member = package_tar.extractfile(
                    "package/toolchain/scripts/deploy/bin/aw-installer.js"
                )
                self.assertIsNotNone(installer_member)
                installer_source = installer_member.read().decode("utf-8")
                self.assertIn("1. Guided update flow", installer_source)
                self.assertIn("5. Show CLI help", installer_source)
                self.assertNotIn("Re-run guided update flow", installer_source)
                self.assertIn("Step 1: Diagnose current agents install.", installer_source)
                self.assertIn("Step 2: Review update dry-run plan.", installer_source)
                self.assertIn("Step 3: Type yes to apply update via prune --all -> check_paths_exist -> install -> verify", installer_source)
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
            tui_completed = subprocess.run(
                [
                    "npm",
                    "exec",
                    "--yes",
                    "--package",
                    str(package_file),
                    "--",
                    "aw-installer",
                    "tui",
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
        self.assertEqual(version_completed.stdout, "aw-installer 0.4.1-rc.1\n")
        self.assertEqual(version_completed.stderr, "")
        self.assertEqual(tui_completed.returncode, 1)
        self.assertEqual(tui_completed.stdout, "")
        self.assertIn("aw-installer tui requires an interactive terminal", tui_completed.stderr)

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
        self.assertEqual(payload["source_kind"], "package")
        self.assertEqual(payload["source_ref"], "package-local")
        self.assertEqual(payload["blocking_issue_count"], 0)
        self.assertEqual(
            payload["operation_sequence"],
            ["prune --all", "check_paths_exist", "install", "verify"],
        )
        self.assertGreater(len(payload["planned_target_paths"]), 0)
        self.assertEqual(stderr, "")
        self.assertFalse(self.local_root.exists())

    def test_update_json_can_use_github_source_archive(self) -> None:
        archive_bytes = self._fake_github_archive_bytes()
        with mock.patch.object(
            adapter_deploy.urllib.request,
            "urlopen",
            return_value=self._fake_urlopen_response(archive_bytes),
        ) as urlopen:
            code, stdout, stderr = self._update(
                "--json",
                "--source",
                "github",
                "--github-repo",
                "OceanEyeFF/vibecoding_autoworkflow",
                "--github-ref",
                "master",
            )

        self.assertEqual(code, 0, stderr)
        urlopen.assert_called_once()
        self.assertEqual(
            urlopen.call_args.args[0],
            "https://codeload.github.com/OceanEyeFF/vibecoding_autoworkflow/zip/refs/heads/master",
        )
        payload = json.loads(stdout)
        self.assertEqual(payload["source_kind"], "github")
        self.assertEqual(payload["source_ref"], "OceanEyeFF/vibecoding_autoworkflow@master")
        self.assertTrue(payload["source_root"].endswith("repo-master"))
        self.assertEqual(payload["target_root"], str(self.local_root))
        self.assertEqual(payload["blocking_issue_count"], 0)
        self.assertGreater(len(payload["planned_target_paths"]), 0)
        self.assertEqual(stderr, "")
        self.assertFalse(self.local_root.exists())

    def test_update_json_github_source_default_repo_can_use_environment(self) -> None:
        archive_bytes = self._fake_github_archive_bytes()
        with mock.patch.object(
            adapter_deploy.urllib.request,
            "urlopen",
            return_value=self._fake_urlopen_response(archive_bytes),
        ) as urlopen:
            code, stdout, stderr = self._run_cli(
                "update",
                "--backend",
                "agents",
                "--json",
                "--source",
                "github",
                env={
                    "GITHUB_REPOSITORY": "ForkOwner/forked_repo",
                },
            )

        self.assertEqual(code, 0, stderr)
        urlopen.assert_called_once()
        self.assertEqual(
            urlopen.call_args.args[0],
            "https://codeload.github.com/ForkOwner/forked_repo/zip/refs/heads/master",
        )
        payload = json.loads(stdout)
        self.assertEqual(payload["source_kind"], "github")
        self.assertEqual(payload["source_ref"], "ForkOwner/forked_repo@master")
        self.assertEqual(stderr, "")
        self.assertFalse(self.local_root.exists())

    def test_github_archive_ref_path_preserves_sha_ref(self) -> None:
        self.assertEqual(
            adapter_deploy.github_archive_ref_path("0123456789abcdef0123456789abcdef01234567"),
            "0123456789abcdef0123456789abcdef01234567",
        )
        self.assertEqual(
            adapter_deploy.github_archive_ref_path("master"),
            "refs/heads/master",
        )

    def test_safe_extract_zip_rejects_parent_traversal(self) -> None:
        zip_path = self.temp_root / "unsafe.zip"
        destination = self.temp_root / "extract-unsafe"
        destination.mkdir()
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("repo-master/../evil.txt", "bad")

        with self.assertRaises(adapter_deploy.DeployError) as ctx:
            adapter_deploy.safe_extract_zip(zip_path, destination)

        self.assertIn("GitHub archive contains unsafe path", str(ctx.exception))
        self.assertEqual(list(destination.iterdir()), [])
        self.assertFalse((self.temp_root / "evil.txt").exists())

    def test_safe_extract_zip_rejects_windows_absolute_path(self) -> None:
        zip_path = self.temp_root / "unsafe-windows.zip"
        destination = self.temp_root / "extract-unsafe-windows"
        destination.mkdir()
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("C:\\temp\\evil.txt", "bad")

        with self.assertRaises(adapter_deploy.DeployError) as ctx:
            adapter_deploy.safe_extract_zip(zip_path, destination)

        self.assertIn("GitHub archive contains unsafe path", str(ctx.exception))
        self.assertEqual(list(destination.iterdir()), [])

    def test_extracted_archive_root_error_includes_recovery_context(self) -> None:
        extract_root = self.temp_root / "empty-archive"
        extract_root.mkdir()

        with self.assertRaises(adapter_deploy.DeployError) as ctx:
            adapter_deploy.extracted_archive_root(extract_root)

        self.assertIn("Check --github-repo/--github-ref", str(ctx.exception))

    def test_update_json_blocks_duplicate_target_dirs_when_target_root_is_missing(self) -> None:
        self._mutate_target_dir("dispatch-skills", "aw-harness-skill")

        code, stdout, stderr = self._update("--json")

        self.assertEqual(code, 1)
        payload = json.loads(stdout)
        self.assertEqual(payload["blocking_issue_count"], 1)
        self.assertEqual(payload["planned_target_paths"], [])
        self.assertEqual(
            payload["blocking_issues"][0]["code"],
            "payload-contract-invalid",
        )
        self.assertIn(
            "Multiple skills map to the same target_dir for backend agents: aw-harness-skill",
            payload["blocking_issues"][0]["detail"],
        )
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

    def test_update_yes_prunes_same_backend_managed_install_with_stale_marker(self) -> None:
        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        target_dir = self.local_root / "aw-harness-skill"
        stale_marker = adapter_deploy.build_runtime_marker(
            "agents",
            "legacy-harness-skill",
            "agents-skill-payload.v0",
            "old-managed-fingerprint",
        )
        (target_dir / "aw.marker").write_text(
            adapter_deploy.runtime_marker_text(stale_marker),
            encoding="utf-8",
        )

        code, stdout, stderr = self._update("--json")

        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(payload["blocking_issue_count"], 0)
        self.assertIn(str(target_dir), payload["managed_installs_to_delete"])
        self.assertTrue(
            any(
                issue["code"] == "unrecognized-target-directory"
                and issue["path"] == str(target_dir)
                for issue in payload["issues"]
            )
        )

        code, stdout, stderr = self._update("--yes")

        self.assertEqual(code, 0, stderr)
        self.assertIn("blocking preflight issues: 0", stdout)
        self.assertIn(f"removed managed skill dir {target_dir}", stdout)
        self.assertEqual(
            (target_dir / "aw.marker").read_text(encoding="utf-8"),
            self._runtime_marker_text("harness-skill"),
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

    def test_update_ignores_unrelated_user_skill_dir(self) -> None:
        user_skill_dir = self.local_root / "my-custom-skill"
        user_skill_dir.mkdir(parents=True)
        (user_skill_dir / "SKILL.md").write_text("# user maintained skill\n", encoding="utf-8")

        code, stdout, stderr = self._update("--json")

        self.assertEqual(code, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(payload["blocking_issue_count"], 0)
        self.assertFalse(
            any(
                issue["code"] == "unrecognized-target-directory"
                and issue["path"] == str(user_skill_dir)
                for issue in payload["issues"]
            )
        )
        self.assertTrue(user_skill_dir.is_dir())

    def test_update_blocks_foreign_managed_planned_directory_without_writing(self) -> None:
        self.local_root.mkdir(parents=True, exist_ok=True)
        foreign_dir = self._install_managed_directory(
            self._target_dir_for_skill("harness-skill"),
            backend="claude",
        )

        code, stdout, stderr = self._update("--yes")

        self.assertEqual(code, 1)
        self.assertIn("foreign-managed-directory", stdout)
        self.assertIn("update blocked", stderr)
        self.assertTrue(foreign_dir.is_dir())
        marker = adapter_deploy.load_runtime_marker(adapter_deploy.managed_skill_marker_path(foreign_dir))
        self.assertIsNotNone(marker)
        assert marker is not None
        self.assertEqual(marker.backend, "claude")
        self.assertFalse((self.local_root / "aw-dispatch-skills").exists())

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

    def test_payload_fingerprint_cache_invalidates_when_source_file_changes(self) -> None:
        plan_before = self._install_plan("harness-skill")
        self._mutate_canonical_skill("harness-skill", "\n# cache invalidation\n")

        plan_after = self._install_plan("harness-skill")

        self.assertNotEqual(plan_before.payload_fingerprint, plan_after.payload_fingerprint)

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

    def test_all_known_target_dirs_reads_each_binding_metadata_once(self) -> None:
        bindings = adapter_deploy.collect_skill_bindings("agents", self.context)
        real_loader = adapter_deploy.load_binding_target_metadata

        with mock.patch.object(
            adapter_deploy,
            "load_binding_target_metadata",
            side_effect=real_loader,
        ) as load_binding_target_metadata:
            known = adapter_deploy.all_known_target_dirs(bindings)

        self.assertIn("aw-harness-skill", known)
        self.assertEqual(load_binding_target_metadata.call_count, len(bindings))

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
