# Simple Profile

This file extracts the stable single-task minimal execution profile from the legacy simple workflow prompt.

## Use this profile when

- the request resolves to one bounded task
- the execution path does not require batching or staged review loops
- the validation path is straightforward enough to stay in one execution line

## Stable profile rules

- freeze one execution contract before implementation starts
- stay on the smallest read set that can support the task
- treat extra opportunistic changes as out of scope unless explicitly approved
- escalate to another workflow shape when the task proves to be multi-part or review-driven

## Minimum evidence set

- execution contract summary
- changed files
- completion state
- verify output for the required gates
- residual risk report

## Escalation triggers

- more than one executable task emerges
- scope freeze becomes unstable
- review/repair becomes the dominant control loop
