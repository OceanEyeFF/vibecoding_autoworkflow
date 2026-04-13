from __future__ import annotations

import subprocess
from pathlib import Path

from harness_scope_gate import (
    check_scope,
    collect_changed_files_from_commit,
    parse_runtime_task_source_ref,
    parse_scope_prefixes,
    resolve_diff_input,
)


def write_harness(path: Path, *, task_source_ref: str = "pending") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            "version: 1\n"
            "contract:\n"
            "  scope:\n"
            "    include:\n"
            "      - product/\n"
            "      - docs/\n"
            "      - toolchain/\n"
            "    exclude:\n"
            "      - .agents/\n"
            "      - .autoworkflow/\n"
            "runtime:\n"
            f"  task_source_ref: {task_source_ref}\n"
        ),
        encoding="utf-8",
    )


def run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def init_repo(repo_root: Path) -> None:
    run_git(repo_root, "init")
    run_git(repo_root, "config", "user.email", "tester@example.com")
    run_git(repo_root, "config", "user.name", "tester")


def write_file(repo_root: Path, relative: str, content: str) -> None:
    path = repo_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_parse_scope_prefixes_from_harness_yaml(tmp_path: Path) -> None:
    harness_file = tmp_path / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file)

    includes, excludes = parse_scope_prefixes(harness_file)

    assert includes == ["product/", "docs/", "toolchain/"]
    assert excludes == [".agents/", ".autoworkflow/"]


def test_parse_runtime_task_source_ref(tmp_path: Path) -> None:
    harness_file = tmp_path / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref="HEAD^..HEAD")

    task_source_ref = parse_runtime_task_source_ref(harness_file)

    assert task_source_ref == "HEAD^..HEAD"


def test_parse_runtime_task_source_ref_preserves_hash_in_quoted_value(tmp_path: Path) -> None:
    harness_file = tmp_path / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref='"PR #123"')

    task_source_ref = parse_runtime_task_source_ref(harness_file)

    assert task_source_ref == "PR #123"


def test_check_scope_accepts_included_changes() -> None:
    result = check_scope(
        changed_files=["product/harness-operations/skills/review-loop-workflow/prompt.md"],
        include_prefixes=["product/", "docs/", "toolchain/"],
        exclude_prefixes=[".agents/", ".autoworkflow/"],
    )

    assert result.passed is True
    assert result.violations == []


def test_check_scope_ignores_excluded_runtime_paths() -> None:
    result = check_scope(
        changed_files=[
            ".agents/skills/review-loop-workflow/SKILL.md",
            ".autoworkflow/build/adapter-sources/agents/review-loop-workflow/SKILL.md",
        ],
        include_prefixes=["product/", "docs/", "toolchain/"],
        exclude_prefixes=[".agents/", ".autoworkflow/"],
    )

    assert result.passed is True
    assert result.violations == []


def test_check_scope_flags_out_of_scope_changes() -> None:
    result = check_scope(
        changed_files=["README.md", "product/harness-operations/README.md"],
        include_prefixes=["product/", "docs/", "toolchain/"],
        exclude_prefixes=[".agents/", ".autoworkflow/"],
    )

    assert result.passed is False
    assert result.violations == ["README.md"]


def test_resolve_diff_input_uses_runtime_commit_on_clean_tree(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    write_file(repo_root, "product/harness-operations/README.md", "init\n")
    run_git(repo_root, "add", "product/harness-operations/README.md")
    run_git(repo_root, "commit", "-m", "init")

    write_file(repo_root, "README.md", "out of scope\n")
    run_git(repo_root, "add", "README.md")
    run_git(repo_root, "commit", "-m", "touch readme")
    commit_ref = run_git(repo_root, "rev-parse", "HEAD")

    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref=commit_ref)
    run_git(repo_root, "add", ".autoworkflow/harness.yaml")
    run_git(repo_root, "commit", "-m", "add harness config")

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
    )

    assert "README.md" in diff_input.changed_files
    assert diff_input.source in {"task-commit", "task-embedded-commit"}


def test_resolve_diff_input_prefers_runtime_ref_over_worktree_noise(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    write_file(repo_root, "product/harness-operations/README.md", "init\n")
    run_git(repo_root, "add", "product/harness-operations/README.md")
    run_git(repo_root, "commit", "-m", "init")
    commit_ref = run_git(repo_root, "rev-parse", "HEAD")

    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref=commit_ref)

    write_file(repo_root, ".autoworkflow/runtime/state.json", '{"status":"dirty"}\n')

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
    )

    assert diff_input.changed_files == ["product/harness-operations/README.md"]
    assert diff_input.source == "task-commit"


def test_collect_changed_files_from_commit_includes_merge_commit_paths(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    write_file(repo_root, "product/harness-operations/README.md", "init\n")
    run_git(repo_root, "add", "product/harness-operations/README.md")
    run_git(repo_root, "commit", "-m", "init")
    main_branch = run_git(repo_root, "branch", "--show-current")

    run_git(repo_root, "checkout", "-b", "feature")
    write_file(repo_root, "README.md", "merged change\n")
    run_git(repo_root, "add", "README.md")
    run_git(repo_root, "commit", "-m", "feature change")

    run_git(repo_root, "checkout", main_branch)
    run_git(repo_root, "merge", "--no-ff", "feature", "-m", "merge feature")
    merge_commit = run_git(repo_root, "rev-parse", "HEAD")

    changed_files = collect_changed_files_from_commit(repo_root, merge_commit)

    assert "README.md" in changed_files


def test_resolve_diff_input_uses_merge_commit_task_source_ref(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    write_file(repo_root, "product/harness-operations/README.md", "init\n")
    run_git(repo_root, "add", "product/harness-operations/README.md")
    run_git(repo_root, "commit", "-m", "init")
    main_branch = run_git(repo_root, "branch", "--show-current")

    run_git(repo_root, "checkout", "-b", "feature")
    write_file(repo_root, "README.md", "merged change\n")
    run_git(repo_root, "add", "README.md")
    run_git(repo_root, "commit", "-m", "feature change")

    run_git(repo_root, "checkout", main_branch)
    run_git(repo_root, "merge", "--no-ff", "feature", "-m", "merge feature")
    merge_commit = run_git(repo_root, "rev-parse", "HEAD")

    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref=merge_commit)
    run_git(repo_root, "add", ".autoworkflow/harness.yaml")
    run_git(repo_root, "commit", "-m", "add harness config")

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
    )

    assert "README.md" in diff_input.changed_files
    assert diff_input.source == "task-commit"


def test_resolve_diff_input_normalizes_absolute_repo_path_task_ref(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    write_file(repo_root, "product/harness-operations/README.md", "init\n")
    run_git(repo_root, "add", "product/harness-operations/README.md")
    run_git(repo_root, "commit", "-m", "init")

    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    absolute_target = (repo_root / "product" / "harness-operations" / "README.md").resolve()
    write_harness(harness_file, task_source_ref=str(absolute_target))
    run_git(repo_root, "add", ".autoworkflow/harness.yaml")
    run_git(repo_root, "commit", "-m", "add harness config")

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
    )

    assert diff_input.changed_files == ["product/harness-operations/README.md"]
    assert diff_input.source == "task-target-path"
