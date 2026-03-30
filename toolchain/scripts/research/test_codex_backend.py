from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backends.codex import CodexBackend


class CodexBackendTest(unittest.TestCase):
    def test_build_skill_command_includes_reasoning_effort_override(self) -> None:
        backend = CodexBackend(
            executable="codex",
            sandbox="workspace-write",
            full_auto=True,
            reasoning_effort="high",
        )

        invocation = backend.build_skill_command(
            prompt_text="route",
            repo_path=Path("/tmp/repo"),
            model=None,
        )

        self.assertIn("-c", invocation.command)
        config_index = invocation.command.index("-c")
        self.assertEqual(
            invocation.command[config_index + 1],
            'model_reasoning_effort="high"',
        )


if __name__ == "__main__":
    unittest.main()
