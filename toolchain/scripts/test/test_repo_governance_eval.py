from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from repo_governance_eval import evaluate_repo_governance, load_input_json


def test_evaluate_repo_governance_accepts_valid_payload() -> None:
    result = evaluate_repo_governance(
        {
            "repo_type": "long_term_product",
            "scores": {
                "baseline_hygiene": 5,
                "change_governance": 4,
                "automation": 4,
                "structural_clarity": 5,
                "operational_maintainability": 4,
            },
            "evidence": {
                "baseline_hygiene": ["docs/README.md"],
                "change_governance": ["docs/operations/review-verify-handbook.md"],
                "automation": ["toolchain/scripts/test/README.md"],
                "structural_clarity": ["docs/knowledge/foundations/root-directory-layering.md"],
                "operational_maintainability": ["toolchain/scripts/test/repo_governance_eval.py"],
            },
            "agent_readiness": {
                "task_split": 4,
                "local_context": 4,
                "auto_validation": 4,
                "safe_change": 4,
            },
        },
        require_evidence=True,
    )

    assert result["total"] == 22
    assert result["rating"] == "工业级（可长期稳定维护）"
    assert result["ai_compatible"] == "YES"
    assert result["dimensions"]["change_governance"]["evidence"] == ["docs/operations/review-verify-handbook.md"]


def test_load_input_json_rejects_missing_evidence_dimension(tmp_path: Path) -> None:
    payload_path = tmp_path / "governance.json"
    payload_path.write_text(
        json.dumps(
            {
                "scores": {
                    "baseline_hygiene": 5,
                    "change_governance": 4,
                    "automation": 4,
                    "structural_clarity": 5,
                    "operational_maintainability": 4,
                },
                "evidence": {
                    "baseline_hygiene": ["docs/README.md"],
                    "change_governance": ["docs/operations/review-verify-handbook.md"],
                    "automation": ["toolchain/scripts/test/README.md"],
                    "structural_clarity": ["docs/knowledge/foundations/root-directory-layering.md"],
                },
                "agent_readiness": {
                    "task_split": 4,
                    "local_context": 4,
                    "auto_validation": 4,
                    "safe_change": 4,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="missing required evidence dimensions: operational_maintainability"):
        load_input_json(payload_path)


def test_evaluate_repo_governance_rejects_out_of_range_score() -> None:
    with pytest.raises(SystemExit, match="invalid score 'automation': expected number in range 0-5"):
        evaluate_repo_governance(
            {
                "scores": {
                    "baseline_hygiene": 5,
                    "change_governance": 4,
                    "automation": 6,
                    "structural_clarity": 5,
                    "operational_maintainability": 4,
                },
                "evidence": {
                    "baseline_hygiene": ["docs/README.md"],
                    "change_governance": ["docs/operations/review-verify-handbook.md"],
                    "automation": ["toolchain/scripts/test/README.md"],
                    "structural_clarity": ["docs/knowledge/foundations/root-directory-layering.md"],
                    "operational_maintainability": ["toolchain/scripts/test/repo_governance_eval.py"],
                },
                "agent_readiness": {
                    "task_split": 4,
                    "local_context": 4,
                    "auto_validation": 4,
                    "safe_change": 4,
                },
            },
            require_evidence=True,
        )


def test_evaluate_repo_governance_accepts_partial_scores_when_allowed() -> None:
    result = evaluate_repo_governance(
        {
            "repo_type": "long_term_product",
            "scores": {
                "baseline_hygiene": 5,
                "change_governance": 4,
            },
            "evidence": {
                "baseline_hygiene": ["docs/README.md"],
                "change_governance": ["docs/operations/review-verify-handbook.md"],
                "automation": ["toolchain/scripts/test/README.md"],
                "structural_clarity": ["docs/knowledge/foundations/root-directory-layering.md"],
                "operational_maintainability": ["toolchain/scripts/test/repo_governance_eval.py"],
            },
        },
        require_evidence=True,
        require_all_scores=False,
    )

    assert result["total"] == 9
    assert result["dimensions"]["baseline_hygiene"]["score"] == 5
    assert result["dimensions"]["change_governance"]["score"] == 4
    assert result["dimensions"]["automation"]["score"] == 0
    assert result["dimensions"]["structural_clarity"]["score"] == 0
    assert result["dimensions"]["operational_maintainability"]["score"] == 0


def test_evaluate_repo_governance_rejects_out_of_range_agent_readiness() -> None:
    with pytest.raises(
        SystemExit,
        match="invalid agent_readiness 'safe_change': expected number in range 0-5",
    ):
        evaluate_repo_governance(
            {
                "scores": {
                    "baseline_hygiene": 5,
                    "change_governance": 4,
                    "automation": 4,
                    "structural_clarity": 5,
                    "operational_maintainability": 4,
                },
                "evidence": {
                    "baseline_hygiene": ["docs/README.md"],
                    "change_governance": ["docs/operations/review-verify-handbook.md"],
                    "automation": ["toolchain/scripts/test/README.md"],
                    "structural_clarity": ["docs/knowledge/foundations/root-directory-layering.md"],
                    "operational_maintainability": ["toolchain/scripts/test/repo_governance_eval.py"],
                },
                "agent_readiness": {
                    "task_split": 4,
                    "local_context": 4,
                    "auto_validation": 4,
                    "safe_change": 6,
                },
            },
            require_evidence=True,
        )
