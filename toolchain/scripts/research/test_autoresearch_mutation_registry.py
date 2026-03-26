from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from autoresearch_contract import load_contract
from autoresearch_contract import AutoresearchContract
from autoresearch_mutation_registry import (
    compute_contract_fingerprint,
    import_manual_mutation_as_registry_entry,
    load_mutation_registry,
    materialize_round_mutation,
)


def build_contract_payload(*, suite_name: str = "lane.yaml") -> dict[str, object]:
    return {
        "run_id": "p1-1-demo",
        "label": "P1.1 Demo",
        "objective": "Registry loading",
        "target_surface": "memory-side",
        "mutable_paths": ["product/memory-side/skills"],
        "frozen_paths": ["docs/knowledge"],
        "train_suites": [suite_name],
        "validation_suites": [suite_name],
        "acceptance_suites": [suite_name],
        "primary_metrics": ["avg_total_score"],
        "guard_metrics": ["parse_error_rate", "timeout_rate"],
        "qualitative_veto_checks": [],
        "max_rounds": 3,
        "max_candidate_attempts_per_round": 1,
        "timeout_policy": {"seconds": 120},
        "promotion_policy": {"mode": "script"},
    }


def build_entry_payload(*, mutation_key: str = "text_rephrase:demo:intro-tighten-v1") -> dict[str, object]:
    return {
        "mutation_key": mutation_key,
        "kind": "text_rephrase",
        "status": "active",
        "target_paths": ["product/memory-side/skills"],
        "allowed_actions": ["edit"],
        "instruction_seed": "Tighten wording.\nKeep boundaries explicit.\n",
        "expected_effect": {
            "hypothesis": "Improve clarity without regressions.",
            "primary_metrics": ["avg_total_score"],
            "guard_metrics": ["parse_error_rate", "timeout_rate"],
        },
        "guardrails": {
            "require_non_empty_diff": True,
            "max_files_touched": 1,
            "extra_frozen_paths": [],
        },
        "origin": {
            "type": "manual_seed",
            "ref": "test",
        },
        "attempts": 0,
        "last_selected_round": None,
        "last_decision": None,
        "fingerprint_basis": {},
        "fingerprint": "sha256:placeholder",
    }


