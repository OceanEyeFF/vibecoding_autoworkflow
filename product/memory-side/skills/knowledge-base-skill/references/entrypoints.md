# Knowledge Base Skill Entrypoints

Load the generic Memory Side contract docs in this order.

## Always Read First

- `docs/deployable-skills/memory-side/layer-boundary.md`
- `docs/deployable-skills/memory-side/overview.md`
- `docs/deployable-skills/memory-side/knowledge-base.md`

## Read When You Need Memory Side Boundaries

- `docs/deployable-skills/memory-side/skill-agent-model.md`

## Reading Policy

- The canonical truth lives in `docs/`, not in this skill source folder.
- Stay in the generic contract layer unless the task explicitly asks for repo-local adapter or eval material.
- Read only the minimum set of docs needed to determine `Bootstrap` vs `Adopt`, the layer classification, and the entrypoint fixes.
- Do not load `Context Routing` or `Writeback & Cleanup` docs unless the task explicitly crosses those boundaries.
