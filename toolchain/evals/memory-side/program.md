# Memory Side Auto Research Program

This file is the editable baseline program for Auto Research-style prompt and
adapter benchmarking in this repository.

The goal is not to rewrite project truth. The goal is to improve how Codex and
Claude use the existing Memory Side assets under fixed benchmark scenarios.

## Scope

In scope for experimentation:

- `docs/knowledge/memory-side/prompts/`
- `.agents/skills/`
- `.claude/skills/`
- `toolchain/evals/memory-side/`

Out of scope for benchmark-time mutation:

- `docs/knowledge/` as the project truth layer
- `toolchain/skills/aw-kernel/memory-side/` as the canonical skill layer
- the benchmark schemas and scenario IDs as the stable measurement surface

## Fixed Invariants

These must remain true in every benchmark run:

- Project truth stays in `docs/knowledge/`
- Canonical skill semantics stay in `toolchain/skills/aw-kernel/memory-side/`
- Prompts and wrappers are adapter layers, not truth layers
- The current Memory Side surface remains the same three skills
- Backend differences may change phrasing or invocation, not the contract

## Core Questions

The benchmark should keep pushing on these questions:

- Did the backend choose the correct Memory Side skill for the task?
- Did it read the minimum docs needed before answering?
- Did it preserve the canonical output contract?
- Did it avoid whole-repo scanning?
- Did it keep speculative claims out of truth-facing answers?
- Did it keep the Codex and Claude capability boundaries aligned?

Skill-specific questions:

- `knowledge-base-skill`
  - Did it classify `Bootstrap` vs `Adopt` correctly?
  - Did it separate `Core Truth`, `Operational Truth`, `Exploratory Records`,
    and `Archive` correctly?
  - Did it recommend the smallest safe entrypoint repairs instead of a rewrite?

- `context-routing-skill`
  - Did it produce a minimal `Route Card`?
  - Did it point to exact doc and code entrypoints?
  - Did it explicitly list `do_not_read_yet` boundaries?
  - Did it stop before turning routing into an execution plan?
  - Did it keep `read_first` anchored on the routing baseline instead of
    front-loading sibling partitions?

- `writeback-cleanup-skill`
  - Did it separate verified changes from unverified guesses?
  - Did it map writeback to the correct truth layer?
  - Did it clearly list `do_not_write_back` and `cleanup_targets`?
  - Did it tie every writeback claim to a verification basis?

## Routing Heuristics

Use these heuristics to keep the benchmark stable:

- For `context-routing-skill`, default `read_first` to:
  - `docs/knowledge/memory-side-baseline.md`
  - `docs/knowledge/memory-side/context-routing.md`
- Keep sibling partition docs such as `knowledge-base.md` and
  `writeback-cleanup.md` out of `read_first` unless the routing baseline is
  still insufficient after reading the two files above.
- For documentation tasks, prefer partition docs and routing rules before
  prompt drafts, wrapper folders, or eval assets.
- For code-adjacent tasks, keep the same routing baseline in `read_first`, then
  move to exact runner functions, exact schemas, and exact scoring files in
  `read_next` or `code_entry`.
- `read_next` should add the smallest supporting files that sharpen the current
  task. It should not repeat baseline material or widen into unrelated
  partitions unless a boundary decision truly depends on them.

## Benchmark Discipline

- Evaluation runs are read-only. Do not edit repo files during a benchmark.
- Read only the minimum repo files needed for the scenario.
- Do not install packages, create commits, or open network-dependent workflows.
- Return only the final JSON object that matches the supplied schema.
- Include every schema key in the final JSON. If a field is optional in the
  canonical docs but not needed for this case, use an empty array or a short
  empty string instead of omitting it.
- If the scenario is underspecified, be conservative and state the minimum gap.
