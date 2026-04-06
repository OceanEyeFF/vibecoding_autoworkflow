# Requirements Document

## Introduction

This spec extends the autoresearch loop from a Codex-only execution path into a backend-neutral execution path with explicit retry policy control. The goal is to let `run_autoresearch_loop.py`, `run_autoresearch.py`, and `run_skill_suite.py` consume the same backend contract and retry semantics without breaking the existing default `codex -> codex` workflow.

## Alignment with Product Vision

This feature supports the repository's contract-layer role by moving backend choice and retry behavior out of hardcoded runner logic and into reusable interfaces, CLI options, and contract fields. It keeps backend-specific transport details inside adapters while preserving one canonical execution path for research runs.

## Requirements

### Requirement 1

**User Story:** As a research operator, I want autoresearch to select `claude`, `codex`, or `opencode` per phase, so that the loop is not permanently coupled to Codex-specific worker execution.

#### Acceptance Criteria

1. WHEN `run_autoresearch_loop.py` runs without new backend overrides THEN the system SHALL keep the current worker behavior by defaulting to `worker_backend=codex`.
2. WHEN a contract or CLI override declares a worker backend and optional worker model THEN the system SHALL route the worker phase through a shared backend forwarding layer instead of a Codex-only subprocess path.
3. IF a P2 contract omits backend expectations THEN the system SHALL keep the current preflight rule by validating suites against `codex -> codex`.
4. IF a P2 contract declares `expected_backend` and `expected_judge_backend` THEN the system SHALL validate suites against those declared values instead of the hardcoded `codex -> codex` pair.
5. WHEN the selected backend is `claude` THEN the system SHALL forward Claude-specific permission arguments and SHALL NOT require Codex-only arguments for that invocation.
6. WHEN the selected backend is `codex` THEN the system SHALL continue to support `--sandbox`, `--full-auto`, and `--codex-reasoning-effort` for that invocation.
7. WHEN the selected backend is `opencode` THEN the system SHALL support an MVP executable path for skill and eval execution, SHALL pass through at least model, repo directory, and output-format controls, and SHALL extract a usable final message from OpenCode JSON event output.
8. IF the selected judge backend does not support schema-based eval THEN the system SHALL fall back to the existing text-parse eval path instead of failing solely because structured schema transport is unavailable.

### Requirement 2

**User Story:** As a research operator, I want configurable retry behavior for worker, skill, and eval phases, so that transient backend failures do not terminate an otherwise valid run.

#### Acceptance Criteria

1. WHEN skill, eval, or loop-worker execution starts THEN the system SHALL apply a shared retry policy with defaults `max_attempts=3`, `backoff_seconds=3`, and `retry_on=[timeout, nonzero_returncode, empty_output_parse_error, transient_disconnect]`.
2. IF `max_attempts=1` is configured THEN the system SHALL execute exactly one attempt and SHALL NOT retry.
3. WHEN a phase fails because of timeout, a retryable non-zero return, an empty eval parse result, or a transient disconnect pattern THEN the system SHALL retry until success or the configured attempt limit is reached.
4. IF execution fails because of contract validation, path boundary enforcement, unsupported parameter combinations, or explicit policy prohibition THEN the system SHALL fail immediately without retrying.
5. WHEN retries occur THEN the system SHALL record the total `attempt_count`, each failed attempt reason, and the final adopted attempt in run metadata and summary artifacts.
6. WHEN the final attempt succeeds after earlier failures THEN the system SHALL mark the overall phase as successful while preserving the full attempt history.
7. WHEN all attempts fail THEN the system SHALL determine the final phase status from the last attempt result and SHALL preserve the intermediate failure history for diagnosis.

## Non-Functional Requirements

### Code Architecture and Modularity

- **Single Responsibility Principle**: Backend transport, retry classification, contract parsing, and autoresearch orchestration should remain in separate modules.
- **Modular Design**: The shared backend forwarding layer should be reusable by both `run_skill_suite.py` and `run_autoresearch_loop.py`.
- **Dependency Management**: Backend-specific flags must remain isolated to backend adapters or backend-specific CLI shaping, not hardcoded across multiple runners.
- **Clear Interfaces**: Retry outcomes must use a single normalized result shape so phase callers do not reimplement timeout/parse-error handling.

### Performance

- Retry backoff must be bounded and configurable.
- Default behavior must preserve current single-threaded semantics unless the operator already uses `--jobs`.

### Security

- Backend routing must continue to honor existing sandbox and permission boundaries for each backend.
- Path validation and repo-boundary checks must remain fail-closed and must not become retryable.

### Reliability

- Existing `codex -> codex` contracts and smoke flows must remain backward-compatible when no new fields are supplied.
- Retry metadata must be persisted in a deterministic structure so failures can be audited after the run.
- The new retry policy must be clearly separated from existing mutation-selection fields such as `max_candidate_attempts_per_round`.

### Usability

- CLI overrides must remain discoverable from `--help`.
- Operators must be able to see which backend and which retry attempt produced the final accepted output.
