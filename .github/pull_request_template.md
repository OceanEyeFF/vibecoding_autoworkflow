## Summary

## Changes

## Verification
- [ ] `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/folder_logic_check.py`
- [ ] `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py`
- [ ] `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/governance_semantic_check.py`
- [ ] `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest toolchain/scripts/test`
- [ ] `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'`

## Risks

## Docs / Runbooks
- [ ] `docs/project-maintenance/governance/review-verify-handbook.md` updated when execution flow changes
- [ ] `docs/project-maintenance/foundations/root-directory-layering.md` updated when root-level layout changes
