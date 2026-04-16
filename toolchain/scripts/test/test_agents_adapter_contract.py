from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTER_SKILLS_DIR = REPO_ROOT / "product" / "harness" / "adapters" / "agents" / "skills"
MANIFEST_DIR = REPO_ROOT / "product" / "harness" / "manifests" / "agents" / "skills"
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
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class AgentsAdapterContractTest(unittest.TestCase):
    def test_first_wave_agents_adapter_payloads_follow_b3_contract(self) -> None:
        adapter_skill_dirs = sorted(
            path.name for path in ADAPTER_SKILLS_DIR.iterdir() if path.is_dir()
        )
        self.assertEqual(adapter_skill_dirs, sorted(EXPECTED_FIRST_WAVE_SKILLS))

        for skill_id in adapter_skill_dirs:
            wrapper_path = ADAPTER_SKILLS_DIR / skill_id / "SKILL.md"
            payload_path = ADAPTER_SKILLS_DIR / skill_id / "payload.json"
            manifest_path = MANIFEST_DIR / f"{skill_id}.json"

            self.assertTrue(wrapper_path.is_file(), wrapper_path)
            self.assertTrue(payload_path.is_file(), payload_path)
            self.assertTrue(manifest_path.is_file(), manifest_path)

            wrapper_text = wrapper_path.read_text(encoding="utf-8")
            payload = load_json(payload_path)
            manifest = load_json(manifest_path)

            self.assertEqual(payload["payload_version"], "agents-skill-payload.v1")
            self.assertEqual(payload["backend"], "agents")
            self.assertEqual(payload["skill_id"], skill_id)
            self.assertEqual(payload["manifest_path"], manifest_path.relative_to(REPO_ROOT).as_posix())
            self.assertEqual(payload["canonical_dir"], manifest["canonical_dir"])

            expected_canonical_paths = [
                f"{manifest['canonical_dir']}/{included_path}"
                for included_path in manifest["included_paths"]
            ]
            self.assertEqual(payload["canonical_paths"], expected_canonical_paths)
            self.assertEqual(payload["target_dir"], manifest["target_dir"])
            self.assertEqual(payload["target_dir"], skill_id)
            self.assertEqual(payload["target_entry_name"], "SKILL.md")
            self.assertEqual(payload["payload_policy"], "thin-shell")
            self.assertEqual(payload["supported_target_scopes"], ["local"])
            self.assertEqual(payload["reference_distribution"], "repo-read-through-local-only")
            self.assertEqual(payload["required_payload_files"], ["SKILL.md", "payload.json"])
            self.assertEqual(payload["first_wave_profile"], manifest["first_wave_profile"])
            self.assertEqual(
                payload["first_wave_scope_kind"],
                EXPECTED_FIRST_WAVE_SKILLS[skill_id]["first_wave_scope_kind"],
            )

            expected_repo_actions = EXPECTED_FIRST_WAVE_SKILLS[skill_id].get("supported_repo_actions")
            actual_repo_actions = payload.get("supported_repo_actions")
            if expected_repo_actions is None:
                self.assertNotIn("supported_repo_actions", payload)
            else:
                self.assertEqual(actual_repo_actions, expected_repo_actions)

            self.assertIn("## Canonical Source", wrapper_text)
            self.assertIn("## Backend Notes", wrapper_text)
            self.assertIn("## Deploy Target", wrapper_text)
            self.assertNotIn("## Execution Rules", wrapper_text)
            self.assertNotIn("## Output Contract", wrapper_text)

            self.assertIn(f"`{payload['manifest_path']}`", wrapper_text)
            self.assertIn(f"`{payload_path.relative_to(REPO_ROOT).as_posix()}`", wrapper_text)
            self.assertIn(f"`{payload['target_dir']}`", wrapper_text)
            self.assertIn(f"`{payload['target_entry_name']}`", wrapper_text)
            self.assertIn("`local`", wrapper_text)
            self.assertIn(f"`{payload['reference_distribution']}`", wrapper_text)
            for canonical_path in expected_canonical_paths:
                self.assertIn(f"`{canonical_path}`", wrapper_text)
                self.assertTrue((REPO_ROOT / canonical_path).is_file(), canonical_path)


if __name__ == "__main__":
    unittest.main()
