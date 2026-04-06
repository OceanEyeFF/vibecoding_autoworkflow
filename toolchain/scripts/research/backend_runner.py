#!/usr/bin/env python3
"""Shared backend phase execution with retry-aware normalized results."""

from __future__ import annotations

import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from backends.base import ResearchBackend


RETRY_REASON_TIMEOUT = "timeout"
RETRY_REASON_NONZERO_RETURNCODE = "nonzero_returncode"
RETRY_REASON_EMPTY_OUTPUT_PARSE_ERROR = "empty_output_parse_error"
RETRY_REASON_TRANSIENT_DISCONNECT = "transient_disconnect"
NON_RETRYABLE_PARSE_ERROR = "parse_error"
ALLOWED_RETRY_REASONS = (
    RETRY_REASON_TIMEOUT,
    RETRY_REASON_NONZERO_RETURNCODE,
    RETRY_REASON_EMPTY_OUTPUT_PARSE_ERROR,
    RETRY_REASON_TRANSIENT_DISCONNECT,
)
DEFAULT_RETRY_ON = ALLOWED_RETRY_REASONS

TRANSIENT_DISCONNECT_PATTERNS = (
    "connection reset",
    "connection aborted",
    "connection closed",
    "broken pipe",
    "econnreset",
    "transport closed",
    "socket hang up",
    "stream closed",
    "stream interrupted",
    "temporarily unavailable",
    "try again",
    "network error",
    "timed out waiting for response",
)

ParseOutputFn = Callable[[str], tuple[dict[str, Any] | None, str | None]]


def coerce_process_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def cleanup_backend_artifacts(paths: list[Path]) -> None:
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            continue


def _excerpt(text: str, *, limit: int = 280) -> str | None:
    normalized = text.strip()
    if not normalized:
        return None
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


@dataclass(frozen=True)
class RetryPolicyConfig:
    max_attempts: int = 3
    backoff_seconds: float = 3.0
    retry_on: tuple[str, ...] = DEFAULT_RETRY_ON

    def __post_init__(self) -> None:
        if isinstance(self.max_attempts, bool) or not isinstance(self.max_attempts, int) or self.max_attempts <= 0:
            raise ValueError("retry_policy.max_attempts must be a positive integer.")
        if isinstance(self.backoff_seconds, bool) or not isinstance(self.backoff_seconds, (int, float)) or self.backoff_seconds < 0:
            raise ValueError("retry_policy.backoff_seconds must be a non-negative number.")
        invalid = sorted(set(self.retry_on) - set(ALLOWED_RETRY_REASONS))
        if invalid:
            raise ValueError(
                "retry_policy.retry_on contains unsupported values: " + ", ".join(invalid)
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_attempts": self.max_attempts,
            "backoff_seconds": self.backoff_seconds,
            "retry_on": list(self.retry_on),
        }


@dataclass(frozen=True)
class PhaseExecutionRequest:
    phase: str
    backend_id: str
    backend: ResearchBackend
    prompt_text: str
    repo_path: Path
    model: str | None
    timeout_seconds: int | float
    retry_policy: RetryPolicyConfig
    permission_args: dict[str, Any] = field(default_factory=dict)
    schema_file: Path | None = None
    parse_output: ParseOutputFn | None = None


@dataclass(frozen=True)
class PhaseAttemptRecord:
    attempt: int
    returncode: int | None
    timed_out: bool
    failure_reason: str | None
    parse_error: str | None
    raw_stdout_excerpt: str | None
    raw_stderr_excerpt: str | None
    started_at: str
    finished_at: str
    elapsed_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PhaseExecutionResult:
    phase: str
    backend_id: str
    command: list[str]
    returncode: int | None
    timed_out: bool
    raw_stdout: str
    raw_stderr: str
    final_message: str
    parse_error: str | None
    structured_output: dict[str, Any] | None
    failure_reason: str | None
    attempt_count: int
    final_attempt: int
    attempts: list[PhaseAttemptRecord]
    started_at: str
    finished_at: str
    elapsed_seconds: float
    schema_file: Path | None
    backend_context: dict[str, Any]


def build_retry_policy(
    *,
    max_attempts: int | None = None,
    backoff_seconds: int | float | None = None,
    retry_on: list[str] | tuple[str, ...] | None = None,
) -> RetryPolicyConfig:
    return RetryPolicyConfig(
        max_attempts=3 if max_attempts is None else max_attempts,
        backoff_seconds=3.0 if backoff_seconds is None else float(backoff_seconds),
        retry_on=tuple(DEFAULT_RETRY_ON if retry_on is None else retry_on),
    )


def parse_retry_on_values(values: list[str] | None) -> tuple[str, ...]:
    if not values:
        return DEFAULT_RETRY_ON
    tokens: list[str] = []
    for raw in values:
        for token in str(raw).split(","):
            normalized = token.strip()
            if normalized:
                tokens.append(normalized)
    if not tokens:
        raise ValueError("--retry-on must contain at least one retry reason when provided.")
    invalid = sorted(set(tokens) - set(ALLOWED_RETRY_REASONS))
    if invalid:
        raise ValueError(
            "--retry-on contains unsupported values: " + ", ".join(invalid)
        )
    return tuple(tokens)


def retry_policy_cli_args(retry_policy: RetryPolicyConfig) -> list[str]:
    args = [
        "--max-attempts",
        str(retry_policy.max_attempts),
        "--backoff-seconds",
        str(retry_policy.backoff_seconds),
    ]
    if retry_policy.retry_on:
        args.extend(["--retry-on", ",".join(retry_policy.retry_on)])
    return args


