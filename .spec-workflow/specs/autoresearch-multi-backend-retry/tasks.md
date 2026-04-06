# Tasks Document

- [x] 1. Extend autoresearch contract schema and loader for backend/retry settings
  - Files: `toolchain/evals/fixtures/schemas/autoresearch-contract.schema.json`, `toolchain/scripts/research/autoresearch_contract.py`, `toolchain/scripts/research/test_autoresearch_contract.py`
  - Add optional contract fields for `worker_backend`, `worker_model`, `expected_backend`, `expected_judge_backend`, and nested `retry_policy`.
  - Preserve current defaults so contracts without new fields still behave as `worker_backend=codex` and P2 `expected_backend/judge_backend=codex`.
  - Keep retry policy distinct from existing `max_candidate_attempts_per_round`.
  - Purpose: make backend routing and retry policy part of the validated contract surface.
  - _Leverage: `toolchain/scripts/research/autoresearch_contract.py`, `toolchain/evals/fixtures/schemas/autoresearch-contract.schema.json`_
  - _Requirements: 1.2, 1.3, 1.4, 2.1, 2.2, 2.4_
  - _Prompt: Implement the task for spec autoresearch-multi-backend-retry, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Senior Python engineer focused on contract/schema design. Task: Extend the autoresearch contract schema and loader so backend expectations and retry policy are validated, defaulted, and exposed through the contract dataclass without changing existing contract behavior when fields are absent. Restrictions: Do not change mutation-selection semantics, do not make new fields mandatory, and do not relax existing repo/path validation. _Leverage: reuse existing schema validation, path normalization, and P2 target resolution helpers. _Requirements: 1.2, 1.3, 1.4, 2.1, 2.2, 2.4. Success: existing contracts still load, new fields validate and default correctly, and tests cover missing-field defaults plus invalid contract cases. Before coding, mark this task as in progress in tasks.md. After implementation, log the work with log-implementation, then mark the task complete in tasks.md._

- [x] 2. Make P2 preflight validate configured backend expectations instead of hardcoded codex-only rules
  - Files: `toolchain/scripts/research/autoresearch_round.py`, `toolchain/scripts/research/test_autoresearch_round.py`
  - Replace the `codex -> codex` hardcode in `validate_p2_preflight()` with contract-driven expected backend values while keeping single-task and `target_prompt_path` enforcement unchanged.
  - Preserve the default `codex -> codex` rule when the contract does not declare expectations.
  - Purpose: decouple P2 preflight from one backend pair while staying backward-compatible.
  - _Leverage: `resolve_p2_contract_target()`, existing suite manifest parsing in `AutoresearchRoundManager.validate_p2_preflight()`_
  - _Requirements: 1.3, 1.4_
  - _Prompt: Implement the task for spec autoresearch-multi-backend-retry, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python engineer focused on validation and fail-closed guardrails. Task: update P2 suite preflight so it enforces single-task and single-prompt constraints exactly as today, but reads the expected skill/judge backend pair from the contract with codex defaults when unset. Restrictions: Do not weaken prompt-path checks, do not allow multi-task suites, and do not move preflight logic out of the round manager. _Leverage: reuse the existing resolved spec expansion and contract target mapping. _Requirements: 1.3, 1.4. Success: codex-default contracts keep passing/failing exactly as before, contracts declaring `claude -> claude` are accepted, and mismatched suites still fail with clear errors. Before coding, mark this task as in progress in tasks.md. After implementation, log the work with log-implementation, then mark the task complete in tasks.md._

