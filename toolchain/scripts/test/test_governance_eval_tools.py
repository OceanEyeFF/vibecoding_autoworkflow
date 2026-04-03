from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from governance_assess import evaluate_governance, load_input_json as load_governance_input_json
from repo_governance_eval import (
    evaluate_ai_compatible,
    evaluate_repo_governance,
    load_input_json as load_repo_input_json,
)


def test_evaluate_governance_caps_overall_when_code_fails() -> None:
    result = evaluate_governance({"rule": 95, "folders": 90, "document": 85, "code": 30})

    assert result["dimensions"]["rule"]["grade"] == "通过"
    assert result["dimensions"]["code"]["grade"] == "不通过"
    assert result["overall"] == "不通过"


def test_evaluate_governance_marks_conditional_pass() -> None:
    result = evaluate_governance({"rule": 65, "folders": 82, "document": 61, "code": 88})

    assert result["dimensions"]["rule"]["grade"] == "有条件通过"
    assert result["overall"] == "有条件通过"
    assert len(result["suggestions"]) == 4


def test_evaluate_ai_compatible_uses_floor_and_average() -> None:
    assert evaluate_ai_compatible({"task_split": 4, "local_context": 4, "auto_validation": 4, "safe_change": 4}) == "YES"
    assert evaluate_ai_compatible({"task_split": 3, "local_context": 3, "auto_validation": 2, "safe_change": 2}) == "PARTIAL"
    assert evaluate_ai_compatible({"task_split": 1, "local_context": 2, "auto_validation": 1, "safe_change": 1}) == "NO"


def test_evaluate_repo_governance_applies_change_governance_cap() -> None:
    result = evaluate_repo_governance(
        {
            "repo_type": "long_term_product",
            "scores": {
                "baseline_hygiene": 5,
                "change_governance": 2,
                "automation": 5,
                "structural_clarity": 4,
                "operational_maintainability": 4,
            },
            "evidence": {"change_governance": ["docs/operations/branch-pr-governance.md"]},
        }
    )

    assert result["total"] == 20
    assert result["rating"] == "可用（存在治理风险，变更治理薄弱）"
    assert result["dimensions"]["change_governance"]["evidence"] == ["docs/operations/branch-pr-governance.md"]


def test_load_input_json_reports_missing_file() -> None:
    with pytest.raises(SystemExit, match="input file not found"):
        load_governance_input_json(Path("/tmp/definitely-missing-governance-input.json"))

    with pytest.raises(SystemExit, match="input file not found"):
        load_repo_input_json(Path("/tmp/definitely-missing-repo-governance-input.json"))
