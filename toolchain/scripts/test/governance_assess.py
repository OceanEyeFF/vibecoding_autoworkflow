#!/usr/bin/env python3
"""Assess minimal governance readiness for harness closeout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DIMENSIONS = ("rule", "folders", "document", "code")
GRADE_ORDER = {"不通过": 0, "有条件通过": 1, "通过": 2}


def coerce_int(value: object, label: str, *, context: str) -> int:
    if value is None:
        raise SystemExit(f"invalid {context} '{label}': null is not allowed, expected number")
    if isinstance(value, bool):
        raise SystemExit(f"invalid {context} '{label}': boolean is not allowed, expected number")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"invalid {context} '{label}': expected number, got {value!r}") from exc


def score_from(scores: dict[str, object], dimension: str) -> int:
    if dimension in scores:
        value = scores[dimension]
    else:
        value = 0
    return coerce_int(value, dimension, context="score")


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


def evaluate_governance(scores: dict[str, object]) -> dict:
    result = {"dimensions": {}, "overall": "通过", "suggestions": [], "guardrails": []}
    overall_rank = GRADE_ORDER["通过"]
    for dimension in DIMENSIONS:
        score = score_from(scores, dimension)
        result_grade = grade(score)
        result["dimensions"][dimension] = {
            "score": score,
            "grade": result_grade,
            "suggestion": suggest(dimension, result_grade),
        }
        result["suggestions"].append({"dimension": dimension, "action": suggest(dimension, result_grade)})
        overall_rank = min(overall_rank, GRADE_ORDER[result_grade])

    reverse_grade_order = {value: key for key, value in GRADE_ORDER.items()}
    result["overall"] = reverse_grade_order[overall_rank]
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
    for dimension in DIMENSIONS:
        if dimension in payload:
            coerce_int(payload[dimension], dimension, context="score")
    return payload


def main() -> int:
    args = parse_args()
    scores = load_input_json(Path(args.input))
    result = evaluate_governance(scores)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    print(payload)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
