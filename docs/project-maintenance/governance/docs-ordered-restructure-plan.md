---
title: "Docs Ordered Restructure Plan"
status: active
updated: 2026-05-14
owner: aw-kernel
last_verified: 2026-05-14
---
# Docs Ordered Restructure Plan

This plan prepares future `docs/` restructuring work. It does not move, rename, delete, or rewrite broad document content in this worktrack.

## Objective

Make `docs/` read as an ordered manual instead of a pile of files. Future migration work should preserve the strengthened [Docs Book Spine](../../book.md), keep owner boundaries clear, and split content only after the target grouping and reader path are explicit.

## Current Grouping Model

The current top-level groups stay valid:

1. `docs/project-maintenance/`: repository maintenance, governance, deploy, testing, usage help, and onboarding.
2. `docs/harness/`: Harness doctrine, runtime protocol, scope, artifact contracts, skill catalog, workflow families, and design notes.
3. `docs/analysis/`: admitted analysis that is not yet stable truth.
4. `docs/ideas/`: uncommitted ideas and early drafts.
5. `docs/archive/`: superseded historical context.

The ordered restructure should keep this top-level grouping. The main problem is not top-level ownership; it is local ordering, duplicate reader paths, and unclear relationships between long-form governance, deploy, runtime protocol, artifact, and workflow documents.

## Relationship Rules

- `docs/book.md` is the full reading order and must direct readers through the whole docs tree.
- A directory `README.md` is a local chapter entrypoint. It should introduce local purpose, link the local sequence, and avoid duplicating canonical rule bodies.
- A non-README document is a rule, contract, runbook, plan, or analysis node. Each node needs exactly one nearest chapter owner.
- Cross-chapter dependencies should be explicit relative links in the dependent document. Reader order must not depend on path adjacency.
- Future migrations should preserve old-path intent through updated links or short migration notes before deleting obsolete references.

## Planned Restructure Slices

### Slice 1: Governance Chapter Sequencing

Goal: make `docs/project-maintenance/governance/` read in operational order.

Candidate order:

1. Review/verify handbook
2. Path governance checks
3. Docs ordered restructure plan
4. Language style
5. Branch/PR governance
6. Release operation and release channel governance
7. Release standard flow, pre-publish governance, and external trial governance

Acceptance for a future worktrack:

- `docs/project-maintenance/governance/README.md` presents the same local sequence.
- `docs/book.md` and the local README agree on governance ordering.
- Release documents keep a single owner and do not duplicate branch/PR or publish rules.

### Slice 2: Project Maintenance Operator Path

Goal: make project maintenance docs read from basic repo rules to operation.

Candidate order:

1. Foundations and root directory layering
2. Governance and review/verify
3. Deploy contracts and runbook
4. Testing command references
5. Usage help and onboarding

Acceptance for a future worktrack:

- Project-maintenance README groups links by operator workflow.
- Deploy, testing, and usage-help chapters clearly point to each other where operations depend on verification.
- The root docs path still begins from `docs/book.md`.

### Slice 3: Harness Doctrine To Runtime Path

Goal: make Harness docs read from doctrine to control execution.

Candidate order:

1. Foundations: doctrine, runtime protocol, split plan, dispatch policy, shared constraints
2. Scope: RepoScope/WorktrackScope state loop
3. Artifact contracts: repo, worktrack, control, standard fields
4. Catalog: skill inventory and impact matrix
5. Workflow families
6. Design notes

Acceptance for a future worktrack:

- `docs/harness/README.md` mirrors this progression.
- `Harness运行协议.md` stays current authority until split work moves protocol detail into focused chapters.
- Artifact contracts remain distinct from skill catalog and design analysis.

### Slice 4: Analysis, Ideas, And Archive Admission

Goal: make non-mainline material discoverable without becoming execution truth.

Acceptance for a future worktrack:

- Empty chapters remain explicitly empty in `docs/book.md` until content exists.
- New analysis, ideas, or archive material must state whether it is execution truth, decision input, uncommitted draft, or historical context.
- Admitted conclusions move into `project-maintenance/` or `harness/` with old entry cleanup.

### Slice 5: Stale Entrypoint And Duplicate Owner Cleanup

Goal: remove reader confusion after the first four slices define target order.

Acceptance for a future worktrack:

- Old entrypoints either point to the current owner or are removed.
- Duplicated owner statements are collapsed to one canonical location.
- `path_governance_check.py` and `governance_semantic_check.py` pass after each migration.

## Reader-Facing Dependencies

- `AGENTS.md` and `INDEX.md` remain the agent boot path and task router.
- `docs/README.md` remains a navigation entry, not a rule body.
- `docs/book.md` remains the full docs reading order.
- Local `README.md` files remain chapter entrypoints and must not conflict with the book order.
- `path_governance_check.py` is the machine guardrail for book reachability and explicit Full Reading Order coverage.

## Migration Risks

- A broad move can create stale links faster than review can catch them.
- Reordering without local README updates creates two competing reading paths.
- Moving Harness artifact or catalog pages can blur doctrine, contract, inventory, and design ownership.
- Release governance documents can duplicate branch, publish, and external trial rules unless owner boundaries are checked per slice.
- Empty `analysis/`, `ideas/`, and `archive/` chapters can attract scratch content unless admission rules are enforced.

## Non-Goals

- No file moves or renames in this planning worktrack.
- No broad content rewrite in this planning worktrack.
- No release, package, deploy target, or adapter behavior change.
- No milestone completion decision; final milestone acceptance remains programmer-owned.

## Future Worktrack Seed

Start with Slice 1 because it is the nearest governance path and has the smallest blast radius. Each later slice should be a separate worktrack with its own branch, closeout evidence, and reader-coherence note.
