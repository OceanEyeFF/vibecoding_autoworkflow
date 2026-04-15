#!/usr/bin/env python3
"""Runtime deploy endpoints for agents skill target roots."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
LOCAL_TARGET_ROOTS = {
    "agents": REPO_ROOT / ".agents" / "skills",
}


class DeployError(RuntimeError):
    """Raised when deployment inputs or targets are invalid."""


@dataclass
class VerifyIssue:
    """One verification problem detected for a deploy target root."""

    code: str
    path: Path
    detail: str


@dataclass
class VerifyResult:
    """Collected verification state for one backend target root."""

    backend: str
    target_scope: str
    target_root: Path
    issues: list[VerifyIssue]


def add_backend_args(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument(
        "--backend",
        choices=("agents",),
        default="agents",
        help="Which backend target to operate on. Only agents is implemented.",
    )


def add_target_override_args(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument(
        "--agents-root",
        type=Path,
        help="Override the Agents/Codex skills target root.",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage runtime endpoints for agents skill target roots."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    local_parser = subparsers.add_parser("local")
    add_backend_args(local_parser)
    local_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without changing files.",
    )

    global_parser = subparsers.add_parser("global")
    add_backend_args(global_parser)
    global_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without changing files.",
    )
    global_parser.add_argument(
        "--create-roots",
        action="store_true",
        help="Allow creating missing target roots for global runtime endpoints.",
    )
    add_target_override_args(global_parser)

    verify_parser = subparsers.add_parser("verify")
    add_backend_args(verify_parser)
    add_target_override_args(verify_parser)
    verify_parser.add_argument(
        "--target",
        choices=("local", "global"),
        default="local",
        help="Which target scope to verify. Defaults to local repo endpoints.",
    )

    return parser.parse_args()


def iter_backends(selected: str) -> list[str]:
    return [selected]


def global_target_root_for(backend: str, args: argparse.Namespace) -> Path:
    if backend == "agents":
        if args.agents_root:
            return args.agents_root

        codex_home = os.environ.get("CODEX_HOME")
        if not codex_home:
            raise DeployError("CODEX_HOME is not set. Use --agents-root or export CODEX_HOME.")
        return Path(codex_home) / "skills"

    raise DeployError(f"Unsupported backend target root resolution: {backend}")


def target_scope_for(args: argparse.Namespace) -> str:
    if args.mode in ("local", "global"):
        return args.mode
    return args.target


def target_root_for(backend: str, args: argparse.Namespace) -> Path:
    if target_scope_for(args) == "local":
        return LOCAL_TARGET_ROOTS[backend]
    return global_target_root_for(backend, args)


def ensure_target_root(path: Path, args: argparse.Namespace) -> None:
    if path.is_symlink():
        if path.exists():
            raise DeployError(f"Target root must be a real directory, not a symlink: {path}")
        raise DeployError(f"Target root is a broken symlink: {path}")

    if path.exists():
        if not path.is_dir():
            raise DeployError(f"Target root exists but is not a directory: {path}")
        print(f"ready target root {path}")
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


def activate_runtime_endpoint(backend: str, args: argparse.Namespace) -> None:
    target_root = target_root_for(backend, args)
    ensure_target_root(target_root, args)


def verify_target_root(backend: str, target_root: Path) -> list[VerifyIssue]:
    if target_root.is_symlink():
        if target_root.exists():
            return [
                VerifyIssue(
                    code="wrong-target-root-type",
                    path=target_root,
                    detail="target root must be a real directory, not a symlink",
                )
            ]
        return [
            VerifyIssue(
                code="broken-target-root-symlink",
                path=target_root,
                detail="target root is a broken symlink",
            )
        ]

    if target_root.exists():
        if target_root.is_dir():
            return []
        return [
            VerifyIssue(
                code="wrong-target-root-type",
                path=target_root,
                detail="target root exists but is not a directory",
            )
        ]

    return [
        VerifyIssue(
            code="missing-target-root",
            path=target_root,
            detail=f"{backend} target root does not exist",
        )
    ]


def verify_backend(backend: str, args: argparse.Namespace) -> VerifyResult:
    target_scope = target_scope_for(args)
    target_root = target_root_for(backend, args)
    return VerifyResult(
        backend=backend,
        target_scope=target_scope,
        target_root=target_root,
        issues=verify_target_root(backend, target_root),
    )


def print_verify_result(result: VerifyResult) -> None:
    scope_label = f"{result.target_scope} target"
    if not result.issues:
        print(f"[{result.backend}] ok: {scope_label} is ready at {result.target_root}")
        return

    print(
        f"[{result.backend}] drift: {len(result.issues)} issue(s) in {scope_label} at {result.target_root}"
    )
    for issue in result.issues:
        print(f"  - {issue.code}: {issue.path} ({issue.detail})")


def main() -> int:
    args = parse_args()
    try:
        if args.mode == "verify":
            results = [verify_backend(backend, args) for backend in iter_backends(args.backend)]
            for result in results:
                print_verify_result(result)
            return 1 if any(result.issues for result in results) else 0

        for backend in iter_backends(args.backend):
            activate_runtime_endpoint(backend, args)
    except DeployError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
