#!/usr/bin/env python3
"""Shared helpers for deterministic lane-by-lane suite execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from autoresearch_scoreboard import load_run_summary


def capture_new_summary(save_dir: Path, before: set[Path]) -> Path:
    after = {path for path in save_dir.iterdir() if path.is_dir()}
    new_dirs = sorted(after - before)
    if len(new_dirs) == 1:
        summary = new_dirs[0] / "run-summary.json"
        if summary.is_file():
            return summary
    candidates = sorted((path / "run-summary.json" for path in after), key=lambda item: item.stat().st_mtime)
    candidates = [path for path in candidates if path.is_file()]
    if not candidates:
        raise FileNotFoundError(f"No run-summary.json found under {save_dir}")
    return candidates[-1]


def execute_lane_suites(
    suite_files: list[Path],
    save_dir: Path,
    *,
    run_suite: Callable[[Path], None],
) -> list[dict[str, Any]]:
    save_dir.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []
    for suite_file in suite_files:
        before = {path for path in save_dir.iterdir() if path.is_dir()}
        run_suite(suite_file)
        summary_path = capture_new_summary(save_dir, before)
        summaries.append(load_run_summary(summary_path))
    return summaries
