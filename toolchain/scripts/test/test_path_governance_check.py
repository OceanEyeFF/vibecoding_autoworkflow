from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from path_governance_check import (
    CheckReport,
    check_gitignore,
    check_required_backlinks,
    check_required_entrypoint_links,
    check_required_entrypoints,
)


def write_gitignore(repo_root: Path, lines: list[str]) -> None:
    (repo_root / ".gitignore").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_docs_book_is_required_and_linked_from_entrypoints(tmp_path: Path) -> None:
    write_file(tmp_path / "AGENTS.md", "[docs](./docs/README.md)\n")
    write_file(tmp_path / "README.md", "[docs](./docs/README.md)\n")
    write_file(
        tmp_path / "INDEX.md",
        "[docs](./docs/README.md)\n[book](./docs/book.md)\n",
    )
    write_file(
        tmp_path / "docs/README.md",
        "[book](./book.md)\n[project](./project-maintenance/README.md)\n[harness](./harness/README.md)\n",
    )
    write_file(tmp_path / "docs/book.md", "[AGENTS](../AGENTS.md)\n")
    write_file(tmp_path / "docs/project-maintenance/README.md", "# project\n")
    write_file(tmp_path / "docs/harness/README.md", "# harness\n")

    entry_report = CheckReport()
    check_required_entrypoints(tmp_path, entry_report)
    check_required_entrypoint_links(tmp_path, entry_report)

    backlink_report = CheckReport()
    check_required_backlinks(
        tmp_path,
        backlink_report,
        label="agents-contract",
        target_relative_path="AGENTS.md",
        backlink_paths=["docs/book.md"],
    )

    assert all("docs/book.md" not in failure for failure in entry_report.failures)
    assert backlink_report.failures == []


def test_docs_book_missing_link_is_flagged(tmp_path: Path) -> None:
    write_file(tmp_path / "INDEX.md", "[docs](./docs/README.md)\n")
    write_file(
        tmp_path / "docs/README.md",
        "[project](./project-maintenance/README.md)\n[harness](./harness/README.md)\n",
    )
    write_file(tmp_path / "docs/project-maintenance/README.md", "# project\n")
    write_file(tmp_path / "docs/harness/README.md", "# harness\n")

    report = CheckReport()
    check_required_entrypoint_links(tmp_path, report)

    assert "entrypoint missing document link: INDEX.md -> docs/book.md" in report.failures
    assert "entrypoint missing document link: docs/README.md -> docs/book.md" in report.failures


def test_check_gitignore_accepts_required_cache_entries(tmp_path: Path) -> None:
    write_gitignore(
        tmp_path,
        [
            ".aw/",
            ".agents/",
            ".claude/",
            ".autoworkflow/",
            ".spec-workflow/",
            "**/__pycache__/",
            ".pytest_cache/",
            "*.pyc",
            "*.pyo",
        ],
    )

    report = CheckReport()
    check_gitignore(tmp_path, report)

    assert report.failures == []


def test_check_gitignore_flags_missing_cache_entry(tmp_path: Path) -> None:
    write_gitignore(
        tmp_path,
        [
            ".aw/",
            ".agents/",
            ".claude/",
            ".autoworkflow/",
            ".spec-workflow/",
            "**/__pycache__/",
            "*.pyc",
            "*.pyo",
        ],
    )

    report = CheckReport()
    check_gitignore(tmp_path, report)

    assert "missing .gitignore entry: .pytest_cache/" in report.failures
