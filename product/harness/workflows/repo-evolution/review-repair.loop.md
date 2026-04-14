# Review Repair Loop

This file extracts the stable review and repair loop from the legacy review-loop workflow prompt.

## Role

- run a bounded inspect-fix-recheck loop against a commit, PR, diff range, or target path
- prioritize correctness, regression risk, and test gaps before documentation polish
- keep repair scope anchored to the reviewed delta and its direct impact area

## Required loop roles

- controller: freezes review scope and decides whether to continue
- inspector: finds issues and produces evidence-backed findings
- fixer: repairs only the confirmed issue set
- meta-reviewer: checks review quality, missed-risk hypotheses, and stop conditions

## Stable phase order

1. freeze review scope against the target diff
2. inspect and record findings with severity and evidence
3. freeze the fix scope
4. repair in an isolated execution context
5. run verify on the repaired state
6. perform directed re-review on the repaired result
7. decide stop or continue

## Stable boundary rules

- do not expand a review loop into an unrelated refactor
- unresolved source or dirty scope conflict stops the loop
- at least one post-fix re-review is required before the loop may close
- final integration state must come from the integration context, not from an arbitrary fix branch

## Required outputs

- review findings and severities
- fixed, unfixed, and blocked issues
- validation per fix
- next-round checklist or explicit stop recommendation
