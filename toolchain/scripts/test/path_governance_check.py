#!/usr/bin/env python3
"""Run lightweight governance checks for path layout and AGENTS-based routing."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
AGENTS_CONTRACT_DOC = "AGENTS.md"
KNOWLEDGE_README = "docs/knowledge/README.md"
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
    KNOWLEDGE_README,
    "docs/knowledge/foundations/README.md",
    "docs/knowledge/memory-side/README.md",
    "docs/knowledge/task-interface/README.md",
    "docs/operations/README.md",
    "docs/operations/deploy/README.md",
    "docs/operations/memory-side/README.md",
    "docs/operations/prompt-templates/README.md",
    "docs/operations/task-interface/README.md",
    "docs/operations/path-governance-checks.md",
    "docs/knowledge/foundations/root-directory-layering.md",
    "toolchain/toolchain-layering.md",
    "product/README.md",
    "product/harness-operations/README.md",
    "product/harness-operations/skills/README.md",
    "product/harness-operations/adapters/README.md",
    "product/harness-operations/manifests/README.md",
    "product/memory-side/README.md",
    "product/memory-side/skills/README.md",
    "product/memory-side/adapters/README.md",
    "toolchain/README.md",
    "toolchain/scripts/README.md",
    "toolchain/scripts/test/README.md",
    "toolchain/evals/README.md",
    "toolchain/evals/memory-side/README.md",
]
AGENTS_CONTRACT_BACKLINK_PATHS = [
    "AGENTS.md",
    "README.md",
    "INDEX.md",
    "GUIDE.md",
    "ROADMAP.md",
    "docs/README.md",
    KNOWLEDGE_README,
    "docs/knowledge/foundations/README.md",
    "docs/operations/README.md",
    "docs/operations/path-governance-checks.md",
    ".nav/README.md",
]
ENTRYPOINT_LINK_RULES = {
    "AGENTS.md": [
        KNOWLEDGE_README,
    ],
    "README.md": [
        KNOWLEDGE_README,
    ],
    "INDEX.md": [
        KNOWLEDGE_README,
    ],
    "GUIDE.md": [
        KNOWLEDGE_README,
    ],
    "ROADMAP.md": [
        KNOWLEDGE_README,
    ],
    "docs/README.md": [
        KNOWLEDGE_README,
    ],
    "docs/operations/README.md": [
        KNOWLEDGE_README,
        "docs/operations/deploy/README.md",
        "docs/operations/prompt-templates/README.md",
        "docs/operations/memory-side/README.md",
        "docs/operations/task-interface/README.md",
    ],
    "docs/operations/prompt-templates/README.md": [
        KNOWLEDGE_README,
        "product/harness-operations/README.md",
    ],
    "product/README.md": [
        "product/memory-side/README.md",
        "product/task-interface/README.md",
        "product/harness-operations/README.md",
    ],
    "docs/reference/README.md": [
        KNOWLEDGE_README,
    ],
    KNOWLEDGE_README: [
        "docs/knowledge/foundations/README.md",
        "docs/knowledge/memory-side/README.md",
        "docs/knowledge/task-interface/README.md",
    ],
    "docs/knowledge/foundations/README.md": [
        "docs/knowledge/foundations/root-directory-layering.md",
        "toolchain/toolchain-layering.md",
        AGENTS_CONTRACT_DOC,
    ],
    "docs/knowledge/memory-side/README.md": [
        "docs/knowledge/memory-side/overview.md",
        "docs/knowledge/memory-side/layer-boundary.md",
        "docs/knowledge/memory-side/knowledge-base.md",
        "docs/knowledge/memory-side/context-routing.md",
        "docs/knowledge/memory-side/context-routing-rules.md",
        "docs/knowledge/memory-side/writeback-cleanup.md",
        "docs/knowledge/memory-side/writeback-cleanup-rules.md",
        "docs/knowledge/memory-side/skill-agent-model.md",
        "docs/knowledge/memory-side/formats/context-routing-output-format.md",
        "docs/knowledge/memory-side/formats/writeback-cleanup-output-format.md",
        "docs/knowledge/memory-side/prompts/knowledge-base-adapter-prompt.md",
        "docs/knowledge/memory-side/prompts/context-routing-adapter-prompt.md",
        "docs/knowledge/memory-side/prompts/writeback-cleanup-adapter-prompt.md",
        "docs/knowledge/memory-side/skills/knowledge-base-skill.md",
        "docs/knowledge/memory-side/skills/context-routing-skill.md",
        "docs/knowledge/memory-side/skills/writeback-cleanup-skill.md",
    ],
    "docs/knowledge/task-interface/README.md": [
        "docs/knowledge/task-interface/task-contract.md",
        "docs/knowledge/task-interface/skills/task-contract-skill.md",
    ],
}
REQUIRED_GITIGNORE_ENTRIES = [
    ".agents/",
    ".claude/",
    ".opencode/",
    ".autoworkflow/",
    ".spec-workflow/",
]
FRONTMATTER_REQUIRED_KEYS = [
    "title",
    "status",
    "updated",
    "owner",
    "last_verified",
]
STATUS_RULES = [
    ("docs/reference/", {"reference"}),
    ("docs/knowledge/", {"active", "draft", "superseded"}),
    ("docs/operations/", {"active", "draft", "superseded"}),
]
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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
        description="Validate AGENTS routing contract, main entrypoints, and lightweight markdown links."
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


def to_relative_posix(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


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


def check_required_backlinks(
    repo_root: Path,
    report: CheckReport,
    *,
    label: str,
    target_relative_path: str,
    backlink_paths: list[str],
) -> None:
    for relative_path in backlink_paths:
        path = repo_root / relative_path
        if not path.exists():
            report.add_failure(f"missing {label} backlink consumer: {relative_path}")
            continue
        if not file_links_to(repo_root, path, target_relative_path):
            report.add_failure(
                f"missing {label} backlink: {relative_path} -> {target_relative_path}"
            )
    report.add_info(f"checked {len(backlink_paths)} {label} backlinks")


def parse_frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None

    frontmatter: dict[str, str] = {}
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            return frontmatter
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"')
    return None


def iter_substantive_docs(repo_root: Path) -> list[Path]:
    docs_root = repo_root / "docs"
    return sorted(path for path in docs_root.rglob("*.md") if path.name != "README.md")


def expected_statuses(relative_path: str) -> set[str] | None:
    for prefix, statuses in STATUS_RULES:
        if relative_path.startswith(prefix):
            return statuses
    return None


def check_docs_frontmatter(repo_root: Path, report: CheckReport) -> None:
    docs_files = iter_substantive_docs(repo_root)
    for doc_path in docs_files:
        relative_path = to_relative_posix(doc_path, repo_root)
        text = doc_path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(text)

        if frontmatter is None:
            report.add_failure(f"missing frontmatter: {relative_path}")
            continue

        missing_keys = [
            key for key in FRONTMATTER_REQUIRED_KEYS if not frontmatter.get(key, "").strip()
        ]
        if missing_keys:
            report.add_failure(
                f"missing frontmatter fields: {relative_path} -> {', '.join(missing_keys)}"
            )

        for date_key in ("updated", "last_verified"):
            value = frontmatter.get(date_key, "")
            if value and not DATE_RE.match(value):
                report.add_failure(
                    f"invalid {date_key} value: {relative_path} -> {value}"
                )

        expected = expected_statuses(relative_path)
        status = frontmatter.get("status", "")
        if expected is not None and status not in expected:
            allowed = ", ".join(sorted(expected))
            report.add_failure(
                f"unexpected status for {relative_path}: {status or '<missing>'} "
                f"(expected one of: {allowed})"
            )

    report.add_info(f"checked {len(docs_files)} docs substantive frontmatter blocks")


def check_required_entrypoint_links(repo_root: Path, report: CheckReport) -> None:
    for readme_path, target_paths in ENTRYPOINT_LINK_RULES.items():
        readme = repo_root / readme_path
        if not readme.exists():
            report.add_failure(f"missing entrypoint for link check: {readme_path}")
            continue
        for target_path in target_paths:
            if not file_links_to(repo_root, readme, target_path):
                report.add_failure(
                    f"entrypoint missing document link: {readme_path} -> {target_path}"
                )

    report.add_info(f"checked {len(ENTRYPOINT_LINK_RULES)} entrypoint link groups")


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
    check_required_backlinks(
        repo_root,
        report,
        label="agents-contract",
        target_relative_path=AGENTS_CONTRACT_DOC,
        backlink_paths=AGENTS_CONTRACT_BACKLINK_PATHS,
    )
    check_docs_frontmatter(repo_root, report)
    check_required_entrypoint_links(repo_root, report)
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
