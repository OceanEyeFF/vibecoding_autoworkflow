#!/usr/bin/env python3
"""Reserved OpenCode backend slot for research runners."""

from __future__ import annotations

from pathlib import Path

from .base import BackendInvocation, ResearchBackend


class OpenCodeBackend(ResearchBackend):
    backend_id = "opencode"
    skill_mount_path = ".agents/skills"
    supports_stdin_prompt = False
    supports_output_file = False
    supports_json_schema = False

    def healthcheck(self) -> tuple[bool, str]:
        ok, message = super().healthcheck()
        if not ok:
            return ok, message
        return False, "OpenCode backend is reserved but not implemented in the research runner."

    def build_skill_command(self, prompt_text: str, repo_path: Path, model: str | None) -> BackendInvocation:
        raise NotImplementedError("OpenCode backend is reserved but not implemented.")

    def build_eval_command(
        self,
        prompt_text: str,
        repo_path: Path,
        model: str | None,
        schema_path: Path | None,
    ) -> BackendInvocation:
        raise NotImplementedError("OpenCode backend is reserved but not implemented.")

    def extract_final_message(self, invocation: BackendInvocation, stdout: str) -> str:
        raise NotImplementedError("OpenCode backend is reserved but not implemented.")

