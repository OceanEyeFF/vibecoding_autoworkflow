from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from governance_semantic_check import (
    SemanticReport,
    check_append_request_contract_terms,
    check_adapter_wrappers_are_thin,
    check_canonical_skill_packages_are_minimal,
    check_foundations_authority_shadows,
    check_outdated_placeholder_phrases,
    check_path_governance_docs_list_gitignore_entries,
    check_repo_python_commands_are_bytecode_free,
    check_root_tool_shims_disable_bytecode,
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


def test_check_append_request_contract_terms_flags_drift(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "docs/harness/artifact/control/append-request.md",
        "append-feature\nappend-design\ngoal change\nnew worktrack\nscope expansion\ndesign-only\ndesign-then-implementation\napproval_required\ncontinuation_ready\n",
    )
    write_doc(
        tmp_path / "docs/harness/workflow-families/repo-evolution/append-request-routing.md",
        "append-feature\nappend-design\ngoal change\nnew worktrack\nscope expansion\ndesign-only\ndesign-then-implementation\napproval_required\ncontinuation_ready\ncontinuation_blockers\n",
    )
    write_doc(
        tmp_path / "product/harness/skills/repo-append-request-skill/SKILL.md",
        "append-feature\nappend-design\ngoal change\nnew worktrack\nscope expansion\ndesign-only\ndesign-then-implementation\napproval_required\ncontinuation_ready\ncontinuation_blockers\n",
    )
    write_doc(
        tmp_path / "product/harness/skills/repo-append-request-skill/templates/append-request.template.md",
        "approval_required\ncontinuation_ready\ncontinuation_blockers\n",
    )

    report = SemanticReport()
    check_append_request_contract_terms(tmp_path, report)

    assert any("continuation_blockers" in item for item in report.failures)


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


def test_check_adapter_wrappers_are_thin_ignores_code_fence_headings(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "product/harness/adapters/agents/skills/demo-skill/SKILL.md",
        "\n".join(
            [
                "# Demo Adapter Wrapper",
                "## Canonical Source",
                "## Backend Notes",
                "## Deploy Target",
                "```md",
                "## Execution Rules",
                "```",
            ]
        )
        + "\n",
    )

    report = SemanticReport()
    check_adapter_wrappers_are_thin(tmp_path, report)

    assert report.failures == []


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


def test_check_canonical_skill_packages_are_minimal_ignores_code_fence_headings(
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
                "```md",
                "## Backend Notes",
                "```",
            ]
        )
        + "\n",
    )
    report = SemanticReport()
    check_canonical_skill_packages_are_minimal(tmp_path, report)

    assert report.failures == []


def test_check_repo_python_commands_are_bytecode_free_flags_bare_repo_command(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "docs/project-maintenance/governance/review-verify-handbook.md",
        "Run `python3 toolchain/scripts/test/folder_logic_check.py`.\n",
    )

    report = SemanticReport()
    check_repo_python_commands_are_bytecode_free(tmp_path, report)

    assert any("review-verify-handbook.md:1" in item for item in report.failures)


def test_check_repo_python_commands_are_bytecode_free_accepts_prefixed_repo_command(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "docs/project-maintenance/governance/review-verify-handbook.md",
        "Run `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/folder_logic_check.py`.\n",
    )

    report = SemanticReport()
    check_repo_python_commands_are_bytecode_free(tmp_path, report)

    assert report.failures == []


def test_check_repo_python_commands_are_bytecode_free_flags_bare_tools_command(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "docs/project-maintenance/governance/review-verify-handbook.md",
        "Run `python3 tools/closeout_acceptance_gate.py --json`.\n",
    )

    report = SemanticReport()
    check_repo_python_commands_are_bytecode_free(tmp_path, report)

    assert any("review-verify-handbook.md:1" in item for item in report.failures)


def test_check_repo_python_commands_are_bytecode_free_checks_each_occurrence(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "toolchain/scripts/deploy/README.md",
        "`PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/aw_scaffold.py list` and "
        "`python3 -m pytest toolchain/scripts/test/test_folder_logic_check.py`\n",
    )

    report = SemanticReport()
    check_repo_python_commands_are_bytecode_free(tmp_path, report)

    assert len(report.failures) == 1


def test_check_repo_python_commands_are_bytecode_free_skips_historical_log(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "docs/project-maintenance/deploy/codex-harness-manual-run-continuous-2026-04-23.md",
        "`python3 -m unittest discover -s tests -v`\n",
    )

    report = SemanticReport()
    check_repo_python_commands_are_bytecode_free(tmp_path, report)

    assert report.failures == []


def test_governance_semantic_cli_disables_bytecode_before_local_import(tmp_path: Path) -> None:
    source_script = Path(__file__).resolve().parent / "governance_semantic_check.py"
    write_doc(tmp_path / "governance_semantic_check.py", source_script.read_text(encoding="utf-8"))
    write_doc(
        tmp_path / "path_governance_check.py",
        "\n".join(
            [
                "def iter_relative_markdown_targets(text):",
                "    return []",
                "",
                "def resolve_markdown_target(markdown_file, repo_root, target):",
                "    return repo_root / target",
            ]
        )
        + "\n",
    )

    env = os.environ.copy()
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    completed = subprocess.run(
        [sys.executable, str(tmp_path / "governance_semantic_check.py"), "--repo-root", str(tmp_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    assert completed.returncode == 1
    assert not list(tmp_path.rglob("__pycache__"))
    assert not list(tmp_path.rglob("*.pyc"))


def test_check_root_tool_shims_disable_bytecode_flags_late_guard(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "tools/scope_gate_check.py",
        "\n".join(
            [
                "import sys",
                "from toolchain.scripts.test.scope_gate_check import main",
                "sys.dont_write_bytecode = True",
            ]
        )
        + "\n",
    )

    report = SemanticReport()
    check_root_tool_shims_disable_bytecode(tmp_path, report)

    assert any("tools/scope_gate_check.py" in item for item in report.failures)


def test_check_root_tool_shims_disable_bytecode_accepts_guard_before_import(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "tools/scope_gate_check.py",
        "\n".join(
            [
                "import sys",
                "sys.dont_write_bytecode = True",
                "from toolchain.scripts.test.scope_gate_check import main",
            ]
        )
        + "\n",
    )

    report = SemanticReport()
    check_root_tool_shims_disable_bytecode(tmp_path, report)

    assert report.failures == []


def test_check_path_governance_docs_list_gitignore_entries_flags_missing_entry(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "docs/project-maintenance/governance/path-governance-checks.md",
        "` .aw/ `\n",
    )

    report = SemanticReport()
    check_path_governance_docs_list_gitignore_entries(tmp_path, report)

    assert any(".agents/" in item for item in report.failures)


def test_check_path_governance_docs_list_gitignore_entries_accepts_complete_list(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "docs/project-maintenance/governance/path-governance-checks.md",
        "\n".join(
            [
                "`.aw/`",
                "`.agents/`",
                "`.claude/`",
                "`.opencode/`",
                "`.autoworkflow/`",
                "`.spec-workflow/`",
                "`**/__pycache__/`",
                "`.pytest_cache/`",
                "`*.pyc`",
                "`*.pyo`",
            ]
        )
        + "\n",
    )

    report = SemanticReport()
    check_path_governance_docs_list_gitignore_entries(tmp_path, report)

    assert report.failures == []
