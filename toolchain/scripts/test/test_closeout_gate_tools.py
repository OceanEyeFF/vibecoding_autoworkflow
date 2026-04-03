from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import closeout_acceptance_gate
from scope_gate_check import check_scope
from gate_status_backfill import update_state


def test_check_scope_accepts_allowed_prefixes() -> None:
    result = check_scope(
        [
            "docs/analysis/README.md",
            "docs/operations/autoresearch-closeout-acceptance-gate.md",
            ".autoworkflow/closeout/demo/summary.json",
            "toolchain/scripts/test/scope_gate_check.py",
            "tools/scope_gate_check.py",
        ],
        (
            ".autoworkflow/closeout/",
            "docs/analysis/README.md",
            "docs/operations/",
            "toolchain/scripts/test/",
            "tools/scope_gate_check.py",
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


def test_update_state_replaces_cross_workflow_state() -> None:
    state = {
        "workflow_id": "workflow-1",
        "gates": {"scope_gate": "passed"},
        "status": "completed",
    }
    updated = update_state(state, "spec_gate", "failed", {"returncode": 1}, "workflow-2")
    assert updated["workflow_id"] == "workflow-2"
    assert updated["gates"] == {"spec_gate": "failed"}
    assert "status" not in updated


def test_root_tool_shims_dispatch() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    commands = [
        [sys.executable, "tools/scope_gate_check.py", "--help"],
        [sys.executable, "tools/gate_status_backfill.py", "--help"],
        [sys.executable, "tools/closeout_acceptance_gate.py", "--help"],
    ]
    for command in commands:
        completed = subprocess.run(command, cwd=repo_root, capture_output=True, text=True)
        assert completed.returncode == 0


def test_run_scope_gate_allows_foundations_governance_docs(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}

    def fake_run_command(command: list[str], *, cwd: Path) -> dict:
        captured["command"] = command
        return {
            "command": command,
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "passed": True,
        }

    monkeypatch.setattr(closeout_acceptance_gate, "run_command", fake_run_command)

    result = closeout_acceptance_gate.run_scope_gate(tmp_path, sys.executable)

    assert result["passed"] is True
    command = captured["command"]
    assert "docs/knowledge/foundations/path-governance-ai-routing.md" in command
    assert "docs/knowledge/foundations/root-directory-layering.md" in command
    assert "docs/knowledge/foundations/toolchain-layering.md" in command


def test_run_spec_gate_includes_folder_logic(monkeypatch, tmp_path) -> None:
    commands: list[list[str]] = []

    def fake_run_command(command: list[str], *, cwd: Path) -> dict:
        commands.append(command)
        return {
            "command": command,
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "passed": True,
        }

    monkeypatch.setattr(closeout_acceptance_gate, "run_command", fake_run_command)

    result = closeout_acceptance_gate.run_spec_gate(tmp_path, sys.executable)

    assert result["passed"] is True
    assert [item["name"] for item in result["subchecks"]] == [
        "folder_logic",
        "path_governance",
        "governance_semantic",
    ]
    assert any(command[-2:] == ["--repo-root", str(tmp_path)] for command in commands)
    assert any("folder_logic_check.py" in command[1] for command in commands)


def test_run_test_gate_includes_folder_logic_tests(monkeypatch, tmp_path) -> None:
    commands: list[list[str]] = []

    def fake_run_command(command: list[str], *, cwd: Path) -> dict:
        commands.append(command)
        return {
            "command": command,
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "passed": True,
        }

    monkeypatch.setattr(closeout_acceptance_gate, "run_command", fake_run_command)

    result = closeout_acceptance_gate.run_test_gate(tmp_path, sys.executable)

    assert result["passed"] is True
    assert [item["name"] for item in result["subchecks"][:2]] == [
        "gate_tool_tests",
        "folder_logic_tests",
    ]
    assert any(command[-1] == "toolchain/scripts/test/test_folder_logic_check.py" for command in commands)


def test_closeout_gate_fails_closed_on_test_gate_failure(monkeypatch, tmp_path, capsys) -> None:
    class Args:
        repo_root = tmp_path
        workflow_id = "workflow-1"
        json = True

    def fake_run_gate(gate: str, *, repo_root: Path, python: str, workflow_id: str) -> dict:
        return {
            "passed": gate != "test_gate",
            "returncode": 0 if gate != "test_gate" else 1,
        }

    def fake_subprocess_run(*args, **kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args[0], 0, stdout="{}", stderr="")

    monkeypatch.setattr(closeout_acceptance_gate, "parse_args", lambda: Args())
    monkeypatch.setattr(closeout_acceptance_gate, "run_gate", fake_run_gate)
    monkeypatch.setattr(closeout_acceptance_gate.subprocess, "run", fake_subprocess_run)

    assert closeout_acceptance_gate.main() == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is False
    assert [result["gate"] for result in payload["results"]] == [
        "scope_gate",
        "spec_gate",
        "static_gate",
        "test_gate",
    ]


def test_run_smoke_gate_reports_missing_runtime_files(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        closeout_acceptance_gate,
        "run_command",
        lambda command, cwd: {
            "command": command,
            "returncode": 0,
            "stdout": "{}",
            "stderr": "",
            "passed": True,
        },
    )

    result = closeout_acceptance_gate.run_smoke_gate(tmp_path, sys.executable, "workflow-1")
    assert result["passed"] is False
    assert result["backfill_smoke"]["passed"] is True
    assert len(result["runtime_checks"]) == 2
    assert all(check["passed"] is False for check in result["runtime_checks"])
    assert all(check["missing"] is True for check in result["runtime_checks"])
