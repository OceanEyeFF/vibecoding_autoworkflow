# Gate Skill Entrypoints

Load the Harness worktrack gate docs in this order.

## Always Read First

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `docs/harness/foundations/Harness运行协议.md`
- `docs/harness/scope/worktrack-scope.md`
- `docs/harness/artifact/worktrack/contract.md`
- `docs/harness/artifact/worktrack/plan-task-queue.md`
- `docs/harness/artifact/worktrack/gate-evidence.md`
- `docs/harness/artifact/control/control-state.md`

## Read If Gate Needs A Stronger Execution-Boundary Check

- `docs/harness/adjacent-systems/task-interface/task-contract.md`

## Read Only If The Current Evidence Crosses Adjacent Systems

- `docs/harness/adjacent-systems/memory-side/overview.md`
- `docs/harness/adjacent-systems/memory-side/layer-boundary.md`
- `docs/harness/adjacent-systems/memory-side/skill-agent-model.md`

## Reading Policy

- This skill is for gate adjudication from existing evidence, not for execution, recovery, or repo refresh.
- Start from the current `Gate Evidence` packet, then load only the additional contract or control-state context needed to judge this round.
- Package a bounded context packet for one `gpt-5.4-xhigh` `SubAgent`.
- Include only the context needed to adjudicate:
  - current worktrack identity
  - current round trigger
  - contract and acceptance summary
  - queue state relevant to the disputed or pending judgment
  - implementation, validation, and policy evidence
  - known evidence gaps, conflicts, or unresolved issues
- Do not reopen full execution discovery when the current evidence packet is already sufficient.
- Apply low-severity absorption before overall verdicting: duplicated or single-surface `P2 / P3` residue should stay residual unless it crosses the documented escalation fence.
- If the packet contains `possible_upstream_constraint_issue`, judge whether the route must move to rule-check, contract/doc repair, or worktrack recovery instead of another pure code-fix request.
- If evidence is missing or contradictory, return that in the verdict; do not silently synthesize a pass.
- Return allowed next routes and review guidance, not the downstream execution plan itself.
