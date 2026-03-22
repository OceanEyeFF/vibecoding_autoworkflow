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
DEFAULT_RUBRIC = EVAL_ROOT / "scoring" / "context-routing-rubric.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize(value: str) -> str:
    return value.strip().lower()


def normalize_list(values: list[str]) -> list[str]:
    return [normalize(item) for item in values]


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


def score_run(manifest_path: Path, rubric_path: Path, write_back: bool) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    parsed_path = REPO_ROOT / manifest["parsed_path"]
    if not parsed_path.exists():
        raise SystemExit(f"Parsed output not found: {parsed_path}")

    response = load_json(parsed_path)
    rubric = load_json(rubric_path)

    if manifest["skill"] != rubric["applies_to_skill"]:
        raise SystemExit(
            f"Rubric applies to {rubric['applies_to_skill']}, but run skill is {manifest['skill']}."
        )
    if manifest["scenario_id"] not in rubric["scenarios"]:
        raise SystemExit(f"No rubric rules for scenario {manifest['scenario_id']}.")

    score = score_context_routing_run(manifest, response, rubric)
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
        default=DEFAULT_RUBRIC,
        help="Scoring rubric JSON file.",
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