def failure_is_retryable(failure_reason: str | None, retry_policy: RetryPolicyConfig) -> bool:
    return failure_reason is not None and failure_reason in retry_policy.retry_on


def classify_phase_failure(
    *,
    returncode: int | None,
    timed_out: bool,
    raw_stdout: str,
    raw_stderr: str,
    final_message: str,
    parse_error: str | None,
) -> str | None:
    if timed_out:
        return RETRY_REASON_TIMEOUT
    combined = "\n".join(
        part for part in (raw_stdout, raw_stderr, final_message) if part.strip()
    ).lower()
    if parse_error is not None:
        if not (final_message or raw_stdout).strip():
            return RETRY_REASON_EMPTY_OUTPUT_PARSE_ERROR
        if any(pattern in combined for pattern in TRANSIENT_DISCONNECT_PATTERNS):
            return RETRY_REASON_TRANSIENT_DISCONNECT
        return NON_RETRYABLE_PARSE_ERROR
    if returncode not in (0, None):
        if any(pattern in combined for pattern in TRANSIENT_DISCONNECT_PATTERNS):
            return RETRY_REASON_TRANSIENT_DISCONNECT
        return RETRY_REASON_NONZERO_RETURNCODE
    return None


def run_phase(request: PhaseExecutionRequest) -> PhaseExecutionResult:
    if request.phase not in {"skill", "eval", "worker"}:
        raise ValueError(f"Unsupported phase: {request.phase}")

    attempts: list[PhaseAttemptRecord] = []
    final_result: PhaseExecutionResult | None = None
    phase_started_at_dt: datetime | None = None
    phase_started_perf: float | None = None

    for attempt in range(1, request.retry_policy.max_attempts + 1):
        if phase_started_at_dt is None:
            phase_started_at_dt = datetime.now(timezone.utc)
            phase_started_perf = time.perf_counter()
        if request.phase == "eval":
            invocation = request.backend.build_eval_command(
                prompt_text=request.prompt_text,
                repo_path=request.repo_path,
                model=request.model,
                schema_path=request.schema_file if request.backend.supports_json_schema else None,
            )
        else:
            invocation = request.backend.build_skill_command(
                prompt_text=request.prompt_text,
                repo_path=request.repo_path,
                model=request.model,
            )

        started_at_dt = datetime.now(timezone.utc)
        started_perf = time.perf_counter()
        try:
            completed = subprocess.run(
                invocation.command,
                cwd=request.repo_path,
                input=invocation.stdin_text,
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds,
                check=False,
            )
            returncode = completed.returncode
            raw_stdout = coerce_process_output(completed.stdout)
            raw_stderr = coerce_process_output(completed.stderr)
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            returncode = None
            raw_stdout = coerce_process_output(exc.stdout)
            raw_stderr = coerce_process_output(exc.stderr)
            timed_out = True
        finally:
            finished_at_dt = datetime.now(timezone.utc)
            elapsed_seconds = time.perf_counter() - started_perf

        try:
            final_message = request.backend.extract_final_message(invocation, raw_stdout)
        finally:
            cleanup_backend_artifacts(invocation.cleanup_paths)

        structured_output: dict[str, Any] | None = None
        parse_error: str | None = None
        if request.parse_output is not None:
            structured_output, parse_error = request.parse_output(final_message or raw_stdout)

        failure_reason = classify_phase_failure(
            returncode=returncode,
            timed_out=timed_out,
            raw_stdout=raw_stdout,
            raw_stderr=raw_stderr,
            final_message=final_message,
            parse_error=parse_error,
        )
        attempts.append(
            PhaseAttemptRecord(
                attempt=attempt,
                returncode=returncode,
                timed_out=timed_out,
                failure_reason=failure_reason,
                parse_error=parse_error,
                raw_stdout_excerpt=_excerpt(raw_stdout),
                raw_stderr_excerpt=_excerpt(raw_stderr),
                started_at=started_at_dt.isoformat(),
                finished_at=finished_at_dt.isoformat(),
                elapsed_seconds=elapsed_seconds,
            )
        )
        final_result = PhaseExecutionResult(
            phase=request.phase,
            backend_id=request.backend_id,
            command=invocation.command,
            returncode=returncode,
            timed_out=timed_out,
            raw_stdout=raw_stdout,
            raw_stderr=raw_stderr,
            final_message=final_message,
            parse_error=parse_error,
            structured_output=structured_output,
            failure_reason=failure_reason,
            attempt_count=len(attempts),
            final_attempt=attempt,
            attempts=list(attempts),
            started_at=(phase_started_at_dt or started_at_dt).isoformat(),
            finished_at=finished_at_dt.isoformat(),
            elapsed_seconds=(
                time.perf_counter() - phase_started_perf
                if phase_started_perf is not None
                else elapsed_seconds
            ),
            schema_file=request.schema_file,
            backend_context=dict(request.permission_args),
        )
        if failure_reason is None:
            return final_result
        if attempt >= request.retry_policy.max_attempts or not failure_is_retryable(failure_reason, request.retry_policy):
            return final_result
        if request.retry_policy.backoff_seconds > 0:
            time.sleep(request.retry_policy.backoff_seconds)

    if final_result is None:
        raise RuntimeError("Phase execution did not produce a result.")
    return final_result
