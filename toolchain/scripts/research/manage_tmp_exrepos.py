#!/usr/bin/env python3
"""Maintain shared tmp exrepos from a GitHub repo catalog."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
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


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo-list",
        type=Path,
        default=DEFAULT_REPO_LIST,
        help=f"Repo catalog file. Defaults to {DEFAULT_REPO_LIST.name}.",
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


def _add_selector_options(parser: argparse.ArgumentParser) -> None:
    selector_group = parser.add_mutually_exclusive_group()
    selector_group.add_argument(
        "--repo",
        action="append",
        default=[],
        help=(
            "Repeatable local repo target name from --repo-list. "
            "Only catalog names are accepted."
        ),
    )
    selector_group.add_argument(
        "--suite",
        type=Path,
        help="Suite manifest path used to derive repos from runs[*].repo.",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Maintain shared tmp exrepos from a catalog of GitHub owner/repo entries. "
            "Legacy flat mode (no subcommand) remains compatible as full-catalog prepare."
        ),
        allow_abbrev=False,
    )
    _add_common_options(parser)
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser(
        "init",
        help="Clone missing repos only. Existing valid repos are left untouched.",
        allow_abbrev=False,
    )
    _add_common_options(init_parser)
    _add_selector_options(init_parser)

    reset_parser = subparsers.add_parser(
        "reset",
        help="Hard reset existing repos to origin default branch HEAD.",
        allow_abbrev=False,
    )
    _add_common_options(reset_parser)
    _add_selector_options(reset_parser)

    prepare_parser = subparsers.add_parser(
        "prepare",
        help="Clone missing repos and reset all selected repos to origin default branch HEAD.",
        allow_abbrev=False,
    )
    _add_common_options(prepare_parser)
    _add_selector_options(prepare_parser)

    args = parser.parse_args(argv)
    if args.command is None:
        # Legacy compatibility: no subcommand and only legacy flags.
        args.command = "prepare"
        args.repo = []
        args.suite = None
        args.legacy_mode = True
    else:
        args.legacy_mode = False
    return args


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


def _is_path_like(value: str) -> bool:
    return value.startswith((".", "~")) or "/" in value or "\\" in value


def load_exrepo_specs(path: Path) -> list[ExrepoSpec]:
    resolved_path = path.expanduser().resolve()
    if not resolved_path.is_file():
        raise FileNotFoundError(f"Repo list not found: {resolved_path}")

    specs: list[ExrepoSpec] = []
    seen_local_names: dict[str, int] = {}
    lines = resolved_path.read_text(encoding="utf-8").splitlines()
    for line_number, raw_line in enumerate(lines, start=1):
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


def _format_git_failure(
    action: str,
    spec: ExrepoSpec,
    target_dir: Path,
    result: subprocess.CompletedProcess[str],
) -> str:
    detail = result.stderr.strip() or result.stdout.strip() or f"exit={result.returncode}"
    return f"{action} failed for {spec.raw} -> {target_dir}: {detail}"


def _read_remote_origin_identity(spec: ExrepoSpec, target_dir: Path) -> str:
    origin_result = run_git(["remote", "get-url", "origin"], cwd=target_dir)
    if origin_result.returncode != 0:
        raise RuntimeError(
            _format_git_failure("git remote get-url origin", spec, target_dir, origin_result)
        )
    origin_identity = _extract_github_repo_identity(origin_result.stdout)
    if origin_identity is None:
        raise RuntimeError(
            f"Existing repo origin is not a supported GitHub remote for {spec.raw}: "
            f"{origin_result.stdout.strip()!r}"
        )
    return origin_identity


def _assert_existing_repo_matches_target(spec: ExrepoSpec, target_dir: Path) -> None:
    expected_identity = _normalize_repo_identity(spec.raw)
    origin_identity = _read_remote_origin_identity(spec, target_dir)
    if origin_identity != expected_identity:
        raise RuntimeError(
            f"Existing repo origin mismatch for {spec.raw} -> {target_dir}: {origin_identity}"
        )


def _fetch_origin(spec: ExrepoSpec, target_dir: Path) -> None:
    fetch_result = run_git(["fetch", "origin"], cwd=target_dir)
    if fetch_result.returncode != 0:
        raise RuntimeError(_format_git_failure("git fetch origin", spec, target_dir, fetch_result))


def _resolve_origin_head(spec: ExrepoSpec, target_dir: Path) -> str:
    last_result: subprocess.CompletedProcess[str] | None = None
    for attempt in range(2):
        origin_head = run_git(
            ["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
            cwd=target_dir,
        )
        if origin_head.returncode == 0 and origin_head.stdout.strip():
            return origin_head.stdout.strip()
        last_result = origin_head
        if attempt == 0:
            refresh_result = run_git(["remote", "set-head", "origin", "--auto"], cwd=target_dir)
            if refresh_result.returncode != 0:
                raise RuntimeError(
                    _format_git_failure("git remote set-head origin --auto", spec, target_dir, refresh_result)
                )
    if last_result is not None:
        detail = _format_git_failure(
            "git symbolic-ref --quiet --short refs/remotes/origin/HEAD",
            spec,
            target_dir,
            last_result,
        )
        raise RuntimeError(f"origin/HEAD unresolved after one refresh attempt. {detail}")
    raise RuntimeError(f"origin/HEAD unresolved for {spec.raw} -> {target_dir}")


def _default_branch_from_origin_head(origin_head: str) -> str:
    prefix = "origin/"
    if not origin_head.startswith(prefix) or len(origin_head) <= len(prefix):
        raise RuntimeError(f"Unexpected origin/HEAD symbolic ref: {origin_head!r}")
    return origin_head[len(prefix) :]


def _reset_existing_repo(spec: ExrepoSpec, target_dir: Path) -> None:
    _assert_existing_repo_matches_target(spec, target_dir)
    _fetch_origin(spec, target_dir)
    origin_head = _resolve_origin_head(spec, target_dir)
    default_branch = _default_branch_from_origin_head(origin_head)
    reset_result = run_git(["reset", "--hard", origin_head], cwd=target_dir)
    if reset_result.returncode != 0:
        raise RuntimeError(_format_git_failure("git reset --hard", spec, target_dir, reset_result))
    checkout_result = run_git(["checkout", "-B", default_branch, origin_head], cwd=target_dir)
    if checkout_result.returncode != 0:
        raise RuntimeError(
            _format_git_failure("git checkout -B <default-branch> <origin-head>", spec, target_dir, checkout_result)
        )


def init_exrepo(spec: ExrepoSpec, exrepo_root: Path) -> str:
    target_dir = _resolve_target_dir(spec, exrepo_root)
    if target_dir.exists():
        if not (target_dir / ".git").is_dir():
            raise RuntimeError(f"Target exists but is not a git repo: {target_dir}")
        _assert_existing_repo_matches_target(spec, target_dir)
        return "kept"

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    clone_result = run_git(["clone", spec.remote_url, str(target_dir)])
    if clone_result.returncode != 0:
        raise RuntimeError(_format_git_failure("git clone", spec, target_dir, clone_result))
    return "cloned"


def reset_exrepo(spec: ExrepoSpec, exrepo_root: Path) -> str:
    target_dir = _resolve_target_dir(spec, exrepo_root)
    if not target_dir.exists():
        raise RuntimeError(f"Target repo missing for reset: {target_dir}")
    if not (target_dir / ".git").is_dir():
        raise RuntimeError(f"Target exists but is not a git repo: {target_dir}")
    _reset_existing_repo(spec, target_dir)
    return "reset"


def prepare_exrepo(spec: ExrepoSpec, exrepo_root: Path) -> str:
    target_dir = _resolve_target_dir(spec, exrepo_root)
    cloned = False
    if target_dir.exists():
        if not (target_dir / ".git").is_dir():
            raise RuntimeError(f"Target exists but is not a git repo: {target_dir}")
    else:
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        clone_result = run_git(["clone", spec.remote_url, str(target_dir)])
        if clone_result.returncode != 0:
            raise RuntimeError(_format_git_failure("git clone", spec, target_dir, clone_result))
        cloned = True

    _reset_existing_repo(spec, target_dir)
    return "cloned_then_reset" if cloned else "reset"


def sync_exrepo(spec: ExrepoSpec, exrepo_root: Path, *, mode: str = "prepare") -> str:
    if mode == "init":
        return init_exrepo(spec, exrepo_root)
    if mode == "reset":
        return reset_exrepo(spec, exrepo_root)
    if mode == "prepare":
        return prepare_exrepo(spec, exrepo_root)
    raise ValueError(f"Unsupported mode: {mode}")


def _load_suite_manifest(path: Path) -> dict[str, Any]:
    resolved_path = path.expanduser().resolve()
    if not resolved_path.is_file():
        raise FileNotFoundError(f"Suite manifest not found: {resolved_path}")

    if resolved_path.suffix == ".json":
        payload = json.loads(resolved_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Suite manifest must be a mapping: {resolved_path}")
        return payload

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("YAML suite manifests require PyYAML to be installed.") from exc

    payload = yaml.safe_load(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Suite manifest must be a mapping: {resolved_path}")
    return payload


def _ordered_unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _resolve_suite_repo_names(
    *,
    suite_path: Path,
    catalog_by_name: dict[str, ExrepoSpec],
    exrepo_root: Path,
) -> list[str]:
    manifest = _load_suite_manifest(suite_path)
    runs = manifest.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("Suite manifest must define a non-empty 'runs' list.")

    resolved_suite_path = suite_path.expanduser().resolve(strict=False)
    resolved_exrepo_root = exrepo_root.expanduser().resolve(strict=False)
    selected_names: list[str] = []
    for index, run_entry in enumerate(runs, start=1):
        if not isinstance(run_entry, dict):
            raise ValueError(f"Suite run #{index} must be a mapping.")
        repo_value = run_entry.get("repo")
        if not repo_value:
            raise ValueError(f"Suite run #{index} is missing 'repo'.")
        raw_repo_value = str(repo_value).strip()
        if not raw_repo_value:
            raise ValueError(f"Suite run #{index} has an empty 'repo'.")

        if _is_path_like(raw_repo_value):
            candidate = Path(raw_repo_value).expanduser()
            if candidate.is_absolute():
                resolved_repo_path = candidate.resolve(strict=False)
            else:
                resolved_repo_path = (resolved_suite_path.parent / candidate).resolve(strict=False)
            if resolved_repo_path.parent != resolved_exrepo_root:
                raise ValueError(
                    "Suite repo path must resolve to a direct child of the tmp exrepo root: "
                    f"{raw_repo_value!r} -> {resolved_repo_path}"
                )
            target_name = resolved_repo_path.name
            if target_name not in catalog_by_name:
                raise ValueError(
                    "Suite repo basename is not in the repo catalog: "
                    f"{raw_repo_value!r} -> {target_name!r}"
                )
            selected_names.append(target_name)
            continue

        if raw_repo_value not in catalog_by_name:
            raise ValueError(
                f"Suite repo {raw_repo_value!r} is not a known local repo target from --repo-list."
            )
        selected_names.append(raw_repo_value)

    return _ordered_unique(selected_names)


def select_exrepo_specs(
    specs: list[ExrepoSpec],
    *,
    selected_repo_names: list[str],
    suite_path: Path | None,
    exrepo_root: Path,
) -> list[ExrepoSpec]:
    catalog_by_name = {spec.target_dirname: spec for spec in specs}
    if selected_repo_names:
        names = _ordered_unique([value.strip() for value in selected_repo_names if value.strip()])
        selected_specs: list[ExrepoSpec] = []
        for name in names:
            spec = catalog_by_name.get(name)
            if spec is None:
                raise ValueError(
                    f"Unknown local repo target {name!r}. Use names from --repo-list only."
                )
            selected_specs.append(spec)
        return selected_specs

    if suite_path is not None:
        selected_names = _resolve_suite_repo_names(
            suite_path=suite_path,
            catalog_by_name=catalog_by_name,
            exrepo_root=exrepo_root,
        )
        return [catalog_by_name[name] for name in selected_names]

    return specs


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        specs = load_exrepo_specs(args.repo_list)
        exrepo_root = resolve_tmp_exrepos_root(repo_root=args.repo_root, temp_root=args.temp_root)
        selected_specs = select_exrepo_specs(
            specs,
            selected_repo_names=args.repo,
            suite_path=args.suite,
            exrepo_root=exrepo_root,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    exrepo_root.mkdir(parents=True, exist_ok=True)
    print(f"tmp_exrepo_root: {exrepo_root}")

    failures: list[str] = []
    for spec in selected_specs:
        try:
            target_dir = _resolve_target_dir(spec, exrepo_root)
            action = sync_exrepo(spec, exrepo_root, mode=args.command)
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
