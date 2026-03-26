from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from run_backend_acceptance_matrix import (
    MATRIX_LANES,
    build_forward_args,
    build_suite_manifest,
    main,
    parse_args,
)


class BackendAcceptanceMatrixTest(unittest.TestCase):
    def test_build_suite_manifest_covers_expected_live_lanes(self) -> None:
        manifest = build_suite_manifest("typer")

        self.assertEqual(manifest["version"], 1)
        self.assertEqual(manifest["defaults"], {"with_eval": True})
        self.assertEqual(
            manifest["runs"],
            [
                {
                    "repo": "typer",
                    "backend": backend,
                    "judge_backend": judge_backend,
                    "task": "all",
                }
                for backend, judge_backend in MATRIX_LANES
            ],
        )

    def test_build_forward_args_omits_optional_overrides_when_unset(self) -> None:
        args = parse_args(["--repo", "typer"])

        forwarded = build_forward_args(args, Path("/tmp/matrix.json"))

        self.assertEqual(forwarded[forwarded.index("--jobs") + 1], "1")
        self.assertNotIn("--model", forwarded)
        self.assertNotIn("--eval-model", forwarded)
        self.assertNotIn("--eval-timeout", forwarded)
        self.assertNotIn("--save-dir", forwarded)
        self.assertIn("--full-auto", forwarded)
        self.assertNotIn("--no-full-auto", forwarded)

    def test_build_forward_args_includes_runtime_overrides(self) -> None:
        args = parse_args(
            [
                "--repo",
                "typer",
                "--model",
                "gpt-5.4",
                "--eval-model",
                "gpt-5.4-mini",
                "--timeout",
                "450",
                "--jobs",
                "2",
                "--eval-timeout",
                "120",
                "--save-dir",
                "/tmp/live-acceptance",
                "--claude-bin",
                "claude-dev",
                "--permission-mode",
                "default",
                "--output-format",
                "stream-json",
                "--codex-bin",
                "codex-dev",
                "--sandbox",
                "danger-full-access",
                "--no-full-auto",
            ]
        )

        forwarded = build_forward_args(args, Path("/tmp/matrix.json"))

        self.assertIn("--model", forwarded)
        self.assertIn("--eval-model", forwarded)
        self.assertIn("--eval-timeout", forwarded)
        self.assertIn("--save-dir", forwarded)
        self.assertIn("--no-full-auto", forwarded)
        self.assertNotIn("--full-auto", forwarded)
        self.assertEqual(forwarded[forwarded.index("--jobs") + 1], "2")
        self.assertEqual(forwarded[forwarded.index("--timeout") + 1], "450")
        self.assertEqual(forwarded[forwarded.index("--eval-timeout") + 1], "120")

    def test_main_delegates_to_unified_runner_with_temp_suite(self) -> None:
        captured: dict[str, object] = {}

        def fake_main(argv: list[str]) -> int:
            captured["argv"] = argv
            suite_path = Path(argv[argv.index("--suite") + 1])
            captured["suite_exists_during_call"] = suite_path.exists()
            captured["suite_payload"] = json.loads(suite_path.read_text(encoding="utf-8"))
            captured["suite_path"] = suite_path
            return 0

        with mock.patch("run_backend_acceptance_matrix.run_skill_suite_main", side_effect=fake_main):
            exit_code = main(["--repo", "typer", "--save-dir", "/tmp/acceptance"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            captured["suite_payload"],
            build_suite_manifest("typer"),
        )
        self.assertTrue(captured["suite_exists_during_call"])
        self.assertFalse(Path(captured["suite_path"]).exists())


if __name__ == "__main__":
    unittest.main()
