# Writeback Cleanup Skill Evaluation Prompt

Use this rubric to evaluate one `writeback-cleanup-skill` response.

Evaluation rules:
- Use only the response under evaluation.
- Score every dimension with `1`, `2`, or `3`. Do not use half scores.
- Penalize unsupported claims, incorrect writeback targets, and weak cleanup recommendations.
- Reward explicit verification boundaries and clear separation between verified changes and non-writeback material.
- Return the completed rubric only.

---

## [Skill Name]: writeback-cleanup-skill

## [Test Case]: Truth writeback and garbage cleanup operations

## [Response Under Evaluation]
Paste the captured skill output below before running this evaluation.

```text
{{TEST_OUTPUT}}
```

### [Dimension 1: Change Identification Accuracy]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Fails to identify relevant changes, misses important modifications, or invents changes not supported by the response
- **2 (Partial):** Identifies some relevant changes but misses key modifications or includes weak extras
- **3 (Excellent):** Accurately identifies relevant changes with clear separation from non-changes

**Notes:**
- Are the changes correctly identified?
- Does it capture the important modifications?
- Is there evidence of false positives or false negatives?

---

### [Dimension 2: Verification Awareness]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Makes claims without verification and does not distinguish evidence from assumption
- **2 (Partial):** Shows some verification discipline but still relies on assumptions for important points
- **3 (Excellent):** Clearly distinguishes verified information, unverified items, and assumptions

**Notes:**
- Does it distinguish between verified and assumed information?
- Are assumptions clearly labeled?
- Is the verification basis explicit enough to justify writeback decisions?

---

### [Dimension 3: Writeback Target Correctness]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Confuses writeback targets or recommends writing to clearly incorrect locations
- **2 (Partial):** Generally correct but has some weak or uncertain target placement
- **3 (Excellent):** Correctly identifies what belongs in core truth, operational truth, or no writeback at all

**Notes:**
- Are writes directed to the correct locations?
- Does it distinguish between core truth, operational docs, and `do_not_write_back` material?
- Is the location selection aligned with repository conventions?

---

### [Dimension 4: Cleanup Quality]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Fails to identify stale information, proposes weak cleanup, or removes the wrong things
- **2 (Partial):** Identifies some cleanup targets but misses important stale material or lacks prioritization
- **3 (Excellent):** Identifies meaningful stale content, preserves valid material, and proposes focused cleanup actions

**Notes:**
- Is stale information properly identified?
- Does it preserve content that is still valid?
- Are cleanup targets concrete and useful?

---

### [Overall Feeling]
- **Bad / Okay / Good**

### [Key Issues]
- ...

### [Key Strengths]
- ...

---

**Total Score:** ___ / 12
