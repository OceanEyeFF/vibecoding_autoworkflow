from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scope_gate_check import check_scope
from gate_status_backfill import update_state


def test_check_scope_accepts_allowed_prefixes() -> None:
    result = check_scope(
        [
            "docs/analysis/README.md",
            "docs/operations/autoresearch-closeout-acceptance-gate.md",
            ".autoworkflow/closeout/demo/summary.json",
            "toolchain/scripts/test/scope_gate_check.py",
        ],
        (
            ".autoworkflow/closeout/",
            "docs/analysis/README.md",
            "docs/operations/",
            "toolchain/scripts/test/",
        ),
    )
    assert result.passed is True
    assert result.violations == []


def test_check_scope_flags_disallowed_changes() -> None:
    result = check_scope(["docs/analysis/autoresearch-closeout-governance-task-list.md"], ("docs/operations/",))
    assert result.passed is False
    assert result.violations == ["docs/analysis/autoresearch-closeout-governance-task-list.md"]


def test_update_state_backfills_gate_status() -> None:
    state = {"gates": {"scope_gate": "pending"}}
    updated = update_state(state, "scope_gate", "passed", {"returncode": 0}, "workflow-1")
    assert updated["workflow_id"] == "workflow-1"
    assert updated["gates"]["scope_gate"] == "passed"
    assert updated["last_backfill"]["gate"] == "scope_gate"
