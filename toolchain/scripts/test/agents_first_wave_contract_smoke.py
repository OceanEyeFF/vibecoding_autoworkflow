#!/usr/bin/env python3
"""Run a repeatable first-wave agents contract smoke path."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
DEPLOY_SCRIPTS_DIR = REPO_ROOT / "toolchain" / "scripts" / "deploy"
if str(DEPLOY_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(DEPLOY_SCRIPTS_DIR))

import adapter_deploy  # noqa: E402
import aw_scaffold  # noqa: E402


FIRST_WAVE_SKILL_ORDER = (
    "harness-skill",
    "repo-status-skill",
    "repo-whats-next-skill",
    "init-worktrack-skill",
    "schedule-worktrack-skill",
    "dispatch-skills",
)

MINIMUM_PROTOCOL_FIELDS = {
    "harness-skill": (
        "current_scope",
        "artifacts_read",
        "status_or_verdict",
        "allowed_next_routes",
        "recommended_next_route",
        "continuation_ready",
        "recommended_next_scope",
        "recommended_next_action",
        "continuation_decision",
        "stop_conditions_hit",
        "approval_required",
        "needs_approval",
    ),
    "repo-status-skill": (
        "current_scope",
        "snapshot_basis",
        "mainline_status",
        "governance_signals",
        "allowed_next_routes",
        "recommended_next_route",
        "continuation_ready",
        "handoff_signals",
        "needs_supervisor_decision",
    ),
    "repo-whats-next-skill": (
        "mode",
        "mode_trigger_reason",
        "recommended_repo_action",
        "recommended_next_route",
        "recommended_next_scope",
        "allowed_repo_actions",
        "selection_reason",
        "continuation_ready",
        "approval_required",
        "needs_programmer_approval",
    ),
    "init-worktrack-skill": (
        "worktrack_id",
        "worktrack_identity",
        "branch_name_or_rule",
        "baseline_ref",
        "constraints",
        "initialization_status",
        "next_action",
        "initial_queue_items",
        "schedule_handoff_packet",
        "recommended_next_route",
        "executor_handoff_packet",
        "execution_not_started",
        "continuation_ready",
    ),
    "schedule-worktrack-skill": (
        "current_worktrack_state",
        "queue_changes",
        "ready_tasks",
        "blocked_or_deferred_tasks",
        "selected_next_action_id",
        "selected_next_action",
        "selection_reason",
        "dispatch_task_brief_draft",
        "dispatch_packet_ready",
        "dispatch_ready",
        "recommended_next_route",
        "recommended_next_skill_or_route",
    ),
    "dispatch-skills": (
        "handoff_packet_source",
        "dispatch_packet_status",
        "dispatch_contract_gaps",
        "selected_executor",
        "runtime_dispatch_mode",
        "selection_reason",
        "fallback_used",
        "task",
        "verification_requirements",
        "done_signal",
        "evidence_collected",
        "return_route_if_not_dispatched",
        "recommended_next_action",
    ),
}

KEYED_LINE_TEMPLATE = r"^- {key}:\s*.*$"
class SmokeError(RuntimeError):
    """Raised when the contract smoke path cannot be completed."""


@dataclass(frozen=True)
class InstalledSkill:
    """Installed first-wave skill plus its canonical tracing metadata."""

    skill_id: str
    target_dir: Path
    wrapper_path: Path
    payload_path: Path
    marker_path: Path
    wrapper_text: str
    payload: dict[str, Any]
    canonical_skill_path: Path
    canonical_text: str
    output_fields: tuple[str, ...]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the repeatable agents first-wave contract smoke path with an isolated install root and "
            "generated .aw fixture."
        )
    )
    parser.add_argument(
        "--agents-root",
        type=Path,
        help="Optional agents target root. Defaults to a temporary isolated workspace.",
    )
    parser.add_argument(
        "--aw-root",
        type=Path,
        help="Optional .aw artifact root. Defaults to a temporary isolated workspace.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the auto-created temporary workspace instead of deleting it.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON only.",
    )
    return parser.parse_args(argv)


def capture_stdout(fn, *args, **kwargs):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        result = fn(*args, **kwargs)
    return result, buffer.getvalue()


def json_ready_verify_result(result: adapter_deploy.VerifyResult) -> dict[str, Any]:
    return {
        "backend": result.backend,
        "target_root": str(result.target_root),
        "issues": [
            {
                "code": issue.code,
                "path": str(issue.path),
                "detail": issue.detail,
            }
            for issue in result.issues
        ],
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_skill_path_from_payload(payload: dict[str, Any], skill_id: str) -> Path:
    canonical_paths = payload.get("canonical_paths")
    if not isinstance(canonical_paths, list) or not canonical_paths:
        raise SmokeError(f"{skill_id} payload is missing canonical_paths")

    skill_paths = [
        REPO_ROOT / canonical_path
        for canonical_path in canonical_paths
        if isinstance(canonical_path, str) and canonical_path.endswith("/SKILL.md")
    ]
    if len(skill_paths) != 1:
        raise SmokeError(f"{skill_id} payload must expose exactly one canonical SKILL.md")
    return skill_paths[0]


def extract_output_fields(canonical_text: str, skill_id: str) -> tuple[str, ...]:
    marker = "Inside the result, include at least these fields or equivalents:"
    lines = canonical_text.splitlines()
    fields: list[str] = []
    collecting = False
    for line in lines:
        stripped = line.strip()
        if stripped == marker:
            collecting = True
            continue
        if not collecting:
            continue
        match = re.match(r"^- `?([a-z0-9_]+)`?\s*$", stripped)
        if match:
            fields.append(match.group(1))
            continue
        if fields and stripped:
            break
        if fields and not stripped:
            break

    if not fields:
        raise SmokeError(f"{skill_id} canonical skill does not expose an output field list")
    return tuple(fields)


def assert_installed_payload_contract(skill: InstalledSkill) -> None:
    if skill.payload.get("payload_policy") != "canonical-copy":
        raise SmokeError(
            f"{skill.skill_id} payload_policy drifted: {skill.payload.get('payload_policy')!r}"
        )
    if skill.payload.get("reference_distribution") != "copy-listed-canonical-paths":
        raise SmokeError(
            f"{skill.skill_id} reference_distribution drifted: "
            f"{skill.payload.get('reference_distribution')!r}"
        )
    if skill.payload.get("target_entry_name") != "SKILL.md":
        raise SmokeError(f"{skill.skill_id} target_entry_name drifted from SKILL.md")

    try:
        canonical_source = adapter_deploy.payload_canonical_source_metadata(
            skill.payload,
            SimpleNamespace(skill_id=skill.skill_id),
        )
    except adapter_deploy.DeployError as exc:
        raise SmokeError(f"{skill.skill_id} payload canonical source is invalid: {exc}") from exc

    required_payload_files = skill.payload.get("required_payload_files")
    expected_required_payload_files = [*canonical_source.included_paths, "payload.json", "aw.marker"]
    if required_payload_files != expected_required_payload_files:
        raise SmokeError(
            f"{skill.skill_id} required_payload_files drifted: {required_payload_files!r}"
        )

    canonical_paths = skill.payload.get("canonical_paths")
    if not isinstance(canonical_paths, list) or not canonical_paths:
        raise SmokeError(f"{skill.skill_id} payload is missing canonical_paths")
    for included_path, canonical_path in canonical_source.canonical_files_by_relative_path.items():
        target_path = skill.target_dir / included_path
        if not canonical_path.is_file():
            raise SmokeError(f"{skill.skill_id} canonical path does not exist: {canonical_path}")
        if not target_path.is_file():
            raise SmokeError(f"{skill.skill_id} target copy is missing: {target_path}")
        if canonical_path.read_text(encoding="utf-8") != target_path.read_text(encoding="utf-8"):
            raise SmokeError(f"{skill.skill_id} target copy drifted from canonical source: {target_path}")

    missing_fields = [
        field_name
        for field_name in MINIMUM_PROTOCOL_FIELDS[skill.skill_id]
        if field_name not in skill.output_fields
    ]
    if missing_fields:
        raise SmokeError(
            f"{skill.skill_id} canonical output contract is missing required fields: "
            f"{', '.join(missing_fields)}"
        )


def discover_installed_skills(agents_root: Path) -> dict[str, InstalledSkill]:
    installed: dict[str, InstalledSkill] = {}
    for skill_id in FIRST_WAVE_SKILL_ORDER:
        target_dir = agents_root / skill_id
        wrapper_path = target_dir / "SKILL.md"
        payload_path = target_dir / "payload.json"
        marker_path = target_dir / "aw.marker"
        if not wrapper_path.is_file():
            raise SmokeError(f"missing installed skill entry for {skill_id}: {wrapper_path}")
        if not payload_path.is_file():
            raise SmokeError(f"missing installed payload descriptor for {skill_id}: {payload_path}")
        if not marker_path.is_file():
            raise SmokeError(f"missing runtime marker for {skill_id}: {marker_path}")

        wrapper_text = wrapper_path.read_text(encoding="utf-8")
        payload = load_json(payload_path)
        canonical_skill_path = canonical_skill_path_from_payload(payload, skill_id)
        canonical_text = canonical_skill_path.read_text(encoding="utf-8")
        installed_skill = InstalledSkill(
            skill_id=skill_id,
            target_dir=target_dir,
            wrapper_path=wrapper_path,
            payload_path=payload_path,
            marker_path=marker_path,
            wrapper_text=wrapper_text,
            payload=payload,
            canonical_skill_path=canonical_skill_path,
            canonical_text=canonical_text,
            output_fields=extract_output_fields(canonical_text, skill_id),
        )
        assert_installed_payload_contract(installed_skill)
        installed[skill_id] = installed_skill
    return installed


def scaffold_args(aw_root: Path) -> argparse.Namespace:
    return argparse.Namespace(
        mode="generate",
        profile=aw_scaffold.DEFAULT_PROFILE,
        template=None,
        all=False,
        output_root=aw_root,
        force=True,
        dry_run=False,
        repo="vibecoding_autoworkflow",
        owner="aw-kernel",
        updated="2026-04-17",
        baseline_branch="main",
        worktrack_id="wt-first-wave-contract-smoke",
        branch="feature/agents-first-wave-contract-smoke",
    )


def replace_keyed_value(path: Path, key: str, value: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(KEYED_LINE_TEMPLATE.format(key=re.escape(key)), flags=re.MULTILINE)
    replaced, count = pattern.subn(f"- {key}: {value}", text, count=1)
    if count != 1:
        raise SmokeError(f"could not update keyed field {key} in {path}")
    path.write_text(replaced, encoding="utf-8")


def replace_section_bullet(path: Path, section: str, value: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"(## {re.escape(section)}\n\n)- .*?$",
        flags=re.MULTILINE,
    )
    replaced, count = pattern.subn(rf"\1- {value}", text, count=1)
    if count != 1:
        raise SmokeError(f"could not update section bullet {section} in {path}")
    path.write_text(replaced, encoding="utf-8")


def replace_checkbox(path: Path, index: int, value: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"^{index}\. \[ \].*$", flags=re.MULTILINE)
    replaced, count = pattern.subn(f"{index}. [ ] {value}", text, count=1)
    if count != 1:
        raise SmokeError(f"could not update task {index} in {path}")
    path.write_text(replaced, encoding="utf-8")


def seed_aw_fixture(aw_root: Path) -> None:
    args = scaffold_args(aw_root)
    selected_specs = aw_scaffold.resolve_selected_specs(args)
    _, render_log = capture_stdout(aw_scaffold.run_generate, selected_specs, args)
    if not render_log.strip():
        raise SmokeError("aw_scaffold generate produced no output")

    control_state = aw_root / "control-state.md"
    goal_charter = aw_root / "goal-charter.md"
    repo_snapshot = aw_root / "repo" / "snapshot-status.md"

    replace_keyed_value(control_state, "repo_scope", "RepoScope.observing")
    replace_keyed_value(control_state, "worktrack_scope", "inactive")
    replace_keyed_value(control_state, "needs_programmer_approval", "no")
    replace_keyed_value(
        control_state,
        "reason",
        "repeatable first-wave contract smoke stays inside the C2 boundary",
    )
    replace_section_bullet(control_state, "Active Worktrack", "wt-first-wave-contract-smoke")
    replace_section_bullet(control_state, "Baseline Branch", "main")
    replace_section_bullet(control_state, "Current Next Action", "repo-status-skill")
    replace_section_bullet(
        control_state,
        "Notes",
        "generated and seeded by toolchain/scripts/test/agents_first_wave_contract_smoke.py",
    )

    replace_keyed_value(goal_charter, "status", "active-contract-smoke-fixture")
    replace_section_bullet(
        goal_charter,
        "Project Vision",
        "Ship a Codex-first harness platform with a repeatable first-wave agents contract smoke path.",
    )
    replace_section_bullet(
        goal_charter,
        "Core Product Goals",
        "Keep C2 limited to installed skill-copy payloads plus one minimal first-wave route.",
    )
    replace_section_bullet(
        goal_charter,
        "Technical Direction",
        "Use canonical skill copies, generated .aw artifacts, and deterministic contract smoke checks.",
    )
    replace_section_bullet(
        goal_charter,
        "Success Criteria",
        "One repo-local command proves harness, repo judgment, init, schedule, and dispatch continuity.",
    )
    replace_section_bullet(
        goal_charter,
        "System Invariants",
        "Do not promote .aw state into docs truth and do not widen into C3 backends.",
    )

    replace_keyed_value(repo_snapshot, "status", "ready-for-c2-contract-smoke")
    replace_section_bullet(
        repo_snapshot,
        "Mainline Status",
        "first-wave agents payload contract is installed in an isolated target root and ready for contract smoke",
    )
    replace_section_bullet(
        repo_snapshot,
        "Architecture And Module Map",
        "docs truth -> .aw scaffold -> artifact instance -> canonical skill -> adapter payload -> deploy target",
    )
    replace_section_bullet(
        repo_snapshot,
        "Active Branches And Purpose",
        "feature/harness-system-workflow: complete A/B/C1 and close C2 with a repeatable contract smoke path",
    )
    replace_section_bullet(
        repo_snapshot,
        "Governance Status",
        "A/B/C1 complete; C2 is the only active delivery target; C3 remains out of scope",
    )
    replace_section_bullet(
        repo_snapshot,
        "Known Issues And Risks",
        "schedule and dispatch contract smoke must prove queue selection plus fallback/general-executor behavior without requiring downstream specialized skills",
    )


def update_control_state_for_worktrack(aw_root: Path) -> None:
    control_state = aw_root / "control-state.md"
    replace_keyed_value(control_state, "repo_scope", "RepoScope.deciding")
    replace_keyed_value(control_state, "worktrack_scope", "WorktrackScope.initializing")
    replace_section_bullet(control_state, "Current Next Action", "init-worktrack-skill")


def seed_worktrack_artifacts(aw_root: Path) -> None:
    contract = aw_root / "worktrack" / "contract.md"
    plan = aw_root / "worktrack" / "plan-task-queue.md"

    replace_keyed_value(contract, "baseline_ref", "main")
    replace_keyed_value(contract, "contract_status", "active")

    replace_section_bullet(
        contract,
        "Task Goal",
        "Lock the agents first-wave contract smoke path with one repeatable command.",
    )
    replace_section_bullet(
        contract,
        "Scope",
        "Installed skill-copy read-through, repo-to-worktrack transition, and dispatch fallback continuity only.",
    )
    replace_section_bullet(
        contract,
        "Non-Goals",
        "Do not expand into C3 backends, full lifecycle execution, or specialized downstream skill coverage.",
    )
    replace_section_bullet(
        contract,
        "Impacted Modules",
        "toolchain/scripts/test and docs/project-maintenance/usage-help",
    )
    replace_section_bullet(
        contract,
        "Planned Next State",
        "A passing first-wave contract smoke harness becomes the canonical C2 contract verification entry.",
    )
    replace_section_bullet(
        contract,
        "Acceptance Criteria",
        "Installed agents payloads are readable and the first-wave route reaches dispatch selection with bounded I/O plus explicit runtime-dispatch reporting.",
    )
    replace_section_bullet(
        contract,
        "Constraints",
        "Do not widen beyond the first-wave C2 contract path and do not treat scaffold state as docs truth.",
    )
    replace_section_bullet(
        contract,
        "Verification Requirements",
        "Run the repo-local agents first-wave contract smoke and keep runtime fallback reporting explicit.",
    )
    replace_section_bullet(
        contract,
        "Rollback Conditions",
        "Remove or shrink the contract smoke harness if it starts redefining deploy truth or C3 scope.",
    )
    replace_section_bullet(
        contract,
        "Notes",
        "This contract is seeded inside an isolated .aw root for contract smoke only.",
    )

    replace_keyed_value(plan, "current_phase", "dispatch-ready")
    replace_keyed_value(plan, "contract_ref", "worktrack/contract.md")
    replace_keyed_value(plan, "queue_status", "seeded-for-schedule-refresh")
    replace_checkbox(plan, 1, "Validate the installed first-wave skill copies and payload descriptors.")
    replace_checkbox(plan, 2, "Refresh the queue and select one bounded C2 work item.")
    replace_checkbox(plan, 3, "Return one dispatch result for the selected work item without claiming real subagent execution.")
    replace_section_bullet(
        plan,
        "Execution Order Notes",
        "The first two tasks stay inside C2 planning; the third proves dispatch for the schedule-selected item without entering implementation.",
    )
    replace_section_bullet(
        plan,
        "Dependencies",
        "Generated .aw fixture and installed agents payloads must both be present.",
    )
    replace_section_bullet(
        plan,
        "Current Blockers",
        "None inside the isolated contract smoke workspace.",
    )
    replace_keyed_value(plan, "selected_next_action_id", "TODO(selected_next_action_id)")
    replace_keyed_value(plan, "selected_next_action", "TODO(selected_next_action)")
    replace_keyed_value(plan, "selection_reason", "TODO(selection_reason)")
    replace_keyed_value(plan, "task", "TODO(task)")
    replace_keyed_value(plan, "goal_for_this_round", "TODO(goal_for_this_round)")
    replace_keyed_value(plan, "constraints_for_this_round", "TODO(constraints_for_this_round)")
    replace_keyed_value(
        plan,
        "acceptance_criteria_for_this_round",
        "TODO(acceptance_criteria_for_this_round)",
    )
    replace_keyed_value(plan, "verification_requirements", "TODO(verification_requirements)")
    replace_keyed_value(plan, "done_signal", "TODO(done_signal)")
    replace_keyed_value(plan, "required_context", "TODO(required_context)")
    replace_keyed_value(plan, "return_to_schedule_if", "TODO(return_to_schedule_if)")
    replace_keyed_value(plan, "dispatch_packet_ready", "pending")
    replace_keyed_value(plan, "recommended_next_route", "schedule-worktrack-skill")
    replace_section_bullet(
        plan,
        "Notes",
        "The plan is intentionally limited to one schedule-then-dispatch path.",
    )


def validate_protocol_fields(
    skill: InstalledSkill,
    output: dict[str, Any],
) -> None:
    missing = [
        field_name
        for field_name in MINIMUM_PROTOCOL_FIELDS[skill.skill_id]
        if field_name not in output
    ]
    if missing:
        raise SmokeError(
            f"{skill.skill_id} step output is missing required fields: {', '.join(missing)}"
        )


def run_harness_round(skill: InstalledSkill, aw_root: Path) -> dict[str, Any]:
    output = {
        "current_scope": "RepoScope",
        "current_phase": "RepoScope.supervising",
        "current_state": "RepoScope.observing",
        "actions_taken": [
            "loaded isolated control-state fixture",
            "kept the round inside RepoScope",
            "selected repo-status-skill as the next bounded observer",
        ],
        "artifacts_read": [
            str(aw_root / "control-state.md"),
            str(aw_root / "repo" / "snapshot-status.md"),
        ],
        "evidence_collected": [
            "control-state links to repo snapshot and pending worktrack artifacts",
            "installed harness skill matches its canonical package copy",
        ],
        "status_or_verdict": "repo baseline ready for a bounded next-direction round",
        "allowed_next_routes": ["repo-status-skill", "repo-whats-next-skill"],
        "recommended_next_route": "repo-status-skill",
        "continuation_ready": True,
        "continuation_blockers": [],
        "recommended_next_scope": "RepoScope",
        "recommended_next_action": "repo-status-skill",
        "continuation_decision": "continue",
        "stop_conditions_hit": [],
        "approval_required": False,
        "approval_scope": "none",
        "approval_reason": "none",
        "needs_approval": False,
        "approval_to_apply": "none",
        "how_to_review": "inspect the installed harness skill copy, payload descriptor, and seeded control-state",
    }
    validate_protocol_fields(skill, output)
    return output


def run_repo_status_round(skill: InstalledSkill, aw_root: Path) -> dict[str, Any]:
    output = {
        "current_scope": "RepoScope",
        "current_phase": "RepoScope.observing",
        "control_state": "RepoScope.observing",
        "snapshot_basis": str(aw_root / "repo" / "snapshot-status.md"),
        "goal_reference_used": str(aw_root / "goal-charter.md"),
        "mainline_status": "first-wave agents payloads are installed and ready for one bounded contract smoke path",
        "active_branches": ["feature/harness-system-workflow"],
        "governance_signals": [
            "A/B/C1 are already complete",
            "C2 remains the only active delivery target",
        ],
        "known_risks": [
            "do not mistake install/verify success for real runtime execution proof",
        ],
        "stale_or_missing_inputs": [],
        "bounded_sensor_checks": [
            "repo snapshot fixture exists",
            "goal charter fixture exists",
            "installed repo-status skill matches canonical source content",
        ],
        "observation_status": "fresh-enough-for-decision",
        "snapshot_freshness": "fresh",
        "repo_judgment_ready": True,
        "allowed_next_routes": ["repo-whats-next-skill", "repo-status-skill"],
        "recommended_next_route": "repo-whats-next-skill",
        "continuation_ready": True,
        "continuation_blockers": [],
        "handoff_signals": [
            "repo baseline is strong enough for repo-whats-next first-wave judgment",
        ],
        "approval_required": False,
        "approval_reason": "none",
        "needs_supervisor_decision": True,
    }
    validate_protocol_fields(skill, output)
    return output


def run_repo_whats_next_round(
    skill: InstalledSkill,
    repo_status_output: dict[str, Any],
) -> dict[str, Any]:
    allowed_repo_actions = skill.payload.get("supported_repo_actions")
    if allowed_repo_actions != ["enter-worktrack", "hold-and-observe"]:
        raise SmokeError(
            f"repo-whats-next supported_repo_actions drifted: {allowed_repo_actions!r}"
        )

    output = {
        "mode": "next-direction",
        "current_phase": "RepoScope.deciding",
        "mode_trigger_reason": "repo-status handed off a fresh enough observation basis",
        "facts": [
            "installed first-wave payloads are readable from the agents target root",
            "repo-status reported enough evidence for a bounded repo decision",
            "C3 backends remain explicitly out of scope",
        ],
        "inferences": [
            "the next bounded move is to enter one minimal worktrack contract smoke path",
        ],
        "unknowns": [],
        "current_primary_contradiction": (
            "install and verify are complete, but the first-wave route still lacks a repeatable contract smoke proof"
        ),
        "primary_aspect": "C2 needs a real route proof, not another operator note",
        "top_priority_now": "prove one direct first-wave route into dispatch fallback",
        "do_not_do": [
            "do not reopen A/B/C1 scope",
            "do not expand into claude or opencode",
            "do not treat .aw templates as runtime payload",
        ],
        "recommended_repo_action": "enter-worktrack",
        "allowed_next_routes": ["init-worktrack-skill", "repo-status-skill"],
        "recommended_next_route": "init-worktrack-skill",
        "recommended_next_scope": "WorktrackScope.initializing",
        "allowed_repo_actions": allowed_repo_actions,
        "in_scope": [
            "one bounded C2 contract-smoke worktrack",
        ],
        "out_of_scope": [
            "goal-change-control",
            "refresh-repo-state",
            "C3 backend expansion",
        ],
        "decision_constraints": [
            "stay inside the agents first-wave subset",
        ],
        "selection_basis": repo_status_output["handoff_signals"],
        "selection_reason": "C2 requires a repeatable worktrack path and the repo baseline is ready.",
        "minimal_missing_info": [],
        "control_state_change_requested": True,
        "continuation_ready": True,
        "continuation_blockers": [],
        "approval_required": False,
        "approval_scope": "none",
        "approval_reason": "none",
        "needs_programmer_approval": False,
        "how_to_review": "confirm the selected repo action stays inside the frozen first-wave action set",
    }
    if output["recommended_repo_action"] not in allowed_repo_actions:
        raise SmokeError("repo-whats-next selected an action outside the first-wave subset")
    validate_protocol_fields(skill, output)
    return output


def run_init_worktrack_round(skill: InstalledSkill, aw_root: Path) -> dict[str, Any]:
    seed_worktrack_artifacts(aw_root)
    output = {
        "worktrack_id": "wt-first-wave-contract-smoke",
        "worktrack_identity": "wt-first-wave-contract-smoke",
        "initialization_status": "ready-for-scheduling",
        "branch_action": "reuse-existing-bounded-branch",
        "branch_name_or_rule": "feature/agents-first-wave-contract-smoke",
        "baseline_ref": "main",
        "baseline_reason": "the contract smoke path compares first-wave behavior against the current mainline contract",
        "goal": "Lock C2 with a repeatable agents first-wave contract smoke path.",
        "in_scope": [
            "installed skill-copy read-through",
            "repo-to-worktrack transition",
            "schedule selection continuity",
            "dispatch fallback continuity",
        ],
        "out_of_scope": [
            "C3 backends",
            "full implementation lifecycle",
            "specialized downstream skill coverage",
        ],
        "impact_modules": [
            "toolchain/scripts/test",
            "docs/project-maintenance/usage-help",
        ],
        "next_state": "WorktrackScope.scheduling via schedule-worktrack-skill",
        "acceptance_criteria": [
            "one command proves the installed first-wave route is readable and bounded through schedule then dispatch",
        ],
        "constraints": [
            "stay inside the first-wave C2 contract smoke scope",
            "do not rewrite docs truth from the generated .aw fixture",
        ],
        "rollback_conditions": [
            "remove the contract smoke harness if it starts redefining deploy or payload truth",
        ],
        "initial_tasks": [
            "validate installed skill copies",
            "seed one bounded scheduling queue",
            "select one current next action",
        ],
        "initial_queue_items": [
            "validate installed skill copies",
            "refresh the queue and select one current next action",
            "package the selected bounded C2 work item and carry it into dispatch fallback",
        ],
        "queue_seed_status": "seeded-for-schedule-refresh",
        "task_order": [1, 2, 3],
        "dependencies": [
            "isolated agents install root",
            "generated .aw fixture",
        ],
        "current_blockers": [],
        "next_action": "refresh the worktrack queue and choose one current next action",
        "next_action_provenance": "schedule-worktrack-skill must author the current next action and dispatch packet",
        "verification_requirements": [
            "agents_first_wave_contract_smoke.py must pass in one bounded route",
        ],
        "required_context": [
            str(aw_root / "worktrack" / "contract.md"),
            str(aw_root / "worktrack" / "plan-task-queue.md"),
        ],
        "known_risks": [
            "mistaking readable payloads for full runtime execution",
        ],
        "schedule_handoff_mode": "seed-queue-for-scheduling",
        "schedule_handoff_packet": {
            "worktrack_contract": str(aw_root / "worktrack" / "contract.md"),
            "plan_task_queue": str(aw_root / "worktrack" / "plan-task-queue.md"),
            "initial_queue_items": [
                "validate installed skill copies",
                "refresh the queue and select one current next action",
                "package the selected bounded C2 work item and carry it into dispatch fallback",
            ],
            "constraints": [
                "stay inside the first-wave C2 contract smoke scope",
                "do not rewrite docs truth from the generated .aw fixture",
            ],
        },
        "executor_handoff_packet": {
            "handoff_type": "schedule-worktrack",
            "worktrack_contract": str(aw_root / "worktrack" / "contract.md"),
            "plan_task_queue": str(aw_root / "worktrack" / "plan-task-queue.md"),
            "verification_requirements": [
                "agents_first_wave_contract_smoke.py must pass in one bounded route",
            ],
        },
        "execution_not_started": True,
        "continuation_ready": True,
        "recommended_next_route": "schedule-worktrack-skill",
        "approval_required": False,
        "approval_scope": "none",
        "approval_reason": "none",
        "recommended_next_action": "schedule-worktrack-skill",
        "needs_approval": False,
        "approval_to_apply": "none",
    }
    validate_protocol_fields(skill, output)
    return output


def run_schedule_worktrack_round(
    skill: InstalledSkill,
    init_output: dict[str, Any],
) -> dict[str, Any]:
    selected_task = "package the selected bounded C2 work item and carry it into dispatch fallback"
    handoff_packet = {
        "task": selected_task,
        "goal": "Lock C2 with a repeatable agents first-wave contract smoke path.",
        "in_scope": [
            "installed skill-copy read-through",
            "repo-to-worktrack transition",
            "dispatch fallback continuity",
        ],
        "out_of_scope": [
            "C3 backends",
            "full implementation lifecycle",
            "specialized downstream skill coverage",
        ],
        "constraints": [
            "do not mutate docs truth from the contract smoke fixture",
            "do not widen beyond one schedule-selected dispatch path",
        ],
        "verification_requirements": init_output["verification_requirements"],
        "done_signal": "return one dispatch result that preserves bounded scope and reports the runtime dispatch mode honestly",
        "required_context": init_output["required_context"],
        "known_risks": init_output["known_risks"],
        "return_to_schedule_if": [
            "task brief and info packet drift out of sync",
            "dispatch carrier tries to widen beyond the selected work item",
        ],
    }
    output = {
        "current_worktrack_state": "queue refreshed from the seeded worktrack contract and ready for one bounded dispatch handoff",
        "queue_snapshot_after_refresh": "one selected action and one dispatch packet are ready",
        "queue_changes": [
            "kept the first validation task in the queue",
            "selected one bounded C2 work item as the current next action",
            "deferred the final dispatch proof to the next bounded execution carrier",
        ],
        "ready_tasks": [
            selected_task,
        ],
        "blocked_or_deferred_tasks": [],
        "acceptance_criteria_considered": init_output["acceptance_criteria"],
        "criteria_addressed_now": [
            "installed agents payloads remain readable and the next action is now explicitly selected",
        ],
        "criteria_remaining": [
            "dispatch fallback still needs to return one bounded result",
        ],
        "acceptance_coverage_gaps": [],
        "selected_next_action_id": "task-3-dispatch-contract-smoke",
        "selected_next_action": selected_task,
        "selection_reason": "the queue now has enough bounded context to hand one work item to dispatch without widening scope",
        "dispatch_task_brief_draft": {
            "task": selected_task,
            "done_signal": handoff_packet["done_signal"],
        },
        "dispatch_info_packet_draft": {
            "constraints": handoff_packet["constraints"],
            "required_context": handoff_packet["required_context"],
        },
        "prerequisites_remaining": [],
        "dispatch_packet_ready": True,
        "dispatch_ready": True,
        "required_context_for_next_round": handoff_packet["required_context"],
        "evidence_used": [
            init_output["executor_handoff_packet"]["worktrack_contract"],
            init_output["executor_handoff_packet"]["plan_task_queue"],
        ],
        "open_issues": [],
        "continuation_ready": True,
        "recommended_next_route": "dispatch-skills",
        "recommended_next_skill_or_route": "dispatch-skills",
        "executor_handoff_packet": handoff_packet,
    }
    validate_protocol_fields(skill, output)
    return output


def run_dispatch_round(
    skill: InstalledSkill,
    schedule_output: dict[str, Any],
) -> dict[str, Any]:
    handoff_packet = schedule_output["executor_handoff_packet"]
    output = {
        "handoff_packet_source": "schedule-worktrack-skill",
        "dispatch_packet_status": "ready",
        "dispatch_contract_gaps": [],
        "selected_executor": "general-task-completion-executor",
        "runtime_dispatch_mode": "current-carrier-fallback",
        "selection_reason": (
            "no first-wave specialized downstream skill is required and this contract smoke does not provide a real delegated subagent shell"
        ),
        "fallback_used": True,
        "task": handoff_packet["task"],
        "goal": handoff_packet["goal"],
        "in_scope": handoff_packet["in_scope"],
        "out_of_scope": handoff_packet["out_of_scope"],
        "constraints": handoff_packet["constraints"],
        "verification_requirements": handoff_packet["verification_requirements"],
        "done_signal": handoff_packet["done_signal"],
        "required_context": handoff_packet["required_context"],
        "actions_taken": [
            "packaged one dispatch task brief",
            "carried forward the bounded info packet",
            "selected fallback general executor without widening scope",
            "reported current-carrier runtime fallback instead of claiming delegated subagent execution",
        ],
        "files_touched_or_expected": handoff_packet["required_context"],
        "evidence_collected": [
            "fallback path preserved the same task and verification contract",
            "no specialized downstream skill coverage was required to keep the route live",
            "the contract smoke reports runtime-dispatch gap explicitly instead of treating selection as real subagent execution",
        ],
        "open_issues": [],
        "return_route_if_not_dispatched": handoff_packet["return_to_schedule_if"],
        "recommended_next_action": "return the dispatch result to Harness; this contract smoke does not prove real delegated execution",
    }
    if output["selected_executor"] != "general-task-completion-executor":
        raise SmokeError("dispatch did not prove the fallback/general-executor path")
    if not output["fallback_used"]:
        raise SmokeError("dispatch contract smoke must exercise the fallback path")
    validate_protocol_fields(skill, output)
    return output


def run_smoke(agents_root: Path, aw_root: Path) -> dict[str, Any]:
    smoke_args = SimpleNamespace(backend="agents", agents_root=agents_root)

    _, prune_log = capture_stdout(adapter_deploy.prune_all_managed_target_dirs, "agents", smoke_args)
    _, check_log = capture_stdout(adapter_deploy.check_backend_target_paths, "agents", smoke_args)
    _, install_log = capture_stdout(adapter_deploy.install_backend_payloads, "agents", smoke_args)
    verify_result, verify_log = capture_stdout(adapter_deploy.verify_backend, "agents", smoke_args)
    if verify_result.issues:
        raise SmokeError(
            "agents install root failed verify before contract smoke:\n"
            + json.dumps(json_ready_verify_result(verify_result), indent=2, ensure_ascii=True)
        )

    seed_aw_fixture(aw_root)
    installed_skills = discover_installed_skills(agents_root)

    harness_output = run_harness_round(installed_skills["harness-skill"], aw_root)
    repo_status_output = run_repo_status_round(installed_skills["repo-status-skill"], aw_root)
    repo_whats_next_output = run_repo_whats_next_round(
        installed_skills["repo-whats-next-skill"],
        repo_status_output,
    )
    update_control_state_for_worktrack(aw_root)
    init_output = run_init_worktrack_round(installed_skills["init-worktrack-skill"], aw_root)
    schedule_output = run_schedule_worktrack_round(
        installed_skills["schedule-worktrack-skill"],
        init_output,
    )
    dispatch_output = run_dispatch_round(installed_skills["dispatch-skills"], schedule_output)

    return {
        "passed": True,
        "repo_root": str(REPO_ROOT),
        "agents_root": str(agents_root),
        "aw_root": str(aw_root),
        "install_cycle": {
            "prune": prune_log.strip().splitlines(),
            "check_paths_exist": check_log.strip().splitlines(),
            "install": install_log.strip().splitlines(),
            "verify_log": verify_log.strip().splitlines(),
            "verify_result": json_ready_verify_result(verify_result),
        },
        "installed_skills": {
            skill_id: {
                "target_dir": str(skill.target_dir),
                "canonical_skill_path": str(skill.canonical_skill_path),
                "output_fields": list(skill.output_fields),
            }
            for skill_id, skill in installed_skills.items()
        },
        "route": [
            {
                "skill_id": "harness-skill",
                "recommended_next_route": harness_output["recommended_next_route"],
                "recommended_next_action": harness_output["recommended_next_action"],
                "recommended_next_scope": harness_output["recommended_next_scope"],
                "continuation_decision": harness_output["continuation_decision"],
                "stop_conditions_hit": harness_output["stop_conditions_hit"],
            },
            {
                "skill_id": "repo-status-skill",
                "recommended_next_route": repo_status_output["recommended_next_route"],
                "handoff_signals": repo_status_output["handoff_signals"],
            },
            {
                "skill_id": "repo-whats-next-skill",
                "recommended_repo_action": repo_whats_next_output["recommended_repo_action"],
                "recommended_next_route": repo_whats_next_output["recommended_next_route"],
                "recommended_next_scope": repo_whats_next_output["recommended_next_scope"],
                "continuation_ready": repo_whats_next_output["continuation_ready"],
            },
            {
                "skill_id": "init-worktrack-skill",
                "next_action": init_output["next_action"],
                "recommended_next_route": init_output["recommended_next_route"],
                "execution_not_started": init_output["execution_not_started"],
                "continuation_ready": init_output["continuation_ready"],
            },
            {
                "skill_id": "schedule-worktrack-skill",
                "selected_next_action_id": schedule_output["selected_next_action_id"],
                "selected_next_action": schedule_output["selected_next_action"],
                "dispatch_packet_ready": schedule_output["dispatch_packet_ready"],
                "recommended_next_route": schedule_output["recommended_next_route"],
                "dispatch_ready": schedule_output["dispatch_ready"],
                "recommended_next_skill_or_route": schedule_output["recommended_next_skill_or_route"],
            },
            {
                "skill_id": "dispatch-skills",
                "dispatch_packet_status": dispatch_output["dispatch_packet_status"],
                "selected_executor": dispatch_output["selected_executor"],
                "runtime_dispatch_mode": dispatch_output["runtime_dispatch_mode"],
                "fallback_used": dispatch_output["fallback_used"],
            },
        ],
        "step_outputs": {
            "harness-skill": harness_output,
            "repo-status-skill": repo_status_output,
            "repo-whats-next-skill": repo_whats_next_output,
            "init-worktrack-skill": init_output,
            "schedule-worktrack-skill": schedule_output,
            "dispatch-skills": dispatch_output,
        },
    }


def print_human_report(report: dict[str, Any]) -> None:
    print("agents first-wave contract smoke: PASS")
    print(f"- agents_root: {report['agents_root']}")
    print(f"- aw_root: {report['aw_root']}")
    print("- route:")
    for step in report["route"]:
        skill_id = step["skill_id"]
        details = ", ".join(f"{key}={value}" for key, value in step.items() if key != "skill_id")
        print(f"  - {skill_id}: {details}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    workspace_root: Path | None = None

    try:
        if args.agents_root is None or args.aw_root is None:
            workspace_root = Path(tempfile.mkdtemp(prefix="agents-first-wave-contract-smoke-"))
        agents_root = args.agents_root or (workspace_root / ".agents" / "skills")
        aw_root = args.aw_root or (workspace_root / ".aw")

        report = run_smoke(agents_root.resolve(), aw_root.resolve())
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=True))
        else:
            print_human_report(report)
            if workspace_root is not None and args.keep_temp:
                print(f"- kept_workspace: {workspace_root}")
        return 0
    except SmokeError as exc:
        error_payload = {"passed": False, "error": str(exc)}
        if args.json:
            print(json.dumps(error_payload, indent=2, ensure_ascii=True))
        else:
            print(f"agents first-wave contract smoke: FAIL\n- error: {exc}", file=sys.stderr)
        return 1
    finally:
        if workspace_root is not None and not args.keep_temp:
            shutil.rmtree(workspace_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
