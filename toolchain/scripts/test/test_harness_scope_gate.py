from __future__ import annotations

import json
import subprocess
from pathlib import Path

from harness_scope_gate import (
    check_scope,
    collect_changed_files_from_commit,
    parse_runtime_task_source_ref,
    parse_scope_prefixes,
    resolve_diff_input,
)


INCLUDE_PREFIXES = ["product/", "docs/", "toolchain/"]
EXCLUDE_PREFIXES = [".agents/", ".autoworkflow/", ".claude/", ".spec-workflow/"]
SCRIPT_PATH = Path(__file__).resolve().with_name("harness_scope_gate.py")


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
            "      - .claude/\n"
            "      - .spec-workflow/\n"
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


def run_git_global(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
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


def commit_file(repo_root: Path, relative: str, content: str, message: str) -> str:
    write_file(repo_root, relative, content)
    run_git(repo_root, "add", relative)
    run_git(repo_root, "commit", "-m", message)
    return run_git(repo_root, "rev-parse", "HEAD")


def commit_harness(repo_root: Path, harness_file: Path) -> None:
    run_git(repo_root, "add", str(harness_file.relative_to(repo_root)))
    run_git(repo_root, "commit", "-m", "add harness config")


def run_scope_gate(repo_root: Path, harness_file: Path) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    return run_scope_gate_with_args(repo_root, harness_file)


def run_scope_gate_with_args(
    repo_root: Path,
    harness_file: Path,
    *extra_args: str,
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    completed = subprocess.run(
        [
            "python3",
            str(SCRIPT_PATH),
            "--repo-root",
            str(repo_root),
            "--harness-file",
            str(harness_file),
            "--json",
            *extra_args,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed, json.loads(completed.stdout)


def test_parse_scope_prefixes_from_harness_yaml(tmp_path: Path) -> None:
    harness_file = tmp_path / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file)

    includes, excludes = parse_scope_prefixes(harness_file)

    assert includes == INCLUDE_PREFIXES
    assert excludes == EXCLUDE_PREFIXES


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
        changed_files=["product/harness/skills/harness-skill/SKILL.md"],
        include_prefixes=INCLUDE_PREFIXES,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert result.passed is True
    assert result.effective_changed_files == ["product/harness/skills/harness-skill/SKILL.md"]
    assert result.violations == []


def test_check_scope_ignores_excluded_runtime_paths() -> None:
    result = check_scope(
        changed_files=[
            ".agents/skills/task-contract-skill/SKILL.md",
            ".autoworkflow/runtime/state.json",
        ],
        include_prefixes=INCLUDE_PREFIXES,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert result.passed is True
    assert result.effective_changed_files == []
    assert result.violations == []


def test_check_scope_keeps_git_infra_paths_in_effective_changes() -> None:
    result = check_scope(
        changed_files=[".github/workflows/review.yml", ".gitignore", ".gitattributes"],
        include_prefixes=INCLUDE_PREFIXES,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert result.passed is False
    assert result.effective_changed_files == [".github/workflows/review.yml", ".gitignore", ".gitattributes"]
    assert result.ignored_files == []
    assert result.violations == [".github/workflows/review.yml", ".gitignore", ".gitattributes"]


def test_check_scope_flags_out_of_scope_changes() -> None:
    result = check_scope(
        changed_files=["README.md", "product/harness/README.md"],
        include_prefixes=INCLUDE_PREFIXES,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert result.passed is False
    assert result.violations == ["README.md"]


def test_resolve_diff_input_uses_runtime_commit_on_clean_tree(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_file(repo_root, "product/harness/README.md", "init\n", "init")
    commit_ref = commit_file(repo_root, "README.md", "out of scope\n", "touch readme")

    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref=commit_ref)
    commit_harness(repo_root, harness_file)

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert "README.md" in diff_input.changed_files
    assert diff_input.source in {"task-commit", "task-embedded-commit"}
    assert diff_input.error is None


def test_collect_changed_files_from_commit_includes_merge_commit_paths(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_file(repo_root, "product/harness/README.md", "init\n", "init")
    main_branch = run_git(repo_root, "branch", "--show-current")

    run_git(repo_root, "checkout", "-b", "feature")
    commit_file(repo_root, "README.md", "merged change\n", "feature change")

    run_git(repo_root, "checkout", main_branch)
    run_git(repo_root, "merge", "--no-ff", "feature", "-m", "merge feature")
    merge_commit = run_git(repo_root, "rev-parse", "HEAD")

    changed_files = collect_changed_files_from_commit(repo_root, merge_commit)

    assert "README.md" in changed_files


def test_resolve_diff_input_uses_merge_commit_task_source_ref(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_file(repo_root, "product/harness/README.md", "init\n", "init")
    main_branch = run_git(repo_root, "branch", "--show-current")

    run_git(repo_root, "checkout", "-b", "feature")
    commit_file(repo_root, "README.md", "merged change\n", "feature change")

    run_git(repo_root, "checkout", main_branch)
    run_git(repo_root, "merge", "--no-ff", "feature", "-m", "merge feature")
    merge_commit = run_git(repo_root, "rev-parse", "HEAD")

    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref=merge_commit)
    commit_harness(repo_root, harness_file)

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert "README.md" in diff_input.changed_files
    assert diff_input.source == "task-commit"
    assert diff_input.error is None


def test_resolve_diff_input_cli_task_source_ref_overrides_runtime_task_source_ref(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    runtime_commit = commit_file(repo_root, "README.md", "runtime source\n", "runtime source")
    cli_commit = commit_file(repo_root, "product/harness/README.md", "cli source\n", "cli source")

    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref=runtime_commit)
    commit_harness(repo_root, harness_file)

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=cli_commit,
        diff_range=None,
        commit_ref=None,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert diff_input.task_source_ref == cli_commit
    assert diff_input.changed_files == ["product/harness/README.md"]


def test_resolve_diff_input_unresolved_task_source_ref_fails_without_fallback(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_file(repo_root, "product/harness/README.md", "init\n", "init")
    commit_file(repo_root, "docs/guide.md", "doc\n", "doc change")

    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref="pending")
    commit_harness(repo_root, harness_file)

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref="missing-ref",
        diff_range=None,
        commit_ref=None,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert diff_input.source == "unresolved-task-source-ref"
    assert diff_input.error == "unresolved-task-source-ref"
    assert diff_input.changed_files == []


def test_resolve_diff_input_reports_live_worktree_conflict_for_extra_non_excluded_changes(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_ref = commit_file(repo_root, "product/harness/README.md", "init\n", "init")
    commit_file(repo_root, "docs/guide.md", "stable\n", "add docs")

    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref=commit_ref)
    commit_harness(repo_root, harness_file)

    write_file(repo_root, "docs/guide.md", "dirty\n")

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert diff_input.error == "live-worktree-conflict"
    assert diff_input.conflict_files == ["docs/guide.md"]
    assert diff_input.changed_files == ["product/harness/README.md"]


def test_resolve_diff_input_reports_live_worktree_conflict_for_same_path_drift_on_fixed_source(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_file(repo_root, "product/harness/README.md", "init\n", "init")
    commit_ref = commit_file(repo_root, "docs/guide.md", "stable\n", "add docs")

    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref=commit_ref)
    commit_harness(repo_root, harness_file)

    write_file(repo_root, "docs/guide.md", "dirty\n")

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert diff_input.source == "task-commit"
    assert diff_input.changed_files == ["docs/guide.md"]
    assert diff_input.error == "live-worktree-conflict"
    assert diff_input.conflict_files == ["docs/guide.md"]


def test_resolve_diff_input_ignores_excluded_runtime_noise_when_ref_is_resolved(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_ref = commit_file(repo_root, "product/harness/README.md", "init\n", "init")
    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref=commit_ref)
    commit_harness(repo_root, harness_file)

    write_file(repo_root, ".autoworkflow/runtime/state.json", '{"status":"dirty"}\n')

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert diff_input.changed_files == ["product/harness/README.md"]
    assert diff_input.error is None


def test_scope_gate_pending_ref_with_only_excluded_runtime_artifacts_does_not_pass(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_file(repo_root, "product/harness/README.md", "init\n", "init")
    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref="pending")
    commit_harness(repo_root, harness_file)

    write_file(repo_root, ".autoworkflow/runtime/state.json", '{"status":"dirty"}\n')

    completed, payload = run_scope_gate(repo_root, harness_file)

    assert completed.returncode == 1
    assert payload["error"] == "excluded-runtime-noise-only"
    assert payload["passed"] is False


def test_resolve_diff_input_normalizes_absolute_repo_path_task_ref(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_file(repo_root, "product/harness/README.md", "init\n", "init")
    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    absolute_target = (repo_root / "product" / "harness" / "README.md").resolve()
    write_harness(harness_file, task_source_ref=str(absolute_target))

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert diff_input.changed_files == []
    assert diff_input.source == "task-target-path"
    assert diff_input.error is None


def test_resolve_diff_input_path_task_ref_with_directory_collects_descendant_changes(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_file(repo_root, "product/harness/README.md", "init\n", "init")
    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref="product/harness")

    write_file(repo_root, "product/harness/README.md", "dirty\n")

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert diff_input.changed_files == ["product/harness/README.md"]
    assert diff_input.source == "task-target-path-worktree"


def test_scope_gate_path_task_ref_without_real_changes_fails_without_allow_empty(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_file(repo_root, "product/harness/README.md", "init\n", "init")
    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref="product/harness/README.md")

    completed, payload = run_scope_gate(repo_root, harness_file)

    assert completed.returncode == 1
    assert payload["source"] == "task-target-path"
    assert payload["changed_files"] == []
    assert payload["error"] == "no-effective-changed-files"


def test_scope_gate_path_task_ref_without_real_changes_allows_empty_when_requested(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_file(repo_root, "product/harness/README.md", "init\n", "init")
    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref="product/harness/README.md")

    completed, payload = run_scope_gate_with_args(repo_root, harness_file, "--allow-empty")

    assert completed.returncode == 0
    assert payload["source"] == "task-target-path"
    assert payload["changed_files"] == []
    assert payload["effective_changed_files"] == []


def test_resolve_diff_input_path_task_delete_resolves_deleted_path_from_git_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    target = "product/harness/README.md"
    commit_file(repo_root, target, "init\n", "init")

    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref=target)

    run_git(repo_root, "rm", target)

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert diff_input.changed_files == [target]
    assert diff_input.source == "task-target-path-worktree"


def test_resolve_diff_input_path_task_rename_resolves_old_and_new_paths(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    old_path = "product/harness/README.md"
    new_path = "docs/task-interface-note.md"
    commit_file(repo_root, old_path, "init\n", "init")

    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref=old_path)

    (repo_root / "docs").mkdir(exist_ok=True)
    run_git(repo_root, "mv", old_path, new_path)

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )
    scope = check_scope(diff_input.changed_files, INCLUDE_PREFIXES, EXCLUDE_PREFIXES)

    assert diff_input.changed_files == [old_path, new_path]
    assert diff_input.source == "task-target-path-worktree"
    assert scope.passed is True


def test_resolve_diff_input_path_task_rename_to_out_of_scope_path_fails(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    old_path = "product/harness/README.md"
    new_path = "README.md"
    commit_file(repo_root, old_path, "init\n", "init")

    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref=old_path)

    run_git(repo_root, "mv", old_path, new_path)

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )
    scope = check_scope(diff_input.changed_files, INCLUDE_PREFIXES, EXCLUDE_PREFIXES)

    assert diff_input.changed_files == [old_path, new_path]
    assert scope.passed is False
    assert scope.violations == ["README.md"]


def test_resolve_diff_input_treats_empty_diff_range_as_resolved(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_file(repo_root, "product/harness/README.md", "base\n", "base")
    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref="HEAD..HEAD")

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert diff_input.source == "task-diff-range"
    assert diff_input.changed_files == []
    assert diff_input.error is None


def test_scope_gate_empty_diff_range_allows_empty_when_requested(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_file(repo_root, "product/harness/README.md", "base\n", "base")
    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref="HEAD..HEAD")

    completed, payload = run_scope_gate_with_args(repo_root, harness_file, "--allow-empty")

    assert completed.returncode == 0
    assert payload["source"] == "task-diff-range"
    assert payload["changed_files"] == []
    assert payload["effective_changed_files"] == []


def test_scope_gate_invalid_explicit_diff_range_fails_even_with_allow_empty(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_file(repo_root, "product/harness/README.md", "base\n", "base")
    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref="pending")

    completed, payload = run_scope_gate_with_args(
        repo_root,
        harness_file,
        "--diff-range",
        "missing..HEAD",
        "--allow-empty",
    )

    assert completed.returncode == 1
    assert payload["source"] == "explicit-diff-range"
    assert payload["task_source_ref"] == "missing..HEAD"
    assert payload["error"] == "unresolved-explicit-diff-range"


def test_scope_gate_invalid_explicit_commit_fails_even_with_allow_empty(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_file(repo_root, "product/harness/README.md", "base\n", "base")
    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref="pending")

    completed, payload = run_scope_gate_with_args(
        repo_root,
        harness_file,
        "--commit",
        "missing-commit",
        "--allow-empty",
    )

    assert completed.returncode == 1
    assert payload["source"] == "explicit-commit"
    assert payload["task_source_ref"] == "missing-commit"
    assert payload["error"] == "unresolved-explicit-commit"


def test_resolve_diff_input_without_task_source_ref_uses_upstream_diff_first(tmp_path: Path) -> None:
    remote_root = tmp_path / "remote.git"
    repo_root = tmp_path / "repo"
    run_git_global("init", "--bare", str(remote_root))
    run_git_global("clone", str(remote_root), str(repo_root))
    run_git(repo_root, "config", "user.email", "tester@example.com")
    run_git(repo_root, "config", "user.name", "tester")

    commit_file(repo_root, "product/harness/README.md", "base\n", "base")
    run_git(repo_root, "push", "-u", "origin", "HEAD")
    commit_file(repo_root, "docs/guide.md", "changed\n", "local change")

    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref="pending")
    commit_harness(repo_root, harness_file)

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert diff_input.source == "upstream-diff"
    assert set(diff_input.changed_files) == {"docs/guide.md", ".autoworkflow/harness.yaml"}


def test_resolve_diff_input_without_task_source_ref_falls_back_to_head_parent_diff(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    init_repo(repo_root)

    commit_file(repo_root, "product/harness/README.md", "base\n", "base")
    commit_file(repo_root, "docs/guide.md", "changed\n", "local change")

    harness_file = repo_root / ".autoworkflow" / "harness.yaml"
    write_harness(harness_file, task_source_ref="pending")
    commit_harness(repo_root, harness_file)

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=None,
        diff_range=None,
        commit_ref=None,
        exclude_prefixes=EXCLUDE_PREFIXES,
    )

    assert diff_input.source == "head-parent-diff"
    assert diff_input.changed_files == [".autoworkflow/harness.yaml"]
