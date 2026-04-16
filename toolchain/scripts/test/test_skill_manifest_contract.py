from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_DIR = REPO_ROOT / "product" / "harness" / "manifests" / "agents" / "skills"
SCHEMA_PATH = (
    REPO_ROOT
    / "product"
    / "harness"
    / "manifests"
    / "schema"
    / "skill-manifest.v1.schema.json"
)

EXPECTED_FIRST_WAVE_ROUTES = {
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
        "supported_repo_actions": {"enter-worktrack", "hold-and-observe"},
    },
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class SkillManifestContractTest(unittest.TestCase):
    def test_first_wave_skill_manifests_follow_b1_contract(self) -> None:
        manifest_paths = sorted(MANIFEST_DIR.glob("*.json"))
        schema = load_json(SCHEMA_PATH)

        try:
            import jsonschema
        except ImportError as exc:
            self.fail(f"jsonschema is required to validate {SCHEMA_PATH}: {exc}")

        self.assertEqual(
            [path.stem for path in manifest_paths],
            sorted(EXPECTED_FIRST_WAVE_ROUTES),
        )

        for manifest_path in manifest_paths:
            payload = load_json(manifest_path)
            try:
                jsonschema.validate(instance=payload, schema=schema)
            except jsonschema.ValidationError as exc:
                self.fail(
                    f"{manifest_path.relative_to(REPO_ROOT)} does not satisfy "
                    f"{SCHEMA_PATH.relative_to(REPO_ROOT)}: {exc.message}"
                )

            skill_id = payload["skill_id"]
            canonical_dir = payload["canonical_dir"]
            target_dir = payload["target_dir"]
            entrypoint = payload["entrypoint"]
            included_paths = payload["included_paths"]
            first_wave_profile = payload["first_wave_profile"]
            first_wave_scope_kind = payload["first_wave_scope_kind"]

            self.assertEqual(payload["manifest_version"], "skill-manifest.v1")
            self.assertEqual(payload["backend"], "agents")
            self.assertEqual(first_wave_profile, "a3-first-wave")
            self.assertEqual(
                first_wave_scope_kind,
                EXPECTED_FIRST_WAVE_ROUTES[skill_id]["first_wave_scope_kind"],
            )

            expected_repo_actions = EXPECTED_FIRST_WAVE_ROUTES[skill_id].get("supported_repo_actions")
            actual_repo_actions = payload.get("supported_repo_actions")
            if expected_repo_actions is None:
                self.assertNotIn("supported_repo_actions", payload)
            else:
                self.assertEqual(set(actual_repo_actions), expected_repo_actions)

            self.assertEqual(Path(canonical_dir).name, skill_id)
            self.assertEqual(Path(target_dir).name, skill_id)
            self.assertIn(entrypoint, included_paths)

            all_relative_paths = [entrypoint, target_dir, *included_paths]
            for relative_path in all_relative_paths:
                parts = Path(relative_path).parts
                self.assertNotIn(".", parts)
                self.assertNotIn("..", parts)

            canonical_root = REPO_ROOT / str(canonical_dir)
            self.assertTrue(canonical_root.is_dir(), canonical_root)
            self.assertTrue((canonical_root / str(entrypoint)).is_file(), manifest_path)
            for included_path in included_paths:
                self.assertTrue((canonical_root / str(included_path)).is_file(), included_path)


if __name__ == "__main__":
    unittest.main()