- [x] 3. Introduce a shared backend phase executor with retry-aware normalized outcomes
  - Files: `toolchain/scripts/research/backend_runner.py`, `toolchain/scripts/research/run_skill_suite.py`, `toolchain/scripts/research/test_run_skill_suite.py`
  - Add a reusable execution module that runs `skill` and `eval` phases through existing backend adapters, classifies retryable failures, applies backoff, and returns normalized attempt metadata.
  - Refactor `run_skill_suite.py` to use the shared executor rather than inline subprocess handling.
  - Record `attempt_count`, per-attempt failures, and final-attempt selection in `*.meta.json` and `run-summary.json`.
  - Purpose: unify subprocess, retry, and result normalization for suite execution.
  - _Leverage: `toolchain/scripts/research/backends/base.py`, existing `RunResult`/artifact writing in `run_skill_suite.py`, current eval parsing path_
  - _Requirements: 1.1, 1.5, 1.6, 1.8, 2.1, 2.2, 2.3, 2.5, 2.6, 2.7_
  - _Prompt: Implement the task for spec autoresearch-multi-backend-retry, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Senior Python engineer focused on runner architecture and fault handling. Task: add a shared backend phase executor and migrate `run_skill_suite.py` to it so skill/eval phases use one retry-aware normalized execution path with artifact-level observability. Restrictions: Do not break current CLI defaults, do not remove raw stdout/stderr capture, and do not change existing eval normalization rules except where needed for retry metadata. _Leverage: preserve the current `RunResult` shape as much as possible, extend artifact writing rather than inventing a second persistence format. _Requirements: 1.1, 1.5, 1.6, 1.8, 2.1, 2.2, 2.3, 2.5, 2.6, 2.7. Success: suite runs still return the same top-level success semantics, retries happen only for configured retryable failures, and saved metadata clearly shows attempt history. Before coding, mark this task as in progress in tasks.md. After implementation, log the work with log-implementation, then mark the task complete in tasks.md._

- [x] 4. Implement the OpenCode backend MVP on top of the shared backend interface
  - Files: `toolchain/scripts/research/backends/opencode.py`, `toolchain/scripts/research/backends/__init__.py`, `toolchain/scripts/research/test_opencode_backend.py`
  - Replace the reserved stub with a minimal executable backend implementation for skill/eval use.
  - Support model override, repo directory targeting, and output-format passthrough.
  - Parse OpenCode JSON event output into a usable final message for downstream eval parsing.
  - Purpose: make `opencode` a real backend option for research runner execution.
  - _Leverage: `ClaudeBackend` and `CodexBackend` command builders, backend registry construction in `backends/__init__.py`_
  - _Requirements: 1.7, 1.8_
  - _Prompt: Implement the task for spec autoresearch-multi-backend-retry, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Backend adapter engineer focused on CLI integration. Task: turn `OpenCodeBackend` from a reserved slot into an MVP runner adapter that can execute skill/eval commands and extract the final usable text from OpenCode JSON events. Restrictions: Keep all OpenCode-specific parsing isolated to the backend adapter, do not claim schema support unless it is actually implemented, and do not modify Claude/Codex command behavior. _Leverage: mirror the existing backend adapter contract and add isolated tests for command construction plus output extraction. _Requirements: 1.7, 1.8. Success: `build_backend(\"opencode\", ...)` returns a healthy executable backend when the binary exists, skill/eval commands are constructed deterministically, and tests prove the final-message extraction path. Before coding, mark this task as in progress in tasks.md. After implementation, log the work with log-implementation, then mark the task complete in tasks.md._

- [x] 5. Add worker backend routing and retry-aware execution to the autoresearch loop wrapper
  - Files: `toolchain/scripts/research/run_autoresearch_loop.py`, `toolchain/scripts/research/test_run_autoresearch_loop.py`
  - Replace `run_codex_worker()` with backend-neutral worker execution that consumes contract defaults plus CLI overrides.
  - Add loop CLI options for `--worker-backend`, `--worker-model`, and shared retry policy overrides while preserving current default behavior.
  - Record worker attempt history and make the final loop status depend on the last attempt result.
  - Purpose: decouple loop worker execution from Codex without changing existing default flows.
  - _Leverage: worker prompt builder and diff validation already in `run_autoresearch_loop.py`, shared backend phase executor from task 3_
  - _Requirements: 1.1, 1.2, 1.5, 1.6, 1.7, 2.1, 2.2, 2.3, 2.5, 2.6, 2.7_
  - _Prompt: Implement the task for spec autoresearch-multi-backend-retry, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Senior Python engineer focused on orchestration shells. Task: refactor the loop wrapper so worker execution is backend-neutral, retry-aware, and configurable from both contract defaults and CLI overrides while keeping the existing Codex default path unchanged. Restrictions: Do not change worker prompt contents unless required for backend neutrality, do not relax diff-scope validation, and do not alter round state transitions. _Leverage: reuse the shared executor from task 3 and existing loop control flow. _Requirements: 1.1, 1.2, 1.5, 1.6, 1.7, 2.1, 2.2, 2.3, 2.5, 2.6, 2.7. Success: current no-flag loop behavior still passes, `claude` and `opencode` can be selected for the worker phase, and retry behavior is visible in testable metadata/output. Before coding, mark this task as in progress in tasks.md. After implementation, log the work with log-implementation, then mark the task complete in tasks.md._

