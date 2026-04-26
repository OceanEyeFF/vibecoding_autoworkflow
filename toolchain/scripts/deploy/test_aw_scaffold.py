from __future__ import annotations

import contextlib
import dataclasses
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import aw_scaffold


class AwScaffoldTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_root = Path(self.temp_dir.name) / "aw-state"
        self.addCleanup(self.temp_dir.cleanup)

    def _run_cli(self, *argv: object) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(sys, "argv", ["aw_scaffold.py", *map(str, argv)]),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            return aw_scaffold.main(), stdout.getvalue(), stderr.getvalue()

    def _write_drifted_template(self, template_id: str, transformed_text: str) -> tuple[Path, aw_scaffold.TemplateSpec]:
        temp_template = Path(self.temp_dir.name) / f"{template_id}-drifted.md"
        temp_template.write_text(transformed_text, encoding="utf-8")
        original_spec = aw_scaffold.TEMPLATE_SPECS[template_id]
        drifted_spec = dataclasses.replace(original_spec, source_relpath=str(temp_template))
        return temp_template, drifted_spec

    def test_validate_legacy_scaffold_profile_succeeds(self) -> None:
        code, stdout, stderr = self._run_cli("validate", "--profile", "first-wave-minimal")

        self.assertEqual(code, 0, stderr)
        self.assertIn("[control-state] ok", stdout)
        self.assertIn("[worktrack-plan-task-queue] ok", stdout)

    def test_generate_legacy_scaffold_profile_to_custom_output_root(self) -> None:
        code, stdout, stderr = self._run_cli(
            "generate",
            "--profile",
            "first-wave-minimal",
            "--output-root",
            self.output_root,
            "--repo",
            "demo-repo",
            "--owner",
            "aw-kernel",
            "--updated",
            "2026-04-16",
            "--baseline-branch",
            "main",
            "--worktrack-id",
            "wt-demo",
            "--branch",
            "feat/wt-demo",
        )

        self.assertEqual(code, 0, stderr)
        self.assertIn("wrote", stdout)

        expected_files = [
            self.output_root / "control-state.md",
            self.output_root / "goal-charter.md",
            self.output_root / "repo" / "snapshot-status.md",
            self.output_root / "repo" / "analysis.md",
            self.output_root / "worktrack" / "contract.md",
            self.output_root / "worktrack" / "plan-task-queue.md",
        ]
        for path in expected_files:
            self.assertTrue(path.is_file(), path)

        contract_text = (self.output_root / "worktrack" / "contract.md").read_text(encoding="utf-8")
        self.assertIn('artifact_type: "worktrack-contract"', contract_text)
        self.assertIn("- worktrack_id: wt-demo", contract_text)
        self.assertIn("- branch: feat/wt-demo", contract_text)
        self.assertIn("- baseline_branch: main", contract_text)
        self.assertIn("- baseline_ref: main", contract_text)
        self.assertIn("## Node Type", contract_text)
        self.assertIn("- source_from_goal_charter: TODO(source_from_goal_charter)", contract_text)
        self.assertIn("- if_interrupted_strategy: TODO(if_interrupted_strategy)", contract_text)
        self.assertIn("## Constraints", contract_text)
        self.assertIn("## Verification Requirements", contract_text)
        self.assertIn("这是 `.aw/worktrack/contract.md` 的运行样例", contract_text)
        self.assertNotIn("这是 `.aw/worktrack/contract.md` 的模板来源", contract_text)

        goal_text = (self.output_root / "goal-charter.md").read_text(encoding="utf-8")
        self.assertIn("## Engineering Node Map", goal_text)
        self.assertIn("  - if_interrupted_strategy: TODO(if_interrupted_strategy)", goal_text)

        analysis_text = (self.output_root / "repo" / "analysis.md").read_text(encoding="utf-8")
        self.assertIn('artifact_type: "repo-analysis"', analysis_text)
        self.assertIn("- analysis_status: TODO(analysis_status)", analysis_text)
        self.assertIn("- current_main_contradiction: TODO(current_main_contradiction)", analysis_text)
        self.assertIn("- recommended_next_route: TODO(recommended_next_route)", analysis_text)

        plan_text = (self.output_root / "worktrack" / "plan-task-queue.md").read_text(encoding="utf-8")
        self.assertIn("- contract_ref: TODO(contract_ref)", plan_text)
        self.assertIn("- queue_status: TODO(queue_status)", plan_text)
        self.assertIn("- selected_next_action_id: TODO(selected_next_action_id)", plan_text)
        self.assertIn("- node_type: TODO(node_type)", plan_text)
        self.assertIn("- gate_criteria_for_this_round: TODO(gate_criteria_for_this_round)", plan_text)
        self.assertIn("## Dispatch Handoff Packet", plan_text)
        self.assertIn("- dispatch_packet_ready: TODO(dispatch_packet_ready)", plan_text)
        self.assertIn("- recommended_next_route: TODO(recommended_next_route)", plan_text)

        control_state_text = (self.output_root / "control-state.md").read_text(encoding="utf-8")
        self.assertIn("- repo_snapshot: repo/snapshot-status.md", control_state_text)
        self.assertIn("- repo_analysis: repo/analysis.md", control_state_text)
        self.assertIn("- worktrack_contract: worktrack/contract.md", control_state_text)
        self.assertIn("- plan_task_queue: worktrack/plan-task-queue.md", control_state_text)
        self.assertIn("- gate_evidence: TODO(gate_evidence)", control_state_text)
        self.assertIn("## Baseline Traceability", control_state_text)
        self.assertIn("- checkpoint_ref: TODO(checkpoint_ref)", control_state_text)

    def test_generate_refuses_to_overwrite_without_force(self) -> None:
        first_code, _, first_stderr = self._run_cli(
            "generate",
            "--template",
            "control-state",
            "--output-root",
            self.output_root,
        )
        self.assertEqual(first_code, 0, first_stderr)

        second_code, stdout, stderr = self._run_cli(
            "generate",
            "--template",
            "control-state",
            "--output-root",
            self.output_root,
        )

        self.assertEqual(second_code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("refusing to overwrite existing file without --force", stderr)

    def test_generate_single_template_fills_missing_context_with_placeholders(self) -> None:
        code, stdout, stderr = self._run_cli(
            "generate",
            "--template",
            "worktrack-gate-evidence",
            "--output-root",
            self.output_root,
            "--updated",
            "2026-04-16",
        )

        self.assertEqual(code, 0, stderr)
        self.assertIn("wrote", stdout)

        rendered = (self.output_root / "worktrack" / "gate-evidence.md").read_text(encoding="utf-8")
        self.assertIn("- worktrack_id: TODO(worktrack_id)", rendered)
        self.assertIn("- gate_round: TODO(gate_round)", rendered)
        self.assertIn("- required_evidence_lanes: TODO(required_evidence_lanes)", rendered)
        self.assertIn("- overall_confidence: TODO(overall_confidence)", rendered)
        self.assertIn("- recommended_next_route: TODO(recommended_next_route)", rendered)
        self.assertIn("- approval_required: TODO(approval_required)", rendered)
        self.assertIn("- why: TODO(why)", rendered)

    def test_generate_profile_ignores_preexisting_unselected_linked_artifacts(self) -> None:
        gate_dir = self.output_root / "worktrack"
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "gate-evidence.md").write_text("stale gate evidence\n", encoding="utf-8")

        code, stdout, stderr = self._run_cli(
            "generate",
            "--profile",
            "first-wave-minimal",
            "--output-root",
            self.output_root,
            "--force",
        )

        self.assertEqual(code, 0, stderr)
        self.assertIn("wrote", stdout)

        control_state_text = (self.output_root / "control-state.md").read_text(encoding="utf-8")
        self.assertIn("- gate_evidence: TODO(gate_evidence)", control_state_text)
        self.assertNotIn("- gate_evidence: worktrack/gate-evidence.md", control_state_text)

    def test_generate_profile_preflights_collisions_before_any_write(self) -> None:
        self.output_root.mkdir(parents=True, exist_ok=True)
        existing_goal_charter = self.output_root / "goal-charter.md"
        existing_goal_charter.write_text("existing goal charter\n", encoding="utf-8")

        code, stdout, stderr = self._run_cli(
            "generate",
            "--profile",
            "first-wave-minimal",
            "--output-root",
            self.output_root,
        )

        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("refusing to overwrite existing file without --force", stderr)
        self.assertFalse((self.output_root / "control-state.md").exists())
        self.assertFalse((self.output_root / "repo" / "snapshot-status.md").exists())
        self.assertEqual(existing_goal_charter.read_text(encoding="utf-8"), "existing goal charter\n")

    def test_validate_rejects_required_section_heading_level_drift(self) -> None:
        original_text = aw_scaffold.TEMPLATE_SPECS["control-state"].source_path.read_text(
            encoding="utf-8"
        )
        drifted_text = original_text.replace("## Notes", "### Notes", 1)
        _, drifted_spec = self._write_drifted_template("control-state", drifted_text)

        with mock.patch.dict(
            aw_scaffold.TEMPLATE_SPECS,
            {"control-state": drifted_spec},
            clear=False,
        ):
            code, stdout, stderr = self._run_cli("validate", "--template", "control-state")

        self.assertEqual(code, 1)
        self.assertEqual(stderr, "")
        self.assertIn("[control-state] invalid", stdout)
        self.assertIn("missing required section: Notes", stdout)

    def test_validate_rejects_keyed_field_moved_to_wrong_section(self) -> None:
        original_text = aw_scaffold.TEMPLATE_SPECS["control-state"].source_path.read_text(
            encoding="utf-8"
        )
        drifted_text = original_text.replace("- owner:\n", "- maintainer:\n", 1)
        drifted_text = drifted_text.replace("## Notes\n\n- \n", "## Notes\n\n- owner:\n- \n", 1)
        _, drifted_spec = self._write_drifted_template("control-state", drifted_text)

        with mock.patch.dict(
            aw_scaffold.TEMPLATE_SPECS,
            {"control-state": drifted_spec},
            clear=False,
        ):
            code, stdout, stderr = self._run_cli("validate", "--template", "control-state")

        self.assertEqual(code, 1)
        self.assertEqual(stderr, "")
        self.assertIn("[control-state] invalid", stdout)
        self.assertIn("missing keyed field in section Metadata: owner", stdout)

    def test_validate_rejects_missing_goal_node_interruption_strategy(self) -> None:
        original_text = aw_scaffold.TEMPLATE_SPECS["goal-charter"].source_path.read_text(
            encoding="utf-8"
        )
        drifted_text = original_text.replace("  - if_interrupted_strategy:\n", "", 1)
        _, drifted_spec = self._write_drifted_template("goal-charter", drifted_text)

        with mock.patch.dict(
            aw_scaffold.TEMPLATE_SPECS,
            {"goal-charter": drifted_spec},
            clear=False,
        ):
            code, stdout, stderr = self._run_cli("validate", "--template", "goal-charter")

        self.assertEqual(code, 1)
        self.assertEqual(stderr, "")
        self.assertIn("[goal-charter] invalid", stdout)
        self.assertIn(
            "missing nested keyed field in section Engineering Node Map: if_interrupted_strategy",
            stdout,
        )

    def test_validate_rejects_missing_worktrack_node_type_section(self) -> None:
        original_text = aw_scaffold.TEMPLATE_SPECS["worktrack-contract"].source_path.read_text(
            encoding="utf-8"
        )
        drifted_text = original_text.replace("## Node Type", "### Node Type", 1)
        _, drifted_spec = self._write_drifted_template("worktrack-contract", drifted_text)

        with mock.patch.dict(
            aw_scaffold.TEMPLATE_SPECS,
            {"worktrack-contract": drifted_spec},
            clear=False,
        ):
            code, stdout, stderr = self._run_cli("validate", "--template", "worktrack-contract")

        self.assertEqual(code, 1)
        self.assertEqual(stderr, "")
        self.assertIn("[worktrack-contract] invalid", stdout)
        self.assertIn("missing required section: Node Type", stdout)


if __name__ == "__main__":
    unittest.main()
