#!/usr/bin/env python3
"""Initialize repo-local harness runtime state from the canonical harness template."""

from __future__ import annotations

import argparse
import contextlib
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_RELATIVE_PATH = Path("product") / "harness-operations" / "manifests" / "harness.template.yaml"
DEFAULT_HARNESS_FILE = ".autoworkflow/harness.yaml"
DEFAULT_STATE_FILE = ".autoworkflow/state/harness-review-loop.json"
DEFAULT_CONTRACT_FILE = ".autoworkflow/contracts/pending.json"
DEFAULT_CLOSEOUT_ROOT = ".autoworkflow/closeout"
DEFAULT_SMOKE_AGENTS_ROOT = ".autoworkflow/smoke/agents/skills"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create harness runtime directories and render harness.yaml from the canonical template."
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--harness-file",
        type=Path,
        default=Path(DEFAULT_HARNESS_FILE),
        help="Harness config path relative to --repo-root unless absolute.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing harness config.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files.")
    return parser.parse_args()


def resolve_harness_file(repo_root: Path, harness_file: Path) -> Path:
    if harness_file.is_absolute():
        return harness_file.resolve()

    resolved = (repo_root / harness_file).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise RuntimeError(
            f"relative harness config path escapes repo root: {harness_file}"
        ) from exc
    return resolved


def resolve_template_path(repo_root: Path) -> Path:
    return repo_root / TEMPLATE_RELATIVE_PATH


def ensure_dir(path: Path, dry_run: bool) -> None:
    if path.exists():
        if not path.is_dir():
            raise RuntimeError(f"Path exists but is not a directory: {path}")
        return
    if dry_run:
        print(f"would create directory {path}")
        return
    path.mkdir(parents=True, exist_ok=True)
    print(f"created directory {path}")


def runtime_path_value(repo_root: Path, absolute_path: Path) -> str:
    """Render runtime paths as repo-relative when possible."""

    with contextlib.suppress(ValueError):
        return str(absolute_path.relative_to(repo_root))
    return str(absolute_path)


def render_harness_template(repo_root: Path, template_text: str, harness_file: Path) -> str:
    """Render the canonical harness template for a concrete runtime root."""

    runtime_root = harness_file.parent
    state_file = runtime_root / "state" / "harness-review-loop.json"
    contract_file = runtime_root / "contracts" / "pending.json"
    closeout_root = runtime_root / "closeout"
    smoke_agents_root = runtime_root / "smoke" / "agents" / "skills"

    rendered = template_text.replace("__REPO_ROOT__", str(repo_root))
    rendered = rendered.replace(DEFAULT_HARNESS_FILE, runtime_path_value(repo_root, harness_file))
    rendered = rendered.replace(DEFAULT_STATE_FILE, runtime_path_value(repo_root, state_file))
    rendered = rendered.replace(DEFAULT_CONTRACT_FILE, runtime_path_value(repo_root, contract_file))
    rendered = rendered.replace(DEFAULT_CLOSEOUT_ROOT, runtime_path_value(repo_root, closeout_root))
    rendered = rendered.replace(
        DEFAULT_SMOKE_AGENTS_ROOT,
        runtime_path_value(repo_root, smoke_agents_root),
    )
    return rendered


def ensure_runtime_dirs(harness_file: Path, dry_run: bool) -> None:
    runtime_root = harness_file.parent
    for path in (
        runtime_root,
        runtime_root / "state",
        runtime_root / "contracts",
        runtime_root / "closeout",
        runtime_root / "smoke" / "agents" / "skills",
    ):
        ensure_dir(path, dry_run)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    template_path = resolve_template_path(repo_root)

    if not template_path.exists():
        print(f"error: missing template file: {template_path}", file=sys.stderr)
        return 1

    try:
        harness_file = resolve_harness_file(repo_root, args.harness_file)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if harness_file.exists() and harness_file.is_dir():
        print(f"error: harness config path is a directory: {harness_file}", file=sys.stderr)
        return 1

    try:
        ensure_runtime_dirs(harness_file, args.dry_run)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if harness_file.exists() and not args.force:
        print(
            f"skip: harness config already exists at {harness_file} "
            "(runtime directories ensured; use --force to overwrite)"
        )
        return 0

    template_text = template_path.read_text(encoding="utf-8")
    rendered = render_harness_template(repo_root, template_text, harness_file)

    if args.dry_run:
        action = "overwrite" if harness_file.exists() else "create"
        print(f"would {action} harness config {harness_file}")
        return 0

    harness_file.write_text(rendered, encoding="utf-8")
    print(f"wrote harness config {harness_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
