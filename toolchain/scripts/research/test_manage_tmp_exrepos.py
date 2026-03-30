from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import manage_tmp_exrepos
from manage_tmp_exrepos import ExrepoSpec, load_exrepo_specs, main, sync_exrepo


class ManageTmpExreposTest(unittest.TestCase):
    def test_load_exrepo_specs_parses_owner_repo_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_list = Path(tmp) / "exrepo.txt"
            repo_list.write_text(
                "# comment\n"
                "\n"
                "fastapi/typer\n"
                "pmndrs/zustand\n",
                encoding="utf-8",
            )

            specs = load_exrepo_specs(repo_list)

            self.assertEqual(
                specs,
                [
                    ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer"),
                    ExrepoSpec(raw="pmndrs/zustand", owner="pmndrs", name="zustand"),
                ],
            )

    def test_load_exrepo_specs_rejects_duplicate_local_repo_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_list = Path(tmp) / "exrepo.txt"
            repo_list.write_text(
                "fastapi/typer\n"
                "acme/typer\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Duplicate local repo target"):
                load_exrepo_specs(repo_list)

    def test_sync_exrepo_clones_missing_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")

            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.return_value = subprocess.CompletedProcess(["git", "clone"], 0, "", "")

                result = sync_exrepo(spec, root)

            self.assertEqual(result, "cloned")
            run_git.assert_called_once_with(
                ["clone", "https://github.com/fastapi/typer.git", str(root / "typer")]
            )

    def test_sync_exrepo_pulls_existing_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "typer"
            (target / ".git").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")

            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.return_value = subprocess.CompletedProcess(["git", "pull"], 0, "", "")

                result = sync_exrepo(spec, root)

            self.assertEqual(result, "pulled")
            run_git.assert_called_once_with(["pull"], cwd=target)

    def test_sync_exrepo_resets_and_retries_pull_after_pull_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "typer"
            (target / ".git").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")

            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.side_effect = [
                    subprocess.CompletedProcess(["git", "pull"], 1, "", "dirty tree"),
                    subprocess.CompletedProcess(["git", "reset", "--hard"], 0, "", ""),
                    subprocess.CompletedProcess(["git", "pull"], 0, "", ""),
                ]

                result = sync_exrepo(spec, root)

            self.assertEqual(result, "reset_then_pulled")
            self.assertEqual(
                run_git.call_args_list,
                [
                    mock.call(["pull"], cwd=target),
                    mock.call(["reset", "--hard"], cwd=target),
                    mock.call(["pull"], cwd=target),
                ],
            )

    def test_main_returns_nonzero_when_a_repo_sync_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_list = root / "exrepo.txt"
            repo_list.write_text("fastapi/typer\n", encoding="utf-8")

            with mock.patch.object(manage_tmp_exrepos, "sync_exrepo", side_effect=RuntimeError("boom")):
                exit_code = main(
                    [
                        "--repo-list",
                        str(repo_list),
                        "--repo-root",
                        str(root / "repo-root"),
                        "--temp-root",
                        str(root / "os-tmp"),
                    ]
                )

            self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
