from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = REPO_ROOT / "product" / "harness-operations" / "manifests" / "harness.template.yaml"


def load_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def command_line(template_text: str, name: str) -> str:
    prefix = f"    {name}: "
    for line in template_text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    raise AssertionError(f"missing command {name} in harness template")


class HarnessTemplateContractTest(unittest.TestCase):
    def test_scope_gate_uses_harness_scope_checker(self) -> None:
        template = load_template()
        scope_cmd = command_line(template, "scope_gate")
        self.assertIn("toolchain/scripts/test/harness_scope_gate.py", scope_cmd)
        self.assertIn("--harness-file .autoworkflow/harness.yaml", scope_cmd)

    def test_backfill_gate_pins_state_and_closeout_paths(self) -> None:
        template = load_template()
        backfill_cmd = command_line(template, "backfill_gate")
        self.assertIn("toolchain/scripts/test/gate_status_backfill.py", backfill_cmd)
        self.assertIn("--workflow-id pending", backfill_cmd)
        self.assertIn("--gate scope_gate", backfill_cmd)
        self.assertIn("--status passed", backfill_cmd)
        self.assertIn("--state-file .autoworkflow/state/harness-review-loop.json", backfill_cmd)
        self.assertIn("--closeout-root .autoworkflow/closeout", backfill_cmd)

    def test_smoke_gate_avoids_build_and_repo_local_mount_side_effects(self) -> None:
        template = load_template()
        smoke_cmd = command_line(template, "smoke_gate")
        self.assertNotIn(" adapter_deploy.py build ", smoke_cmd)
        self.assertNotIn(" adapter_deploy.py local ", smoke_cmd)
        self.assertIn("adapter_deploy.py global --backend agents", smoke_cmd)
        self.assertIn("--agents-root .autoworkflow/smoke/agents/skills", smoke_cmd)


if __name__ == "__main__":
    unittest.main()
