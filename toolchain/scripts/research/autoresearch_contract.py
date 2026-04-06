#!/usr/bin/env python3
"""Helpers for autoresearch P0.1 contract loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

from backend_runner import RetryPolicyConfig, build_retry_policy
from common import REPO_ROOT, SCHEMAS_ROOT, SUITES_ROOT


AUTORESEARCH_CONTRACT_SCHEMA_PATH = SCHEMAS_ROOT / "autoresearch-contract.schema.json"
AUTORESEARCH_BACKEND_IDS = ("claude", "codex", "opencode")
HISTORY_COLUMNS = [
    "round",
    "kind",
    "base_sha",
    "candidate_sha",
    "train_score",
    "validation_score",
    "train_parse_error_rate",
    "validation_parse_error_rate",
    "decision",
    "notes",
]

P2_TARGET_TASK_TO_RUNNER_TASK = {
    "context-routing-skill": "context-routing",
    "knowledge-base-skill": "knowledge-base",
    "task-contract-skill": "task-contract",
    "writeback-cleanup-skill": "writeback-cleanup",
}
P2_RUNNER_TASK_TO_TARGET_TASK = {value: key for key, value in P2_TARGET_TASK_TO_RUNNER_TASK.items()}
P2_TARGET_TASK_TO_PROMPT_PATH = {
    "context-routing-skill": "toolchain/scripts/research/tasks/context-routing-skill-prompt.md",
    "knowledge-base-skill": "toolchain/scripts/research/tasks/knowledge-base-skill-prompt.md",
    "task-contract-skill": "toolchain/scripts/research/tasks/task-contract-skill-prompt.md",
    "writeback-cleanup-skill": "toolchain/scripts/research/tasks/writeback-cleanup-skill-prompt.md",
}


@dataclass(frozen=True)
class AutoresearchContract:
    source_path: Path
    payload: dict[str, Any]
    run_id: str
    train_suites: list[str]
    validation_suites: list[str]
    acceptance_suites: list[str]
    mutable_paths: list[str]
    frozen_paths: list[str]
    worker_backend: str = "codex"
    worker_model: str | None = None
    expected_backend: str = "codex"
    expected_judge_backend: str = "codex"
    retry_policy: RetryPolicyConfig = field(default_factory=build_retry_policy)
    target_task: str | None = None
    target_prompt_path: str | None = None


def resolve_timeout_seconds(contract: AutoresearchContract, *, default: int = 300) -> int:
    timeout_policy = contract.payload.get("timeout_policy")
    if not isinstance(timeout_policy, dict):
        return default
    seconds = timeout_policy.get("seconds")
    if isinstance(seconds, bool) or not isinstance(seconds, int) or seconds <= 0:
        return default
    return seconds


def history_header() -> str:
    return "\t".join(HISTORY_COLUMNS)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Contract must be an object: {path}")
    return payload


def _is_under(base: Path, target: Path) -> bool:
    try:
        target.relative_to(base)
    except ValueError:
        return False
    return True


def normalize_repo_path(value: str, repo_root: Path) -> PurePosixPath:
    raw = Path(value).expanduser()
    resolved = raw.resolve() if raw.is_absolute() else (repo_root / raw).resolve()
    if not _is_under(repo_root.resolve(), resolved):
        raise ValueError(f"Path escapes repository root: {value}")
    relative = resolved.relative_to(repo_root.resolve())
    return PurePosixPath(relative.as_posix())


def paths_overlap(path_a: PurePosixPath, path_b: PurePosixPath) -> bool:
    if path_a == path_b:
        return True
    a_parts = path_a.parts
    b_parts = path_b.parts
    return a_parts == b_parts[: len(a_parts)] or b_parts == a_parts[: len(b_parts)]


def validate_contract_payload(payload: dict[str, Any]) -> None:
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError("jsonschema is required to validate autoresearch contracts.") from exc

    schema = _load_json(AUTORESEARCH_CONTRACT_SCHEMA_PATH)
    jsonschema.validate(instance=payload, schema=schema)


def normalize_backend_id(value: str | None, *, field_name: str, default: str) -> str:
    backend_id = str(value or default).strip()
    if backend_id not in AUTORESEARCH_BACKEND_IDS:
        supported = ", ".join(AUTORESEARCH_BACKEND_IDS)
        raise ValueError(f"{field_name} must be one of: {supported}")
    return backend_id


def resolve_retry_policy_from_payload(payload: dict[str, Any]) -> RetryPolicyConfig:
    retry_policy_raw = payload.get("retry_policy")
    if retry_policy_raw is None:
        return build_retry_policy()
    if not isinstance(retry_policy_raw, dict):
        raise ValueError("retry_policy must be an object when present.")
    retry_on_raw = retry_policy_raw.get("retry_on")
    retry_on: list[str] | None = None
    if retry_on_raw is not None:
        if not isinstance(retry_on_raw, list):
            raise ValueError("retry_policy.retry_on must be an array when present.")
        retry_on = [str(item).strip() for item in retry_on_raw if str(item).strip()]
    return build_retry_policy(
        max_attempts=retry_policy_raw.get("max_attempts"),
        backoff_seconds=retry_policy_raw.get("backoff_seconds"),
        retry_on=retry_on,
    )


def resolve_suite_path(suite_value: str, *, base_dir: Path) -> Path:
    candidate = Path(suite_value).expanduser()
    if candidate.is_absolute() and candidate.exists():
        return candidate.resolve()

    local = (base_dir / candidate).resolve()
    if local.exists():
        return local

    fixture = (SUITES_ROOT / candidate.name).resolve()
    if fixture.exists():
        return fixture

    raise FileNotFoundError(f"Suite manifest not found: {suite_value}")


def resolve_suite_files(contract: AutoresearchContract, *, base_dir: Path | None = None) -> dict[str, list[Path]]:
    source_dir = base_dir or contract.source_path.parent
    return {
        "train": [resolve_suite_path(value, base_dir=source_dir) for value in contract.train_suites],
        "validation": [resolve_suite_path(value, base_dir=source_dir) for value in contract.validation_suites],
        "acceptance": [resolve_suite_path(value, base_dir=source_dir) for value in contract.acceptance_suites],
    }


def validate_path_boundaries(contract: AutoresearchContract, *, repo_root: Path = REPO_ROOT) -> None:
    mutable = [normalize_repo_path(value, repo_root) for value in contract.mutable_paths]
    frozen = [normalize_repo_path(value, repo_root) for value in contract.frozen_paths]
    for mutable_path in mutable:
        for frozen_path in frozen:
            if paths_overlap(mutable_path, frozen_path):
                raise ValueError(
                    "mutable_paths and frozen_paths overlap: "
                    f"{mutable_path.as_posix()} vs {frozen_path.as_posix()}"
                )


def normalize_p2_target_task(value: str) -> str:
    task = str(value or "").strip()
    if task not in P2_TARGET_TASK_TO_RUNNER_TASK:
        supported = ", ".join(sorted(P2_TARGET_TASK_TO_RUNNER_TASK))
        raise ValueError(f"P2 target_task must be one of: {supported}")
    return task


def expected_p2_target_prompt_path(target_task: str) -> PurePosixPath:
    normalized_task = normalize_p2_target_task(target_task)
    return PurePosixPath(P2_TARGET_TASK_TO_PROMPT_PATH[normalized_task])


def resolve_p2_contract_target(
    contract: AutoresearchContract,
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[str, PurePosixPath] | None:
    target_task = contract.target_task
    target_prompt_path = contract.target_prompt_path
    if target_task is None and target_prompt_path is None:
        return None
    if not target_task or not target_prompt_path:
        raise ValueError("P2 contract requires both target_task and target_prompt_path.")

    normalized_task = normalize_p2_target_task(target_task)
    normalized_prompt = normalize_repo_path(target_prompt_path, repo_root)
    expected_prompt = expected_p2_target_prompt_path(normalized_task)
    if normalized_prompt != expected_prompt:
        raise ValueError(
            "P2 target_prompt_path must match the fixed task mapping: "
            f"{normalized_task} -> {expected_prompt.as_posix()}"
        )

    mutable = sorted(
        {normalize_repo_path(value, repo_root) for value in contract.mutable_paths},
        key=lambda item: item.as_posix(),
    )
    if mutable != [expected_prompt]:
        raise ValueError(
            "P2 mutable_paths must normalize to only target_prompt_path: "
            f"{expected_prompt.as_posix()}"
        )
    return normalized_task, expected_prompt


def load_contract(path: Path, *, repo_root: Path = REPO_ROOT) -> AutoresearchContract:
    source = path.expanduser().resolve()
    payload = _load_json(source)
    validate_contract_payload(payload)
    retry_policy = resolve_retry_policy_from_payload(payload)
    contract = AutoresearchContract(
        source_path=source,
        payload=payload,
        run_id=str(payload["run_id"]),
        train_suites=[str(item) for item in payload["train_suites"]],
        validation_suites=[str(item) for item in payload["validation_suites"]],
        acceptance_suites=[str(item) for item in payload["acceptance_suites"]],
        mutable_paths=[str(item) for item in payload["mutable_paths"]],
        frozen_paths=[str(item) for item in payload["frozen_paths"]],
        worker_backend=normalize_backend_id(
            payload.get("worker_backend"),
            field_name="worker_backend",
            default="codex",
        ),
        worker_model=str(payload["worker_model"]).strip() if payload.get("worker_model") is not None else None,
        expected_backend=normalize_backend_id(
            payload.get("expected_backend"),
            field_name="expected_backend",
            default="codex",
        ),
        expected_judge_backend=normalize_backend_id(
            payload.get("expected_judge_backend"),
            field_name="expected_judge_backend",
            default="codex",
        ),
        retry_policy=retry_policy,
        target_task=str(payload["target_task"]).strip() if payload.get("target_task") is not None else None,
        target_prompt_path=(
            str(normalize_repo_path(str(payload["target_prompt_path"]), repo_root).as_posix())
            if payload.get("target_prompt_path") is not None
            else None
        ),
    )
    resolve_suite_files(contract)
    validate_path_boundaries(contract, repo_root=repo_root)
    return contract
