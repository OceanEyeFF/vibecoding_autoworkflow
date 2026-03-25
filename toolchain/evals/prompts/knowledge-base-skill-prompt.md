# Knowledge Base Skill Evaluation Prompt

Use this rubric to evaluate one `knowledge-base-skill` response.

Evaluation rules:
- Use only the response under evaluation.
- Score every dimension with `1`, `2`, or `3`. Do not use half scores.
- Penalize missing classification, missing entrypoints, and overbuilt recommendations instead of assuming they were implied.
- Focus on documentation-system judgment, structural fit, and minimum-safe change behavior.
- Return the completed rubric only.

---

## [Skill Name]: knowledge-base-skill

## [Test Case]: Documentation system correctness and structure modeling

## [Response Under Evaluation]
Paste the captured skill output below before running this evaluation.

```text
{{TEST_OUTPUT}}
```

### [Dimension 1: Mode and Layer Modeling]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Fails to determine repository state correctly or mixes documentation layers without control
- **2 (Partial):** Shows some correct mode/layer judgment but has inconsistencies or weak separation
- **3 (Excellent):** Correctly identifies repository state and models documentation layers with clear separation

**Notes:**
- Does the response correctly determine `Bootstrap` vs `Adopt` when enough evidence exists?
- Are content layers clearly distinguished?
- Is the structure consistent with repository conventions rather than generic doc advice?

---

### [Dimension 2: Mainline Entrypoint Identification]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Fails to identify meaningful documentation entrypoints or suggests irrelevant ones
- **2 (Partial):** Identifies some useful entrypoints but misses key ones or includes unnecessary ones
- **3 (Excellent):** Accurately identifies the most important entrypoints for documentation navigation and maintenance

**Notes:**
- Are the main entrypoints correctly identified?
- Does it distinguish mainline entrypoints from secondary material?
- Is the entrypoint prioritization sound?

---

### [Dimension 3: Minimal Modification Principle]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Over-engineers the repo or recommends a broad rewrite without strong evidence
- **2 (Partial):** Generally restrained but still includes some unnecessary additions or restructuring
- **3 (Excellent):** Recommends only the smallest safe doc updates required by the observed repo state

**Notes:**
- Does the response avoid overbuilding?
- Are changes minimal and focused?
- Is there evidence of restraint in modifications?

---

### [Dimension 4: Alignment with Existing Repo]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Ignores or conflicts with the repository's existing structure and conventions
- **2 (Partial):** Partially aligns but still imposes outside structure in some places
- **3 (Excellent):** Aligns tightly with existing repository patterns, conventions, and terminology

**Notes:**
- Does it respect existing repository conventions?
- Is it consistent with current documentation patterns?
- Would the proposed changes integrate cleanly into the repo?

---

### [Overall Feeling]
- **Bad / Okay / Good**

### [Key Issues]
- ...

### [Key Strengths]
- ...

---

**Total Score:** ___ / 12
