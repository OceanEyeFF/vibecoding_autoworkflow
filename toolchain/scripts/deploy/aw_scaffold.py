#!/usr/bin/env python3
"""Initialize `.aw` scaffold artifacts from `product/.aw_template/`."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_ROOT = REPO_ROOT / "product" / ".aw_template"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / ".aw"
DEFAULT_PROFILE = "first-wave-minimal"
KEYED_LINE_PATTERN = re.compile(r"^(?P<indent>\s*)- (?P<key>[a-z0-9_]+):\s*(?P<value>.*)$")
CHECKBOX_LINE_PATTERN = re.compile(r"^(\d+)\. \[ \]\s*$")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


class ScaffoldError(RuntimeError):
    """Raised when template validation or rendering fails."""


@dataclass(frozen=True)
class TemplateSpec:
    """Static contract for one `.aw_template` source."""

    template_id: str
    source_relpath: str
    output_relpath: str
    artifact_type: str
    title: str
    instance_note: str
    required_sections: tuple[str, ...]
    required_keyed_fields_by_section: tuple[tuple[str, tuple[str, ...]], ...]
    required_nested_keyed_fields_by_section: tuple[tuple[str, tuple[str, ...]], ...] = ()

    @property
    def source_path(self) -> Path:
        return REPO_ROOT / self.source_relpath

    @property
    def output_path(self) -> Path:
        return Path(self.output_relpath)


TEMPLATE_SPECS = {
    "control-state": TemplateSpec(
        template_id="control-state",
        source_relpath="product/.aw_template/control-state.md",
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
        source_relpath="product/.aw_template/goal-charter.md",
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
        source_relpath="product/.aw_template/repo/snapshot-status.md",
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
        source_relpath="product/.aw_template/repo/analysis.md",
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
    "worktrack-contract": TemplateSpec(
        template_id="worktrack-contract",
        source_relpath="product/.aw_template/worktrack/contract.md",
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
        source_relpath="product/.aw_template/worktrack/plan-task-queue.md",
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
        source_relpath="product/.aw_template/worktrack/gate-evidence.md",
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

PROFILE_TEMPLATES = {
    DEFAULT_PROFILE: (
        "control-state",
        "goal-charter",
        "repo-snapshot-status",
        "repo-analysis",
        "worktrack-contract",
        "worktrack-plan-task-queue",
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
        description="Generate and validate `.aw` scaffold artifacts from product/.aw_template."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    list_parser = subparsers.add_parser("list", help="List known profiles and templates.")
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit profile/template metadata as JSON.",
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate source templates for required sections and keyed fields.",
    )
    add_selection_args(validate_parser)

    generate_parser = subparsers.add_parser(
        "generate",
        help="Render one profile or template set into an `.aw` output root.",
    )
    add_selection_args(generate_parser)
    generate_parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Output directory for generated `.aw` artifacts. Defaults to <repo>/.aw.",
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
    generate_parser.add_argument(
        "--repo",
        default=REPO_ROOT.name,
        help="Repo name placeholder. Defaults to the current repo directory name.",
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
        help="Baseline branch placeholder for repo/worktrack artifacts.",
    )
    generate_parser.add_argument(
        "--worktrack-id",
        help="Worktrack identifier placeholder for worktrack/control artifacts.",
    )
    generate_parser.add_argument(
        "--branch",
        help="Branch placeholder for worktrack contract artifacts.",
    )

    return parser.parse_args(argv)


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
        help="Select all known templates.",
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
        raise ScaffoldError("choose only one of --profile, --template, or --all")

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

    selected_specs: list[TemplateSpec] = []
    seen: set[str] = set()
    for template_id in template_ids:
        if template_id in seen:
            continue
        seen.add(template_id)
        selected_specs.append(TEMPLATE_SPECS[template_id])
    return selected_specs


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
                # Nested headings still belong to the nearest top-level section.
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
        raise ScaffoldError(f"{spec.source_relpath} failed validation: {joined}")

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

        if h1_seen and not note_rewritten and line.startswith("> "):
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

        if line == "- ":
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
        "generated_from": spec.source_relpath,
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
        raise ScaffoldError(
            f"refusing to overwrite existing file without --force: {output_path}"
        )

    if dry_run:
        print(f"would write {output_path}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered_text, encoding="utf-8")
    print(f"wrote {output_path}")


def preflight_output_paths(
    selected_specs: list[TemplateSpec],
    *,
    output_root: Path,
    force: bool,
) -> None:
    for spec in selected_specs:
        output_path = output_root / spec.output_path
        if output_path.exists() and not force:
            raise ScaffoldError(
                f"refusing to overwrite existing file without --force: {output_path}"
            )


def run_list(json_mode: bool) -> int:
    if json_mode:
        payload = {
            "profiles": PROFILE_TEMPLATES,
            "templates": {
                template_id: {
                    "source": spec.source_relpath,
                    "output": spec.output_relpath,
                    "artifact_type": spec.artifact_type,
                }
                for template_id, spec in TEMPLATE_SPECS.items()
            },
        }
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 0

    print("profiles:")
    for profile_name, template_ids in PROFILE_TEMPLATES.items():
        joined = ", ".join(template_ids)
        print(f"  - {profile_name}: {joined}")
    print("templates:")
    for template_id, spec in TEMPLATE_SPECS.items():
        print(f"  - {template_id}: {spec.source_relpath} -> {spec.output_relpath}")
    return 0


def run_validate(selected_specs: list[TemplateSpec]) -> int:
    had_issue = False
    for spec in selected_specs:
        issues = validate_template_source(spec)
        if issues:
            had_issue = True
            print(f"[{spec.template_id}] invalid: {spec.source_relpath}")
            for issue in issues:
                print(f"  - {issue}")
            continue
        print(f"[{spec.template_id}] ok: {spec.source_relpath}")
    return 1 if had_issue else 0


def run_generate(selected_specs: list[TemplateSpec], args: argparse.Namespace) -> int:
    output_root = args.output_root
    selected_template_ids = {spec.template_id for spec in selected_specs}
    rendered_templates: list[tuple[TemplateSpec, str]] = []
    for spec in selected_specs:
        rendered = render_template(
            spec=spec,
            selected_template_ids=selected_template_ids,
            args=args,
        )
        rendered_templates.append((spec, rendered))

    preflight_output_paths(
        selected_specs,
        output_root=output_root,
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
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.mode == "list":
            return run_list(args.json)

        selected_specs = resolve_selected_specs(args)
        if args.mode == "validate":
            return run_validate(selected_specs)
        if args.mode == "generate":
            return run_generate(selected_specs, args)
        raise ScaffoldError(f"unsupported mode: {args.mode}")
    except ScaffoldError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
