from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend_runner import (
    PhaseExecutionRequest,
    RETRY_REASON_EMPTY_OUTPUT_PARSE_ERROR,
    RETRY_REASON_NONZERO_RETURNCODE,
    RETRY_REASON_TIMEOUT,
    build_retry_policy,
    classify_phase_failure,
    parse_retry_on_values,
    retry_policy_cli_args,
    run_phase,
)
from backends.base import BackendInvocation, ResearchBackend
from common import RunResult, RunSpec, resolve_repo
from exrepo_runtime import materialize_suite, resolve_tmp_exrepos_root
from run_skill_suite import (
    build_backend_context,
    coerce_process_output,
    execute_specs,
    parse_args,
    resolve_suite_specs,
    save_result,
    save_summary,
    validate_args,
)


class FakeBackend(ResearchBackend):
    backend_id = "fake"

    def build_skill_command(self, prompt_text: str, repo_path: Path, model: str | None) -> BackendInvocation:
        del prompt_text, repo_path, model
        return BackendInvocation(command=["fake", "skill"])

    def build_eval_command(
        self,
        prompt_text: str,
        repo_path: Path,
        model: str | None,
        schema_path: Path | None,
    ) -> BackendInvocation:
        del prompt_text, repo_path, model, schema_path
        return BackendInvocation(command=["fake", "eval"])

    def extract_final_message(self, invocation: BackendInvocation, stdout: str) -> str:
        del invocation
        return stdout.strip()


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
        self.assertEqual(args.codex_reasoning_effort, "high")

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
            codex_reasoning_effort="high",
            opencode_bin="opencode",
            max_attempts=3,
            backoff_seconds=3.0,
            retry_on=None,
        )

        with self.assertRaisesRegex(ValueError, "--jobs must be at least 1."):
            validate_args(args)

    def test_resolve_repo_accepts_bare_repo_from_tmp_exrepos_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tmp_exrepos_root = root / "tmp-exrepos"
            repo_path = tmp_exrepos_root / "typer"
            repo_path.mkdir(parents=True, exist_ok=True)

            with mock.patch("common.TMP_EXREPOS_ROOT", tmp_exrepos_root), mock.patch(
                "common.EXREPOS_ROOT",
                root / ".exrepos",
            ):
                resolved = resolve_repo("typer")

            self.assertEqual(resolved, repo_path.resolve(strict=False))

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

    def test_resolve_suite_specs_consumes_materialized_yaml_suite_with_absolute_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite_dir = root / "suites"
            prompt_dir = suite_dir / "prompts"
            prompt_dir.mkdir(parents=True, exist_ok=True)
            prompt_path = prompt_dir / "task.md"
            eval_prompt_path = prompt_dir / "eval.md"
            prompt_path.write_text("prompt\n", encoding="utf-8")
            eval_prompt_path.write_text("eval\n", encoding="utf-8")
            source_suite = suite_dir / "train.yaml"
            source_suite.write_text(
                "version: 1\n"
                "defaults:\n"
                "  backend: codex\n"
                "  judge_backend: codex\n"
                "  with_eval: true\n"
                "runs:\n"
                "  - repo: typer\n"
                "    task: context-routing\n"
                "    prompt_file: prompts/task.md\n"
                "    eval_prompt_file: prompts/eval.md\n",
                encoding="utf-8",
            )
            exrepo_root = resolve_tmp_exrepos_root(repo_root=root / "repo-root", temp_root=root / "os-tmp")
            repo_path = exrepo_root / "typer"
            repo_path.mkdir(parents=True, exist_ok=True)

            materialized = materialize_suite(source_suite, root / "artifacts", exrepo_root=exrepo_root)

            specs, suite_path, run_label = resolve_suite_specs(argparse.Namespace(suite=str(materialized)))

            self.assertEqual(suite_path, materialized.resolve(strict=False))
            self.assertEqual(run_label, materialized.stem)
            self.assertEqual(len(specs), 1)
            self.assertEqual(specs[0].repo_path, repo_path.resolve(strict=False))
            self.assertEqual(specs[0].prompt_file, prompt_path.resolve(strict=False))
            self.assertEqual(specs[0].eval_prompt_file, eval_prompt_path.resolve(strict=False))

    def test_resolve_suite_specs_consumes_materialized_json_suite_with_absolute_repo_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite_dir = root / "json-suite"
            prompt_dir = suite_dir / "prompts"
            prompt_dir.mkdir(parents=True, exist_ok=True)
            prompt_path = prompt_dir / "task.md"
            eval_prompt_path = prompt_dir / "eval.md"
            prompt_path.write_text("prompt\n", encoding="utf-8")
            eval_prompt_path.write_text("eval\n", encoding="utf-8")
            source_suite = suite_dir / "validation.json"
            source_suite.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "defaults": {
                            "backend": "codex",
                            "judge_backend": "codex",
                            "with_eval": True,
                        },
                        "runs": [
                            {
                                "repo": ".",
                                "task": "context-routing",
                                "prompt_file": "prompts/task.md",
                                "eval_prompt_file": "prompts/eval.md",
                            }
                        ],
                    },
                    ensure_ascii=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            materialized = materialize_suite(source_suite, root / "artifacts", exrepo_root=root / "tmp-exrepos")

            specs, _, _ = resolve_suite_specs(argparse.Namespace(suite=str(materialized)))

            self.assertEqual(len(specs), 1)
            self.assertEqual(specs[0].repo_path, suite_dir.resolve(strict=False))
            self.assertEqual(specs[0].prompt_file, prompt_path.resolve(strict=False))
            self.assertEqual(specs[0].eval_prompt_file, eval_prompt_path.resolve(strict=False))

    def test_phase_executor_retries_until_third_attempt_success(self) -> None:
        backend = FakeBackend(executable="fake")

        def parse_output(output_text: str) -> tuple[dict[str, object] | None, str | None]:
            if not output_text.strip():
                return None, "Eval phase produced no usable output."
            return {"ok": True}, None

        completed = [
            subprocess.TimeoutExpired(cmd=["fake", "eval"], timeout=30),
            subprocess.CompletedProcess(["fake", "eval"], 0, "", ""),
            subprocess.CompletedProcess(["fake", "eval"], 0, "usable output", ""),
        ]

        with mock.patch("backend_runner.subprocess.run", side_effect=completed):
            result = run_phase(
                PhaseExecutionRequest(
                    phase="eval",
                    backend_id="fake",
                    backend=backend,
                    prompt_text="judge",
                    repo_path=Path("/tmp/repo"),
                    model=None,
                    timeout_seconds=30,
                    retry_policy=build_retry_policy(max_attempts=3, backoff_seconds=0),
                    parse_output=parse_output,
                )
            )

        self.assertEqual(result.attempt_count, 3)
        self.assertEqual(result.final_attempt, 3)
        self.assertEqual(result.structured_output, {"ok": True})
        self.assertIsNone(result.parse_error)
        self.assertEqual(result.attempts[0].failure_reason, RETRY_REASON_TIMEOUT)
        self.assertEqual(result.attempts[1].failure_reason, RETRY_REASON_EMPTY_OUTPUT_PARSE_ERROR)
        self.assertIsNone(result.attempts[2].failure_reason)

    def test_phase_executor_honors_max_attempts_one(self) -> None:
        backend = FakeBackend(executable="fake")

        with mock.patch(
            "backend_runner.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["fake", "skill"], timeout=30),
        ) as mocked_run:
            result = run_phase(
                PhaseExecutionRequest(
                    phase="skill",
                    backend_id="fake",
                    backend=backend,
                    prompt_text="prompt",
                    repo_path=Path("/tmp/repo"),
                    model=None,
                    timeout_seconds=30,
                    retry_policy=build_retry_policy(max_attempts=1, backoff_seconds=0),
                )
            )

        self.assertEqual(mocked_run.call_count, 1)
        self.assertEqual(result.attempt_count, 1)
        self.assertEqual(result.final_attempt, 1)
        self.assertTrue(result.timed_out)

    def test_phase_executor_preserves_phase_level_timing_across_retries(self) -> None:
        backend = FakeBackend(executable="fake")
        completed = [
            subprocess.CompletedProcess(["fake", "skill"], 1, "temporary failure", ""),
            subprocess.CompletedProcess(["fake", "skill"], 0, "usable output", ""),
        ]
        timestamps = [
            dt.datetime(2026, 3, 26, 0, 0, 0, tzinfo=dt.timezone.utc),
            dt.datetime(2026, 3, 26, 0, 0, 1, tzinfo=dt.timezone.utc),
            dt.datetime(2026, 3, 26, 0, 0, 2, tzinfo=dt.timezone.utc),
            dt.datetime(2026, 3, 26, 0, 0, 10, tzinfo=dt.timezone.utc),
            dt.datetime(2026, 3, 26, 0, 0, 12, tzinfo=dt.timezone.utc),
        ]

        with mock.patch("backend_runner.subprocess.run", side_effect=completed), mock.patch(
            "backend_runner.datetime"
        ) as mocked_datetime, mock.patch(
            "backend_runner.time.perf_counter",
            side_effect=[10.0, 11.0, 12.0, 20.0, 25.0, 30.0, 30.0],
        ):
            mocked_datetime.now.side_effect = timestamps
            result = run_phase(
                PhaseExecutionRequest(
                    phase="skill",
                    backend_id="fake",
                    backend=backend,
                    prompt_text="prompt",
                    repo_path=Path("/tmp/repo"),
                    model=None,
                    timeout_seconds=30,
                    retry_policy=build_retry_policy(max_attempts=2, backoff_seconds=0),
                )
            )

        self.assertEqual(result.started_at, timestamps[0].isoformat())
        self.assertEqual(result.finished_at, timestamps[-1].isoformat())
        self.assertEqual(result.elapsed_seconds, 20.0)
        self.assertEqual(result.attempts[0].started_at, timestamps[1].isoformat())
        self.assertEqual(result.attempts[-1].finished_at, timestamps[-1].isoformat())

    def test_retry_policy_cli_args_encodes_empty_retry_on_with_none_sentinel(self) -> None:
        retry_policy = build_retry_policy(max_attempts=1, backoff_seconds=0, retry_on=[])

        args = retry_policy_cli_args(retry_policy)

        self.assertEqual(args, ["--max-attempts", "1", "--backoff-seconds", "0.0", "--retry-on", "none"])

    def test_parse_retry_on_values_accepts_none_sentinel_as_empty_set(self) -> None:
        self.assertEqual(parse_retry_on_values(["none"]), ())

    def test_build_backend_context_records_effective_claude_eval_output_format(self) -> None:
        args = argparse.Namespace(
            permission_mode="bypassPermissions",
            output_format="text",
            sandbox="workspace-write",
            full_auto=True,
            codex_reasoning_effort="high",
        )

        context = build_backend_context(
            args,
            "claude",
            phase="eval",
            schema_file=Path("/tmp/schema.json"),
        )

        self.assertEqual(
            context,
            {
                "permission_mode": "bypassPermissions",
                "output_format": "json",
            },
        )

    def test_classify_phase_failure_prefers_nonzero_returncode_over_parse_error_with_stdout(self) -> None:
        failure_reason = classify_phase_failure(
            returncode=1,
            timed_out=False,
            raw_stdout="backend printed something",
            raw_stderr="",
            final_message="",
            parse_error="Eval output did not contain any parsed rubric scores.",
        )

        self.assertEqual(failure_reason, RETRY_REASON_NONZERO_RETURNCODE)

    def test_classify_phase_failure_does_not_treat_stderr_only_parse_error_as_empty_output(self) -> None:
        failure_reason = classify_phase_failure(
            returncode=0,
            timed_out=False,
            raw_stdout="",
            raw_stderr="usage: fake judge --token <token>",
            final_message="",
            parse_error="Eval phase produced no usable output.",
        )

        self.assertNotEqual(failure_reason, RETRY_REASON_EMPTY_OUTPUT_PARSE_ERROR)

    def test_save_summary_and_meta_include_retry_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            result = self._make_result(self._make_spec("context-routing"), 1)
            result.attempt_count = 3
            result.final_attempt = 3
            result.failure_reason = None
            result.attempts = [
                {
                    "attempt": 1,
                    "returncode": None,
                    "timed_out": True,
                    "failure_reason": "timeout",
                    "parse_error": None,
                    "raw_stdout_excerpt": None,
                    "raw_stderr_excerpt": None,
                    "started_at": "2026-03-26T00:00:00+00:00",
                    "finished_at": "2026-03-26T00:00:01+00:00",
                    "elapsed_seconds": 1.0,
                },
                {
                    "attempt": 2,
                    "returncode": 1,
                    "timed_out": False,
                    "failure_reason": "nonzero_returncode",
                    "parse_error": None,
                    "raw_stdout_excerpt": "temporary",
                    "raw_stderr_excerpt": "temporary",
                    "started_at": "2026-03-26T00:00:02+00:00",
                    "finished_at": "2026-03-26T00:00:03+00:00",
                    "elapsed_seconds": 1.0,
                },
                {
                    "attempt": 3,
                    "returncode": 0,
                    "timed_out": False,
                    "failure_reason": None,
                    "parse_error": None,
                    "raw_stdout_excerpt": "final",
                    "raw_stderr_excerpt": None,
                    "started_at": "2026-03-26T00:00:04+00:00",
                    "finished_at": "2026-03-26T00:00:05+00:00",
                    "elapsed_seconds": 1.0,
                },
            ]

            artifacts = save_result(run_dir, result, 1)
            save_summary(run_dir, None, [(result, artifacts)])

            meta = json.loads((run_dir / artifacts["meta"]).read_text(encoding="utf-8"))
            summary = json.loads((run_dir / "run-summary.json").read_text(encoding="utf-8"))

            self.assertEqual(meta["attempt_count"], 3)
            self.assertEqual(meta["final_attempt"], 3)
            self.assertEqual(len(meta["attempts"]), 3)
            self.assertIn("attempts", artifacts)
            self.assertEqual(summary["results"][0]["attempt_count"], 3)
            self.assertEqual(summary["results"][0]["final_attempt"], 3)
            self.assertEqual(len(summary["results"][0]["attempts"]), 3)

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
