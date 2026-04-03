#!/usr/bin/env python3
import argparse, json
from pathlib import Path

DIMENSIONS = ["rule", "folders", "document", "code"]

def grade(score: int) -> str:
    if score >= 80:
        return "通过"
    if score >= 60:
        return "有条件通过"
    return "不通过"

def suggest(dim: str, g: str):
    if g == "通过":
        return "保持现状，按周小步复查，避免过度治理。"
    if dim == "rule":
        return "补齐最低约束规则与例外条件，避免规则过密导致开发冻结。"
    if dim == "folders":
        return "先清理高频误用目录与临时落地路径，再做目录重构。"
    if dim == "document":
        return "优先修复真相层文档与入口导航，不做大规模文档美化。"
    if dim == "code":
        return "优先处理影响交付的技术债与测试缺口，避免一次性大重构。"
    return "按最小改动补齐风险项。"

def main():
    ap = argparse.ArgumentParser(description="Governance maturity assessor for harness closure")
    ap.add_argument("--input", required=True, help="JSON file with scores: rule/folders/document/code (0-100)")
    ap.add_argument("--output", default="", help="optional output json path")
    args = ap.parse_args()

    scores = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = {"dimensions": {}, "overall": "通过", "suggestions": [], "guardrails": []}

    worst = 2
    for dim in DIMENSIONS:
        score = int(scores.get(dim, 0))
        g = grade(score)
        result["dimensions"][dim] = {"score": score, "grade": g, "suggestion": suggest(dim, g)}
        result["suggestions"].append({"dimension": dim, "action": suggest(dim, g)})
        worst = min(worst, ["不通过", "有条件通过", "通过"].index(g))

    result["overall"] = ["不通过", "有条件通过", "通过"][worst]
    result["guardrails"] = [
        "避免形式化治理：临时过渡阶段允许有限豁免，但必须设到期条件。",
        "避免伪闭环：评分必须附证据（文件/命令/差异）而非主观口径。",
        "避免高分低质：若 code 维度不通过，整体不得评为通过。"
    ]

    if result["dimensions"]["code"]["grade"] == "不通过":
        result["overall"] = "不通过"

    txt = json.dumps(result, ensure_ascii=False, indent=2)
    print(txt)
    if args.output:
        Path(args.output).write_text(txt, encoding="utf-8")

if __name__ == "__main__":
    main()
