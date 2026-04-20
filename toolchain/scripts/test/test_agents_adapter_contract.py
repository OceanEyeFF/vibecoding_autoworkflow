from __future__ import annotations

import json
import unittest
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTER_SKILLS_DIR = REPO_ROOT / "product" / "harness" / "adapters" / "agents" / "skills"
FIRST_WAVE_FREEZE_DOC = (
    REPO_ROOT / "docs" / "project-maintenance" / "deploy" / "first-wave-skill-freeze.md"
)
EXPECTED_FIRST_WAVE_SKILLS = {
    "dispatch-skills": {
        "first_wave_scope_kind": "subset-by-a3-freeze",
    },
    "harness-skill": {
        "first_wave_scope_kind": "full-skill",
    },
    "init-worktrack-skill": {
        "first_wave_scope_kind": "subset-by-a3-freeze",
    },
    "repo-status-skill": {
        "first_wave_scope_kind": "full-skill",
    },
    "repo-whats-next-skill": {
        "first_wave_scope_kind": "subset-by-a3-freeze",
        "supported_repo_actions": ["enter-worktrack", "hold-and-observe"],
    },
    "schedule-worktrack-skill": {
        "first_wave_scope_kind": "full-skill",
    },
}
EXPECTED_FIRST_WAVE_SKILL_ORDER = [
    "harness-skill",
    "repo-status-skill",
    "repo-whats-next-skill",
    "init-worktrack-skill",
    "schedule-worktrack-skill",
    "dispatch-skills",
]


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def included_paths_from_payload(payload: dict[str, object]) -> list[str]:
    canonical_dir = payload["canonical_dir"]
    canonical_paths = payload["canonical_paths"]
    assert isinstance(canonical_dir, str)
    assert isinstance(canonical_paths, list)

    canonical_dir_path = PurePosixPath(canonical_dir)
    included_paths: list[str] = []
    for canonical_path in canonical_paths:
        assert isinstance(canonical_path, str)
        included_paths.append(PurePosixPath(canonical_path).relative_to(canonical_dir_path).as_posix())
    return included_paths


def extract_bullet_block(text: str, start_marker: str, end_marker: str) -> list[str]:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    block = text[start:end]
    lines = []
    for raw_line in block.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("- `") and stripped.endswith("`"):
            lines.append(stripped[len("- `") : -1])
    return lines


class AgentsAdapterContractTest(unittest.TestCase):
    def test_first_wave_agents_adapter_payloads_follow_b3_contract(self) -> None:
        adapter_skill_dirs = sorted(
            path.name for path in ADAPTER_SKILLS_DIR.iterdir() if path.is_dir()
        )
        self.assertEqual(adapter_skill_dirs, sorted(EXPECTED_FIRST_WAVE_SKILLS))

        for skill_id in adapter_skill_dirs:
            payload_path = ADAPTER_SKILLS_DIR / skill_id / "payload.json"

            self.assertTrue(payload_path.is_file(), payload_path)
            self.assertEqual(
                sorted(path.name for path in (ADAPTER_SKILLS_DIR / skill_id).iterdir() if path.is_file()),
                ["payload.json"],
            )

            payload = load_json(payload_path)
            included_paths = included_paths_from_payload(payload)
            canonical_dir = payload["canonical_dir"]
            canonical_paths = payload["canonical_paths"]

            self.assertEqual(payload["payload_version"], "agents-skill-payload.v1")
            self.assertEqual(payload["backend"], "agents")
            self.assertEqual(payload["skill_id"], skill_id)
            self.assertEqual(payload["canonical_dir"], f"product/harness/skills/{skill_id}")
            self.assertEqual(payload["canonical_paths"], [f"{canonical_dir}/{path}" for path in included_paths])
            self.assertEqual(payload["target_dir"], skill_id)
            self.assertEqual(payload["target_entry_name"], "SKILL.md")
            self.assertEqual(payload["payload_policy"], "canonical-copy")
            self.assertEqual(payload["supported_target_scopes"], ["local"])
            self.assertEqual(payload["reference_distribution"], "copy-listed-canonical-paths")
            self.assertEqual(
                payload["required_payload_files"],
                [*included_paths, "payload.json", "aw.marker"],
            )
            self.assertEqual(payload["first_wave_profile"], "a3-first-wave")
            self.assertEqual(
                payload["first_wave_scope_kind"],
                EXPECTED_FIRST_WAVE_SKILLS[skill_id]["first_wave_scope_kind"],
            )
            self.assertEqual(Path(str(canonical_dir)).name, skill_id)

            expected_repo_actions = EXPECTED_FIRST_WAVE_SKILLS[skill_id].get("supported_repo_actions")
            actual_repo_actions = payload.get("supported_repo_actions")
            if expected_repo_actions is None:
                self.assertNotIn("supported_repo_actions", payload)
            else:
                self.assertEqual(actual_repo_actions, expected_repo_actions)

            for canonical_path in canonical_paths:
                self.assertTrue((REPO_ROOT / canonical_path).is_file(), canonical_path)

    def test_first_wave_agents_adapter_target_dirs_are_unique(self) -> None:
        target_dir_to_skills: dict[str, list[str]] = {}

        for skill_dir in sorted(path for path in ADAPTER_SKILLS_DIR.iterdir() if path.is_dir()):
            skill_id = skill_dir.name
            payload_path = ADAPTER_SKILLS_DIR / skill_id / "payload.json"

            self.assertTrue(payload_path.is_file(), payload_path)

            payload = load_json(payload_path)
            target_dir = payload["target_dir"]

            self.assertIsInstance(target_dir, str)
            target_dir_to_skills.setdefault(target_dir, []).append(skill_id)

        duplicates = {
            target_dir: sorted(skill_ids)
            for target_dir, skill_ids in target_dir_to_skills.items()
            if len(skill_ids) > 1
        }
        self.assertEqual(
            duplicates,
            {},
            f"duplicate target_dir bindings are not allowed: {duplicates}",
        )

    def test_first_wave_freeze_doc_matches_live_skill_set(self) -> None:
        text = FIRST_WAVE_FREEZE_DOC.read_text(encoding="utf-8")

        in_scope = extract_bullet_block(
            text,
            "当前首发范围固定为以下六个 canonical skills",
            "各自承担的最小角色如下：",
        )
        self.assertEqual(in_scope, EXPECTED_FIRST_WAVE_SKILL_ORDER)

        out_of_scope = extract_bullet_block(
            text,
            "当前仓库里其余已存在的 canonical skills（规范 skill），全部不进入首发范围：",
            "其中可按两类理解：",
        )
        self.assertNotIn("schedule-worktrack-skill", out_of_scope)


if __name__ == "__main__":
    unittest.main()
