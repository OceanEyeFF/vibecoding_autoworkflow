from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CHECK_SCRIPT = REPO_ROOT / "toolchain" / "scripts" / "test" / "repo_analysis_contract_check.py"


class RepoAnalysisContractCheckTest(unittest.TestCase):
    def test_default_repo_analysis_templates_pass(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(CHECK_SCRIPT)],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("repo analysis contract check passed for 2 file(s)", completed.stdout)
        self.assertEqual(completed.stderr, "")

    def test_missing_required_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = Path(temp_dir) / "analysis.md"
            invalid_path.write_text(
                textwrap.dedent(
                    """\
                    # Repo Analysis

                    ## Metadata

                    - repo: demo
                    - baseline_branch: main
                    - baseline_ref: abc123
                    - updated: 2026-04-26
                    - analysis_status: fresh

                    ## Facts

                    - facts: demo

                    ## Inferences

                    - inferences: demo

                    ## Unknowns

                    - unknowns: demo

                    ## Main Contradiction

                    - current_main_contradiction: demo
                    - main_aspect: demo

                    ## Priority Judgment

                    - current_highest_priority: demo
                    - long_term_highest_priority: demo
                    - do_not_do_now: demo

                    ## Routing Projection

                    - recommended_repo_action: enter-worktrack
                    - suggested_node_type: test
                    - continuation_ready: true
                    - continuation_blockers: N/A

                    ## Writeback Eligibility

                    - writeback_eligibility: demo
                    """
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [sys.executable, str(CHECK_SCRIPT), str(invalid_path)],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 1)
        self.assertIn("missing-repo-analysis-field", completed.stderr)
        self.assertIn("recommended_next_route", completed.stderr)
        self.assertEqual(completed.stdout, "")


if __name__ == "__main__":
    unittest.main()
