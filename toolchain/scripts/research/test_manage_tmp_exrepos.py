from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import manage_tmp_exrepos
from manage_tmp_exrepos import (
    ExrepoSpec,
    init_exrepo,
    load_exrepo_specs,
    main,
    parse_args,
    prepare_exrepo,
    reset_exrepo,
    select_exrepo_specs,
)


class ManageTmpExreposTest(unittest.TestCase):
    def _write_repo_list(self, root: Path) -> Path:
        repo_list = root / "exrepo.txt"
        repo_list.write_text(
            "fastapi/typer\n"
            "pmndrs/zustand\n",
            encoding="utf-8",
        )
        return repo_list

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

    def test_load_exrepo_specs_rejects_target_dir_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_list = Path(tmp) / "exrepo.txt"
            repo_list.write_text(
                "evil/..\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Invalid local repo target"):
                load_exrepo_specs(repo_list)

    def test_parse_args_legacy_mode_defaults_to_prepare(self) -> None:
        args = parse_args(["--repo-list", "catalog.txt"])
        self.assertEqual(args.command, "prepare")
        self.assertEqual(args.repo, [])
        self.assertIsNone(args.suite)
        self.assertTrue(args.legacy_mode)

    def test_parse_args_subcommand_mode(self) -> None:
        args = parse_args(["init", "--repo", "typer"])
        self.assertEqual(args.command, "init")
        self.assertEqual(args.repo, ["typer"])
        self.assertFalse(args.legacy_mode)

    def test_parse_args_rejects_selector_without_subcommand(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_args(["--repo", "typer"])

    def test_select_exrepo_specs_with_explicit_repo_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specs = load_exrepo_specs(self._write_repo_list(root))
            selected = select_exrepo_specs(
                specs,
                selected_repo_names=["zustand", "typer", "zustand"],
                suite_path=None,
                exrepo_root=root / "tmp-exrepos",
            )
            self.assertEqual([spec.target_dirname for spec in selected], ["zustand", "typer"])

    def test_select_exrepo_specs_rejects_unknown_explicit_repo_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specs = load_exrepo_specs(self._write_repo_list(root))

            with self.assertRaisesRegex(ValueError, "Unknown local repo target"):
                select_exrepo_specs(
                    specs,
                    selected_repo_names=["unknown-repo"],
                    suite_path=None,
                    exrepo_root=root / "tmp-exrepos",
                )

    def test_select_exrepo_specs_from_suite_repo_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specs = load_exrepo_specs(self._write_repo_list(root))
            exrepo_root = root / "tmp-exrepos"
            suite_path = root / "suite.json"
            suite_path.write_text(
                (
                    '{"version":1,"runs":['
                    '{"repo":"typer"},'
                    f'{{"repo":"{(exrepo_root / "zustand").as_posix()}"}},'
                    '{"repo":"typer"}'
                    "]}"
                ),
                encoding="utf-8",
            )

            selected = select_exrepo_specs(
                specs,
                selected_repo_names=[],
                suite_path=suite_path,
                exrepo_root=exrepo_root,
            )

            self.assertEqual([spec.target_dirname for spec in selected], ["typer", "zustand"])

    def test_select_exrepo_specs_accepts_relative_suite_repo_path_to_direct_child(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specs = load_exrepo_specs(self._write_repo_list(root))
            exrepo_root = root / "tmp-exrepos"
            suite_dir = root / "suites"
            suite_dir.mkdir(parents=True, exist_ok=True)
            suite_path = suite_dir / "suite.json"
            suite_path.write_text(
                '{"version":1,"runs":[{"repo":"../tmp-exrepos/typer"}]}',
                encoding="utf-8",
            )

            selected = select_exrepo_specs(
                specs,
                selected_repo_names=[],
                suite_path=suite_path,
                exrepo_root=exrepo_root,
            )

            self.assertEqual([spec.target_dirname for spec in selected], ["typer"])

    def test_select_exrepo_specs_rejects_suite_repo_path_outside_tmp_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specs = load_exrepo_specs(self._write_repo_list(root))
            exrepo_root = root / "tmp-exrepos"
            suite_path = root / "suite.json"
            outside_repo = (root / "outside" / "typer").as_posix()
            suite_path.write_text(
                f'{{"version":1,"runs":[{{"repo":"{outside_repo}"}}]}}',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "direct child of the tmp exrepo root"):
                select_exrepo_specs(
                    specs,
                    selected_repo_names=[],
                    suite_path=suite_path,
                    exrepo_root=exrepo_root,
                )

    def test_select_exrepo_specs_rejects_suite_repo_basename_not_in_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specs = load_exrepo_specs(self._write_repo_list(root))
            exrepo_root = root / "tmp-exrepos"
            suite_dir = root / "suites"
            suite_dir.mkdir(parents=True, exist_ok=True)
            suite_path = suite_dir / "suite.json"
            suite_path.write_text(
                '{"version":1,"runs":[{"repo":"../tmp-exrepos/not-in-catalog"}]}',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Suite repo basename is not in the repo catalog"):
                select_exrepo_specs(
                    specs,
                    selected_repo_names=[],
                    suite_path=suite_path,
                    exrepo_root=exrepo_root,
                )

    def test_select_exrepo_specs_rejects_empty_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specs = load_exrepo_specs(self._write_repo_list(root))
            suite_path = root / "suite.json"
            suite_path.write_text('{"version":1,"runs":[]}', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "must define a non-empty 'runs' list"):
                select_exrepo_specs(
                    specs,
                    selected_repo_names=[],
                    suite_path=suite_path,
                    exrepo_root=root / "tmp-exrepos",
                )

    def test_select_exrepo_specs_rejects_non_list_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            specs = load_exrepo_specs(self._write_repo_list(root))
            suite_path = root / "suite.json"
            suite_path.write_text('{"version":1,"runs":{"repo":"typer"}}', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "must define a non-empty 'runs' list"):
                select_exrepo_specs(
                    specs,
                    selected_repo_names=[],
                    suite_path=suite_path,
                    exrepo_root=root / "tmp-exrepos",
                )

    def test_init_exrepo_clones_missing_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")
            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.return_value = subprocess.CompletedProcess(["git", "clone"], 0, "", "")
                result = init_exrepo(spec, root)

            self.assertEqual(result, "cloned")
            run_git.assert_called_once_with(
                ["clone", "https://github.com/fastapi/typer.git", str(root / "typer")]
            )

    def test_init_exrepo_keeps_existing_valid_repo_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "typer"
            (target / ".git").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")

            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.side_effect = [
                    subprocess.CompletedProcess(
                        ["git", "remote", "get-url", "origin"],
                        0,
                        "https://github.com/fastapi/typer.git\n",
                        "",
                    ),
                ]
                result = init_exrepo(spec, root)

            self.assertEqual(result, "kept")
            self.assertEqual(
                run_git.call_args_list,
                [
                    mock.call(["remote", "get-url", "origin"], cwd=target),
                ],
            )

    def test_init_exrepo_rejects_existing_non_git_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "typer").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")

            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                with self.assertRaisesRegex(RuntimeError, "Target exists but is not a git repo"):
                    init_exrepo(spec, root)
            run_git.assert_not_called()

    def test_init_exrepo_fails_closed_on_origin_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "typer"
            (target / ".git").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")

            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.return_value = subprocess.CompletedProcess(
                    ["git", "remote", "get-url", "origin"],
                    0,
                    "https://github.com/acme/other.git\n",
                    "",
                )
                with self.assertRaisesRegex(RuntimeError, "origin mismatch"):
                    init_exrepo(spec, root)

    def test_init_exrepo_reports_clone_failure_formatting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")
            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.return_value = subprocess.CompletedProcess(
                    ["git", "clone"],
                    128,
                    "",
                    "fatal: clone failed",
                )
                with self.assertRaises(RuntimeError) as raised:
                    init_exrepo(spec, root)

            message = str(raised.exception)
            self.assertIn("git clone failed for fastapi/typer", message)
            self.assertIn(str(root / "typer"), message)
            self.assertIn("fatal: clone failed", message)

    def test_init_exrepo_rejects_target_that_resolves_outside_tmp_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "tmp-exrepos"
            root.mkdir(parents=True, exist_ok=True)
            external_repo = Path(tmp) / "external-repo"
            (external_repo / ".git").mkdir(parents=True, exist_ok=True)
            (root / "typer").symlink_to(external_repo, target_is_directory=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")

            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                with self.assertRaisesRegex(RuntimeError, "outside tmp exrepo root"):
                    init_exrepo(spec, root)
            run_git.assert_not_called()

    def test_reset_exrepo_fails_when_repo_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")
            with self.assertRaisesRegex(RuntimeError, "missing for reset"):
                reset_exrepo(spec, root)

    def test_reset_exrepo_rejects_existing_non_git_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "typer").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")

            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                with self.assertRaisesRegex(RuntimeError, "Target exists but is not a git repo"):
                    reset_exrepo(spec, root)
            run_git.assert_not_called()

    def test_reset_exrepo_rejects_target_that_resolves_outside_tmp_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "tmp-exrepos"
            root.mkdir(parents=True, exist_ok=True)
            external_repo = Path(tmp) / "external-repo"
            (external_repo / ".git").mkdir(parents=True, exist_ok=True)
            (root / "typer").symlink_to(external_repo, target_is_directory=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")

            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                with self.assertRaisesRegex(RuntimeError, "outside tmp exrepo root"):
                    reset_exrepo(spec, root)
            run_git.assert_not_called()

    def test_reset_exrepo_hard_resets_to_origin_default_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "typer"
            (target / ".git").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")

            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.side_effect = [
                    subprocess.CompletedProcess(
                        ["git", "remote", "get-url", "origin"],
                        0,
                        "https://github.com/fastapi/typer.git\n",
                        "",
                    ),
                    subprocess.CompletedProcess(["git", "fetch", "origin"], 0, "", ""),
                    subprocess.CompletedProcess(
                        ["git", "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
                        0,
                        "origin/main\n",
                        "",
                    ),
                    subprocess.CompletedProcess(["git", "reset", "--hard", "origin/main"], 0, "", ""),
                    subprocess.CompletedProcess(
                        ["git", "checkout", "-B", "main", "origin/main"],
                        0,
                        "",
                        "",
                    ),
                ]

                result = reset_exrepo(spec, root)

            self.assertEqual(result, "reset")
            self.assertEqual(
                run_git.call_args_list,
                [
                    mock.call(["remote", "get-url", "origin"], cwd=target),
                    mock.call(["fetch", "origin"], cwd=target),
                    mock.call(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"], cwd=target),
                    mock.call(["reset", "--hard", "origin/main"], cwd=target),
                    mock.call(["checkout", "-B", "main", "origin/main"], cwd=target),
                ],
            )

    def test_reset_exrepo_reports_remote_get_url_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "typer"
            (target / ".git").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")
            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.return_value = subprocess.CompletedProcess(
                    ["git", "remote", "get-url", "origin"],
                    2,
                    "",
                    "fatal: no origin",
                )
                with self.assertRaises(RuntimeError) as raised:
                    reset_exrepo(spec, root)
            self.assertIn("git remote get-url origin failed for fastapi/typer", str(raised.exception))
            self.assertIn("fatal: no origin", str(raised.exception))

    def test_reset_exrepo_rejects_non_github_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "typer"
            (target / ".git").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")
            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.return_value = subprocess.CompletedProcess(
                    ["git", "remote", "get-url", "origin"],
                    0,
                    "https://gitlab.com/fastapi/typer.git\n",
                    "",
                )
                with self.assertRaisesRegex(RuntimeError, "not a supported GitHub remote"):
                    reset_exrepo(spec, root)

    def test_reset_exrepo_rejects_origin_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "typer"
            (target / ".git").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")
            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.return_value = subprocess.CompletedProcess(
                    ["git", "remote", "get-url", "origin"],
                    0,
                    "https://github.com/acme/typer.git\n",
                    "",
                )
                with self.assertRaisesRegex(RuntimeError, "origin mismatch"):
                    reset_exrepo(spec, root)

    def test_reset_exrepo_reports_fetch_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "typer"
            (target / ".git").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")
            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.side_effect = [
                    subprocess.CompletedProcess(
                        ["git", "remote", "get-url", "origin"],
                        0,
                        "https://github.com/fastapi/typer.git\n",
                        "",
                    ),
                    subprocess.CompletedProcess(["git", "fetch", "origin"], 1, "", "fatal: fetch failed"),
                ]
                with self.assertRaises(RuntimeError) as raised:
                    reset_exrepo(spec, root)
            self.assertIn("git fetch origin failed for fastapi/typer", str(raised.exception))
            self.assertIn("fatal: fetch failed", str(raised.exception))

    def test_reset_exrepo_reports_remote_set_head_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "typer"
            (target / ".git").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")
            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.side_effect = [
                    subprocess.CompletedProcess(
                        ["git", "remote", "get-url", "origin"],
                        0,
                        "https://github.com/fastapi/typer.git\n",
                        "",
                    ),
                    subprocess.CompletedProcess(["git", "fetch", "origin"], 0, "", ""),
                    subprocess.CompletedProcess(
                        ["git", "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
                        1,
                        "",
                        "fatal: missing",
                    ),
                    subprocess.CompletedProcess(
                        ["git", "remote", "set-head", "origin", "--auto"],
                        1,
                        "",
                        "fatal: set-head failed",
                    ),
                ]
                with self.assertRaises(RuntimeError) as raised:
                    reset_exrepo(spec, root)
            self.assertIn("git remote set-head origin --auto failed for fastapi/typer", str(raised.exception))
            self.assertIn("fatal: set-head failed", str(raised.exception))

    def test_reset_exrepo_rejects_malformed_origin_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "typer"
            (target / ".git").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")
            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.side_effect = [
                    subprocess.CompletedProcess(
                        ["git", "remote", "get-url", "origin"],
                        0,
                        "https://github.com/fastapi/typer.git\n",
                        "",
                    ),
                    subprocess.CompletedProcess(["git", "fetch", "origin"], 0, "", ""),
                    subprocess.CompletedProcess(
                        ["git", "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
                        0,
                        "main\n",
                        "",
                    ),
                ]
                with self.assertRaisesRegex(RuntimeError, "Unexpected origin/HEAD symbolic ref"):
                    reset_exrepo(spec, root)

    def test_reset_exrepo_fails_when_default_branch_cannot_be_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "typer"
            (target / ".git").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")

            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.side_effect = [
                    subprocess.CompletedProcess(
                        ["git", "remote", "get-url", "origin"],
                        0,
                        "https://github.com/fastapi/typer.git\n",
                        "",
                    ),
                    subprocess.CompletedProcess(["git", "fetch", "origin"], 0, "", ""),
                    subprocess.CompletedProcess(
                        ["git", "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
                        1,
                        "",
                        "missing",
                    ),
                    subprocess.CompletedProcess(["git", "remote", "set-head", "origin", "--auto"], 0, "", ""),
                    subprocess.CompletedProcess(
                        ["git", "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
                        1,
                        "",
                        "still missing",
                    ),
                ]

                with self.assertRaisesRegex(RuntimeError, "origin/HEAD unresolved after one refresh attempt"):
                    reset_exrepo(spec, root)

            self.assertEqual(
                run_git.call_args_list,
                [
                    mock.call(["remote", "get-url", "origin"], cwd=target),
                    mock.call(["fetch", "origin"], cwd=target),
                    mock.call(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"], cwd=target),
                    mock.call(["remote", "set-head", "origin", "--auto"], cwd=target),
                    mock.call(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"], cwd=target),
                ],
            )

    def test_prepare_exrepo_clones_missing_then_resets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")

            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.side_effect = [
                    subprocess.CompletedProcess(["git", "clone"], 0, "", ""),
                    subprocess.CompletedProcess(
                        ["git", "remote", "get-url", "origin"],
                        0,
                        "https://github.com/fastapi/typer.git\n",
                        "",
                    ),
                    subprocess.CompletedProcess(["git", "fetch", "origin"], 0, "", ""),
                    subprocess.CompletedProcess(
                        ["git", "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
                        0,
                        "origin/main\n",
                        "",
                    ),
                    subprocess.CompletedProcess(["git", "reset", "--hard", "origin/main"], 0, "", ""),
                    subprocess.CompletedProcess(
                        ["git", "checkout", "-B", "main", "origin/main"],
                        0,
                        "",
                        "",
                    ),
                ]

                result = prepare_exrepo(spec, root)

            self.assertEqual(result, "cloned_then_reset")
            self.assertEqual(
                run_git.call_args_list,
                [
                    mock.call(["clone", "https://github.com/fastapi/typer.git", str(root / "typer")]),
                    mock.call(["remote", "get-url", "origin"], cwd=root / "typer"),
                    mock.call(["fetch", "origin"], cwd=root / "typer"),
                    mock.call(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"], cwd=root / "typer"),
                    mock.call(["reset", "--hard", "origin/main"], cwd=root / "typer"),
                    mock.call(["checkout", "-B", "main", "origin/main"], cwd=root / "typer"),
                ],
            )

    def test_prepare_exrepo_existing_valid_repo_returns_reset_without_clone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "typer"
            (target / ".git").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")
            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                run_git.side_effect = [
                    subprocess.CompletedProcess(
                        ["git", "remote", "get-url", "origin"],
                        0,
                        "https://github.com/fastapi/typer.git\n",
                        "",
                    ),
                    subprocess.CompletedProcess(["git", "fetch", "origin"], 0, "", ""),
                    subprocess.CompletedProcess(
                        ["git", "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
                        0,
                        "origin/main\n",
                        "",
                    ),
                    subprocess.CompletedProcess(["git", "reset", "--hard", "origin/main"], 0, "", ""),
                    subprocess.CompletedProcess(
                        ["git", "checkout", "-B", "main", "origin/main"],
                        0,
                        "",
                        "",
                    ),
                ]
                result = prepare_exrepo(spec, root)

            self.assertEqual(result, "reset")
            self.assertEqual(
                run_git.call_args_list,
                [
                    mock.call(["remote", "get-url", "origin"], cwd=target),
                    mock.call(["fetch", "origin"], cwd=target),
                    mock.call(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"], cwd=target),
                    mock.call(["reset", "--hard", "origin/main"], cwd=target),
                    mock.call(["checkout", "-B", "main", "origin/main"], cwd=target),
                ],
            )

    def test_prepare_exrepo_rejects_existing_non_git_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "typer").mkdir(parents=True, exist_ok=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")
            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                with self.assertRaisesRegex(RuntimeError, "Target exists but is not a git repo"):
                    prepare_exrepo(spec, root)
            run_git.assert_not_called()

    def test_prepare_exrepo_rejects_target_that_resolves_outside_tmp_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "tmp-exrepos"
            root.mkdir(parents=True, exist_ok=True)
            external_repo = Path(tmp) / "external-repo"
            (external_repo / ".git").mkdir(parents=True, exist_ok=True)
            (root / "typer").symlink_to(external_repo, target_is_directory=True)
            spec = ExrepoSpec(raw="fastapi/typer", owner="fastapi", name="typer")

            with mock.patch.object(manage_tmp_exrepos, "run_git") as run_git:
                with self.assertRaisesRegex(RuntimeError, "outside tmp exrepo root"):
                    prepare_exrepo(spec, root)

            run_git.assert_not_called()

    def test_main_legacy_flat_mode_dispatches_prepare(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_list = self._write_repo_list(root)
            exrepo_root = root / "tmp-exrepos"
            exrepo_root.mkdir(parents=True, exist_ok=True)
            with mock.patch.object(
                manage_tmp_exrepos,
                "resolve_tmp_exrepos_root",
                return_value=exrepo_root,
            ), mock.patch.object(
                manage_tmp_exrepos,
                "sync_exrepo",
                return_value="reset",
            ) as sync_exrepo_mock:
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

            self.assertEqual(exit_code, 0)
            self.assertEqual(sync_exrepo_mock.call_count, 2)
            for call in sync_exrepo_mock.call_args_list:
                self.assertEqual(call.kwargs["mode"], "prepare")

    def test_main_subcommand_dispatches_init(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_list = self._write_repo_list(root)
            exrepo_root = root / "tmp-exrepos"
            exrepo_root.mkdir(parents=True, exist_ok=True)
            with mock.patch.object(
                manage_tmp_exrepos,
                "resolve_tmp_exrepos_root",
                return_value=exrepo_root,
            ), mock.patch.object(
                manage_tmp_exrepos,
                "sync_exrepo",
                return_value="kept",
            ) as sync_exrepo_mock:
                exit_code = main(
                    [
                        "init",
                        "--repo-list",
                        str(repo_list),
                        "--repo",
                        "typer",
                        "--repo-root",
                        str(root / "repo-root"),
                        "--temp-root",
                        str(root / "os-tmp"),
                    ]
                )

            self.assertEqual(exit_code, 0)
            sync_exrepo_mock.assert_called_once()
            self.assertEqual(sync_exrepo_mock.call_args.kwargs["mode"], "init")

    def test_main_returns_error_prefix_and_exit_1_on_selection_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_list = self._write_repo_list(root)
            exrepo_root = root / "tmp-exrepos"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), mock.patch.object(
                manage_tmp_exrepos,
                "resolve_tmp_exrepos_root",
                return_value=exrepo_root,
            ), mock.patch.object(manage_tmp_exrepos, "sync_exrepo") as sync_exrepo_mock:
                exit_code = main(
                    [
                        "init",
                        "--repo-list",
                        str(repo_list),
                        "--repo",
                        "not-in-catalog",
                    ]
                )

            self.assertEqual(exit_code, 1)
            self.assertIn("error:", stderr.getvalue())
            sync_exrepo_mock.assert_not_called()

    def test_main_returns_failed_and_sync_failed_on_per_repo_sync_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_list = self._write_repo_list(root)
            exrepo_root = root / "tmp-exrepos"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), mock.patch.object(
                manage_tmp_exrepos,
                "resolve_tmp_exrepos_root",
                return_value=exrepo_root,
            ), mock.patch.object(
                manage_tmp_exrepos,
                "sync_exrepo",
                side_effect=[RuntimeError("boom"), "reset"],
            ) as sync_exrepo_mock:
                exit_code = main(
                    [
                        "reset",
                        "--repo-list",
                        str(repo_list),
                    ]
                )

            self.assertEqual(exit_code, 1)
            self.assertEqual(sync_exrepo_mock.call_count, 2)
            error_text = stderr.getvalue()
            self.assertIn("failed:", error_text)
            self.assertIn("sync_failed:", error_text)


if __name__ == "__main__":
    unittest.main()
