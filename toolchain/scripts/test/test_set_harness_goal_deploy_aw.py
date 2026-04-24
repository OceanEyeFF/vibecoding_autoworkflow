from __future__ import annotations

import dataclasses
import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
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


def load_deploy_aw_module():
    spec = importlib.util.spec_from_file_location(
        "set_harness_goal_deploy_aw", DEPLOY_AW_PATH
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


if __name__ == "__main__":
    unittest.main()
