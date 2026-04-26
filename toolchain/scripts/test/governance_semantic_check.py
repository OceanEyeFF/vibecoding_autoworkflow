#!/usr/bin/env python3
"""Run minimal semantic governance checks for key docs handoffs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.dont_write_bytecode = True

from path_governance_check import REQUIRED_GITIGNORE_ENTRIES, iter_relative_markdown_targets, resolve_markdown_target


REPO_ROOT = Path(__file__).resolve().parents[3]
FOUNDATIONS_DIR = "docs/project-maintenance/foundations"
REQUIRED_TEMPLATE_PATHS = [
    "docs/harness/adjacent-systems/memory-side/formats/context-routing-output-format.md",
    "docs/harness/adjacent-systems/memory-side/formats/writeback-cleanup-output-format.md",
    "docs/harness/adjacent-systems/task-interface/task-contract.md",
]
REQUIRED_HANDOFF_LINKS = {
    "product/README.md": [
        "product/harness/README.md",
    ],
    "toolchain/toolchain-layering.md": [
        "toolchain/scripts/README.md",
    ],
    "docs/harness/README.md": [
        "docs/harness/foundations/README.md",
        "docs/harness/adjacent-systems/README.md",
        "docs/harness/workflow-families/README.md",
        "product/harness/README.md",
    ],
    "product/harness/README.md": [
        "docs/harness/README.md",
        "product/harness/skills/README.md",
        "product/harness/adapters/README.md",
    ],
    "docs/harness/adjacent-systems/task-interface/README.md": [
        "docs/harness/adjacent-systems/task-interface/task-contract.md",
    ],
    "docs/harness/adjacent-systems/memory-side/README.md": [
        "docs/harness/adjacent-systems/memory-side/overview.md",
        "docs/harness/adjacent-systems/memory-side/layer-boundary.md",
        "docs/harness/adjacent-systems/memory-side/skill-agent-model.md",
    ],
    "docs/harness/adjacent-systems/memory-side/context-routing.md": [
        "docs/harness/adjacent-systems/memory-side/formats/context-routing-output-format.md",
    ],
    "docs/harness/adjacent-systems/memory-side/writeback-cleanup.md": [
        "docs/harness/adjacent-systems/memory-side/formats/writeback-cleanup-output-format.md",
    ],
}
FOUNDATIONS_AUTHORITY_STEMS = [
    "root-directory-layering",
]
OUTDATED_PLACEHOLDER_PHRASES = {
    "docs/harness/README.md": [
        "已验证的 legacy skills 已降级为可回收资产；当前 repo 不再保留独立的 harness skill/source 分区",
    ],
    "docs/harness/workflow-families/README.md": [
        "当前这些 workflow family 先固定在文档真相层；仓库内不再保留独立的 `product/harness/` workflow/profile source 分区。",
    ],
    "toolchain/toolchain-layering.md": [
        "`research/` 目录当前只保留占位入口，不承载 active runner；其中 `OpenCode` 仍是 research backend 预留位",
        "`research/` 与 `evals/` 保留为预留位，只有在方案重新准入后才继续扩展。",
    ],
    "toolchain/scripts/README.md": [
        "`research/`：预留给后续准入的最小研究脚本",
    ],
}
CANONICAL_SKILL_GLOBS = [
    "product/*/skills/*/SKILL.md",
]
ADAPTER_SKILL_GLOBS = [
    "product/*/adapters/*/skills/*/SKILL.md",
]
CANONICAL_SKILL_FORBIDDEN_HEADINGS = [
    "## Canonical Source",
    "## Backend Notes",
    "## Deploy Target",
]
THIN_WRAPPER_REQUIRED_HEADINGS = [
    "## Canonical Source",
    "## Backend Notes",
    "## Deploy Target",
]
THIN_WRAPPER_FORBIDDEN_HEADINGS = [
    "## Execution Rules",
    "## Output Contract",
]
APPEND_REQUEST_CONTRACT_PATHS = [
    "docs/harness/artifact/control/append-request.md",
    "docs/harness/workflow-families/repo-evolution/append-request-routing.md",
    "product/harness/skills/repo-append-request-skill/SKILL.md",
    "product/harness/skills/repo-append-request-skill/templates/append-request.template.md",
]
PATH_GOVERNANCE_CHECKS_DOC = "docs/project-maintenance/governance/path-governance-checks.md"
APPEND_REQUEST_REQUIRED_TERMS = [
    "approval_required",
    "continuation_ready",
    "continuation_blockers",
]
APPEND_REQUEST_MODES = [
    "append-feature",
    "append-design",
]
APPEND_REQUEST_CLASSIFICATIONS = [
    "goal change",
    "new worktrack",
    "scope expansion",
    "design-only",
    "design-then-implementation",
]
ROOT_TOOL_SHIM_GLOB = "tools/*.py"
BYTECODE_FREE_COMMAND_GLOBS = [
    "AGENTS.md",
    "docs/project-maintenance/**/*.md",
    "product/harness/skills/**/*.md",
    "toolchain/scripts/deploy/README.md",
]
BYTECODE_FREE_COMMAND_EXCLUDED_PATHS = {
    "docs/project-maintenance/deploy/codex-harness-manual-run-continuous-2026-04-23.md",
}
REPO_PYTHON_COMMAND_RE = re.compile(
    r"\bpython3\s+(?:"
    r"-m\s+(?:pytest|unittest)\b|"
    r"(?:toolchain/scripts|tools|scripts/deploy_aw\.py|product/harness/skills)/"
    r")"
)


@dataclass
class SemanticReport:
    failures: list[str] = field(default_factory=list)
    infos: list[str] = field(default_factory=list)

    def add_failure(self, message: str) -> None:
        self.failures.append(message)

    def add_info(self, message: str) -> None:
        self.infos.append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate minimal semantic governance handoffs.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    return parser.parse_args()


def to_relative_posix(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def collect_repo_relative_markdown_links(repo_root: Path, relative_path: str) -> set[str]:
    markdown_file = repo_root / relative_path
    text = markdown_file.read_text(encoding="utf-8")
    resolved_targets: set[str] = set()
    for target in iter_relative_markdown_targets(text):
        resolved = resolve_markdown_target(markdown_file, repo_root, target)
        try:
            resolved_targets.add(to_relative_posix(resolved, repo_root))
        except ValueError:
            continue
    return resolved_targets


def markdown_headings_outside_code_fences(text: str) -> set[str]:
    headings: set[str] = set()
    in_code_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        if stripped.startswith("#"):
            marker, _, title = stripped.partition(" ")
            if marker and set(marker) == {"#"} and title:
                headings.add(stripped)
    return headings


def check_required_templates(repo_root: Path, report: SemanticReport) -> None:
    missing = [path for path in REQUIRED_TEMPLATE_PATHS if not (repo_root / path).exists()]
    for path in missing:
        report.add_failure(f"missing required governance template: {path}")
    report.add_info(f"checked {len(REQUIRED_TEMPLATE_PATHS)} required governance templates")


def check_required_handoffs(repo_root: Path, report: SemanticReport) -> None:
    checked = 0
    for source, expected_targets in REQUIRED_HANDOFF_LINKS.items():
        if not (repo_root / source).exists():
            report.add_failure(f"missing handoff source document: {source}")
            continue
        resolved_targets = collect_repo_relative_markdown_links(repo_root, source)
        for target in expected_targets:
            checked += 1
            if target not in resolved_targets:
                report.add_failure(f"missing semantic handoff link: {source} -> {target}")
    report.add_info(f"checked {checked} semantic handoff links")


def check_foundations_authority_shadows(repo_root: Path, report: SemanticReport) -> None:
    foundations_dir = repo_root / FOUNDATIONS_DIR
    checked = 0
    for stem in FOUNDATIONS_AUTHORITY_STEMS:
        checked += 1
        matches = sorted(path.name for path in foundations_dir.glob(f"{stem}*.md"))
        canonical_name = f"{stem}.md"
        extras = [name for name in matches if name != canonical_name]
        if canonical_name not in matches:
            report.add_failure(f"missing foundations authority document: {FOUNDATIONS_DIR}/{canonical_name}")
        if extras:
            report.add_failure(
                f"shadow authority documents found for {canonical_name}: {', '.join(extras)}"
            )
    report.add_info(f"checked {checked} foundations authority slots for shadow files")


def check_outdated_placeholder_phrases(repo_root: Path, report: SemanticReport) -> None:
    checked = 0
    for relative_path, phrases in OUTDATED_PLACEHOLDER_PHRASES.items():
        if not (repo_root / relative_path).exists():
            report.add_failure(f"missing semantic phrase source document: {relative_path}")
            continue
        text = (repo_root / relative_path).read_text(encoding="utf-8")
        for phrase in phrases:
            checked += 1
            if phrase in text:
                report.add_failure(f"outdated placeholder wording still present in {relative_path}")
    report.add_info(f"checked {checked} outdated placeholder phrases")



def iter_adapter_skill_files(repo_root: Path) -> list[Path]:
    adapter_files: list[Path] = []
    seen: set[Path] = set()
    for pattern in ADAPTER_SKILL_GLOBS:
        for path in sorted(repo_root.glob(pattern)):
            if path not in seen:
                seen.add(path)
                adapter_files.append(path)
    return adapter_files


def iter_canonical_skill_files(repo_root: Path) -> list[Path]:
    canonical_files: list[Path] = []
    seen: set[Path] = set()
    for pattern in CANONICAL_SKILL_GLOBS:
        for path in sorted(repo_root.glob(pattern)):
            if path not in seen:
                seen.add(path)
                canonical_files.append(path)
    return canonical_files


def check_canonical_skill_packages_are_minimal(repo_root: Path, report: SemanticReport) -> None:
    canonical_files = iter_canonical_skill_files(repo_root)
    if not canonical_files:
        report.add_failure("missing canonical skill packages under product/*/skills/*/SKILL.md")
        return

    checked = 0
    for canonical_file in canonical_files:
        checked += 1
        relative_path = to_relative_posix(canonical_file, repo_root)
        text = canonical_file.read_text(encoding="utf-8")

        if not text.lstrip().startswith("---"):
            report.add_failure(f"canonical skill missing frontmatter block: {relative_path}")
        if "\n# " not in text and not text.lstrip().startswith("# "):
            report.add_failure(f"canonical skill missing H1 title: {relative_path}")

        headings = markdown_headings_outside_code_fences(text)
        for heading in CANONICAL_SKILL_FORBIDDEN_HEADINGS:
            if heading in headings:
                report.add_failure(
                    f"canonical skill leaked adapter-style section {heading!r}: {relative_path}"
                )

        if "references/entrypoints.md" in text:
            report.add_failure(
                f"canonical skill still references deprecated references/entrypoints.md: {relative_path}"
            )

        references_path = canonical_file.parent / "references/entrypoints.md"
        if references_path.exists():
            report.add_failure(
                f"canonical skill still contains deprecated references/entrypoints.md file: {relative_path}"
            )

    report.add_info(f"checked {checked} canonical skill packages for minimal executable shape")


def check_adapter_wrappers_are_thin(repo_root: Path, report: SemanticReport) -> None:
    adapter_files = iter_adapter_skill_files(repo_root)
    if not adapter_files:
        report.add_info("checked 0 adapter wrappers for thin-shell structure")
        return

    checked = 0
    for adapter_file in adapter_files:
        checked += 1
        relative_path = to_relative_posix(adapter_file, repo_root)
        text = adapter_file.read_text(encoding="utf-8")
        headings = markdown_headings_outside_code_fences(text)
        for heading in THIN_WRAPPER_REQUIRED_HEADINGS:
            if heading not in headings:
                report.add_failure(
                    f"adapter wrapper missing required thin-shell heading {heading!r}: {relative_path}"
                )
        for heading in THIN_WRAPPER_FORBIDDEN_HEADINGS:
            if heading in headings:
                report.add_failure(
                    f"adapter wrapper still contains forbidden duplicated section {heading!r}: {relative_path}"
                )
    report.add_info(f"checked {checked} adapter wrappers for thin-shell structure")


def check_append_request_contract_terms(repo_root: Path, report: SemanticReport) -> None:
    checked = 0
    for relative_path in APPEND_REQUEST_CONTRACT_PATHS:
        path = repo_root / relative_path
        if not path.exists():
            report.add_failure(f"missing append request contract source: {relative_path}")
            continue
        checked += 1
        text = path.read_text(encoding="utf-8")
        for term in APPEND_REQUEST_REQUIRED_TERMS:
            if term not in text:
                report.add_failure(
                    f"append request contract missing required term {term!r}: {relative_path}"
                )

    for relative_path in APPEND_REQUEST_CONTRACT_PATHS[:3]:
        path = repo_root / relative_path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for mode in APPEND_REQUEST_MODES:
            if mode not in text:
                report.add_failure(
                    f"append request contract missing mode {mode!r}: {relative_path}"
                )
        for classification in APPEND_REQUEST_CLASSIFICATIONS:
            if classification not in text:
                report.add_failure(
                    f"append request contract missing classification {classification!r}: {relative_path}"
                )

    report.add_info(f"checked {checked} append request contract sources")


def iter_bytecode_free_command_files(repo_root: Path) -> list[Path]:
    command_files: list[Path] = []
    seen: set[Path] = set()
    for pattern in BYTECODE_FREE_COMMAND_GLOBS:
        for path in sorted(repo_root.glob(pattern)):
            if path.is_file() and path not in seen:
                seen.add(path)
                command_files.append(path)
    return command_files


def check_repo_python_commands_are_bytecode_free(repo_root: Path, report: SemanticReport) -> None:
    checked = 0
    for command_file in iter_bytecode_free_command_files(repo_root):
        relative_path = to_relative_posix(command_file, repo_root)
        if relative_path in BYTECODE_FREE_COMMAND_EXCLUDED_PATHS:
            continue

        for line_number, line in enumerate(command_file.read_text(encoding="utf-8").splitlines(), 1):
            for match in REPO_PYTHON_COMMAND_RE.finditer(line):
                checked += 1
                prefix_window = line[max(0, match.start() - 48) : match.start()]
                if "PYTHONDONTWRITEBYTECODE=1" not in prefix_window:
                    report.add_failure(
                        "repo Python command must set PYTHONDONTWRITEBYTECODE=1: "
                        f"{relative_path}:{line_number}"
                    )
    report.add_info(f"checked {checked} repo Python command examples for bytecode-free invocation")


def check_root_tool_shims_disable_bytecode(repo_root: Path, report: SemanticReport) -> None:
    checked = 0
    for shim_path in sorted(repo_root.glob(ROOT_TOOL_SHIM_GLOB)):
        if not shim_path.is_file():
            continue
        checked += 1
        relative_path = to_relative_posix(shim_path, repo_root)
        text = shim_path.read_text(encoding="utf-8")
        toolchain_import_index = text.find("from toolchain.")
        if toolchain_import_index == -1:
            continue
        guard_index = text.find("sys.dont_write_bytecode = True")
        if guard_index == -1 or guard_index > toolchain_import_index:
            report.add_failure(
                "root tool shim must disable bytecode before importing toolchain modules: "
                f"{relative_path}"
            )
    report.add_info(f"checked {checked} root tool shims for bytecode guard ordering")


def check_path_governance_docs_list_gitignore_entries(repo_root: Path, report: SemanticReport) -> None:
    doc_path = repo_root / PATH_GOVERNANCE_CHECKS_DOC
    if not doc_path.exists():
        report.add_failure(f"missing path governance checks document: {PATH_GOVERNANCE_CHECKS_DOC}")
        return

    text = doc_path.read_text(encoding="utf-8")
    checked = 0
    for entry in REQUIRED_GITIGNORE_ENTRIES:
        checked += 1
        if f"`{entry}`" not in text:
            report.add_failure(
                f"path governance docs missing required .gitignore entry {entry!r}: "
                f"{PATH_GOVERNANCE_CHECKS_DOC}"
            )
    report.add_info(f"checked {checked} documented .gitignore governance entries")


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    report = SemanticReport()
    check_required_templates(repo_root, report)
    check_required_handoffs(repo_root, report)
    check_foundations_authority_shadows(repo_root, report)
    check_outdated_placeholder_phrases(repo_root, report)
    check_canonical_skill_packages_are_minimal(repo_root, report)
    check_adapter_wrappers_are_thin(repo_root, report)
    check_append_request_contract_terms(repo_root, report)
    check_repo_python_commands_are_bytecode_free(repo_root, report)
    check_root_tool_shims_disable_bytecode(repo_root, report)
    check_path_governance_docs_list_gitignore_entries(repo_root, report)

    payload = {
        "passed": not report.failures,
        "failures": report.failures,
        "infos": report.infos,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for info in report.infos:
            print(f"info: {info}")
        if report.failures:
            for failure in report.failures:
                print(f"failure: {failure}")
        else:
            print("governance semantic checks passed")

    return 0 if not report.failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
