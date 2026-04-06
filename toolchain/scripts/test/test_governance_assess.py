from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import governance_assess


def _write_input(tmp_path: Path, payload: dict) -> Path:
    input_path = tmp_path / "governance-input.json"
    input_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return input_path


def _valid_payload() -> dict:
    return {
        "rule": 95,
        "folders": 88,
        "document": 84,
        "code": 91,
        "evidence": {
            "rule": ["docs/knowledge/foundations/docs-governance.md"],
            "folders": ["toolchain/scripts/test/README.md"],
            "document": ["docs/operations/prompt-templates/review-loop-code-review.md"],
            "code": ["toolchain/scripts/test/governance_assess.py"],
        },
    }


def test_main_requires_evidence_object(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_path = _write_input(
        tmp_path,
        {
            "rule": 95,
            "folders": 88,
            "document": 84,
            "code": 91,
        },
    )
    monkeypatch.setattr(sys, "argv", ["governance_assess.py", "--input", str(input_path)])

    with pytest.raises(SystemExit, match="must include an 'evidence' object"):
        governance_assess.main()


def test_main_rejects_partial_evidence_map(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_path = _write_input(
        tmp_path,
        {
            "rule": 95,
            "folders": 88,
            "document": 84,
            "code": 91,
            "evidence": {
                "rule": ["docs/knowledge/foundations/docs-governance.md"],
                "folders": ["toolchain/scripts/test/README.md"],
                "document": ["docs/operations/prompt-templates/review-loop-code-review.md"],
            },
        },
    )
    monkeypatch.setattr(sys, "argv", ["governance_assess.py", "--input", str(input_path)])

    with pytest.raises(SystemExit, match="missing evidence for dimensions: code"):
        governance_assess.main()


def test_load_input_json_rejects_out_of_range_scores(tmp_path: Path) -> None:
    input_path = _write_input(
        tmp_path,
        {
            "rule": 101,
            "folders": 88,
            "document": 84,
            "code": 91,
            "evidence": {
                "rule": ["docs/knowledge/foundations/docs-governance.md"],
                "folders": ["toolchain/scripts/test/README.md"],
                "document": ["docs/operations/prompt-templates/review-loop-code-review.md"],
                "code": ["toolchain/scripts/test/governance_assess.py"],
            },
        },
    )

    with pytest.raises(SystemExit, match="expected number between 0 and 100, got 101"):
        governance_assess.load_input_json(input_path)


def test_main_includes_evidence_in_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = _write_input(tmp_path, _valid_payload())
    monkeypatch.setattr(sys, "argv", ["governance_assess.py", "--input", str(input_path)])

    assert governance_assess.main() == 0

    result = json.loads(capsys.readouterr().out)
    assert result["overall"] == "通过"
    assert result["dimensions"]["rule"]["evidence"] == ["docs/knowledge/foundations/docs-governance.md"]
    assert result["evidence"]["code"] == ["toolchain/scripts/test/governance_assess.py"]
