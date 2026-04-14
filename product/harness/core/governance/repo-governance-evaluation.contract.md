# Repo Governance Evaluation Contract

This file extracts the stable evaluation structure from the legacy governance-evaluation prompt.

## Step 1: Repository Type

Choose exactly one:

- `prototype`
- `small_product`
- `long_term_product`
- `platform_infrastructure`

The verdict must include evidence-backed reasoning.

## Step 2: Score Five Dimensions

Each dimension is scored `0-5`:

- `Baseline Hygiene`
- `Change Governance`
- `Automation`
- `Structural Clarity`
- `Operational Maintainability`

`Change Governance` remains the highest-priority dimension.

## Step 3: Overall Rating

- Total score: `X / 25`
- Rating bands:
  - `22-25`: 工业级
  - `16-21`: 可用
  - `10-15`: 技术债明显
  - `<10`: 不可维护

## Step 4: Required Evidence

- Every dimension must cite concrete files, directories, commands, or PR evidence.
- Empty or generic judgments are invalid.

## Step 5: High-Priority Problems

- Output the top 5 issues with the largest long-term maintenance impact.

## Step 6: 30-Day Improvements

- Output at most 3 recommendations.
- Recommendations must emphasize high ROI and governance lift.

## Step 7: AI / Harness Compatibility

Assess:

- task decomposition
- local context comprehension
- automated verification capability
- safe modification capability

Output one verdict:

- `YES`
- `PARTIAL`
- `NO`
