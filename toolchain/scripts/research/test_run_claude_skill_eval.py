from __future__ import annotations

import unittest

from run_claude_skill_eval import build_forward_args, parse_args


class RunClaudeSkillEvalForwardingTest(unittest.TestCase):
    def test_build_forward_args_omits_judge_backend_without_eval(self) -> None:
        args = parse_args(["--repo", "typer", "--task", "context-routing"])

        forwarded = build_forward_args(args)

        self.assertNotIn("--judge-backend", forwarded)
        self.assertNotIn("--with-eval", forwarded)

    def test_build_forward_args_includes_judge_backend_with_eval(self) -> None:
        args = parse_args(["--repo", "typer", "--task", "context-routing", "--with-eval"])

        forwarded = build_forward_args(args)

        self.assertIn("--with-eval", forwarded)
        self.assertEqual(
            forwarded[forwarded.index("--judge-backend") + 1],
            "claude",
        )


if __name__ == "__main__":
    unittest.main()
