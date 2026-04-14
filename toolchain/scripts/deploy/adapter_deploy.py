#!/usr/bin/env python3
"""Build, deploy, and verify repo adapter sources for local/global skill targets."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PRODUCT_ROOT = REPO_ROOT / "product"
PRODUCT_PARTITIONS = ("memory-side", "task-interface")
LOCAL_TARGET_ROOTS = {
    "claude": REPO_ROOT / ".claude" / "skills",
    "agents": REPO_ROOT / ".agents" / "skills",
    "opencode": REPO_ROOT / ".opencode" / "skills",
}
DEFAULT_BUILD_ROOT = REPO_ROOT / ".autoworkflow" / "build" / "adapter-sources"


class DeployError(RuntimeError):
    """Raised when deployment inputs or targets are invalid."""


@dataclass
class VerifyIssue:
    """One verification problem detected for a deploy target."""

    code: str
    path: Path
    detail: str


@dataclass
class VerifyResult:
    """Collected verification state for one backend target."""

    backend: str
    target_scope: str
    target_root: Path
    issues: list[VerifyIssue]


def add_backend_args(subparser: argparse.ArgumentParser) -> None:
    """Add the shared backend selector."""

    subparser.add_argument(
        "--backend",
        choices=("all", "claude", "agents", "opencode"),
        default="all",
        help="Which backend adapters to target.",
    )


def add_build_root_arg(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument(
        "--build-root",
        type=Path,
        default=DEFAULT_BUILD_ROOT,
        help="Directory used for assembled adapter sources.",
    )


def add_target_override_args(subparser: argparse.ArgumentParser) -> None:
    """Add backend-specific target root overrides."""

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
    subparser.add_argument(
        "--opencode-root",
        type=Path,
        help="Override the OpenCode skills target root.",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build, deploy, and verify repo adapter sources for local mounts or global skill roots."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    build_parser = subparsers.add_parser("build")
    add_backend_args(build_parser)
    add_build_root_arg(build_parser)
    build_parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove backend build root before assembling skills.",
    )
    build_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without changing files.",
    )

    for mode in ("local", "global"):
        subparser = subparsers.add_parser(mode)
        add_backend_args(subparser)
        add_build_root_arg(subparser)
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
            "--prune",
            action="store_true",
            help="Remove unexpected target entries before syncing expected adapter mounts.",
        )
        subparser.add_argument(
            "--create-roots",
            action="store_true",
            help="Allow creating missing target roots for global deployment.",
        )
        add_target_override_args(subparser)

    verify_parser = subparsers.add_parser("verify")
    add_backend_args(verify_parser)
    add_build_root_arg(verify_parser)
    add_target_override_args(verify_parser)
    verify_parser.add_argument(
        "--target",
        choices=("local", "global"),
        default="local",
        help="Which target scope to verify. Defaults to local repo mounts.",
    )

    return parser.parse_args()


def iter_backends(selected: str) -> list[str]:
    if selected == "all":
        return ["claude", "agents", "opencode"]
    return [selected]


def resolve_build_root(args: argparse.Namespace) -> Path:
    build_root = args.build_root
    if not build_root.is_absolute():
        return (REPO_ROOT / build_root).resolve()
    return build_root.resolve()


def build_backend_root_for(backend: str, args: argparse.Namespace) -> Path:
    return resolve_build_root(args) / backend


def source_roots_for(backend: str) -> list[tuple[str, Path]]:
    source_roots: list[tuple[str, Path]] = []
    for partition in PRODUCT_PARTITIONS:
        source_root = PRODUCT_ROOT / partition / "adapters" / backend / "skills"
        if source_root.is_dir():
            source_roots.append((partition, source_root))

    if not source_roots:
        raise DeployError(f"Missing source roots for {backend} under {PRODUCT_ROOT}")
    return source_roots


def remove_existing_path(path: Path, dry_run: bool, action: str = "remove") -> None:
    if not path.exists() and not path.is_symlink():
        return

    if dry_run:
        print(f"would {action} {path}")
        return

    if path.is_symlink() or path.is_file():
        path.unlink()
        return

    shutil.rmtree(path)


def expected_sources_for(
    backend: str,
    args: argparse.Namespace,
    *,
    dry_run: bool,
    allow_build: bool = True,
) -> tuple[dict[str, Path], int]:
    """Map expected target entry names to their adapter source directories."""
    del args, dry_run, allow_build
    return source_entries_for(backend), 0


def source_entries_for(backend: str) -> dict[str, Path]:
    """Map expected target entry names to canonical adapter source directories."""

    expected: dict[str, Path] = {}
    for partition, source_root in source_roots_for(backend):
        for source_path in sorted(path for path in source_root.iterdir() if path.is_dir()):
            expected[source_path.name] = source_path
    return expected


def global_target_root_for(backend: str, args: argparse.Namespace) -> Path:
    if backend == "claude":
        return args.claude_root or (Path.home() / ".claude" / "skills")

    if backend == "opencode":
        if args.opencode_root:
            return args.opencode_root
        xdg_config_home = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
        return xdg_config_home / "opencode" / "skills"

    if backend == "agents":
        if args.agents_root:
            return args.agents_root

        codex_home = os.environ.get("CODEX_HOME")
        if not codex_home:
            raise DeployError("CODEX_HOME is not set. Use --agents-root or export CODEX_HOME.")
        return Path(codex_home) / "skills"

    raise DeployError(f"Unsupported backend target root resolution: {backend}")


def target_scope_for(args: argparse.Namespace) -> str:
    """Resolve which target scope the current command should operate on."""

    if args.mode in ("local", "global"):
        return args.mode
    return args.target


def target_root_for(backend: str, args: argparse.Namespace) -> Path:
    if target_scope_for(args) == "local":
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


def prune_unexpected_targets(target_root: Path, expected_names: set[str], dry_run: bool) -> None:
    """Remove stale target entries when deploy runs with --prune."""

    if not target_root.exists() or not target_root.is_dir():
        return

    for target_path in sorted(path for path in target_root.iterdir() if path.name not in expected_names):
        remove_existing_path(target_path, dry_run, action="prune")


def build_backend(backend: str, args: argparse.Namespace) -> None:
    build_backend_root = build_backend_root_for(backend, args)
    if args.clean:
        remove_existing_path(build_backend_root, args.dry_run, action="clean")
    print(f"[{backend}] no build step required for current source partitions")


def deploy_backend(backend: str, args: argparse.Namespace) -> None:
    target_root = target_root_for(backend, args)
    ensure_target_root(target_root, args)
    expected_sources, _ = expected_sources_for(backend, args, dry_run=args.dry_run)

    if args.prune:
        prune_unexpected_targets(target_root, set(expected_sources), args.dry_run)

    for name, source_path in expected_sources.items():
        target_path = target_root / name
        deploy_one(source_path, target_path, args.method, args.dry_run)


def verify_target_root(backend: str, target_root: Path) -> list[VerifyIssue]:
    """Check that the target root exists and has the right type."""

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

    if target_root.is_symlink():
        return [
            VerifyIssue(
                code="broken-target-root-symlink",
                path=target_root,
                detail="target root is a broken symlink",
            )
        ]

    return [
        VerifyIssue(
            code="missing-target-root",
            path=target_root,
            detail=f"{backend} target root does not exist",
        )
    ]


def verify_local_target(target_path: Path, source_path: Path) -> list[VerifyIssue]:
    """Validate one repo-local mount entry."""

    issues: list[VerifyIssue] = []
    expected_link = Path(os.path.relpath(source_path, start=target_path.parent))

    if not target_path.is_symlink():
        found_type = "directory" if target_path.is_dir() else "file"
        issues.append(
            VerifyIssue(
                code="wrong-target-type",
                path=target_path,
                detail=f"expected symlink, found {found_type}",
            )
        )
        return issues

    if not target_path.exists():
        issues.append(
            VerifyIssue(
                code="broken-symlink",
                path=target_path,
                detail=f"symlink target is missing; expected {expected_link}",
            )
        )

    actual_link = Path(os.readlink(target_path))
    if actual_link != expected_link:
        issues.append(
            VerifyIssue(
                code="wrong-symlink-target",
                path=target_path,
                detail=f"expected {expected_link}, found {actual_link}",
            )
        )
    return issues


def verify_global_target(target_path: Path) -> list[VerifyIssue]:
    """Validate one global copied target entry."""

    issues: list[VerifyIssue] = []

    if target_path.is_symlink():
        issues.append(
            VerifyIssue(
                code="wrong-target-type",
                path=target_path,
                detail="expected directory copy, found symlink",
            )
        )
        if not target_path.exists():
            issues.append(
                VerifyIssue(
                    code="broken-symlink",
                    path=target_path,
                    detail="global target symlink is broken",
                )
            )
        return issues

    if not target_path.is_dir():
        issues.append(
            VerifyIssue(
                code="wrong-target-type",
                path=target_path,
                detail="expected directory copy, found file",
            )
        )
    return issues


def verify_directory_content(
    actual_root: Path,
    expected_files: dict[Path, bytes],
    *,
    missing_code: str,
    stale_code: str,
    unexpected_code: str,
) -> list[VerifyIssue]:
    """Compare one directory tree against expected file snapshot."""

    issues: list[VerifyIssue] = []
    actual_files = collected_file_bytes(actual_root)

    for relative_path in sorted(expected_files):
        expected_content = expected_files[relative_path]
        actual_content = actual_files.get(relative_path)
        if actual_content is None:
            issues.append(
                VerifyIssue(
                    code=missing_code,
                    path=actual_root / relative_path,
                    detail=f"missing copied file from source snapshot: {relative_path}",
                )
            )
            continue

        if expected_content != actual_content:
            issues.append(
                VerifyIssue(
                    code=stale_code,
                    path=actual_root / relative_path,
                    detail=f"content differs from source snapshot for {relative_path}",
                )
            )

    for relative_path in sorted(actual_files):
        if relative_path not in expected_files:
            issues.append(
                VerifyIssue(
                    code=unexpected_code,
                    path=actual_root / relative_path,
                    detail=f"file exists in target but not in source snapshot: {relative_path}",
                )
            )
    return issues


def collected_file_bytes(root: Path, *, skip_paths: set[Path] | None = None) -> dict[Path, bytes]:
    """Collect regular files under one directory, keyed by relative path."""

    skipped = skip_paths or set()
    files: dict[Path, bytes] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if relative in skipped:
            continue
        files[relative] = path.read_bytes()
    return files


def expected_global_source_snapshot(backend: str, source_path: Path) -> dict[Path, bytes]:
    """Build expected file snapshot for one source directory in global copy mode."""
    del backend
    return collected_file_bytes(source_path)


def verify_global_target_content(target_path: Path, expected_files: dict[Path, bytes]) -> list[VerifyIssue]:
    """Compare one global copied target directory against expected file snapshot."""

    return verify_directory_content(
        target_path,
        expected_files,
        missing_code="missing-target-file",
        stale_code="stale-target-file",
        unexpected_code="unexpected-target-file",
    )


def verify_backend(backend: str, args: argparse.Namespace) -> VerifyResult:
    """Compare a deployed backend target against expected adapter directories."""

    target_scope = target_scope_for(args)
    target_root = target_root_for(backend, args)
    source_entries: dict[str, Path] | None = None
    if target_scope == "local":
        source_entries = source_entries_for(backend)
        expected_sources, _ = expected_sources_for(
            backend,
            args,
            dry_run=False,
            allow_build=False,
        )
    else:
        expected_sources = source_entries_for(backend)
    issues = verify_target_root(backend, target_root)

    if issues:
        return VerifyResult(
            backend=backend,
            target_scope=target_scope,
            target_root=target_root,
            issues=issues,
        )

    actual_targets = {path.name: path for path in target_root.iterdir()}
    for name in sorted(expected_sources):
        source_path = expected_sources[name]
        if not source_path.exists():
            issues.append(
                VerifyIssue(
                    code="missing-source-entry",
                    path=source_path,
                    detail=f"expected source adapter directory is missing for {name}",
                )
            )
            continue

        target_path = target_root / name
        if name not in actual_targets:
            issues.append(
                VerifyIssue(
                    code="missing-target-entry",
                    path=target_path,
                    detail=f"missing expected {backend} mount entry {name}",
                )
            )
            continue

        if target_scope == "local":
            issues.extend(
                verify_local_target(
                    target_path,
                    source_path,
                )
            )
        else:
            issues.extend(verify_global_target(target_path))
            issues.extend(
                verify_global_target_content(
                    target_path,
                    expected_global_source_snapshot(backend, source_path),
                )
            )

    for name in sorted(actual_targets):
        if name not in expected_sources:
            issues.append(
                VerifyIssue(
                    code="unexpected-target-entry",
                    path=actual_targets[name],
                    detail=f"no matching source adapter exists for {name}",
                )
            )

    return VerifyResult(
        backend=backend,
        target_scope=target_scope,
        target_root=target_root,
        issues=issues,
    )


def print_verify_result(result: VerifyResult) -> None:
    """Render one concise backend verification summary."""

    scope_label = f"{result.target_scope} target"
    if not result.issues:
        print(f"[{result.backend}] ok: {scope_label} is in sync at {result.target_root}")
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

        if args.mode == "build":
            for backend in iter_backends(args.backend):
                build_backend(backend, args)
            return 0

        for backend in iter_backends(args.backend):
            deploy_backend(backend, args)
    except DeployError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
