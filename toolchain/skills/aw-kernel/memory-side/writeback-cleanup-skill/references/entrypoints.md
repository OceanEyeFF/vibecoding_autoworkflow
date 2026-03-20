# Writeback Cleanup Skill Entrypoints

Load the canonical repo docs in this order.

## Always Read First

- `docs/knowledge/memory-side-baseline.md`
- `docs/knowledge/memory-side/writeback-cleanup.md`

## Read For Writeback Logic

- `docs/knowledge/memory-side/writeback-cleanup-rules.md`

## Read Before Finalizing Output

- `docs/knowledge/memory-side/formats/writeback-cleanup-output-format.md`
- `docs/knowledge/memory-side/prompts/writeback-cleanup-adapter-prompt.md`

## Read Only If Layer Boundaries Are Unclear

- `docs/knowledge/memory-side/knowledge-base.md`
- `docs/knowledge/memory-side/skill-agent-model.md`

## Reading Policy

- The canonical writeback rules live in `docs/`, not in this skill folder.
- Load only the minimum set of docs required to place verified facts into the right layer.
- Do not pull task-entry routing material into closeout unless the task explicitly asks for end-to-end analysis.
