#!/usr/bin/env python3
"""Run the repeatable closeout acceptance gate."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
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


def run_command(command: list[str], *, cwd: Path) -> dict:
    completed = subprocess.run(command, capture_output=True, text=True, cwd=cwd)
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
    return run_command([python, "-m", "compileall", "toolchain/scripts/test"], cwd=repo_root)


def run_test_gate(repo_root: Path, python: str) -> dict:
    def run_local_deploy_verify(backend: str) -> dict:
        command = [
            python,
            str(repo_root / "toolchain" / "scripts" / "deploy" / "adapter_deploy.py"),
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
            "agents_adapter_contract_tests",
            run_command([python, "-m", "pytest", "toolchain/scripts/test/test_agents_adapter_contract.py"], cwd=repo_root),
        ),
    ]
    subchecks.extend(
        (
            f"deploy_verify_{backend}",
            run_local_deploy_verify(backend),
        )
        for backend in SUPPORTED_DEPLOY_VERIFY_BACKENDS
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

    runtime_checks = []
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

        backfill = subprocess.run(
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
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        backfill_results.append(
            {
                "gate": result["gate"],
                "returncode": backfill.returncode,
                "stdout": backfill.stdout,
                "stderr": backfill.stderr,
                "passed": backfill.returncode == 0,
            }
        )
        step_passed = result["passed"] and backfill.returncode == 0
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
