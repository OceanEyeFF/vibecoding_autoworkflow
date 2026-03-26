from __future__ import annotations

import argparse
import time
import unittest
from pathlib import Path
from unittest import mock

from common import RunResult, RunSpec
from run_skill_suite import coerce_process_output, execute_specs, parse_args, validate_args


class RunSkillSuiteTest(unittest.TestCase):
    def test_coerce_process_output_handles_none(self) -> None:
        self.assertEqual(coerce_process_output(None), "")

    def test_coerce_process_output_preserves_text(self) -> None:
        self.assertEqual(coerce_process_output("plain text"), "plain text")

    def test_coerce_process_output_decodes_bytes(self) -> None:
        self.assertEqual(coerce_process_output("hello".encode("utf-8")), "hello")

    def test_parse_args_defaults_jobs_to_one(self) -> None:
        args = parse_args(["--repo", "typer", "--backend", "codex"])

        self.assertEqual(args.jobs, 1)

    def test_validate_args_rejects_non_positive_jobs(self) -> None:
        args = argparse.Namespace(
            repo="typer",
            suite=None,
            backend="codex",
            judge_backend=None,
            task="context-routing",
            with_eval=False,
            prompt_file=None,
            eval_prompt_file=None,
            model=None,
            eval_model=None,
            timeout=300,
            eval_timeout=None,
            save_dir=None,
            jobs=0,
            claude_bin="claude",
            permission_mode="bypassPermissions",
            output_format="text",
            codex_bin="codex",
            sandbox="workspace-write",
            full_auto=True,
            opencode_bin="opencode",
        )

        with self.assertRaisesRegex(ValueError, "--jobs must be at least 1."):
            validate_args(args)

    def test_execute_specs_parallelizes_spec_pipelines_but_preserves_result_order(self) -> None:
        specs = [
            self._make_spec("context-routing"),
            self._make_spec("knowledge-base"),
            self._make_spec("task-contract"),
        ]
        args = argparse.Namespace(jobs=3)

        def fake_pipeline(spec: RunSpec, spec_index: int, **_: object) -> list[tuple[RunResult, None]]:
            time.sleep(0.25)
            return [(self._make_result(spec, spec_index), None)]

        started = time.perf_counter()
        with mock.patch("run_skill_suite.run_spec_pipeline", side_effect=fake_pipeline):
            results = execute_specs(
                specs,
                args=args,
                backend_registry={},
                run_dir=None,
            )
        elapsed = time.perf_counter() - started

        self.assertLess(elapsed, 0.55)
        self.assertEqual(
            [result.task for result, _ in results],
            ["context-routing", "knowledge-base", "task-contract"],
        )

    @staticmethod
    def _make_spec(task: str) -> RunSpec:
        return RunSpec(
            repo_path=Path("/tmp/typer"),
            task=task,
            prompt_file=Path(f"/tmp/{task}.prompt.md"),
            eval_prompt_file=None,
            backend="codex",
            judge_backend="codex",
            with_eval=False,
        )

    @staticmethod
    def _make_result(spec: RunSpec, spec_index: int) -> RunResult:
        return RunResult(
            task=spec.task,
            phase="skill",
            backend=spec.backend,
            judge_backend=spec.judge_backend,
            repo_path=spec.repo_path,
            prompt_file=spec.prompt_file,
            prompt_text=f"prompt-{spec_index}",
            command=["codex", "exec"],
            returncode=0,
            raw_stdout=f"stdout-{spec_index}",
            raw_stderr="",
            final_message=f"final-{spec_index}",
            elapsed_seconds=0.25,
            timed_out=False,
            started_at="2026-03-26T00:00:00+00:00",
            finished_at="2026-03-26T00:00:01+00:00",
        )


if __name__ == "__main__":
    unittest.main()
