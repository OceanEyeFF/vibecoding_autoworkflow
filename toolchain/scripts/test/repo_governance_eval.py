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
RATING_BANDS = (
    (22, "工业级（可长期稳定维护）"),
    (16, "可用（存在治理风险）"),
    (10, "技术债明显"),
    (0, "不可维护"),
)


def evaluate_ai_compatible(readiness: dict[str, int]) -> str:
    keys = ("task_split", "local_context", "auto_validation", "safe_change")
    values = [int(readiness.get(key, 0)) for key in keys]
    if min(values, default=0) >= 4:
        return "YES"
    average = sum(values) / len(values) if values else 0
    if average >= 2.5:
        return "PARTIAL"
    return "NO"


def evaluate_repo_governance(data: dict) -> dict:
    scores = data.get("scores", data)
    dimensions: dict[str, dict] = {}
    total = 0
    for key, label in DIMENSIONS:
        score = max(0, min(5, int(scores.get(key, 0))))
        total += score
        dimensions[key] = {
            "label": label,
            "score": score,
            "evidence": data.get("evidence", {}).get(key, []),
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
        "ai_compatible": evaluate_ai_compatible(data.get("agent_readiness", {})),
        "agent_readiness": data.get("agent_readiness", {}),
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
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in input file {path}: {exc.msg}") from exc


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
