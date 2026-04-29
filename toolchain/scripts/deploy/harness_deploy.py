#!/usr/bin/env python3
"""Stable deploy wrapper for future Harness distribution packaging."""

from __future__ import annotations

import sys

import adapter_deploy


def main(argv: list[str] | None = None) -> int:
    """Run the existing deploy command surface through a stable wrapper name."""

    return adapter_deploy.main(
        argv,
        prog="harness_deploy.py",
        description=(
            "Run Harness deploy commands through the stable distribution wrapper. "
            "This wrapper preserves adapter_deploy.py command semantics."
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
