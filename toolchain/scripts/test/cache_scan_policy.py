"""Shared cache-scan policy for governance and closeout checks."""

from __future__ import annotations

CACHE_SCAN_ROOTS = ("docs", "product", "toolchain", "tools")
CACHE_DIR_NAMES = {"__pycache__", ".pytest_cache"}
CACHE_FILE_SUFFIXES = (".pyc", ".pyo")
