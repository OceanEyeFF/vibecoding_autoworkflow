#!/usr/bin/env python3
"""Assess minimal governance readiness for harness closeout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DIMENSIONS = ("rule", "folders", "document", "code")
MIN_SCORE = 0
MAX_SCORE = 100
GRADE_ORDER = {"不通过": 0, "有条件通过": 1, "通过": 2}


def coerce_score(value: object, label: str, *, context: str) -> int:
    if value is None:
        raise SystemExit(
            f"invalid {context} '{label}': null is not allowed, expected number between {MIN_SCORE} and {MAX_SCORE}"
        )
    if isinstance(value, bool):
        raise SystemExit(
            f"invalid {context} '{label}': boolean is not allowed, expected number between {MIN_SCORE} and {MAX_SCORE}"
        )
    if not isinstance(value, int):
        raise SystemExit(
            f"invalid {context} '{label}': expected number between {MIN_SCORE} and {MAX_SCORE}, got {value!r}"
        )
    if value < MIN_SCORE or value > MAX_SCORE:
        raise SystemExit(
            f"invalid {context} '{label}': expected number between {MIN_SCORE} and {MAX_SCORE}, got {value}"
        )
    return value


def coerce_evidence_items(value: object, label: str, *, context: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise SystemExit(f"invalid {context} '{label}': expected a non-empty array of evidence strings")
    normalized: list[str] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item.strip():
            raise SystemExit(f"invalid {context} '{label}' item #{index}: expected a non-empty evidence string")
        normalized.append(" ".join(item.split()))
    return normalized


def _score_source(payload: dict[str, object]) -> dict[str, object]:
    scores = payload.get("scores")
    if scores is None:
        scores = payload
    if not isinstance(scores, dict):
        raise SystemExit("input JSON must be an object or contain a 'scores' object")
    return scores


def _validate_scores(payload: dict[str, object]) -> dict[str, int]:
    scores = _score_source(payload)
    normalized: dict[str, int] = {}
    for dimension in DIMENSIONS:
        if dimension not in scores:
            raise SystemExit(f"missing score for dimension '{dimension}'")
        normalized[dimension] = coerce_score(scores[dimension], dimension, context="score")
    return normalized


def _validate_evidence(payload: dict[str, object], *, require_presence: bool) -> dict[str, list[str]]:
    evidence = payload.get("evidence")
    if evidence is None:
        if require_presence:
            raise SystemExit("input JSON must include an 'evidence' object")
        return {dimension: [] for dimension in DIMENSIONS}
    if not isinstance(evidence, dict):
        raise SystemExit("input JSON field 'evidence' must be an object")
    missing_dimensions = [dimension for dimension in DIMENSIONS if dimension not in evidence]
    if missing_dimensions:
        raise SystemExit("missing evidence for dimensions: " + ", ".join(missing_dimensions))
    normalized: dict[str, list[str]] = {}
    for dimension in DIMENSIONS:
        normalized[dimension] = coerce_evidence_items(evidence[dimension], dimension, context="evidence")
    return normalized


def score_from(scores: dict[str, int], dimension: str) -> int:
    return scores[dimension]


def grade(score: int) -> str:
    if score >= 80:
        return "通过"
    if score >= 60:
        return "有条件通过"
    return "不通过"


def suggest(dimension: str, result_grade: str) -> str:
    if result_grade == "通过":
        return "保持现状，按周小步复查，避免过度治理。"
    if dimension == "rule":
        return "补齐最低约束规则与例外条件，避免规则过密导致开发冻结。"
    if dimension == "folders":
        return "先清理高频误用目录与临时落地路径，再做目录重构。"
    if dimension == "document":
        return "优先修复真相层文档与入口导航，不做大规模文档美化。"
    if dimension == "code":
        return "优先处理影响交付的技术债与测试缺口，避免一次性大重构。"
    return "按最小改动补齐风险项。"


def evaluate_governance(payload: dict[str, object], *, require_evidence: bool = True) -> dict:
    scores = _validate_scores(payload)
    evidence = _validate_evidence(payload, require_presence=require_evidence)
    result = {"dimensions": {}, "overall": "通过", "suggestions": [], "guardrails": []}
    overall_rank = GRADE_ORDER["通过"]
    for dimension in DIMENSIONS:
        score = score_from(scores, dimension)
        result_grade = grade(score)
        result["dimensions"][dimension] = {
            "score": score,
            "grade": result_grade,
            "suggestion": suggest(dimension, result_grade),
            "evidence": evidence[dimension],
        }
        result["suggestions"].append({"dimension": dimension, "action": suggest(dimension, result_grade)})
        overall_rank = min(overall_rank, GRADE_ORDER[result_grade])

    reverse_grade_order = {value: key for key, value in GRADE_ORDER.items()}
    result["overall"] = reverse_grade_order[overall_rank]
    result["evidence"] = evidence
    result["guardrails"] = [
        "避免形式化治理：过渡阶段允许有限豁免，但必须设到期条件。",
        "避免伪闭环：评分必须附证据（文件、命令、差异）而非主观口径。",
        "避免高分低质：若 code 维度不通过，整体不得评为通过。",
    ]

    if result["dimensions"]["code"]["grade"] == "不通过":
        result["overall"] = "不通过"
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Governance maturity assessor for harness closure")
    parser.add_argument("--input", required=True, help="JSON file with scores: rule/folders/document/code (0-100)")
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
        raise SystemExit("input JSON must be an object with score fields")
    scores = _score_source(payload)
    for dimension in DIMENSIONS:
        if dimension in scores:
            coerce_score(scores[dimension], dimension, context="score")
    if "evidence" in payload:
        _validate_evidence(payload, require_presence=False)
    return payload


def main() -> int:
    args = parse_args()
    scores = load_input_json(Path(args.input))
    result = evaluate_governance(scores, require_evidence=True)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    print(payload)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
