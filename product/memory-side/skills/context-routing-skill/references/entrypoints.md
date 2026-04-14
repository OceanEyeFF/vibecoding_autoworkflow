# Context Routing Skill Entrypoints

Load the generic Memory Side contract docs in this order.

## Always Read First

- `docs/harness/adjacent-systems/memory-side/layer-boundary.md`
- `docs/harness/adjacent-systems/memory-side/overview.md`
- `docs/harness/adjacent-systems/memory-side/context-routing.md`

## Read For Routing Logic

- `docs/harness/adjacent-systems/memory-side/context-routing-rules.md`
- `docs/harness/adjacent-systems/memory-side/formats/context-routing-output-format.md`

## Read Only If Boundaries Are Unclear

- `docs/harness/adjacent-systems/memory-side/knowledge-base.md`
- `docs/harness/adjacent-systems/memory-side/skill-agent-model.md`

## Reading Policy

- The canonical route rules live in `docs/`, not in this skill source folder.
- Stay in the generic contract layer unless the task explicitly asks for repo-local adapter or eval material.
- Load the minimum set of docs needed to generate the current `Route Card`.
- Do not read `Writeback & Cleanup` docs during task entry unless the task explicitly asks for closeout behavior.
