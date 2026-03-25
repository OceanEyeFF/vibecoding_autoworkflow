#!/usr/bin/env python3
"""Claude backend implementation for research runners."""

from __future__ import annotations

import json
from pathlib import Path

from .base import BackendInvocation, ResearchBackend


class ClaudeBackend(ResearchBackend):
    backend_id = "claude"
    skill_mount_path = ".claude/skills"
    supports_stdin_prompt = False
    supports_output_file = False
    supports_json_schema = True

    def __init__(self, executable: str, permission_mode: str, output_format: str) -> None:
        super().__init__(executable=executable)
        self.permission_mode = permission_mode
        self.output_format = output_format

    def build_skill_command(self, prompt_text: str, repo_path: Path, model: str | None) -> BackendInvocation:
        command = self._build_base_command(model=model)
        command.append(prompt_text)
        return BackendInvocation(command=command)

    def build_eval_command(
        self,
        prompt_text: str,
        repo_path: Path,
        model: str | None,
        schema_path: Path | None,
    ) -> BackendInvocation:
        output_format = "json" if schema_path is not None else self.output_format
        command = self._build_base_command(model=model, output_format=output_format)
        if schema_path is not None:
            command.extend(["--json-schema", schema_path.read_text(encoding="utf-8")])
        command.append(prompt_text)
        return BackendInvocation(command=command)

    def extract_final_message(self, invocation: BackendInvocation, stdout: str) -> str:
        payload = self._parse_output_payload(stdout)
        if payload is not None:
            structured_output = payload.get("structured_output")
            if isinstance(structured_output, dict):
                return json.dumps(structured_output, ensure_ascii=True, indent=2)
            result = payload.get("result")
            if isinstance(result, str):
                return result.strip()
        return stdout.strip()

    def _build_base_command(self, model: str | None, output_format: str | None = None) -> list[str]:
        command = [
            self.executable,
            "-p",
            "--permission-mode",
            self.permission_mode,
            "--output-format",
            output_format or self.output_format,
        ]
        if model:
            command.extend(["--model", model])
        return command

    def _parse_output_payload(self, stdout: str) -> dict | None:
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None
