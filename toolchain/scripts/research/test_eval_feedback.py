from __future__ import annotations

import unittest
from pathlib import Path

from common import RunSpec, normalize_eval_payload, parse_rubric_text
from run_skill_suite import parse_eval_output


class EvalFeedbackTest(unittest.TestCase):
    def test_normalize_eval_payload_keeps_task_scoped_dimension_feedback(self) -> None:
        payload = {
            "scores": {
                "path_contraction": 3,
                "entry_point_identification": 2,
                "avoidance_of_over_scanning": 3,
                "execution_usability": 2,
            },
            "dimension_feedback": {
                "path_contraction": {
                    "what_worked": "Scoped reading to docs and product only.",
                    "needs_improvement": "Stop condition should be stated more explicitly.",
                },
                "entry_point_identification": {
                    "what_worked": "Picked the main knowledge entrypoints first.",
                    "needs_improvement": "Should drop one lower-value secondary file.",
                },
                "unexpected_key": {
                    "what_worked": "ignore me",
                    "needs_improvement": "ignore me",
                },
            },
            "overall": "Good",
            "key_issues": ["Needs a tighter stop condition."],
            "key_strengths": ["Reading scope stayed narrow."],
            "source_format": "json",
        }

        normalized = normalize_eval_payload(
            task_name="context-routing",
            repo_name="typer",
            backend="codex",
            judge_backend="codex",
            payload=payload,
        )

        self.assertEqual(
            normalized["dimension_feedback"],
            {
                "path_contraction": {
                    "what_worked": "Scoped reading to docs and product only.",
                    "needs_improvement": "Stop condition should be stated more explicitly.",
                },
                "entry_point_identification": {
                    "what_worked": "Picked the main knowledge entrypoints first.",
                    "needs_improvement": "Should drop one lower-value secondary file.",
                },
            },
        )

    def test_parse_rubric_text_extracts_dimension_feedback(self) -> None:
        rubric = """
### [Dimension 1: Path Contraction]
**Score:** 3
**What Worked:** Tightened the scope to the smallest useful docs and code roots.
**Needs Improvement:** Could state the stop boundary in one shorter line.

---

### [Dimension 2: Entry Point Identification]
**Score:** 2
**What Worked:** Identified the two main entry docs correctly.
**Needs Improvement:** Still included one extra low-value file.

---

### [Dimension 3: Avoidance of Over-Scanning]
**Score:** 3
**What Worked:** Explicitly avoided repo-wide scanning.
**Needs Improvement:** Could name one more excluded area.

---

### [Dimension 4: Output Contract and Execution Usability]
**Score:** 2
**What Worked:** Returned a mostly usable Route Card.
**Needs Improvement:** Missing one contract field in the output shape.

### [Overall Feeling]
- Good

### [Key Issues]
- Stop condition could be tighter.

### [Key Strengths]
- Scope stayed narrow.

---

**Total Score:** 10 / 12
"""

        parsed = parse_rubric_text("context-routing", rubric)

        self.assertEqual(
            parsed["dimension_feedback"]["path_contraction"],
            {
                "what_worked": "Tightened the scope to the smallest useful docs and code roots.",
                "needs_improvement": "Could state the stop boundary in one shorter line.",
            },
        )
        self.assertEqual(
            parsed["dimension_feedback"]["execution_usability"],
            {
                "what_worked": "Returned a mostly usable Route Card.",
                "needs_improvement": "Missing one contract field in the output shape.",
            },
        )

    def test_parse_rubric_text_ignores_placeholder_dimension_feedback(self) -> None:
        rubric = """
### [Dimension 1: Path Contraction]
**Score:** 3
**What Worked:** ...
**Needs Improvement:** ...

### [Overall Feeling]
- Good
"""

        parsed = parse_rubric_text("context-routing", rubric)

        self.assertEqual(parsed["dimension_feedback"], {})

    def test_parse_eval_output_requires_complete_dimension_feedback(self) -> None:
        spec = RunSpec(
            repo_path=Path("/tmp/typer"),
            task="context-routing",
            prompt_file=Path("/tmp/prompt.md"),
            eval_prompt_file=Path("/tmp/eval.md"),
            backend="codex",
            judge_backend="codex",
            with_eval=True,
        )

        payload = """
{
  "skill": "context-routing",
  "repo": "typer",
  "backend": "codex",
  "judge_backend": "codex",
  "scores": {
    "path_contraction": 3,
    "entry_point_identification": 2,
    "avoidance_of_over_scanning": 3,
    "execution_usability": 2
  },
  "dimension_feedback": {
    "path_contraction": {
      "what_worked": "Tight scope.",
      "needs_improvement": "State stop condition."
    }
  },
  "total_score": 10,
  "max_score": 12,
  "overall": "Good",
  "key_issues": ["Stop condition could be clearer."],
  "key_strengths": ["Scope stayed narrow."],
  "source_format": "json"
}
"""

        normalized, parse_error = parse_eval_output(spec, payload)

        self.assertIsNotNone(normalized)
        self.assertEqual(
            parse_error,
            "Structured eval output did not contain complete dimension feedback.",
        )


if __name__ == "__main__":
    unittest.main()
