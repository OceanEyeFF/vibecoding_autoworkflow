from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from governance_semantic_check import (
    SemanticReport,
    check_adapter_wrappers_are_thin,
    check_canonical_skill_packages_are_minimal,
    check_foundations_authority_shadows,
    check_outdated_placeholder_phrases,
    check_required_handoffs,
)


def write_doc(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_check_required_handoffs_flags_missing_link(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "product/README.md",
        "[harness](./harness/README.md)\n",
    )
    write_doc(
        tmp_path / "product/harness/README.md",
        "[docs](../../docs/harness/README.md)\n[skills](./skills/README.md)\n[adapters](./adapters/README.md)\n",
    )
    write_doc(tmp_path / "product/harness/skills/README.md", "# skills\n")
    write_doc(tmp_path / "product/harness/adapters/README.md", "# adapters\n")
    write_doc(
        tmp_path / "toolchain/toolchain-layering.md",
        "missing script handoff\n",
    )
    write_doc(tmp_path / "docs/harness/README.md", "")
    write_doc(tmp_path / "docs/harness/foundations/README.md", "")
    write_doc(tmp_path / "docs/harness/adjacent-systems/README.md", "")
    write_doc(tmp_path / "docs/harness/workflow-families/README.md", "")
    write_doc(tmp_path / "docs/harness/adjacent-systems/task-interface/README.md", "")
    write_doc(tmp_path / "docs/harness/adjacent-systems/task-interface/task-contract.md", "")
    write_doc(tmp_path / "docs/harness/adjacent-systems/memory-side/README.md", "")
    write_doc(tmp_path / "docs/harness/adjacent-systems/memory-side/overview.md", "")
    write_doc(tmp_path / "docs/harness/adjacent-systems/memory-side/layer-boundary.md", "")
    write_doc(tmp_path / "docs/harness/adjacent-systems/memory-side/skill-agent-model.md", "")
    write_doc(tmp_path / "docs/harness/adjacent-systems/memory-side/context-routing.md", "")
    write_doc(tmp_path / "docs/harness/adjacent-systems/memory-side/writeback-cleanup.md", "")
    write_doc(tmp_path / "docs/harness/adjacent-systems/memory-side/formats/context-routing-output-format.md", "")
    write_doc(tmp_path / "docs/harness/adjacent-systems/memory-side/formats/writeback-cleanup-output-format.md", "")
    write_doc(tmp_path / "toolchain/scripts/README.md", "# scripts\n")

    report = SemanticReport()
    check_required_handoffs(tmp_path, report)

    assert any("toolchain-layering.md -> toolchain/scripts/README.md" in item for item in report.failures)


def test_check_foundations_authority_shadows_flags_prefixed_duplicate(tmp_path: Path) -> None:
    foundations_dir = tmp_path / "docs/project-maintenance/foundations"
    foundations_dir.mkdir(parents=True, exist_ok=True)
    write_doc(foundations_dir / "root-directory-layering.md", "# doc\n")
    write_doc(foundations_dir / "root-directory-layering-v2.md", "# shadow\n")

    report = SemanticReport()
    check_foundations_authority_shadows(tmp_path, report)

    assert any("root-directory-layering.md" in item for item in report.failures)


def test_check_outdated_placeholder_phrases_flags_stale_text(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "toolchain/scripts/README.md",
        "`research/`：预留给后续准入的最小研究脚本\n",
    )
    write_doc(tmp_path / "toolchain/toolchain-layering.md", "current wording\n")

    report = SemanticReport()
    check_outdated_placeholder_phrases(tmp_path, report)

    assert any("toolchain/scripts/README.md" in item for item in report.failures)


def test_check_adapter_wrappers_are_thin_ignores_absent_adapter_layer(tmp_path: Path) -> None:
    report = SemanticReport()
    check_adapter_wrappers_are_thin(tmp_path, report)
    assert report.failures == []


def test_check_adapter_wrappers_are_thin_accepts_valid_wrapper(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "product/harness/adapters/agents/skills/demo-skill/SKILL.md",
        "\n".join(
            [
                "# Demo Adapter Wrapper",
                "## Canonical Source",
                "## Backend Notes",
                "## Deploy Target",
            ]
        )
        + "\n",
    )

    report = SemanticReport()
    check_adapter_wrappers_are_thin(tmp_path, report)

    assert report.failures == []


def test_check_adapter_wrappers_are_thin_flags_missing_heading_and_duplication(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "product/harness/adapters/agents/skills/demo-skill/SKILL.md",
        "\n".join(
            [
                "# Demo Adapter Wrapper",
                "## Canonical Source",
                "## Backend Notes",
                "## Execution Rules",
            ]
        )
        + "\n",
    )

    report = SemanticReport()
    check_adapter_wrappers_are_thin(tmp_path, report)

    assert any("Deploy Target" in item for item in report.failures)
    assert any("Execution Rules" in item for item in report.failures)


def test_check_canonical_skill_packages_are_minimal_accepts_valid_package(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "product/harness/skills/demo-skill/SKILL.md",
        "\n".join(
            [
                "---",
                "name: demo-skill",
                "description: Demo.",
                "---",
                "# Demo Skill",
            ]
        )
        + "\n",
    )
    report = SemanticReport()
    check_canonical_skill_packages_are_minimal(tmp_path, report)

    assert report.failures == []


def test_check_canonical_skill_packages_are_minimal_flags_deprecated_entrypoint_reference(
    tmp_path: Path,
) -> None:
    write_doc(
        tmp_path / "product/harness/skills/demo-skill/SKILL.md",
        "\n".join(
            [
                "---",
                "name: demo-skill",
                "description: Demo.",
                "---",
                "# Demo Skill",
                "1. Read `references/entrypoints.md`.",
            ]
        )
        + "\n",
    )

    report = SemanticReport()
    check_canonical_skill_packages_are_minimal(tmp_path, report)

    assert any("deprecated references/entrypoints.md" in item for item in report.failures)


def test_check_canonical_skill_packages_are_minimal_flags_deprecated_entrypoint_file(
    tmp_path: Path,
) -> None:
    write_doc(
        tmp_path / "product/harness/skills/demo-skill/SKILL.md",
        "\n".join(
            [
                "---",
                "name: demo-skill",
                "description: Demo.",
                "---",
                "# Demo Skill",
            ]
        )
        + "\n",
    )
    write_doc(
        tmp_path / "product/harness/skills/demo-skill/references/entrypoints.md",
        "# Demo references\n\n## Reading Policy\n",
    )

    report = SemanticReport()
    check_canonical_skill_packages_are_minimal(tmp_path, report)

    assert any("deprecated references/entrypoints.md file" in item for item in report.failures)


def test_check_canonical_skill_packages_are_minimal_flags_adapter_leakage(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "product/harness/skills/demo-skill/SKILL.md",
        "\n".join(
            [
                "---",
                "name: demo-skill",
                "description: Demo.",
                "---",
                "# Demo Skill",
                "## Backend Notes",
            ]
        )
        + "\n",
    )
    report = SemanticReport()
    check_canonical_skill_packages_are_minimal(tmp_path, report)

    assert any("Backend Notes" in item for item in report.failures)
