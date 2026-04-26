#!/usr/bin/env python3
"""Run the repeatable closeout acceptance gate."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_ID = "closeout-governance-task-list-20260402"
LOCAL_DEPLOY_TARGET_ROOTS = {
    "agents": REPO_ROOT / ".agents" / "skills",
    "claude": REPO_ROOT / ".claude" / "skills",
    "opencode": REPO_ROOT / ".opencode" / "skills",
}
SUPPORTED_DEPLOY_VERIFY_BACKENDS = ("agents",)
DEPLOY_VERIFY_ENTRYPOINTS = (
    ("adapter", "adapter_deploy.py"),
    ("wrapper", "harness_deploy.py"),
)
EXPECTED_NPM_PACKAGE_FILES = {
    "README.md",
    "adapter_deploy.py",
    "bin/aw-installer.js",
    "bin/aw-harness-deploy.js",
    "harness_deploy.py",
    "package.json",
}
ROOT_NPM_REQUIRED_PACKAGE_FILES = {
    "package.json",
    "README.md",
    "LICENSE",
    "toolchain/scripts/deploy/adapter_deploy.py",
    "toolchain/scripts/deploy/harness_deploy.py",
    "toolchain/scripts/deploy/bin/aw-installer.js",
    "toolchain/scripts/deploy/bin/check-root-publish.js",
    "product/harness/skills/harness-skill/SKILL.md",
    "product/harness/adapters/agents/skills/harness-skill/payload.json",
}
CACHE_SCAN_ROOTS = ("docs", "product", "toolchain", "tools")
CACHE_DIR_NAMES = {"__pycache__", ".pytest_cache"}
CACHE_FILE_SUFFIXES = (".pyc", ".pyo")


@dataclass
class GateStep:
    gate: str
    required: bool = True


def extract_verify_issue_codes(stdout: str) -> list[str]:
    return re.findall(r"^\s+- ([a-z0-9-]+):", stdout, flags=re.MULTILINE)


def find_primary_worktree_root(repo_root: Path) -> Path | None:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "worktree", "list", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    )
    candidates: list[Path] = []
    for line in completed.stdout.splitlines():
        if not line.startswith("worktree "):
            continue
        path = Path(line.split(" ", 1)[1]).resolve()
        if path == repo_root:
            continue
        candidates.append(path)

    for path in candidates:
        if "/.worktrees/" not in path.as_posix():
            return path
    return candidates[0] if candidates else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the closeout acceptance gate.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--workflow-id", default=WORKFLOW_ID)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON only.",
    )
    return parser.parse_args()


def run_command(command: list[str], *, cwd: Path, extra_env: dict[str, str] | None = None) -> dict:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if extra_env:
        env.update(extra_env)
    try:
        completed = subprocess.run(command, capture_output=True, text=True, cwd=cwd, env=env)
    except FileNotFoundError as error:
        return {
            "command": command,
            "returncode": 127,
            "stdout": "",
            "stderr": str(error),
            "passed": False,
        }
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }


def run_scope_gate(repo_root: Path, python: str) -> dict:
    return run_command(
        [
            python,
            str(repo_root / "tools" / "scope_gate_check.py"),
            "--repo-root",
            str(repo_root),
            "--json",
            "--allowed-prefix",
            "README.md",
            "--allowed-prefix",
            "docs/README.md",
            "--allowed-prefix",
            "AGENTS.md",
            "--allowed-prefix",
            "CONTRIBUTING.md",
            "--allowed-prefix",
            ".codex/",
            "--allowed-prefix",
            ".github/",
            "--allowed-prefix",
            "docs/project-maintenance/README.md",
            "--allowed-prefix",
            "docs/harness/",
            "--allowed-prefix",
            "docs/project-maintenance/governance/review-verify-handbook.md",
            "--allowed-prefix",
            "docs/project-maintenance/foundations/root-directory-layering.md",
            "--allowed-prefix",
            "toolchain/toolchain-layering.md",
            "--allowed-prefix",
            "product/README.md",
            "--allowed-prefix",
            "package.json",
        ],
        cwd=repo_root,
    )


def run_spec_gate(repo_root: Path, python: str) -> dict:
    subchecks = [
        (
            "folder_logic",
            run_command(
                [
                    python,
                    str(repo_root / "toolchain" / "scripts" / "test" / "folder_logic_check.py"),
                    "--repo-root",
                    str(repo_root),
                ],
                cwd=repo_root,
            ),
        ),
        (
            "path_governance",
            run_command(
                [
                    python,
                    str(repo_root / "toolchain" / "scripts" / "test" / "path_governance_check.py"),
                    "--repo-root",
                    str(repo_root),
                    "--scan-path",
                    "docs/project-maintenance",
                    "--scan-path",
                    "docs/harness",
                    "--scan-path",
                    ".autoworkflow/closeout",
                ],
                cwd=repo_root,
            ),
        ),
        (
            "governance_semantic",
            run_command(
                [
                    python,
                    str(repo_root / "toolchain" / "scripts" / "test" / "governance_semantic_check.py"),
                    "--repo-root",
                    str(repo_root),
                ],
                cwd=repo_root,
            ),
        ),
    ]
    passed = all(result["passed"] for _, result in subchecks)
    return {
        "passed": passed,
        "returncode": 0 if passed else 1,
        "subchecks": [{**result, "name": name} for name, result in subchecks],
    }


def run_static_gate(repo_root: Path, python: str) -> dict:
    del python
    scan_root = repo_root / "toolchain" / "scripts" / "test"
    checked: list[str] = []
    failures: list[str] = []
    for path in sorted(scan_root.rglob("*.py")):
        relative_path = path.relative_to(repo_root).as_posix()
        checked.append(relative_path)
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, relative_path, "exec", dont_inherit=True)
        except SyntaxError as error:
            failures.append(f"{relative_path}:{error.lineno}:{error.offset}: {error.msg}")
        except OSError as error:
            failures.append(f"{relative_path}: {error}")

    passed = not failures
    return {
        "command": ["python-syntax-check", "toolchain/scripts/test"],
        "returncode": 0 if passed else 1,
        "stdout": "\n".join(f"checked {path}" for path in checked),
        "stderr": "\n".join(failures),
        "passed": passed,
    }


def run_cache_gate(repo_root: Path, python: str) -> dict:
    del python
    checked_roots: list[str] = []
    failures: list[str] = []
    for relative_root in CACHE_SCAN_ROOTS:
        scan_root = repo_root / relative_root
        if not scan_root.exists():
            continue
        checked_roots.append(relative_root)
        for path in sorted(scan_root.rglob("*")):
            if path.name in CACHE_DIR_NAMES or path.name.endswith(CACHE_FILE_SUFFIXES):
                failures.append(path.relative_to(repo_root).as_posix())

    passed = not failures
    return {
        "command": ["cache-scan", *CACHE_SCAN_ROOTS],
        "returncode": 0 if passed else 1,
        "stdout": "\n".join(f"checked {root}" for root in checked_roots),
        "stderr": "\n".join(failures),
        "passed": passed,
    }


def run_test_gate(repo_root: Path, python: str) -> dict:
    def run_npm_package_packlist() -> dict:
        package_root = repo_root / "toolchain" / "scripts" / "deploy"
        result = run_command(["npm", "pack", "--dry-run", "--json"], cwd=package_root)
        result = {**result, "cwd": package_root.relative_to(repo_root).as_posix()}
        if not result["passed"]:
            return result
        try:
            payload = json.loads(result["stdout"])
        except json.JSONDecodeError as error:
            return {
                **result,
                "returncode": 1,
                "passed": False,
                "stderr": f"{result['stderr']}\ninvalid npm pack JSON: {error}".strip(),
            }
        if len(payload) != 1:
            return {
                **result,
                "returncode": 1,
                "passed": False,
                "stderr": f"expected one npm pack result, got {len(payload)}",
            }

        packed_files = {entry["path"] for entry in payload[0].get("files", [])}
        package_filename = payload[0].get("filename")
        failures: list[str] = []
        if packed_files != EXPECTED_NPM_PACKAGE_FILES:
            failures.append(
                "unexpected npm package files: "
                f"expected {sorted(EXPECTED_NPM_PACKAGE_FILES)}, got {sorted(packed_files)}"
            )
        if not package_filename:
            failures.append("missing npm package filename")
        else:
            artifact_path = package_root / package_filename
            if artifact_path.exists():
                failures.append(f"dry-run left package artifact: {artifact_path.relative_to(repo_root).as_posix()}")
        if failures:
            return {
                **result,
                "returncode": 1,
                "passed": False,
                "stderr": "\n".join(failures),
                "packed_files": sorted(packed_files),
            }
        return {**result, "packed_files": sorted(packed_files)}

    def run_npm_package_tarball_smoke() -> dict:
        package_root = repo_root / "toolchain" / "scripts" / "deploy"
        failures: list[str] = []
        subchecks: list[dict] = []
        package_filename = ""
        with tempfile.TemporaryDirectory() as package_dir:
            package_dir_path = Path(package_dir)
            pack_result = {
                **run_command(
                    ["npm", "pack", "--json", "--pack-destination", str(package_dir_path)],
                    cwd=package_root,
                ),
                "cwd": package_root.relative_to(repo_root).as_posix(),
            }
            subchecks.append({**pack_result, "name": "npm_pack_tarball"})
            if pack_result["passed"]:
                try:
                    payload = json.loads(pack_result["stdout"])
                except json.JSONDecodeError as error:
                    failures.append(f"invalid npm pack JSON: {error}")
                else:
                    if len(payload) != 1:
                        failures.append(f"expected one npm pack result, got {len(payload)}")
                    else:
                        package_filename = payload[0].get("filename", "")
                        package_file = package_dir_path / package_filename
                        if not package_filename:
                            failures.append("missing npm package filename")
                        elif not package_file.is_file():
                            failures.append(f"packed tarball was not created: {package_file}")
                        elif (package_root / package_filename).exists():
                            failures.append(
                                "packed tarball was written into repo: "
                                f"{(package_root / package_filename).relative_to(repo_root).as_posix()}"
                            )

            if pack_result["passed"] and not failures:
                package_file = package_dir_path / package_filename
                exec_result = run_command(
                    [
                        "npm",
                        "exec",
                        "--yes",
                        "--package",
                        str(package_file),
                        "--",
                        "aw-installer",
                        "--help",
                    ],
                    cwd=package_root,
                )
                if exec_result["passed"]:
                    for required_text in (
                        "aw-installer",
                        "harness_deploy.py",
                        "tui",
                        "diagnose",
                        "verify",
                        "install",
                        "update",
                    ):
                        if required_text not in exec_result["stdout"]:
                            failures.append(f"tarball help omitted {required_text!r}")
                subchecks.append({**exec_result, "name": "npm_exec_tarball"})
                version_result = run_command(
                    [
                        "npm",
                        "exec",
                        "--yes",
                        "--package",
                        str(package_file),
                        "--",
                        "aw-installer",
                        "--version",
                    ],
                    cwd=package_root,
                )
                if version_result["passed"] and "0.0.0-local" not in version_result["stdout"]:
                    failures.append("tarball version probe omitted package version")
                subchecks.append({**version_result, "name": "npm_exec_tarball_version"})
                diagnose_result = run_command(
                    [
                        "npm",
                        "exec",
                        "--yes",
                        "--package",
                        str(package_file),
                        "--",
                        "aw-installer",
                        "diagnose",
                        "--backend",
                        "agents",
                        "--json",
                    ],
                    cwd=package_root,
                    extra_env={"AW_HARNESS_REPO_ROOT": str(repo_root)},
                )
                if diagnose_result["passed"]:
                    try:
                        diagnose_payload = json.loads(diagnose_result["stdout"])
                    except json.JSONDecodeError as error:
                        failures.append(f"invalid packaged diagnose JSON: {error}")
                    else:
                        if diagnose_payload.get("backend") != "agents":
                            failures.append("packaged diagnose did not report agents backend")
                        if diagnose_payload.get("binding_count", 0) <= 0:
                            failures.append("packaged diagnose did not load source bindings")
                subchecks.append({**diagnose_result, "name": "npm_exec_tarball_diagnose"})
                update_result = run_command(
                    [
                        "npm",
                        "exec",
                        "--yes",
                        "--package",
                        str(package_file),
                        "--",
                        "aw-installer",
                        "update",
                        "--backend",
                        "agents",
                        "--json",
                    ],
                    cwd=package_root,
                    extra_env={"AW_HARNESS_REPO_ROOT": str(repo_root)},
                )
                if update_result["passed"]:
                    try:
                        update_payload = json.loads(update_result["stdout"])
                    except json.JSONDecodeError as error:
                        failures.append(f"invalid packaged update JSON: {error}")
                    else:
                        if update_payload.get("backend") != "agents":
                            failures.append("packaged update did not report agents backend")
                        if update_payload.get("blocking_issue_count", 0) != 0:
                            failures.append("packaged update dry-run reported blocking issues")
                        if not update_payload.get("planned_target_paths"):
                            failures.append("packaged update dry-run did not report target paths")
                subchecks.append({**update_result, "name": "npm_exec_tarball_update_dry_run"})

        passed = all(result["passed"] for result in subchecks) and not failures
        return {
            "command": ["npm-package-tarball-smoke"],
            "returncode": 0 if passed else 1,
            "stdout": "",
            "stderr": "\n".join(failures),
            "passed": passed,
            "subchecks": subchecks,
        }

    def run_root_npm_package_packlist() -> dict:
        result = run_command(["npm", "pack", "--dry-run", "--json"], cwd=repo_root)
        result = {**result, "cwd": "."}
        if not result["passed"]:
            return result
        try:
            payload = json.loads(result["stdout"])
        except json.JSONDecodeError as error:
            return {
                **result,
                "returncode": 1,
                "passed": False,
                "stderr": f"{result['stderr']}\ninvalid root npm pack JSON: {error}".strip(),
            }
        if len(payload) != 1:
            return {
                **result,
                "returncode": 1,
                "passed": False,
                "stderr": f"expected one root npm pack result, got {len(payload)}",
            }

        packed_files = {entry["path"] for entry in payload[0].get("files", [])}
        package_filename = payload[0].get("filename")
        failures: list[str] = []
        missing_files = sorted(ROOT_NPM_REQUIRED_PACKAGE_FILES - packed_files)
        if missing_files:
            failures.append(f"root npm package missing required files: {missing_files}")
        for disallowed_prefix in (".aw/", ".agents/", ".autoworkflow/", ".claude/", ".opencode/"):
            if any(path.startswith(disallowed_prefix) for path in packed_files):
                failures.append(f"root npm package included {disallowed_prefix} content")
        if not package_filename:
            failures.append("missing root npm package filename")
        else:
            artifact_path = repo_root / package_filename
            if artifact_path.exists():
                failures.append(f"dry-run left root package artifact: {artifact_path.name}")
        if failures:
            return {
                **result,
                "returncode": 1,
                "passed": False,
                "stderr": "\n".join(failures),
                "packed_files": sorted(packed_files),
            }
        return {**result, "packed_files": sorted(packed_files)}

    def run_root_npm_publish_dry_run() -> dict:
        result = run_command(["npm", "run", "publish:dry-run", "--silent"], cwd=repo_root)
        result = {**result, "cwd": "."}
        if not result["passed"]:
            return result
        try:
            payload = json.loads(result["stdout"])
        except json.JSONDecodeError as error:
            return {
                **result,
                "returncode": 1,
                "passed": False,
                "stderr": f"{result['stderr']}\ninvalid root npm publish dry-run JSON: {error}".strip(),
            }

        packed_files = {entry["path"] for entry in payload.get("files", [])}
        package_filename = payload.get("filename")
        failures: list[str] = []
        if payload.get("name") != "aw-installer":
            failures.append("publish dry-run package name is not aw-installer")
        missing_files = sorted(ROOT_NPM_REQUIRED_PACKAGE_FILES - packed_files)
        if missing_files:
            failures.append(f"root npm publish dry-run missing required files: {missing_files}")
        if not package_filename:
            failures.append("missing root npm publish dry-run package filename")
        else:
            artifact_path = repo_root / package_filename
            if artifact_path.exists():
                failures.append(f"publish dry-run left root package artifact: {artifact_path.name}")
        if failures:
            return {
                **result,
                "returncode": 1,
                "passed": False,
                "stderr": "\n".join(failures),
                "packed_files": sorted(packed_files),
            }
        return {**result, "packed_files": sorted(packed_files)}

    def run_root_npm_package_tarball_smoke() -> dict:
        failures: list[str] = []
        subchecks: list[dict] = []
        package_filename = ""
        with tempfile.TemporaryDirectory() as package_dir:
            package_dir_path = Path(package_dir)
            target_repo = package_dir_path / "target-repo"
            target_repo.mkdir()
            pack_result = {
                **run_command(
                    ["npm", "pack", "--json", "--pack-destination", str(package_dir_path)],
                    cwd=repo_root,
                ),
                "cwd": ".",
            }
            subchecks.append({**pack_result, "name": "root_npm_pack_tarball"})
            if pack_result["passed"]:
                try:
                    payload = json.loads(pack_result["stdout"])
                except json.JSONDecodeError as error:
                    failures.append(f"invalid root npm pack JSON: {error}")
                else:
                    if len(payload) != 1:
                        failures.append(f"expected one root npm pack result, got {len(payload)}")
                    else:
                        package_filename = payload[0].get("filename", "")
                        package_file = package_dir_path / package_filename
                        if not package_filename:
                            failures.append("missing root npm package filename")
                        elif not package_file.is_file():
                            failures.append(f"root packed tarball was not created: {package_file}")
                        elif (repo_root / package_filename).exists():
                            failures.append(f"root packed tarball was written into repo: {package_filename}")

            if pack_result["passed"] and not failures:
                package_file = package_dir_path / package_filename
                clean_env = {
                    "AW_HARNESS_REPO_ROOT": "",
                    "AW_HARNESS_TARGET_REPO_ROOT": "",
                }
                exec_result = run_command(
                    [
                        "npm",
                        "exec",
                        "--yes",
                        "--package",
                        str(package_file),
                        "--",
                        "aw-installer",
                        "--help",
                    ],
                    cwd=target_repo,
                    extra_env=clean_env,
                )
                if exec_result["passed"]:
                    for required_text in ("aw-installer", "harness_deploy.py", "tui", "diagnose", "update"):
                        if required_text not in exec_result["stdout"]:
                            failures.append(f"root tarball help omitted {required_text!r}")
                subchecks.append({**exec_result, "name": "root_npm_exec_tarball"})

                version_result = run_command(
                    [
                        "npm",
                        "exec",
                        "--yes",
                        "--package",
                        str(package_file),
                        "--",
                        "aw-installer",
                        "--version",
                    ],
                    cwd=target_repo,
                    extra_env=clean_env,
                )
                if version_result["passed"] and "0.0.0-local" not in version_result["stdout"]:
                    failures.append("root tarball version probe omitted package version")
                subchecks.append({**version_result, "name": "root_npm_exec_tarball_version"})

                diagnose_result = run_command(
                    [
                        "npm",
                        "exec",
                        "--yes",
                        "--package",
                        str(package_file),
                        "--",
                        "aw-installer",
                        "diagnose",
                        "--backend",
                        "agents",
                        "--json",
                    ],
                    cwd=target_repo,
                    extra_env=clean_env,
                )
                if diagnose_result["passed"]:
                    try:
                        diagnose_payload = json.loads(diagnose_result["stdout"])
                    except json.JSONDecodeError as error:
                        failures.append(f"invalid root packaged diagnose JSON: {error}")
                    else:
                        if diagnose_payload.get("backend") != "agents":
                            failures.append("root packaged diagnose did not report agents backend")
                        if diagnose_payload.get("binding_count", 0) <= 0:
                            failures.append("root packaged diagnose did not load source bindings")
                        expected_target = str(target_repo / ".agents" / "skills")
                        if diagnose_payload.get("target_root") != expected_target:
                            failures.append("root packaged diagnose did not use cwd target root")
                        if diagnose_payload.get("source_root") == str(target_repo):
                            failures.append("root packaged diagnose used target repo as source root")
                subchecks.append({**diagnose_result, "name": "root_npm_exec_tarball_diagnose"})

                update_result = run_command(
                    [
                        "npm",
                        "exec",
                        "--yes",
                        "--package",
                        str(package_file),
                        "--",
                        "aw-installer",
                        "update",
                        "--backend",
                        "agents",
                        "--json",
                    ],
                    cwd=target_repo,
                    extra_env=clean_env,
                )
                if update_result["passed"]:
                    try:
                        update_payload = json.loads(update_result["stdout"])
                    except json.JSONDecodeError as error:
                        failures.append(f"invalid root packaged update JSON: {error}")
                    else:
                        if update_payload.get("backend") != "agents":
                            failures.append("root packaged update did not report agents backend")
                        if update_payload.get("blocking_issue_count", 0) != 0:
                            failures.append("root packaged update dry-run reported blocking issues")
                        if not update_payload.get("planned_target_paths"):
                            failures.append("root packaged update did not report target paths")
                        expected_target = str(target_repo / ".agents" / "skills")
                        if update_payload.get("target_root") != expected_target:
                            failures.append("root packaged update did not use cwd target root")
                        if update_payload.get("source_root") == str(target_repo):
                            failures.append("root packaged update used target repo as source root")
                subchecks.append({**update_result, "name": "root_npm_exec_tarball_update_dry_run"})

                install_result = run_command(
                    [
                        "npm",
                        "exec",
                        "--yes",
                        "--package",
                        str(package_file),
                        "--",
                        "aw-installer",
                        "install",
                        "--backend",
                        "agents",
                    ],
                    cwd=target_repo,
                    extra_env=clean_env,
                )
                if install_result["passed"]:
                    installed_skill = target_repo / ".agents" / "skills" / "aw-harness-skill" / "SKILL.md"
                    if not installed_skill.is_file():
                        failures.append("root packaged install did not write aw-harness-skill")
                subchecks.append({**install_result, "name": "root_npm_exec_tarball_install"})

                verify_result = run_command(
                    [
                        "npm",
                        "exec",
                        "--yes",
                        "--package",
                        str(package_file),
                        "--",
                        "aw-installer",
                        "verify",
                        "--backend",
                        "agents",
                    ],
                    cwd=target_repo,
                    extra_env=clean_env,
                )
                subchecks.append({**verify_result, "name": "root_npm_exec_tarball_verify"})

        passed = all(result["passed"] for result in subchecks) and not failures
        return {
            "command": ["root-npm-package-tarball-smoke"],
            "returncode": 0 if passed else 1,
            "stdout": "",
            "stderr": "\n".join(failures),
            "passed": passed,
            "subchecks": subchecks,
        }

    def run_local_deploy_verify(backend: str, script_name: str) -> dict:
        command = [
            python,
            str(repo_root / "toolchain" / "scripts" / "deploy" / script_name),
            "verify",
            "--backend",
            backend,
        ]
        result = run_command(command, cwd=repo_root)
        issue_codes = extract_verify_issue_codes(result["stdout"])
        if (
            not result["passed"]
            and issue_codes
            and all(code == "missing-target-root" for code in issue_codes)
        ):
            target_root = repo_root / LOCAL_DEPLOY_TARGET_ROOTS[backend].relative_to(REPO_ROOT)
            return {
                **result,
                "returncode": 0,
                "passed": True,
                "skipped": True,
                "skip_reason": f"missing local deploy target root {target_root}",
                "raw_returncode": result["returncode"],
            }
        return result

    subchecks = [
        (
            "gate_tool_tests",
            run_command([python, "-m", "pytest", "toolchain/scripts/test/test_closeout_gate_tools.py"], cwd=repo_root),
        ),
        (
            "folder_logic_tests",
            run_command([python, "-m", "pytest", "toolchain/scripts/test/test_folder_logic_check.py"], cwd=repo_root),
        ),
        (
            "path_governance_tests",
            run_command([python, "-m", "pytest", "toolchain/scripts/test/test_path_governance_check.py"], cwd=repo_root),
        ),
        (
            "governance_semantic_tests",
            run_command([python, "-m", "pytest", "toolchain/scripts/test/test_governance_semantic_check.py"], cwd=repo_root),
        ),
        (
            "agents_adapter_contract_tests",
            run_command([python, "-m", "pytest", "toolchain/scripts/test/test_agents_adapter_contract.py"], cwd=repo_root),
        ),
        (
            "deploy_regression_tests",
            run_command(
                [
                    python,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "toolchain/scripts/deploy",
                    "-p",
                    "test_*.py",
                ],
                cwd=repo_root,
            ),
        ),
        (
            "repo_analysis_contract_check",
            run_command([python, "toolchain/scripts/test/repo_analysis_contract_check.py"], cwd=repo_root),
        ),
        (
            "npm_pack_dry_run_aw_installer",
            run_npm_package_packlist(),
        ),
        (
            "npm_tarball_smoke_aw_installer",
            run_npm_package_tarball_smoke(),
        ),
        (
            "root_npm_pack_dry_run_aw_installer",
            run_root_npm_package_packlist(),
        ),
        (
            "root_npm_publish_dry_run_aw_installer",
            run_root_npm_publish_dry_run(),
        ),
        (
            "root_npm_tarball_smoke_aw_installer",
            run_root_npm_package_tarball_smoke(),
        ),
    ]
    subchecks.extend(
        (
            f"deploy_verify_{entrypoint}_{backend}",
            run_local_deploy_verify(backend, script_name),
        )
        for backend in SUPPORTED_DEPLOY_VERIFY_BACKENDS
        for entrypoint, script_name in DEPLOY_VERIFY_ENTRYPOINTS
    )
    passed = all(result["passed"] for _, result in subchecks)
    skipped = any(result.get("skipped", False) for _, result in subchecks)
    return {
        "passed": passed,
        "returncode": 0 if passed else 1,
        "status": "skipped" if passed and skipped else ("passed" if passed else "failed"),
        "subchecks": [{**result, "name": name} for name, result in subchecks],
    }


def run_smoke_gate(repo_root: Path, python: str, workflow_id: str) -> dict:
    def retained_runtime_paths_for(root: Path) -> list[Path]:
        runtime_root = root / ".autoworkflow" / "closeout"
        return [
            runtime_root / "manual-governance-loop-3round-r000001-m000642" / "runtime.json",
            runtime_root / "manual-governance-loop-6-3-3-r000001-m046830" / "runtime.json",
        ]

    def retained_roots_present(paths: list[Path]) -> bool:
        return any(path.parent.exists() or path.parent.is_symlink() for path in paths)

    selected_root = repo_root
    retained_runtime_paths = retained_runtime_paths_for(repo_root)
    if not retained_roots_present(retained_runtime_paths):
        primary_root = find_primary_worktree_root(repo_root)
        if primary_root is not None:
            primary_paths = retained_runtime_paths_for(primary_root)
            if retained_roots_present(primary_paths):
                selected_root = primary_root
                retained_runtime_paths = primary_paths

    backfill_smoke = run_command(
        [
            python,
            str(repo_root / "tools" / "gate_status_backfill.py"),
            "--workflow-id",
            workflow_id,
            "--gate",
            "smoke_gate_dry_run",
            "--status",
            "passed",
            "--details",
            json.dumps({"mode": "smoke", "dry_run": True}, sort_keys=True),
            "--dry-run",
            "--json",
        ],
        cwd=repo_root,
    )

    runtime_checks = []
    if not retained_roots_present(retained_runtime_paths):
        return {
            "passed": backfill_smoke["passed"],
            "returncode": 0 if backfill_smoke["passed"] else 1,
            "status": "skipped" if backfill_smoke["passed"] else "failed",
            "runtime_checks": [
                {
                    "path": str(selected_root / ".autoworkflow" / "closeout"),
                    "passed": True,
                    "skipped": True,
                    "reason": "no retained closeout runtime evidence configured for this repository",
                }
            ],
            "backfill_smoke": backfill_smoke,
        }

    runtime_passed = True
    for runtime_path in retained_runtime_paths:
        if not runtime_path.exists():
            check = {
                "path": str(runtime_path),
                "missing": True,
                "passed": False,
            }
            runtime_checks.append(check)
            runtime_passed = False
            continue
        payload = json.loads(runtime_path.read_text(encoding="utf-8"))
        active_round = payload.get("active_round")
        check = {
            "path": str(runtime_path),
            "active_round": active_round,
            "passed": active_round is None,
        }
        if selected_root != repo_root:
            check["checked_from"] = str(selected_root)
        runtime_checks.append(check)
        runtime_passed = runtime_passed and check["passed"]

    passed = runtime_passed and backfill_smoke["passed"]
    return {
        "passed": passed,
        "returncode": 0 if passed else 1,
        "status": "passed" if passed else "failed",
        "runtime_checks": runtime_checks,
        "backfill_smoke": backfill_smoke,
    }


def run_gate(gate: str, *, repo_root: Path, python: str, workflow_id: str) -> dict:
    if gate == "scope_gate":
        return run_scope_gate(repo_root, python)
    if gate == "spec_gate":
        return run_spec_gate(repo_root, python)
    if gate == "static_gate":
        return run_static_gate(repo_root, python)
    if gate == "cache_gate":
        return run_cache_gate(repo_root, python)
    if gate == "test_gate":
        return run_test_gate(repo_root, python)
    if gate == "smoke_gate":
        return run_smoke_gate(repo_root, python, workflow_id)
    raise ValueError(f"Unsupported gate: {gate}")


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    python = sys.executable
    steps = [
        GateStep(gate="scope_gate"),
        GateStep(gate="spec_gate"),
        GateStep(gate="static_gate"),
        GateStep(gate="cache_gate"),
        GateStep(gate="test_gate"),
        GateStep(gate="smoke_gate"),
    ]

    results = []
    backfill_results = []
    passed = True
    for step in steps:
        result = run_gate(step.gate, repo_root=repo_root, python=python, workflow_id=args.workflow_id)
        result["gate"] = step.gate
        results.append(result)
        skip_reasons: list[str] = []
        for subcheck in result.get("subchecks", []):
            if subcheck.get("skipped"):
                reason = subcheck.get("skip_reason") or subcheck.get("stdout", "").strip() or subcheck["name"]
                skip_reasons.append(f"{subcheck['name']}: {reason}")
        for runtime_check in result.get("runtime_checks", []):
            if runtime_check.get("skipped"):
                reason = runtime_check.get("reason") or runtime_check["path"]
                skip_reasons.append(f"runtime: {reason}")

        backfill_status = result.get("status") or ("passed" if result["passed"] else "failed")
        backfill_details = {"returncode": result["returncode"]}
        if skip_reasons:
            backfill_details["skip_reasons"] = skip_reasons

        backfill = run_command(
            [
                python,
                str(repo_root / "tools" / "gate_status_backfill.py"),
                "--workflow-id",
                args.workflow_id,
                "--gate",
                result["gate"],
                "--status",
                backfill_status,
                "--details",
                json.dumps(backfill_details, sort_keys=True),
            ],
            cwd=repo_root,
        )
        backfill_results.append(
            {
                "gate": result["gate"],
                "returncode": backfill["returncode"],
                "stdout": backfill["stdout"],
                "stderr": backfill["stderr"],
                "passed": backfill["passed"],
            }
        )
        step_passed = result["passed"] and backfill["passed"]
        passed = passed and (step_passed or not step.required)
        if step.required and not step_passed:
            break

    payload = {
        "workflow_id": args.workflow_id,
        "results": results,
        "backfill_results": backfill_results,
        "passed": passed,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
