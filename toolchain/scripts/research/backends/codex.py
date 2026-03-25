#!/usr/bin/env python3
"""Codex backend implementation for research runners."""

from __future__ import annotations

import tempfile
from pathlib import Path

from .base import BackendInvocation, ResearchBackend


class CodexBackend(ResearchBackend):
    backend_id = "codex"
    skill_mount_path = ".agents/skills"
    supports_stdin_prompt = True
    supports_output_file = True
    supports_json_schema = True

    def __init__(self, executable: str, sandbox: str, full_auto: bool) -> None:
        super().__init__(executable=executable)
        self.sandbox = sandbox
        self.full_auto = full_auto

    def build_skill_command(self, prompt_text: str, repo_path: Path, model: str | None) -> BackendInvocation:
        return self._build_command(
            prompt_text=prompt_text,
            repo_path=repo_path,
            model=model,
            schema_path=None,
        )

    def build_eval_command(
        self,
        prompt_text: str,
        repo_path: Path,
        model: str | None,
        schema_path: Path | None,
    ) -> BackendInvocation:
        return self._build_command(
            prompt_text=prompt_text,
            repo_path=repo_path,
            model=model,
            schema_path=schema_path,
        )

    def extract_final_message(self, invocation: BackendInvocation, stdout: str) -> str:
        if invocation.final_message_path and invocation.final_message_path.exists():
            return invocation.final_message_path.read_text(encoding="utf-8").strip()
        return stdout.strip()

    def _build_command(
        self,
        prompt_text: str,
        repo_path: Path,
        model: str | None,
        schema_path: Path | None,
    ) -> BackendInvocation:
        handle = tempfile.NamedTemporaryFile(prefix="codex-final-", suffix=".txt", delete=False)
        handle.close()
        final_message_path = Path(handle.name)

        command = [
            self.executable,
            "exec",
            "--cd",
            str(repo_path),
            "--sandbox",
            self.sandbox,
            "--output-last-message",
            str(final_message_path),
        ]
        if self.full_auto:
            command.append("--full-auto")
        if model:
            command.extend(["--model", model])
        if schema_path is not None:
            command.extend(["--output-schema", str(schema_path)])
        command.append("-")

        return BackendInvocation(
            command=command,
            stdin_text=prompt_text,
            final_message_path=final_message_path,
            cleanup_paths=[final_message_path],
        )

