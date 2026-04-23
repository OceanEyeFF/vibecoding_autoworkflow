from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backends.claude import ClaudeBackend


class ClaudeBackendTest(unittest.TestCase):
    def test_build_skill_command_preserves_configured_output_format(self) -> None:
        backend = ClaudeBackend(executable="claude", permission_mode="bypassPermissions", output_format="text")

        invocation = backend.build_skill_command(
            prompt_text="hello",
            repo_path=Path("."),
            model=None,
        )

        self.assertEqual(
            invocation.command,
            [
                "claude",
                "-p",
                "--permission-mode",
                "bypassPermissions",
                "--output-format",
                "text",
                "hello",
            ],
        )

    def test_build_eval_command_forces_json_output_when_schema_is_present(self) -> None:
        backend = ClaudeBackend(executable="claude", permission_mode="bypassPermissions", output_format="text")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            handle.write('{"type":"object"}')
            schema_path = Path(handle.name)
        self.addCleanup(schema_path.unlink)

        invocation = backend.build_eval_command(
            prompt_text="judge",
            repo_path=Path("."),
            model=None,
            schema_path=schema_path,
        )

        self.assertEqual(invocation.command[5], "json")
        self.assertIn("--json-schema", invocation.command)

    def test_extract_final_message_prefers_structured_output_from_json_envelope(self) -> None:
        backend = ClaudeBackend(executable="claude", permission_mode="bypassPermissions", output_format="text")
        stdout = json.dumps(
            {
                "type": "result",
                "result": "natural language summary",
                "structured_output": {"scores": {"path_contraction": 3}, "overall": "Good"},
            }
        )

        final_message = backend.extract_final_message(invocation=None, stdout=stdout)

        self.assertEqual(
            json.loads(final_message),
            {"scores": {"path_contraction": 3}, "overall": "Good"},
        )

    def test_extract_final_message_uses_result_field_without_structured_output(self) -> None:
        backend = ClaudeBackend(executable="claude", permission_mode="bypassPermissions", output_format="text")
        stdout = json.dumps({"type": "result", "result": "plain summary"})

        final_message = backend.extract_final_message(invocation=None, stdout=stdout)

        self.assertEqual(final_message, "plain summary")


if __name__ == "__main__":
    unittest.main()
