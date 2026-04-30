from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


FAKE_FAILING_PYTHON_EXIT_CODE = 97


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


@pytest.fixture
def node_path() -> str:
    resolved = shutil.which("node")
    if resolved is None:
        pytest.skip("node is not available")
    return resolved


def run_aw_installer(
    repo_root: Path,
    node_path: str,
    target_repo: Path,
    *args: str,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    target_repo.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        "AW_HARNESS_REPO_ROOT": str(repo_root),
        "AW_HARNESS_TARGET_REPO_ROOT": str(target_repo),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if env_overrides is not None:
        env.update(env_overrides)
    return subprocess.run(
        [
            node_path,
            str(repo_root / "toolchain" / "scripts" / "deploy" / "bin" / "aw-installer.js"),
            *args,
        ],
        cwd=target_repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def assert_success(completed: subprocess.CompletedProcess[str]) -> None:
    assert completed.returncode == 0, completed.stderr


def assert_json_payload(completed: subprocess.CompletedProcess[str]) -> dict[str, object]:
    assert_success(completed)
    assert completed.stderr == ""
    return json.loads(completed.stdout)


def test_cli_help_version_and_noninteractive_default(
    repo_root: Path,
    node_path: str,
    tmp_path: Path,
) -> None:
    target_repo = tmp_path / "target"

    for args in [(), ("--help",), ("-h",)]:
        completed = run_aw_installer(repo_root, node_path, target_repo, *args)
        assert_success(completed)
        assert "usage: aw-installer" in completed.stdout
        for command_name in [
            "tui",
            "diagnose",
            "verify",
            "install",
            "update",
            "prune",
            "check_paths_exist",
        ]:
            assert command_name in completed.stdout
        assert completed.stderr == ""

    for args in [("--version",), ("-V",)]:
        completed = run_aw_installer(repo_root, node_path, target_repo, *args)
        assert_success(completed)
        assert completed.stdout.startswith("aw-installer ")
        assert completed.stderr == ""


def test_cli_agents_command_lifecycle(repo_root: Path, node_path: str, tmp_path: Path) -> None:
    target_repo = tmp_path / "agents-target"
    target_root = target_repo / ".agents" / "skills"
    installed_skill = target_root / "aw-harness-skill" / "SKILL.md"

    diagnose = assert_json_payload(
        run_aw_installer(repo_root, node_path, target_repo, "diagnose", "--backend", "agents", "--json")
    )
    assert diagnose["backend"] == "agents"
    assert diagnose["target_root_status"] == "missing"

    update_json = assert_json_payload(
        run_aw_installer(repo_root, node_path, target_repo, "update", "--backend", "agents", "--json")
    )
    assert update_json["backend"] == "agents"
    assert update_json["operation_sequence"] == [
        "prune --all",
        "check_paths_exist",
        "install",
        "verify",
    ]
    assert update_json["blocking_issue_count"] == 0
    assert update_json["planned_target_paths"]

    update_dry_run = run_aw_installer(repo_root, node_path, target_repo, "update", "--backend", "agents")
    assert_success(update_dry_run)
    assert "[agents] update plan" in update_dry_run.stdout
    assert "dry-run only; pass --yes to apply update" in update_dry_run.stdout
    assert not target_root.exists()

    check_paths = run_aw_installer(repo_root, node_path, target_repo, "check_paths_exist", "--backend", "agents")
    assert_success(check_paths)
    assert "[agents] ok: no conflicting target paths" in check_paths.stdout

    prune_empty = run_aw_installer(repo_root, node_path, target_repo, "prune", "--all", "--backend", "agents")
    assert_success(prune_empty)
    assert "no managed skill dirs found" in prune_empty.stdout

    install = run_aw_installer(repo_root, node_path, target_repo, "install", "--backend", "agents")
    assert_success(install)
    assert "installed skill harness-skill" in install.stdout
    assert installed_skill.is_file()

    verify = run_aw_installer(repo_root, node_path, target_repo, "verify", "--backend", "agents")
    assert_success(verify)
    assert "[agents] ok" in verify.stdout

    update_apply = run_aw_installer(repo_root, node_path, target_repo, "update", "--backend", "agents", "--yes")
    assert_success(update_apply)
    assert "[agents] applying update" in update_apply.stdout
    assert "[agents] ok" in update_apply.stdout
    assert "[agents] update complete" in update_apply.stdout
    assert installed_skill.is_file()


def test_cli_claude_command_lifecycle(repo_root: Path, node_path: str, tmp_path: Path) -> None:
    target_repo = tmp_path / "claude-target"
    target_root = target_repo / ".claude" / "skills"
    installed_skill = target_root / "aw-set-harness-goal-skill" / "SKILL.md"

    diagnose = assert_json_payload(
        run_aw_installer(repo_root, node_path, target_repo, "diagnose", "--backend", "claude", "--json")
    )
    assert diagnose["backend"] == "claude"
    assert diagnose["target_root_status"] == "missing"

    update_json = assert_json_payload(
        run_aw_installer(repo_root, node_path, target_repo, "update", "--backend", "claude", "--json")
    )
    assert update_json["backend"] == "claude"
    assert update_json["blocking_issue_count"] == 0
    assert update_json["planned_target_paths"] == [str(target_root / "aw-set-harness-goal-skill")]

    update_dry_run = run_aw_installer(repo_root, node_path, target_repo, "update", "--backend", "claude")
    assert_success(update_dry_run)
    assert "[claude] update plan" in update_dry_run.stdout

    check_paths = run_aw_installer(repo_root, node_path, target_repo, "check_paths_exist", "--backend", "claude")
    assert_success(check_paths)
    assert "[claude] ok: no conflicting target paths" in check_paths.stdout

    prune_empty = run_aw_installer(repo_root, node_path, target_repo, "prune", "--all", "--backend", "claude")
    assert_success(prune_empty)
    assert "no managed skill dirs found" in prune_empty.stdout

    install = run_aw_installer(repo_root, node_path, target_repo, "install", "--backend", "claude")
    assert_success(install)
    assert "installed skill set-harness-goal-skill" in install.stdout
    assert installed_skill.is_file()

    verify = run_aw_installer(repo_root, node_path, target_repo, "verify", "--backend", "claude")
    assert_success(verify)
    assert "[claude] ok" in verify.stdout

    update_apply = run_aw_installer(repo_root, node_path, target_repo, "update", "--backend", "claude", "--yes")
    assert_success(update_apply)
    assert "[claude] applying update" in update_apply.stdout
    assert "[claude] ok" in update_apply.stdout
    assert "[claude] update complete" in update_apply.stdout
    assert installed_skill.is_file()


def test_cli_update_github_source_stays_on_python_fallback(
    repo_root: Path,
    node_path: str,
    tmp_path: Path,
) -> None:
    fake_bin = tmp_path / "fake-python-bin"
    fake_bin.mkdir()
    fake_python = fake_bin / "python3"
    fake_python.write_text(
        "#!/bin/sh\n"
        "printf 'unexpected-python %s\\n' \"$*\" >&2\n"
        f"exit {FAKE_FAILING_PYTHON_EXIT_CODE}\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)

    completed = run_aw_installer(
        repo_root,
        node_path,
        tmp_path / "github-source-target",
        "update",
        "--backend",
        "agents",
        "--source",
        "github",
        "--github-ref",
        "master",
        "--json",
        env_overrides={"PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}"},
    )

    assert completed.returncode == FAKE_FAILING_PYTHON_EXIT_CODE
    assert completed.stdout == ""
    assert "unexpected-python" in completed.stderr
    assert "harness_deploy.py" in completed.stderr


def test_cli_tui_requires_interactive_terminal(repo_root: Path, node_path: str, tmp_path: Path) -> None:
    completed = run_aw_installer(repo_root, node_path, tmp_path / "noninteractive-tui", "tui")

    assert completed.returncode == 1
    assert completed.stdout == ""
    assert "aw-installer tui requires an interactive terminal" in completed.stderr
