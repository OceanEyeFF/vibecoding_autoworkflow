#!/usr/bin/env python3
"""Backend contract for research runners."""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BackendInvocation:
    command: list[str]
    stdin_text: str | None = None
    final_message_path: Path | None = None
    cleanup_paths: list[Path] = field(default_factory=list)


class ResearchBackend(ABC):
    backend_id = ""
    skill_mount_path = ""
    supports_stdin_prompt = False
    supports_output_file = False
    supports_json_schema = False

    def __init__(self, executable: str) -> None:
        self.executable = executable

    def healthcheck(self) -> tuple[bool, str]:
        if shutil.which(self.executable):
            return True, self.executable
        return False, f"Executable not found: {self.executable}"

    @abstractmethod
    def build_skill_command(self, prompt_text: str, repo_path: Path, model: str | None) -> BackendInvocation:
        raise NotImplementedError

    @abstractmethod
    def build_eval_command(
        self,
        prompt_text: str,
        repo_path: Path,
        model: str | None,
        schema_path: Path | None,
    ) -> BackendInvocation:
        raise NotImplementedError

    @abstractmethod
    def extract_final_message(self, invocation: BackendInvocation, stdout: str) -> str:
        raise NotImplementedError

