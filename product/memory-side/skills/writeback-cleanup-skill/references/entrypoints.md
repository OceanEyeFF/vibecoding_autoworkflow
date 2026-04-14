# Writeback Cleanup Skill Entrypoints

Load the generic Memory Side contract docs in this order.

## Always Read First

- `docs/harness/adjacent-systems/memory-side/layer-boundary.md`
- `docs/harness/adjacent-systems/memory-side/overview.md`
- `docs/harness/adjacent-systems/memory-side/writeback-cleanup.md`

## Read For Writeback Logic

- `docs/harness/adjacent-systems/memory-side/writeback-cleanup-rules.md`
- `docs/harness/adjacent-systems/memory-side/formats/writeback-cleanup-output-format.md`

## Read Only If Layer Boundaries Are Unclear

- `docs/harness/adjacent-systems/memory-side/knowledge-base.md`
- `docs/harness/adjacent-systems/memory-side/skill-agent-model.md`

## Reading Policy

- The canonical writeback rules live in `docs/`, not in this skill folder.
- Stay in the generic contract layer unless the task explicitly asks for repo-local adapter or eval material.
- Load only the minimum set of docs required to place verified facts into the right layer.
- Do not pull task-entry routing material into closeout unless the task explicitly asks for end-to-end analysis.
