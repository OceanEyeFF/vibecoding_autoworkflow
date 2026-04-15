# Rule Check Skill Entrypoints

Load the Harness rule-check docs in this order.

## Always Read First

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `docs/project-maintenance/governance/review-verify-handbook.md`
- `docs/harness/foundations/Harness运行协议.md`
- `docs/harness/scope/worktrack-scope.md`
- `docs/harness/artifact/worktrack/gate-evidence.md`

## Read If This Round Touches Governance-Sensitive Surfaces

- `docs/project-maintenance/governance/path-governance-checks.md`
- `docs/project-maintenance/governance/branch-pr-governance.md`

## Read If The Rule Check Needs A Stronger Task Boundary

- `docs/harness/adjacent-systems/task-interface/task-contract.md`

## Read Only If The Current Worktrack Actually Depends On Adjacent Systems

- `docs/harness/adjacent-systems/memory-side/overview.md`
- `docs/harness/adjacent-systems/memory-side/layer-boundary.md`

## Reading Policy

- This skill collects rule/governance evidence for `WorktrackScope.verifying`; it is not the final `gate-skill`.
- Start from the current diff surface and verification requirements, then load only the rule sources and governance docs that are actually triggered by this round.
- If you use a `gpt-5.4-xhigh` `SubAgent` as the reasoning carrier, pass only a bounded `Rule Check Info Packet`:
  - current worktrack identity and goal
  - changed paths and affected layers
  - current in-scope and out-of-scope boundaries
  - applicable governance rules and required sync items
  - available verify outputs and open policy questions
- Prefer the minimum applicable governance checks for this round rather than broad rediscovery.
- Return collected policy evidence, violations, and missing evidence for later gate use; do not adjudicate the final policy verdict here.
