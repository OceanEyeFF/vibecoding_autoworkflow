from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backends.opencode import OpenCodeBackend


class OpenCodeBackendTest(unittest.TestCase):
    def test_build_skill_command_passes_model_dir_and_output_format(self) -> None:
        backend = OpenCodeBackend(executable="opencode", output_format="json")

        invocation = backend.build_skill_command(
            prompt_text="hello world",
            repo_path=Path("/tmp/repo"),
            model="openai/gpt-5",
        )

        self.assertEqual(
            invocation.command,
            [
                "opencode",
                "run",
                "--dir",
                "/tmp/repo",
                "--format",
                "json",
                "--model",
                "openai/gpt-5",
                "hello world",
            ],
        )

    def test_build_eval_command_ignores_schema_and_model_when_absent(self) -> None:
        backend = OpenCodeBackend(executable="opencode", output_format="json")

        invocation = backend.build_eval_command(
            prompt_text="judge output",
            repo_path=Path("/tmp/repo"),
            model=None,
            schema_path=Path("/tmp/schema.json"),
        )

        self.assertEqual(
            invocation.command,
            [
                "opencode",
                "run",
                "--dir",
                "/tmp/repo",
                "--format",
                "json",
                "judge output",
            ],
        )

    def test_extract_final_message_prefers_last_assistant_text_parts(self) -> None:
        backend = OpenCodeBackend(executable="opencode", output_format="json")
        stdout = "\n".join(
            [
                json.dumps(
                    {
                        "payload": {
                            "type": "message.updated",
                            "message": {"id": "m1", "role": "assistant"},
                        }
                    }
                ),
                json.dumps(
                    {
                        "payload": {
                            "type": "message.part.updated",
                            "messageID": "m1",
                            "part": {"id": "p1", "type": "text", "text": "first"},
                        }
                    }
                ),
                json.dumps(
                    {
                        "payload": {
                            "type": "message.updated",
                            "message": {"id": "m2", "role": "assistant"},
                        }
                    }
                ),
                json.dumps(
                    {
                        "payload": {
                            "type": "message.part.updated",
                            "messageID": "m2",
                            "part": {"id": "p2", "type": "text", "text": "final answer"},
                        }
                    }
                ),
            ]
        )

        final_message = backend.extract_final_message(invocation=None, stdout=stdout)

        self.assertEqual(final_message, "final answer")

    def test_extract_final_message_falls_back_to_delta_stream(self) -> None:
        backend = OpenCodeBackend(executable="opencode", output_format="json")
        stdout = "\n".join(
            [
                json.dumps({"type": "message.updated", "message": {"id": "m1", "role": "assistant"}}),
                json.dumps({"type": "message.part.delta", "messageID": "m1", "partID": "p1", "delta": "hello "}),
                json.dumps({"type": "message.part.delta", "messageID": "m1", "partID": "p1", "delta": "world"}),
            ]
        )

        final_message = backend.extract_final_message(invocation=None, stdout=stdout)

        self.assertEqual(final_message, "hello world")


if __name__ == "__main__":
    unittest.main()