class AutoresearchMutationRegistryTest(unittest.TestCase):
    def _write_contract(self, root: Path) -> Path:
        (root / "lane.yaml").write_text("version: 1\nruns: []\n", encoding="utf-8")
        contract_path = root / "contract.json"
        contract_path.write_text(json.dumps(build_contract_payload()), encoding="utf-8")
        return contract_path

    def _load_contract(self, contract_path: Path, *, repo_root: Path) -> object:
        return load_contract(contract_path, repo_root=repo_root)

    def test_load_mutation_registry_happy_path_and_fingerprint_stability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = self._write_contract(root)
            contract = load_contract(contract_path, repo_root=root)
            contract_fp = compute_contract_fingerprint(contract)

            entry = build_entry_payload()
            entry["target_paths"] = [
                "product/memory-side/skills/b.md",
                "product/memory-side/skills/a.md",
            ]
            # Remove placeholder computed fields and let loader fill them.
            entry.pop("fingerprint_basis")
            entry.pop("fingerprint")
            registry_payload = {
                "run_id": contract.run_id,
                "registry_version": 1,
                "contract_fingerprint": contract_fp,
                "entries": [entry],
            }
            registry_path = root / "mutation-registry.json"
            registry_path.write_text(json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

            loaded = load_mutation_registry(registry_path, contract=contract, repo_root=root)
            self.assertEqual(loaded.run_id, contract.run_id)
            self.assertEqual(loaded.contract_fingerprint, contract_fp)
            self.assertEqual(len(loaded.entries), 1)
            fp1 = loaded.entries[0]["fingerprint"]

            # Reorder some input keys; fingerprint should remain stable.
            reordered_entry = {
                "allowed_actions": ["edit"],
                "status": "active",
                "kind": "text_rephrase",
                "mutation_key": "text_rephrase:demo:intro-tighten-v1",
                "instruction_seed": "Tighten wording.\nKeep boundaries explicit.\n",
                "target_paths": [
                    "product/memory-side/skills/a.md",
                    "product/memory-side/skills/b.md",
                ],
                "expected_effect": {
                    "guard_metrics": ["timeout_rate", "parse_error_rate"],
                    "primary_metrics": ["avg_total_score"],
                    "hypothesis": "Improve clarity without regressions.",
                },
                "guardrails": {
                    "extra_frozen_paths": [],
                    "max_files_touched": 1,
                    "require_non_empty_diff": True,
                },
                "origin": {"ref": "test", "type": "manual_seed"},
                "attempts": 0,
                "last_selected_round": None,
                "last_decision": None,
            }
            registry_payload2 = {
                "registry_version": 1,
                "entries": [reordered_entry],
                "contract_fingerprint": contract_fp,
                "run_id": contract.run_id,
            }
            registry_path2 = root / "mutation-registry-2.json"
            registry_path2.write_text(
                json.dumps(registry_payload2, ensure_ascii=True, indent=2) + "\n",
                encoding="utf-8",
            )
            loaded2 = load_mutation_registry(registry_path2, contract=contract, repo_root=root)
            fp2 = loaded2.entries[0]["fingerprint"]
            self.assertEqual(fp1, fp2)

    def test_load_mutation_registry_rejects_run_id_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = self._write_contract(root)
            contract = load_contract(contract_path, repo_root=root)
            entry = build_entry_payload()
            entry.pop("fingerprint_basis")
            entry.pop("fingerprint")
            registry_payload = {
                "run_id": "other",
                "registry_version": 1,
                "contract_fingerprint": compute_contract_fingerprint(contract),
                "entries": [entry],
            }
            registry_path = root / "mutation-registry.json"
            registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "run_id does not match"):
                load_mutation_registry(registry_path, contract=contract, repo_root=root)

    def test_load_mutation_registry_rejects_contract_fingerprint_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = self._write_contract(root)
            contract = load_contract(contract_path, repo_root=root)
            entry = build_entry_payload()
            entry.pop("fingerprint_basis")
            entry.pop("fingerprint")
            registry_payload = {
                "run_id": contract.run_id,
                "registry_version": 1,
                "contract_fingerprint": "sha256:deadbeef",
                "entries": [entry],
            }
            registry_path = root / "mutation-registry.json"
            registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "contract_fingerprint"):
                load_mutation_registry(registry_path, contract=contract, repo_root=root)

    def test_load_mutation_registry_rejects_duplicate_mutation_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = self._write_contract(root)
            contract = load_contract(contract_path, repo_root=root)
            contract_fp = compute_contract_fingerprint(contract)
            entry = build_entry_payload()
            entry.pop("fingerprint_basis")
            entry.pop("fingerprint")
            registry_payload = {
                "run_id": contract.run_id,
                "registry_version": 1,
                "contract_fingerprint": contract_fp,
                "entries": [entry, dict(entry)],
            }
            registry_path = root / "mutation-registry.json"
            registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Duplicate mutation_key"):
                load_mutation_registry(registry_path, contract=contract, repo_root=root)

    def test_load_mutation_registry_rejects_duplicate_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = self._write_contract(root)
            contract = load_contract(contract_path, repo_root=root)
            contract_fp = compute_contract_fingerprint(contract)
            entry1 = build_entry_payload(mutation_key="text_rephrase:demo:a")
            entry2 = build_entry_payload(mutation_key="text_rephrase:demo:b")
            for entry in (entry1, entry2):
                entry.pop("fingerprint_basis")
                entry.pop("fingerprint")
            registry_payload = {
                "run_id": contract.run_id,
                "registry_version": 1,
                "contract_fingerprint": contract_fp,
                "entries": [entry1, entry2],
            }
            registry_path = root / "mutation-registry.json"
            registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Duplicate mutation fingerprint"):
                load_mutation_registry(registry_path, contract=contract, repo_root=root)

    def test_load_mutation_registry_rejects_unsupported_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = self._write_contract(root)
            contract = load_contract(contract_path, repo_root=root)
            contract_fp = compute_contract_fingerprint(contract)
            entry = build_entry_payload()
            entry["kind"] = "file_create"
            entry.pop("fingerprint_basis")
            entry.pop("fingerprint")
            registry_payload = {
                "run_id": contract.run_id,
                "registry_version": 1,
                "contract_fingerprint": contract_fp,
                "entries": [entry],
            }
            registry_path = root / "mutation-registry.json"
            registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Unsupported mutation kind"):
                load_mutation_registry(registry_path, contract=contract, repo_root=root)

    def test_load_mutation_registry_rejects_unsupported_allowed_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = self._write_contract(root)
            contract = load_contract(contract_path, repo_root=root)
            contract_fp = compute_contract_fingerprint(contract)
            entry = build_entry_payload()
            entry["allowed_actions"] = ["edit", "create"]
            entry.pop("fingerprint_basis")
            entry.pop("fingerprint")
            registry_payload = {
                "run_id": contract.run_id,
                "registry_version": 1,
                "contract_fingerprint": contract_fp,
                "entries": [entry],
            }
            registry_path = root / "mutation-registry.json"
            registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "allowed_actions"):
                load_mutation_registry(registry_path, contract=contract, repo_root=root)

    def test_load_mutation_registry_rejects_target_paths_outside_contract_mutable_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = self._write_contract(root)
            contract = load_contract(contract_path, repo_root=root)
            contract_fp = compute_contract_fingerprint(contract)
            entry = build_entry_payload()
            entry["target_paths"] = ["README.md"]
            entry.pop("fingerprint_basis")
            entry.pop("fingerprint")
            registry_payload = {
                "run_id": contract.run_id,
                "registry_version": 1,
                "contract_fingerprint": contract_fp,
                "entries": [entry],
            }
            registry_path = root / "mutation-registry.json"
            registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "must stay within contract.mutable_paths"):
                load_mutation_registry(registry_path, contract=contract, repo_root=root)

    def test_load_mutation_registry_rejects_target_paths_overlapping_frozen_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = self._write_contract(root)
            payload = build_contract_payload()
            # White-box contract fixture: overlap between mutable and frozen is normally rejected by load_contract(),
            # but the registry must still defend against frozen overlaps at the entry boundary.
            payload["frozen_paths"] = ["product/memory-side/skills/skill.md"]
            contract = AutoresearchContract(
                source_path=contract_path,
                payload=payload,
                run_id=str(payload["run_id"]),
                train_suites=[str(item) for item in payload["train_suites"]],  # type: ignore[index]
                validation_suites=[str(item) for item in payload["validation_suites"]],  # type: ignore[index]
                acceptance_suites=[str(item) for item in payload["acceptance_suites"]],  # type: ignore[index]
                mutable_paths=[str(item) for item in payload["mutable_paths"]],  # type: ignore[index]
                frozen_paths=[str(item) for item in payload["frozen_paths"]],  # type: ignore[index]
            )
            contract_fp = compute_contract_fingerprint(contract)
            entry = build_entry_payload()
            entry.pop("fingerprint_basis")
            entry.pop("fingerprint")
            registry_payload = {
                "run_id": contract.run_id,
                "registry_version": 1,
                "contract_fingerprint": contract_fp,
                "entries": [entry],
            }
            registry_path = root / "mutation-registry.json"
            registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "must not overlap contract.frozen_paths"):
                load_mutation_registry(registry_path, contract=contract, repo_root=root)

    def test_load_mutation_registry_rejects_unknown_primary_metric(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = self._write_contract(root)
            contract = load_contract(contract_path, repo_root=root)
            contract_fp = compute_contract_fingerprint(contract)
            entry = build_entry_payload()
            entry["expected_effect"]["primary_metrics"] = ["unknown_metric"]  # type: ignore[index]
            entry.pop("fingerprint_basis")
            entry.pop("fingerprint")
            registry_payload = {
                "run_id": contract.run_id,
                "registry_version": 1,
                "contract_fingerprint": contract_fp,
                "entries": [entry],
            }
            registry_path = root / "mutation-registry.json"
            registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "primary_metrics"):
                load_mutation_registry(registry_path, contract=contract, repo_root=root)

    def test_load_mutation_registry_rejects_unknown_guard_metric(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = self._write_contract(root)
            contract = load_contract(contract_path, repo_root=root)
            contract_fp = compute_contract_fingerprint(contract)
            entry = build_entry_payload()
            entry["expected_effect"]["guard_metrics"] = ["parse_error_rate", "not_in_contract"]  # type: ignore[index]
            entry.pop("fingerprint_basis")
            entry.pop("fingerprint")
            registry_payload = {
                "run_id": contract.run_id,
                "registry_version": 1,
                "contract_fingerprint": contract_fp,
                "entries": [entry],
            }
            registry_path = root / "mutation-registry.json"
            registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "subset of contract.guard_metrics"):
                load_mutation_registry(registry_path, contract=contract, repo_root=root)

    def test_load_mutation_registry_rejects_extra_frozen_paths_outside_target_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = self._write_contract(root)
            contract = load_contract(contract_path, repo_root=root)
            contract_fp = compute_contract_fingerprint(contract)
            entry = build_entry_payload()
            entry["guardrails"]["extra_frozen_paths"] = ["product/memory-side"]  # type: ignore[index]
            entry.pop("fingerprint_basis")
            entry.pop("fingerprint")
            registry_payload = {
                "run_id": contract.run_id,
                "registry_version": 1,
                "contract_fingerprint": contract_fp,
                "entries": [entry],
            }
            registry_path = root / "mutation-registry.json"
            registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "extra_frozen_paths must be within target_paths"):
                load_mutation_registry(registry_path, contract=contract, repo_root=root)

    def test_load_mutation_registry_rejects_fingerprint_basis_or_fingerprint_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = self._write_contract(root)
            contract = load_contract(contract_path, repo_root=root)
            contract_fp = compute_contract_fingerprint(contract)
            entry = build_entry_payload()
            entry["fingerprint_basis"] = {"kind": "text_rephrase"}
            entry["fingerprint"] = "sha256:deadbeef"
            registry_payload = {
                "run_id": contract.run_id,
                "registry_version": 1,
                "contract_fingerprint": contract_fp,
                "entries": [entry],
            }
            registry_path = root / "mutation-registry.json"
            registry_path.write_text(json.dumps(registry_payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "fingerprint_basis"):
                load_mutation_registry(registry_path, contract=contract, repo_root=root)

    def test_import_manual_mutation_as_registry_entry_supports_legacy_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = self._write_contract(root)
            contract = load_contract(contract_path, repo_root=root)
            entry = import_manual_mutation_as_registry_entry(
                {
                    "mutation_id": "mut-001",
                    "kind": "text_rephrase",
                    "target_paths": ["product/memory-side/skills"],
                    "allowed_actions": ["edit"],
                    "instruction": "Tighten wording.",
                    "expected_effect": "Improve train score without validation regression.",
                },
                contract=contract,
                repo_root=root,
                origin_ref="test",
            )
            self.assertEqual(entry["mutation_key"], "imported:text_rephrase:mut-001")
            self.assertEqual(entry["expected_effect"]["primary_metrics"], ["avg_total_score"])
            self.assertEqual(entry["expected_effect"]["guard_metrics"], ["parse_error_rate", "timeout_rate"])

    def test_materialize_round_mutation_builds_attempt_scoped_round_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = self._write_contract(root)
            contract = load_contract(contract_path, repo_root=root)
            contract_fp = compute_contract_fingerprint(contract)
            entry = build_entry_payload()
            entry.pop("fingerprint_basis")
            entry.pop("fingerprint")
            registry_payload = {
                "run_id": contract.run_id,
                "registry_version": 1,
                "contract_fingerprint": contract_fp,
                "entries": [entry],
            }
            registry_path = root / "mutation-registry.json"
            registry_path.write_text(json.dumps(registry_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
            registry = load_mutation_registry(registry_path, contract=contract, repo_root=root)

            round_payload = materialize_round_mutation(entry=registry.entries[0], round_number=2, attempt=3)
            self.assertEqual(round_payload["round"], 2)
            self.assertEqual(round_payload["attempt"], 3)
            self.assertEqual(round_payload["mutation_id"], "text_rephrase:demo:intro-tighten-v1#a003")
            self.assertEqual(round_payload["instruction"], "Tighten wording.\nKeep boundaries explicit.")


if __name__ == "__main__":
    unittest.main()
