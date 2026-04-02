#!/usr/bin/env python3
"""Compatibility entrypoint for the closeout acceptance gate."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from toolchain.scripts.test.closeout_acceptance_gate import main


if __name__ == "__main__":
    raise SystemExit(main())
