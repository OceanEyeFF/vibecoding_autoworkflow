from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from folder_logic_check import FolderRules, run_checks


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_executable(path: Path) -> None:
    path.chmod(path.stat().st_mode | 0o111)


def git(repo_root: Path, *args: str, force: bool = False) -> None:
    command = ["git", "-C", str(repo_root), *args]
    if force and "add" in args:
        command.insert(command.index("add") + 1, "-f")
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def create_nav_symlink(path: Path, target: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(target)


def create_valid_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path
    git(repo_root, "init")

    for root_file in ("README.md", "INDEX.md", "GUIDE.md", "ROADMAP.md", "AGENTS.md", "LICENSE", ".gitignore", ".claudeignore"):
        write_file(repo_root / root_file, root_file)

    for path in (
        repo_root / "product/README.md",
        repo_root / "docs/README.md",
        repo_root / "toolchain/README.md",
    ):
        write_file(path, path.name)

    for directory in (
        ".codex/rules",
        "product/memory-side/skills",
        "product/task-interface",
        "docs/project-maintenance",
        "docs/harness",
        "docs/deployable-skills",
        "docs/autoresearch",
        "toolchain/scripts",
        "toolchain/evals",
        "tools",
        ".serena/memories",
    ):
        (repo_root / directory).mkdir(parents=True, exist_ok=True)

    for tool_path in (
        "tools/closeout_acceptance_gate.py",
        "tools/gate_status_backfill.py",
        "tools/scope_gate_check.py",
    ):
        write_file(repo_root / tool_path, "# shim\n")

    write_file(repo_root / ".serena/.gitignore", ".serena/\n")
    write_file(repo_root / ".serena/project.yml", "project: demo\n")
    write_file(repo_root / ".serena/memories/Claude-Workspace-Architecture.md", "# memory\n")

    write_file(
        repo_root / ".codex/config.toml",
        "approval_policy = \"on-request\"\nsandbox_mode = \"workspace-write\"\npersonality = \"pragmatic\"\nmodel_reasoning_effort = \"high\"\nweb_search = \"cached\"\n\n[features]\nmulti_agent = true\n",
    )
    write_file(
        repo_root / ".codex/rules/repo.rules",
        "prefix_rule(\n    pattern = [\"git\", \"push\"],\n    decision = \"prompt\",\n    justification = \"Publishing repository changes must stay explicit in this repository.\",\n    match = [\"git push\", \"git push origin main\"],\n)\n",
    )

    (repo_root / ".nav").mkdir(parents=True, exist_ok=True)
    write_file(repo_root / ".nav/README.md", "# nav\n")
    create_nav_symlink(repo_root / ".nav/@docs", repo_root / "docs")
    create_nav_symlink(repo_root / ".nav/@skills", repo_root / "product/memory-side/skills")

    git(
        repo_root,
        "add",
        "AGENTS.md",
        "GUIDE.md",
        "INDEX.md",
        "LICENSE",
        "README.md",
        "ROADMAP.md",
        ".gitignore",
        ".claudeignore",
        force=True,
    )
    git(repo_root, "add", "product", "docs", "toolchain", "tools", ".serena", ".nav", ".codex", force=True)
    return repo_root


def issue_codes(report) -> set[str]:
    return {issue.code for issue in report.issues}


def issue_paths(report) -> set[str]:
    return {issue.path for issue in report.issues}


def test_valid_repo_passes(tmp_path: Path) -> None:
    repo_root = create_valid_repo(tmp_path)
    report = run_checks(repo_root)
    assert report.issues == []


def test_root_unknown_directory_fails(tmp_path: Path) -> None:
    repo_root = create_valid_repo(tmp_path)
    (repo_root / "scratch").mkdir()

    report = run_checks(repo_root)

    assert "FL001" in issue_codes(report)
    assert "scratch" in issue_paths(report)


def test_tools_must_be_declared_as_compat_shim(tmp_path: Path) -> None:
    repo_root = create_valid_repo(tmp_path)
    rules = FolderRules(root_allowed_names=set(FolderRules().root_allowed_names) - {"tools"})

    report = run_checks(repo_root, rules=rules)

    assert "FL001" in issue_codes(report)
    assert "tools" in issue_paths(report)


def test_pytest_cache_untracked_passes_but_tracked_fails(tmp_path: Path) -> None:
    repo_root = create_valid_repo(tmp_path)
    write_file(repo_root / ".pytest_cache/README.md", "cache\n")

    untracked_report = run_checks(repo_root)
    assert "FL013" not in issue_codes(untracked_report)

    git(repo_root, "add", ".pytest_cache/README.md", force=True)
    tracked_report = run_checks(repo_root)

    assert "FL013" in issue_codes(tracked_report)


def test_codex_layer_passes_when_config_and_rules_are_present(tmp_path: Path) -> None:
    repo_root = create_valid_repo(tmp_path)

    report = run_checks(repo_root)

    assert "FL015" not in issue_codes(report)
    assert "FL016" not in issue_codes(report)


def test_codex_unknown_entry_fails(tmp_path: Path) -> None:
    repo_root = create_valid_repo(tmp_path)
    write_file(repo_root / ".codex/cache.json", "{}\n")

    report = run_checks(repo_root)

    assert "FL015" in issue_codes(report)
    assert ".codex/cache.json" in issue_paths(report)


def test_codex_tracked_non_whitelist_fails(tmp_path: Path) -> None:
    repo_root = create_valid_repo(tmp_path)
    write_file(repo_root / ".codex/notes.md", "# notes\n")
    git(repo_root, "add", ".codex/notes.md", force=True)

    report = run_checks(repo_root)

    assert "FL016" in issue_codes(report)
    assert ".codex/notes.md" in issue_paths(report)


def test_serena_whitelist_passes_and_non_whitelist_tracked_fails(tmp_path: Path) -> None:
    repo_root = create_valid_repo(tmp_path)
    baseline_report = run_checks(repo_root)
    assert "FL008" not in issue_codes(baseline_report)

    write_file(repo_root / ".serena/cache/runtime.json", "{}\n")
    git(repo_root, "add", ".serena/cache/runtime.json", force=True)
    report = run_checks(repo_root)

    assert "FL008" in issue_codes(report)
    assert ".serena/cache/runtime.json" in issue_paths(report)


def test_first_level_allowlist_drift_fails(tmp_path: Path) -> None:
    repo_root = create_valid_repo(tmp_path)
    (repo_root / "toolchain/misc").mkdir()

    report = run_checks(repo_root)

    assert "FL003" in issue_codes(report)
    assert "toolchain/misc" in issue_paths(report)


def test_harness_partition_is_allowed_under_product_and_docs(tmp_path: Path) -> None:
    repo_root = create_valid_repo(tmp_path)
    (repo_root / "docs/harness").mkdir(parents=True, exist_ok=True)

    report = run_checks(repo_root)

    assert "docs/harness" not in issue_paths(report)


def test_misplaced_content_patterns_fail(tmp_path: Path) -> None:
    repo_root = create_valid_repo(tmp_path)
    write_file(repo_root / "product/runbook.md", "# runbook\n")
    write_file(repo_root / "docs/helper.py", "print('no')\n")
    write_file(repo_root / "toolchain/logs/output.log", "bad\n")

    report = run_checks(repo_root)

    assert {"FL004", "FL005", "FL006"} <= issue_codes(report)


def test_nav_extra_entry_fails(tmp_path: Path) -> None:
    repo_root = create_valid_repo(tmp_path)
    write_file(repo_root / ".nav/@tmp", "bad\n")
    git(repo_root, "add", ".nav/@tmp", force=True)

    report = run_checks(repo_root)

    assert "FL010" in issue_codes(report)
    assert ".nav/@tmp" in issue_paths(report)


def test_nav_required_slots_must_be_symlinks(tmp_path: Path) -> None:
    repo_root = create_valid_repo(tmp_path)
    (repo_root / ".nav/@docs").unlink()
    write_file(repo_root / ".nav/@docs", "not a symlink\n")

    report = run_checks(repo_root)

    assert "FL011" in issue_codes(report)
    assert ".nav/@docs" in issue_paths(report)


def test_nav_symlink_target_must_be_allowed(tmp_path: Path) -> None:
    repo_root = create_valid_repo(tmp_path)
    (repo_root / ".nav/@skills").unlink()
    create_nav_symlink(repo_root / ".nav/@skills", repo_root / "product/task-interface")

    report = run_checks(repo_root)

    assert "FL012" in issue_codes(report)
    assert ".nav/@skills" in issue_paths(report)


def test_docs_executable_file_fails(tmp_path: Path) -> None:
    repo_root = create_valid_repo(tmp_path)
    path = repo_root / "docs/project-maintenance/run.sh"
    write_file(path, "#!/bin/sh\nexit 0\n")
    make_executable(path)

    report = run_checks(repo_root)

    assert "FL005" in issue_codes(report)
