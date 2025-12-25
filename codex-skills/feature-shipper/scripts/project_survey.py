from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    title: str
    details: list[str]


def _exists(root: Path, *parts: str) -> bool:
    return (root.joinpath(*parts)).exists()


def _read_package_json_scripts(root: Path) -> dict[str, str]:
    package_json = root / "package.json"
    if not package_json.exists():
        return {}
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except Exception:
        return {}
    scripts = data.get("scripts")
    if isinstance(scripts, dict):
        return {str(k): str(v) for k, v in scripts.items()}
    return {}


def detect_project(root: Path) -> list[Finding]:
    findings: list[Finding] = []

    # CI signals
    ci_hints: list[str] = []
    if _exists(root, ".github", "workflows"):
        workflow_dir = root / ".github" / "workflows"
        workflow_files = sorted(
            [p.name for p in workflow_dir.glob("*.yml")] + [p.name for p in workflow_dir.glob("*.yaml")]
        )
        if workflow_files:
            ci_hints.append(".github/workflows: " + ", ".join(workflow_files[:8]))
    for name in (".gitlab-ci.yml", "azure-pipelines.yml", "azure-pipelines.yaml", "Jenkinsfile"):
        if (root / name).exists():
            ci_hints.append(name)

    # Node
    if _exists(root, "package.json"):
        pm = "npm"
        if _exists(root, "pnpm-lock.yaml"):
            pm = "pnpm"
        elif _exists(root, "yarn.lock"):
            pm = "yarn"

        scripts = _read_package_json_scripts(root)
        script_lines: list[str] = []
        for key in ("test", "test:unit", "test:e2e", "lint", "format", "build", "dev"):
            if key in scripts:
                script_lines.append(f"{key}: {scripts[key]}")
        details = [
            "Detected: Node project (package.json)",
            f"Package manager hint: {pm}",
            "Suggested commands (verify against README/CI):",
            f"- install: {pm} install" if pm != "pnpm" else "- install: pnpm install",
            "- test:    <pm> test  (or run the most specific test script you find)",
            "- lint:    <pm> run lint",
            "- format:  <pm> run format",
        ]
        if script_lines:
            details.append("package.json scripts (common ones):")
            details.extend([f"- {line}" for line in script_lines])
        findings.append(Finding("JavaScript/TypeScript", details))

    # Python
    if _exists(root, "pyproject.toml") or _exists(root, "requirements.txt") or _exists(root, "poetry.lock"):
        details = [
            "Detected: Python project",
            "Suggested commands (verify against README/CI):",
            "- tests (pytest):  python -m pytest",
            "- format (ruff/black): ruff format .  /  black .",
            "- lint (ruff):     ruff check .",
        ]
        if _exists(root, "poetry.lock"):
            details.insert(2, "- poetry:           poetry install ; poetry run pytest")
        findings.append(Finding("Python", details))

    # .NET / C#
    sln_files = sorted([p.name for p in root.glob("*.sln")])
    csproj_files = sorted([p.name for p in root.rglob("*.csproj")])[:5]
    if sln_files or csproj_files or _exists(root, "Directory.Build.props"):
        details = [
            "Detected: .NET project (solution/project files)",
            "Suggested commands:",
            "- restore: dotnet restore",
            "- build:   dotnet build",
            "- test:    dotnet test",
        ]
        if sln_files:
            details.append("Solutions:")
            details.extend([f"- {name}" for name in sln_files[:5]])
        if csproj_files:
            details.append("Projects (sample):")
            details.extend([f"- {name}" for name in csproj_files])
        findings.append(Finding("C# / .NET", details))

    # Unity (heuristic; often tests are run via Unity in batchmode)
    if _exists(root, "ProjectSettings", "ProjectVersion.txt") and _exists(root, "Assets") and _exists(root, "Packages"):
        findings.append(
            Finding(
                "Unity (C#)",
                [
                    "Detected: Unity project markers (ProjectSettings/Assets/Packages)",
                    "Suggested test approach:",
                    "- Prefer CI docs or existing scripts for batchmode test runs.",
                    "- Unity CLI often supports running tests in batchmode (EditMode/PlayMode) and exporting results to XML.",
                    "Note: exact command differs by Unity version and CI setup; check README/CI first.",
                ],
            )
        )

    # Rust
    if _exists(root, "Cargo.toml"):
        findings.append(
            Finding(
                "Rust",
                [
                    "Detected: Rust project (Cargo.toml)",
                    "Suggested commands:",
                    "- build: cargo build",
                    "- test:  cargo test",
                    "- fmt:   cargo fmt",
                    "- lint:  cargo clippy",
                ],
            )
        )

    # Go
    if _exists(root, "go.mod"):
        findings.append(
            Finding(
                "Go",
                [
                    "Detected: Go project (go.mod)",
                    "Suggested commands:",
                    "- test:  go test ./...",
                    "- fmt:   gofmt -w .",
                    "- vet:   go vet ./...",
                ],
            )
        )

    # Java (Maven/Gradle)
    if _exists(root, "pom.xml"):
        findings.append(
            Finding(
                "Java (Maven)",
                [
                    "Detected: Maven project (pom.xml)",
                    "Suggested commands:",
                    "- test:  mvn test",
                    "- build: mvn package",
                ],
            )
        )
    if _exists(root, "build.gradle") or _exists(root, "build.gradle.kts"):
        findings.append(
            Finding(
                "Java/Kotlin (Gradle)",
                [
                    "Detected: Gradle project (build.gradle*)",
                    "Suggested commands:",
                    "- test:  ./gradlew test",
                    "- build: ./gradlew build",
                ],
            )
        )

    # C/C++ (CMake)
    if _exists(root, "CMakeLists.txt"):
        findings.append(
            Finding(
                "C/C++ (CMake)",
                [
                    "Detected: CMake project (CMakeLists.txt)",
                    "Suggested commands:",
                    "- configure: cmake -S . -B build",
                    "- build:     cmake --build build",
                    "- test:      ctest --test-dir build  (or: cd build && ctest)",
                ],
            )
        )

    # Unreal Engine (heuristic)
    uproject_files = sorted([p.name for p in root.glob("*.uproject")])
    if uproject_files:
        findings.append(
            Finding(
                "Unreal Engine (C++)",
                [
                    "Detected: Unreal project (*.uproject)",
                    "Projects:",
                    *[f"- {name}" for name in uproject_files[:3]],
                    "Suggested test approach:",
                    "- Prefer existing CI/scripts; Unreal automation tests are typically run via Editor-Cmd or UAT.",
                    "- Look for scripts like RunUAT/BuildCookRun or documented Automation RunTests usage.",
                    "Note: exact command is engine/version specific and may require installed engine paths.",
                ],
            )
        )

    # Generic
    if _exists(root, "Makefile"):
        findings.append(
            Finding(
                "Build helpers",
                [
                    "Found: Makefile (check `make help` if supported)",
                    "Suggested commands:",
                    "- list targets: make -n | head  (or open Makefile)",
                ],
            )
        )

    if ci_hints:
        findings.append(
            Finding(
                "CI configuration",
                [
                    "Found CI config files (high-signal for the real gate):",
                    *[f"- {item}" for item in ci_hints],
                    "Tip: mirror CI commands locally to avoid rework.",
                ],
            )
        )

    return findings


def list_high_signal_files(root: Path) -> list[str]:
    candidates = [
        "README.md",
        "README.txt",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "LICENSE",
        ".editorconfig",
        "pyproject.toml",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "CMakeLists.txt",
        ".gitlab-ci.yml",
        "azure-pipelines.yml",
        "azure-pipelines.yaml",
        "Jenkinsfile",
        "Makefile",
        "docker-compose.yml",
        "Dockerfile",
    ]
    return [name for name in candidates if (root / name).exists()]


def main() -> int:
    root = Path(os.getcwd()).resolve()
    print(f"project-survey: {root}")
    print()

    files = list_high_signal_files(root)
    if files:
        print("High-signal files found:")
        for name in files:
            print(f"- {name}")
        print()

    findings = detect_project(root)
    if not findings:
        print("No obvious project type detected from common markers.")
        print("Next steps:")
        print("- Inspect README and build/test scripts (CI if present)")
        print("- Search for test commands (rg \"pytest|vitest|jest|go test|cargo test|mvn test|gradlew test\")")
        return 0

    for item in findings:
        print(f"[{item.title}]")
        for line in item.details:
            print(line)
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
