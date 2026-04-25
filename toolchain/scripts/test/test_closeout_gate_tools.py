from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import closeout_acceptance_gate
from scope_gate_check import check_scope, normalize_status_path
from gate_status_backfill import update_state


def test_check_scope_accepts_allowed_prefixes() -> None:
    result = check_scope(
        [
            "AGENTS.md",
            "CONTRIBUTING.md",
            ".codex/config.toml",
            ".github/workflows/ci.yml",
            "docs/README.md",
            "docs/harness/README.md",
            "docs/project-maintenance/README.md",
            "product/README.md",
            "docs/project-maintenance/governance/review-verify-handbook.md",
            "docs/project-maintenance/governance/path-governance-checks.md",
            ".autoworkflow/closeout/demo/summary.json",
            "toolchain/scripts/test/scope_gate_check.py",
            "tools/scope_gate_check.py",
        ],
        (
            "AGENTS.md",
            "CONTRIBUTING.md",
            ".codex/",
            ".github/",
            "docs/README.md",
            ".autoworkflow/closeout/",
            "docs/project-maintenance/",
            "docs/harness/",
            "product/README.md",
            "toolchain/scripts/test/",
            "tools/scope_gate_check.py",
        ),
    )
    assert result.passed is True
    assert result.violations == []


def test_check_scope_accepts_closeout_prefix() -> None:
    result = check_scope(
        ["docs/project-maintenance/governance/review-verify-handbook.md"],
        ("docs/project-maintenance/governance/",),
    )
    assert result.passed is True
    assert result.violations == []


def test_check_scope_flags_disallowed_changes() -> None:
    result = check_scope(["GUIDE.md"], ("docs/project-maintenance/",))
    assert result.passed is False
    assert result.violations == ["GUIDE.md"]


