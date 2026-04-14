# Standard Worktrack Workflow

This file extracts the stable repo-evolution worktrack skeleton from the legacy workflow prompts.

## Role

- canonical workflow skeleton for repo-evolution tasks
- bridge `Task Interface` inputs to Harness core contracts, governance, and closeout
- define the minimum phase order that profile variants may tighten but must not bypass

## Required inputs

- task contract from `docs/harness/adjacent-systems/task-interface/task-contract.md`
- execution contract from `product/harness/core/contracts/execution-contract.template.md`
- harness contract metadata from `product/harness/core/contracts/harness-contract.template.json`
- applicable governance fields from `product/harness/core/governance/harness-governance-fields.md`

## Minimum sequence

1. freeze goal, non-goals, scope, acceptance, risks, and validation requirements
2. choose the execution profile or workflow variant
3. initialize worktrack contract and any required task queue
4. dispatch implementation or review work
5. collect evidence and run verify
6. judge gate results and residual risk
7. recover on failure, or integrate and close on pass
8. write back verified state to repo truth layers

## Stable boundary rules

- do not enter implementation before the execution boundary is frozen
- do not close a worktrack without evidence-backed verify output
- workflow variants may add phases, but they must not skip gate judgment or recovery handling
- runtime state stays in repo-local state and must not be written back into canonical product source

## Current companion sources

- `task-batching.pattern.md`
- `review-repair.loop.md`
- `../../profiles/simple.profile.md`
- `../../profiles/strict.profile.md`
- `../../profiles/task-list.variant.md`
