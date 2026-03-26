from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from worktree_manager import WorktreeManager, candidate_branch_name, champion_branch_name, read_json


class WorktreeManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.repo_root = self.root / "repo"
        self.repo_root.mkdir(parents=True, exist_ok=True)
        self.run_id = "demo-run"
        self.manager = WorktreeManager(
            repo_root=self.repo_root,
            autoresearch_root=self.repo_root / ".autoworkflow" / "autoresearch",
        )

        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "tester")
        (self.repo_root / ".gitignore").write_text(".autoworkflow/\n", encoding="utf-8")
        (self.repo_root / "README.md").write_text("initial\n", encoding="utf-8")
        self._git("add", ".gitignore", "README.md")
        self._git("commit", "-q", "-m", "init")

        self.initial_branch = self._git_output("branch", "--show-current")
        self.initial_head = self._git_output("rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _git(self, *args: str, cwd: Path | None = None) -> None:
        subprocess.run(
            ["git", *args],
            cwd=cwd or self.repo_root,
            check=True,
            capture_output=True,
            text=True,
        )

    def _git_output(self, *args: str, cwd: Path | None = None) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=cwd or self.repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    def test_prepare_round_creates_candidate_branch_worktree_and_state(self) -> None:
        result = self.manager.prepare_round(self.run_id)

        candidate_path = Path(result["worktree"]["path"])
        runtime = read_json(self.manager.runtime_path(self.run_id))
        round_payload = read_json(self.manager.round_path(self.run_id, 1))
        worktree_payload = read_json(self.manager.worktree_path_record(self.run_id, 1))

        self.assertTrue(candidate_path.is_dir())
        self.assertTrue(self.manager.branch_exists(champion_branch_name(self.run_id)))
        self.assertTrue(self.manager.branch_exists(candidate_branch_name(self.run_id, 1)))
        self.assertEqual(runtime["active_round"], 1)
        self.assertEqual(runtime["active_candidate_branch"], candidate_branch_name(self.run_id, 1))
        self.assertEqual(round_payload["state"], "candidate_active")
        self.assertEqual(worktree_payload["branch"], candidate_branch_name(self.run_id, 1))
        self.assertEqual(self._git_output("branch", "--show-current"), self.initial_branch)
        self.assertEqual(self._git_output("status", "--porcelain"), "")

    def test_prepare_round_rejects_second_active_candidate(self) -> None:
        self.manager.prepare_round(self.run_id)

        with self.assertRaisesRegex(RuntimeError, "active round already exists"):
            self.manager.prepare_round(self.run_id)

        self.assertEqual(self._git_output("branch", "--show-current"), self.initial_branch)
        self.assertEqual(self._git_output("status", "--porcelain"), "")

    def test_promote_round_fast_forwards_champion_and_cleans_candidate(self) -> None:
        result = self.manager.prepare_round(self.run_id)
        candidate_path = Path(result["worktree"]["path"])

        (candidate_path / "README.md").write_text("candidate-change\n", encoding="utf-8")
        self._git("add", "README.md", cwd=candidate_path)
        self._git("commit", "-q", "-m", "candidate-commit", cwd=candidate_path)
        candidate_sha = self._git_output("rev-parse", "HEAD", cwd=candidate_path)

        self.manager.promote_round(self.run_id)

        runtime = read_json(self.manager.runtime_path(self.run_id))
        round_payload = read_json(self.manager.round_path(self.run_id, 1))
        worktree_payload = read_json(self.manager.worktree_path_record(self.run_id, 1))

        self.assertEqual(self._git_output("rev-parse", champion_branch_name(self.run_id)), candidate_sha)
        self.assertEqual(runtime["champion_sha"], candidate_sha)
        self.assertIsNone(runtime["active_round"])
        self.assertFalse(candidate_path.exists())
        self.assertFalse(self.manager.branch_exists(candidate_branch_name(self.run_id, 1)))
        self.assertEqual(round_payload["state"], "cleaned")
        self.assertIsNotNone(worktree_payload["cleaned_at"])
        self.assertEqual(self._git_output("branch", "--show-current"), self.initial_branch)
        self.assertEqual(self._git_output("status", "--porcelain"), "")

    def test_promote_round_rejects_non_fast_forward_candidate(self) -> None:
        result = self.manager.prepare_round(self.run_id)
        candidate_path = Path(result["worktree"]["path"])

        (self.repo_root / "main-only.txt").write_text("main\n", encoding="utf-8")
        self._git("add", "main-only.txt")
        self._git("commit", "-q", "-m", "main-advance")
        self._git("branch", "-f", champion_branch_name(self.run_id), "HEAD")

        (candidate_path / "README.md").write_text("candidate-diverged\n", encoding="utf-8")
        self._git("add", "README.md", cwd=candidate_path)
        self._git("commit", "-q", "-m", "candidate-diverged", cwd=candidate_path)

        with self.assertRaisesRegex(RuntimeError, "fast-forward"):
            self.manager.promote_round(self.run_id)

        runtime = read_json(self.manager.runtime_path(self.run_id))
        self.assertEqual(runtime["active_round"], 1)
        self.assertTrue(candidate_path.exists())
        self.assertTrue(self.manager.branch_exists(candidate_branch_name(self.run_id, 1)))

    def test_discard_round_cleans_candidate_without_revert_noise(self) -> None:
        result = self.manager.prepare_round(self.run_id)
        candidate_path = Path(result["worktree"]["path"])
        champion_sha = self._git_output("rev-parse", champion_branch_name(self.run_id))
        main_head = self._git_output("rev-parse", "HEAD")

        self.manager.discard_round(self.run_id)

        runtime = read_json(self.manager.runtime_path(self.run_id))
        round_payload = read_json(self.manager.round_path(self.run_id, 1))
        worktree_payload = read_json(self.manager.worktree_path_record(self.run_id, 1))

        self.assertEqual(self._git_output("rev-parse", champion_branch_name(self.run_id)), champion_sha)
        self.assertEqual(self._git_output("rev-parse", "HEAD"), main_head)
        self.assertIsNone(runtime["active_round"])
        self.assertFalse(candidate_path.exists())
        self.assertFalse(self.manager.branch_exists(candidate_branch_name(self.run_id, 1)))
        self.assertEqual(round_payload["state"], "cleaned")
        self.assertIsNotNone(worktree_payload["cleaned_at"])
        self.assertEqual(self._git_output("status", "--porcelain"), "")

    def test_cleanup_round_recovers_dirty_candidate_worktree(self) -> None:
        result = self.manager.prepare_round(self.run_id)
        candidate_path = Path(result["worktree"]["path"])
        (candidate_path / "scratch.txt").write_text("dirty\n", encoding="utf-8")

        self.manager.cleanup_round(self.run_id)

        runtime = read_json(self.manager.runtime_path(self.run_id))
        round_payload = read_json(self.manager.round_path(self.run_id, 1))
        worktree_payload = read_json(self.manager.worktree_path_record(self.run_id, 1))

        self.assertIsNone(runtime["active_round"])
        self.assertFalse(candidate_path.exists())
        self.assertFalse(self.manager.branch_exists(candidate_branch_name(self.run_id, 1)))
        self.assertEqual(round_payload["state"], "cleaned")
        self.assertIsNotNone(worktree_payload["cleaned_at"])
        self.assertEqual(self._git_output("branch", "--show-current"), self.initial_branch)
        self.assertEqual(self._git_output("status", "--porcelain"), "")

    def test_prepare_round_failure_still_allows_cleanup_recovery(self) -> None:
        original_git = self.manager._git

        def failing_git(*args: str, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
            if args[:2] == ("worktree", "add"):
                raise subprocess.CalledProcessError(1, ["git", *args], stderr="simulated worktree add failure")
            return original_git(*args, check=check, cwd=cwd)

        with mock.patch.object(self.manager, "_git", side_effect=failing_git):
            with self.assertRaises(subprocess.CalledProcessError):
                self.manager.prepare_round(self.run_id)

        runtime = read_json(self.manager.runtime_path(self.run_id))
        round_payload = read_json(self.manager.round_path(self.run_id, 1))
        worktree_payload = read_json(self.manager.worktree_path_record(self.run_id, 1))
        candidate_path = Path(worktree_payload["path"])

        self.assertEqual(runtime["active_round"], 1)
        self.assertEqual(round_payload["state"], "prepared")
        self.assertFalse(candidate_path.exists())
        self.assertFalse(self.manager.branch_exists(candidate_branch_name(self.run_id, 1)))
        self.assertIsNone(worktree_payload["candidate_sha"])

        self.manager.cleanup_round(self.run_id)

        runtime = read_json(self.manager.runtime_path(self.run_id))
        round_payload = read_json(self.manager.round_path(self.run_id, 1))
        worktree_payload = read_json(self.manager.worktree_path_record(self.run_id, 1))

        self.assertIsNone(runtime["active_round"])
        self.assertEqual(round_payload["state"], "cleaned")
        self.assertIsNotNone(worktree_payload["cleaned_at"])
        self.assertFalse(candidate_path.exists())
        self.assertFalse(self.manager.branch_exists(candidate_branch_name(self.run_id, 1)))


if __name__ == "__main__":
    unittest.main()
