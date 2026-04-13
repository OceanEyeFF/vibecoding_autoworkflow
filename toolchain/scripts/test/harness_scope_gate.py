#!/usr/bin/env python3
"""Validate changed files against harness contract scope include/exclude prefixes."""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class ScopeGateResult:
    passed: bool
    changed_files: list[str]
    violations: list[str]
    include_prefixes: list[str]
    exclude_prefixes: list[str]


@dataclass
class DiffInputResult:
    changed_files: list[str]
    source: str
    task_source_ref: str | None


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


def collect_changed_files(repo_root: Path) -> list[str]:
    completed = run_git(repo_root, "status", "--short", "--untracked-files=all", check=True)
    changed: list[str] = []
    for raw_line in completed.stdout.splitlines():
        if not raw_line:
            continue
        path = raw_line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        changed.append(path)
    return changed


def collect_changed_files_from_diff_range(repo_root: Path, diff_range: str) -> list[str]:
    completed = run_git(repo_root, "diff", "--name-only", diff_range)
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def collect_changed_files_from_commit(repo_root: Path, commit_ref: str) -> list[str]:
    completed = run_git(repo_root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit_ref)
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


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


def collect_changed_files_from_task_source_ref(repo_root: Path, task_source_ref: str) -> DiffInputResult:
    ref = task_source_ref.strip()
    if not ref or ref == "pending":
        return DiffInputResult(changed_files=[], source="pending-task-source-ref", task_source_ref=task_source_ref)

    if ".." in ref:
        files = collect_changed_files_from_diff_range(repo_root, ref)
        if files:
            return DiffInputResult(changed_files=files, source="task-diff-range", task_source_ref=task_source_ref)

    resolved_path = (repo_root / ref).resolve()
    with contextlib.suppress(ValueError):
        relative_path = resolved_path.relative_to(repo_root.resolve())
        if resolved_path.exists():
            return DiffInputResult(
                changed_files=[relative_path.as_posix()],
                source="task-target-path",
                task_source_ref=task_source_ref,
            )

    if is_commit_ref(repo_root, ref):
        files = collect_changed_files_from_commit(repo_root, ref)
        if files:
            return DiffInputResult(changed_files=files, source="task-commit", task_source_ref=task_source_ref)

    range_match = re.search(r"([A-Za-z0-9._/-]+\.{2,3}[A-Za-z0-9._/-]+)", ref)
    if range_match:
        diff_ref = range_match.group(1)
        files = collect_changed_files_from_diff_range(repo_root, diff_ref)
        if files:
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

    return DiffInputResult(changed_files=[], source="unresolved-task-source-ref", task_source_ref=task_source_ref)


def resolve_diff_input(
    repo_root: Path,
    harness_file: Path,
    *,
    task_source_ref: str | None,
    diff_range: str | None,
    commit_ref: str | None,
) -> DiffInputResult:
    if diff_range:
        return DiffInputResult(
            changed_files=collect_changed_files_from_diff_range(repo_root, diff_range),
            source="explicit-diff-range",
            task_source_ref=task_source_ref,
        )

    if commit_ref:
        return DiffInputResult(
            changed_files=collect_changed_files_from_commit(repo_root, commit_ref),
            source="explicit-commit",
            task_source_ref=task_source_ref,
        )

    ref = task_source_ref or parse_runtime_task_source_ref(harness_file)
    worktree_files = collect_changed_files(repo_root)
    if worktree_files:
        return DiffInputResult(changed_files=worktree_files, source="worktree-status", task_source_ref=ref)

    if ref and ref != "pending":
        result = collect_changed_files_from_task_source_ref(repo_root, ref)
        if result.changed_files:
            return result

    fallback = collect_changed_files_from_fallback(repo_root)
    fallback.task_source_ref = ref
    return fallback


def check_scope(
    changed_files: list[str],
    include_prefixes: list[str],
    exclude_prefixes: list[str],
) -> ScopeGateResult:
    violations: list[str] = []
    for path in changed_files:
        if path.startswith(".git"):
            continue
        if any(path.startswith(prefix) for prefix in exclude_prefixes):
            continue
        if include_prefixes and not any(path.startswith(prefix) for prefix in include_prefixes):
            violations.append(path)

    return ScopeGateResult(
        passed=not violations,
        changed_files=changed_files,
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
    )
    changed_files = diff_input.changed_files
    if not changed_files and not args.allow_empty:
        payload = {
            "passed": False,
            "changed_files": [],
            "violations": [],
            "include_prefixes": include_prefixes,
            "exclude_prefixes": exclude_prefixes,
            "harness_file": str(harness_file),
            "source": diff_input.source,
            "task_source_ref": diff_input.task_source_ref,
            "error": "no changed files resolved from diff/worktree input",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    result = check_scope(changed_files, include_prefixes, exclude_prefixes)

    payload = {
        "passed": result.passed,
        "changed_files": result.changed_files,
        "violations": result.violations,
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
