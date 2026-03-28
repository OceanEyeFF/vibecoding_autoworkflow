#!/usr/bin/env python3
"""Helpers for autoresearch P1.1 mutation registry loading and validation.

This module is intentionally limited to:
- registry schema validation
- contract boundary validation
- canonicalization + deterministic fingerprinting

It does NOT implement any scheduler/selector logic, round materialization, or state transitions.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from autoresearch_contract import AutoresearchContract, normalize_repo_path, paths_overlap, resolve_p2_contract_target
from common import REPO_ROOT, SCHEMAS_ROOT


AUTORESEARCH_MUTATION_REGISTRY_SCHEMA_PATH = SCHEMAS_ROOT / "autoresearch-mutation-registry.schema.json"

SUPPORTED_MUTATION_KINDS = frozenset(
    {
        "text_rephrase",
        "constraint_tighten",
        "instruction_reorder",
        "example_trim",
    }
)
SUPPORTED_ALLOWED_ACTIONS = frozenset({"edit"})
SUPPORTED_STATUSES = frozenset({"active", "disabled", "exhausted"})
SUPPORTED_LAST_DECISIONS = frozenset({"keep", "discard"})

# Scoreboard lane metrics that are stable and safe to reference in P1.1.
SUPPORTED_SCOREBOARD_METRICS = frozenset(
    {
        "avg_total_score",
        "pass_rate",
        "timeout_rate",
        "parse_error_rate",
    }
)


@dataclass(frozen=True)
class AutoresearchMutationRegistry:
    source_path: Path
    payload: dict[str, Any]
    run_id: str
    registry_version: str | int
    contract_fingerprint: str
    entries: list[dict[str, Any]]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Mutation registry must be an object: {path}")
    return payload


def _require_non_empty_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Registry field '{field}' must be a non-empty string.")
    return value.strip()


def _require_non_empty_string_list(payload: dict[str, Any], field: str) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list) or not value:
        raise ValueError(f"Registry field '{field}' must be a non-empty array.")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Registry field '{field}' must contain only non-empty strings.")
        normalized.append(item.strip())
    return normalized


def _stable_json_dumps(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_prefixed(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _sha256_file_prefixed(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def supported_mutation_kinds() -> frozenset[str]:
    return SUPPORTED_MUTATION_KINDS


def validate_mutation_registry_payload(payload: dict[str, Any]) -> None:
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError("jsonschema is required to validate autoresearch mutation registries.") from exc

    schema = json.loads(AUTORESEARCH_MUTATION_REGISTRY_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=payload, schema=schema)


def compute_contract_fingerprint(contract: AutoresearchContract) -> str:
    # The contract payload is already the canonical authority; keep list ordering meaningful.
    return _sha256_prefixed(_stable_json_dumps(contract.payload))


def _normalize_text_seed(value: str) -> str:
    # Preserve line structure while removing formatting-only drift.
    lines = [line.rstrip() for line in value.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    text = "\n".join(lines).strip()
    if not text:
        raise ValueError("Registry field 'instruction_seed' must be a non-empty string.")
    return text


def _normalize_paths(values: list[str], *, repo_root: Path) -> list[PurePosixPath]:
    normalized = [normalize_repo_path(value, repo_root) for value in values]
    return sorted(set(normalized), key=lambda item: item.as_posix())


def _posix_is_under(base: PurePosixPath, target: PurePosixPath) -> bool:
    if base == target:
        return True
    base_parts = base.parts
    target_parts = target.parts
    return base_parts == target_parts[: len(base_parts)]


def _validate_bookkeeping_state(
    *,
    entry: dict[str, Any],
    max_attempts: int,
) -> None:
    status = str(entry.get("status") or "").strip().lower()
    attempts = int(entry.get("attempts") or 0)
    last_selected_round = entry.get("last_selected_round")
    last_decision = entry.get("last_decision")

    if attempts > max_attempts:
        raise ValueError(
            "Registry entry attempts must not exceed contract.max_candidate_attempts_per_round: "
            f"{entry.get('mutation_key')}"
        )
    if last_selected_round is not None and attempts <= 0:
        raise ValueError(
            "Registry entry last_selected_round requires attempts > 0: "
            f"{entry.get('mutation_key')}"
        )
    if last_decision is not None and last_selected_round is None:
        raise ValueError(
            "Registry entry last_decision requires last_selected_round: "
            f"{entry.get('mutation_key')}"
        )
    if status == "exhausted":
        if attempts < max_attempts:
            raise ValueError(
                "Registry entry exhausted status requires attempts to reach the configured max: "
                f"{entry.get('mutation_key')}"
            )
        if last_decision is None:
            raise ValueError(
                "Registry entry exhausted status requires a recorded last_decision: "
                f"{entry.get('mutation_key')}"
            )
    if status == "active" and attempts >= max_attempts and last_decision is not None:
        raise ValueError(
            "Registry entry with a recorded last_decision must not remain active after exhausting attempts: "
            f"{entry.get('mutation_key')}"
        )


def build_mutation_fingerprint_basis(entry_payload: dict[str, Any]) -> dict[str, Any]:
    guardrails = entry_payload.get("guardrails") or {}
    if not isinstance(guardrails, dict):
        raise ValueError("Registry entry field 'guardrails' must be an object.")
    basis = {
        "kind": str(entry_payload.get("kind") or ""),
        "target_paths": list(entry_payload.get("target_paths") or []),
        "allowed_actions": list(entry_payload.get("allowed_actions") or []),
        "instruction_seed": str(entry_payload.get("instruction_seed") or ""),
        "guardrails": {
            "require_non_empty_diff": bool(guardrails.get("require_non_empty_diff")),
            "max_files_touched": int(guardrails.get("max_files_touched") or 0),
            "extra_frozen_paths": list(guardrails.get("extra_frozen_paths") or []),
        },
    }
    return basis


def compute_mutation_fingerprint(entry_payload: dict[str, Any]) -> str:
    basis = build_mutation_fingerprint_basis(entry_payload)
    return _sha256_prefixed(_stable_json_dumps(basis))


def canonicalize_mutation_entry(
    entry_payload: dict[str, Any],
    *,
    repo_root: Path,
    contract: AutoresearchContract,
) -> dict[str, Any]:
    if not isinstance(entry_payload, dict):
        raise ValueError("Registry entries must be JSON objects.")

    mutation_key = _require_non_empty_string(entry_payload, "mutation_key")
    kind = _require_non_empty_string(entry_payload, "kind").lower()
    status = _require_non_empty_string(entry_payload, "status").lower()
    instruction_seed = _normalize_text_seed(_require_non_empty_string(entry_payload, "instruction_seed"))
    allowed_actions = [value.lower() for value in _require_non_empty_string_list(entry_payload, "allowed_actions")]
    target_paths = _normalize_paths(_require_non_empty_string_list(entry_payload, "target_paths"), repo_root=repo_root)

    if kind not in SUPPORTED_MUTATION_KINDS:
        raise ValueError(f"Unsupported mutation kind: {kind}")
    if status not in SUPPORTED_STATUSES:
        raise ValueError(f"Unsupported registry entry status: {status}")
    if sorted(set(allowed_actions)) != ["edit"]:
        raise ValueError("Registry entry allowed_actions must be exactly ['edit'] in P1.1.")

    expected_effect = entry_payload.get("expected_effect")
    if not isinstance(expected_effect, dict):
        raise ValueError("Registry entry expected_effect must be an object.")
    hypothesis = _require_non_empty_string(expected_effect, "hypothesis")
    primary_metrics = [str(value).strip() for value in (expected_effect.get("primary_metrics") or [])]
    primary_metrics = [value for value in primary_metrics if value]
    if not primary_metrics:
        raise ValueError("Registry entry expected_effect.primary_metrics must be a non-empty array.")
    guard_metrics = [str(value).strip() for value in (expected_effect.get("guard_metrics") or [])]
    guard_metrics = [value for value in guard_metrics if value]
    unknown_primary = sorted(set(primary_metrics) - SUPPORTED_SCOREBOARD_METRICS)
    if unknown_primary:
        raise ValueError(
            "Registry entry expected_effect.primary_metrics contain unsupported values: "
            + ", ".join(unknown_primary)
        )
    contract_guard = [str(value) for value in (contract.payload.get("guard_metrics") or [])]
    unknown_guard = sorted(set(guard_metrics) - set(contract_guard))
    if unknown_guard:
        raise ValueError(
            "Registry entry expected_effect.guard_metrics must be a subset of contract.guard_metrics: "
            + ", ".join(unknown_guard)
        )

    guardrails = entry_payload.get("guardrails")
    if not isinstance(guardrails, dict):
        raise ValueError("Registry entry guardrails must be an object.")
    require_non_empty_diff = bool(guardrails.get("require_non_empty_diff"))
    max_files_touched = guardrails.get("max_files_touched")
    if not isinstance(max_files_touched, int) or max_files_touched <= 0:
        raise ValueError("Registry entry guardrails.max_files_touched must be a positive integer.")
    extra_frozen_paths_raw = guardrails.get("extra_frozen_paths") or []
    if not isinstance(extra_frozen_paths_raw, list):
        raise ValueError("Registry entry guardrails.extra_frozen_paths must be an array.")
    extra_frozen_paths = _normalize_paths(
        [str(value).strip() for value in extra_frozen_paths_raw if str(value).strip()],
        repo_root=repo_root,
    )

    contract_mutable = _normalize_paths([str(value) for value in contract.mutable_paths], repo_root=repo_root)
    contract_frozen = _normalize_paths([str(value) for value in contract.frozen_paths], repo_root=repo_root)
    p2_target = resolve_p2_contract_target(contract, repo_root=repo_root)
    if p2_target is not None:
        _target_task, target_prompt_path = p2_target
        if target_paths != [target_prompt_path]:
            raise ValueError(
                "P2 registry entry target_paths must be exactly [contract.target_prompt_path]: "
                f"{target_prompt_path.as_posix()}"
            )
    for target_path in target_paths:
        if not any(_posix_is_under(base=mutable_path, target=target_path) for mutable_path in contract_mutable):
            raise ValueError(
                "Registry entry target_paths must stay within contract.mutable_paths: "
                f"{target_path.as_posix()}"
            )
        if any(paths_overlap(target_path, frozen_path) for frozen_path in contract_frozen):
            raise ValueError(
                "Registry entry target_paths must not overlap contract.frozen_paths: "
                f"{target_path.as_posix()}"
            )

    for extra_frozen in extra_frozen_paths:
        if not any(_posix_is_under(base=target_path, target=extra_frozen) for target_path in target_paths):
            raise ValueError(
                "Registry entry guardrails.extra_frozen_paths must be within target_paths: "
                f"{extra_frozen.as_posix()}"
            )

    origin = entry_payload.get("origin")
    if not isinstance(origin, dict):
        raise ValueError("Registry entry origin must be an object.")
    origin_type = _require_non_empty_string(origin, "type")
    origin_ref = _require_non_empty_string(origin, "ref")

    attempts = entry_payload.get("attempts", 0)
    if not isinstance(attempts, int) or attempts < 0:
        raise ValueError("Registry entry attempts must be a non-negative integer.")
    last_selected_round = entry_payload.get("last_selected_round")
    if last_selected_round is not None and (not isinstance(last_selected_round, int) or last_selected_round < 1):
        raise ValueError("Registry entry last_selected_round must be null or a positive integer.")
    last_decision = entry_payload.get("last_decision")
    if last_decision is not None:
        if not isinstance(last_decision, str) or last_decision not in SUPPORTED_LAST_DECISIONS:
            raise ValueError("Registry entry last_decision must be null, 'keep', or 'discard'.")

    canonical_entry: dict[str, Any] = {
        "mutation_key": mutation_key,
        "kind": kind,
        "status": status,
        "target_paths": [path.as_posix() for path in target_paths],
        "allowed_actions": ["edit"],
        "instruction_seed": instruction_seed,
        "expected_effect": {
            "hypothesis": hypothesis,
            "primary_metrics": sorted(set(primary_metrics)),
            "guard_metrics": sorted(set(guard_metrics)),
        },
        "guardrails": {
            "require_non_empty_diff": require_non_empty_diff,
            "max_files_touched": int(max_files_touched),
            "extra_frozen_paths": [path.as_posix() for path in extra_frozen_paths],
        },
        "origin": {
            "type": origin_type,
            "ref": origin_ref,
        },
        "attempts": int(attempts),
        "last_selected_round": last_selected_round,
        "last_decision": last_decision,
    }

    fingerprint_basis = build_mutation_fingerprint_basis(canonical_entry)
    fingerprint = compute_mutation_fingerprint(canonical_entry)

    provided_basis = entry_payload.get("fingerprint_basis")
    if provided_basis is not None and provided_basis != fingerprint_basis:
        raise ValueError(f"Registry entry fingerprint_basis does not match canonical value: {mutation_key}")

    provided_fingerprint = entry_payload.get("fingerprint")
    if provided_fingerprint is not None and str(provided_fingerprint) != fingerprint:
        raise ValueError(f"Registry entry fingerprint does not match canonical value: {mutation_key}")

    canonical_entry["fingerprint_basis"] = fingerprint_basis
    canonical_entry["fingerprint"] = fingerprint
    return canonical_entry


def materialize_round_mutation(
    *,
    entry: dict[str, Any],
    round_number: int,
    attempt: int,
) -> dict[str, Any]:
    """Materialize a round-local mutation.json payload from a registry entry."""
    if not isinstance(round_number, int) or round_number <= 0:
        raise ValueError("round_number must be a positive integer.")
    if not isinstance(attempt, int) or attempt <= 0:
        raise ValueError("attempt must be a positive integer.")
    mutation_key = str(entry.get("mutation_key") or "").strip()
    if not mutation_key:
        raise ValueError("Registry entry missing mutation_key.")
    fingerprint = str(entry.get("fingerprint") or "").strip()
    if not fingerprint:
        raise ValueError("Registry entry missing fingerprint.")
    mutation_id = f"{mutation_key}#a{attempt:03d}"
    return {
        "round": round_number,
        "mutation_id": mutation_id,
        "mutation_key": mutation_key,
        "attempt": attempt,
        "fingerprint": fingerprint,
        "kind": str(entry.get("kind") or ""),
        "target_paths": list(entry.get("target_paths") or []),
        "allowed_actions": list(entry.get("allowed_actions") or []),
        # Round-local runtime fields
        "instruction": str(entry.get("instruction_seed") or ""),
        "expected_effect": dict(entry.get("expected_effect") or {}),
        "guardrails": dict(entry.get("guardrails") or {}),
    }


def load_mutation_registry(
    path: Path,
    *,
    contract: AutoresearchContract,
    repo_root: Path = REPO_ROOT,
) -> AutoresearchMutationRegistry:
    source = path.expanduser().resolve()
    payload = _load_json(source)
    validate_mutation_registry_payload(payload)

    run_id = _require_non_empty_string(payload, "run_id")
    if run_id != contract.run_id:
        raise ValueError(f"Registry run_id does not match contract.run_id: {run_id} vs {contract.run_id}")

    registry_version = payload.get("registry_version")
    if not isinstance(registry_version, (int, str)) or (isinstance(registry_version, str) and not registry_version.strip()):
        raise ValueError("Registry field 'registry_version' must be a non-empty string or a positive integer.")
    if isinstance(registry_version, str):
        registry_version = registry_version.strip()

    computed_contract_fp = compute_contract_fingerprint(contract)
    provided_contract_fp = payload.get("contract_fingerprint")
    if provided_contract_fp is not None and str(provided_contract_fp) != computed_contract_fp:
        raise ValueError("Registry contract_fingerprint does not match the provided contract.")

    entries_raw = payload.get("entries")
    if not isinstance(entries_raw, list) or not entries_raw:
        raise ValueError("Registry field 'entries' must be a non-empty array.")
    max_attempts_raw = contract.payload.get("max_candidate_attempts_per_round")
    if isinstance(max_attempts_raw, bool) or not isinstance(max_attempts_raw, int) or max_attempts_raw <= 0:
        raise ValueError("contract.payload.max_candidate_attempts_per_round must be a positive integer.")

    canonical_entries: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    seen_fingerprints: set[str] = set()
    for raw_entry in entries_raw:
        entry = canonicalize_mutation_entry(
            raw_entry,
            repo_root=repo_root,
            contract=contract,
        )
        _validate_bookkeeping_state(entry=entry, max_attempts=max_attempts_raw)
        key = str(entry["mutation_key"])
        if key in seen_keys:
            raise ValueError(f"Duplicate mutation_key in registry: {key}")
        seen_keys.add(key)
        fp = str(entry["fingerprint"])
        if fp in seen_fingerprints:
            raise ValueError(f"Duplicate mutation fingerprint in registry: {fp}")
        seen_fingerprints.add(fp)
        canonical_entries.append(entry)

    canonical_payload: dict[str, Any] = {
        "run_id": contract.run_id,
        "registry_version": registry_version,
        "contract_fingerprint": computed_contract_fp,
        "entries": canonical_entries,
    }

    validate_mutation_registry_payload(canonical_payload)
    return AutoresearchMutationRegistry(
        source_path=source,
        payload=canonical_payload,
        run_id=str(canonical_payload["run_id"]),
        registry_version=canonical_payload["registry_version"],
        contract_fingerprint=str(canonical_payload["contract_fingerprint"]),
        entries=list(canonical_payload["entries"]),
    )


def find_registry_entry(registry: AutoresearchMutationRegistry, mutation_key: str) -> dict[str, Any]:
    key = str(mutation_key or "").strip()
    if not key:
        raise ValueError("mutation_key must be a non-empty string.")
    for entry in registry.entries:
        if str(entry.get("mutation_key")) == key:
            return entry
    raise KeyError(f"mutation_key not found in registry: {key}")


def build_registry_payload(
    *,
    contract: AutoresearchContract,
    entries: list[dict[str, Any]],
    registry_version: int | str = 1,
) -> dict[str, Any]:
    payload = {
        "run_id": contract.run_id,
        "registry_version": registry_version,
        "contract_fingerprint": compute_contract_fingerprint(contract),
        "entries": entries,
    }
    validate_mutation_registry_payload(payload)
    return payload


def write_mutation_registry(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def upsert_registry_entry(
    *,
    registry: AutoresearchMutationRegistry,
    entry: dict[str, Any],
) -> AutoresearchMutationRegistry:
    """Insert or replace an entry by mutation_key, preserving unique fingerprint constraint."""
    mutation_key = str(entry.get("mutation_key") or "").strip()
    if not mutation_key:
        raise ValueError("Registry entry missing mutation_key.")
    fingerprint = str(entry.get("fingerprint") or "").strip()
    if not fingerprint:
        raise ValueError("Registry entry missing fingerprint.")

    entries = list(registry.entries)
    replaced = False
    for idx, existing in enumerate(entries):
        if str(existing.get("mutation_key")) == mutation_key:
            # Fingerprint must remain stable for a family key.
            if str(existing.get("fingerprint")) != fingerprint:
                raise ValueError(f"Registry entry fingerprint changed for mutation_key: {mutation_key}")
            entries[idx] = entry
            replaced = True
            break
    if not replaced:
        entries.append(entry)

    # Enforce uniqueness across the updated pool.
    seen_keys: set[str] = set()
    seen_fps: set[str] = set()
    for item in entries:
        key = str(item.get("mutation_key"))
        fp = str(item.get("fingerprint"))
        if key in seen_keys:
            raise ValueError(f"Duplicate mutation_key in registry: {key}")
        if fp in seen_fps:
            raise ValueError(f"Duplicate mutation fingerprint in registry: {fp}")
        seen_keys.add(key)
        seen_fps.add(fp)

    payload = dict(registry.payload)
    payload["entries"] = entries
    return AutoresearchMutationRegistry(
        source_path=registry.source_path,
        payload=payload,
        run_id=registry.run_id,
        registry_version=registry.registry_version,
        contract_fingerprint=registry.contract_fingerprint,
        entries=entries,
    )


def import_manual_mutation_as_registry_entry(
    payload: dict[str, Any],
    *,
    contract: AutoresearchContract,
    repo_root: Path = REPO_ROOT,
    origin_ref: str,
) -> dict[str, Any]:
    """Import a legacy/manual mutation spec into a registry entry seed and canonicalize it.

    Supported inputs:
    - legacy P0.3: instruction(str), expected_effect(str)
    - registry-like: instruction_seed(str), expected_effect(obj)
    """
    if not isinstance(payload, dict):
        raise ValueError("Manual mutation payload must be a JSON object.")

    kind = str(payload.get("kind") or "").strip().lower()
    if not kind:
        raise ValueError("Manual mutation payload missing 'kind'.")
    # Back-compat for P0.3 manual mutation kinds.
    kind = {
        "prompt_rewrite": "text_rephrase",
        "adapter_rephrase": "text_rephrase",
        "ordering_adjustment": "instruction_reorder",
    }.get(kind, kind)

    mutation_key = str(payload.get("mutation_key") or "").strip()
    if not mutation_key:
        mutation_id = str(payload.get("mutation_id") or "").strip() or "manual"
        mutation_key = f"imported:{kind}:{mutation_id}"

    target_paths = payload.get("target_paths") or []
    allowed_actions = payload.get("allowed_actions") or ["edit"]

    if "instruction_seed" in payload:
        instruction_seed = str(payload.get("instruction_seed") or "")
    else:
        instruction_seed = str(payload.get("instruction") or "")

    expected_effect = payload.get("expected_effect")
    if isinstance(expected_effect, str):
        expected_effect = {
            "hypothesis": expected_effect,
            "primary_metrics": list(contract.payload.get("primary_metrics") or []),
            "guard_metrics": list(contract.payload.get("guard_metrics") or []),
        }
    if not isinstance(expected_effect, dict):
        raise ValueError("Manual mutation payload expected_effect must be a string (legacy) or an object.")

    entry_seed: dict[str, Any] = {
        "mutation_key": mutation_key,
        "kind": kind,
        "status": "active",
        "target_paths": list(target_paths),
        "allowed_actions": list(allowed_actions),
        "instruction_seed": instruction_seed,
        "expected_effect": expected_effect,
        "guardrails": payload.get("guardrails")
        or {
            "require_non_empty_diff": True,
            "max_files_touched": 1,
            "extra_frozen_paths": [],
        },
        "origin": {
            "type": "manual_import",
            "ref": origin_ref,
        },
        "attempts": int(payload.get("attempts") or 0),
        "last_selected_round": payload.get("last_selected_round"),
        "last_decision": payload.get("last_decision"),
    }
    return canonicalize_mutation_entry(entry_seed, repo_root=repo_root, contract=contract)
