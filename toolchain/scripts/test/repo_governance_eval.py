#!/usr/bin/env python3
"""Evaluate repository maintainability and governance with a fixed rubric."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DIMENSIONS = (
    ("baseline_hygiene", "A. Baseline Hygiene"),
    ("change_governance", "B. Change Governance"),
    ("automation", "C. Automation"),
    ("structural_clarity", "D. Structural Clarity"),
    ("operational_maintainability", "E. Operational Maintainability"),
)
READINESS_KEYS = ("task_split", "local_context", "auto_validation", "safe_change")
RATING_BANDS = (
    (22, "工业级（可长期稳定维护）"),
    (16, "可用（存在治理风险）"),
    (10, "技术债明显"),
    (0, "不可维护"),
)


def fail_input(context: str, label: str, message: str) -> None:
    raise SystemExit(f"invalid {context} '{label}': {message}")


def require_int_in_range(
    value: object,
    *,
    context: str,
    label: str,
    minimum: int,
    maximum: int,
) -> int:
    if value is None:
        fail_input(context, label, f"null is not allowed, expected integer in range {minimum}-{maximum}")
    if isinstance(value, bool) or not isinstance(value, int):
        fail_input(context, label, f"expected number in range {minimum}-{maximum}, got {value!r}")
    if value < minimum or value > maximum:
        fail_input(context, label, f"expected number in range {minimum}-{maximum}, got {value!r}")
    return value


def normalize_score_map(scores: dict[str, object], *, require_all: bool = False) -> dict[str, int]:
    normalized: dict[str, int] = {}
    for key, _label in DIMENSIONS:
        if key not in scores:
            continue
        normalized[key] = require_int_in_range(
            scores[key],
            context="score",
            label=key,
            minimum=0,
            maximum=5,
        )
    missing = [key for key, _label in DIMENSIONS if key not in scores]
    if require_all and missing:
        raise SystemExit("missing required score dimensions: " + ", ".join(missing))
    return normalized


def normalize_evidence_map(evidence: object, *, require_all: bool) -> dict[str, list[str]]:
    if evidence is None:
        evidence_map: dict[str, object] = {}
    elif isinstance(evidence, dict):
        evidence_map = evidence
    else:
        fail_input("evidence", "evidence", "expected object with per-dimension evidence lists")

    missing = [key for key, _label in DIMENSIONS if key not in evidence_map]
    if require_all and missing:
        raise SystemExit("missing required evidence dimensions: " + ", ".join(missing))

    normalized: dict[str, list[str]] = {}
    for key, _label in DIMENSIONS:
        if key not in evidence_map:
            normalized[key] = []
            continue
        value = evidence_map[key]
        if not isinstance(value, list):
            fail_input("evidence", key, "expected non-empty array of evidence strings")
        if not value:
            fail_input("evidence", key, "evidence array must not be empty")
        normalized_items: list[str] = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                fail_input("evidence", key, f"expected non-empty string evidence item, got {item!r}")
            normalized_items.append(item.strip())
        normalized[key] = normalized_items
    return normalized


def normalize_readiness_map(readiness: object, *, require_all: bool = False) -> dict[str, int]:
    if readiness is None:
        return {}
    if not isinstance(readiness, dict):
        fail_input("agent_readiness", "agent_readiness", "expected object with readiness dimensions")
    missing = [key for key in READINESS_KEYS if key not in readiness]
    if require_all and missing:
        raise SystemExit("missing required agent_readiness dimensions: " + ", ".join(missing))
    normalized: dict[str, int] = {}
    for key in READINESS_KEYS:
        if key not in readiness:
            normalized[key] = 0
            continue
        normalized[key] = require_int_in_range(
            readiness[key],
            context="agent_readiness",
            label=key,
            minimum=0,
            maximum=5,
        )
    return normalized


def evaluate_ai_compatible(readiness: dict[str, object]) -> str:
    normalized = normalize_readiness_map(readiness)
    if not normalized:
        return "NO"
    values = list(normalized.values())
    if min(values, default=0) >= 4:
        return "YES"
    average = sum(values) / len(values) if values else 0
    if average >= 2.5:
        return "PARTIAL"
    return "NO"


def evaluate_repo_governance(
    data: dict,
    *,
    require_evidence: bool = True,
    require_all_scores: bool = True,
) -> dict:
    if not isinstance(data, dict):
        raise SystemExit("input JSON must be an object with governance fields")
    scores_input = data.get("scores", data)
    if not isinstance(scores_input, dict):
        raise SystemExit("scores must be an object when provided")
    scores = normalize_score_map(scores_input, require_all=require_all_scores)
    evidence = normalize_evidence_map(data.get("evidence"), require_all=require_evidence)
    readiness = normalize_readiness_map(data.get("agent_readiness"))
    dimensions: dict[str, dict] = {}
    total = 0
    for key, label in DIMENSIONS:
        score = scores[key]
        total += score
        dimensions[key] = {
            "label": label,
            "score": score,
            "evidence": evidence[key],
        }

    rating = next(label for threshold, label in RATING_BANDS if total >= threshold)
    if dimensions["change_governance"]["score"] <= 2 and total >= 16:
        rating = "可用（存在治理风险，变更治理薄弱）"

    return {
        "repo_type": data.get("repo_type", "unknown"),
        "total": total,
        "max": 25,
        "rating": rating,
        "dimensions": dimensions,
        "top_issues": data.get("top_issues", []),
        "suggestions_30d": data.get("suggestions_30d", []),
        "ai_compatible": evaluate_ai_compatible(readiness),
        "agent_readiness": readiness,
        "risk_model": data.get("risk_model", {}),
        "guardrails": [
            "不要因为文档多而高分，必须看可执行性与一致性。",
            "不要因为代码整齐而忽略 Change Governance。",
            "避免形式化：过渡阶段允许有条件通过，但要有复评时间。",
            "避免伪闭环：所有结论必须附证据。",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repo governance evaluation aligned with the prompt rubric")
    parser.add_argument("--input", required=True, help="JSON file with 5 dimension scores (0-5)")
    parser.add_argument("--output", default="", help="Optional output json path")
    return parser.parse_args()


def load_input_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in input file {path}: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("input JSON must be an object with governance fields")

    scores = payload.get("scores", payload)
    if not isinstance(scores, dict):
        raise SystemExit("scores must be an object when provided")
    normalize_score_map(scores, require_all=True)

    readiness = payload.get("agent_readiness", {})
    if not isinstance(readiness, dict):
        raise SystemExit("agent_readiness must be an object when provided")
    normalize_readiness_map(readiness, require_all=False)

    evidence = payload.get("evidence")
    normalize_evidence_map(evidence, require_all=True)

    return payload


def main() -> int:
    args = parse_args()
    data = load_input_json(Path(args.input))
    result = evaluate_repo_governance(data)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    print(payload)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
