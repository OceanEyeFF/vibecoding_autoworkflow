#!/usr/bin/env python3
"""Validate changed files against harness contract scope include/exclude prefixes."""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ChangedPathEntry:
    status: str
    paths: tuple[str, ...]


@dataclass
class ScopeGateResult:
    passed: bool
    changed_files: list[str]
    effective_changed_files: list[str]
    ignored_files: list[str]
    violations: list[str]
    include_prefixes: list[str]
    exclude_prefixes: list[str]


@dataclass
class DiffInputResult:
    changed_files: list[str]
    source: str
    task_source_ref: str | None
    error: str | None = None
    error_detail: str | None = None
    conflict_files: list[str] = field(default_factory=list)
    live_worktree_files: list[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate changed files against harness contract scope.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--harness-file",
        type=Path,
        default=Path(".autoworkflow") / "harness.yaml",
        help="Path to harness config, relative to --repo-root unless absolute.",
    )
    parser.add_argument(
        "--task-source-ref",
        default=None,
        help="Task source reference (commit / PR ref / diff range / target path).",
    )
    parser.add_argument(
        "--diff-range",
        default=None,
        help="Explicit git diff range (e.g. main...HEAD or <base>..<head>).",
    )
    parser.add_argument("--commit", default=None, help="Explicit commit reference to inspect.")
    parser.add_argument("--include-prefix", action="append", default=[])
    parser.add_argument("--exclude-prefix", action="append", default=[])
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow empty changed-files result without failing the gate.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    return parser.parse_args()


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def strip_yaml_comments(line: str) -> str:
    """Remove trailing YAML comments while preserving # inside quoted strings."""

    in_single = False
    in_double = False
    escaped = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single and not escaped:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:index]

        escaped = (char == "\\") and in_double and not escaped
        if char != "\\":
            escaped = False

    return line


def parse_scope_prefixes(harness_file: Path) -> tuple[list[str], list[str]]:
    """Parse contract.scope.include/exclude list entries from one harness YAML file."""

    text = harness_file.read_text(encoding="utf-8")
    key_stack: list[str] = []
    indent_stack: list[int] = []
    includes: list[str] = []
    excludes: list[str] = []

    key_pattern = re.compile(r"^(\s*)([A-Za-z0-9_-]+):(?:\s*(.*))?$")
    list_pattern = re.compile(r"^(\s*)-\s*(.+)$")

    for raw_line in text.splitlines():
        line = strip_yaml_comments(raw_line).rstrip()
        if not line.strip():
            continue

        key_match = key_pattern.match(line)
        if key_match:
            indent = len(key_match.group(1))
            key = key_match.group(2)
            while indent_stack and indent <= indent_stack[-1]:
                indent_stack.pop()
                key_stack.pop()
            key_stack.append(key)
            indent_stack.append(indent)
            continue

        list_match = list_pattern.match(line)
        if not list_match:
            continue

        item = unquote(list_match.group(2))
        current_path = tuple(key_stack)
        if current_path == ("contract", "scope", "include"):
            includes.append(item)
        elif current_path == ("contract", "scope", "exclude"):
            excludes.append(item)

    return includes, excludes


def parse_runtime_task_source_ref(harness_file: Path) -> str | None:
    """Parse runtime.task_source_ref scalar from one harness YAML file."""

    text = harness_file.read_text(encoding="utf-8")
    key_stack: list[str] = []
    indent_stack: list[int] = []
    key_pattern = re.compile(r"^(\s*)([A-Za-z0-9_-]+):(?:\s*(.*))?$")

    for raw_line in text.splitlines():
        line = strip_yaml_comments(raw_line).rstrip()
        if not line.strip():
            continue
        match = key_pattern.match(line)
        if not match:
            continue

        indent = len(match.group(1))
        key = match.group(2)
        value = match.group(3) or ""
        while indent_stack and indent <= indent_stack[-1]:
            indent_stack.pop()
            key_stack.pop()
        key_stack.append(key)
        indent_stack.append(indent)

        if tuple(key_stack) == ("runtime", "task_source_ref"):
            parsed = unquote(value)
            return parsed or None
    return None


