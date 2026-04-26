#!/usr/bin/env python3
"""Generate skill-owned `.aw` bootstrap artifacts from set-harness-goal-skill assets."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AW_DIRNAME = ".aw"
DEFAULT_PROFILE = "full-deploy-bootstrap"
DEFAULT_CLAUDE_SKILL_ROOT = Path(".claude") / "skills"
DEFAULT_CLAUDE_SKILL_NAME = "aw-set-harness-goal-skill"
SKILL_PACKAGE_EXCLUDED_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "aw.marker",
    "payload.json",
}
KEYED_LINE_PATTERN = re.compile(r"^(?P<indent>\s*)- (?P<key>[a-z0-9_]+):\s*(?P<value>.*)$")
CHECKBOX_LINE_PATTERN = re.compile(r"^(\d+)\. \[ \]\s*$")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


class DeployAwError(RuntimeError):
    """Raised when asset validation or rendering fails."""


@dataclass(frozen=True)
class TemplateSpec:
    """Structured asset contract for one rendered `.aw` template."""

    template_id: str
    source_relpath: str
    output_relpath: str
    artifact_type: str
    title: str
    instance_note: str
    required_sections: tuple[str, ...]
    required_keyed_fields_by_section: tuple[tuple[str, tuple[str, ...]], ...]
    required_nested_keyed_fields_by_section: tuple[tuple[str, tuple[str, ...]], ...] = ()
    inject_instance_note: bool = True

    @property
    def source_path(self) -> Path:
        raw_path = Path(self.source_relpath)
        if raw_path.is_absolute():
            return raw_path
        return SKILL_ROOT / raw_path

    @property
    def source_display_path(self) -> str:
        raw_path = Path(self.source_relpath)
        if raw_path.is_absolute():
            return raw_path.as_posix()
        return Path(SKILL_ROOT.name, self.source_relpath).as_posix()

    @property
    def output_path(self) -> Path:
        return Path(self.output_relpath)


@dataclass(frozen=True)
class CopyAssetSpec:
    """Static asset copied verbatim into the generated `.aw` tree."""

    asset_id: str
    source_relpath: str
    output_relpath: str

    @property
    def source_path(self) -> Path:
        return SKILL_ROOT / self.source_relpath

    @property
    def source_display_path(self) -> str:
        return Path(SKILL_ROOT.name, self.source_relpath).as_posix()

    @property
    def output_path(self) -> Path:
        return Path(self.output_relpath)


TEMPLATE_SPECS = {
    "control-state": TemplateSpec(
        template_id="control-state",
        source_relpath="assets/control-state.md",
        output_relpath="control-state.md",
        artifact_type="control-state",
        title="Harness Control State",
        instance_note=(
            "这是 `.aw/control-state.md` 的运行样例，用来维护当前 Harness supervisor 的控制面状态，"
            "不要把业务真相写进来。"
        ),
        required_sections=(
            "Metadata",
            "Current Control Level",
            "Active Worktrack",
            "Baseline Branch",
            "Current Next Action",
            "Linked Formal Documents",
            "Approval Boundary",
            "Continuation Authority",
            "Handback Guard",
            "Baseline Traceability",
            "Autonomy Ledger",
            "Notes",
        ),
        required_keyed_fields_by_section=(
            ("Metadata", ("updated", "owner")),
            ("Current Control Level", ("repo_scope", "worktrack_scope")),
            (
                "Linked Formal Documents",
                (
                    "repo_snapshot",
                    "repo_analysis",
                    "worktrack_contract",
                    "plan_task_queue",
                    "gate_evidence",
                ),
            ),
            ("Approval Boundary", ("needs_programmer_approval", "reason")),
            (
                "Baseline Traceability",
                (
                    "last_verified_checkpoint",
                    "checkpoint_type",
                    "checkpoint_ref",
                    "verified_at",
                    "if_no_commit_reason",
                    "alternative_traceability",
                ),
            ),
        ),
    ),
    "goal-charter": TemplateSpec(
        template_id="goal-charter",
        source_relpath="assets/goal-charter.md",
        output_relpath="goal-charter.md",
        artifact_type="goal-charter",
        title="Repo Goal / Charter",
        instance_note=(
            "这是 `.aw/goal-charter.md` 的运行样例，用来记录当前 repo 的长期目标和方向。"
            "最终内容应与 `docs/harness/artifact/repo/goal-charter.md` 的定义一致。"
        ),
        required_sections=(
            "Metadata",
            "Project Vision",
            "Core Product Goals",
            "Technical Direction",
            "Engineering Node Map",
            "Success Criteria",
            "System Invariants",
            "Notes",
        ),
        required_keyed_fields_by_section=(
            ("Metadata", ("repo", "owner", "updated", "status")),
            (
                "Engineering Node Map",
                ("type", "if_worktrack_interrupted", "if_no_merge"),
            ),
        ),
        required_nested_keyed_fields_by_section=(
            (
                "Engineering Node Map",
                (
                    "expected_count",
                    "merge_required",
                    "baseline_form",
                    "gate_criteria",
                    "if_interrupted_strategy",
                ),
            ),
        ),
    ),
    "repo-snapshot-status": TemplateSpec(
        template_id="repo-snapshot-status",
        source_relpath="assets/repo/snapshot-status.md",
        output_relpath="repo/snapshot-status.md",
        artifact_type="repo-snapshot-status",
        title="Repo Snapshot / Status",
        instance_note=(
            "这是 `.aw/repo/snapshot-status.md` 的运行样例，用来记录当前 repo 的慢变量观测面。"
            "最终内容应与 `docs/harness/artifact/repo/snapshot-status.md` 的定义一致。"
        ),
        required_sections=(
            "Metadata",
            "Mainline Status",
            "Architecture And Module Map",
            "Active Branches And Purpose",
            "Governance Status",
            "Known Issues And Risks",
            "Notes",
        ),
        required_keyed_fields_by_section=(
            ("Metadata", ("repo", "baseline_branch", "updated", "status")),
            (
                "Mainline Status",
                (
                    "baseline_branch",
                    "last_verified_checkpoint",
                    "checkpoint_ref",
                    "checkpoint_type",
                ),
            ),
        ),
    ),
    "repo-analysis": TemplateSpec(
        template_id="repo-analysis",
        source_relpath="assets/repo/analysis.md",
        output_relpath="repo/analysis.md",
        artifact_type="repo-analysis",
        title="Repo Analysis",
        instance_note=(
            "这是 `.aw/repo/analysis.md` 的运行样例，用来记录 RepoScope 的阶段性分析与"
            "优先级判断。它是决策支撑 artifact，不是 goal truth。"
        ),
        required_sections=(
            "Metadata",
            "Facts",
            "Inferences",
            "Unknowns",
            "Main Contradiction",
            "Priority Judgment",
            "Routing Projection",
            "Writeback Eligibility",
            "Notes",
        ),
        required_keyed_fields_by_section=(
            ("Metadata", ("repo", "baseline_branch", "baseline_ref", "updated", "analysis_status")),
            ("Main Contradiction", ("current_main_contradiction", "main_aspect")),
            ("Priority Judgment", ("current_highest_priority", "long_term_highest_priority", "do_not_do_now")),
            (
                "Routing Projection",
                (
                    "recommended_repo_action",
                    "recommended_next_route",
                    "suggested_node_type",
                    "continuation_ready",
                    "continuation_blockers",
                ),
            ),
            ("Writeback Eligibility", ("writeback_eligibility",)),
        ),
    ),
    "repo-discovery-input": TemplateSpec(
        template_id="repo-discovery-input",
        source_relpath="assets/repo/discovery-input.md",
        output_relpath="repo/discovery-input.md",
        artifact_type="repo-discovery-input",
        title="Repo Discovery Input",
        instance_note=(
            "这是 `.aw/repo/discovery-input.md` 的运行样例，用于 Existing Code Project "
            "Adoption 模式下记录既有代码库的只读事实输入。它不是 goal truth。"
        ),
        required_sections=(
            "Metadata",
            "Source Materials",
            "Repository Facts",
            "Architecture And Module Inventory",
            "Build, Test, And Runtime Signals",
            "Governance And Documentation Signals",
            "Risks And Unknowns",
            "Candidate Goal Signals",
            "Confirmation Questions",
            "Downstream Mapping Notes",
            "Notes",
        ),
        required_keyed_fields_by_section=(
            ("Metadata", ("repo", "owner", "updated", "adoption_mode", "source_scope", "generated_by")),
            (
                "Source Materials",
                (
                    "repository_path",
                    "baseline_branch",
                    "current_branch",
                    "current_commit",
                    "working_tree_state",
                    "user_provided_context",
                    "inspected_paths",
                    "skipped_paths",
                ),
            ),
            (
                "Repository Facts",
                (
                    "primary_language_or_stack",
                    "package_or_build_system",
                    "runtime_entrypoints",
                    "test_entrypoints",
                    "deploy_or_release_entrypoints",
                    "configuration_files",
                ),
            ),
            (
                "Build, Test, And Runtime Signals",
                (
                    "build_commands_seen",
                    "test_commands_seen",
                    "runtime_commands_seen",
                    "commands_not_run",
                ),
            ),
            (
                "Governance And Documentation Signals",
                (
                    "existing_docs",
                    "agent_or_harness_instructions",
                    "ownership_or_layering_rules",
                    "review_or_verify_rules",
                    "known_policy_constraints",
                ),
            ),
            (
                "Downstream Mapping Notes",
                ("goal_charter_inputs", "snapshot_status_inputs", "control_state_links"),
            ),
        ),
    ),
    "worktrack-contract": TemplateSpec(
        template_id="worktrack-contract",
        source_relpath="assets/worktrack/contract.md",
        output_relpath="worktrack/contract.md",
        artifact_type="worktrack-contract",
        title="Worktrack Contract",
        instance_note=(
            "这是 `.aw/worktrack/contract.md` 的运行样例，用来填写单个 worktrack 的局部状态转移合同。"
            "最终内容应与 `docs/harness/artifact/worktrack/contract.md` 的定义一致。"
        ),
        required_sections=(
            "Metadata",
            "Node Type",
            "Task Goal",
            "Scope",
            "Non-Goals",
            "Impacted Modules",
            "Planned Next State",
            "Acceptance Criteria",
            "Constraints",
            "Verification Requirements",
            "Rollback Conditions",
            "Notes",
        ),
        required_keyed_fields_by_section=(
            (
                "Metadata",
                (
                    "worktrack_id",
                    "branch",
                    "baseline_branch",
                    "baseline_ref",
                    "owner",
                    "updated",
                    "contract_status",
                ),
            ),
            (
                "Node Type",
                (
                    "type",
                    "source_from_goal_charter",
                    "baseline_form",
                    "merge_required",
                    "gate_criteria",
                    "if_interrupted_strategy",
                ),
            ),
        ),
    ),
    "worktrack-plan-task-queue": TemplateSpec(
        template_id="worktrack-plan-task-queue",
        source_relpath="assets/worktrack/plan-task-queue.md",
        output_relpath="worktrack/plan-task-queue.md",
        artifact_type="worktrack-plan-task-queue",
        title="Plan / Task Queue",
        instance_note=(
            "这是 `.aw/worktrack/plan-task-queue.md` 的运行样例，用来把 worktrack contract "
            "展开成当前执行队列。"
        ),
        required_sections=(
            "Metadata",
            "Task List",
            "Execution Order Notes",
            "Dependencies",
            "Current Blockers",
            "Current Next Action",
            "Dispatch Handoff Packet",
            "Readiness",
            "Notes",
        ),
        required_keyed_fields_by_section=(
            (
                "Metadata",
                ("worktrack_id", "updated", "current_phase", "contract_ref", "queue_status"),
            ),
            (
                "Current Next Action",
                ("selected_next_action_id", "selected_next_action", "selection_reason"),
            ),
            (
                "Dispatch Handoff Packet",
                (
                    "task",
                    "goal_for_this_round",
                    "node_type",
                    "gate_criteria_for_this_round",
                    "baseline_policy",
                    "constraints_for_this_round",
                    "acceptance_criteria_for_this_round",
                    "verification_requirements",
                    "done_signal",
                    "required_context",
                    "return_to_schedule_if",
                ),
            ),
            ("Readiness", ("dispatch_packet_ready", "recommended_next_route")),
        ),
    ),
    "worktrack-gate-evidence": TemplateSpec(
        template_id="worktrack-gate-evidence",
        source_relpath="assets/worktrack/gate-evidence.md",
        output_relpath="worktrack/gate-evidence.md",
        artifact_type="worktrack-gate-evidence",
        title="Gate Evidence",
        instance_note=(
            "这是 `.aw/worktrack/gate-evidence.md` 的运行样例，用来记录当前 worktrack 的 "
            "gate 证据与裁决依据。"
        ),
        required_sections=(
            "Metadata",
            "Review Lane",
            "Validation Lane",
            "Policy Lane",
            "Evidence Assessment",
            "Per-Surface Verdicts",
            "Recommended Next Route",
            "Follow-up Actions",
        ),
        required_keyed_fields_by_section=(
            ("Metadata", ("worktrack_id", "updated", "gate_round", "required_evidence_lanes")),
            (
                "Review Lane",
                (
                    "input_ref",
                    "freshness",
                    "confidence",
                    "missing_evidence",
                    "residual_risks",
                    "upstream_constraint_signals",
                    "low_severity_absorption_applied",
                    "ready_for_gate",
                ),
            ),
            (
                "Validation Lane",
                (
                    "input_ref",
                    "freshness",
                    "confidence",
                    "missing_evidence",
                    "residual_risks",
                    "upstream_constraint_signals",
                    "low_severity_absorption_applied",
                    "ready_for_gate",
                ),
            ),
            (
                "Policy Lane",
                (
                    "input_ref",
                    "freshness",
                    "confidence",
                    "missing_evidence",
                    "residual_risks",
                    "upstream_constraint_signals",
                    "low_severity_absorption_applied",
                    "ready_for_gate",
                ),
            ),
            (
                "Evidence Assessment",
                (
                    "node_type",
                    "node_type_source",
                    "applied_gate_criteria",
                    "fallback_used",
                    "overall_confidence",
                    "overall_confidence_reason",
                    "freshness_blockers",
                ),
            ),
            (
                "Per-Surface Verdicts",
                (
                    "implementation_surface",
                    "validation_surface",
                    "policy_surface",
                    "low_severity_absorption_reason",
                ),
            ),
            (
                "Recommended Next Route",
                (
                    "allowed_next_routes",
                    "recommended_next_route",
                    "approval_required",
                    "approval_scope",
                    "approval_reason",
                    "needs_programmer_approval",
                    "why",
                ),
            ),
        ),
    ),
}

STATIC_ASSET_SPECS = {
    "template-readme": CopyAssetSpec(
        asset_id="template-readme",
        source_relpath="assets/template/README.md",
        output_relpath="template/README.md",
    ),
    "goal-charter-template": CopyAssetSpec(
        asset_id="goal-charter-template",
        source_relpath="assets/template/goal-charter.template.md",
        output_relpath="template/goal-charter.template.md",
    ),
    "repo-readme": CopyAssetSpec(
        asset_id="repo-readme",
        source_relpath="assets/repo/README.md",
        output_relpath="repo/README.md",
    ),
    "worktrack-readme": CopyAssetSpec(
        asset_id="worktrack-readme",
        source_relpath="assets/worktrack/README.md",
        output_relpath="worktrack/README.md",
    ),
}

PROFILE_TEMPLATES = {
    DEFAULT_PROFILE: (
        "control-state",
        "goal-charter",
        "repo-snapshot-status",
        "repo-analysis",
        "worktrack-contract",
        "worktrack-plan-task-queue",
        "worktrack-gate-evidence",
    ),
}

PROFILE_STATIC_ASSETS = {
    DEFAULT_PROFILE: (
        "template-readme",
        "goal-charter-template",
        "repo-readme",
        "worktrack-readme",
    ),
}

LINKED_PATH_FIELDS = {
    "repo_snapshot": "repo-snapshot-status",
    "repo_analysis": "repo-analysis",
    "worktrack_contract": "worktrack-contract",
    "plan_task_queue": "worktrack-plan-task-queue",
    "gate_evidence": "worktrack-gate-evidence",
}

SECTION_VALUE_FIELDS = {
    "Active Worktrack": "worktrack_id",
    "Baseline Branch": "baseline_branch",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=(
            "Generate and validate `.aw` bootstrap artifacts from "
            "set-harness-goal-skill-owned assets."
        ),
        epilog=(
            "Examples:\n"
            f"  PYTHONDONTWRITEBYTECODE=1 python3 {Path(__file__).name} validate\n"
            f"  PYTHONDONTWRITEBYTECODE=1 python3 {Path(__file__).name} generate --deploy-path \"$DEPLOY_PATH\" --owner aw-kernel\n"
            f"  PYTHONDONTWRITEBYTECODE=1 python3 {Path(__file__).name} generate --deploy-path \"$DEPLOY_PATH\" --install-claude-skill\n"
            f"  PYTHONDONTWRITEBYTECODE=1 python3 {Path(__file__).name} install-claude-skill --deploy-path \"$DEPLOY_PATH\"\n"
            f"  DEPLOY_PATH=/path/to/worktree PYTHONDONTWRITEBYTECODE=1 python3 {Path(__file__).name} generate --force --dry-run\n"
            "\n"
            "Path semantics:\n"
            "  --deploy-path points at the target repo/worktree root.\n"
            f"  Generated files are written under <deploy-path>/{DEFAULT_AW_DIRNAME}/.\n"
            f"  Claude skill installs are written under <deploy-path>/{DEFAULT_CLAUDE_SKILL_ROOT.as_posix()}/.\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    list_parser = subparsers.add_parser("list", help="List known profiles, templates, and copied assets.")
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit profile/template metadata as JSON.",
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate structured `.aw` source assets for required sections and keyed fields.",
    )
    add_selection_args(validate_parser)

    generate_parser = subparsers.add_parser(
        "generate",
        help="Render one profile or template set into <deploy-path>/.aw.",
    )
    add_selection_args(generate_parser)
    generate_parser.add_argument(
        "--deploy-path",
        type=Path,
        help=(
            "Target repo/worktree root. Generated files go under <deploy-path>/.aw. "
            "If omitted, the script falls back to the DEPLOY_PATH environment variable."
        ),
    )
    generate_parser.add_argument(
        "--force",
        action="store_true",
        help="Allow overwriting existing generated files.",
    )
    generate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned writes without changing files.",
    )
    add_claude_skill_args(generate_parser, include_install_flag=True)
    generate_parser.add_argument(
        "--no-static-assets",
        action="store_true",
        help="Do not copy static helper assets such as `.aw/template/*` and `worktrack/README.md`.",
    )
    generate_parser.add_argument(
        "--adoption-mode",
        choices=("new-goal-initialization", "existing-code-adoption"),
        default="new-goal-initialization",
        help=(
            "Initialization mode. existing-code-adoption also renders "
            ".aw/repo/discovery-input.md when using a profile/default generation."
        ),
    )
    generate_parser.add_argument(
        "--repo",
        help="Repo name placeholder. Defaults to the basename of --deploy-path.",
    )
    generate_parser.add_argument(
        "--owner",
        help="Owner placeholder to write into generated artifacts.",
    )
    generate_parser.add_argument(
        "--updated",
        default=date.today().isoformat(),
        help="Date to stamp into generated artifacts. Defaults to today.",
    )
    generate_parser.add_argument(
        "--baseline-branch",
        help=(
            "Baseline branch for repo/worktrack artifacts. Required unless the script "
            "can verify one from AW_BASELINE_BRANCH, origin/HEAD, or a unique "
            "main/master ref."
        ),
    )
    generate_parser.add_argument(
        "--worktrack-id",
        help="Worktrack identifier placeholder for worktrack/control artifacts.",
    )
    generate_parser.add_argument(
        "--branch",
        help="Branch placeholder for worktrack contract artifacts.",
    )

    claude_parser = subparsers.add_parser(
        "install-claude-skill",
        help="Install this skill package into <deploy-path>/.claude/skills.",
    )
    claude_parser.add_argument(
        "--deploy-path",
        type=Path,
        help=(
            "Target repo/worktree root. If omitted, the script falls back to the "
            "DEPLOY_PATH environment variable."
        ),
    )
    claude_parser.add_argument(
        "--force",
        action="store_true",
        help="Allow overwriting existing files for this skill package.",
    )
    claude_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned writes without changing files.",
    )
    add_claude_skill_args(claude_parser, include_install_flag=False)

    return parser.parse_args(argv)


def add_claude_skill_args(
    parser: argparse.ArgumentParser,
    *,
    include_install_flag: bool,
) -> None:
    if include_install_flag:
        parser.add_argument(
            "--install-claude-skill",
            action="store_true",
            help="Also install this skill package under <deploy-path>/.claude/skills.",
        )
    parser.add_argument(
        "--claude-root",
        type=Path,
        help=(
            "Override the Claude skills target root. Defaults to "
            "<deploy-path>/.claude/skills."
        ),
    )


def add_selection_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_TEMPLATES),
        help=f"Use one named template bundle. Defaults to {DEFAULT_PROFILE} for generate.",
    )
    parser.add_argument(
        "--template",
        action="append",
        choices=sorted(TEMPLATE_SPECS),
        help="Select one or more individual template ids.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Select all known structured templates.",
    )


def placeholder(name: str) -> str:
    return f"TODO({slugify(name)})"


def slugify(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") or "value"


def resolve_selected_specs(args: argparse.Namespace) -> list[TemplateSpec]:
    selection_modes = 0
    if args.profile:
        selection_modes += 1
    if args.template:
        selection_modes += 1
    if getattr(args, "all", False):
        selection_modes += 1
    if selection_modes > 1:
        raise DeployAwError("choose only one of --profile, --template, or --all")

    if args.template:
        template_ids = args.template
    elif args.profile:
        template_ids = list(PROFILE_TEMPLATES[args.profile])
    elif getattr(args, "all", False):
        template_ids = list(TEMPLATE_SPECS)
    elif args.mode == "generate":
        template_ids = list(PROFILE_TEMPLATES[DEFAULT_PROFILE])
    else:
        template_ids = list(TEMPLATE_SPECS)

    if (
        args.mode == "generate"
        and args.adoption_mode == "existing-code-adoption"
        and not args.template
        and "repo-discovery-input" not in template_ids
    ):
        template_ids.insert(template_ids.index("repo-snapshot-status"), "repo-discovery-input")

    selected_specs: list[TemplateSpec] = []
    seen: set[str] = set()
    for template_id in template_ids:
        if template_id in seen:
            continue
        seen.add(template_id)
        selected_specs.append(TEMPLATE_SPECS[template_id])
    return selected_specs


def resolve_deploy_path(args: argparse.Namespace) -> Path:
    raw_value = args.deploy_path
    if raw_value is None:
        env_value = os.environ.get("DEPLOY_PATH")
        if env_value:
            raw_value = Path(env_value)

    if raw_value is None:
        raise DeployAwError(
            "missing deploy path: pass --deploy-path <repo-or-worktree-root> or set DEPLOY_PATH"
        )

    deploy_path = raw_value.expanduser().resolve()
    if not deploy_path.exists():
        raise DeployAwError(f"deploy path does not exist: {deploy_path}")
    if not deploy_path.is_dir():
        raise DeployAwError(f"deploy path must be a directory: {deploy_path}")
    return deploy_path


def aw_output_root_for(deploy_path: Path) -> Path:
    return deploy_path / DEFAULT_AW_DIRNAME


def repo_name_for(args: argparse.Namespace, deploy_path: Path) -> str:
    return args.repo or deploy_path.name


def run_git_output(repo_root: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None


def git_ref_exists(repo_root: Path, ref: str) -> bool:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "show-ref", "--verify", "--quiet", ref],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return False
    return completed.returncode == 0


def resolve_baseline_branch(args: argparse.Namespace, deploy_path: Path) -> str:
    if args.baseline_branch and args.baseline_branch.strip():
        return args.baseline_branch.strip()

    env_value = (os.environ.get("AW_BASELINE_BRANCH") or "").strip()
    if env_value:
        return env_value

    origin_head = run_git_output(
        deploy_path, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"
    )
    if origin_head:
        baseline = origin_head.removeprefix("origin/").strip()
        if baseline:
            return baseline

    remote_candidates = [
        branch
        for branch in ("main", "master")
        if git_ref_exists(deploy_path, f"refs/remotes/origin/{branch}")
    ]
    if len(remote_candidates) == 1:
        return remote_candidates[0]
    if len(remote_candidates) > 1:
        raise DeployAwError(
            "ambiguous remote baseline branches: both origin/main and origin/master exist; "
            "pass --baseline-branch"
        )

    local_candidates = [
        branch
        for branch in ("main", "master")
        if git_ref_exists(deploy_path, f"refs/heads/{branch}")
    ]
    if len(local_candidates) == 1:
        return local_candidates[0]
    if len(local_candidates) > 1:
        raise DeployAwError(
            "ambiguous local baseline branches: both main and master exist; pass --baseline-branch"
        )

    raise DeployAwError(
        "unable to resolve baseline branch: pass --baseline-branch or set "
        "AW_BASELINE_BRANCH; origin/HEAD is unavailable and no unique main/master "
        "branch ref could verify a baseline"
    )


def resolve_static_asset_specs(args: argparse.Namespace) -> list[CopyAssetSpec]:
    if getattr(args, "no_static_assets", False):
        return []
    if getattr(args, "template", None):
        return []
    profile = args.profile or DEFAULT_PROFILE
    asset_ids = PROFILE_STATIC_ASSETS.get(profile, ())
    return [STATIC_ASSET_SPECS[asset_id] for asset_id in asset_ids]


def validate_template_source(spec: TemplateSpec) -> list[str]:
    source_path = spec.source_path
    if not source_path.is_file():
        return [f"missing template source: {source_path}"]

    text = source_path.read_text(encoding="utf-8")
    heading, sections, keyed_fields_by_section, nested_keyed_fields_by_section = (
        parse_template_structure(text)
    )
    issues: list[str] = []
    if heading != spec.title:
        issues.append(f"expected title {spec.title!r}, got {heading!r}")

    for section in spec.required_sections:
        if section not in sections:
            issues.append(f"missing required section: {section}")

    for section_name, required_fields in spec.required_keyed_fields_by_section:
        if section_name not in sections:
            continue
        actual_fields = keyed_fields_by_section.get(section_name, set())
        for field_name in required_fields:
            if field_name not in actual_fields:
                issues.append(
                    f"missing keyed field in section {section_name}: {field_name}"
                )

    for section_name, required_fields in spec.required_nested_keyed_fields_by_section:
        if section_name not in sections:
            continue
        actual_fields = nested_keyed_fields_by_section.get(section_name, set())
        for field_name in required_fields:
            if field_name not in actual_fields:
                issues.append(
                    f"missing nested keyed field in section {section_name}: {field_name}"
                )

    return issues


def validate_static_asset_source(spec: CopyAssetSpec) -> list[str]:
    if not spec.source_path.is_file():
        return [f"missing static asset source: {spec.source_path}"]
    if spec.asset_id != "goal-charter-template":
        return []

    text = spec.source_path.read_text(encoding="utf-8")
    heading, sections, keyed_fields_by_section, nested_keyed_fields_by_section = (
        parse_template_structure(text)
    )
    issues: list[str] = []
    if heading != "Repo Goal / Charter Answer Template":
        issues.append(
            f"expected title 'Repo Goal / Charter Answer Template', got {heading!r}"
        )
    for section in (
        "Metadata",
        "Project Vision",
        "Core Product Goals",
        "Technical Direction",
        "Engineering Node Map",
        "Success Criteria",
        "System Invariants",
        "Notes",
    ):
        if section not in sections:
            issues.append(f"missing required section: {section}")

    engineering_fields = keyed_fields_by_section.get("Engineering Node Map", set())
    for field_name in ("type", "if_worktrack_interrupted", "if_no_merge"):
        if field_name not in engineering_fields:
            issues.append(
                f"missing keyed field in section Engineering Node Map: {field_name}"
            )

    nested_engineering_fields = nested_keyed_fields_by_section.get(
        "Engineering Node Map", set()
    )
    for field_name in (
        "expected_count",
        "merge_required",
        "baseline_form",
        "gate_criteria",
        "if_interrupted_strategy",
    ):
        if field_name not in nested_engineering_fields:
            issues.append(
                f"missing nested keyed field in section Engineering Node Map: {field_name}"
            )
    return issues


def parse_template_structure(
    text: str,
) -> tuple[str | None, set[str], dict[str, set[str]], dict[str, set[str]]]:
    heading: str | None = None
    sections: set[str] = set()
    keyed_fields_by_section: dict[str, set[str]] = {}
    nested_keyed_fields_by_section: dict[str, set[str]] = {}
    current_section: str | None = None

    for line in text.splitlines():
        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            if level == 1:
                if heading is None:
                    heading = title
                current_section = None
            elif level == 2:
                current_section = title
                sections.add(title)
                keyed_fields_by_section.setdefault(title, set())
            else:
                # Nested subsections are still part of the nearest required
                # top-level template section for validation purposes.
                pass
            continue

        if current_section is None:
            continue

        keyed_match = KEYED_LINE_PATTERN.match(line)
        if keyed_match:
            fields_by_section = (
                nested_keyed_fields_by_section
                if keyed_match.group("indent")
                else keyed_fields_by_section
            )
            fields_by_section.setdefault(current_section, set()).add(
                keyed_match.group("key")
            )

    return heading, sections, keyed_fields_by_section, nested_keyed_fields_by_section


def render_template(
    spec: TemplateSpec,
    selected_template_ids: set[str],
    args: argparse.Namespace,
) -> str:
    issues = validate_template_source(spec)
    if issues:
        joined = "; ".join(issues)
        raise DeployAwError(f"{spec.source_display_path} failed validation: {joined}")

    source_text = spec.source_path.read_text(encoding="utf-8")
    rendered_lines: list[str] = []
    current_section = ""
    h1_seen = False
    note_rewritten = False
    for line in source_text.splitlines():
        if line.startswith("# "):
            h1_seen = True
            rendered_lines.append(line)
            continue

        if spec.inject_instance_note and h1_seen and not note_rewritten and line.startswith("> "):
            rendered_lines.append(f"> {spec.instance_note}")
            note_rewritten = True
            continue

        if line.startswith("## "):
            current_section = line[3:].strip()
            rendered_lines.append(line)
            continue

        keyed_match = KEYED_LINE_PATTERN.match(line)
        if keyed_match:
            indent = keyed_match.group("indent")
            key = keyed_match.group("key")
            value = resolve_keyed_value(
                key=key,
                selected_template_ids=selected_template_ids,
                args=args,
            )
            rendered_lines.append(f"{indent}- {key}: {value}")
            continue

        checkbox_match = CHECKBOX_LINE_PATTERN.match(line)
        if checkbox_match:
            index = checkbox_match.group(1)
            rendered_lines.append(f"{index}. [ ] {placeholder(f'task_{index}')}")
            continue

        if line in ("-", "- "):
            rendered_lines.append(f"- {resolve_blank_value(current_section, args)}")
            continue

        rendered_lines.append(line)

    body = "\n".join(rendered_lines).rstrip() + "\n"
    return render_frontmatter(spec, args) + "\n" + body


def resolve_keyed_value(
    *,
    key: str,
    selected_template_ids: set[str],
    args: argparse.Namespace,
) -> str:
    direct_values = {
        "repo": args.repo,
        "owner": args.owner or placeholder("owner"),
        "updated": args.updated,
        "adoption_mode": getattr(args, "adoption_mode", "new-goal-initialization"),
        "repository_path": str(getattr(args, "deploy_path", "") or placeholder("repository_path")),
        "baseline_branch": args.baseline_branch or placeholder("baseline_branch"),
        "baseline_ref": args.baseline_branch or placeholder("baseline_ref"),
        "worktrack_id": args.worktrack_id or placeholder("worktrack_id"),
        "branch": args.branch or placeholder("branch"),
        "status": placeholder("status"),
        "current_phase": placeholder("current_phase"),
        "gate_round": placeholder("gate_round"),
        "repo_scope": placeholder("repo_scope"),
        "worktrack_scope": placeholder("worktrack_scope"),
        "needs_programmer_approval": placeholder("needs_programmer_approval"),
        "reason": placeholder("reason"),
        "why": placeholder("why"),
        "pass": "pending",
    }
    if key in direct_values:
        return direct_values[key]

    linked_template_id = LINKED_PATH_FIELDS.get(key)
    if linked_template_id is not None:
        linked_spec = TEMPLATE_SPECS[linked_template_id]
        if linked_template_id in selected_template_ids:
            return linked_spec.output_path.as_posix()
        return placeholder(key)

    return placeholder(key)


def resolve_blank_value(section: str, args: argparse.Namespace) -> str:
    aliased_key = SECTION_VALUE_FIELDS.get(section)
    if aliased_key == "worktrack_id" and args.worktrack_id:
        return args.worktrack_id
    if aliased_key == "baseline_branch" and args.baseline_branch:
        return args.baseline_branch
    return placeholder(section)


def render_frontmatter(spec: TemplateSpec, args: argparse.Namespace) -> str:
    frontmatter = {
        "title": spec.title,
        "artifact_type": spec.artifact_type,
        "generated_from": spec.source_display_path,
        "updated": args.updated,
        "owner": args.owner or placeholder("owner"),
    }
    rendered = ["---"]
    for key, value in frontmatter.items():
        rendered.append(f"{key}: {json.dumps(str(value), ensure_ascii=True)}")
    rendered.append("---")
    return "\n".join(rendered)


def write_rendered_template(
    spec: TemplateSpec,
    rendered_text: str,
    *,
    output_root: Path,
    force: bool,
    dry_run: bool,
) -> None:
    output_path = output_root / spec.output_path
    if output_path.exists() and not force:
        raise DeployAwError(
            f"refusing to overwrite existing file without --force: {output_path}"
        )

    if dry_run:
        print(f"would write {output_path}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered_text, encoding="utf-8")
    print(f"wrote {output_path}")


def copy_static_asset(
    spec: CopyAssetSpec,
    *,
    output_root: Path,
    force: bool,
    dry_run: bool,
) -> None:
    output_path = output_root / spec.output_path
    if output_path.exists() and not force:
        raise DeployAwError(
            f"refusing to overwrite existing file without --force: {output_path}"
        )
    if dry_run:
        print(f"would copy {output_path}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(spec.source_path, output_path)
    print(f"copied {output_path}")


def preflight_output_paths(
    selected_specs: list[TemplateSpec],
    static_assets: list[CopyAssetSpec],
    *,
    output_root: Path,
    force: bool,
) -> None:
    for spec in selected_specs:
        output_path = output_root / spec.output_path
        if output_path.exists() and not force:
            raise DeployAwError(
                f"refusing to overwrite existing file without --force: {output_path}"
            )
    for spec in static_assets:
        output_path = output_root / spec.output_path
        if output_path.exists() and not force:
            raise DeployAwError(
                f"refusing to overwrite existing file without --force: {output_path}"
            )


def claude_skill_root_for(args: argparse.Namespace, deploy_path: Path) -> Path:
    raw_root = getattr(args, "claude_root", None)
    if raw_root is not None:
        return raw_root.expanduser()
    return deploy_path / DEFAULT_CLAUDE_SKILL_ROOT


def claude_skill_target_dir_for(args: argparse.Namespace, deploy_path: Path) -> Path:
    return claude_skill_root_for(args, deploy_path) / DEFAULT_CLAUDE_SKILL_NAME


def should_copy_skill_package_path(path: Path) -> bool:
    if any(part in SKILL_PACKAGE_EXCLUDED_NAMES for part in path.parts):
        return False
    return path.is_file() and path.suffix not in {".pyc", ".pyo"}


def collect_skill_package_files() -> list[tuple[Path, Path]]:
    package_files: list[tuple[Path, Path]] = []
    for source_path in sorted(SKILL_ROOT.rglob("*")):
        if not should_copy_skill_package_path(source_path):
            continue
        package_files.append((source_path, source_path.relative_to(SKILL_ROOT)))
    if not package_files:
        raise DeployAwError(f"no skill package files found under {SKILL_ROOT}")
    return package_files


def absolute_path_without_resolve(path: Path) -> Path:
    return Path(os.path.abspath(path))


def is_current_skill_dir(path: Path) -> bool:
    if path.is_symlink():
        return False
    if absolute_path_without_resolve(path) == absolute_path_without_resolve(SKILL_ROOT):
        return True
    return path.exists() and path.resolve() == SKILL_ROOT.resolve()


def preflight_claude_skill_target_path(target_skill_dir: Path) -> None:
    target_path = absolute_path_without_resolve(target_skill_dir)
    for candidate in [*reversed(target_path.parents), target_path]:
        if candidate.is_symlink() and not candidate.is_dir():
            raise DeployAwError(
                f"Claude skill target ancestor is not a directory: {candidate}"
            )
        if candidate.exists() and not candidate.is_dir():
            raise DeployAwError(
                f"Claude skill target ancestor is not a directory: {candidate}"
            )


def preflight_existing_claude_skill_tree(target_skill_dir: Path) -> None:
    for root, dirs, files in os.walk(target_skill_dir, followlinks=False):
        for name in [*dirs, *files]:
            child = Path(root) / name
            if child.is_symlink():
                raise DeployAwError(
                    f"refusing to install through symlinked Claude skill directory: {child}"
                )


def preflight_claude_skill_parent(path: Path, *, target_skill_dir: Path) -> None:
    relative_parent = path.relative_to(target_skill_dir)
    candidate = target_skill_dir
    candidates = [candidate]
    for part in relative_parent.parts:
        candidate = candidate / part
        candidates.append(candidate)

    for candidate in candidates:
        if candidate.is_symlink():
            raise DeployAwError(
                f"refusing to install through symlinked Claude skill directory: {candidate}"
            )
        if candidate.exists() and not candidate.is_dir():
            raise DeployAwError(
                f"Claude skill target ancestor is not a directory: {candidate}"
            )


def preflight_claude_skill_copy_target(
    target_path: Path,
    *,
    target_skill_dir: Path,
    force: bool,
) -> None:
    if target_path.is_symlink():
        raise DeployAwError(
            f"refusing to overwrite symlinked Claude skill file: {target_path}"
        )

    preflight_claude_skill_parent(
        target_path.parent,
        target_skill_dir=target_skill_dir,
    )

    if target_path.exists():
        if target_path.is_dir():
            raise DeployAwError(
                f"Claude skill target file path is a directory: {target_path}"
            )
        if not force:
            raise DeployAwError(
                f"refusing to overwrite existing Claude skill file without --force: {target_path}"
            )


def preflight_claude_skill_install(
    package_files: list[tuple[Path, Path]],
    *,
    target_skill_dir: Path,
    force: bool,
) -> None:
    if target_skill_dir.is_symlink():
        raise DeployAwError(
            f"refusing to install into symlinked Claude skill dir: {target_skill_dir}"
        )
    preflight_claude_skill_target_path(target_skill_dir)
    if is_current_skill_dir(target_skill_dir):
        return
    if target_skill_dir.exists() and not target_skill_dir.is_dir():
        raise DeployAwError(
            f"Claude skill target exists but is not a directory: {target_skill_dir}"
        )
    if target_skill_dir.exists():
        preflight_existing_claude_skill_tree(target_skill_dir)

    for _, relative_path in package_files:
        target_path = target_skill_dir / relative_path
        preflight_claude_skill_copy_target(
            target_path,
            target_skill_dir=target_skill_dir,
            force=force,
        )


def install_claude_skill_package(
    package_files: list[tuple[Path, Path]],
    *,
    target_skill_dir: Path,
    force: bool,
    dry_run: bool,
) -> None:
    preflight_claude_skill_install(
        package_files,
        target_skill_dir=target_skill_dir,
        force=force,
    )
    if is_current_skill_dir(target_skill_dir):
        print(f"Claude skill already installed at {target_skill_dir}")
        return

    if dry_run:
        print(
            f"would install Claude skill {DEFAULT_CLAUDE_SKILL_NAME} -> {target_skill_dir}"
        )
        for _, relative_path in package_files:
            print(f"would copy {target_skill_dir / relative_path}")
        return

    for source_path, relative_path in package_files:
        target_path = target_skill_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        preflight_claude_skill_copy_target(
            target_path,
            target_skill_dir=target_skill_dir,
            force=force,
        )
        shutil.copy2(source_path, target_path)
        if target_path.is_symlink():
            raise DeployAwError(
                f"refusing to chmod symlinked Claude skill file: {target_path}"
            )
        target_path.chmod(0o644)
    print(f"installed Claude skill {DEFAULT_CLAUDE_SKILL_NAME} -> {target_skill_dir}")


def run_list(json_mode: bool) -> int:
    if json_mode:
        payload = {
            "profiles": {
                profile_name: {
                    "templates": list(template_ids),
                    "static_assets": list(PROFILE_STATIC_ASSETS.get(profile_name, ())),
                }
                for profile_name, template_ids in PROFILE_TEMPLATES.items()
            },
            "templates": {
                template_id: {
                    "source": spec.source_display_path,
                    "output": spec.output_relpath,
                    "artifact_type": spec.artifact_type,
                }
                for template_id, spec in TEMPLATE_SPECS.items()
            },
            "static_assets": {
                asset_id: {
                    "source": spec.source_display_path,
                    "output": spec.output_relpath,
                }
                for asset_id, spec in STATIC_ASSET_SPECS.items()
            },
        }
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 0

    print("profiles:")
    for profile_name, template_ids in PROFILE_TEMPLATES.items():
        rendered = ", ".join(template_ids)
        copied = ", ".join(PROFILE_STATIC_ASSETS.get(profile_name, ())) or "(none)"
        print(f"  - {profile_name}: render [{rendered}] copy [{copied}]")
    print("templates:")
    for template_id, spec in TEMPLATE_SPECS.items():
        print(f"  - {template_id}: {spec.source_display_path} -> {spec.output_relpath}")
    print("static assets:")
    for asset_id, spec in STATIC_ASSET_SPECS.items():
        print(f"  - {asset_id}: {spec.source_display_path} -> {spec.output_relpath}")
    return 0


def run_validate(selected_specs: list[TemplateSpec], static_assets: list[CopyAssetSpec]) -> int:
    had_issue = False
    for spec in selected_specs:
        issues = validate_template_source(spec)
        if issues:
            had_issue = True
            print(f"[{spec.template_id}] invalid: {spec.source_display_path}")
            for issue in issues:
                print(f"  - {issue}")
            continue
        print(f"[{spec.template_id}] ok: {spec.source_display_path}")

    for spec in static_assets:
        issues = validate_static_asset_source(spec)
        if issues:
            had_issue = True
            print(f"[{spec.asset_id}] invalid: {spec.source_display_path}")
            for issue in issues:
                print(f"  - {issue}")
            continue
        print(f"[{spec.asset_id}] ok: {spec.source_display_path}")

    return 1 if had_issue else 0


def run_generate(
    selected_specs: list[TemplateSpec],
    static_assets: list[CopyAssetSpec],
    args: argparse.Namespace,
) -> int:
    deploy_path = resolve_deploy_path(args)
    args.deploy_path = deploy_path
    output_root = aw_output_root_for(deploy_path)
    install_claude_skill = getattr(args, "install_claude_skill", False)
    claude_package_files = collect_skill_package_files() if install_claude_skill else []
    claude_target_dir = (
        claude_skill_target_dir_for(args, deploy_path) if install_claude_skill else None
    )
    args.repo = repo_name_for(args, deploy_path)
    args.baseline_branch = resolve_baseline_branch(args, deploy_path)
    selected_template_ids = {spec.template_id for spec in selected_specs}
    rendered_templates: list[tuple[TemplateSpec, str]] = []
    for spec in selected_specs:
        rendered = render_template(
            spec=spec,
            selected_template_ids=selected_template_ids,
            args=args,
        )
        rendered_templates.append((spec, rendered))
    for spec in static_assets:
        issues = validate_static_asset_source(spec)
        if issues:
            joined = "; ".join(issues)
            raise DeployAwError(f"{spec.source_display_path} failed validation: {joined}")

    preflight_output_paths(
        selected_specs,
        static_assets,
        output_root=output_root,
        force=args.force,
    )
    if install_claude_skill and claude_target_dir is not None:
        preflight_claude_skill_install(
            claude_package_files,
            target_skill_dir=claude_target_dir,
            force=args.force,
        )

    for spec, rendered in rendered_templates:
        write_rendered_template(
            spec,
            rendered,
            output_root=output_root,
            force=args.force,
            dry_run=args.dry_run,
        )
    for spec in static_assets:
        copy_static_asset(
            spec,
            output_root=output_root,
            force=args.force,
            dry_run=args.dry_run,
        )
    if install_claude_skill and claude_target_dir is not None:
        install_claude_skill_package(
            claude_package_files,
            target_skill_dir=claude_target_dir,
            force=args.force,
            dry_run=args.dry_run,
        )
    return 0


def run_install_claude_skill(args: argparse.Namespace) -> int:
    deploy_path = resolve_deploy_path(args)
    package_files = collect_skill_package_files()
    target_skill_dir = claude_skill_target_dir_for(args, deploy_path)
    install_claude_skill_package(
        package_files,
        target_skill_dir=target_skill_dir,
        force=args.force,
        dry_run=args.dry_run,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.mode == "list":
            return run_list(args.json)
        if args.mode == "install-claude-skill":
            return run_install_claude_skill(args)

        selected_specs = resolve_selected_specs(args)
        static_assets = resolve_static_asset_specs(args)
        if args.mode == "validate":
            return run_validate(selected_specs, static_assets)
        if args.mode == "generate":
            return run_generate(selected_specs, static_assets, args)
        raise DeployAwError(f"unsupported mode: {args.mode}")
    except DeployAwError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
