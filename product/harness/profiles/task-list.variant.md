# Task List Variant

This file extracts the stable task-list variant from the legacy task-list workflow prompt.

## Role

- multi-task profile layered on top of the standard repo-evolution worktrack
- tighten planning, batching, and integration requirements when one request contains multiple executable tasks

## Selection rule

- select this variant only after task detection proves the request contains two or more executable tasks

## Stable variant rules

- planning must include a task inventory and execution matrix
- batch order and parallel groups must be explicit before execution starts
- each task must return status, changed files, validation, and residual risks
- final acceptance is judged at integration level, not by per-task local success alone

## Relationship to other sources

- workflow skeleton: `../workflows/repo-evolution/standard-worktrack.workflow.md`
- batching pattern: `../workflows/repo-evolution/task-batching.pattern.md`
- planning template: `../core/contracts/task-planning-contract.template.md`
