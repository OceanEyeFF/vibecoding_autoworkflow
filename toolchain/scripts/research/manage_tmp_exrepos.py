#!/usr/bin/env python3
"""Clone or update tmp exrepos from a simple GitHub repo list."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from common import REPO_ROOT
from exrepo_runtime import resolve_tmp_exrepos_root


DEFAULT_REPO_LIST = Path(__file__).with_name("exrepo.txt")
INVALID_TARGET_DIRNAMES = {".", ".."}


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


def _validate_target_dirname(name: str, *, line_number: int, raw_value: str) -> str:
    if not name or name in INVALID_TARGET_DIRNAMES or "\\" in name or "/" in name:
        raise ValueError(
            "Invalid local repo target "
            f"{name!r} at line {line_number}: {raw_value!r}."
        )
    return name


def _resolve_target_dir(spec: ExrepoSpec, exrepo_root: Path) -> Path:
    resolved_root = exrepo_root.expanduser().resolve(strict=False)
    target_dir = (resolved_root / spec.target_dirname).resolve(strict=False)
    try:
        target_dir.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(
            "Refusing to operate outside tmp exrepo root: "
            f"{spec.raw} -> {target_dir}"
        ) from exc
    return target_dir


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

        target_name = _validate_target_dirname(
            repo_name.strip(),
            line_number=line_number,
            raw_value=value,
        )
        spec = ExrepoSpec(raw=value, owner=owner.strip(), name=target_name)
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


def _normalize_repo_identity(value: str) -> str:
    return value.strip().strip("/").removesuffix(".git").casefold()


def _extract_github_repo_identity(remote_url: str) -> str | None:
    value = remote_url.strip()
    if not value:
        return None

    ssh_match = re.match(r"^git@github\.com:(?P<path>.+)$", value, flags=re.IGNORECASE)
    if ssh_match:
        path_value = ssh_match.group("path")
    else:
        parsed = urlparse(value)
        host = (parsed.hostname or "").casefold()
        if host not in {"github.com", "www.github.com"}:
            return None
        path_value = parsed.path

    parts = [part for part in path_value.strip("/").split("/") if part]
    if len(parts) != 2:
        return None
    owner, repo = parts
    return _normalize_repo_identity(f"{owner}/{repo}")


def _read_remote_origin_identity(spec: ExrepoSpec, target_dir: Path) -> str:
    origin_result = run_git(["remote", "get-url", "origin"], cwd=target_dir)
    if origin_result.returncode != 0:
        raise RuntimeError(_format_git_failure("git remote get-url origin", spec, target_dir, origin_result))
    origin_identity = _extract_github_repo_identity(origin_result.stdout)
    if origin_identity is None:
        raise RuntimeError(
            f"Existing repo origin is not a supported GitHub remote for {spec.raw}: {origin_result.stdout.strip()!r}"
        )
    return origin_identity


def _resolve_origin_head(spec: ExrepoSpec, target_dir: Path) -> str:
    origin_head = run_git(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"], cwd=target_dir)
    if origin_head.returncode != 0 or not origin_head.stdout.strip():
        raise RuntimeError(
            _format_git_failure("git symbolic-ref --quiet --short refs/remotes/origin/HEAD", spec, target_dir, origin_head)
        )
    return origin_head.stdout.strip()


def _resolve_current_upstream(spec: ExrepoSpec, target_dir: Path) -> str:
    upstream = run_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=target_dir)
    if upstream.returncode != 0 or not upstream.stdout.strip():
        raise RuntimeError(
            _format_git_failure("git rev-parse --abbrev-ref --symbolic-full-name @{u}", spec, target_dir, upstream)
        )
    return upstream.stdout.strip()


def _assert_existing_repo_matches_target(spec: ExrepoSpec, target_dir: Path) -> None:
    expected_identity = _normalize_repo_identity(spec.raw)
    origin_identity = _read_remote_origin_identity(spec, target_dir)
    if origin_identity != expected_identity:
        raise RuntimeError(
            f"Existing repo origin mismatch for {spec.raw} -> {target_dir}: {origin_identity}"
        )

    expected_upstream = _resolve_origin_head(spec, target_dir)
    current_upstream = _resolve_current_upstream(spec, target_dir)
    if current_upstream != expected_upstream:
        raise RuntimeError(
            "Existing repo is not tracking the default upstream "
            f"for {spec.raw} -> {target_dir}: expected {expected_upstream}, got {current_upstream}"
        )


def sync_exrepo(spec: ExrepoSpec, exrepo_root: Path) -> str:
    target_dir = _resolve_target_dir(spec, exrepo_root)
    if target_dir.exists():
        if not (target_dir / ".git").is_dir():
            raise RuntimeError(f"Target exists but is not a git repo: {target_dir}")
        _assert_existing_repo_matches_target(spec, target_dir)

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
        try:
            target_dir = _resolve_target_dir(spec, exrepo_root)
            action = sync_exrepo(spec, exrepo_root)
        except RuntimeError as exc:
            target_dir = exrepo_root / spec.target_dirname
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
