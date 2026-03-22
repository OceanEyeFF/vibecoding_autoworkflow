# Memory Side Auto Research Program

This file is the editable baseline program for Auto Research-style prompt and
adapter benchmarking in this repository.

The goal is not to rewrite project truth. The goal is to improve how Codex and
Claude use the current Memory Side adapter sources and repo-local deploy
targets under fixed benchmark scenarios.

## Scope

In scope for experimentation:

- `docs/knowledge/memory-side/prompts/`
- `product/memory-side/adapters/`
- `.agents/skills/`
- `.claude/skills/`
- `toolchain/evals/memory-side/`

Out of scope for benchmark-time mutation:

- `docs/knowledge/` as the project truth layer
- `product/memory-side/skills/` as the canonical skill source layer
- the benchmark schemas and scenario IDs as the stable measurement surface

## Fixed Invariants

These must remain true in every benchmark run:

- Project truth stays in `docs/knowledge/`
- Canonical skill semantics stay in `product/memory-side/skills/`
- Repo-local mounts stay in `.agents/skills/` and `.claude/skills/`
- Prompts and adapters are implementation layers, not truth layers
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
