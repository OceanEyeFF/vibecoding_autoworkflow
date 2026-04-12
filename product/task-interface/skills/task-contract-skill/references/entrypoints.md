# Task Contract Skill Entrypoints

Load the generic Task Interface contract docs in this order.

## Always Read First

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `docs/deployable-skills/task-interface/task-contract.md`
- `docs/deployable-skills/task-interface/task-contract.md`

## Read Only If Task Interface Touches Memory Side

- `docs/deployable-skills/memory-side/overview.md`
- `docs/deployable-skills/memory-side/skill-agent-model.md`

## Reading Policy

- The canonical Task Contract rules live in `docs/`, not in this skill source folder.
- Stay in the Task Interface layer unless the task explicitly crosses into `Memory Side`.
- Load the minimum set of docs needed to produce the current `Task Contract`.
- Do not read repo-local deploy targets during canonical Task Contract generation.