def test_normalize_status_path_decodes_git_quoted_utf8_path() -> None:
    quoted = '"docs/harness/foundations/Harness\\350\\277\\220\\350\\241\\214\\345\\215\\217\\350\\256\\256.md"'

    assert normalize_status_path(quoted) == "docs/harness/foundations/Harness运行协议.md"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_pre_push_blocks_origin_head_baseline(tmp_path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    hook_path = repo_root / "toolchain" / "scripts" / "git-hooks" / "pre-push"
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "symbolic-ref",
            "refs/remotes/origin/HEAD",
            "refs/remotes/origin/master",
        ],
        cwd=tmp_path,
        check=True,
    )

    completed = subprocess.run(
        ["bash", str(hook_path)],
        cwd=tmp_path,
        input=(
            "refs/heads/master 0000000000000000000000000000000000000000 "
            "refs/heads/master 0000000000000000000000000000000000000000\n"
        ),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert "direct push to protected baseline 'master' is blocked" in completed.stderr


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_pre_push_allows_non_baseline_branch(tmp_path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    hook_path = repo_root / "toolchain" / "scripts" / "git-hooks" / "pre-push"
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "symbolic-ref",
            "refs/remotes/origin/HEAD",
            "refs/remotes/origin/master",
        ],
        cwd=tmp_path,
        check=True,
    )

    completed = subprocess.run(
        ["bash", str(hook_path)],
        cwd=tmp_path,
        input=(
            "refs/heads/work/test 0000000000000000000000000000000000000000 "
            "refs/heads/work/test 0000000000000000000000000000000000000000\n"
        ),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stderr == ""


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_pre_push_fallback_blocks_main_when_origin_head_unresolved(tmp_path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    hook_path = repo_root / "toolchain" / "scripts" / "git-hooks" / "pre-push"
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)

    completed = subprocess.run(
        ["bash", str(hook_path)],
        cwd=tmp_path,
        input=(
            "refs/heads/main 0000000000000000000000000000000000000000 "
            "refs/heads/main 0000000000000000000000000000000000000000\n"
        ),
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert "fallback protects main/master" in completed.stderr


def test_update_state_backfills_gate_status() -> None:
    state = {"gates": {"scope_gate": "pending"}}
    updated = update_state(state, "scope_gate", "passed", {"returncode": 0}, "workflow-1")
    assert updated["workflow_id"] == "workflow-1"
    assert updated["gates"]["scope_gate"] == "passed"
    assert updated["last_backfill"]["gate"] == "scope_gate"


def test_update_state_allows_skipped_gate_status() -> None:
    state = {"gates": {"scope_gate": "pending"}}
    updated = update_state(
        state,
        "test_gate",
        "skipped",
        {"returncode": 0, "skip_reasons": ["missing local deploy target root"]},
        "workflow-1",
    )
    assert updated["gates"]["test_gate"] == "skipped"
    assert updated["last_backfill"]["status"] == "skipped"


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
    assert "AGENTS.md" in command
    assert "CONTRIBUTING.md" in command
    assert "docs/README.md" in command
    assert ".codex/" in command
    assert ".github/" in command
    assert "docs/project-maintenance/README.md" in command
    assert "docs/harness/" in command
    assert "product/README.md" in command
    assert "docs/project-maintenance/foundations/root-directory-layering.md" in command
    assert "toolchain/toolchain-layering.md" in command
    assert "docs/project-maintenance/governance/review-verify-handbook.md" in command


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
    assert any("docs/harness" in command for command in commands)


def test_run_test_gate_includes_agents_adapter_contract_tests(monkeypatch, tmp_path) -> None:
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
    assert [item["name"] for item in result["subchecks"][:3]] == [
        "gate_tool_tests",
        "folder_logic_tests",
        "agents_adapter_contract_tests",
    ]
    assert any(command[-1] == "toolchain/scripts/test/test_folder_logic_check.py" for command in commands)
    assert any(command[-1] == "toolchain/scripts/test/test_agents_adapter_contract.py" for command in commands)
    deploy_verify_commands = [command for command in commands if "adapter_deploy.py" in command[1]]
    assert len(deploy_verify_commands) == 1
    assert deploy_verify_commands[0][-2:] == ["--backend", "agents"]
    assert "--target" not in deploy_verify_commands[0]


def test_run_test_gate_skips_missing_local_deploy_targets(monkeypatch, tmp_path) -> None:
    commands: list[list[str]] = []

    def fake_run_command(command: list[str], *, cwd: Path) -> dict:
        commands.append(command)
        if "adapter_deploy.py" in command[1]:
            return {
                "command": command,
                "returncode": 1,
                "stdout": (
                    "[agents] drift: 1 issue(s) in local target at /tmp/demo\n"
                    "  - missing-target-root: /tmp/demo (.agents target root does not exist)\n"
                ),
                "stderr": "",
                "passed": False,
            }
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
    assert result["status"] == "skipped"
    deploy_results = {
        item["name"]: item for item in result["subchecks"] if item["name"].startswith("deploy_verify_")
    }
    assert set(deploy_results) == {"deploy_verify_agents"}
    assert all(item["passed"] is True for item in deploy_results.values())
    assert all(item["skipped"] is True for item in deploy_results.values())
    assert any("adapter_deploy.py" in command[1] for command in commands)


def test_run_test_gate_checks_broken_local_deploy_target_symlink(monkeypatch, tmp_path) -> None:
    commands: list[list[str]] = []
    broken_root = tmp_path / ".agents" / "skills"
    broken_root.parent.mkdir(parents=True)
    broken_root.symlink_to(tmp_path / "missing-agents-skills")

    def fake_run_command(command: list[str], *, cwd: Path) -> dict:
        commands.append(command)
        if "adapter_deploy.py" in command[1]:
            return {
                "command": command,
                "returncode": 1,
                "stdout": "broken-target-root-symlink\n",
                "stderr": "",
                "passed": False,
            }
        return {
            "command": command,
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "passed": True,
        }

    monkeypatch.setattr(closeout_acceptance_gate, "run_command", fake_run_command)

    result = closeout_acceptance_gate.run_test_gate(tmp_path, sys.executable)

    assert result["passed"] is False
    assert result["status"] == "failed"
    assert any("adapter_deploy.py" in command[1] for command in commands)


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


def test_run_smoke_gate_skips_missing_runtime_root(monkeypatch, tmp_path) -> None:
    primary_root = tmp_path / "primary"
    runtime_dir = (
        primary_root
        / ".autoworkflow"
        / "closeout"
        / "manual-governance-loop-3round-r000001-m000642"
    )
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "runtime.json").write_text('{"active_round": null}', encoding="utf-8")
    other_runtime_dir = (
        primary_root
        / ".autoworkflow"
        / "closeout"
        / "manual-governance-loop-6-3-3-r000001-m046830"
    )
    other_runtime_dir.mkdir(parents=True)
    (other_runtime_dir / "runtime.json").write_text('{"active_round": null}', encoding="utf-8")
    monkeypatch.setattr(closeout_acceptance_gate, "find_primary_worktree_root", lambda repo_root: primary_root)
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
    assert result["passed"] is True
    assert result["status"] == "passed"
    assert result["backfill_smoke"]["passed"] is True
    assert len(result["runtime_checks"]) == 2
    assert all(check["passed"] is True for check in result["runtime_checks"])
    assert all(check["checked_from"] == str(primary_root) for check in result["runtime_checks"])


def test_run_smoke_gate_fails_when_runtime_root_exists_but_retained_files_are_missing(monkeypatch, tmp_path) -> None:
    (
        tmp_path
        / ".autoworkflow"
        / "closeout"
        / "manual-governance-loop-3round-r000001-m000642"
    ).mkdir(parents=True)
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


def test_run_smoke_gate_skips_when_only_unrelated_runtime_artifacts_exist(monkeypatch, tmp_path) -> None:
    primary_root = tmp_path / "primary"
    (primary_root / ".autoworkflow" / "closeout" / "some-other-run").mkdir(parents=True)
    monkeypatch.setattr(closeout_acceptance_gate, "find_primary_worktree_root", lambda repo_root: primary_root)
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
    assert result["passed"] is True
    assert result["status"] == "skipped"
    assert len(result["runtime_checks"]) == 1
    assert result["runtime_checks"][0]["skipped"] is True


def test_closeout_gate_backfills_skipped_status(monkeypatch, tmp_path, capsys) -> None:
    class Args:
        repo_root = tmp_path
        workflow_id = "workflow-1"
        json = True

    backfill_commands: list[list[str]] = []

    def fake_run_gate(gate: str, *, repo_root: Path, python: str, workflow_id: str) -> dict:
        if gate == "scope_gate":
            return {"passed": True, "returncode": 0}
        if gate == "spec_gate":
            return {"passed": True, "returncode": 0}
        if gate == "static_gate":
            return {"passed": True, "returncode": 0}
        if gate == "test_gate":
            return {
                "passed": True,
                "returncode": 0,
                "status": "skipped",
                "subchecks": [
                    {
                        "name": "deploy_verify_agents",
                        "passed": True,
                        "skipped": True,
                        "skip_reason": "missing local deploy target root /tmp/demo",
                    }
                ],
            }
        return {"passed": True, "returncode": 0}

    def fake_subprocess_run(*args, **kwargs) -> subprocess.CompletedProcess[str]:
        command = args[0]
        backfill_commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")

    monkeypatch.setattr(closeout_acceptance_gate, "parse_args", lambda: Args())
    monkeypatch.setattr(closeout_acceptance_gate, "run_gate", fake_run_gate)
    monkeypatch.setattr(closeout_acceptance_gate.subprocess, "run", fake_subprocess_run)

    assert closeout_acceptance_gate.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True
    test_gate_backfill = next(command for command in backfill_commands if "--gate" in command and command[command.index("--gate") + 1] == "test_gate")
    assert test_gate_backfill[test_gate_backfill.index("--status") + 1] == "skipped"
    details = json.loads(test_gate_backfill[test_gate_backfill.index("--details") + 1])
    assert "skip_reasons" in details


def test_find_primary_worktree_root_prefers_non_nested_worktree(monkeypatch, tmp_path) -> None:
    current_root = tmp_path / ".worktrees" / "topic"
    current_root.mkdir(parents=True)
    primary_root = tmp_path / "repo"
    primary_root.mkdir()

    def fake_run(*args, **kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args[0],
            0,
            stdout=(
                f"worktree {primary_root}\n"
                "HEAD abcdef\n"
                "branch refs/heads/develop-main\n"
                f"worktree {current_root}\n"
                "HEAD 123456\n"
                "branch refs/heads/topic\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(closeout_acceptance_gate.subprocess, "run", fake_run)

    assert closeout_acceptance_gate.find_primary_worktree_root(current_root.resolve()) == primary_root.resolve()
