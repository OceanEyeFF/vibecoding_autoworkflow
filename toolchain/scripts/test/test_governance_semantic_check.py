from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from governance_semantic_check import (
    SemanticReport,
    check_foundations_authority_shadows,
    check_outdated_placeholder_phrases,
    check_required_handoffs,
)


def write_doc(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_check_required_handoffs_flags_missing_link(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "docs/knowledge/foundations/toolchain-layering.md",
        "[scripts](../../../toolchain/scripts/README.md)\n",
    )
    write_doc(tmp_path / "toolchain/scripts/README.md", "# scripts\n")
    write_doc(tmp_path / "toolchain/evals/README.md", "# evals\n")
    write_doc(tmp_path / "docs/knowledge/foundations/README.md", "")
    write_doc(tmp_path / "docs/knowledge/foundations/task-contract-template.md", "")
    write_doc(tmp_path / "docs/knowledge/foundations/context-entry-template.md", "")
    write_doc(tmp_path / "docs/knowledge/foundations/writeback-log-template.md", "")
    write_doc(tmp_path / "docs/knowledge/foundations/decision-record-template.md", "")
    write_doc(tmp_path / "docs/knowledge/foundations/module-entry-template.md", "")
    write_doc(tmp_path / "docs/knowledge/memory-side/context-routing.md", "")
    write_doc(tmp_path / "docs/knowledge/memory-side/writeback-cleanup.md", "")
    write_doc(tmp_path / "docs/knowledge/autoresearch/README.md", "")

    report = SemanticReport()
    check_required_handoffs(tmp_path, report)

    assert any("toolchain-layering.md -> toolchain/evals/README.md" in item for item in report.failures)


def test_check_foundations_authority_shadows_flags_prefixed_duplicate(tmp_path: Path) -> None:
    foundations_dir = tmp_path / "docs/knowledge/foundations"
    foundations_dir.mkdir(parents=True, exist_ok=True)
    required = [
        "root-directory-layering.md",
        "path-governance-ai-routing.md",
        "docs-governance.md",
        "toolchain-layering.md",
        "partition-model.md",
        "task-contract-template.md",
        "context-entry-template.md",
        "writeback-log-template.md",
        "decision-record-template.md",
        "module-entry-template.md",
    ]
    for name in required:
        write_doc(foundations_dir / name, "# doc\n")
    write_doc(foundations_dir / "root-directory-layering-v2.md", "# shadow\n")

    report = SemanticReport()
    check_foundations_authority_shadows(tmp_path, report)

    assert any("root-directory-layering.md" in item for item in report.failures)


def test_check_outdated_placeholder_phrases_flags_stale_text(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "toolchain/scripts/README.md",
        "`research/`：预留给后续准入的最小研究脚本\n",
    )
    write_doc(
        tmp_path / "toolchain/evals/README.md",
        "`memory-side/` 当前承接已准入主题的 eval 入口。\n",
    )
    write_doc(
        tmp_path / "docs/knowledge/foundations/toolchain-layering.md",
        "current wording\n",
    )

    report = SemanticReport()
    check_outdated_placeholder_phrases(tmp_path, report)

    assert any("toolchain/scripts/README.md" in item for item in report.failures)
