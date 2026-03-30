#!/usr/bin/env python3
"""Clone or update tmp exrepos from a simple GitHub repo list."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from common import REPO_ROOT
from exrepo_runtime import resolve_tmp_exrepos_root


DEFAULT_REPO_LIST = Path(__file__).with_name("exrepo.txt")


@dataclass(frozen=True)
class ExrepoSpec:
    raw: str
    owner: str
    name: str

    @property
    def remote_url(self) -> str:
        return f"https://github.com/{self.raw}.git"

    @property
    def target_dirname(self) -> str:
        return self.name


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Clone or update tmp exrepos from a repo list. "
            "Each entry must be a GitHub owner/repo line."
        )
    )
    parser.add_argument(
        "--repo-list",
        type=Path,
        default=DEFAULT_REPO_LIST,
        help=f"Repo list file. Defaults to {DEFAULT_REPO_LIST.name}.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root used to derive the stable tmp exrepo root.",
    )
    parser.add_argument(
        "--temp-root",
        type=Path,
        help="Optional OS temp root override for tests or custom environments.",
    )
    return parser.parse_args(argv)


def load_exrepo_specs(path: Path) -> list[ExrepoSpec]:
    resolved_path = path.expanduser().resolve()
    if not resolved_path.is_file():
        raise FileNotFoundError(f"Repo list not found: {resolved_path}")

    specs: list[ExrepoSpec] = []
    seen_local_names: dict[str, int] = {}
    for line_number, raw_line in enumerate(resolved_path.read_text(encoding="utf-8").splitlines(), start=1):
        value = raw_line.strip()
        if not value or value.startswith("#"):
            continue

        owner, separator, repo_name = value.partition("/")
        if not separator or not owner.strip() or not repo_name.strip() or "/" in repo_name:
            raise ValueError(
                f"Invalid repo entry at line {line_number}: {value!r}. Expected 'owner/repo'."
            )

        spec = ExrepoSpec(raw=value, owner=owner.strip(), name=repo_name.strip())
        previous_line = seen_local_names.get(spec.target_dirname)
        if previous_line is not None:
            raise ValueError(
                "Duplicate local repo target "
                f"{spec.target_dirname!r} at line {line_number}; first seen at line {previous_line}."
            )
        seen_local_names[spec.target_dirname] = line_number
        specs.append(spec)

    if not specs:
        raise ValueError(f"Repo list is empty: {resolved_path}")
    return specs


def run_git(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def sync_exrepo(spec: ExrepoSpec, exrepo_root: Path) -> str:
    target_dir = exrepo_root / spec.target_dirname
    if target_dir.exists():
        if not (target_dir / ".git").is_dir():
            raise RuntimeError(f"Target exists but is not a git repo: {target_dir}")

        pull_result = run_git(["pull"], cwd=target_dir)
        if pull_result.returncode == 0:
            return "pulled"

        reset_result = run_git(["reset", "--hard"], cwd=target_dir)
        if reset_result.returncode != 0:
            raise RuntimeError(_format_git_failure("git reset --hard", spec, target_dir, reset_result))

        retry_pull_result = run_git(["pull"], cwd=target_dir)
        if retry_pull_result.returncode != 0:
            raise RuntimeError(_format_git_failure("git pull", spec, target_dir, retry_pull_result))
        return "reset_then_pulled"

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    clone_result = run_git(["clone", spec.remote_url, str(target_dir)])
    if clone_result.returncode != 0:
        raise RuntimeError(_format_git_failure("git clone", spec, target_dir, clone_result))
    return "cloned"


def _format_git_failure(
    action: str,
    spec: ExrepoSpec,
    target_dir: Path,
    result: subprocess.CompletedProcess[str],
) -> str:
    detail = result.stderr.strip() or result.stdout.strip() or f"exit={result.returncode}"
    return f"{action} failed for {spec.raw} -> {target_dir}: {detail}"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        specs = load_exrepo_specs(args.repo_list)
        exrepo_root = resolve_tmp_exrepos_root(repo_root=args.repo_root, temp_root=args.temp_root)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    exrepo_root.mkdir(parents=True, exist_ok=True)
    print(f"tmp_exrepo_root: {exrepo_root}")

    failures: list[str] = []
    for spec in specs:
        target_dir = exrepo_root / spec.target_dirname
        try:
            action = sync_exrepo(spec, exrepo_root)
        except RuntimeError as exc:
            message = f"failed: {spec.raw} -> {target_dir} :: {exc}"
            failures.append(message)
            print(message, file=sys.stderr)
            continue
        print(f"{action}: {spec.raw} -> {target_dir}")

    if failures:
        print(f"sync_failed: {len(failures)} repo(s)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
