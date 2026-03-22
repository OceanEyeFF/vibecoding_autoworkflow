#!/usr/bin/env python3
"""Run lightweight governance checks for path layout and AI routing docs."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PATH_GOVERNANCE_DOC = "docs/knowledge/foundations/path-governance-ai-routing.md"
DEFAULT_SCAN_PATHS = [
    "README.md",
    "INDEX.md",
    "GUIDE.md",
    "ROADMAP.md",
    "AGENTS.md",
    ".nav/README.md",
    "docs",
    "product",
    "toolchain",
]
REQUIRED_ENTRY_PATHS = [
    "AGENTS.md",
    "README.md",
    "INDEX.md",
    "GUIDE.md",
    "ROADMAP.md",
    "docs/README.md",
    "docs/operations/README.md",
    "docs/operations/path-governance-checks.md",
    PATH_GOVERNANCE_DOC,
    "docs/knowledge/foundations/root-directory-layering.md",
    "docs/knowledge/foundations/toolchain-layering.md",
    "product/README.md",
    "product/memory-side/README.md",
    "product/memory-side/skills/README.md",
    "product/memory-side/adapters/README.md",
    "toolchain/README.md",
    "toolchain/scripts/README.md",
    "toolchain/scripts/test/README.md",
    "toolchain/evals/README.md",
    "toolchain/evals/memory-side/README.md",
]
REQUIRED_BACKLINK_PATHS = [
    "AGENTS.md",
    "README.md",
    "INDEX.md",
    "GUIDE.md",
    "ROADMAP.md",
    "docs/README.md",
    "docs/knowledge/foundations/root-directory-layering.md",
    ".nav/README.md",
]
REQUIRED_GITIGNORE_ENTRIES = [
    ".agents/",
    ".claude/",
    ".autoworkflow/",
    ".spec-workflow/",
]
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


@dataclass
class CheckReport:
    failures: list[str] = field(default_factory=list)
    infos: list[str] = field(default_factory=list)

    def add_failure(self, message: str) -> None:
        self.failures.append(message)

    def add_info(self, message: str) -> None:
        self.infos.append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate path-governance docs, main entrypoints, and lightweight markdown links."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Override the repository root used for checks.",
    )
    parser.add_argument(
        "--scan-path",
        action="append",
        default=[],
        help="Additional file or directory to scan for markdown relative links.",
    )
    return parser.parse_args()


def iter_markdown_files(repo_root: Path, scan_paths: list[str]) -> list[Path]:
    markdown_files: list[Path] = []
    seen: set[Path] = set()
    for raw_path in scan_paths:
        path = repo_root / raw_path
        if not path.exists():
            continue
        if path.is_dir():
            candidates = sorted(path.rglob("*.md"))
        else:
            candidates = [path]
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                markdown_files.append(candidate)
    return markdown_files


def iter_relative_markdown_targets(text: str) -> list[str]:
    targets: list[str] = []
    for match in MARKDOWN_LINK_RE.findall(text):
        target = match.strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1].strip()
        if not target:
            continue
        if target.startswith(("#", "http://", "https://", "mailto:", "tel:")):
            continue
        if "://" in target:
            continue
        path_part = target.split("#", 1)[0].strip()
        if not path_part:
            continue
        targets.append(path_part)
    return targets


def resolve_markdown_target(markdown_file: Path, repo_root: Path, target: str) -> Path:
    if target.startswith("/"):
        return (repo_root / target.lstrip("/")).resolve()
    return (markdown_file.parent / target).resolve()


def check_markdown_links(repo_root: Path, report: CheckReport, scan_paths: list[str]) -> None:
    markdown_files = iter_markdown_files(repo_root, scan_paths)
    checked_links = 0
    for markdown_file in markdown_files:
        text = markdown_file.read_text(encoding="utf-8")
        for target in iter_relative_markdown_targets(text):
            checked_links += 1
            resolved = resolve_markdown_target(markdown_file, repo_root, target)
            if not resolved.exists():
                relative_file = markdown_file.relative_to(repo_root)
                report.add_failure(f"broken markdown link: {relative_file} -> {target}")
    report.add_info(f"checked {checked_links} markdown relative links")


def file_links_to(repo_root: Path, markdown_file: Path, target_relative_path: str) -> bool:
    target_path = (repo_root / target_relative_path).resolve()
    text = markdown_file.read_text(encoding="utf-8")
    if target_relative_path in text or target_path.name in text:
        return True
    for target in iter_relative_markdown_targets(text):
        if resolve_markdown_target(markdown_file, repo_root, target) == target_path:
            return True
    return False


def check_required_entrypoints(repo_root: Path, report: CheckReport) -> None:
    for relative_path in REQUIRED_ENTRY_PATHS:
        if not (repo_root / relative_path).exists():
            report.add_failure(f"missing required entrypoint: {relative_path}")
    report.add_info(f"checked {len(REQUIRED_ENTRY_PATHS)} required entrypoints")


def check_path_governance_backlinks(repo_root: Path, report: CheckReport) -> None:
    for relative_path in REQUIRED_BACKLINK_PATHS:
        path = repo_root / relative_path
        if not path.exists():
            report.add_failure(f"missing backlink consumer: {relative_path}")
            continue
        if not file_links_to(repo_root, path, PATH_GOVERNANCE_DOC):
            report.add_failure(
                f"missing path-governance backlink: {relative_path} -> {PATH_GOVERNANCE_DOC}"
            )
    report.add_info(f"checked {len(REQUIRED_BACKLINK_PATHS)} path-governance backlinks")


def check_gitignore(repo_root: Path, report: CheckReport) -> None:
    gitignore_path = repo_root / ".gitignore"
    if not gitignore_path.exists():
        report.add_failure("missing .gitignore")
        return
    lines = {
        line.strip()
        for line in gitignore_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    for entry in REQUIRED_GITIGNORE_ENTRIES:
        if entry not in lines:
            report.add_failure(f"missing .gitignore entry: {entry}")
    report.add_info(f"checked {len(REQUIRED_GITIGNORE_ENTRIES)} .gitignore entries")


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    report = CheckReport()

    scan_paths = DEFAULT_SCAN_PATHS + args.scan_path
    check_markdown_links(repo_root, report, scan_paths)
    check_required_entrypoints(repo_root, report)
    check_path_governance_backlinks(repo_root, report)
    check_gitignore(repo_root, report)

    for info in report.infos:
        print(f"info: {info}")

    if report.failures:
        print("governance checks failed:")
        for failure in report.failures:
            print(f"- {failure}")
        return 1

    print("governance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
