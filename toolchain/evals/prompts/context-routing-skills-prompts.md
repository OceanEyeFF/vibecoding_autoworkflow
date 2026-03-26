# Context Routing Skill Evaluation Prompt

Use this rubric to evaluate one `context-routing-skill` response.

Evaluation rules:
- Use only the response under evaluation.
- Score every dimension with `1`, `2`, or `3`. Do not use half scores.
- Penalize missing required fields instead of inferring intent.
- Focus on correctness, boundary control, and next-step usability, not writing style.
- If the captured output contains tool chatter or a failure string, score only the final usable answer. If there is no usable answer, score the relevant dimensions as `1`.
- For each dimension, fill `What Worked` and `Needs Improvement` with one short, concrete sentence.
- Return the completed rubric only.

---

## [Skill Name]: context-routing-skill

## [Test Case]: Task context routing and path limitation

## [Response Under Evaluation]
Paste the captured skill output below before running this evaluation.

```text
{{TEST_OUTPUT}}
```

### [Dimension 1: Path Contraction]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Fails to reduce reading scope, attempts to scan the whole repository, or expands into broad irrelevant areas
- **2 (Partial):** Reduces scope somewhat but still includes avoidable files, directories, or reading branches
- **3 (Excellent):** Narrows reading scope to the smallest useful area and clearly avoids unnecessary exploration

**Notes:**
- Does the response effectively reduce the reading scope?
- Is the contraction strategy tight rather than generic?
- Does it avoid unnecessary exploration?

**What Worked:** ...
**Needs Improvement:** ...

---

### [Dimension 2: Entry Point Identification]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Identifies incorrect, irrelevant, or missing entry docs/files
- **2 (Partial):** Identifies some correct entry points but misses key ones or includes extras
- **3 (Excellent):** Accurately identifies the most relevant docs and code entrypoints for starting the task

**Notes:**
- Are the entry docs/files correctly identified?
- Does it prioritize the most relevant entry points?
- Is the reasoning for entry point selection sound?

**What Worked:** ...
**Needs Improvement:** ...

---

### [Dimension 3: Avoidance of Over-Scanning]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Shows clear whole-repo or broad-scan behavior
- **2 (Partial):** Mostly focused but still includes some unnecessary exploration
- **3 (Excellent):** Maintains strict reading discipline and clearly excludes irrelevant areas

**Notes:**
- Is there evidence of "scan everything" behavior?
- Does the response demonstrate restraint in exploration?
- Are irrelevant areas explicitly excluded?

**What Worked:** ...
**Needs Improvement:** ...

---

### [Dimension 4: Output Contract and Execution Usability]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Output is vague, incomplete, or does not function as a usable `Route Card`
- **2 (Partial):** Output is somewhat actionable but misses contract fields or lacks clarity
- **3 (Excellent):** Output is clear, actionable, and matches the expected `Route Card` shape closely enough to drive next steps

**Notes:**
- Does the answer include the expected `Route Card` fields such as `read_first`, `read_next`, `code_entry`, `do_not_read_yet`, and `stop_reading_when`?
- Can the output be used directly for next steps?
- Is the guidance specific and actionable?

**What Worked:** ...
**Needs Improvement:** ...

---

### [Overall Feeling]
- **Bad / Okay / Good**

### [Key Issues]
- ...

### [Key Strengths]
- ...

---

**Total Score:** ___ / 12
