# Task Batching Pattern

This file extracts the stable multi-task batching logic from the legacy task-list workflow prompt.

## Role

- decide when a repo-evolution worktrack must become a multi-task flow
- define the minimum planning artifacts required before batched execution starts
- define how task-level execution rolls up into one integration verdict

## Use this pattern when

- the source request contains two or more executable tasks
- tasks have explicit dependencies, sequencing, or parallelization needs
- integration must judge the combined state, not just isolated task outputs

## Required planning artifacts

- task inventory with ids, titles, source locations, priorities, and unknowns
- task execution matrix using `product/harness/core/contracts/task-planning-contract.template.md`
- dependency graph
- batch order
- parallel task groups
- high-risk task list

## Stable execution rules

- detect task count before choosing the workflow shape
- tasks inside one batch may execute in parallel; batches execute in order
- every task must report status, changed files, validation, and residual risks
- integration verify must happen after batch execution and before closeout
- do not silently downgrade a multi-task request into a single-task flow once batching is required

## Integration requirements

- the integration state must run the required gates for the combined change set
- unresolved P0 or equivalent blocking risk prevents a pass verdict
- failures return the worktrack to recovery or targeted repair, not to silent partial completion
