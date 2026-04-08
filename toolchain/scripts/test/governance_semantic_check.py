#!/usr/bin/env python3
"""Run minimal semantic governance checks for key docs handoffs."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from path_governance_check import iter_relative_markdown_targets, resolve_markdown_target


REPO_ROOT = Path(__file__).resolve().parents[3]
FOUNDATIONS_DIR = "docs/knowledge/foundations"
REQUIRED_TEMPLATE_PATHS = [
    "docs/knowledge/foundations/task-contract-template.md",
    "docs/knowledge/foundations/context-entry-template.md",
    "docs/knowledge/foundations/writeback-log-template.md",
    "docs/knowledge/foundations/decision-record-template.md",
    "docs/knowledge/foundations/module-entry-template.md",
]
REQUIRED_HANDOFF_LINKS = {
    "docs/knowledge/foundations/toolchain-layering.md": [
        "toolchain/scripts/README.md",
        "toolchain/evals/README.md",
    ],
    "docs/knowledge/foundations/README.md": REQUIRED_TEMPLATE_PATHS,
    "docs/knowledge/memory-side/context-routing.md": [
        "docs/knowledge/foundations/context-entry-template.md",
    ],
    "docs/knowledge/memory-side/writeback-cleanup.md": [
        "docs/knowledge/foundations/writeback-log-template.md",
    ],
    "docs/knowledge/autoresearch/README.md": [
        "docs/knowledge/foundations/module-entry-template.md",
    ],
}
FOUNDATIONS_AUTHORITY_STEMS = [
    "root-directory-layering",
    "path-governance-ai-routing",
    "docs-governance",
    "toolchain-layering",
    "partition-model",
    "task-contract-template",
    "context-entry-template",
    "writeback-log-template",
    "decision-record-template",
    "module-entry-template",
]
OUTDATED_PLACEHOLDER_PHRASES = {
    "docs/knowledge/foundations/toolchain-layering.md": [
        "`research/` 目录当前只保留占位入口，不承载 active runner；其中 `OpenCode` 仍是 research backend 预留位",
        "`research/` 与 `evals/` 保留为预留位，只有在方案重新准入后才继续扩展。",
    ],
    "toolchain/scripts/README.md": [
        "`research/`：预留给后续准入的最小研究脚本",
    ],
    "toolchain/evals/README.md": [
        "`memory-side/` 当前只保留占位入口，不承载 active 的 `program / scenarios / scoring database` 一类资产。",
    ],
}
PROMPT_TEMPLATES_DIR = "docs/operations/prompt-templates"
PROMPT_TEMPLATE_REQUIRED_CANONICAL_LINKS = {
    "docs/operations/prompt-templates/README.md": [
        "product/harness-operations/README.md",
    ],
    "docs/operations/prompt-templates/simple-subagent-workflow.md": [
        "product/harness-operations/skills/simple-workflow/references/prompt.md",
    ],
    "docs/operations/prompt-templates/strict-subagent-workflow.md": [
        "product/harness-operations/skills/strict-workflow/references/prompt.md",
    ],
    "docs/operations/prompt-templates/task-planning-contract.md": [
        "product/harness-operations/skills/task-planning-contract/references/prompt.md",
    ],
    "docs/operations/prompt-templates/execution-contract-template.md": [
        "product/harness-operations/skills/execution-contract-template/references/prompt.md",
    ],
    "docs/operations/prompt-templates/review-loop-code-review.md": [
        "product/harness-operations/skills/review-loop-workflow/references/prompt.md",
    ],
    "docs/operations/prompt-templates/task-list-subagent-workflow.md": [
        "product/harness-operations/skills/task-list-workflow/references/prompt.md",
    ],
    "docs/operations/prompt-templates/harness-contract-template.md": [
        "product/harness-operations/skills/harness-contract-shape/references/prompt.md",
    ],
    "docs/operations/prompt-templates/repo-governance-evaluation.md": [
        "product/harness-operations/skills/repo-governance-evaluation/references/prompt.md",
    ],
}
CANONICAL_SKILL_GLOBS = [
    "product/*/skills/*/SKILL.md",
]
ADAPTER_SKILL_GLOBS = [
    "product/memory-side/adapters/*/skills/*/SKILL.md",
    "product/task-interface/adapters/*/skills/*/SKILL.md",
    "product/harness-operations/adapters/*/skills/*/SKILL.md",
]
CANONICAL_SKILL_REQUIRED_HEADINGS = [
    "## Overview",
    "## When To Use",
    "## Workflow",
    "## Hard Constraints",
    "## Expected Output",
    "## Resources",
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
CANONICAL_ENTRYPOINT_REQUIRED_LINKS = {
    "product/memory-side/skills/context-routing-skill/references/entrypoints.md": [
        "docs/knowledge/memory-side/formats/context-routing-output-format.md",
    ],
    "product/memory-side/skills/writeback-cleanup-skill/references/entrypoints.md": [
        "docs/knowledge/memory-side/formats/writeback-cleanup-output-format.md",
    ],
}


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


def collect_repo_relative_code_paths(repo_root: Path, relative_path: str) -> set[str]:
    text = (repo_root / relative_path).read_text(encoding="utf-8")
    return {match.strip() for match in re.findall(r"`([^`]+)`", text) if match.strip()}


def iter_prompt_template_files(repo_root: Path) -> list[Path]:
    prompt_root = repo_root / PROMPT_TEMPLATES_DIR
    if not prompt_root.exists():
        return []
    return sorted(prompt_root.glob("*.md"))


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


def check_prompt_template_knowledge_backlinks(repo_root: Path, report: SemanticReport) -> None:
    prompt_files = iter_prompt_template_files(repo_root)
    if not prompt_files:
        report.add_failure(f"missing prompt template directory: {PROMPT_TEMPLATES_DIR}")
        return

    checked = 0
    for prompt_file in prompt_files:
        checked += 1
        relative_path = to_relative_posix(prompt_file, repo_root)
        resolved_targets = collect_repo_relative_markdown_links(repo_root, relative_path)
        if relative_path.endswith("/README.md"):
            if "docs/knowledge/README.md" not in resolved_targets:
                report.add_failure(
                    f"prompt template entrypoint missing knowledge backlink: {relative_path}"
                )
        elif not any(target.startswith("docs/knowledge/") for target in resolved_targets):
            report.add_failure(
                f"prompt template missing docs/knowledge backlink: {relative_path}"
            )
        for target in PROMPT_TEMPLATE_REQUIRED_CANONICAL_LINKS.get(relative_path, []):
            if target not in resolved_targets:
                report.add_failure(
                    f"prompt template shim missing canonical source link: {relative_path} -> {target}"
                )
    report.add_info(f"checked {checked} prompt template knowledge backlinks")


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

        for heading in CANONICAL_SKILL_REQUIRED_HEADINGS:
            if heading not in text:
                report.add_failure(
                    f"canonical skill missing required heading {heading!r}: {relative_path}"
                )

        for heading in CANONICAL_SKILL_FORBIDDEN_HEADINGS:
            if heading in text:
                report.add_failure(
                    f"canonical skill leaked adapter-style section {heading!r}: {relative_path}"
                )

        references_path = canonical_file.parent / "references/entrypoints.md"
        if not references_path.exists():
            report.add_failure(
                f"canonical skill missing references/entrypoints.md: {relative_path}"
            )
            continue

        if "product/harness-operations/skills/" in relative_path:
            for extra_name in ("prompt.md", "bindings.md"):
                extra_path = canonical_file.parent / "references" / extra_name
                if not extra_path.exists():
                    report.add_failure(
                        f"harness canonical skill missing references/{extra_name}: {relative_path}"
                    )

        references_text = references_path.read_text(encoding="utf-8")
        if "## Reading Policy" not in references_text:
            report.add_failure(
                f"canonical skill references missing reading policy block: {relative_path}"
            )

    report.add_info(f"checked {checked} canonical skill packages for minimal executable shape")


def check_adapter_wrappers_are_thin(repo_root: Path, report: SemanticReport) -> None:
    adapter_files = iter_adapter_skill_files(repo_root)
    if not adapter_files:
        report.add_failure("missing adapter wrapper skills under product/*/adapters/*/skills/*/SKILL.md")
        return

    checked = 0
    for adapter_file in adapter_files:
        checked += 1
        relative_path = to_relative_posix(adapter_file, repo_root)
        text = adapter_file.read_text(encoding="utf-8")
        for heading in THIN_WRAPPER_REQUIRED_HEADINGS:
            if heading not in text:
                report.add_failure(
                    f"adapter wrapper missing required thin-shell heading {heading!r}: {relative_path}"
                )
        for heading in THIN_WRAPPER_FORBIDDEN_HEADINGS:
            if heading in text:
                report.add_failure(
                    f"adapter wrapper still contains forbidden duplicated section {heading!r}: {relative_path}"
                )
    report.add_info(f"checked {checked} adapter wrappers for thin-shell structure")


def check_canonical_entrypoints_cover_required_formats(repo_root: Path, report: SemanticReport) -> None:
    checked = 0
    for relative_path, expected_targets in CANONICAL_ENTRYPOINT_REQUIRED_LINKS.items():
        source = repo_root / relative_path
        if not source.exists():
            report.add_failure(f"missing canonical entrypoints document: {relative_path}")
            continue
        resolved_targets = collect_repo_relative_code_paths(repo_root, relative_path)
        for target in expected_targets:
            checked += 1
            if target not in resolved_targets:
                report.add_failure(
                    f"canonical entrypoints missing required format link: {relative_path} -> {target}"
                )
    report.add_info(f"checked {checked} canonical entrypoint format links")


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    report = SemanticReport()
    check_required_templates(repo_root, report)
    check_required_handoffs(repo_root, report)
    check_foundations_authority_shadows(repo_root, report)
    check_outdated_placeholder_phrases(repo_root, report)
    check_prompt_template_knowledge_backlinks(repo_root, report)
    check_canonical_skill_packages_are_minimal(repo_root, report)
    check_canonical_entrypoints_cover_required_formats(repo_root, report)
    check_adapter_wrappers_are_thin(repo_root, report)

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
