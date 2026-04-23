#!/usr/bin/env python3
"""Structured stop signals for expected autoresearch loop termination."""

from __future__ import annotations


class AutoresearchStop(RuntimeError):
    """Raised when autoresearch should stop without being treated as a failure."""

    def __init__(self, *, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message


def format_stop_status(command: str) -> str:
    normalized = str(command or "").strip().replace("-", "_")
    if not normalized:
        return "command_status"
    return f"{normalized}_status"
