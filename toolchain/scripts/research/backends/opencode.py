#!/usr/bin/env python3
"""OpenCode backend implementation for research runners."""

from __future__ import annotations

import json
from pathlib import Path

from .base import BackendInvocation, ResearchBackend


class OpenCodeBackend(ResearchBackend):
    backend_id = "opencode"
    skill_mount_path = ".opencode/skills"
    supports_stdin_prompt = False
    supports_output_file = False
    supports_json_schema = False

    def __init__(self, executable: str, output_format: str) -> None:
        super().__init__(executable=executable)
        self.output_format = output_format

    def build_skill_command(self, prompt_text: str, repo_path: Path, model: str | None) -> BackendInvocation:
        return BackendInvocation(command=self._build_command(prompt_text=prompt_text, repo_path=repo_path, model=model))

    def build_eval_command(
        self,
        prompt_text: str,
        repo_path: Path,
        model: str | None,
        schema_path: Path | None,
    ) -> BackendInvocation:
        del schema_path
        return BackendInvocation(command=self._build_command(prompt_text=prompt_text, repo_path=repo_path, model=model))

    def extract_final_message(self, invocation: BackendInvocation, stdout: str) -> str:
        del invocation
        payloads = list(self._iter_event_payloads(stdout))
        if not payloads:
            return stdout.strip()

        latest_assistant_message_id: str | None = None
        structured_by_message: dict[str, object] = {}
        text_parts: dict[tuple[str, str], str] = {}
        delta_parts: dict[tuple[str, str], str] = {}
        part_order: list[tuple[str, str]] = []

        for index, payload in enumerate(payloads, start=1):
            event_type = str(payload.get("type") or payload.get("event") or "").strip()
            if not event_type:
                continue
            if event_type == "message.updated":
                message = payload.get("message")
                if not isinstance(message, dict):
                    message = payload
                role = str(message.get("role") or payload.get("role") or "").strip()
                message_id = str(
                    payload.get("messageID")
                    or message.get("id")
                    or payload.get("id")
                    or latest_assistant_message_id
                    or f"assistant-{index}"
                ).strip()
                if role == "assistant":
                    latest_assistant_message_id = message_id
                    structured = message.get("structured")
                    if structured is not None:
                        structured_by_message[message_id] = structured
                continue
            if event_type == "text":
                part = payload.get("part")
                if not isinstance(part, dict):
                    continue
                message_id = str(part.get("messageID") or payload.get("messageID") or latest_assistant_message_id or "").strip()
                if not message_id:
                    continue
                latest_assistant_message_id = message_id
                part_id = str(part.get("id") or payload.get("partID") or f"text-{index}").strip()
                key = (message_id, part_id)
                text_parts[key] = str(part.get("text") or "")
                if key not in part_order:
                    part_order.append(key)
                continue
            if event_type == "message.part.updated":
                part = payload.get("part")
                if not isinstance(part, dict):
                    continue
                message_id = str(payload.get("messageID") or latest_assistant_message_id or "").strip()
                if not message_id:
                    continue
                if part.get("type") != "text":
                    continue
                part_id = str(part.get("id") or payload.get("partID") or f"part-{index}").strip()
                key = (message_id, part_id)
                text_parts[key] = str(part.get("text") or "")
                if key not in part_order:
                    part_order.append(key)
                continue
            if event_type == "message.part.delta":
                message_id = str(payload.get("messageID") or latest_assistant_message_id or "").strip()
                if not message_id:
                    continue
                part_id = str(payload.get("partID") or payload.get("id") or f"delta-{index}").strip()
                key = (message_id, part_id)
                delta_parts[key] = delta_parts.get(key, "") + str(payload.get("delta") or "")
                if key not in part_order:
                    part_order.append(key)

        selected_message_id = latest_assistant_message_id
        if selected_message_id and selected_message_id in structured_by_message:
            return json.dumps(structured_by_message[selected_message_id], ensure_ascii=True, indent=2)

        if selected_message_id:
            updated_text = "".join(
                text_parts[key]
                for key in part_order
                if key[0] == selected_message_id and text_parts.get(key)
            )
            if updated_text.strip():
                return updated_text.strip()

            delta_text = "".join(
                delta_parts[key]
                for key in part_order
                if key[0] == selected_message_id and delta_parts.get(key)
            )
            if delta_text.strip():
                return delta_text.strip()

        return stdout.strip()

    def _build_command(self, *, prompt_text: str, repo_path: Path, model: str | None) -> list[str]:
        command = [
            self.executable,
            "run",
            "--dir",
            str(repo_path),
            "--format",
            self.output_format,
        ]
        if model:
            command.extend(["--model", model])
        command.append(prompt_text)
        return command

    def _iter_event_payloads(self, stdout: str):
        for raw_line in stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and isinstance(payload.get("payload"), dict):
                yield payload["payload"]
                continue
            if isinstance(payload, dict):
                yield payload
