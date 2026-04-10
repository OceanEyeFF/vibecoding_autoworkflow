#!/usr/bin/env python3
"""Check that the current working tree only touches an approved closeout scope."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ALLOWED_PREFIXES = (
    ".autoworkflow/contracts/",
    ".autoworkflow/closeout/",
    ".autoworkflow/state/",
    "docs/knowledge/README.md",
    "docs/knowledge/autoresearch/README.md",
    "docs/knowledge/autoresearch/overview.md",
    "docs/operations/",
    "toolchain/scripts/test/",
    "tools/closeout_acceptance_gate.py",
    "tools/gate_status_backfill.py",
    "tools/scope_gate_check.py",
)


@dataclass
class ScopeGateResult:
    passed: bool
    changed_files: list[str]
    violations: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the closeout worktree scope.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root used for git status inspection.",
    )
    parser.add_argument(
        "--allowed-prefix",
        action="append",
        default=[],
        help="Additional path prefix that is allowed to change.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON only.",
    )
    return parser.parse_args()


def collect_changed_files(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--short", "--untracked-files=all"],
        check=True,
        capture_output=True,
        text=True,
    )
    changed: list[str] = []
    for raw_line in completed.stdout.splitlines():
        if not raw_line:
            continue
        path = raw_line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        changed.append(path)
    return changed


def check_scope(changed_files: list[str], allowed_prefixes: tuple[str, ...]) -> ScopeGateResult:
    violations: list[str] = []
    for path in changed_files:
        if path.startswith(".git"):
            continue
        if any(path.startswith(prefix) for prefix in allowed_prefixes):
            continue
        violations.append(path)
    return ScopeGateResult(passed=not violations, changed_files=changed_files, violations=violations)


def main() -> int:
    args = parse_args()
    allowed_prefixes = DEFAULT_ALLOWED_PREFIXES + tuple(args.allowed_prefix)
    changed_files = collect_changed_files(args.repo_root)
    result = check_scope(changed_files, allowed_prefixes)

    payload = {
        "passed": result.passed,
        "changed_files": result.changed_files,
        "violations": result.violations,
        "allowed_prefixes": list(allowed_prefixes),
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if result.passed:
            print("Scope gate passed.")
        else:
            print("Scope gate failed.")
            for violation in result.violations:
                print(f"  disallowed change: {violation}")
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
