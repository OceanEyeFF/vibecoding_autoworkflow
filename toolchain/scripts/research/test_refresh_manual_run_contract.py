from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import refresh_manual_run_contract


class RefreshManualRunContractTest(unittest.TestCase):
    def test_derive_base_run_id_strips_generated_suffix(self) -> None:
        self.assertEqual(
            refresh_manual_run_contract.derive_base_run_id("manual-cr-typer-claude-r000123-m045678"),
            "manual-cr-typer-claude",
        )
        self.assertEqual(
            refresh_manual_run_contract.derive_base_run_id("manual-cr-typer-claude"),
            "manual-cr-typer-claude",
        )

    def test_refresh_contract_run_id_creates_and_advances_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manual_root = root / ".autoworkflow" / "manual-runs" / "minimal"
            manual_root.mkdir(parents=True, exist_ok=True)
            contract_path = manual_root / "contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "run_id": "manual-cr-typer-claude",
                        "label": "demo",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            with mock.patch.object(refresh_manual_run_contract, "REPO_ROOT", root):
                first = refresh_manual_run_contract.refresh_contract_run_id(contract_path)
                second = refresh_manual_run_contract.refresh_contract_run_id(contract_path)

            self.assertEqual(first["base_run_id"], "manual-cr-typer-claude")
            self.assertEqual(first["serial"], 1)
            self.assertEqual(second["serial"], 2)
            self.assertNotEqual(first["run_id"], second["run_id"])
            self.assertTrue(str(first["run_id"]).startswith("manual-cr-typer-claude-r000001-m"))
            self.assertTrue(str(second["run_id"]).startswith("manual-cr-typer-claude-r000002-m"))

            saved_contract = json.loads(contract_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_contract["run_id"], second["run_id"])

            state_path = Path(second["state_path"])
            state_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state_payload["serial"], 2)
            self.assertEqual(state_payload["last_run_id"], second["run_id"])
            self.assertEqual(state_payload["modulus"], refresh_manual_run_contract.DEFAULT_MODULUS)

    def test_refresh_contract_run_id_supports_repo_local_contract_outside_manual_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract_path = root / "contracts" / "manual.json"
            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_text(
                json.dumps(
                    {
                        "run_id": "manual-cr-typer-claude",
                        "label": "demo",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            with mock.patch.object(refresh_manual_run_contract, "REPO_ROOT", root):
                result = refresh_manual_run_contract.refresh_contract_run_id(contract_path)

            state_path = Path(result["state_path"])
            self.assertEqual(
                state_path,
                root / ".autoworkflow" / "manual-runs" / ".run-id-state" / "contracts" / "manual-cr-typer-claude.json",
            )
            self.assertTrue(state_path.is_file())

    def test_build_fresh_run_id_is_seeded_by_base(self) -> None:
        run_id_a, residue_a = refresh_manual_run_contract.build_fresh_run_id(
            "manual-cr-typer-claude",
            serial=3,
            modulus=refresh_manual_run_contract.DEFAULT_MODULUS,
        )
        run_id_b, residue_b = refresh_manual_run_contract.build_fresh_run_id(
            "manual-cr-typer-claude",
            serial=3,
            modulus=refresh_manual_run_contract.DEFAULT_MODULUS,
        )
        self.assertEqual(run_id_a, run_id_b)
        self.assertEqual(residue_a, residue_b)


if __name__ == "__main__":
    unittest.main()
