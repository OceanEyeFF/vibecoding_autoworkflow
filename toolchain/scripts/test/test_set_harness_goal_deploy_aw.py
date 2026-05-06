from __future__ import annotations

import dataclasses
import contextlib
import importlib.util
import io
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DEPLOY_AW_PATH = (
    REPO_ROOT
    / "product"
    / "harness"
    / "skills"
    / "set-harness-goal-skill"
    / "scripts"
    / "deploy_aw.py"
)


def load_deploy_aw_module(
    path: Path = DEPLOY_AW_PATH,
    module_name: str = "set_harness_goal_deploy_aw",
):
    spec = importlib.util.spec_from_file_location(
        module_name, path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
    return module


deploy_aw = load_deploy_aw_module()


class SetHarnessGoalDeployAwValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def _drifted_spec(self, template_id: str, transformed_text: str):
        temp_template = Path(self.temp_dir.name) / f"{template_id}-drifted.md"
        temp_template.write_text(transformed_text, encoding="utf-8")
        original_spec = deploy_aw.TEMPLATE_SPECS[template_id]
        return dataclasses.replace(original_spec, source_relpath=str(temp_template))

    def _load_deployed_skill_module(self):
        deployed_skill_root = (
            Path(self.temp_dir.name)
            / "deployed"
            / deploy_aw.DEFAULT_CLAUDE_SKILL_NAME
        )
        shutil.copytree(
            deploy_aw.SKILL_ROOT,
            deployed_skill_root,
            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
        )
        module = load_deploy_aw_module(
            deployed_skill_root / "scripts" / "deploy_aw.py",
            f"set_harness_goal_deploy_aw_deployed_{len(sys.modules)}",
        )
        return module, deployed_skill_root

    def test_validate_accepts_goal_charter_nested_engineering_node_fields(self) -> None:
        issues = deploy_aw.validate_template_source(deploy_aw.TEMPLATE_SPECS["goal-charter"])

        self.assertEqual(issues, [])

    def test_validate_rejects_indented_required_metadata_field(self) -> None:
        original_text = deploy_aw.TEMPLATE_SPECS["goal-charter"].source_path.read_text(
            encoding="utf-8"
        )
        drifted_text = original_text.replace("- owner:\n", "  - owner:\n", 1)
        drifted_spec = self._drifted_spec("goal-charter", drifted_text)

        issues = deploy_aw.validate_template_source(drifted_spec)

        self.assertIn("missing keyed field in section Metadata: owner", issues)

    def test_validate_rejects_unindented_required_nested_field(self) -> None:
        original_text = deploy_aw.TEMPLATE_SPECS["goal-charter"].source_path.read_text(
            encoding="utf-8"
        )
        drifted_text = original_text.replace(
            "  - merge_required:\n", "- merge_required:\n", 1
        )
        drifted_spec = self._drifted_spec("goal-charter", drifted_text)

        issues = deploy_aw.validate_template_source(drifted_spec)

        self.assertIn(
            "missing nested keyed field in section Engineering Node Map: merge_required",
            issues,
        )

    def test_validate_requires_interruption_strategy_in_goal_node_fields(self) -> None:
        original_text = deploy_aw.TEMPLATE_SPECS["goal-charter"].source_path.read_text(
            encoding="utf-8"
        )
        drifted_text = original_text.replace("  - if_interrupted_strategy:\n", "", 1)
        drifted_spec = self._drifted_spec("goal-charter", drifted_text)

        issues = deploy_aw.validate_template_source(drifted_spec)

        self.assertIn(
            "missing nested keyed field in section Engineering Node Map: if_interrupted_strategy",
            issues,
        )

    def test_validate_static_goal_charter_answer_template_requires_node_fields(self) -> None:
        original_spec = deploy_aw.STATIC_ASSET_SPECS["goal-charter-template"]
        original_text = original_spec.source_path.read_text(encoding="utf-8")
        drifted_text = original_text.replace("  - if_interrupted_strategy:\n", "", 1)
        temp_template = Path(self.temp_dir.name) / "goal-charter-answer-drifted.md"
        temp_template.write_text(drifted_text, encoding="utf-8")
        drifted_spec = dataclasses.replace(
            original_spec, source_relpath=str(temp_template)
        )

        issues = deploy_aw.validate_static_asset_source(drifted_spec)

        self.assertIn(
            "missing nested keyed field in section Engineering Node Map: if_interrupted_strategy",
            issues,
        )

    def test_generate_rejects_invalid_static_goal_charter_answer_template(self) -> None:
        output_root = Path(self.temp_dir.name) / "repo"
        output_root.mkdir()
        original_spec = deploy_aw.STATIC_ASSET_SPECS["goal-charter-template"]
        original_text = original_spec.source_path.read_text(encoding="utf-8")
        drifted_text = original_text.replace("  - if_interrupted_strategy:\n", "", 1)
        temp_template = Path(self.temp_dir.name) / "goal-charter-answer-drifted.md"
        temp_template.write_text(drifted_text, encoding="utf-8")
        drifted_spec = dataclasses.replace(
            original_spec, source_relpath=str(temp_template)
        )
        args = deploy_aw.parse_args(
            [
                "generate",
                "--template",
                "goal-charter",
                "--deploy-path",
                str(output_root),
                "--baseline-branch",
                "main",
            ]
        )

        with self.assertRaises(deploy_aw.DeployAwError) as raised:
            deploy_aw.run_generate(
                [deploy_aw.TEMPLATE_SPECS["goal-charter"]],
                [drifted_spec],
                args,
            )

        self.assertIn(
            "missing nested keyed field in section Engineering Node Map: if_interrupted_strategy",
            str(raised.exception),
        )
        self.assertFalse((output_root / ".aw" / "goal-charter.md").exists())
        self.assertFalse(
            (output_root / ".aw" / "template" / "goal-charter.template.md").exists()
        )

    def test_repo_snapshot_mainline_branch_uses_baseline_branch(self) -> None:
        output_root = Path(self.temp_dir.name) / ".aw"
        args = deploy_aw.parse_args(
            [
                "generate",
                "--template",
                "repo-snapshot-status",
                "--deploy-path",
                self.temp_dir.name,
                "--baseline-branch",
                "main",
                "--branch",
                "feature/foo",
                "--force",
            ]
        )

        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = deploy_aw.run_generate(
                [deploy_aw.TEMPLATE_SPECS["repo-snapshot-status"]],
                [],
                args,
            )

        self.assertEqual(exit_code, 0)
        rendered = (output_root / "repo" / "snapshot-status.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("## Mainline Status\n\n- baseline_branch: main\n", rendered)
        self.assertNotIn("- branch: feature/foo", rendered)

    def test_existing_code_adoption_profile_writes_discovery_input(self) -> None:
        output_root = Path(self.temp_dir.name)
        args = deploy_aw.parse_args(
            [
                "generate",
                "--deploy-path",
                str(output_root),
                "--adoption-mode",
                "existing-code-adoption",
                "--baseline-branch",
                "master",
                "--force",
            ]
        )
        selected_specs = deploy_aw.resolve_selected_specs(args)
        static_assets = deploy_aw.resolve_static_asset_specs(args)

        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = deploy_aw.run_generate(selected_specs, static_assets, args)

        self.assertEqual(exit_code, 0)
        discovery_path = output_root / ".aw" / "repo" / "discovery-input.md"
        self.assertTrue(discovery_path.is_file())
        discovery_text = discovery_path.read_text(encoding="utf-8")
        self.assertIn('artifact_type: "repo-discovery-input"', discovery_text)
        self.assertIn("- adoption_mode: existing-code-adoption", discovery_text)
        self.assertIn(f"- repository_path: {output_root.resolve()}", discovery_text)
        self.assertNotIn("TODO(repository_path)", discovery_text)
        self.assertIn("- baseline_branch: master", discovery_text)

        analysis_path = output_root / ".aw" / "repo" / "analysis.md"
        self.assertTrue(analysis_path.is_file())
        analysis_text = analysis_path.read_text(encoding="utf-8")
        self.assertIn('artifact_type: "repo-analysis"', analysis_text)
        self.assertIn("- analysis_status: TODO(analysis_status)", analysis_text)
        self.assertIn("- recommended_next_route: TODO(recommended_next_route)", analysis_text)

        control_state_text = (output_root / ".aw" / "control-state.md").read_text(encoding="utf-8")
        self.assertIn("- repo_analysis: repo/analysis.md", control_state_text)
        self.assertIn("- repo_scope: active", control_state_text)
        self.assertIn("- worktrack_scope: closed", control_state_text)
        self.assertIn("- latest_observed_checkpoint:", control_state_text)
        self.assertIn("- last_doc_catch_up_checkpoint:", control_state_text)

    def test_repo_analysis_baseline_ref_stays_placeholder_when_only_branch_is_known(self) -> None:
        output_root = Path(self.temp_dir.name)
        args = deploy_aw.parse_args(
            [
                "generate",
                "--template",
                "repo-analysis",
                "--deploy-path",
                str(output_root),
                "--baseline-branch",
                "develop-main",
                "--force",
            ]
        )

        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = deploy_aw.run_generate(
                [deploy_aw.TEMPLATE_SPECS["repo-analysis"]],
                [],
                args,
            )

        self.assertEqual(exit_code, 0)
        analysis_text = (output_root / ".aw" / "repo" / "analysis.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("- baseline_branch: develop-main", analysis_text)
        self.assertIn("- baseline_ref: TODO(baseline_ref)", analysis_text)
        self.assertNotIn("- baseline_ref: develop-main", analysis_text)

    def test_existing_code_adoption_env_deploy_path_writes_repository_path(self) -> None:
        output_root = Path(self.temp_dir.name)
        args = deploy_aw.parse_args(
            [
                "generate",
                "--adoption-mode",
                "existing-code-adoption",
                "--baseline-branch",
                "master",
                "--force",
            ]
        )
        selected_specs = deploy_aw.resolve_selected_specs(args)
        static_assets = deploy_aw.resolve_static_asset_specs(args)

        with mock.patch.dict(deploy_aw.os.environ, {"DEPLOY_PATH": str(output_root)}):
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = deploy_aw.run_generate(selected_specs, static_assets, args)

        self.assertEqual(exit_code, 0)
        discovery_path = output_root / ".aw" / "repo" / "discovery-input.md"
        self.assertTrue(discovery_path.is_file())
        discovery_text = discovery_path.read_text(encoding="utf-8")
        self.assertIn(f"- repository_path: {output_root.resolve()}", discovery_text)
        self.assertNotIn("TODO(repository_path)", discovery_text)
        self.assertIn("- baseline_branch: master", discovery_text)

    def test_resolve_baseline_branch_prefers_origin_head(self) -> None:
        args = deploy_aw.parse_args(
            [
                "generate",
                "--deploy-path",
                self.temp_dir.name,
            ]
        )

        with mock.patch.dict(deploy_aw.os.environ, {"AW_BASELINE_BRANCH": ""}):
            with mock.patch.object(deploy_aw, "run_git_output", return_value="origin/master"):
                baseline = deploy_aw.resolve_baseline_branch(args, Path(self.temp_dir.name))

        self.assertEqual(baseline, "master")

    def test_resolve_baseline_branch_accepts_short_origin_head_branch(self) -> None:
        args = deploy_aw.parse_args(
            [
                "generate",
                "--deploy-path",
                self.temp_dir.name,
            ]
        )

        with mock.patch.dict(deploy_aw.os.environ, {"AW_BASELINE_BRANCH": ""}):
            with mock.patch.object(deploy_aw, "run_git_output", return_value="master"):
                baseline = deploy_aw.resolve_baseline_branch(args, Path(self.temp_dir.name))

        self.assertEqual(baseline, "master")

    def test_resolve_baseline_branch_ignores_empty_origin_head(self) -> None:
        args = deploy_aw.parse_args(
            [
                "generate",
                "--deploy-path",
                self.temp_dir.name,
            ]
        )

        def ref_exists(_repo_root: Path, ref: str) -> bool:
            return ref == "refs/remotes/origin/master"

        with mock.patch.dict(deploy_aw.os.environ, {"AW_BASELINE_BRANCH": ""}):
            with mock.patch.object(deploy_aw, "run_git_output", return_value="origin/"):
                with mock.patch.object(deploy_aw, "git_ref_exists", side_effect=ref_exists):
                    baseline = deploy_aw.resolve_baseline_branch(
                        args, Path(self.temp_dir.name)
                    )

        self.assertEqual(baseline, "master")

    def test_resolve_baseline_branch_prefers_environment_value(self) -> None:
        args = deploy_aw.parse_args(
            [
                "generate",
                "--deploy-path",
                self.temp_dir.name,
            ]
        )

        with mock.patch.dict(
            deploy_aw.os.environ,
            {"AW_BASELINE_BRANCH": " release/main "},
        ):
            baseline = deploy_aw.resolve_baseline_branch(args, Path(self.temp_dir.name))

        self.assertEqual(baseline, "release/main")

    def test_resolve_baseline_branch_uses_unique_remote_candidate(self) -> None:
        args = deploy_aw.parse_args(
            [
                "generate",
                "--deploy-path",
                self.temp_dir.name,
            ]
        )

        def ref_exists(_repo_root: Path, ref: str) -> bool:
            return ref == "refs/remotes/origin/main"

        with mock.patch.dict(deploy_aw.os.environ, {"AW_BASELINE_BRANCH": ""}):
            with mock.patch.object(deploy_aw, "run_git_output", return_value=None):
                with mock.patch.object(deploy_aw, "git_ref_exists", side_effect=ref_exists):
                    baseline = deploy_aw.resolve_baseline_branch(
                        args, Path(self.temp_dir.name)
                    )

        self.assertEqual(baseline, "main")

    def test_resolve_baseline_branch_rejects_ambiguous_remote_candidates(self) -> None:
        args = deploy_aw.parse_args(
            [
                "generate",
                "--deploy-path",
                self.temp_dir.name,
            ]
        )

        def ref_exists(_repo_root: Path, ref: str) -> bool:
            return ref in {
                "refs/remotes/origin/main",
                "refs/remotes/origin/master",
            }

        with mock.patch.dict(deploy_aw.os.environ, {"AW_BASELINE_BRANCH": ""}):
            with mock.patch.object(deploy_aw, "run_git_output", return_value=None):
                with mock.patch.object(deploy_aw, "git_ref_exists", side_effect=ref_exists):
                    with self.assertRaises(deploy_aw.DeployAwError) as raised:
                        deploy_aw.resolve_baseline_branch(args, Path(self.temp_dir.name))

        self.assertIn("ambiguous remote baseline branches", str(raised.exception))

    def test_resolve_baseline_branch_uses_unique_local_candidate(self) -> None:
        args = deploy_aw.parse_args(
            [
                "generate",
                "--deploy-path",
                self.temp_dir.name,
            ]
        )

        def ref_exists(_repo_root: Path, ref: str) -> bool:
            return ref == "refs/heads/master"

        with mock.patch.dict(deploy_aw.os.environ, {"AW_BASELINE_BRANCH": ""}):
            with mock.patch.object(deploy_aw, "run_git_output", return_value=None):
                with mock.patch.object(deploy_aw, "git_ref_exists", side_effect=ref_exists):
                    baseline = deploy_aw.resolve_baseline_branch(
                        args, Path(self.temp_dir.name)
                    )

        self.assertEqual(baseline, "master")

    def test_resolve_baseline_branch_rejects_unverified_baseline(self) -> None:
        args = deploy_aw.parse_args(
            [
                "generate",
                "--deploy-path",
                self.temp_dir.name,
            ]
        )

        def git_output(_repo_root: Path, *git_args: str) -> str | None:
            if git_args == ("config", "--get", "init.defaultBranch"):
                return "main"
            return None

        with mock.patch.dict(deploy_aw.os.environ, {"AW_BASELINE_BRANCH": ""}):
            with mock.patch.object(deploy_aw, "run_git_output", side_effect=git_output):
                with mock.patch.object(deploy_aw, "git_ref_exists", return_value=False):
                    with self.assertRaises(deploy_aw.DeployAwError) as raised:
                        deploy_aw.resolve_baseline_branch(args, Path(self.temp_dir.name))

        self.assertIn("unable to resolve baseline branch", str(raised.exception))

    def test_generate_rejects_unverified_baseline_before_writes(self) -> None:
        output_root = Path(self.temp_dir.name) / "repo"
        output_root.mkdir()
        args = deploy_aw.parse_args(
            [
                "generate",
                "--template",
                "goal-charter",
                "--deploy-path",
                str(output_root),
            ]
        )

        with mock.patch.dict(deploy_aw.os.environ, {"AW_BASELINE_BRANCH": ""}):
            with mock.patch.object(deploy_aw, "run_git_output", return_value=None):
                with mock.patch.object(deploy_aw, "git_ref_exists", return_value=False):
                    with self.assertRaises(deploy_aw.DeployAwError) as raised:
                        deploy_aw.run_generate(
                            [deploy_aw.TEMPLATE_SPECS["goal-charter"]],
                            [],
                            args,
                        )

        self.assertIn("unable to resolve baseline branch", str(raised.exception))
        self.assertFalse((output_root / ".aw").exists())

    def test_generate_can_install_set_goal_skill_for_claude(self) -> None:
        output_root = Path(self.temp_dir.name)
        args = deploy_aw.parse_args(
            [
                "generate",
                "--template",
                "goal-charter",
                "--deploy-path",
                str(output_root),
                "--baseline-branch",
                "main",
                "--install-claude-skill",
            ]
        )

        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = deploy_aw.run_generate(
                [deploy_aw.TEMPLATE_SPECS["goal-charter"]],
                [],
                args,
            )

        self.assertEqual(exit_code, 0)
        claude_skill_root = (
            output_root
            / ".claude"
            / "skills"
            / "aw-set-harness-goal-skill"
        )
        self.assertTrue((claude_skill_root / "SKILL.md").is_file())
        self.assertTrue((claude_skill_root / "scripts" / "deploy_aw.py").is_file())
        self.assertTrue((claude_skill_root / "assets" / "control-state.md").is_file())
        self.assertFalse((claude_skill_root / "payload.json").exists())
        self.assertFalse((claude_skill_root / "aw.marker").exists())

    def test_generate_install_claude_skill_allows_symlink_root_self_install(self) -> None:
        deployed_module, deployed_skill_root = self._load_deployed_skill_module()
        output_root = Path(self.temp_dir.name) / "repo"
        output_root.mkdir()
        claude_dir = output_root / ".claude"
        claude_dir.mkdir()
        (claude_dir / "skills").symlink_to(
            deployed_skill_root.parent,
            target_is_directory=True,
        )
        args = deployed_module.parse_args(
            [
                "generate",
                "--template",
                "goal-charter",
                "--deploy-path",
                str(output_root),
                "--baseline-branch",
                "main",
                "--install-claude-skill",
            ]
        )

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            exit_code = deployed_module.run_generate(
                [deployed_module.TEMPLATE_SPECS["goal-charter"]],
                [],
                args,
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("Claude skill already installed", stdout.getvalue())
        self.assertTrue((output_root / ".aw" / "goal-charter.md").is_file())

    def test_generate_install_claude_skill_rejects_file_claude_dir_before_aw_write(self) -> None:
        output_root = Path(self.temp_dir.name)
        (output_root / ".claude").write_text("not a directory\n", encoding="utf-8")
        args = deploy_aw.parse_args(
            [
                "generate",
                "--template",
                "goal-charter",
                "--deploy-path",
                str(output_root),
                "--baseline-branch",
                "main",
                "--install-claude-skill",
            ]
        )

        with self.assertRaises(deploy_aw.DeployAwError) as raised:
            deploy_aw.run_generate(
                [deploy_aw.TEMPLATE_SPECS["goal-charter"]],
                [],
                args,
            )

        self.assertIn("Claude skill target ancestor is not a directory", str(raised.exception))
        self.assertFalse((output_root / ".aw" / "goal-charter.md").exists())

    def test_generate_install_claude_skill_rejects_file_skills_dir_before_aw_write(self) -> None:
        output_root = Path(self.temp_dir.name)
        claude_dir = output_root / ".claude"
        claude_dir.mkdir()
        (claude_dir / "skills").write_text("not a directory\n", encoding="utf-8")
        args = deploy_aw.parse_args(
            [
                "generate",
                "--template",
                "goal-charter",
                "--deploy-path",
                str(output_root),
                "--baseline-branch",
                "main",
                "--install-claude-skill",
            ]
        )

        with self.assertRaises(deploy_aw.DeployAwError) as raised:
            deploy_aw.run_generate(
                [deploy_aw.TEMPLATE_SPECS["goal-charter"]],
                [],
                args,
            )

        self.assertIn("Claude skill target ancestor is not a directory", str(raised.exception))
        self.assertFalse((output_root / ".aw" / "goal-charter.md").exists())

    def test_generate_install_claude_skill_rejects_file_custom_root_ancestor_before_aw_write(self) -> None:
        output_root = Path(self.temp_dir.name)
        claude_root_file = output_root / "custom-claude-root"
        claude_root_file.write_text("not a directory\n", encoding="utf-8")
        args = deploy_aw.parse_args(
            [
                "generate",
                "--template",
                "goal-charter",
                "--deploy-path",
                str(output_root),
                "--baseline-branch",
                "main",
                "--install-claude-skill",
                "--claude-root",
                str(claude_root_file / "skills"),
            ]
        )

        with self.assertRaises(deploy_aw.DeployAwError) as raised:
            deploy_aw.run_generate(
                [deploy_aw.TEMPLATE_SPECS["goal-charter"]],
                [],
                args,
            )

        self.assertIn("Claude skill target ancestor is not a directory", str(raised.exception))
        self.assertFalse((output_root / ".aw" / "goal-charter.md").exists())

    def test_collect_skill_package_files_excludes_git_metadata(self) -> None:
        fake_skill_root = Path(self.temp_dir.name) / "fake-skill"
        git_dir = fake_skill_root / ".git"
        git_dir.mkdir(parents=True)
        (git_dir / "config").write_text("[core]\n", encoding="utf-8")
        (fake_skill_root / "SKILL.md").write_text("# Fake\n", encoding="utf-8")
        previous_skill_root = deploy_aw.SKILL_ROOT
        deploy_aw.SKILL_ROOT = fake_skill_root
        try:
            package_files = deploy_aw.collect_skill_package_files()
        finally:
            deploy_aw.SKILL_ROOT = previous_skill_root

        relative_paths = [relative_path for _, relative_path in package_files]
        self.assertIn(Path("SKILL.md"), relative_paths)
        self.assertFalse(
            any(".git" in relative_path.parts for relative_path in relative_paths)
        )

    def test_install_claude_skill_refuses_existing_file_without_force(self) -> None:
        output_root = Path(self.temp_dir.name)
        existing_skill = (
            output_root
            / ".claude"
            / "skills"
            / "aw-set-harness-goal-skill"
            / "SKILL.md"
        )
        existing_skill.parent.mkdir(parents=True)
        existing_skill.write_text("existing\n", encoding="utf-8")
        args = deploy_aw.parse_args(
            [
                "install-claude-skill",
                "--deploy-path",
                str(output_root),
            ]
        )

        with self.assertRaises(deploy_aw.DeployAwError) as raised:
            deploy_aw.run_install_claude_skill(args)

        self.assertIn(
            "refusing to overwrite existing Claude skill file",
            str(raised.exception),
        )
        self.assertEqual(existing_skill.read_text(encoding="utf-8"), "existing\n")

    def test_install_claude_skill_refuses_symlinked_package_subdir(self) -> None:
        output_root = Path(self.temp_dir.name)
        outside_assets = output_root / "outside-assets"
        outside_assets.mkdir()
        skill_root = (
            output_root
            / ".claude"
            / "skills"
            / "aw-set-harness-goal-skill"
        )
        skill_root.mkdir(parents=True)
        (skill_root / "assets").symlink_to(outside_assets, target_is_directory=True)
        args = deploy_aw.parse_args(
            [
                "install-claude-skill",
                "--deploy-path",
                str(output_root),
            ]
        )

        with self.assertRaises(deploy_aw.DeployAwError) as raised:
            deploy_aw.run_install_claude_skill(args)

        self.assertIn(
            "refusing to install through symlinked Claude skill directory",
            str(raised.exception),
        )
        self.assertFalse((outside_assets / "control-state.md").exists())

    def test_install_claude_skill_rechecks_symlinked_parent_immediately_before_copy(self) -> None:
        output_root = Path(self.temp_dir.name)
        source_root = output_root / "source"
        source_root.mkdir()
        first_source = source_root / "SKILL.md"
        second_source = source_root / "control-state.md"
        first_source.write_text("skill\n", encoding="utf-8")
        second_source.write_text("control\n", encoding="utf-8")
        outside_assets = output_root / "outside-assets"
        outside_assets.mkdir()
        target_skill_dir = (
            output_root
            / ".claude"
            / "skills"
            / "aw-set-harness-goal-skill"
        )
        package_files = [
            (first_source, Path("SKILL.md")),
            (second_source, Path("assets") / "control-state.md"),
        ]
        original_copy2 = shutil.copy2

        def copy_with_race(source_path: Path, target_path: Path) -> None:
            original_copy2(source_path, target_path)
            if Path(target_path).name == "SKILL.md":
                (target_skill_dir / "assets").symlink_to(
                    outside_assets,
                    target_is_directory=True,
                )

        with mock.patch.object(deploy_aw.shutil, "copy2", side_effect=copy_with_race):
            with self.assertRaises(deploy_aw.DeployAwError) as raised:
                deploy_aw.install_claude_skill_package(
                    package_files,
                    target_skill_dir=target_skill_dir,
                    force=False,
                    dry_run=False,
                )

        self.assertIn(
            "refusing to install through symlinked Claude skill directory",
            str(raised.exception),
        )
        self.assertFalse((outside_assets / "control-state.md").exists())

    def test_install_claude_skill_sets_copied_file_permissions_to_0644(self) -> None:
        output_root = Path(self.temp_dir.name)
        source_root = output_root / "source"
        source_root.mkdir()
        source_file = source_root / "SKILL.md"
        source_file.write_text("skill\n", encoding="utf-8")
        source_file.chmod(0o755)
        target_skill_dir = (
            output_root
            / ".claude"
            / "skills"
            / "aw-set-harness-goal-skill"
        )

        with contextlib.redirect_stdout(io.StringIO()):
            deploy_aw.install_claude_skill_package(
                [(source_file, Path("SKILL.md"))],
                target_skill_dir=target_skill_dir,
                force=False,
                dry_run=False,
            )

        target_file = target_skill_dir / "SKILL.md"
        self.assertEqual(target_file.stat().st_mode & 0o777, 0o644)

    def test_install_claude_skill_allows_symlinked_claude_root_override(self) -> None:
        output_root = Path(self.temp_dir.name)
        outside_root = output_root / "outside-claude-skills"
        outside_root.mkdir()
        symlinked_claude_root = output_root / "claude-skills-link"
        symlinked_claude_root.symlink_to(outside_root, target_is_directory=True)
        args = deploy_aw.parse_args(
            [
                "install-claude-skill",
                "--deploy-path",
                str(output_root),
                "--claude-root",
                str(symlinked_claude_root),
            ]
        )

        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = deploy_aw.run_install_claude_skill(args)

        self.assertEqual(exit_code, 0)
        installed_skill = outside_root / "aw-set-harness-goal-skill"
        self.assertTrue((installed_skill / "SKILL.md").is_file())
        self.assertTrue((installed_skill / "scripts" / "deploy_aw.py").is_file())

    def test_install_claude_skill_allows_symlinked_default_claude_skills_root(self) -> None:
        output_root = Path(self.temp_dir.name)
        outside_root = output_root / "outside-claude-skills"
        outside_root.mkdir()
        claude_dir = output_root / ".claude"
        claude_dir.mkdir()
        (claude_dir / "skills").symlink_to(outside_root, target_is_directory=True)
        args = deploy_aw.parse_args(
            [
                "install-claude-skill",
                "--deploy-path",
                str(output_root),
            ]
        )

        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = deploy_aw.run_install_claude_skill(args)

        self.assertEqual(exit_code, 0)
        installed_skill = outside_root / "aw-set-harness-goal-skill"
        self.assertTrue((installed_skill / "SKILL.md").is_file())
        self.assertTrue((installed_skill / "scripts" / "deploy_aw.py").is_file())

    def test_install_claude_skill_allows_symlink_root_self_install(self) -> None:
        deployed_module, deployed_skill_root = self._load_deployed_skill_module()
        output_root = Path(self.temp_dir.name) / "repo"
        output_root.mkdir()
        claude_dir = output_root / ".claude"
        claude_dir.mkdir()
        (claude_dir / "skills").symlink_to(
            deployed_skill_root.parent,
            target_is_directory=True,
        )
        args = deployed_module.parse_args(
            [
                "install-claude-skill",
                "--deploy-path",
                str(output_root),
            ]
        )

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            exit_code = deployed_module.run_install_claude_skill(args)

        self.assertEqual(exit_code, 0)
        self.assertIn("Claude skill already installed", stdout.getvalue())

    def test_install_claude_skill_rejects_symlink_alias_to_source_skill(self) -> None:
        output_root = Path(self.temp_dir.name)
        target_skill_dir = (
            output_root
            / ".claude"
            / "skills"
            / "aw-set-harness-goal-skill"
        )
        target_skill_dir.parent.mkdir(parents=True)
        target_skill_dir.symlink_to(deploy_aw.SKILL_ROOT, target_is_directory=True)
        args = deploy_aw.parse_args(
            [
                "install-claude-skill",
                "--deploy-path",
                str(output_root),
            ]
        )

        with self.assertRaises(deploy_aw.DeployAwError) as raised:
            deploy_aw.run_install_claude_skill(args)

        self.assertIn(
            "refusing to install into symlinked Claude skill dir",
            str(raised.exception),
        )

    def test_install_claude_skill_refuses_existing_internal_symlink_subdir(self) -> None:
        output_root = Path(self.temp_dir.name)
        outside_legacy = output_root / "outside-legacy"
        outside_legacy.mkdir()
        skill_root = (
            output_root
            / ".claude"
            / "skills"
            / "aw-set-harness-goal-skill"
        )
        skill_root.mkdir(parents=True)
        (skill_root / "legacy").symlink_to(outside_legacy, target_is_directory=True)
        args = deploy_aw.parse_args(
            [
                "install-claude-skill",
                "--deploy-path",
                str(output_root),
            ]
        )

        with self.assertRaises(deploy_aw.DeployAwError) as raised:
            deploy_aw.run_install_claude_skill(args)

        self.assertIn(
            "refusing to install through symlinked Claude skill directory",
            str(raised.exception),
        )

    def test_claude_skill_target_uses_wrapped_name_from_deployed_wrapper(self) -> None:
        output_root = Path(self.temp_dir.name) / "repo"
        output_root.mkdir()
        deployed_script = (
            Path(self.temp_dir.name)
            / "aw-set-harness-goal-skill"
            / "scripts"
            / "deploy_aw.py"
        )
        deployed_script.parent.mkdir(parents=True)
        shutil.copy2(DEPLOY_AW_PATH, deployed_script)
        deployed_module = load_deploy_aw_module(
            deployed_script,
            "set_harness_goal_deploy_aw_deployed_wrapper",
        )
        args = deployed_module.parse_args(
            [
                "install-claude-skill",
                "--deploy-path",
                str(output_root),
            ]
        )

        self.assertEqual(
            deployed_module.claude_skill_target_dir_for(args, output_root),
            output_root / ".claude" / "skills" / "aw-set-harness-goal-skill",
        )


if __name__ == "__main__":
    unittest.main()