def run_git(repo_root: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def dedupe_paths(paths: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if not path or path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return deduped


def extract_entry_paths(status: str, parts: list[str]) -> tuple[str, ...]:
    cleaned = tuple(part.strip() for part in parts if part.strip())
    if not cleaned:
        return ()
    if status and status[0] in {"R", "C"} and len(cleaned) >= 2:
        return cleaned[:2]
    return (cleaned[-1],)


def parse_git_name_status_entries(output: str) -> list[ChangedPathEntry]:
    entries: list[ChangedPathEntry] = []
    for raw_line in output.splitlines():
        if not raw_line.strip():
            continue
        parts = raw_line.split("\t")
        status = parts[0].strip()
        entry_paths = extract_entry_paths(status, parts[1:])
        if entry_paths:
            entries.append(ChangedPathEntry(status=status, paths=entry_paths))
    return entries


def parse_git_status_entries(output: str) -> list[ChangedPathEntry]:
    entries: list[ChangedPathEntry] = []
    for raw_line in output.splitlines():
        if not raw_line:
            continue
        status = raw_line[:2].strip() or raw_line[:2]
        path_text = raw_line[3:].strip()
        parts = [part.strip() for part in path_text.split(" -> ", 1)] if " -> " in path_text else [path_text]
        entry_paths = extract_entry_paths(status, parts)
        if entry_paths:
            entries.append(ChangedPathEntry(status=status, paths=entry_paths))
    return entries


def flatten_changed_entries(entries: list[ChangedPathEntry]) -> list[str]:
    return dedupe_paths([path for entry in entries for path in entry.paths])


def normalize_repo_relative_path(repo_root: Path, path_ref: str) -> str | None:
    candidate = Path(path_ref)
    resolved = candidate.resolve() if candidate.is_absolute() else (repo_root / candidate).resolve()
    with contextlib.suppress(ValueError):
        return resolved.relative_to(repo_root.resolve()).as_posix()
    return None


def filter_effective_changed_files(changed_files: list[str], exclude_prefixes: list[str]) -> tuple[list[str], list[str]]:
    effective: list[str] = []
    ignored: list[str] = []
    for path in changed_files:
        if path.startswith(".git") or any(path.startswith(prefix) for prefix in exclude_prefixes):
            ignored.append(path)
            continue
        effective.append(path)
    return dedupe_paths(effective), dedupe_paths(ignored)


def collect_changed_entries(repo_root: Path) -> list[ChangedPathEntry]:
    completed = run_git(repo_root, "status", "--short", "--untracked-files=all", check=True)
    return parse_git_status_entries(completed.stdout)


def collect_changed_files(repo_root: Path) -> list[str]:
    return flatten_changed_entries(collect_changed_entries(repo_root))


def collect_changed_files_from_diff_range(repo_root: Path, diff_range: str) -> list[str]:
    completed = run_git(repo_root, "diff", "--name-status", "--find-renames", diff_range)
    if completed.returncode != 0:
        return []
    return flatten_changed_entries(parse_git_name_status_entries(completed.stdout))


def resolve_diff_range(repo_root: Path, diff_range: str) -> tuple[list[str], bool]:
    completed = run_git(repo_root, "diff", "--name-status", "--find-renames", diff_range)
    if completed.returncode != 0:
        return [], False
    return flatten_changed_entries(parse_git_name_status_entries(completed.stdout)), True


def collect_changed_files_from_commit(repo_root: Path, commit_ref: str) -> list[str]:
    completed = run_git(
        repo_root,
        "diff-tree",
        "--name-status",
        "--find-renames",
        "--no-commit-id",
        "--root",
        "-r",
        "-m",
        commit_ref,
    )
    if completed.returncode != 0:
        return []
    return flatten_changed_entries(parse_git_name_status_entries(completed.stdout))


def is_commit_ref(repo_root: Path, ref: str) -> bool:
    completed = run_git(repo_root, "rev-parse", "--verify", f"{ref}^{{commit}}")
    return completed.returncode == 0


def collect_changed_files_from_fallback(repo_root: Path) -> DiffInputResult:
    upstream = run_git(repo_root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    if upstream.returncode == 0:
        upstream_ref = upstream.stdout.strip()
        merge_base = run_git(repo_root, "merge-base", "HEAD", upstream_ref)
        if merge_base.returncode == 0:
            base = merge_base.stdout.strip()
            files = collect_changed_files_from_diff_range(repo_root, f"{base}..HEAD")
            if files:
                return DiffInputResult(changed_files=files, source="upstream-diff", task_source_ref=upstream_ref)

    head_parent = run_git(repo_root, "rev-parse", "--verify", "HEAD^")
    if head_parent.returncode == 0:
        files = collect_changed_files_from_diff_range(repo_root, "HEAD^..HEAD")
        if files:
            return DiffInputResult(changed_files=files, source="head-parent-diff", task_source_ref="HEAD^..HEAD")

    return DiffInputResult(changed_files=[], source="empty", task_source_ref=None)


def collect_changed_files_for_path_ref(repo_root: Path, path_ref: str) -> tuple[list[str], bool]:
    relative_path = normalize_repo_relative_path(repo_root, path_ref)
    if relative_path is None:
        return [], False

    matched_paths: list[str] = []
    prefix = f"{relative_path}/"

    for entry in collect_changed_entries(repo_root):
        if any(path == relative_path or path.startswith(prefix) for path in entry.paths):
            matched_paths.extend(entry.paths)

    if matched_paths:
        return dedupe_paths(matched_paths), True

    resolved_path = repo_root / relative_path
    if resolved_path.exists():
        return [], True
    return [], False


def collect_changed_files_from_task_source_ref(repo_root: Path, task_source_ref: str) -> DiffInputResult:
    ref = task_source_ref.strip()
    if not ref or ref == "pending":
        return DiffInputResult(changed_files=[], source="pending-task-source-ref", task_source_ref=task_source_ref)

    if ".." in ref:
        files, resolved = resolve_diff_range(repo_root, ref)
        if resolved:
            return DiffInputResult(changed_files=files, source="task-diff-range", task_source_ref=task_source_ref)

    path_files, path_resolved = collect_changed_files_for_path_ref(repo_root, ref)
    if path_resolved:
        source = "task-target-path"
        if path_files:
            source = "task-target-path-worktree"
        return DiffInputResult(changed_files=path_files, source=source, task_source_ref=task_source_ref)

    if is_commit_ref(repo_root, ref):
        files = collect_changed_files_from_commit(repo_root, ref)
        if files:
            return DiffInputResult(changed_files=files, source="task-commit", task_source_ref=task_source_ref)

    range_match = re.search(r"([A-Za-z0-9._/-]+\.{2,3}[A-Za-z0-9._/-]+)", ref)
    if range_match:
        diff_ref = range_match.group(1)
        files, resolved = resolve_diff_range(repo_root, diff_ref)
        if resolved:
            return DiffInputResult(changed_files=files, source="task-embedded-range", task_source_ref=task_source_ref)

    commit_match = re.search(r"\b([0-9a-f]{7,40})\b", ref, flags=re.IGNORECASE)
    if commit_match:
        commit_ref = commit_match.group(1)
        files = collect_changed_files_from_commit(repo_root, commit_ref)
        if files:
            return DiffInputResult(
                changed_files=files,
                source="task-embedded-commit",
                task_source_ref=task_source_ref,
            )

    return DiffInputResult(
        changed_files=[],
        source="unresolved-task-source-ref",
        task_source_ref=task_source_ref,
        error="unresolved-task-source-ref",
        error_detail=f"unable to resolve task_source_ref: {task_source_ref}",
    )


def attach_live_worktree_context(
    repo_root: Path,
    diff_input: DiffInputResult,
    *,
    exclude_prefixes: list[str],
) -> DiffInputResult:
    worktree_files = collect_changed_files(repo_root)
    diff_input.live_worktree_files = worktree_files

    worktree_effective, _ = filter_effective_changed_files(worktree_files, exclude_prefixes)
    resolved_effective, _ = filter_effective_changed_files(diff_input.changed_files, exclude_prefixes)
    resolved_effective_set = set(resolved_effective)
    extra_files = [path for path in worktree_effective if path not in resolved_effective_set]
    if extra_files:
        diff_input.error = "live-worktree-conflict"
        diff_input.error_detail = (
            "resolved source has additional live worktree changes outside the task source ref"
        )
        diff_input.conflict_files = extra_files
    return diff_input


def resolve_diff_input(
    repo_root: Path,
    harness_file: Path,
    *,
    task_source_ref: str | None,
    diff_range: str | None,
    commit_ref: str | None,
    exclude_prefixes: list[str] | None = None,
) -> DiffInputResult:
    exclude_prefixes = exclude_prefixes or []
    if diff_range:
        return attach_live_worktree_context(
            repo_root,
            DiffInputResult(
                changed_files=collect_changed_files_from_diff_range(repo_root, diff_range),
                source="explicit-diff-range",
                task_source_ref=task_source_ref,
            ),
            exclude_prefixes=exclude_prefixes,
        )

    if commit_ref:
        return attach_live_worktree_context(
            repo_root,
            DiffInputResult(
                changed_files=collect_changed_files_from_commit(repo_root, commit_ref),
                source="explicit-commit",
                task_source_ref=task_source_ref,
            ),
            exclude_prefixes=exclude_prefixes,
        )

    ref = task_source_ref or parse_runtime_task_source_ref(harness_file)
    if ref and ref != "pending":
        diff_input = collect_changed_files_from_task_source_ref(repo_root, ref)
        if diff_input.error:
            diff_input.live_worktree_files = collect_changed_files(repo_root)
            return diff_input
        return attach_live_worktree_context(repo_root, diff_input, exclude_prefixes=exclude_prefixes)

    worktree_files = collect_changed_files(repo_root)
    worktree_effective, _ = filter_effective_changed_files(worktree_files, exclude_prefixes)
    if worktree_effective:
        return DiffInputResult(changed_files=worktree_files, source="worktree-status", task_source_ref=ref)
    if worktree_files:
        return DiffInputResult(
            changed_files=worktree_files,
            source="worktree-status-excluded-only",
            task_source_ref=ref,
            error="excluded-runtime-noise-only",
            error_detail="live worktree only contains excluded runtime artifacts",
            live_worktree_files=worktree_files,
        )

    fallback = collect_changed_files_from_fallback(repo_root)
    fallback.task_source_ref = ref
    return fallback


def check_scope(
    changed_files: list[str],
    include_prefixes: list[str],
    exclude_prefixes: list[str],
) -> ScopeGateResult:
    effective_changed_files, ignored_files = filter_effective_changed_files(changed_files, exclude_prefixes)
    violations: list[str] = []
    for path in effective_changed_files:
        if include_prefixes and not any(path.startswith(prefix) for prefix in include_prefixes):
            violations.append(path)

    return ScopeGateResult(
        passed=not violations,
        changed_files=changed_files,
        effective_changed_files=effective_changed_files,
        ignored_files=ignored_files,
        violations=violations,
        include_prefixes=include_prefixes,
        exclude_prefixes=exclude_prefixes,
    )


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    harness_file = resolve_path(repo_root, args.harness_file)
    if not harness_file.exists():
        print(f"error: missing harness file: {harness_file}")
        return 1
    if not harness_file.is_file():
        print(f"error: harness path is not a file: {harness_file}")
        return 1

    include_prefixes, exclude_prefixes = parse_scope_prefixes(harness_file)
    include_prefixes.extend(args.include_prefix)
    exclude_prefixes.extend(args.exclude_prefix)

    diff_input = resolve_diff_input(
        repo_root,
        harness_file,
        task_source_ref=args.task_source_ref,
        diff_range=args.diff_range,
        commit_ref=args.commit,
        exclude_prefixes=exclude_prefixes,
    )
    result = check_scope(diff_input.changed_files, include_prefixes, exclude_prefixes)
    if diff_input.error:
        payload = {
            "passed": False,
            "changed_files": diff_input.changed_files,
            "effective_changed_files": result.effective_changed_files,
            "ignored_files": result.ignored_files,
            "violations": result.violations,
            "conflict_files": diff_input.conflict_files,
            "live_worktree_files": diff_input.live_worktree_files,
            "include_prefixes": include_prefixes,
            "exclude_prefixes": exclude_prefixes,
            "harness_file": str(harness_file),
            "source": diff_input.source,
            "task_source_ref": diff_input.task_source_ref,
            "error": diff_input.error,
            "error_detail": diff_input.error_detail,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    if not result.effective_changed_files and not args.allow_empty:
        payload = {
            "passed": False,
            "changed_files": diff_input.changed_files,
            "effective_changed_files": [],
            "ignored_files": result.ignored_files,
            "violations": result.violations,
            "conflict_files": diff_input.conflict_files,
            "live_worktree_files": diff_input.live_worktree_files,
            "include_prefixes": include_prefixes,
            "exclude_prefixes": exclude_prefixes,
            "harness_file": str(harness_file),
            "source": diff_input.source,
            "task_source_ref": diff_input.task_source_ref,
            "error": "no-effective-changed-files",
            "error_detail": "no non-excluded changed files resolved from diff/worktree input",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    payload = {
        "passed": result.passed,
        "changed_files": result.changed_files,
        "effective_changed_files": result.effective_changed_files,
        "ignored_files": result.ignored_files,
        "violations": result.violations,
        "conflict_files": diff_input.conflict_files,
        "live_worktree_files": diff_input.live_worktree_files,
        "include_prefixes": result.include_prefixes,
        "exclude_prefixes": result.exclude_prefixes,
        "harness_file": str(harness_file),
        "source": diff_input.source,
        "task_source_ref": diff_input.task_source_ref,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if result.passed:
            print("Harness scope gate passed.")
        else:
            print("Harness scope gate failed.")
            for violation in result.violations:
                print(f"  out-of-scope change: {violation}")
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
