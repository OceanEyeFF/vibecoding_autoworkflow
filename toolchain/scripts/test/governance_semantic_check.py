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

try:
    from cache_scan_policy import CACHE_SCAN_ROOTS
except ModuleNotFoundError:
    from toolchain.scripts.test.cache_scan_policy import CACHE_SCAN_ROOTS
from path_governance_check import REQUIRED_GITIGNORE_ENTRIES, iter_relative_markdown_targets, resolve_markdown_target


REPO_ROOT = Path(__file__).resolve().parents[3]
FOUNDATIONS_DIR = "docs/project-maintenance/foundations"
REQUIRED_TEMPLATE_PATHS = [
    "docs/harness/artifact/worktrack/contract.md",
    "docs/harness/artifact/worktrack/plan-task-queue.md",
    "docs/harness/artifact/worktrack/gate-evidence.md",
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
        "docs/harness/artifact/README.md",
        "docs/harness/workflow-families/README.md",
        "product/harness/README.md",
    ],
    "product/harness/README.md": [
        "docs/harness/README.md",
        "product/harness/skills/README.md",
        "product/harness/adapters/README.md",
    ],
    "docs/harness/artifact/worktrack/README.md": [
        "docs/harness/artifact/worktrack/contract.md",
        "docs/harness/artifact/worktrack/plan-task-queue.md",
        "docs/harness/artifact/worktrack/gate-evidence.md",
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
        "`research/` 与 `evals/` 保留为预留位，只有在方案重新准入后才继续扩展。",
    ],
    "toolchain/scripts/README.md": [
        "`research/`：预留给后续准入的最小研究脚本",
    ],
}
RETIRED_ENTRYPOINT_REFERENCES = {
    "AGENTS.md": [
        "docs/harness/adjacent-systems/memory-side/",
        "docs/harness/adjacent-systems/memory-side/layer-boundary.md",
        "docs/harness/adjacent-systems/memory-side/overview.md",
        "docs/harness/adjacent-systems/memory-side/skill-agent-model.md",
        "docs/harness/adjacent-systems/task-interface/",
        "product/memory-side/README.md",
        "product/memory-side/skills/",
        "product/task-interface/README.md",
        "product/task-interface/skills/",
    ],
    "docs/README.md": [
        "docs/harness/adjacent-systems/memory-side/",
        "docs/harness/adjacent-systems/memory-side/layer-boundary.md",
        "docs/harness/adjacent-systems/memory-side/overview.md",
        "docs/harness/adjacent-systems/memory-side/skill-agent-model.md",
        "docs/harness/adjacent-systems/task-interface/",
    ],
    "docs/harness/README.md": [
        "docs/harness/adjacent-systems/memory-side/",
        "docs/harness/adjacent-systems/memory-side/layer-boundary.md",
        "docs/harness/adjacent-systems/memory-side/overview.md",
        "docs/harness/adjacent-systems/memory-side/skill-agent-model.md",
        "docs/harness/adjacent-systems/task-interface/",
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
REVIEW_VERIFY_HANDBOOK_DOC = "docs/project-maintenance/governance/review-verify-handbook.md"
TOOLCHAIN_TEST_README_DOC = "toolchain/scripts/test/README.md"
CODEX_HARNESS_MANUAL_RUNBOOK_DOC = (
    "docs/project-maintenance/testing/codex-post-deploy-behavior-tests.md"
)
SUBAGENT_DEFAULT_CONTRACT_PATHS = [
    "product/harness/skills/harness-skill/SKILL.md",
    "product/harness/skills/dispatch-skills/SKILL.md",
    "product/harness/skills/set-harness-goal-skill/SKILL.md",
    "product/harness/skills/set-harness-goal-skill/assets/control-state.md",
    "product/harness/skills/set-harness-goal-skill/assets/worktrack/contract.md",
    "product/harness/skills/init-worktrack-skill/templates/contract.template.md",
    "product/.aw_template/control-state.md",
    "product/.aw_template/worktrack/contract.md",
    "docs/harness/artifact/control/control-state.md",
    "docs/harness/artifact/worktrack/contract.md",
    "docs/harness/foundations/Harness运行协议.md",
    "docs/harness/catalog/worktrack.md",
]
AGENTS_ADAPTER_SKILLS_DIR = "product/harness/adapters/agents/skills"
MANUAL_RUNBOOK_AGENTS_SKILL_COUNT_RE = re.compile(
    r"当前 `agents` install 已包含全部 (?P<count>\d+) 个 skills"
)
CLOSEOUT_ACCEPTANCE_GATE_STEPS = [
    "scope_gate",
    "spec_gate",
    "static_gate",
    "cache_gate",
    "test_gate",
    "smoke_gate",
]
SUBAGENT_DEFAULT_REQUIRED_TERMS = [
    "默认",
    "SubAgent",
    "权限边界",
    "subagent_dispatch_mode",
    "subagent_dispatch_mode_override_scope",
    "worktrack-contract-primary",
    "global-override",
    "runtime_dispatch_mode",
    "auto",
    "delegated",
    "current-carrier",
    "runtime fallback",
    "dispatch package unsafe",
]
REVIEW_EVIDENCE_FOUR_LANE_CONTRACT_PATHS = [
    "product/harness/skills/review-evidence-skill/SKILL.md",
    "docs/harness/catalog/worktrack.md",
    "product/harness/skills/set-harness-goal-skill/assets/worktrack/gate-evidence.md",
    "docs/harness/artifact/worktrack/gate-evidence.md",
]
REVIEW_EVIDENCE_FOUR_LANE_REQUIRED_TERMS = [
    "并行",
    "SubAgent",
    "fallback",
    "static-semantic-review",
    "test-review",
    "project-security-review",
    "complexity-performance-review",
    "静态语义解释",
    "测试 review",
    "security review",
    "代码复杂度和性能 review",
]
REPO_WHATS_NEXT_OVERVIEW_FALLBACK_CONTRACT_PATHS = [
    "product/harness/skills/repo-whats-next-skill/SKILL.md",
    "product/harness/skills/repo-whats-next-skill/references/overview-fallback-mode.md",
    "docs/harness/catalog/repo.md",
]
REPO_WHATS_NEXT_OVERVIEW_FALLBACK_REQUIRED_TERMS = [
    "overview fallback",
    "project-dialectic-planning-skill",
    "candidate_worktracks",
    "top_candidate",
    "Facts / Inferences / Unknowns",
    "不创建工作追踪",
    "不改变 Harness 控制状态",
]
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
BYTECODE_FREE_COMMAND_EXCLUDED_PATTERNS = (
    re.compile(
        r"docs/project-maintenance/testing/"
        r"codex-harness-manual-run-continuous-\d{4}-\d{2}-\d{2}\.md"
    ),
)
REPO_PYTHON_COMMAND_RE = re.compile(
    r"\bpython(?:3)?\s+(?:"
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


def check_retired_entrypoint_references(repo_root: Path, report: SemanticReport) -> None:
    checked = 0
    for relative_path, retired_references in RETIRED_ENTRYPOINT_REFERENCES.items():
        path = repo_root / relative_path
        if not path.exists():
            report.add_failure(f"missing retired entrypoint scan source: {relative_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for retired_reference in retired_references:
            checked += 1
            if retired_reference in text:
                report.add_failure(
                    "retired entrypoint reference still present: "
                    f"{relative_path} -> {retired_reference}"
                )
    report.add_info(f"checked {checked} retired entrypoint references")


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


def is_bytecode_free_command_excluded(relative_path: str) -> bool:
    return any(pattern.fullmatch(relative_path) for pattern in BYTECODE_FREE_COMMAND_EXCLUDED_PATTERNS)


def check_repo_python_commands_are_bytecode_free(repo_root: Path, report: SemanticReport) -> None:
    checked = 0
    for command_file in iter_bytecode_free_command_files(repo_root):
        relative_path = to_relative_posix(command_file, repo_root)
        if is_bytecode_free_command_excluded(relative_path):
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


def check_review_verify_docs_list_closeout_steps(repo_root: Path, report: SemanticReport) -> None:
    doc_path = repo_root / REVIEW_VERIFY_HANDBOOK_DOC
    if not doc_path.exists():
        report.add_failure(f"missing review/verify handbook: {REVIEW_VERIFY_HANDBOOK_DOC}")
        return

    text = doc_path.read_text(encoding="utf-8")
    checked = 0
    for step in CLOSEOUT_ACCEPTANCE_GATE_STEPS:
        checked += 1
        if step not in text:
            report.add_failure(
                f"review/verify handbook missing closeout gate step {step!r}: "
                f"{REVIEW_VERIFY_HANDBOOK_DOC}"
            )
    report.add_info(f"checked {checked} documented closeout gate steps")


def check_docs_list_closeout_cache_roots(repo_root: Path, report: SemanticReport) -> None:
    checked = 0
    for relative_path in (REVIEW_VERIFY_HANDBOOK_DOC, TOOLCHAIN_TEST_README_DOC):
        doc_path = repo_root / relative_path
        if not doc_path.exists():
            report.add_failure(f"missing closeout cache root document: {relative_path}")
            continue
        text = doc_path.read_text(encoding="utf-8")
        for root in CACHE_SCAN_ROOTS:
            checked += 1
            if f"`{root}/`" not in text:
                report.add_failure(f"document missing closeout cache root {root!r}: {relative_path}")
    report.add_info(f"checked {checked} documented closeout cache roots")


def count_agents_adapter_payload_skills(repo_root: Path, report: SemanticReport) -> int | None:
    skills_dir = repo_root / AGENTS_ADAPTER_SKILLS_DIR
    if not skills_dir.is_dir():
        report.add_failure(f"missing agents adapter skills directory: {AGENTS_ADAPTER_SKILLS_DIR}")
        return None

    count = 0
    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir():
            continue
        payload_path = child / "payload.json"
        if payload_path.is_file():
            count += 1
    if count == 0:
        report.add_failure(f"agents adapter skills directory has no payload sources: {AGENTS_ADAPTER_SKILLS_DIR}")
        return None
    return count


def check_manual_runbook_agents_skill_count(repo_root: Path, report: SemanticReport) -> None:
    expected_count = count_agents_adapter_payload_skills(repo_root, report)
    doc_path = repo_root / CODEX_HARNESS_MANUAL_RUNBOOK_DOC
    if not doc_path.exists():
        report.add_failure(f"missing Codex Harness manual runbook: {CODEX_HARNESS_MANUAL_RUNBOOK_DOC}")
        return

    text = doc_path.read_text(encoding="utf-8")
    match = MANUAL_RUNBOOK_AGENTS_SKILL_COUNT_RE.search(text)
    if match is None:
        report.add_failure(
            "Codex Harness manual runbook missing agents skill count claim: "
            f"{CODEX_HARNESS_MANUAL_RUNBOOK_DOC}"
        )
        return

    documented_count = int(match.group("count"))
    if expected_count is not None and documented_count != expected_count:
        report.add_failure(
            "Codex Harness manual runbook agents skill count mismatch: "
            f"{CODEX_HARNESS_MANUAL_RUNBOOK_DOC} documents {documented_count}, "
            f"adapter payload source has {expected_count}"
        )
    report.add_info("checked Codex Harness manual runbook agents skill count")


def check_subagent_dispatch_default_contract(repo_root: Path, report: SemanticReport) -> None:
    checked = 0
    for relative_path in SUBAGENT_DEFAULT_CONTRACT_PATHS:
        path = repo_root / relative_path
        if not path.exists():
            report.add_failure(f"missing SubAgent default contract source: {relative_path}")
            continue
        checked += 1
        text = path.read_text(encoding="utf-8")
        for term in SUBAGENT_DEFAULT_REQUIRED_TERMS:
            if term not in text:
                report.add_failure(
                    f"SubAgent default contract missing required term {term!r}: {relative_path}"
                )
    report.add_info(f"checked {checked} SubAgent default dispatch contract sources")


def check_review_evidence_four_lane_contract(repo_root: Path, report: SemanticReport) -> None:
    checked = 0
    for relative_path in REVIEW_EVIDENCE_FOUR_LANE_CONTRACT_PATHS:
        path = repo_root / relative_path
        if not path.exists():
            report.add_failure(f"missing review evidence four-lane contract source: {relative_path}")
            continue
        checked += 1
        text = path.read_text(encoding="utf-8")
        for term in REVIEW_EVIDENCE_FOUR_LANE_REQUIRED_TERMS:
            if term not in text:
                report.add_failure(
                    f"review evidence four-lane contract missing required term {term!r}: {relative_path}"
                )
    report.add_info(f"checked {checked} review evidence four-lane contract sources")


def check_repo_whats_next_overview_fallback_contract(
    repo_root: Path, report: SemanticReport
) -> None:
    checked = 0
    for relative_path in REPO_WHATS_NEXT_OVERVIEW_FALLBACK_CONTRACT_PATHS:
        path = repo_root / relative_path
        if not path.exists():
            report.add_failure(f"missing repo whats-next overview fallback source: {relative_path}")
            continue
        checked += 1
        text = path.read_text(encoding="utf-8")
        for term in REPO_WHATS_NEXT_OVERVIEW_FALLBACK_REQUIRED_TERMS:
            if term not in text:
                report.add_failure(
                    f"repo whats-next overview fallback missing required term {term!r}: {relative_path}"
                )
    report.add_info(f"checked {checked} repo whats-next overview fallback sources")


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    report = SemanticReport()
    check_required_templates(repo_root, report)
    check_required_handoffs(repo_root, report)
    check_foundations_authority_shadows(repo_root, report)
    check_outdated_placeholder_phrases(repo_root, report)
    check_retired_entrypoint_references(repo_root, report)
    check_canonical_skill_packages_are_minimal(repo_root, report)
    check_adapter_wrappers_are_thin(repo_root, report)
    check_append_request_contract_terms(repo_root, report)
    check_repo_python_commands_are_bytecode_free(repo_root, report)
    check_root_tool_shims_disable_bytecode(repo_root, report)
    check_path_governance_docs_list_gitignore_entries(repo_root, report)
    check_review_verify_docs_list_closeout_steps(repo_root, report)
    check_docs_list_closeout_cache_roots(repo_root, report)
    check_manual_runbook_agents_skill_count(repo_root, report)
    check_subagent_dispatch_default_contract(repo_root, report)
    check_review_evidence_four_lane_contract(repo_root, report)
    check_repo_whats_next_overview_fallback_contract(repo_root, report)

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
