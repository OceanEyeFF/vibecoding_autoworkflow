from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from path_governance_check import CheckReport, check_gitignore


def write_gitignore(repo_root: Path, lines: list[str]) -> None:
    (repo_root / ".gitignore").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_check_gitignore_accepts_required_cache_entries(tmp_path: Path) -> None:
    write_gitignore(
        tmp_path,
        [
            ".aw/",
            ".agents/",
            ".claude/",
            ".opencode/",
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
            ".opencode/",
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
