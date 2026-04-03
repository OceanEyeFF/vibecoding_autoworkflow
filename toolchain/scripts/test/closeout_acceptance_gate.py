#!/usr/bin/env python3
"""Run the repeatable closeout acceptance gate for autoresearch closeout."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_ID = "autoresearch-closeout-governance-task-list-20260402"


@dataclass
class GateStep:
    gate: str
    required: bool = True


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
            "docs/knowledge/foundations/path-governance-ai-routing.md",
            "--allowed-prefix",
            "docs/knowledge/foundations/root-directory-layering.md",
            "--allowed-prefix",
            "docs/knowledge/foundations/toolchain-layering.md",
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
                    "docs/analysis",
                    "--scan-path",
                    "docs/operations",
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
            "deploy_verify_agents",
            run_command(
                [
                    python,
                    str(repo_root / "toolchain" / "scripts" / "deploy" / "adapter_deploy.py"),
                    "verify",
                    "--backend",
                    "agents",
                    "--target",
                    "local",
                ],
                cwd=repo_root,
            ),
        ),
        (
            "deploy_verify_claude",
            run_command(
                [
                    python,
                    str(repo_root / "toolchain" / "scripts" / "deploy" / "adapter_deploy.py"),
                    "verify",
                    "--backend",
                    "claude",
                    "--target",
                    "local",
                ],
                cwd=repo_root,
            ),
        ),
        (
            "deploy_verify_opencode",
            run_command(
                [
                    python,
                    str(repo_root / "toolchain" / "scripts" / "deploy" / "adapter_deploy.py"),
                    "verify",
                    "--backend",
                    "opencode",
                    "--target",
                    "local",
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


def run_smoke_gate(repo_root: Path, python: str, workflow_id: str) -> dict:
    retained_runtime_paths = [
        repo_root / ".autoworkflow" / "autoresearch" / "manual-cr-codex-loop-3round-r000001-m000642" / "runtime.json",
        repo_root / ".autoworkflow" / "autoresearch" / "manual-cr-codex-loop-6-3-3-r000001-m046830" / "runtime.json",
    ]
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
        backfill = subprocess.run(
            [
                python,
                str(repo_root / "tools" / "gate_status_backfill.py"),
                "--workflow-id",
                args.workflow_id,
                "--gate",
                result["gate"],
                "--status",
                "passed" if result["passed"] else "failed",
                "--details",
                json.dumps(
                    {
                        "returncode": result["returncode"],
                    },
                    sort_keys=True,
                ),
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
