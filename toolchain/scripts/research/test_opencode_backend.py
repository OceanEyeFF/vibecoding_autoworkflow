from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

from backends import build_backend, normalize_opencode_output_format
from backends.opencode import OpenCodeBackend


class OpenCodeBackendTest(unittest.TestCase):
    def test_normalize_opencode_output_format_maps_shared_runner_values(self) -> None:
        self.assertEqual(normalize_opencode_output_format("text"), "default")
        self.assertEqual(normalize_opencode_output_format("json"), "json")
        self.assertEqual(normalize_opencode_output_format("stream-json"), "json")

    def test_build_backend_normalizes_opencode_output_format(self) -> None:
        backend = build_backend(
            "opencode",
            SimpleNamespace(opencode_bin="opencode", output_format="text"),
        )

        self.assertIsInstance(backend, OpenCodeBackend)
        self.assertEqual(backend.output_format, "default")

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

    def test_extract_final_message_handles_jsonl_text_events(self) -> None:
        backend = OpenCodeBackend(executable="opencode", output_format="json")
        stdout = "\n".join(
            [
                json.dumps(
                    {
                        "type": "text",
                        "part": {
                            "id": "part-1",
                            "messageID": "assistant-1",
                            "text": "first line\n",
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "text",
                        "part": {
                            "id": "part-2",
                            "messageID": "assistant-1",
                            "text": "second line",
                        },
                    }
                ),
                json.dumps({"type": "step_finish", "step": {"id": "done"}}),
            ]
        )

        final_message = backend.extract_final_message(invocation=None, stdout=stdout)

        self.assertEqual(final_message, "first line\nsecond line")


if __name__ == "__main__":
    unittest.main()