- [x] 6. Forward contract-driven retry settings through autoresearch baseline and round suite launches
  - Files: `toolchain/scripts/research/run_autoresearch.py`, `toolchain/scripts/research/autoresearch_round.py`, `toolchain/scripts/research/test_run_autoresearch.py`
  - Resolve retry policy from contract fields and pass it into nested `run_skill_suite.py` invocations for baseline, candidate, and replay suite execution.
  - Keep immediate failures for contract/preflight/path errors non-retryable.
  - Purpose: ensure retry policy applies inside the full autoresearch flow, not only direct suite runs.
  - _Leverage: `run_lane_suites()` in `run_autoresearch.py`, `_run_lane_suites()` in `autoresearch_round.py`, contract loader defaults from task 1_
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.7_
  - _Prompt: Implement the task for spec autoresearch-multi-backend-retry, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python engineer focused on end-to-end orchestration consistency. Task: propagate the resolved retry policy from autoresearch contracts into all nested suite executions so baseline, run-round, and replay honor the same retry semantics as direct suite runs. Restrictions: Do not change scoreboard aggregation logic, do not retry contract/preflight validation failures, and do not change materialized-suite authority rules. _Leverage: extend existing suite-launch helper functions rather than adding a second invocation path. _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.7. Success: nested suite launches receive the configured retry settings, deterministic tests cover retry forwarding, and failed non-retryable setup errors still abort immediately. Before coding, mark this task as in progress in tasks.md. After implementation, log the work with log-implementation, then mark the task complete in tasks.md._

- [x] 7. Update runner-facing documentation for backend selection and retry policy
  - Files: `toolchain/scripts/research/README.md`, `docs/operations/research-cli-help.md`, `docs/operations/autoresearch-minimal-loop.md`
  - Update CLI examples and behavior notes to document new worker backend selection, retry policy flags, default compatibility behavior, and OpenCode MVP support.
  - Replace text that still describes the loop as permanently `prepare-round -> Codex worker -> run-round -> decide-round`.
  - Purpose: keep repo-local runbooks aligned with the new execution surface.
  - _Leverage: existing CLI sections and minimal-loop examples in current operations docs_
  - _Requirements: 1.1, 1.2, 1.7, 2.1, 2.5_
  - _Prompt: Implement the task for spec autoresearch-multi-backend-retry, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Technical writer with deep repo-local CLI knowledge. Task: update the research runner and autoresearch loop documentation so operators can discover the new backend and retry controls without losing the current default-codex mental model. Restrictions: Do not document behavior that the code does not implement, do not duplicate long-form design rationale into operations docs, and keep examples consistent with real CLI flags. _Leverage: existing README and runbook structure. _Requirements: 1.1, 1.2, 1.7, 2.1, 2.5. Success: the docs describe default compatibility, configurable backend selection, retry flags, and OpenCode MVP behavior accurately and concisely. Before coding, mark this task as in progress in tasks.md. After implementation, log the work with log-implementation, then mark the task complete in tasks.md._

- [x] 8. Update analysis/observability documents to reflect OpenCode activation and retry metadata
  - Files: `docs/analysis/research-eval-contracts.md`, `docs/analysis/research-eval-observability.md`, `docs/analysis/autoresearch-p2-lightweight-single-prompt-codex-loop.md`
  - Change analysis-layer statements that still describe OpenCode as a stub-only backend or P2 preflight as intrinsically codex-only.
  - Document the new attempt-history observability contract for `meta.json` and `run-summary.json`.
  - Purpose: keep analysis-layer boundary docs synchronized with verified behavior after implementation.
  - _Leverage: existing backend contract and observability sections in analysis docs_
  - _Requirements: 1.3, 1.7, 2.5_
  - _Prompt: Implement the task for spec autoresearch-multi-backend-retry, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Engineering analyst focused on contract documentation. Task: update the analysis docs so backend state, P2 preflight semantics, and retry observability match the implemented code and no longer describe OpenCode or P2 backend checks with obsolete hardcoded assumptions. Restrictions: Only write verified facts, keep historical rationale intact where still useful, and do not turn analysis docs into step-by-step runbooks. _Leverage: existing contract and observability sections in the listed docs. _Requirements: 1.3, 1.7, 2.5. Success: obsolete stub-only and codex-only claims are removed or qualified, and attempt-history observability is documented with clear artifact terminology. Before coding, mark this task as in progress in tasks.md. After implementation, log the work with log-implementation, then mark the task complete in tasks.md._
