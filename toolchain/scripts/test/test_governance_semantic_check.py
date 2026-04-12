from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from governance_semantic_check import (
    SemanticReport,
    check_canonical_entrypoints_cover_required_formats,
    check_canonical_skill_packages_are_minimal,
    check_adapter_wrappers_are_thin,
    check_foundations_authority_shadows,
    check_outdated_placeholder_phrases,
    check_required_handoffs,
)


def write_doc(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_check_required_handoffs_flags_missing_link(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "toolchain/toolchain-layering.md",
        "[scripts](../../../toolchain/scripts/README.md)\n",
    )
    write_doc(tmp_path / "toolchain/scripts/README.md", "# scripts\n")
    write_doc(tmp_path / "toolchain/evals/README.md", "# evals\n")
    write_doc(tmp_path / "docs/deployable-skills/README.md", "")
    write_doc(tmp_path / "docs/deployable-skills/memory-side/formats/context-routing-output-format.md", "")
    write_doc(tmp_path / "docs/deployable-skills/memory-side/formats/writeback-cleanup-output-format.md", "")
    write_doc(tmp_path / "docs/deployable-skills/task-interface/task-contract.md", "")
    write_doc(tmp_path / "docs/deployable-skills/memory-side/context-routing.md", "")
    write_doc(tmp_path / "docs/deployable-skills/memory-side/writeback-cleanup.md", "")
    write_doc(tmp_path / "docs/autoresearch/knowledge/README.md", "")

    report = SemanticReport()
    check_required_handoffs(tmp_path, report)

    assert any("toolchain-layering.md -> toolchain/evals/README.md" in item for item in report.failures)


def test_check_foundations_authority_shadows_flags_prefixed_duplicate(tmp_path: Path) -> None:
    foundations_dir = tmp_path / "docs/project-maintenance/foundations"
    foundations_dir.mkdir(parents=True, exist_ok=True)
    required = [
        "root-directory-layering.md",
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
        tmp_path / "toolchain/toolchain-layering.md",
        "current wording\n",
    )

    report = SemanticReport()
    check_outdated_placeholder_phrases(tmp_path, report)

    assert any("toolchain/scripts/README.md" in item for item in report.failures)



def test_check_adapter_wrappers_are_thin_flags_legacy_sections(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "product/memory-side/adapters/agents/skills/context-routing-skill/SKILL.md",
        "\n".join(
            [
                "# Wrapper",
                "## Canonical Source",
                "## Backend Notes",
                "## Deploy Target",
                "## Execution Rules",
            ]
        )
        + "\n",
    )

    report = SemanticReport()
    check_adapter_wrappers_are_thin(tmp_path, report)

    assert any("Execution Rules" in item for item in report.failures)


def test_check_canonical_skill_packages_are_minimal_accepts_valid_package(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "product/memory-side/skills/demo-skill/SKILL.md",
        "\n".join(
            [
                "# Demo Skill",
                "## Overview",
                "## When To Use",
                "## Workflow",
                "## Hard Constraints",
                "## Expected Output",
                "## Resources",
            ]
        )
        + "\n",
    )
    write_doc(
        tmp_path / "product/memory-side/skills/demo-skill/references/entrypoints.md",
        "# Demo references\n\n## Reading Policy\n",
    )

    report = SemanticReport()
    check_canonical_skill_packages_are_minimal(tmp_path, report)

    assert report.failures == []


def test_check_canonical_skill_packages_are_minimal_flags_adapter_leakage(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "product/task-interface/skills/demo-skill/SKILL.md",
        "\n".join(
            [
                "# Demo Skill",
                "## Overview",
                "## When To Use",
                "## Workflow",
                "## Hard Constraints",
                "## Expected Output",
                "## Resources",
                "## Backend Notes",
            ]
        )
        + "\n",
    )
    write_doc(
        tmp_path / "product/task-interface/skills/demo-skill/references/entrypoints.md",
        "# Demo references\n\n## Reading Policy\n",
    )

    report = SemanticReport()
    check_canonical_skill_packages_are_minimal(tmp_path, report)

    assert any("Backend Notes" in item for item in report.failures)


def test_check_canonical_skill_packages_are_minimal_requires_harness_prompt_and_bindings(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "product/harness-operations/skills/demo-workflow/SKILL.md",
        "\n".join(
            [
                "# Demo Skill",
                "## Overview",
                "## When To Use",
                "## Workflow",
                "## Hard Constraints",
                "## Expected Output",
                "## Resources",
            ]
        )
        + "\n",
    )
    write_doc(
        tmp_path / "product/harness-operations/skills/demo-workflow/references/entrypoints.md",
        "# Demo references\n\n## Reading Policy\n",
    )

    report = SemanticReport()
    check_canonical_skill_packages_are_minimal(tmp_path, report)

    assert any("references/prompt.md" in item for item in report.failures)
    assert any("references/bindings.md" in item for item in report.failures)


def test_check_canonical_entrypoints_cover_required_formats_flags_missing_link(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "product/memory-side/skills/context-routing-skill/references/entrypoints.md",
        "# refs\n\n- `docs/deployable-skills/memory-side/context-routing-rules.md`\n",
    )
    write_doc(
        tmp_path / "product/memory-side/skills/writeback-cleanup-skill/references/entrypoints.md",
        "# refs\n\n- `docs/deployable-skills/memory-side/writeback-cleanup-rules.md`\n",
    )
    write_doc(
        tmp_path / "docs/deployable-skills/memory-side/formats/context-routing-output-format.md",
        "# format\n",
    )
    write_doc(
        tmp_path / "docs/deployable-skills/memory-side/formats/writeback-cleanup-output-format.md",
        "# format\n",
    )

    report = SemanticReport()
    check_canonical_entrypoints_cover_required_formats(tmp_path, report)

    assert any("context-routing-output-format.md" in item for item in report.failures)
    assert any("writeback-cleanup-output-format.md" in item for item in report.failures)
