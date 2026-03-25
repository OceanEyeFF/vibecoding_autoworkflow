from __future__ import annotations

import unittest

from run_skill_suite import coerce_process_output


class RunSkillSuiteTest(unittest.TestCase):
    def test_coerce_process_output_handles_none(self) -> None:
        self.assertEqual(coerce_process_output(None), "")

    def test_coerce_process_output_preserves_text(self) -> None:
        self.assertEqual(coerce_process_output("plain text"), "plain text")

    def test_coerce_process_output_decodes_bytes(self) -> None:
        self.assertEqual(coerce_process_output("hello".encode("utf-8")), "hello")


if __name__ == "__main__":
    unittest.main()
