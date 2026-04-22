from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import adapter_deploy


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

    def _install(self, *extra_args: object) -> tuple[int, str, str]:
        return self._run_cli("install", "--backend", "agents", *extra_args)

    def _check_paths_exist(self, *extra_args: object) -> tuple[int, str, str]:
        return self._run_cli("check_paths_exist", "--backend", "agents", *extra_args)

    def _verify(self, *extra_args: object) -> tuple[int, str, str]:
        return self._run_cli("verify", "--backend", "agents", *extra_args)

    def _prune_all(self, *extra_args: object) -> tuple[int, str, str]:
        return self._run_cli("prune", "--backend", "agents", "--all", *extra_args)

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

    def _install_foreign_conflict(self, skill_dir_name: str = "harness-skill") -> Path:
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

    def test_install_creates_target_root_and_installs_first_wave_payloads(self) -> None:
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

    def test_install_uses_override_root(self) -> None:
        code, stdout, stderr = self._install("--agents-root", self.override_root)

        self.assertEqual(code, 0, stderr)
        self.assertTrue(self.override_root.is_dir())
        self.assertTrue((self.override_root / "harness-skill").is_dir())
        self.assertIn(str(self.override_root), stdout)
        self.assertFalse(self.local_root.exists())

    def test_check_paths_exist_reports_ok_when_paths_are_free(self) -> None:
        code, stdout, stderr = self._check_paths_exist()

        self.assertEqual(code, 0, stderr)
        self.assertIn("[agents] ok: no conflicting target paths", stdout)

    def test_check_paths_exist_lists_all_conflicts(self) -> None:
        self.local_root.mkdir(parents=True, exist_ok=True)
        (self.local_root / "harness-skill").mkdir()
        (self.local_root / "dispatch-skills").mkdir()

        code, stdout, stderr = self._check_paths_exist()

        self.assertEqual(code, 1)
        self.assertIn("target path conflicts:", stderr)
        self.assertIn("harness-skill", stderr)
        self.assertIn("dispatch-skills", stderr)

    def test_check_paths_exist_reports_file_and_broken_symlink_conflicts(self) -> None:
        self.local_root.mkdir(parents=True, exist_ok=True)
        (self.local_root / "harness-skill").write_text("occupied by file\n", encoding="utf-8")
        (self.local_root / "dispatch-skills").symlink_to(
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
        self.assertFalse((self.local_root / "dispatch-skills").exists())

    def test_install_does_not_incrementally_rewrite_existing_managed_directories(self) -> None:
        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        target_wrapper_path = self.local_root / "harness-skill" / "SKILL.md"
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
        self._mutate_target_dir("dispatch-skills", "harness-skill")

        code, stdout, stderr = self._install()

        self.assertEqual(code, 1)
        self.assertIn(
            "Multiple skills map to the same target_dir for backend agents: harness-skill",
            stderr,
        )
        self.assertFalse((self.local_root / "harness-skill").exists())
        self.assertFalse((self.local_root / "dispatch-skills").exists())

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
        self.assertFalse((self.local_root / "harness-skill").exists())
        self.assertFalse((self.local_root / "dispatch-skills").exists())

    def test_prune_all_keeps_foreign_and_invalid_marker_dirs(self) -> None:
        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        foreign_dir = self._install_managed_directory("foreign-managed", backend="claude")
        invalid_dir = self.local_root / "broken-managed"
        invalid_dir.mkdir(parents=True, exist_ok=True)
        (invalid_dir / "aw.marker").write_text("{invalid json\n", encoding="utf-8")

        code, stdout, stderr = self._prune_all()

        self.assertEqual(code, 0, stderr)
        self.assertFalse((self.local_root / "harness-skill").exists())
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
        self.assertFalse((self.local_root / "harness-skill").exists())

        code, stdout, stderr = self._check_paths_exist()
        self.assertEqual(code, 0, stderr)

        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        self.assertTrue((self.local_root / "harness-skill").is_dir())

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
        shutil.rmtree(self.local_root / "dispatch-skills")

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
        payload["legacy_target_dirs"] = ["harness-skill"]
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
        self.assertTrue((self.local_root / "harness-skill").is_dir())

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

    def test_install_skips_legacy_cleanup_when_marker_mismatched(self) -> None:
        self._install_managed_directory("old-harness-skill", marker_skill_id="other-skill")
        self.assertTrue((self.local_root / "old-harness-skill").is_dir())

        payload_path = self.adapter_dir / "harness-skill" / "payload.json"
        payload = self._load_json(payload_path)
        payload["legacy_target_dirs"] = ["old-harness-skill"]
        payload["legacy_skill_ids"] = ["old-harness-skill"]
        payload_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        code, stdout, stderr = self._install()
        self.assertEqual(code, 0, stderr)
        self.assertNotIn("removed legacy skill dir", stdout)
        self.assertTrue((self.local_root / "old-harness-skill").is_dir())

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
