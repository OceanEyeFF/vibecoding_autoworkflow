#!/usr/bin/env python3
"""Backend registry for research runners."""

from __future__ import annotations

from .claude import ClaudeBackend
from .codex import CODEX_REASONING_EFFORTS, CodexBackend
from .opencode import OpenCodeBackend


BACKEND_IDS = ("claude", "codex", "opencode")


def normalize_opencode_output_format(output_format: str | None) -> str:
    if output_format in (None, "", "text", "default"):
        return "default"
    if output_format in ("json", "stream-json"):
        return "json"
    raise ValueError(f"Unsupported OpenCode output format: {output_format}")


def build_backend(backend_id: str, args) -> object:
    if backend_id == "claude":
        return ClaudeBackend(
            executable=args.claude_bin,
            permission_mode=args.permission_mode,
            output_format=args.output_format,
        )
    if backend_id == "codex":
        return CodexBackend(
            executable=args.codex_bin,
            sandbox=args.sandbox,
            full_auto=args.full_auto,
            reasoning_effort=getattr(args, "codex_reasoning_effort", "high"),
        )
    if backend_id == "opencode":
        return OpenCodeBackend(
            executable=args.opencode_bin,
            output_format=normalize_opencode_output_format(getattr(args, "output_format", "text")),
        )
    raise ValueError(f"Unknown backend: {backend_id}")
