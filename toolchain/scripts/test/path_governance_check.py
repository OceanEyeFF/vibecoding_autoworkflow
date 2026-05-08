#!/usr/bin/env python3
"""Run lightweight governance checks for path layout and AGENTS-based routing."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
AGENTS_CONTRACT_DOC = "AGENTS.md"
PROJECT_MAINTENANCE_README = "docs/project-maintenance/README.md"
HARNESS_README = "docs/harness/README.md"
DEFAULT_SCAN_PATHS = [
    "README.md",
    "INDEX.md",
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
    "docs/README.md",
    PROJECT_MAINTENANCE_README,
    HARNESS_README,
    "docs/harness/foundations/README.md",
    "docs/harness/foundations/Harness指导思想.md",
    "docs/harness/foundations/Harness运行协议.md",
    "docs/harness/scope/README.md",
    "docs/harness/artifact/README.md",
    "docs/harness/catalog/README.md",
    "docs/harness/catalog/supervisor.md",
    "docs/harness/catalog/repo.md",
    "docs/harness/catalog/worktrack.md",
    "docs/harness/artifact/repo/README.md",
    "docs/harness/artifact/repo/goal-charter.md",
    "docs/harness/artifact/repo/snapshot-status.md",
    "docs/harness/artifact/worktrack/README.md",
    "docs/harness/artifact/worktrack/contract.md",
    "docs/harness/artifact/worktrack/plan-task-queue.md",
    "docs/harness/artifact/worktrack/gate-evidence.md",
    "docs/harness/artifact/control/README.md",
    "docs/harness/artifact/control/control-state.md",
    "docs/harness/artifact/control/goal-change-request.md",
    "docs/harness/workflow-families/README.md",
    "docs/harness/workflow-families/repo-evolution/README.md",
    "docs/project-maintenance/foundations/README.md",
    "docs/project-maintenance/governance/README.md",
    "docs/project-maintenance/deploy/README.md",
    "docs/project-maintenance/testing/README.md",
    "docs/project-maintenance/usage-help/README.md",
    "docs/project-maintenance/governance/path-governance-checks.md",
    "docs/project-maintenance/foundations/root-directory-layering.md",
    "toolchain/toolchain-layering.md",
    "product/README.md",
    "product/harness/README.md",
    "product/harness/skills/README.md",
    "product/harness/adapters/README.md",
    "toolchain/README.md",
    "toolchain/scripts/README.md",
    "toolchain/scripts/test/README.md",
]
AGENTS_CONTRACT_BACKLINK_PATHS = [
    "AGENTS.md",
    "README.md",
    "INDEX.md",
    "docs/README.md",
    PROJECT_MAINTENANCE_README,
    HARNESS_README,
    "docs/project-maintenance/foundations/README.md",
    "docs/project-maintenance/governance/path-governance-checks.md",
    ".nav/README.md",
]
ENTRYPOINT_LINK_RULES = {
    "AGENTS.md": [
        "docs/README.md",
    ],
    "README.md": [
        "docs/README.md",
    ],
    "INDEX.md": [
        "docs/README.md",
    ],
    "docs/README.md": [
        PROJECT_MAINTENANCE_README,
        HARNESS_README,
    ],
    HARNESS_README: [
        "docs/harness/foundations/README.md",
        "docs/harness/scope/README.md",
        "docs/harness/artifact/README.md",
        "docs/harness/catalog/README.md",
        "docs/harness/workflow-families/README.md",
        AGENTS_CONTRACT_DOC,
    ],
    "docs/harness/catalog/README.md": [
        "docs/harness/catalog/supervisor.md",
        "docs/harness/catalog/repo.md",
        "docs/harness/catalog/worktrack.md",
        "docs/harness/foundations/Harness指导思想.md",
        "docs/harness/foundations/Harness运行协议.md",
        "product/harness/skills/README.md",
    ],
    "docs/harness/foundations/README.md": [
        "docs/harness/foundations/Harness指导思想.md",
        "docs/harness/foundations/Harness运行协议.md",
    ],
    "docs/harness/scope/README.md": [
        "docs/harness/scope/repo-scope.md",
        "docs/harness/scope/worktrack-scope.md",
        "docs/harness/scope/state-loop.md",
    ],
    "docs/harness/artifact/README.md": [
        "docs/harness/artifact/repo/README.md",
        "docs/harness/artifact/worktrack/README.md",
        "docs/harness/artifact/control/README.md",
    ],
    "docs/harness/artifact/repo/README.md": [
        "docs/harness/artifact/repo/goal-charter.md",
        "docs/harness/artifact/repo/snapshot-status.md",
    ],
    "docs/harness/artifact/worktrack/README.md": [
        "docs/harness/artifact/worktrack/contract.md",
        "docs/harness/artifact/worktrack/plan-task-queue.md",
        "docs/harness/artifact/worktrack/gate-evidence.md",
    ],
    "docs/harness/artifact/control/README.md": [
        "docs/harness/artifact/control/control-state.md",
        "docs/harness/artifact/control/goal-change-request.md",
    ],
    "docs/harness/workflow-families/README.md": [
        "docs/harness/workflow-families/repo-evolution/README.md",
    ],
    "docs/harness/workflow-families/repo-evolution/README.md": [
        "docs/harness/workflow-families/repo-evolution/standard-worktrack.md",
        "docs/harness/workflow-families/repo-evolution/policy-profiles.md",
    ],
    PROJECT_MAINTENANCE_README: [
        "docs/project-maintenance/foundations/README.md",
        "docs/project-maintenance/governance/README.md",
        "docs/project-maintenance/deploy/README.md",
        "docs/project-maintenance/testing/README.md",
        "docs/project-maintenance/usage-help/README.md",
    ],
    "docs/project-maintenance/foundations/README.md": [
        "docs/project-maintenance/foundations/root-directory-layering.md",
        "toolchain/toolchain-layering.md",
        AGENTS_CONTRACT_DOC,
    ],
    "docs/project-maintenance/governance/README.md": [
        "docs/project-maintenance/governance/review-verify-handbook.md",
        "docs/project-maintenance/governance/path-governance-checks.md",
        "docs/project-maintenance/governance/branch-pr-governance.md",
    ],
    "docs/project-maintenance/deploy/README.md": [
        "docs/project-maintenance/deploy/deploy-runbook.md",
        "docs/project-maintenance/deploy/skill-deployment-maintenance.md",
    ],
    "docs/project-maintenance/testing/README.md": [
        "docs/project-maintenance/testing/python-script-test-execution.md",
        "docs/project-maintenance/testing/npx-command-test-execution.md",
        "docs/project-maintenance/testing/codex-post-deploy-behavior-tests.md",
        "docs/project-maintenance/testing/claude-post-deploy-behavior-tests.md",
    ],
    "docs/project-maintenance/usage-help/README.md": [
        "docs/project-maintenance/usage-help/codex.md",
        "docs/project-maintenance/usage-help/claude.md",
    ],
    "product/README.md": [
        "product/harness/README.md",
    ],
    "product/harness/README.md": [
        "docs/harness/README.md",
        "product/harness/skills/README.md",
        "product/harness/adapters/README.md",
    ],
}
REQUIRED_GITIGNORE_ENTRIES = [
    ".aw/",
    ".agents/",
    ".claude/",
    ".autoworkflow/",
    ".spec-workflow/",
    "**/__pycache__/",
    ".pytest_cache/",
    "*.pyc",
    "*.pyo",
]
FRONTMATTER_REQUIRED_KEYS = [
    "title",
    "status",
    "updated",
    "owner",
    "last_verified",
]
STATUS_RULES = [
    ("docs/project-maintenance/", {"active", "draft", "superseded"}),
    ("docs/harness/", {"active", "draft", "superseded"}),
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
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output instead of human-readable text.",
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


_INFO_TOTAL_RE = re.compile(r"checked (\d+)")


def _build_checks_payload(reports: dict[str, CheckReport]) -> dict:
    checks: dict[str, dict] = {}
    for cat, cat_report in reports.items():
        total = 0
        for info in cat_report.infos:
            m = _INFO_TOTAL_RE.match(info)
            if m:
                total += int(m.group(1))
        failed = len(cat_report.failures)
        checks[cat] = {
            "passed": total - failed,
            "failed": failed,
            "errors": cat_report.failures,
        }
    return checks


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()

    reports = {
        "relative_links": CheckReport(),
        "entrypoints": CheckReport(),
        "frontmatter": CheckReport(),
    }

    scan_paths = DEFAULT_SCAN_PATHS + args.scan_path
    check_markdown_links(repo_root, reports["relative_links"], scan_paths)
    check_required_entrypoints(repo_root, reports["entrypoints"])
    check_required_backlinks(
        repo_root,
        reports["entrypoints"],
        label="agents-contract",
        target_relative_path=AGENTS_CONTRACT_DOC,
        backlink_paths=AGENTS_CONTRACT_BACKLINK_PATHS,
    )
    check_docs_frontmatter(repo_root, reports["frontmatter"])
    check_required_entrypoint_links(repo_root, reports["entrypoints"])
    check_gitignore(repo_root, reports["entrypoints"])

    all_failures: list[str] = []
    all_infos: list[str] = []
    for cat_report in reports.values():
        all_failures.extend(cat_report.failures)
        all_infos.extend(cat_report.infos)

    checks = _build_checks_payload(reports)
    total_passed = sum(c["passed"] for c in checks.values())
    total_failed = sum(c["failed"] for c in checks.values())

    if args.json:
        payload = {
            "status": "pass" if not all_failures else "fail",
            "checks": checks,
            "summary": (
                f"{total_passed} passed, {total_failed} failed "
                f"across {len(checks)} categories"
            ),
        }
        print(json.dumps(payload, indent=2))
    else:
        for info in all_infos:
            print(f"info: {info}")
        if all_failures:
            print("governance checks failed:")
            for failure in all_failures:
                print(f"- {failure}")
        else:
            print("governance checks passed")
    return 0 if not all_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
