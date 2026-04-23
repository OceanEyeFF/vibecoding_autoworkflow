#!/usr/bin/env python3
"""Refresh a manual autoresearch contract with a fresh run_id."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import REPO_ROOT, slugify


DEFAULT_MODULUS = 100_003
RUN_ID_SUFFIX_PATTERN = r"-r\d+-m\d+$"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assign a fresh run_id to a manual autoresearch contract.")
    parser.add_argument("--contract", type=Path, required=True, help="Path to the manual contract JSON file.")
    parser.add_argument(
        "--modulus",
        type=int,
        default=DEFAULT_MODULUS,
        help="Positive modulus used for the lineage residue. Default: 100003.",
    )
    return parser.parse_args(argv)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object required: {path}")
    return payload


def derive_base_run_id(run_id: str) -> str:
    import re

    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id must be a non-empty string.")
    return re.sub(RUN_ID_SUFFIX_PATTERN, "", run_id.strip())


def state_dir_for_contract(contract_path: Path) -> Path:
    contract_path = contract_path.expanduser().resolve()
    try:
        relative = contract_path.relative_to(REPO_ROOT)
    except ValueError:
        return contract_path.parent / ".run-id-state"
    state_root = REPO_ROOT / ".autoworkflow" / "manual-runs" / ".run-id-state"
    try:
        suffix = relative.parent.relative_to(".autoworkflow/manual-runs")
    except ValueError:
        suffix = relative.parent
    return state_root / suffix


def state_path_for_contract(contract_path: Path, *, base_run_id: str) -> Path:
    return state_dir_for_contract(contract_path) / f"{slugify(base_run_id)}.json"


def seed_for_base_run_id(base_run_id: str, *, modulus: int) -> int:
    digest = hashlib.sha256(base_run_id.encode("utf-8")).hexdigest()
    return int(digest[:16], 16) % modulus


def build_fresh_run_id(base_run_id: str, *, serial: int, modulus: int, seed: int | None = None) -> tuple[str, int]:
    if serial <= 0:
        raise ValueError("serial must be a positive integer.")
    if modulus <= 1:
        raise ValueError("modulus must be greater than 1.")
    base_seed = seed_for_base_run_id(base_run_id, modulus=modulus) if seed is None else seed % modulus
    residue = (base_seed + serial) % modulus
    width = max(6, len(str(modulus - 1)))
    return f"{base_run_id}-r{serial:0{width}d}-m{residue:0{width}d}", residue


def refresh_contract_run_id(contract_path: Path, *, modulus: int = DEFAULT_MODULUS) -> dict[str, Any]:
    if modulus <= 1:
        raise ValueError("modulus must be greater than 1.")
    contract_path = contract_path.expanduser().resolve()
    payload = _read_json(contract_path)
    current_run_id = str(payload.get("run_id") or "")
    base_run_id = derive_base_run_id(current_run_id)
    state_path = state_path_for_contract(contract_path, base_run_id=base_run_id)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    seed = seed_for_base_run_id(base_run_id, modulus=modulus)
    serial = 1
    if state_path.is_file():
        state = _read_json(state_path)
        recorded_base = str(state.get("base_run_id") or "")
        recorded_modulus = int(state.get("modulus") or modulus)
        if recorded_base != base_run_id:
            raise ValueError(f"run_id state base mismatch: {recorded_base} != {base_run_id}")
        if recorded_modulus != modulus:
            raise ValueError(f"run_id state modulus mismatch: {recorded_modulus} != {modulus}")
        recorded_seed = int(state.get("seed") or seed)
        if recorded_seed != seed:
            raise ValueError(f"run_id state seed mismatch: {recorded_seed} != {seed}")
        serial = int(state.get("serial") or 0) + 1

    fresh_run_id, residue = build_fresh_run_id(base_run_id, serial=serial, modulus=modulus, seed=seed)
    payload["run_id"] = fresh_run_id
    contract_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    state_payload = {
        "base_run_id": base_run_id,
        "modulus": modulus,
        "seed": seed,
        "serial": serial,
        "last_residue": residue,
        "last_run_id": fresh_run_id,
        "updated_at": now_iso(),
    }
    state_path.write_text(json.dumps(state_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return {
        "contract_path": str(contract_path),
        "state_path": str(state_path),
        "base_run_id": base_run_id,
        "run_id": fresh_run_id,
        "serial": serial,
        "residue": residue,
        "modulus": modulus,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        result = refresh_contract_run_id(args.contract, modulus=args.modulus)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"contract: {result['contract_path']}")
    print(f"state: {result['state_path']}")
    print(f"base_run_id: {result['base_run_id']}")
    print(f"serial: {result['serial']}")
    print(f"modulus: {result['modulus']}")
    print(f"residue: {result['residue']}")
    print(f"run_id: {result['run_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
