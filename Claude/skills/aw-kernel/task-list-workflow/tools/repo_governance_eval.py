#!/usr/bin/env python3
import argparse, json
from pathlib import Path

DIM_KEYS = [
    ("baseline_hygiene", "A. Baseline Hygiene"),
    ("change_governance", "B. Change Governance"),
    ("automation", "C. Automation"),
    ("structural_clarity", "D. Structural Clarity"),
    ("operational_maintainability", "E. Operational Maintainability"),
]

RUBRIC = [
    (22, "工业级（可长期稳定维护）"),
    (16, "可用（存在治理风险）"),
    (10, "技术债明显"),
    (0, "不可维护"),
]

def ai_compatible(readiness: dict):
    vals = [int(readiness.get(k, 0)) for k in ["task_split", "local_context", "auto_validation", "safe_change"]]
    avg = sum(vals) / 4 if vals else 0
    if min(vals, default=0) >= 4:
        return "YES"
    if avg >= 2.5:
        return "PARTIAL"
    return "NO"

def main():
    ap = argparse.ArgumentParser(description="Repo governance evaluation (Prompt+Rubric aligned)")
    ap.add_argument("--input", required=True, help="JSON with 5 dimension scores (0-5)")
    ap.add_argument("--output", default="")
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    scores = data.get("scores", data)

    details = {}
    total = 0
    for k, label in DIM_KEYS:
        s = max(0, min(5, int(scores.get(k, 0))))
        details[k] = {"label": label, "score": s, "evidence": data.get("evidence", {}).get(k, [])}
        total += s

    rating = next(txt for threshold, txt in RUBRIC if total >= threshold)

    # Change Governance is highest priority: low score caps final judgement
    if details["change_governance"]["score"] <= 2 and total >= 16:
        rating = "可用（存在治理风险，变更治理薄弱）"

    result = {
        "repo_type": data.get("repo_type", "unknown"),
        "total": total,
        "max": 25,
        "rating": rating,
        "dimensions": details,
        "top_issues": data.get("top_issues", []),
        "suggestions_30d": data.get("suggestions_30d", []),
        "ai_compatible": ai_compatible(data.get("agent_readiness", {})),
        "agent_readiness": data.get("agent_readiness", {}),
        "risk_model": data.get("risk_model", {}),
        "guardrails": [
            "不要因为文档多而高分，必须看可执行性与一致性。",
            "不要因为代码整齐而忽略 Change Governance。",
            "避免形式化：过渡阶段允许有条件通过，但要有复评时间。",
            "避免伪闭环：所有结论必须附证据。"
        ]
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")

if __name__ == "__main__":
    main()
