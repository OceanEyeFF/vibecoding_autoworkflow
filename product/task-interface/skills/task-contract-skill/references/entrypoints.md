# Task Contract Skill Entrypoints

Load the generic Task Interface contract docs in this order.

## Always Read First

- `docs/knowledge/foundations/partition-model.md`
- `docs/knowledge/foundations/task-contract-template.md`
- `docs/knowledge/task-interface/task-contract.md`

## Read For Skill Boundaries

- `docs/knowledge/task-interface/skills/task-contract-skill.md`

## Read Only If Task Interface Touches Memory Side

- `docs/knowledge/memory-side/overview.md`
- `docs/knowledge/memory-side/skill-agent-model.md`

## Reading Policy

- The canonical Task Contract rules live in `docs/`, not in this skill source folder.
- Stay in the Task Interface layer unless the task explicitly crosses into `Memory Side`.
- Load the minimum set of docs needed to produce the current `Task Contract`.
- Do not read repo-local deploy targets during canonical Task Contract generation.
