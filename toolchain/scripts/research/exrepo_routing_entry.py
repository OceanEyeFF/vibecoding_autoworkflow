#!/usr/bin/env python3
"""Helpers for exrepo routing-entry inspection in lightweight P2 runs."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import REPO_ROOT
from exrepo_runtime import resolve_tmp_exrepos_root
from run_skill_suite import load_suite_manifest, resolve_suite_repo


ROUTING_ENTRY_FALLBACK_MARKER = "<!-- exrepo-routing-entry-fallback: allow -->"
CONTEXT_ROUTING_SKILL_RELATIVE_PATH = Path(".agents/skills/context-routing-skill/SKILL.md")
STATUS_USABLE = "usable_repo_skill"
STATUS_MISSING = "missing_repo_skill"
STATUS_INVALID = "invalid_repo_skill_wrapper"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_under(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _extract_canonical_source_paths(skill_text: str) -> list[str]:
    lines = skill_text.splitlines()
    in_section = False
    paths: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == "## Canonical Sources":
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if not in_section:
            continue
        for match in re.findall(r"`([^`]+)`", line):
            candidate = match.strip()
            if not candidate:
                continue
            paths.append(candidate)
    seen: set[str] = set()
    ordered: list[str] = []
    for value in paths:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def prompt_allows_exrepo_routing_fallback(prompt_path: Path) -> bool:
    if not prompt_path.is_file():
        return False
    return ROUTING_ENTRY_FALLBACK_MARKER in prompt_path.read_text(encoding="utf-8")


def classify_context_routing_repo_skill(
    repo_path: Path,
    *,
    repo_root: Path = REPO_ROOT,
    tmp_exrepos_root: Path | None = None,
) -> dict[str, Any] | None:
    resolved_repo = repo_path.expanduser().resolve()
    exrepos_root = (repo_root / ".exrepos").resolve()
    resolved_tmp_root = (
        tmp_exrepos_root.expanduser().resolve()
        if tmp_exrepos_root is not None
        else resolve_tmp_exrepos_root(repo_root=repo_root)
    )
    if not any(
        _is_under(resolved_repo, base_root)
        for base_root in (exrepos_root, resolved_tmp_root)
    ):
        return None

    skill_path = resolved_repo / CONTEXT_ROUTING_SKILL_RELATIVE_PATH
    payload: dict[str, Any] = {
        "repo": resolved_repo.name,
        "repo_path": str(resolved_repo),
        "skill_path": str(skill_path),
        "canonical_paths": [],
        "missing_paths": [],
    }
    if not skill_path.is_file():
        payload["status"] = STATUS_MISSING
        return payload

    canonical_paths = _extract_canonical_source_paths(skill_path.read_text(encoding="utf-8"))
    payload["canonical_paths"] = canonical_paths
    missing_paths = [
        value
        for value in canonical_paths
        if not (resolved_repo / value.rstrip("/")).exists()
    ]
    payload["missing_paths"] = missing_paths
    if not canonical_paths or missing_paths:
        payload["status"] = STATUS_INVALID
        return payload

    payload["status"] = STATUS_USABLE
    return payload


def collect_context_routing_suite_repo_skill_report(
    suite_files: list[Path],
    *,
    repo_root: Path = REPO_ROOT,
    tmp_exrepos_root: Path | None = None,
) -> list[dict[str, Any]]:
    seen: set[Path] = set()
    report: list[dict[str, Any]] = []
    for suite_file in suite_files:
        manifest = load_suite_manifest(suite_file)
        runs = manifest.get("runs") or []
        if not isinstance(runs, list):
            continue
        for run_entry in runs:
            if not isinstance(run_entry, dict):
                continue
            repo_value = run_entry.get("repo")
            if not repo_value:
                continue
            repo_path = resolve_suite_repo(str(repo_value), suite_file.parent)
            resolved_repo = repo_path.expanduser().resolve()
            if resolved_repo in seen:
                continue
            seen.add(resolved_repo)
            capability = classify_context_routing_repo_skill(
                resolved_repo,
                repo_root=repo_root,
                tmp_exrepos_root=tmp_exrepos_root,
            )
            if capability is not None:
                report.append(capability)
    return sorted(report, key=lambda item: (str(item.get("status") or ""), str(item.get("repo") or "")))


def build_context_routing_capability_report_payload(
    *,
    prompt_path: Path,
    capabilities: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "report_version": 1,
        "generated_at": now_iso(),
        "prompt_path": str(prompt_path),
        "prompt_allows_repo_skill_fallback": prompt_allows_exrepo_routing_fallback(prompt_path),
        "capabilities": capabilities,
    }


def write_context_routing_capability_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def format_context_routing_capability_lines(capabilities: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for item in capabilities:
        parts = [
            "context_routing_repo_skill",
            f"repo={item['repo']}",
            f"status={item['status']}",
        ]
        missing_paths = [str(value).strip() for value in item.get("missing_paths") or [] if str(value).strip()]
        if missing_paths:
            parts.append("missing=" + ",".join(missing_paths))
        lines.append(" ".join(parts))
    return lines
