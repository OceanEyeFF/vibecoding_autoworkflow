from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import agents_first_wave_contract_smoke


class AgentsFirstWaveContractSmokeTest(unittest.TestCase):
    def test_run_smoke_returns_repeatable_first_wave_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            agents_root = workspace / ".agents" / "skills"
            aw_root = workspace / ".aw"

            report = agents_first_wave_contract_smoke.run_smoke(agents_root, aw_root)

        self.assertTrue(report["passed"])
        self.assertEqual(
            [step["skill_id"] for step in report["route"]],
            list(agents_first_wave_contract_smoke.FIRST_WAVE_SKILL_ORDER),
        )
        self.assertEqual(
            report["route"][2]["recommended_repo_action"],
            "enter-worktrack",
        )
        self.assertEqual(report["route"][0]["continuation_decision"], "continue")
        self.assertEqual(report["route"][0]["stop_conditions_hit"], [])
        self.assertTrue(report["route"][2]["continuation_ready"])
        self.assertTrue(report["route"][3]["continuation_ready"])
        self.assertEqual(
            report["route"][4]["selected_executor"],
            "general-task-completion-executor",
        )
        self.assertEqual(
            report["route"][4]["runtime_dispatch_mode"],
            "current-carrier-fallback",
        )
        self.assertTrue(report["route"][4]["fallback_used"])
        self.assertEqual(report["install_cycle"]["verify_result"]["issues"], [])

    def test_cli_json_mode_emits_machine_readable_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            agents_root = workspace / ".agents" / "skills"
            aw_root = workspace / ".aw"
            stdout = io.StringIO()
            stderr = io.StringIO()

            with (
                mock.patch.object(
                    sys,
                    "argv",
                    [
                        "agents_first_wave_contract_smoke.py",
                        "--agents-root",
                        str(agents_root),
                        "--aw-root",
                        str(aw_root),
                        "--json",
                    ],
                ),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                exit_code = agents_first_wave_contract_smoke.main()

        self.assertEqual(exit_code, 0, stderr.getvalue())
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["passed"])
        self.assertEqual(payload["route"][0]["skill_id"], "harness-skill")
        self.assertEqual(payload["route"][0]["continuation_decision"], "continue")
        self.assertEqual(payload["route"][0]["stop_conditions_hit"], [])
        self.assertTrue(payload["route"][2]["continuation_ready"])
        self.assertTrue(payload["route"][3]["continuation_ready"])
        self.assertEqual(
            payload["route"][-1]["selected_executor"],
            "general-task-completion-executor",
        )
        self.assertEqual(
            payload["route"][-1]["runtime_dispatch_mode"],
            "current-carrier-fallback",
        )


if __name__ == "__main__":
    unittest.main()
