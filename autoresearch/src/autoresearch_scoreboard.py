#!/usr/bin/env python3
"""Scoreboard aggregation for autoresearch P0.1 baseline lanes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import AUTORESEARCH_SCHEMAS_ROOT


AUTORESEARCH_SCOREBOARD_SCHEMA_PATH = AUTORESEARCH_SCHEMAS_ROOT / "autoresearch-scoreboard.schema.json"


def load_run_summary(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"run-summary must be an object: {path}")
    return payload


def merge_run_summaries(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    if not summaries:
        return {"suite_file": "", "results": []}
    merged_results: list[dict[str, Any]] = []
    suite_parts: list[str] = []
    for summary in summaries:
        suite = summary.get("suite_file")
        if isinstance(suite, str) and suite:
            suite_parts.append(suite)
        results = summary.get("results") or []
        if isinstance(results, list):
            merged_results.extend(item for item in results if isinstance(item, dict))
    return {
        "suite_file": ",".join(suite_parts),
        "results": merged_results,
    }


def _is_eval_success(result: dict[str, Any]) -> bool:
    return (
        result.get("timed_out") is False
        and result.get("returncode") == 0
        and not result.get("parse_error")
        and isinstance(result.get("structured_output"), dict)
    )


def build_lane_scoreboard(lane_name: str, summary: dict[str, Any]) -> dict[str, Any]:
    results = summary.get("results") or []
    eval_results = [item for item in results if isinstance(item, dict) and item.get("phase") == "eval"]
    tasks_total = len(eval_results)
    unique_repos = {str(item.get("repo_path") or "") for item in eval_results if item.get("repo_path")}
    pass_count = sum(1 for item in eval_results if _is_eval_success(item))
    timeout_count = sum(1 for item in eval_results if item.get("timed_out") is True)
    parse_error_count = sum(1 for item in eval_results if item.get("parse_error"))

    scores: list[float] = []
    for item in eval_results:
        structured = item.get("structured_output")
        if not isinstance(structured, dict):
            continue
        total_score = structured.get("total_score")
        if isinstance(total_score, (int, float)):
            scores.append(float(total_score))

    sample = eval_results[0] if eval_results else {}
    denominator = float(tasks_total) if tasks_total else 1.0
    return {
        "lane_name": lane_name,
        "suite_file": str(summary.get("suite_file") or ""),
        "backend": str(sample.get("backend") or ""),
        "judge_backend": str(sample.get("judge_backend") or ""),
        "repos_total": len(unique_repos),
        "tasks_total": tasks_total,
        "pass_rate": pass_count / denominator if tasks_total else 0.0,
        "timeout_rate": timeout_count / denominator if tasks_total else 0.0,
        "parse_error_rate": parse_error_count / denominator if tasks_total else 0.0,
        "avg_total_score": (sum(scores) / len(scores)) if scores else 0.0,
    }


def build_repo_task_rows(lane_name: str, summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in summary.get("results") or []:
        if not isinstance(item, dict) or item.get("phase") != "eval":
            continue
        structured = item.get("structured_output")
        if not isinstance(structured, dict):
            continue
        repo_path = Path(str(item.get("repo_path") or ""))
        total_score = structured.get("total_score")
        if not isinstance(total_score, (int, float)):
            continue
        rows.append(
            {
                "lane_name": lane_name,
                "repo": repo_path.name or str(repo_path),
                "task": str(item.get("task") or ""),
                "phase": "eval",
                "total_score": float(total_score),
                "overall": str(structured.get("overall") or ""),
                "dimension_feedback": structured.get("dimension_feedback") or {},
            }
        )
    return rows


def build_scoreboard(
    *,
    run_id: str,
    baseline_sha: str,
    lane_summaries: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    lane_order = ["train", "validation"]
    lanes: list[dict[str, Any]] = []
    repo_tasks: list[dict[str, Any]] = []
    for lane_name in lane_order:
        summary = lane_summaries.get(lane_name, {"suite_file": "", "results": []})
        lanes.append(build_lane_scoreboard(lane_name, summary))
        repo_tasks.extend(build_repo_task_rows(lane_name, summary))

    return {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline_sha": baseline_sha,
        "rounds_completed": 0,
        "best_round": 0,
        "lanes": lanes,
        "repo_tasks": repo_tasks,
    }


def validate_scoreboard_payload(payload: dict[str, Any]) -> None:
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError("jsonschema is required to validate autoresearch scoreboard.") from exc

    schema = json.loads(AUTORESEARCH_SCOREBOARD_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=payload, schema=schema)


def write_scoreboard(path: Path, scoreboard: dict[str, Any]) -> None:
    validate_scoreboard_payload(scoreboard)
    path.write_text(json.dumps(scoreboard, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
