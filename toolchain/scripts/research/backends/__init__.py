#!/usr/bin/env python3
"""Backend registry for research runners."""

from __future__ import annotations

from .claude import ClaudeBackend
from .codex import CODEX_REASONING_EFFORTS, CodexBackend
from .opencode import OpenCodeBackend


BACKEND_IDS = ("claude", "codex", "opencode")


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
        return OpenCodeBackend(executable=args.opencode_bin)
    raise ValueError(f"Unknown backend: {backend_id}")
