# Task Contract Skill Evaluation Prompt

Use this rubric to evaluate one `task-contract-skill` response.

Evaluation rules:
- Use only the response under evaluation.
- Score every dimension with `1`, `2`, or `3`. Do not use half scores.
- Penalize guessed facts, missing boundaries, and solution leakage instead of assuming intent.
- Because the current test flow is non-interactive, do not reward follow-up questioning. Reward clear handling of uncertainty through `pending`, `Open Decisions`, or equivalent sections.
- Return the completed rubric only.

---

## [Skill Name]: task-contract-skill

## [Test Case]: Transforming vague requirements into structured contracts

## [Response Under Evaluation]
Paste the captured skill output below before running this evaluation.

```text
{{TEST_OUTPUT}}
```

### [Dimension 1: Structuring Ability (Contract Quality)]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Fails to create a clear, structured contract; remains vague or incomplete
- **2 (Partial):** Creates some structure but lacks clarity, completeness, or proper formatting
- **3 (Excellent):** Produces a clear, stable contract structure that is easy to consume downstream

**Notes:**
- Is the contract structure clear and logical?
- Does it cover the essential parts of the task?
- Is the formatting consistent enough to act as a reusable contract?

---

### [Dimension 2: Boundary Definition]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Fails to define clear scope boundaries; scope is ambiguous or overly broad
- **2 (Partial):** Defines some boundaries but leaves important aspects unclear
- **3 (Excellent):** Clearly defines in-scope and out-of-scope boundaries with precision

**Notes:**
- Are task boundaries clearly defined?
- Is the scope appropriately bounded?
- Does it avoid scope creep and ambiguity?

---

### [Dimension 3: Project Context Integration]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Ignores project context or makes unsupported assumptions
- **2 (Partial):** Uses some project context but misses important repo-specific factors
- **3 (Excellent):** Integrates repository context appropriately without overreaching beyond evidence

**Notes:**
- Does it analyze the project context properly?
- Are repo-specific constraints or observations included where supported?
- Is the contract tailored to the specific repository rather than generic?

---

### [Dimension 4: Avoidance of Solution Leakage]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Leaks implementation details or precommits to specific solutions inside the contract
- **2 (Partial):** Mostly avoids solution leakage but still includes some implementation-oriented language
- **3 (Excellent):** Stays problem-focused and avoids unnecessary implementation commitments

**Notes:**
- Does the contract focus on the problem rather than the solution?
- Are there implementation details or specific solutions mentioned without need?
- Is the language appropriately abstract and contract-oriented?

---

### [Dimension 5: Uncertainty Handling]
**Score:** 1 / 2 / 3

**Scoring Criteria:**
- **1 (Poor):** Guesses missing facts, leaves ambiguity hidden, or depends on follow-up questions to function
- **2 (Partial):** Acknowledges some uncertainty but does not separate it cleanly from confirmed facts
- **3 (Excellent):** Clearly separates confirmed facts from pending items or open decisions without guessing

**Notes:**
- Are unresolved items clearly marked?
- Does the response avoid pretending ambiguity is resolved?
- Can the contract still be consumed even when some items remain pending?

---

### [Overall Feeling]
- **Bad / Okay / Good**

### [Key Issues]
- ...

### [Key Strengths]
- ...

---

**Total Score:** ___ / 15
