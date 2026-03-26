#!/usr/bin/env python3
"""Git worktree lifecycle manager for autoresearch P0.2."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import REPO_ROOT, slugify


AUTORESEARCH_ROOT = REPO_ROOT / ".autoworkflow" / "autoresearch"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def champion_branch_name(run_id: str) -> str:
    return f"champion/{run_id}"


def candidate_branch_name(run_id: str, round_number: int) -> str:
    return f"candidate/{run_id}/r{round_number:03d}"


def round_label(round_number: int) -> str:
    return f"round-{round_number:03d}"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object required: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


class WorktreeManager:
    """Manage champion/candidate git lifecycle without touching the user's current worktree."""

    def __init__(
        self,
        *,
        repo_root: Path = REPO_ROOT,
        autoresearch_root: Path = AUTORESEARCH_ROOT,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.autoresearch_root = autoresearch_root.resolve()

    def run_dir(self, run_id: str) -> Path:
        return self.autoresearch_root / slugify(run_id)

    def runtime_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "runtime.json"

    def rounds_root(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "rounds"

    def round_dir(self, run_id: str, round_number: int) -> Path:
        return self.rounds_root(run_id) / round_label(round_number)

    def round_path(self, run_id: str, round_number: int) -> Path:
        return self.round_dir(run_id, round_number) / "round.json"

    def worktree_path_record(self, run_id: str, round_number: int) -> Path:
        return self.round_dir(run_id, round_number) / "worktree.json"

    def candidate_worktree_path(self, run_id: str, round_number: int) -> Path:
        return self.run_dir(run_id) / "worktrees" / round_label(round_number)

    def _build_worktree_payload(
        self,
        *,
        worktree_path: Path,
        candidate_branch: str,
        base_sha: str,
        candidate_sha: str | None,
        created_at: str | None = None,
        cleaned_at: str | None = None,
    ) -> dict[str, Any]:
        return {
            "path": str(worktree_path),
            "branch": candidate_branch,
            "base_sha": base_sha,
            "candidate_sha": candidate_sha,
            "created_at": created_at or now_iso(),
            "cleaned_at": cleaned_at,
        }

    def _git(
        self,
        *args: str,
        check: bool = True,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=cwd or self.repo_root,
            check=check,
            capture_output=True,
            text=True,
        )

    def current_head(self) -> str:
        return self._git("rev-parse", "HEAD").stdout.strip()

    def ref_sha(self, ref: str) -> str:
        return self._git("rev-parse", ref).stdout.strip()

    def branch_exists(self, branch: str) -> bool:
        completed = self._git("show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False)
        return completed.returncode == 0

    def is_ancestor(self, older_ref: str, newer_ref: str) -> bool:
        completed = self._git("merge-base", "--is-ancestor", older_ref, newer_ref, check=False)
        if completed.returncode in (0, 1):
            return completed.returncode == 0
        raise RuntimeError(completed.stderr.strip() or "git merge-base failed")

    def initialize_runtime(self, run_id: str) -> dict[str, Any]:
        champion_branch = champion_branch_name(run_id)
        payload = {
            "run_id": run_id,
            "champion_branch": champion_branch,
            "champion_sha": self.current_head(),
            "active_round": None,
            "active_candidate_branch": None,
            "active_candidate_worktree": None,
            "updated_at": now_iso(),
        }
        write_json(self.runtime_path(run_id), payload)
        return payload

    def load_runtime(self, run_id: str) -> dict[str, Any]:
        path = self.runtime_path(run_id)
        if not path.is_file():
            return self.initialize_runtime(run_id)
        return read_json(path)

    def save_runtime(self, run_id: str, payload: dict[str, Any]) -> None:
        payload["updated_at"] = now_iso()
        write_json(self.runtime_path(run_id), payload)

    def ensure_champion_branch(self, run_id: str) -> tuple[str, dict[str, Any]]:
        runtime = self.load_runtime(run_id)
        champion_branch = str(runtime["champion_branch"])
        champion_sha = str(runtime.get("champion_sha") or self.current_head())
        if not self.branch_exists(champion_branch):
            self._git("branch", champion_branch, champion_sha)
        champion_sha = self.ref_sha(champion_branch)
        runtime["champion_sha"] = champion_sha
        self.save_runtime(run_id, runtime)
        return champion_sha, runtime

    def next_round_number(self, run_id: str) -> int:
        root = self.rounds_root(run_id)
        if not root.exists():
            return 1
        rounds = []
        for path in root.iterdir():
            if not path.is_dir() or not path.name.startswith("round-"):
                continue
            try:
                rounds.append(int(path.name.split("-", 1)[1]))
            except ValueError:
                continue
        return max(rounds, default=0) + 1

    def prepare_round(self, run_id: str) -> dict[str, Any]:
        base_sha, runtime = self.ensure_champion_branch(run_id)
        if runtime.get("active_round") is not None:
            raise RuntimeError(
                "An active round already exists. Use cleanup-round, discard-round, or promote-round first."
            )

        round_number = self.next_round_number(run_id)
        candidate_branch = candidate_branch_name(run_id, round_number)
        if self.branch_exists(candidate_branch):
            raise RuntimeError(f"Candidate branch already exists: {candidate_branch}")

        round_dir = self.round_dir(run_id, round_number)
        worktree_path = self.candidate_worktree_path(run_id, round_number)
        round_payload = {
            "round": round_number,
            "state": "prepared",
            "base_sha": base_sha,
            "candidate_branch": candidate_branch,
            "candidate_worktree": str(worktree_path),
            "candidate_sha": None,
            "decision": None,
        }
        write_json(self.round_path(run_id, round_number), round_payload)
        worktree_payload = self._build_worktree_payload(
            worktree_path=worktree_path,
            candidate_branch=candidate_branch,
            base_sha=base_sha,
            candidate_sha=None,
        )
        write_json(self.worktree_path_record(run_id, round_number), worktree_payload)

        runtime["active_round"] = round_number
        runtime["active_candidate_branch"] = candidate_branch
        runtime["active_candidate_worktree"] = str(worktree_path)
        runtime["champion_sha"] = base_sha
        self.save_runtime(run_id, runtime)

        self._git("worktree", "add", "-b", candidate_branch, str(worktree_path), base_sha)
        candidate_sha = self.ref_sha(candidate_branch)
        worktree_payload["candidate_sha"] = candidate_sha
        write_json(self.worktree_path_record(run_id, round_number), worktree_payload)

        round_payload["state"] = "candidate_active"
        round_payload["candidate_sha"] = candidate_sha
        write_json(self.round_path(run_id, round_number), round_payload)
        self.save_runtime(run_id, runtime)
        return {
            "runtime": runtime,
            "round": round_payload,
            "worktree": worktree_payload,
        }

    def load_active_round(self, run_id: str) -> dict[str, Any]:
        runtime, round_payload, worktree_payload = self._require_active_round(run_id)
        return {
            "runtime": runtime,
            "round": round_payload,
            "worktree": worktree_payload,
        }

    def capture_candidate_commit(self, run_id: str, *, message: str) -> dict[str, Any]:
        runtime, round_payload, worktree_payload = self._require_active_round(run_id)
        candidate_worktree = Path(str(worktree_payload["path"]))
        self._git("add", "-A", cwd=candidate_worktree)
        staged = self._git("diff", "--cached", "--quiet", cwd=candidate_worktree, check=False)
        if staged.returncode not in (0, 1):
            raise RuntimeError(staged.stderr.strip() or "git diff --cached failed")
        if staged.returncode == 1:
            self._git("commit", "-q", "-m", message, cwd=candidate_worktree)

        candidate_sha = self._git("rev-parse", "HEAD", cwd=candidate_worktree).stdout.strip()
        round_payload["candidate_sha"] = candidate_sha
        write_json(self.round_path(run_id, int(round_payload["round"])), round_payload)
        worktree_payload["candidate_sha"] = candidate_sha
        write_json(self.worktree_path_record(run_id, int(round_payload["round"])), worktree_payload)
        return {
            "runtime": runtime,
            "round": round_payload,
            "worktree": worktree_payload,
        }

    def _require_active_round(self, run_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        runtime = self.load_runtime(run_id)
        active_round = runtime.get("active_round")
        if active_round is None:
            raise RuntimeError("No active round found in runtime.json")
        round_number = int(active_round)
        round_payload = read_json(self.round_path(run_id, round_number))
        worktree_path = self.worktree_path_record(run_id, round_number)
        if worktree_path.is_file():
            worktree_payload = read_json(worktree_path)
        else:
            worktree_payload = self._build_worktree_payload(
                worktree_path=Path(
                    str(
                        runtime.get("active_candidate_worktree")
                        or round_payload.get("candidate_worktree")
                        or self.candidate_worktree_path(run_id, round_number)
                    )
                ),
                candidate_branch=str(
                    runtime.get("active_candidate_branch") or round_payload.get("candidate_branch") or ""
                ),
                base_sha=str(round_payload.get("base_sha") or runtime.get("champion_sha") or ""),
                candidate_sha=round_payload.get("candidate_sha"),
                created_at=None,
                cleaned_at=None,
            )
            write_json(worktree_path, worktree_payload)
        return runtime, round_payload, worktree_payload

    def _finalize_cleanup(
        self,
        run_id: str,
        *,
        runtime: dict[str, Any],
        round_payload: dict[str, Any],
        worktree_payload: dict[str, Any],
        final_state: str,
    ) -> dict[str, Any]:
        candidate_worktree = Path(str(worktree_payload["path"]))
        if candidate_worktree.exists():
            self._git("worktree", "remove", "--force", str(candidate_worktree))

        candidate_branch = str(worktree_payload["branch"])
        if self.branch_exists(candidate_branch):
            self._git("branch", "-D", candidate_branch)

        worktree_payload["cleaned_at"] = now_iso()
        write_json(self.worktree_path_record(run_id, int(round_payload["round"])), worktree_payload)

        round_payload["state"] = final_state
        write_json(self.round_path(run_id, int(round_payload["round"])), round_payload)

        runtime["active_round"] = None
        runtime["active_candidate_branch"] = None
        runtime["active_candidate_worktree"] = None
        runtime["champion_sha"] = self.ref_sha(str(runtime["champion_branch"]))
        self.save_runtime(run_id, runtime)
        return {
            "runtime": runtime,
            "round": round_payload,
            "worktree": worktree_payload,
        }

    def promote_round(self, run_id: str) -> dict[str, Any]:
        runtime, round_payload, worktree_payload = self._require_active_round(run_id)
        champion_branch = str(runtime["champion_branch"])
        champion_sha = self.ref_sha(champion_branch)
        candidate_branch = str(worktree_payload["branch"])
        candidate_sha = self.ref_sha(candidate_branch)
        if not self.is_ancestor(champion_sha, candidate_sha):
            raise RuntimeError("Promote requires fast-forward semantics: champion is not an ancestor of candidate")

        round_payload["state"] = "accepted"
        round_payload["candidate_sha"] = candidate_sha
        round_payload["decision"] = "keep"
        write_json(self.round_path(run_id, int(round_payload["round"])), round_payload)

        self._git("update-ref", f"refs/heads/{champion_branch}", candidate_sha, champion_sha)
        runtime["champion_sha"] = candidate_sha
        self.save_runtime(run_id, runtime)
        return self._finalize_cleanup(
            run_id,
            runtime=runtime,
            round_payload=round_payload,
            worktree_payload=worktree_payload,
            final_state="cleaned",
        )

    def discard_round(self, run_id: str) -> dict[str, Any]:
        runtime, round_payload, worktree_payload = self._require_active_round(run_id)
        round_payload["state"] = "discarded"
        round_payload["decision"] = "discard"
        write_json(self.round_path(run_id, int(round_payload["round"])), round_payload)
        return self._finalize_cleanup(
            run_id,
            runtime=runtime,
            round_payload=round_payload,
            worktree_payload=worktree_payload,
            final_state="cleaned",
        )

    def cleanup_round(self, run_id: str) -> dict[str, Any]:
        runtime, round_payload, worktree_payload = self._require_active_round(run_id)
        return self._finalize_cleanup(
            run_id,
            runtime=runtime,
            round_payload=round_payload,
            worktree_payload=worktree_payload,
            final_state="cleaned",
        )
