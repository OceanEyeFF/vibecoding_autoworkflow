# Knowledge Base Skill Entrypoints

Load the canonical repo docs in this order.

## Always Read First

- `docs/knowledge/memory-side-baseline.md`
- `docs/knowledge/memory-side/knowledge-base.md`

## Read When You Need Maintenance Rules

- `docs/knowledge/memory-side/prompts/knowledge-base-adapter-prompt.md`

## Read When You Need Memory Side Boundaries

- `docs/knowledge/memory-side/skill-agent-model.md`

## Reading Policy

- The canonical truth lives in `docs/`, not in `toolchain/skills/`.
- Read only the minimum set of docs needed to determine `Bootstrap` vs `Adopt`, layer classification, and entrypoint fixes.
- Do not load `Context Routing` or `Writeback & Cleanup` docs unless the task explicitly crosses those boundaries.
