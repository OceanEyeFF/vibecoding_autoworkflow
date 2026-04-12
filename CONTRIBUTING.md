# Contributing

This repository is a repo-side contract layer. Keep contributions narrow, explicit, and aligned to the governance rules.

## Default Workflow

1. Create a branch for the change.
2. Use a pull request for review and merge.
3. Run the minimal governance checks before requesting review.

## Required Checks (Local)

Run these before requesting review:

```bash
python toolchain/scripts/test/folder_logic_check.py
python toolchain/scripts/test/path_governance_check.py
python toolchain/scripts/test/governance_semantic_check.py
python -m pytest toolchain/scripts/test/test_folder_logic_check.py toolchain/scripts/test/test_closeout_gate_tools.py
```

## Review Expectations

- Follow `docs/project-maintenance/governance/review-verify-handbook.md`.
- If you touch governance rules, update the matching docs and checks in the same PR.
- If you introduce a new root-level object, update `docs/project-maintenance/foundations/root-directory-layering.md` and folder logic checks.

## PR / Branch Rules

See `docs/project-maintenance/governance/branch-pr-governance.md` for the branch model, PR requirements, and CI expectations.
