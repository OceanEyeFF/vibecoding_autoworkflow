#!/usr/bin/env python3
"""Deploy repo adapter sources to repo-local or global skill roots."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PRODUCT_ROOT = REPO_ROOT / "product"
PRODUCT_PARTITIONS = ("memory-side", "task-interface")
LOCAL_TARGET_ROOTS = {
    "claude": REPO_ROOT / ".claude" / "skills",
    "agents": REPO_ROOT / ".agents" / "skills",
}


class DeployError(RuntimeError):
    """Raised when deployment inputs or targets are invalid."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deploy repo adapter sources to local mounts or global skill roots."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    for mode in ("local", "global"):
        subparser = subparsers.add_parser(mode)
        subparser.add_argument(
            "--backend",
            choices=("all", "claude", "agents"),
            default="all",
            help="Which backend adapters to deploy.",
        )
        subparser.add_argument(
            "--method",
            choices=("symlink", "copy"),
            default="symlink" if mode == "local" else "copy",
            help="How to materialize the deploy target.",
        )
        subparser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print planned actions without changing files.",
        )
        subparser.add_argument(
            "--create-roots",
            action="store_true",
            help="Allow creating missing target roots for global deployment.",
        )
        subparser.add_argument(
            "--claude-root",
            type=Path,
            help="Override the Claude skills target root.",
        )
        subparser.add_argument(
            "--agents-root",
            type=Path,
            help="Override the Agents/Codex skills target root.",
        )

    return parser.parse_args()


def iter_backends(selected: str) -> list[str]:
    if selected == "all":
        return ["claude", "agents"]
    return [selected]


def source_roots_for(backend: str) -> list[Path]:
    source_roots = []
    for partition in PRODUCT_PARTITIONS:
        source_root = PRODUCT_ROOT / partition / "adapters" / backend / "skills"
        if source_root.is_dir():
            source_roots.append(source_root)

    if not source_roots:
        raise DeployError(f"Missing source roots for {backend} under {PRODUCT_ROOT}")
    return source_roots


def global_target_root_for(backend: str, args: argparse.Namespace) -> Path:
    if backend == "claude":
        return args.claude_root or (Path.home() / ".claude" / "skills")

    if args.agents_root:
        return args.agents_root

    codex_home = os.environ.get("CODEX_HOME")
    if not codex_home:
        raise DeployError("CODEX_HOME is not set. Use --agents-root or export CODEX_HOME.")
    return Path(codex_home) / "skills"


def target_root_for(backend: str, args: argparse.Namespace) -> Path:
    if args.mode == "local":
        return LOCAL_TARGET_ROOTS[backend]
    return global_target_root_for(backend, args)


def ensure_target_root(path: Path, args: argparse.Namespace) -> None:
    if path.exists():
        if not path.is_dir():
            raise DeployError(f"Target root exists but is not a directory: {path}")
        return

    should_create = args.mode == "local" or args.create_roots
    if not should_create:
        raise DeployError(
            f"Target root does not exist: {path}. Re-run with --create-roots if you want to create it."
        )

    if args.dry_run:
        print(f"would create target root {path}")
        return

    path.mkdir(parents=True, exist_ok=True)
    print(f"created target root {path}")


def remove_existing_path(path: Path, dry_run: bool) -> None:
    if not path.exists() and not path.is_symlink():
        return

    if dry_run:
        print(f"would remove {path}")
        return

    if path.is_symlink() or path.is_file():
        path.unlink()
        return

    shutil.rmtree(path)


def deploy_one(source_path: Path, target_path: Path, method: str, dry_run: bool) -> None:
    remove_existing_path(target_path, dry_run)

    if method == "symlink":
        link_target = Path(os.path.relpath(source_path, start=target_path.parent))
        if dry_run:
            print(f"would symlink {target_path} -> {link_target}")
            return
        target_path.symlink_to(link_target, target_is_directory=True)
        print(f"symlinked {target_path} -> {link_target}")
        return

    if dry_run:
        print(f"would copy {source_path} -> {target_path}")
        return

    shutil.copytree(source_path, target_path)
    print(f"copied {source_path} -> {target_path}")


def deploy_backend(backend: str, args: argparse.Namespace) -> None:
    target_root = target_root_for(backend, args)
    ensure_target_root(target_root, args)

    for source_root in source_roots_for(backend):
        for source_path in sorted(path for path in source_root.iterdir() if path.is_dir()):
            target_path = target_root / source_path.name
            deploy_one(source_path, target_path, args.method, args.dry_run)


def main() -> int:
    args = parse_args()
    try:
        for backend in iter_backends(args.backend):
            deploy_backend(backend, args)
    except DeployError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
