from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_cross_layer_sync import check_charter_registry_consistency


def write_doc(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_charter_registry_uses_tracked_source_without_runtime_aw(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "product/harness/skills/set-harness-goal-skill/assets/goal-charter.md",
        "\n".join(
            [
                "### Node Type Registry",
                "",
                "| type | merge_required |",
                "|------|----------------|",
                "| `bugfix` | yes |",
            ]
        )
        + "\n",
    )
    write_doc(
        tmp_path / "docs/harness/artifact/control/node-type-registry.md",
        "### bugfix\n",
    )

    result = check_charter_registry_consistency(tmp_path)

    assert result["status"] == "pass"
    assert any("runtime charter instance absent" in item for item in result["infos"])


def test_charter_registry_does_not_promote_runtime_aw_truth(tmp_path: Path) -> None:
    write_doc(
        tmp_path / "product/harness/skills/set-harness-goal-skill/assets/goal-charter.md",
        "\n".join(
            [
                "### Node Type Registry",
                "",
                "| type | merge_required |",
                "|------|----------------|",
                "| `bugfix` | yes |",
            ]
        )
        + "\n",
    )
    write_doc(
        tmp_path / "docs/harness/artifact/control/node-type-registry.md",
        "### bugfix\n",
    )
    write_doc(
        tmp_path / ".aw/goal-charter.md",
        "\n".join(
            [
                "### Node Type Registry",
                "",
                "| type | merge_required |",
                "|------|----------------|",
                "| `runtime-only` | yes |",
            ]
        )
        + "\n",
    )

    result = check_charter_registry_consistency(tmp_path)

    assert result["status"] == "pass"
    assert any("runtime charter instance present" in item for item in result["infos"])
