#!/usr/bin/env python3
"""Helpers for tmp exrepo runtime paths and suite materialization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

TMP_EXREPO_OS_ROOT = Path("/tmp").resolve(strict=False)


def resolve_tmp_exrepos_root(
    *,
    repo_root: Path,
    temp_root: Path | None = None,
) -> Path:
    """Return the stable tmp exrepo root for the provided repository root."""
    resolved_repo_root = repo_root.expanduser().resolve(strict=False)
    resolved_temp_root = (
        temp_root.expanduser().resolve(strict=False)
        if temp_root is not None
        else TMP_EXREPO_OS_ROOT
    )
    fingerprint = hashlib.sha256(str(resolved_repo_root).encode("utf-8")).hexdigest()[:12]
    return (resolved_temp_root / f"{resolved_repo_root.name}-exrepos-{fingerprint}").resolve(strict=False)


def resolve_materialized_suite_path(source_suite: Path, output_dir: Path) -> Path:
    """Build a deterministic output path for a materialized suite."""
    resolved_source = source_suite.expanduser().resolve(strict=False)
    resolved_output_dir = output_dir.expanduser().resolve(strict=False)
    fingerprint = hashlib.sha256(str(resolved_source).encode("utf-8")).hexdigest()[:12]
    return resolved_output_dir / f"{resolved_source.stem}.materialized.{fingerprint}{resolved_source.suffix}"


def materialize_suite(
    source_suite: Path,
    output_dir: Path,
    *,
    exrepo_root: Path | None = None,
    repo_root: Path | None = None,
) -> Path:
    """Rewrite suite path fields into absolute runtime paths without mutating the source suite."""
    resolved_source = source_suite.expanduser().resolve(strict=False)
    manifest = _load_suite_manifest(resolved_source)
    version = manifest.get("version", 1)
    if version != 1:
        raise ValueError(f"Unsupported suite manifest version: {version}")

    defaults = manifest.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise ValueError("Suite manifest 'defaults' must be a mapping when present.")
    runs = manifest.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("Suite manifest must define a non-empty 'runs' list.")

    if exrepo_root is not None:
        resolved_exrepo_root = exrepo_root.expanduser().resolve(strict=False)
    else:
        if repo_root is None:
            raise ValueError("materialize_suite requires either exrepo_root or repo_root.")
        resolved_exrepo_root = resolve_tmp_exrepos_root(repo_root=repo_root)
    rewritten_runs: list[dict[str, Any]] = []
    for index, run_entry in enumerate(runs, start=1):
        if not isinstance(run_entry, dict):
            raise ValueError(f"Suite run #{index} must be a mapping.")
        repo_value = run_entry.get("repo")
        if not repo_value:
            raise ValueError(f"Suite run #{index} is missing 'repo'.")
        rewritten_entry = dict(run_entry)
        rewritten_entry["repo"] = _rewrite_repo_value(
            str(repo_value),
            suite_dir=resolved_source.parent,
            exrepo_root=resolved_exrepo_root,
        )
        for field in ("prompt_file", "eval_prompt_file"):
            field_value = run_entry.get(field)
            if field_value is None:
                continue
            rewritten_entry[field] = _rewrite_path_value(str(field_value), base_dir=resolved_source.parent)
        rewritten_runs.append(rewritten_entry)

    rewritten_manifest = dict(manifest)
    rewritten_manifest["runs"] = rewritten_runs

    output_path = resolve_materialized_suite_path(resolved_source, output_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_suite_manifest(output_path, rewritten_manifest)
    return output_path


def _rewrite_repo_value(repo_value: str, *, suite_dir: Path, exrepo_root: Path) -> str:
    candidate = Path(repo_value).expanduser()
    if candidate.is_absolute():
        return str(candidate.resolve(strict=False))
    if _is_path_like(repo_value):
        return str((suite_dir / candidate).resolve(strict=False))
    return str((exrepo_root / repo_value).resolve(strict=False))


def _rewrite_path_value(value: str, *, base_dir: Path) -> str:
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return str(candidate.resolve(strict=False))
    return str((base_dir / candidate).resolve(strict=False))


def _is_path_like(value: str) -> bool:
    return value.startswith((".", "~")) or "/" in value or "\\" in value


def _load_suite_manifest(path: Path) -> dict[str, Any]:
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Suite manifest must be a mapping: {path}")
        return payload

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("YAML suite manifests require PyYAML to be installed.") from exc

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Suite manifest must be a mapping: {path}")
    return payload


def _write_suite_manifest(path: Path, payload: dict[str, Any]) -> None:
    if path.suffix == ".json":
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        return

    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("YAML suite manifests require PyYAML to be installed.") from exc

    text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)
    path.write_text(text, encoding="utf-8")
