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
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=cwd or self.repo_root,
            check=check,
            capture_output=True,
            text=True,
            input=input_text,
        )

    def git_dir(self) -> Path:
        completed = self._git("rev-parse", "--git-dir")
        git_dir = Path(completed.stdout.strip())
        if not git_dir.is_absolute():
            git_dir = (self.repo_root / git_dir).resolve()
        return git_dir

    def ref_exists(self, ref: str) -> bool:
        completed = self._git("show-ref", "--verify", "--quiet", ref, check=False)
        return completed.returncode == 0

    def round_authority_ref(self, run_id: str, round_number: int) -> str:
        return f"refs/autoresearch/round-authority/{slugify(run_id)}/{round_number:03d}"

    def write_round_authority(self, run_id: str, round_number: int, payload: dict[str, Any]) -> str:
        authority_ref = self.round_authority_ref(run_id, round_number)
        serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
        blob_oid = self._git("hash-object", "-w", "--stdin", input_text=serialized).stdout.strip()
        self._git("update-ref", authority_ref, blob_oid)
        return blob_oid

    def read_round_authority(self, run_id: str, round_number: int) -> tuple[str, dict[str, Any]]:
        authority_ref = self.round_authority_ref(run_id, round_number)
        if not self.ref_exists(authority_ref):
            raise FileNotFoundError(f"Missing round authority ref: {authority_ref}")
        oid = self.ref_sha(authority_ref)
        completed = self._git("cat-file", "-p", authority_ref)
        payload = json.loads(completed.stdout)
        if not isinstance(payload, dict):
            raise ValueError(f"Round authority ref does not contain a JSON object: {authority_ref}")
        return oid, payload

    def current_head(self) -> str:
        return self._git("rev-parse", "HEAD").stdout.strip()

    def ref_sha(self, ref: str) -> str:
        return self._git("rev-parse", ref).stdout.strip()

    def merge_base(self, ref_a: str, ref_b: str) -> str:
        return self._git("merge-base", ref_a, ref_b).stdout.strip()

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

    def refresh_champion_branch(self, run_id: str, champion_sha: str) -> None:
        champion_branch = champion_branch_name(run_id)
        self._git("update-ref", f"refs/heads/{champion_branch}", champion_sha)

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
        champion_branch = champion_branch_name(run_id)
        runtime_champion_branch = str(runtime.get("champion_branch") or "").strip()
        runtime_champion_sha = str(runtime.get("champion_sha") or "").strip()
        scoreboard_path = self.run_dir(run_id) / "scoreboard.json"
        if not self.branch_exists(champion_branch):
            raise RuntimeError(f"Missing champion branch: {champion_branch}. Rerun baseline before prepare-round.")
        champion_sha = self.ref_sha(champion_branch)
        if runtime_champion_branch != champion_branch:
            raise RuntimeError("runtime.json champion_branch does not match deterministic champion identity.")
        if runtime_champion_sha != champion_sha:
            raise RuntimeError("runtime.json champion_sha does not match champion branch authority.")
        if scoreboard_path.is_file():
            scoreboard = read_json(scoreboard_path)
            scoreboard_baseline_sha = str(scoreboard.get("baseline_sha") or "").strip()
            if scoreboard_baseline_sha and scoreboard_baseline_sha != champion_sha:
                raise RuntimeError("scoreboard.json baseline_sha does not match champion branch authority.")
        runtime["champion_branch"] = champion_branch
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
        expected_branch = candidate_branch_name(run_id, round_number)
        expected_worktree_path = self.candidate_worktree_path(run_id, round_number)
        expected_champion_branch = champion_branch_name(run_id)
        if int(round_payload.get("round") or 0) != round_number:
            raise RuntimeError("round.json round does not match runtime.json active_round.")
        if not self.branch_exists(expected_branch):
            raise RuntimeError(f"Missing candidate branch: {expected_branch}")
        if not self.branch_exists(expected_champion_branch):
            raise RuntimeError(f"Missing champion branch: {expected_champion_branch}")
        pinned_candidate_sha = str(round_payload.get("candidate_sha") or "").strip()
        if not pinned_candidate_sha:
            raise RuntimeError("round.json candidate_sha is missing for the active round.")
        current_candidate_sha = self.ref_sha(expected_branch)
        expected_base_sha = self.merge_base(expected_branch, expected_champion_branch)
        if str(runtime.get("active_candidate_branch") or "") != expected_branch:
            raise RuntimeError("runtime.json active_candidate_branch does not match deterministic candidate identity.")
        if str(runtime.get("active_candidate_worktree") or "") != str(expected_worktree_path):
            raise RuntimeError("runtime.json active_candidate_worktree does not match deterministic candidate identity.")
        if str(round_payload.get("candidate_branch") or "") != expected_branch:
            raise RuntimeError("round.json candidate_branch does not match deterministic candidate identity.")
        if str(round_payload.get("candidate_worktree") or "") != str(expected_worktree_path):
            raise RuntimeError("round.json candidate_worktree does not match deterministic candidate identity.")
        if current_candidate_sha != pinned_candidate_sha:
            raise RuntimeError("candidate branch tip does not match pinned round candidate_sha.")
        if str(round_payload.get("base_sha") or "") != expected_base_sha:
            raise RuntimeError("round.json base_sha does not match deterministic git authority.")
        worktree_path = self.worktree_path_record(run_id, round_number)
        if worktree_path.is_file():
            worktree_payload = read_json(worktree_path)
            if str(worktree_payload.get("path") or "") != str(expected_worktree_path):
                raise RuntimeError("worktree.json path does not match deterministic candidate identity.")
            if str(worktree_payload.get("branch") or "") != expected_branch:
                raise RuntimeError("worktree.json branch does not match deterministic candidate identity.")
            if str(worktree_payload.get("base_sha") or "") != expected_base_sha:
                raise RuntimeError("worktree.json base_sha does not match deterministic git authority.")
            worktree_candidate_sha = str(worktree_payload.get("candidate_sha") or "").strip()
            if worktree_candidate_sha != pinned_candidate_sha:
                raise RuntimeError("worktree.json candidate_sha does not match pinned round candidate_sha.")
        else:
            raise FileNotFoundError(f"Missing candidate worktree record: {worktree_path}")
        runtime = dict(runtime)
        round_payload = dict(round_payload)
        worktree_payload = dict(worktree_payload)
        round_payload["round"] = round_number
        round_payload["candidate_branch"] = expected_branch
        round_payload["candidate_worktree"] = str(expected_worktree_path)
        round_payload["base_sha"] = expected_base_sha
        round_payload["candidate_sha"] = pinned_candidate_sha
        worktree_payload["path"] = str(expected_worktree_path)
        worktree_payload["branch"] = expected_branch
        worktree_payload["base_sha"] = expected_base_sha
        worktree_payload["candidate_sha"] = pinned_candidate_sha
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
        runtime["champion_branch"] = champion_branch_name(run_id)
        runtime["champion_sha"] = self.ref_sha(runtime["champion_branch"])
        self.save_runtime(run_id, runtime)
        return {
            "runtime": runtime,
            "round": round_payload,
            "worktree": worktree_payload,
        }

    def _load_cleanup_state(self, run_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        runtime = self.load_runtime(run_id)
        active_round = runtime.get("active_round")
        if active_round is None:
            raise RuntimeError("No active round found in runtime.json")
        round_number = int(active_round)
        round_path = self.round_path(run_id, round_number)
        if not round_path.is_file():
            raise FileNotFoundError(f"Missing round file: {round_path}")
        round_payload = read_json(round_path)
        if int(round_payload.get("round") or 0) != round_number:
            raise RuntimeError("round.json round does not match runtime.json active_round.")
        state = str(round_payload.get("state") or "")
        if state not in {"prepared", "candidate_active", "evaluating", "evaluated", "accepted"}:
            raise RuntimeError("cleanup-round recovery requires an active round state.")

        expected_branch = candidate_branch_name(run_id, round_number)
        expected_worktree_path = self.candidate_worktree_path(run_id, round_number)
        if str(runtime.get("active_candidate_branch") or "") != expected_branch:
            raise RuntimeError("runtime.json active_candidate_branch does not match deterministic candidate identity.")
        if str(runtime.get("active_candidate_worktree") or "") != str(expected_worktree_path):
            raise RuntimeError("runtime.json active_candidate_worktree does not match deterministic candidate identity.")
        if str(round_payload.get("candidate_branch") or "") != expected_branch:
            raise RuntimeError("round.json candidate_branch does not match deterministic candidate identity.")
        if str(round_payload.get("candidate_worktree") or "") != str(expected_worktree_path):
            raise RuntimeError("round.json candidate_worktree does not match deterministic candidate identity.")

        pinned_candidate_sha = str(round_payload.get("candidate_sha") or "").strip()
        worktree_path = self.worktree_path_record(run_id, round_number)
        if worktree_path.is_file():
            worktree_payload = read_json(worktree_path)
            if str(worktree_payload.get("path") or "") != str(expected_worktree_path):
                raise RuntimeError("worktree.json path does not match deterministic candidate identity.")
            if str(worktree_payload.get("branch") or "") != expected_branch:
                raise RuntimeError("worktree.json branch does not match deterministic candidate identity.")
            if str(worktree_payload.get("base_sha") or "") != str(round_payload.get("base_sha") or ""):
                raise RuntimeError("worktree.json base_sha does not match round.json base_sha.")
            worktree_candidate_sha = str(worktree_payload.get("candidate_sha") or "").strip()
            if state == "prepared":
                if worktree_candidate_sha and pinned_candidate_sha and worktree_candidate_sha != pinned_candidate_sha:
                    raise RuntimeError("worktree.json candidate_sha does not match round.json candidate_sha.")
            else:
                if not pinned_candidate_sha:
                    raise RuntimeError("round.json candidate_sha is missing for the active round.")
                if worktree_candidate_sha and worktree_candidate_sha != pinned_candidate_sha:
                    raise RuntimeError("worktree.json candidate_sha does not match pinned round candidate_sha.")
        else:
            if state == "prepared":
                candidate_sha = pinned_candidate_sha or None
            else:
                if not pinned_candidate_sha:
                    raise RuntimeError("round.json candidate_sha is missing for the active round.")
                candidate_sha = pinned_candidate_sha
                if self.branch_exists(expected_branch):
                    current_candidate_sha = self.ref_sha(expected_branch)
                    if current_candidate_sha != pinned_candidate_sha:
                        raise RuntimeError("candidate branch tip does not match pinned round candidate_sha.")
            worktree_payload = self._build_worktree_payload(
                worktree_path=expected_worktree_path,
                candidate_branch=expected_branch,
                base_sha=str(round_payload.get("base_sha") or ""),
                candidate_sha=candidate_sha,
                created_at=None,
                cleaned_at=None,
            )
        runtime = dict(runtime)
        round_payload = dict(round_payload)
        worktree_payload = dict(worktree_payload)
        round_payload["round"] = round_number
        round_payload["candidate_branch"] = expected_branch
        round_payload["candidate_worktree"] = str(expected_worktree_path)
        worktree_payload["path"] = str(expected_worktree_path)
        worktree_payload["branch"] = expected_branch
        worktree_payload["base_sha"] = str(round_payload.get("base_sha") or "")
        if state != "prepared":
            worktree_payload["candidate_sha"] = pinned_candidate_sha
        else:
            worktree_payload["candidate_sha"] = pinned_candidate_sha or worktree_payload.get("candidate_sha")
        return runtime, round_payload, worktree_payload

    def promote_round(self, run_id: str) -> dict[str, Any]:
        runtime = self.load_runtime(run_id)
        active_round = runtime.get("active_round")
        if active_round is None:
            raise RuntimeError("No active round found in runtime.json")
        round_number = int(active_round)
        round_path = self.round_path(run_id, round_number)
        if not round_path.is_file():
            raise FileNotFoundError(f"Missing round file: {round_path}")
        round_payload = read_json(round_path)
        if int(round_payload.get("round") or 0) != round_number:
            raise RuntimeError("round.json round does not match runtime.json active_round.")
        state = str(round_payload.get("state") or "")
        if state not in {"evaluated", "accepted"}:
            raise RuntimeError("promote-round requires the active round to be in evaluated state.")
        round_number = int(round_payload["round"])
        decision_path = self.round_dir(run_id, round_number) / "decision.json"
        if not decision_path.is_file():
            raise RuntimeError("promote-round requires a persisted keep decision.")
        decision_payload = read_json(decision_path)
        if int(decision_payload.get("round") or 0) != round_number:
            raise RuntimeError("decision.json round does not match the active round.")
        if str(decision_payload.get("decision") or "") != "keep":
            raise RuntimeError("promote-round requires a persisted keep decision.")
        champion_branch = champion_branch_name(run_id)
        candidate_branch = candidate_branch_name(run_id, round_number)
        expected_worktree_path = self.candidate_worktree_path(run_id, round_number)
        candidate_sha = str(round_payload.get("candidate_sha") or "").strip()
        if not candidate_sha:
            raise RuntimeError("round.json candidate_sha is missing for the active round.")
        if str(decision_payload.get("candidate_sha") or "") != candidate_sha:
            raise RuntimeError("decision.json candidate_sha does not match the pinned round candidate_sha.")
        candidate_branch_exists = self.branch_exists(candidate_branch)
        champion_sha = self.ref_sha(champion_branch)
        if candidate_branch_exists:
            current_candidate_sha = self.ref_sha(candidate_branch)
            if current_candidate_sha != candidate_sha:
                raise RuntimeError("candidate branch tip does not match pinned round candidate_sha.")
            if not self.is_ancestor(champion_sha, candidate_sha):
                raise RuntimeError("Promote requires fast-forward semantics: champion is not an ancestor of candidate")
        elif state != "accepted":
            raise RuntimeError(f"Missing candidate branch: {candidate_branch}")
        if state == "evaluated":
            round_payload["state"] = "accepted"
            round_payload["candidate_sha"] = candidate_sha
            round_payload["decision"] = "keep"
            write_json(self.round_path(run_id, round_number), round_payload)
            state = "accepted"

        if champion_sha != candidate_sha:
            if not candidate_branch_exists:
                raise RuntimeError(f"Missing candidate branch: {candidate_branch}")
            self._git("update-ref", f"refs/heads/{champion_branch}", candidate_sha, champion_sha)
            runtime["champion_branch"] = champion_branch
            runtime["champion_sha"] = candidate_sha
            self.save_runtime(run_id, runtime)

        worktree_path = self.worktree_path_record(run_id, round_number)
        if worktree_path.is_file():
            worktree_payload = read_json(worktree_path)
            if str(worktree_payload.get("path") or "") != str(expected_worktree_path):
                raise RuntimeError("worktree.json path does not match deterministic candidate identity.")
            if str(worktree_payload.get("branch") or "") != candidate_branch:
                raise RuntimeError("worktree.json branch does not match deterministic candidate identity.")
            if str(worktree_payload.get("base_sha") or "") != str(round_payload.get("base_sha") or ""):
                raise RuntimeError("worktree.json base_sha does not match round.json base_sha.")
            if str(worktree_payload.get("candidate_sha") or "").strip() != candidate_sha:
                raise RuntimeError("worktree.json candidate_sha does not match pinned round candidate_sha.")
        else:
            worktree_payload = self._build_worktree_payload(
                worktree_path=expected_worktree_path,
                candidate_branch=candidate_branch,
                base_sha=str(round_payload.get("base_sha") or ""),
                candidate_sha=candidate_sha,
                created_at=None,
                cleaned_at=None,
            )
        round_payload["state"] = "accepted"
        round_payload["candidate_sha"] = candidate_sha
        round_payload["decision"] = "keep"
        write_json(self.round_path(run_id, round_number), round_payload)
        return self._finalize_cleanup(
            run_id,
            runtime=runtime,
            round_payload=round_payload,
            worktree_payload=worktree_payload,
            final_state="cleaned",
        )

    def discard_round(self, run_id: str) -> dict[str, Any]:
        runtime, round_payload, worktree_payload = self._load_cleanup_state(run_id)
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
        runtime, round_payload, worktree_payload = self._load_cleanup_state(run_id)
        return self._finalize_cleanup(
            run_id,
            runtime=runtime,
            round_payload=round_payload,
            worktree_payload=worktree_payload,
            final_state="cleaned",
        )
