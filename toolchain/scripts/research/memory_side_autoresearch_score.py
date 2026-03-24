#!/usr/bin/env python3
"""Score Memory Side Auto Research benchmark outputs."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
EVAL_ROOT = REPO_ROOT / "toolchain" / "evals" / "memory-side"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / ".autoworkflow" / "memory-side-autoresearch"
DEFAULT_RUBRICS = {
    "context-routing-skill": EVAL_ROOT / "scoring" / "context-routing-rubric.json",
    "knowledge-base-skill": EVAL_ROOT / "scoring" / "knowledge-base-rubric.json",
    "writeback-cleanup-skill": EVAL_ROOT / "scoring" / "writeback-cleanup-rubric.json",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize(value: str) -> str:
    return value.strip().lower()


def normalize_list(values: list[str]) -> list[str]:
    return [normalize(item) for item in values]


def coerce_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def coerce_str_list(value: Any) -> list[str]:
    return [str(item) for item in coerce_list(value) if str(item).strip()]


def text_value(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def has_any_pattern(text: str, patterns: list[str]) -> bool:
    lowered = normalize(text)
    return any(normalize(pattern) in lowered for pattern in patterns)


def list_has_pattern(values: list[str], patterns: list[str]) -> bool:
    return any(has_any_pattern(item, patterns) for item in values)


def has_exact_value(values: list[str], expected_values: list[str]) -> bool:
    normalized_values = {normalize(item) for item in values}
    normalized_expected = {normalize(item) for item in expected_values}
    return not normalized_values.isdisjoint(normalized_expected)


def list_contains_required_item(values: list[str], required: str) -> bool:
    required_norm = normalize(required)
    return any(required_norm == normalize(item) for item in values)


def count_required_matches(values: list[str], required_items: list[str]) -> tuple[int, list[str]]:
    missing = [item for item in required_items if not list_contains_required_item(values, item)]
    return len(required_items) - len(missing), missing


@dataclass
class CheckResult:
    name: str
    points_awarded: int
    points_possible: int
    passed: bool
    notes: str


def add_check(
    checks: list[CheckResult],
    name: str,
    points_awarded: int,
    points_possible: int,
    passed: bool,
    notes: str,
) -> None:
    checks.append(
        CheckResult(
            name=name,
            points_awarded=points_awarded,
            points_possible=points_possible,
            passed=passed,
            notes=notes,
        )
    )


def has_non_negated_marker(text: str, markers: list[str], negation_markers: list[str]) -> bool:
    lowered = normalize(text)
    if any(marker in lowered for marker in normalize_list(negation_markers)):
        return False
    return any(marker in lowered for marker in normalize_list(markers))


def list_has_non_negated_marker(
    values: list[str],
    markers: list[str],
    negation_markers: list[str],
) -> bool:
    return any(has_non_negated_marker(item, markers, negation_markers) for item in values)


def get_classifications(response: dict[str, Any]) -> list[dict[str, Any]]:
    raw_value = response.get("layer_classification", [])
    if not isinstance(raw_value, list):
        return []
    return [item for item in raw_value if isinstance(item, dict)]


def classification_entry_is_complete(entry: dict[str, Any]) -> bool:
    return all(
        text_value(entry.get(key))
        for key in ("path", "layer", "reason")
    )


def find_classification_for_path(
    classifications: list[dict[str, Any]],
    path: str,
) -> dict[str, Any] | None:
    for entry in classifications:
        if normalize(text_value(entry.get("path"))) == normalize(path):
            return entry
    return None


def find_classification_for_patterns(
    classifications: list[dict[str, Any]],
    path_patterns: list[str],
) -> dict[str, Any] | None:
    for entry in classifications:
        path = text_value(entry.get("path"))
        if path and has_any_pattern(path, path_patterns):
            return entry
    return None


def list_has_any_pattern(values: list[str], patterns: list[str]) -> bool:
    return any(has_any_pattern(value, patterns) for value in values)


def find_latest_manifest(output_root: Path, backend: str | None, scenario: str | None) -> Path:
    candidates = []
    for manifest_path in output_root.glob("*/manifest.json"):
        try:
            manifest = load_json(manifest_path)
        except Exception:
            continue
        if backend and manifest.get("backend") != backend:
            continue
        if scenario and manifest.get("scenario_id") != scenario:
            continue
        candidates.append(manifest_path)
    if not candidates:
        raise SystemExit("No matching manifest.json found under the output root.")
    return sorted(candidates)[-1]


def score_context_routing_run(
    manifest: dict[str, Any],
    response: dict[str, Any],
    rubric: dict[str, Any],
) -> dict[str, Any]:
    scenario_id = manifest["scenario_id"]
    scenario_rules = rubric["scenarios"][scenario_id]
    global_rules = rubric["global"]

    checks: list[CheckResult] = []

    status = manifest.get("status")
    status_pass = status == "completed"
    add_check(
        checks,
        name="run_status",
        points_awarded=10 if status_pass else 0,
        points_possible=10,
        passed=status_pass,
        notes=f"manifest status={status}",
    )

    task_type = str(response.get("task_type", ""))
    task_type_norm = normalize(task_type)
    allowed_task_type = any(token in task_type_norm for token in normalize_list(scenario_rules["task_type_contains_any"]))
    disallowed_tokens = normalize_list(scenario_rules.get("task_type_must_not_contain_any", []))
    blocked_task_type = any(token in task_type_norm for token in disallowed_tokens)
    task_type_pass = allowed_task_type and not blocked_task_type
    task_notes = f"task_type={task_type}"
    if blocked_task_type:
        task_notes += "; contains forbidden scenario markers"
    add_check(
        checks,
        name="task_type_alignment",
        points_awarded=10 if task_type_pass else 0,
        points_possible=10,
        passed=task_type_pass,
        notes=task_notes,
    )

    read_first = response.get("read_first", [])
    matched_read_first, missing_read_first = count_required_matches(
        read_first, scenario_rules["read_first_must_include"]
    )
    read_first_points = int(25 * matched_read_first / len(scenario_rules["read_first_must_include"]))
    add_check(
        checks,
        name="read_first_coverage",
        points_awarded=read_first_points,
        points_possible=25,
        passed=matched_read_first == len(scenario_rules["read_first_must_include"]),
        notes=(
            "missing required read_first entries: " + ", ".join(missing_read_first)
            if missing_read_first
            else "all required read_first entries present"
        ),
    )

    read_next = response.get("read_next", [])
    read_next_ok = list_has_pattern(read_next, scenario_rules["read_next_should_include_any"])
    add_check(
        checks,
        name="read_next_support",
        points_awarded=10 if read_next_ok else 0,
        points_possible=10,
        passed=read_next_ok,
        notes="read_next contains a scenario-appropriate supporting entry"
        if read_next_ok
        else "read_next misses expected supporting entries",
    )

    main_read_values = read_first + read_next + response.get("code_entry", [])
    has_forbidden_main_read = list_has_pattern(
        main_read_values, global_rules["forbidden_main_read_patterns"]
    )
    has_whole_repo_scan = has_exact_value(
        main_read_values, global_rules.get("whole_repo_scan_values_exact", [])
    ) or list_has_pattern(main_read_values, global_rules["whole_repo_scan_patterns"])
    boundary_points = 20
    if has_forbidden_main_read:
        boundary_points -= 10
    if has_whole_repo_scan:
        boundary_points -= 10
    add_check(
        checks,
        name="main_read_hygiene",
        points_awarded=max(boundary_points, 0),
        points_possible=20,
        passed=not has_forbidden_main_read and not has_whole_repo_scan,
        notes=(
            f"forbidden_main_read={has_forbidden_main_read}; whole_repo_scan={has_whole_repo_scan}"
        ),
    )

    code_entry = response.get("code_entry", [])
    code_entry_expected = list_has_pattern(code_entry, scenario_rules["code_entry_should_include_any"])
    code_entry_forbidden = list_has_pattern(code_entry, scenario_rules["code_entry_forbidden_patterns"])
    code_entry_points = 15
    if not code_entry_expected:
        code_entry_points -= 10
    if code_entry_forbidden:
        code_entry_points -= 5
    add_check(
        checks,
        name="code_entry_precision",
        points_awarded=max(code_entry_points, 0),
        points_possible=15,
        passed=code_entry_expected and not code_entry_forbidden,
        notes=(
            f"expected_match={code_entry_expected}; forbidden_match={code_entry_forbidden}"
        ),
    )

    do_not_read = response.get("do_not_read_yet", [])
    expected_patterns = scenario_rules["do_not_read_should_include_patterns"]
    matched_do_not_read = sum(
        1 for pattern in expected_patterns if list_has_pattern(do_not_read, [pattern])
    )
    do_not_read_points = int(10 * matched_do_not_read / len(expected_patterns))
    add_check(
        checks,
        name="do_not_read_boundaries",
        points_awarded=do_not_read_points,
        points_possible=10,
        passed=matched_do_not_read == len(expected_patterns),
        notes=f"matched {matched_do_not_read}/{len(expected_patterns)} expected boundary patterns",
    )

    stop_reading_when = response.get("stop_reading_when", [])
    scope_hint = response.get("scope_hint", [])
    stop_has_content = len(stop_reading_when) > 0
    plan_markers_present = list_has_non_negated_marker(
        stop_reading_when + scope_hint,
        global_rules["execution_plan_markers"],
        global_rules.get("negation_markers", []),
    )
    stop_points = 10 if stop_has_content and not plan_markers_present else 0
    add_check(
        checks,
        name="stop_condition_quality",
        points_awarded=stop_points,
        points_possible=10,
        passed=stop_has_content and not plan_markers_present,
        notes=f"stop_has_content={stop_has_content}; plan_markers_present={plan_markers_present}",
    )

    total_awarded = sum(item.points_awarded for item in checks)
    total_possible = sum(item.points_possible for item in checks)

    hard_failures = [
        item.name
        for item in checks
        if item.name in {"run_status", "read_first_coverage", "main_read_hygiene"}
        and not item.passed
    ]
    result = "pass" if total_awarded >= 75 and not hard_failures else "fail"

    return {
        "backend": manifest["backend"],
        "scenario_id": scenario_id,
        "skill": manifest["skill"],
        "status": manifest["status"],
        "result": result,
        "score_awarded": total_awarded,
        "score_possible": total_possible,
        "hard_failures": hard_failures,
        "checks": [item.__dict__ for item in checks],
    }


def score_knowledge_base_run(
    manifest: dict[str, Any],
    response: dict[str, Any],
    rubric: dict[str, Any],
) -> dict[str, Any]:
    scenario_id = manifest["scenario_id"]
    scenario_rules = rubric["scenarios"][scenario_id]
    global_rules = rubric["global"]

    checks: list[CheckResult] = []

    status = manifest.get("status")
    status_pass = status == "completed"
    add_check(
        checks,
        name="run_status",
        points_awarded=10 if status_pass else 0,
        points_possible=10,
        passed=status_pass,
        notes=f"manifest status={status}",
    )

    mode = text_value(response.get("mode"))
    required_mode = scenario_rules["required_mode"]
    mode_pass = normalize(mode) == normalize(required_mode)
    add_check(
        checks,
        name="mode_alignment",
        points_awarded=20 if mode_pass else 0,
        points_possible=20,
        passed=mode_pass,
        notes=f"mode={mode}; required_mode={required_mode}",
    )

    classifications = get_classifications(response)
    complete_classifications = [entry for entry in classifications if classification_entry_is_complete(entry)]
    unique_paths = {normalize(text_value(entry.get("path"))) for entry in complete_classifications if text_value(entry.get("path"))}
    shape_pass = bool(complete_classifications) and len(unique_paths) == len(complete_classifications)
    add_check(
        checks,
        name="layer_classification_shape",
        points_awarded=15 if shape_pass else 0,
        points_possible=15,
        passed=shape_pass,
        notes=(
            f"classification_count={len(complete_classifications)}; unique_paths={len(unique_paths)}"
        ),
    )

    required_classifications = scenario_rules["required_classifications"]
    matched_required = 0
    missing_required: list[str] = []
    bad_layer_entries: list[str] = []
    for requirement in required_classifications:
        expected_label = requirement.get("label") or requirement.get("path") or " / ".join(
            requirement.get("path_patterns", [])
        )
        allowed_layers = requirement["layers"]
        if "path_patterns" in requirement:
            entry = find_classification_for_patterns(classifications, requirement["path_patterns"])
        else:
            entry = find_classification_for_path(classifications, requirement["path"])
        if entry is None:
            missing_required.append(expected_label)
            continue
        entry_layer = text_value(entry.get("layer"))
        if normalize(entry_layer) not in {normalize(item) for item in allowed_layers}:
            bad_layer_entries.append(f"{expected_label}=>{entry_layer}")
            continue
        matched_required += 1

    required_points = int(25 * matched_required / len(required_classifications))
    core_truth_pass = matched_required == len(required_classifications) and not bad_layer_entries
    add_check(
        checks,
        name="core_truth_mapping",
        points_awarded=required_points,
        points_possible=25,
        passed=core_truth_pass,
        notes=(
            "missing required classifications: " + ", ".join(missing_required)
            if missing_required
            else (
                "unexpected layers: " + ", ".join(bad_layer_entries)
                if bad_layer_entries
                else "all required knowledge base docs classified as core truth"
            )
        ),
    )

    missing_or_broken_entrypoints = coerce_str_list(response.get("missing_or_broken_entrypoints", []))
    entrypoint_marker_pool = scenario_rules["entrypoint_markers"] + global_rules["entrypoint_path_markers"]
    entrypoint_signal = bool(missing_or_broken_entrypoints) and list_has_any_pattern(
        missing_or_broken_entrypoints,
        entrypoint_marker_pool,
    )
    add_check(
        checks,
        name="entrypoint_repair_signal",
        points_awarded=15 if entrypoint_signal else 0,
        points_possible=15,
        passed=entrypoint_signal,
        notes=(
            "missing_or_broken_entrypoints has relevant mainline signal"
            if entrypoint_signal
            else "missing_or_broken_entrypoints lacks mainline repair signal"
        ),
    )

    smallest_safe_updates = coerce_str_list(response.get("smallest_safe_updates", []))
    has_update_signal = bool(smallest_safe_updates) and list_has_any_pattern(
        smallest_safe_updates,
        scenario_rules["small_update_markers"],
    )
    has_forbidden_update = list_has_any_pattern(
        smallest_safe_updates,
        scenario_rules["forbidden_update_markers"],
    )
    update_pass = has_update_signal and not has_forbidden_update
    add_check(
        checks,
        name="smallest_update_quality",
        points_awarded=10 if update_pass else 0,
        points_possible=10,
        passed=update_pass,
        notes=(
            f"update_signal={has_update_signal}; forbidden_update={has_forbidden_update}"
        ),
    )

    notes_for_benchmark = coerce_str_list(response.get("notes_for_benchmark", []))
    notes_pass = bool(notes_for_benchmark) and list_has_any_pattern(
        notes_for_benchmark,
        scenario_rules["note_markers"],
    )
    add_check(
        checks,
        name="notes_quality",
        points_awarded=5 if notes_pass else 0,
        points_possible=5,
        passed=notes_pass,
        notes=(
            "notes_for_benchmark contains benchmark/caveat guidance"
            if notes_pass
            else "notes_for_benchmark is missing or too generic"
        ),
    )

    total_awarded = sum(item.points_awarded for item in checks)
    total_possible = sum(item.points_possible for item in checks)

    hard_failures = [
        item.name
        for item in checks
        if item.name in {"run_status", "mode_alignment", "core_truth_mapping"}
        and not item.passed
    ]
    result = "pass" if total_awarded >= 75 and not hard_failures else "fail"

    return {
        "backend": manifest["backend"],
        "scenario_id": scenario_id,
        "skill": manifest["skill"],
        "status": manifest["status"],
        "result": result,
        "score_awarded": total_awarded,
        "score_possible": total_possible,
        "hard_failures": hard_failures,
        "checks": [item.__dict__ for item in checks],
    }


def score_writeback_cleanup_run(
    manifest: dict[str, Any],
    response: dict[str, Any],
    rubric: dict[str, Any],
) -> dict[str, Any]:
    scenario_id = manifest["scenario_id"]
    scenario_rules = rubric["scenarios"][scenario_id]
    global_rules = rubric["global"]

    checks: list[CheckResult] = []

    status = manifest.get("status")
    status_pass = status == "completed"
    add_check(
        checks,
        name="run_status",
        points_awarded=10 if status_pass else 0,
        points_possible=10,
        passed=status_pass,
        notes=f"manifest status={status}",
    )

    task = text_value(response.get("task"))
    task_pass = bool(task)
    add_check(
        checks,
        name="task_presence",
        points_awarded=10 if task_pass else 0,
        points_possible=10,
        passed=task_pass,
        notes=f"task={task}" if task_pass else "task is missing or empty",
    )

    verified_changes = coerce_str_list(response.get("verified_changes", []))
    non_changes = coerce_str_list(response.get("non_changes", []))
    write_to_core_truth = coerce_str_list(response.get("write_to_core_truth", []))
    write_to_operational_truth = coerce_str_list(response.get("write_to_operational_truth", []))
    write_to_exploratory_records = coerce_str_list(response.get("write_to_exploratory_records", []))
    do_not_write_back = coerce_str_list(response.get("do_not_write_back", []))
    cleanup_targets = coerce_str_list(response.get("cleanup_targets", []))
    risks_left = coerce_str_list(response.get("risks_left", []))
    verification_basis = coerce_str_list(response.get("verification_basis", []))
    writeback_targets = write_to_core_truth + write_to_operational_truth

    required_values = [
        verified_changes,
        non_changes,
        do_not_write_back,
        cleanup_targets,
        risks_left,
        verification_basis,
    ]
    required_present = sum(1 for value in required_values if value)
    requires_mainline_writeback = scenario_rules.get("requires_mainline_writeback", True)
    writeback_presence_ok = bool(writeback_targets) if requires_mainline_writeback else True
    exploratory_signal = bool(write_to_exploratory_records)
    required_pass = required_present == len(required_values) and writeback_presence_ok
    add_check(
        checks,
        name="required_field_coverage",
        points_awarded=int(20 * required_present / len(required_values)),
        points_possible=20,
        passed=required_pass,
        notes=(
            f"required_nonempty={required_present}/{len(required_values)}; "
            f"mainline_writeback={bool(writeback_targets)}; exploratory_writeback={exploratory_signal}; "
            f"requires_mainline_writeback={requires_mainline_writeback}"
        ),
    )

    verification_markers = scenario_rules["verification_markers"] + global_rules["verification_markers"]
    verified_changes_signal = list_has_any_pattern(verified_changes, scenario_rules["verified_change_markers"])
    basis_signal = list_has_any_pattern(verification_basis, verification_markers)
    basis_mentions_changes = list_has_any_pattern(verification_basis, scenario_rules["verified_change_markers"])
    verification_pass = verified_changes_signal and basis_signal and basis_mentions_changes
    add_check(
        checks,
        name="verification_alignment",
        points_awarded=20 if verification_pass else 0,
        points_possible=20,
        passed=verification_pass,
        notes=(
            f"verified_changes_signal={verified_changes_signal}; basis_signal={basis_signal}; basis_mentions_changes={basis_mentions_changes}"
        ),
    )

    uncertainty_markers = scenario_rules["uncertainty_markers"] + global_rules["uncertainty_markers"]
    do_not_signal = bool(do_not_write_back) and list_has_any_pattern(
        do_not_write_back,
        uncertainty_markers,
    )
    writeback_text = writeback_targets + verified_changes
    writeback_leak = list_has_any_pattern(writeback_text, uncertainty_markers)
    safety_pass = do_not_signal and not writeback_leak
    add_check(
        checks,
        name="writeback_safety",
        points_awarded=20 if safety_pass else 0,
        points_possible=20,
        passed=safety_pass,
        notes=(
            f"do_not_signal={do_not_signal}; writeback_leak={writeback_leak}"
        ),
    )

    cleanup_signal = bool(cleanup_targets) and list_has_any_pattern(
        cleanup_targets,
        scenario_rules["cleanup_markers"],
    )
    add_check(
        checks,
        name="cleanup_quality",
        points_awarded=10 if cleanup_signal else 0,
        points_possible=10,
        passed=cleanup_signal,
        notes=(
            "cleanup_targets contains stale/old/entrypoint/prompt/risk markers"
            if cleanup_signal
            else "cleanup_targets is missing or too generic"
        ),
    )

    risk_signal = bool(risks_left) and list_has_any_pattern(
        risks_left,
        scenario_rules["risk_markers"],
    )
    add_check(
        checks,
        name="risk_reporting",
        points_awarded=10 if risk_signal else 0,
        points_possible=10,
        passed=risk_signal,
        notes=(
            "risks_left contains explicit risk/caveat markers"
            if risk_signal
            else "risks_left is missing or too generic"
        ),
    )

    followup_targets = (
        coerce_str_list(response.get("docs_to_sync", []))
        + coerce_str_list(response.get("followups", []))
        + coerce_str_list(response.get("notes_for_next_round", []))
    )
    followup_signal = bool(followup_targets) and list_has_any_pattern(
        followup_targets,
        scenario_rules["followup_markers"],
    )
    add_check(
        checks,
        name="followup_quality",
        points_awarded=10 if followup_signal else 0,
        points_possible=10,
        passed=followup_signal,
        notes=(
            "follow-up fields contain docs sync / next-round markers"
            if followup_signal
            else "follow-up fields are missing or too generic"
        ),
    )

    scenario_signal = list_has_any_pattern(
        verified_changes + writeback_targets + do_not_write_back + risks_left + cleanup_targets,
        scenario_rules["scenario_markers"],
    )
    add_check(
        checks,
        name="scenario_signal",
        points_awarded=10 if scenario_signal else 0,
        points_possible=10,
        passed=scenario_signal,
        notes=(
            "writeback output reflects the scenario's expected task family"
            if scenario_signal
            else "writeback output does not reflect the scenario's expected task family"
        ),
    )

    total_awarded = sum(item.points_awarded for item in checks)
    total_possible = sum(item.points_possible for item in checks)

    hard_failures = [
        item.name
        for item in checks
        if item.name in {"run_status", "required_field_coverage", "verification_alignment", "writeback_safety"}
        and not item.passed
    ]
    result = "pass" if total_awarded >= 75 and not hard_failures else "fail"

    return {
        "backend": manifest["backend"],
        "scenario_id": scenario_id,
        "skill": manifest["skill"],
        "status": manifest["status"],
        "result": result,
        "score_awarded": total_awarded,
        "score_possible": total_possible,
        "hard_failures": hard_failures,
        "checks": [item.__dict__ for item in checks],
    }


def resolve_rubric_path(manifest: dict[str, Any], rubric_path: Path | None) -> Path:
    if rubric_path is not None:
        return rubric_path

    skill = manifest.get("skill")
    default_rubric = DEFAULT_RUBRICS.get(skill)
    if default_rubric is None:
        raise SystemExit(f"No default rubric registered for skill {skill}.")
    return default_rubric


def score_run(manifest_path: Path, rubric_path: Path | None, write_back: bool) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    parsed_path = REPO_ROOT / manifest["parsed_path"]
    if not parsed_path.exists():
        raise SystemExit(f"Parsed output not found: {parsed_path}")

    response = load_json(parsed_path)
    rubric_path = resolve_rubric_path(manifest, rubric_path)
    rubric = load_json(rubric_path)

    if manifest["skill"] != rubric["applies_to_skill"]:
        raise SystemExit(
            f"Rubric applies to {rubric['applies_to_skill']}, but run skill is {manifest['skill']}."
        )
    if manifest["scenario_id"] not in rubric["scenarios"]:
        raise SystemExit(f"No rubric rules for scenario {manifest['scenario_id']}.")

    if manifest["skill"] == "context-routing-skill":
        score = score_context_routing_run(manifest, response, rubric)
    elif manifest["skill"] == "knowledge-base-skill":
        score = score_knowledge_base_run(manifest, response, rubric)
    elif manifest["skill"] == "writeback-cleanup-skill":
        score = score_writeback_cleanup_run(manifest, response, rubric)
    else:
        raise SystemExit(f"Unsupported skill: {manifest['skill']}")
    if write_back:
        score_path = manifest_path.parent / "score.json"
        dump_json(score_path, score)
    return score


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score Memory Side benchmark outputs.")
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Path to a run manifest.json to score.",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Score the latest matching manifest under the output root.",
    )
    parser.add_argument(
        "--backend",
        help="Filter for --latest.",
    )
    parser.add_argument(
        "--scenario",
        help="Filter for --latest.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Benchmark output root containing run directories.",
    )
    parser.add_argument(
        "--rubric",
        type=Path,
        default=None,
        help="Optional scoring rubric JSON file override.",
    )
    parser.add_argument(
        "--write-score",
        action="store_true",
        help="Write score.json next to the manifest.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if bool(args.manifest) == bool(args.latest):
        raise SystemExit("Use exactly one of --manifest or --latest.")

    manifest_path = args.manifest
    if args.latest:
        manifest_path = find_latest_manifest(args.output_root, args.backend, args.scenario)

    if manifest_path is None:
        raise SystemExit("Could not resolve a manifest to score.")

    score = score_run(manifest_path, args.rubric, write_back=args.write_score)
    print(json.dumps(score, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
