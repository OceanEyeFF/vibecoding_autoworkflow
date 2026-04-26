#!/usr/bin/env python3
"""Runtime install and verify endpoints for agents skill payload targets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


def resolve_repo_root() -> Path:
    """Resolve the source root that owns canonical Harness payload files."""

    override = os.environ.get("AW_HARNESS_REPO_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[3]


def resolve_target_repo_root(source_root: Path) -> Path:
    """Resolve the user project root that receives backend install targets."""

    target_override = os.environ.get("AW_HARNESS_TARGET_REPO_ROOT")
    if target_override:
        return Path(target_override).expanduser().resolve()
    if os.environ.get("AW_HARNESS_REPO_ROOT"):
        return source_root
    return Path.cwd().resolve()


REPO_ROOT = resolve_repo_root()
TARGET_REPO_ROOT = resolve_target_repo_root(REPO_ROOT)
LOCAL_TARGET_ROOTS = {
    "agents": TARGET_REPO_ROOT / ".agents" / "skills",
}
ADAPTER_SKILL_DIRS = {
    "agents": REPO_ROOT / "product" / "harness" / "adapters" / "agents" / "skills",
}
EXPECTED_PAYLOAD_POLICIES = {
    "agents": "canonical-copy",
}
EXPECTED_REFERENCE_DISTRIBUTION = {
    "agents": "copy-listed-canonical-paths",
}
EXPECTED_PAYLOAD_VERSIONS = {
    "agents": "agents-skill-payload.v1",
}
MANAGED_SKILL_MARKER = "aw.marker"
MANAGED_SKILL_MARKER_VERSION = "aw-managed-skill-marker.v2"
UNRECOGNIZED_ISSUE_CODES = {
    "unrecognized-target-directory",
}
CONFLICT_ISSUE_CODES = {
    "unexpected-managed-directory",
    "unrecognized-target-directory",
    "wrong-target-entry-type",
}
UPDATE_RECOVERABLE_ISSUE_CODES = {
    "missing-target-root",
    "missing-target-entry",
    "missing-required-payload",
    "target-payload-drift",
    "unexpected-managed-directory",
}


class DeployError(RuntimeError):
    """Raised when deployment inputs or targets are invalid."""


@dataclass
class VerifyIssue:
    """One verification problem detected for a deploy target root."""

    code: str
    path: Path
    detail: str


@dataclass
class VerifyResult:
    """Collected verification state for one backend target root."""

    backend: str
    target_root: Path
    issues: list[VerifyIssue]


@dataclass
class SkillBinding:
    """Resolved payload source records for one backend skill."""

    backend: str
    skill_id: str
    payload_dir: Path
    payload_path: Path


@dataclass(frozen=True)
class CanonicalSourceMetadata:
    """Normalized canonical-source metadata derived from one payload descriptor."""

    canonical_dir: str
    included_paths: list[str]
    canonical_files_by_relative_path: dict[str, Path]


@dataclass(frozen=True)
class PayloadTargetMetadata:
    """Normalized target metadata derived from one payload descriptor."""

    target_dir: str
    target_entry_name: str
    required_payload_files: list[str]
    legacy_target_dirs: list[str]
    legacy_skill_ids: list[str]


@dataclass(frozen=True)
class InstallPlan:
    """Resolved install plan for one binding and target directory."""

    binding: SkillBinding
    target_metadata: PayloadTargetMetadata
    target_skill_dir: Path
    payload_version: str
    payload_fingerprint: str


@dataclass(frozen=True)
class RuntimeMarker:
    """Runtime-generated marker stored in managed target directories."""

    marker_version: str
    backend: str
    skill_id: str
    payload_version: str
    payload_fingerprint: str


@dataclass(frozen=True)
class PathConflict:
    """One target path conflict that blocks install."""

    skill_id: str
    path: Path
    detail: str


def add_backend_args(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument(
        "--backend",
        choices=("agents",),
        default="agents",
        help="Which backend target to operate on. Only agents is implemented.",
    )


def add_target_override_args(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument(
        "--agents-root",
        type=Path,
        help="Override the managed agents skills target root.",
    )


def parse_args(
    argv: list[str] | None = None,
    *,
    prog: str | None = None,
    description: str | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=prog,
        description=description or "Install and verify managed agents skill payloads.",
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    install_parser = subparsers.add_parser("install")
    add_backend_args(install_parser)
    add_target_override_args(install_parser)

    check_parser = subparsers.add_parser("check_paths_exist")
    add_backend_args(check_parser)
    add_target_override_args(check_parser)

    verify_parser = subparsers.add_parser("verify")
    add_backend_args(verify_parser)
    add_target_override_args(verify_parser)

    diagnose_parser = subparsers.add_parser("diagnose")
    add_backend_args(diagnose_parser)
    add_target_override_args(diagnose_parser)
    diagnose_parser.add_argument(
        "--json",
        action="store_true",
        help="Print a structured diagnostic summary.",
    )

    prune_parser = subparsers.add_parser("prune")
    add_backend_args(prune_parser)
    add_target_override_args(prune_parser)
    prune_parser.add_argument(
        "--all",
        action="store_true",
        help="Delete every recognized managed install directory in the target root.",
    )

    update_parser = subparsers.add_parser("update")
    add_backend_args(update_parser)
    add_target_override_args(update_parser)
    update_parser.add_argument(
        "--yes",
        action="store_true",
        help="Apply the destructive reinstall update after printing the preflight plan.",
    )
    update_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the dry-run update plan as JSON. Cannot be combined with --yes.",
    )

    return parser.parse_args(argv)


def iter_backends(selected: str) -> list[str]:
    return [selected]


def target_root_for(backend: str, args: argparse.Namespace) -> Path:
    if backend == "agents" and args.agents_root is not None:
        return args.agents_root
    try:
        return LOCAL_TARGET_ROOTS[backend]
    except KeyError as exc:
        raise DeployError(f"Unsupported backend target root resolution: {backend}") from exc


def ensure_install_target_root(path: Path) -> None:
    if path.is_symlink():
        if path.exists():
            raise DeployError(f"Target root must be a real directory, not a symlink: {path}")
        raise DeployError(f"Target root is a broken symlink: {path}")

    if path.exists():
        if not path.is_dir():
            raise DeployError(f"Target root exists but is not a directory: {path}")
        print(f"ready target root {path}")
        return

    path.mkdir(parents=True, exist_ok=True)
    print(f"created target root {path}")


def verify_target_root(backend: str, target_root: Path) -> list[VerifyIssue]:
    if target_root.is_symlink():
        if target_root.exists():
            return [
                VerifyIssue(
                    code="wrong-target-root-type",
                    path=target_root,
                    detail="target root must be a real directory, not a symlink",
                )
            ]
        return [
            VerifyIssue(
                code="broken-target-root-symlink",
                path=target_root,
                detail="target root is a broken symlink",
            )
        ]

    if target_root.exists():
        if target_root.is_dir():
            return []
        return [
            VerifyIssue(
                code="wrong-target-root-type",
                path=target_root,
                detail="target root exists but is not a directory",
            )
        ]

    return [
        VerifyIssue(
            code="missing-target-root",
            path=target_root,
            detail=f"{backend} target root does not exist",
        )
    ]


def adapter_skills_dir_for(backend: str) -> Path:
    try:
        return ADAPTER_SKILL_DIRS[backend]
    except KeyError as exc:
        raise DeployError(f"Unsupported adapter directory for backend: {backend}") from exc


def collect_skill_bindings(backend: str) -> list[SkillBinding]:
    adapter_dir = adapter_skills_dir_for(backend)

    adapter_skill_ids = (
        {path.name for path in adapter_dir.iterdir() if path.is_dir()}
        if adapter_dir.is_dir()
        else set()
    )

    skill_ids = sorted(adapter_skill_ids)
    return [
        SkillBinding(
            backend=backend,
            skill_id=skill_id,
            payload_dir=adapter_dir / skill_id,
            payload_path=adapter_dir / skill_id / "payload.json",
        )
        for skill_id in skill_ids
    ]


def load_json_file(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DeployError(f"Missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DeployError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise DeployError(f"JSON payload must be an object: {path}")
    return data


def string_list(value: object) -> list[str] | None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return value


def normalize_relative_target_path(value: str, *, field_name: str, skill_id: str) -> str:
    windows_path = PureWindowsPath(value)
    if (
        PurePosixPath(value).is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or bool(windows_path.root)
    ):
        raise DeployError(
            f"{field_name} must stay within the backend target root for skill {skill_id}: {value}"
        )

    segments = [segment for segment in value.replace("\\", "/").split("/") if segment]
    if not segments:
        raise DeployError(f"{field_name} must be a non-empty relative path for skill {skill_id}")

    invalid_segment = next((segment for segment in segments if segment in (".", "..")), None)
    if invalid_segment is not None:
        raise DeployError(
            f"{field_name} must not contain {invalid_segment!r} path segments for skill {skill_id}: {value}"
        )

    return PurePosixPath(*segments).as_posix()


def normalize_relative_canonical_path(value: str, *, field_name: str, skill_id: str) -> str:
    try:
        return normalize_relative_target_path(value, field_name=field_name, skill_id=skill_id)
    except DeployError as exc:
        detail = str(exc).replace("backend target root", "canonical skill directory")
        raise DeployError(detail) from exc


def normalize_relative_repo_path(value: str, *, field_name: str, skill_id: str) -> str:
    try:
        return normalize_relative_target_path(value, field_name=field_name, skill_id=skill_id)
    except DeployError as exc:
        detail = str(exc).replace("backend target root", "repository root")
        raise DeployError(detail) from exc


def payload_target_metadata(payload: dict[str, Any], binding: SkillBinding) -> PayloadTargetMetadata:
    target_dir_value = payload.get("target_dir")
    target_entry_name = payload.get("target_entry_name")
    required_payload_files = string_list(payload.get("required_payload_files"))

    if not isinstance(target_dir_value, str) or not isinstance(target_entry_name, str):
        raise DeployError(f"payload target metadata is invalid for skill {binding.skill_id}")

    if required_payload_files is None:
        raise DeployError(
            f"payload required_payload_files must be a string array for skill {binding.skill_id}"
        )

    normalized_target_dir = normalize_relative_target_path(
        target_dir_value,
        field_name="payload target_dir",
        skill_id=binding.skill_id,
    )
    if "/" in normalized_target_dir:
        raise DeployError(
            f"payload target_dir must be a single directory name for skill {binding.skill_id}: {target_dir_value}"
        )

    normalized_target_entry_name = normalize_relative_target_path(
        target_entry_name,
        field_name="payload target_entry_name",
        skill_id=binding.skill_id,
    )
    normalized_required_payload_files = [
        normalize_relative_target_path(
            relative_name,
            field_name="payload required_payload_files entry",
            skill_id=binding.skill_id,
        )
        for relative_name in required_payload_files
    ]

    if normalized_target_entry_name not in normalized_required_payload_files:
        raise DeployError(
            f"payload target_entry_name {target_entry_name} must be listed in "
            f"required_payload_files for skill {binding.skill_id}"
        )

    if "payload.json" not in normalized_required_payload_files:
        raise DeployError(
            f"payload required_payload_files must include payload.json for skill {binding.skill_id}"
        )

    if MANAGED_SKILL_MARKER not in normalized_required_payload_files:
        raise DeployError(
            f"payload required_payload_files must include {MANAGED_SKILL_MARKER} for skill {binding.skill_id}"
        )

    normalized_legacy_target_dirs: list[str] = []
    legacy_target_dirs_value = payload.get("legacy_target_dirs")
    if legacy_target_dirs_value is not None:
        legacy_target_dirs_raw = string_list(legacy_target_dirs_value)
        if legacy_target_dirs_raw is None:
            raise DeployError(
                f"payload legacy_target_dirs must be a list of strings for skill {binding.skill_id}"
            )
        for legacy_dir in legacy_target_dirs_raw:
            normalized_legacy_dir = normalize_relative_target_path(
                legacy_dir,
                field_name="payload legacy_target_dirs entry",
                skill_id=binding.skill_id,
            )
            if "/" in normalized_legacy_dir:
                raise DeployError(
                    f"payload legacy_target_dirs entries must be single directory names "
                    f"for skill {binding.skill_id}: {legacy_dir}"
                )
            normalized_legacy_target_dirs.append(normalized_legacy_dir)

    if normalized_target_dir in normalized_legacy_target_dirs:
        raise DeployError(
            f"payload target_dir {normalized_target_dir} must not be listed in "
            f"legacy_target_dirs for skill {binding.skill_id}"
        )

    normalized_legacy_skill_ids: list[str] = []
    legacy_skill_ids_value = payload.get("legacy_skill_ids")
    if legacy_skill_ids_value is not None:
        legacy_skill_ids_raw = string_list(legacy_skill_ids_value)
        if legacy_skill_ids_raw is None:
            raise DeployError(
                f"payload legacy_skill_ids must be a list of strings for skill {binding.skill_id}"
            )
        for legacy_skill_id in legacy_skill_ids_raw:
            normalized_legacy_skill_id = normalize_relative_target_path(
                legacy_skill_id,
                field_name="payload legacy_skill_ids entry",
                skill_id=binding.skill_id,
            )
            if "/" in normalized_legacy_skill_id:
                raise DeployError(
                    f"payload legacy_skill_ids entries must be single directory names "
                    f"for skill {binding.skill_id}: {legacy_skill_id}"
                )
            normalized_legacy_skill_ids.append(normalized_legacy_skill_id)

    if binding.skill_id in normalized_legacy_skill_ids:
        raise DeployError(
            f"binding skill_id {binding.skill_id} must not be listed in "
            f"legacy_skill_ids for skill {binding.skill_id}"
        )

    return PayloadTargetMetadata(
        target_dir=normalized_target_dir,
        target_entry_name=normalized_target_entry_name,
        required_payload_files=normalized_required_payload_files,
        legacy_target_dirs=normalized_legacy_target_dirs,
        legacy_skill_ids=normalized_legacy_skill_ids,
    )


def load_binding_target_metadata(binding: SkillBinding) -> PayloadTargetMetadata:
    return payload_target_metadata(load_json_file(binding.payload_path), binding)


def current_target_dirs_by_skill_id(bindings: list[SkillBinding]) -> dict[str, str]:
    target_dirs: set[str] = set()
    target_dirs_by_skill_id: dict[str, str] = {}
    for binding in bindings:
        target_dir = load_binding_target_metadata(binding).target_dir
        if target_dir in target_dirs:
            raise DeployError(
                f"Multiple skills map to the same target_dir for backend {binding.backend}: {target_dir}"
            )
        target_dirs.add(target_dir)
        target_dirs_by_skill_id[binding.skill_id] = target_dir
    return target_dirs_by_skill_id


def expected_target_dirs(bindings: list[SkillBinding]) -> set[str]:
    return set(current_target_dirs_by_skill_id(bindings).values())


def all_known_target_dirs(bindings: list[SkillBinding]) -> set[str]:
    """Return all target directory names known to belong to current bindings,
    including both current target_dirs and legacy_target_dirs."""
    known = set(current_target_dirs_by_skill_id(bindings).values())
    for binding in bindings:
        metadata = load_binding_target_metadata(binding)
        known.update(metadata.legacy_target_dirs)
    return known


def managed_skill_marker_path(target_skill_dir: Path) -> Path:
    return target_skill_dir / MANAGED_SKILL_MARKER


def load_binding_payload(binding: SkillBinding) -> dict[str, Any]:
    return load_json_file(binding.payload_path)


def payload_version_from_descriptor(payload: dict[str, Any], *, binding: SkillBinding) -> str:
    payload_version = payload.get("payload_version")
    if not isinstance(payload_version, str):
        raise DeployError(f"payload payload_version must be a string for skill {binding.skill_id}")
    return payload_version


def payload_canonical_source_metadata(
    payload: dict[str, Any], binding: SkillBinding
) -> CanonicalSourceMetadata:
    canonical_dir_value = payload.get("canonical_dir")
    canonical_paths_value = string_list(payload.get("canonical_paths"))

    if (
        not isinstance(canonical_dir_value, str)
        or canonical_paths_value is None
    ):
        raise DeployError(
            f"payload canonical_dir and canonical_paths must be defined for skill {binding.skill_id}"
        )

    normalized_canonical_dir = normalize_relative_repo_path(
        canonical_dir_value,
        field_name="payload canonical_dir",
        skill_id=binding.skill_id,
    )
    canonical_dir_path = PurePosixPath(normalized_canonical_dir)

    included_paths: list[str] = []
    canonical_files_by_relative_path: dict[str, Path] = {}
    for canonical_path in canonical_paths_value:
        normalized_canonical_path = normalize_relative_repo_path(
            canonical_path,
            field_name="payload canonical_paths entry",
            skill_id=binding.skill_id,
        )
        try:
            relative_path = PurePosixPath(normalized_canonical_path).relative_to(canonical_dir_path)
        except ValueError as exc:
            raise DeployError(
                f"payload canonical_paths entry must stay within canonical_dir for skill "
                f"{binding.skill_id}: {canonical_path}"
            ) from exc

        normalized_included_path = relative_path.as_posix()
        if normalized_included_path in ("", "."):
            raise DeployError(
                f"payload canonical_paths entry must point to a file inside canonical_dir "
                f"for skill {binding.skill_id}: {canonical_path}"
            )
        if normalized_included_path in canonical_files_by_relative_path:
            raise DeployError(
                f"payload canonical_paths contain duplicate target-relative file "
                f"{normalized_included_path} for skill {binding.skill_id}"
            )

        included_paths.append(normalized_included_path)
        canonical_files_by_relative_path[normalized_included_path] = REPO_ROOT / normalized_canonical_path

    return CanonicalSourceMetadata(
        canonical_dir=normalized_canonical_dir,
        included_paths=included_paths,
        canonical_files_by_relative_path=canonical_files_by_relative_path,
    )


def canonical_source_files_by_target_relative_path(
    binding: SkillBinding, *, payload: dict[str, Any] | None = None
) -> dict[str, Path]:
    if payload is None:
        payload = load_binding_payload(binding)
    return payload_canonical_source_metadata(
        payload,
        binding,
    ).canonical_files_by_relative_path


def source_path_for_target_relative_file(
    binding: SkillBinding,
    relative_name: str,
    *,
    payload: dict[str, Any] | None = None,
) -> Path:
    if relative_name == "payload.json":
        return binding.payload_path
    if relative_name == MANAGED_SKILL_MARKER:
        raise DeployError(f"{MANAGED_SKILL_MARKER} is runtime-generated for skill {binding.skill_id}")

    canonical_files = canonical_source_files_by_target_relative_path(binding, payload=payload)
    try:
        return canonical_files[relative_name]
    except KeyError as exc:
        raise DeployError(
            f"payload required file {relative_name} is not declared in payload canonical_paths "
            f"for skill {binding.skill_id}"
        ) from exc


def compute_payload_fingerprint(binding: SkillBinding, *, payload: dict[str, Any] | None = None) -> str:
    if payload is None:
        payload = load_binding_payload(binding)

    payload_version = payload_version_from_descriptor(payload, binding=binding)
    target_metadata = payload_target_metadata(payload, binding)
    try:
        payload_text = binding.payload_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise DeployError(
            f"Missing payload source file while computing fingerprint: {exc.filename}"
        ) from exc

    fingerprint_parts = [
        f"backend={binding.backend}\n"
        f"skill_id={binding.skill_id}\n"
        f"payload_version={payload_version}\n"
    ]
    for relative_name in target_metadata.required_payload_files:
        if relative_name == MANAGED_SKILL_MARKER:
            continue
        source_path = source_path_for_target_relative_file(
            binding,
            relative_name,
            payload=payload,
        )
        try:
            source_text = source_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise DeployError(
                f"Missing payload source file while computing fingerprint: {exc.filename}"
            ) from exc
        fingerprint_parts.append(f"file:{relative_name}\n{source_text}\n")

    fingerprint_parts.append(f"file:payload.json\n{payload_text}\n")
    return hashlib.sha256("".join(fingerprint_parts).encode("utf-8")).hexdigest()


def runtime_marker_to_dict(marker: RuntimeMarker) -> dict[str, str]:
    return {
        "marker_version": marker.marker_version,
        "backend": marker.backend,
        "skill_id": marker.skill_id,
        "payload_version": marker.payload_version,
        "payload_fingerprint": marker.payload_fingerprint,
    }


def runtime_marker_text(marker: RuntimeMarker) -> str:
    return json.dumps(runtime_marker_to_dict(marker), indent=2) + "\n"


def build_runtime_marker(
    backend: str,
    skill_id: str,
    payload_version: str,
    payload_fingerprint: str,
) -> RuntimeMarker:
    return RuntimeMarker(
        marker_version=MANAGED_SKILL_MARKER_VERSION,
        backend=backend,
        skill_id=skill_id,
        payload_version=payload_version,
        payload_fingerprint=payload_fingerprint,
    )


def parse_runtime_marker(marker: dict[str, Any]) -> RuntimeMarker | None:
    expected_keys = {
        "marker_version",
        "backend",
        "skill_id",
        "payload_version",
        "payload_fingerprint",
    }
    if set(marker) != expected_keys:
        return None

    marker_version = marker.get("marker_version")
    backend = marker.get("backend")
    skill_id = marker.get("skill_id")
    payload_version = marker.get("payload_version")
    payload_fingerprint = marker.get("payload_fingerprint")
    if not all(
        isinstance(value, str)
        for value in (
            marker_version,
            backend,
            skill_id,
            payload_version,
            payload_fingerprint,
        )
    ):
        return None
    if marker_version != MANAGED_SKILL_MARKER_VERSION:
        return None

    return RuntimeMarker(
        marker_version=marker_version,
        backend=backend,
        skill_id=skill_id,
        payload_version=payload_version,
        payload_fingerprint=payload_fingerprint,
    )


def load_runtime_marker(path: Path) -> RuntimeMarker | None:
    if path.is_symlink() or not path.is_file():
        return None

    try:
        marker = load_json_file(path)
    except DeployError:
        return None

    return parse_runtime_marker(marker)


def build_install_plan(binding: SkillBinding, target_root: Path) -> InstallPlan:
    payload = load_binding_payload(binding)
    target_metadata = payload_target_metadata(payload, binding)
    payload_version = payload_version_from_descriptor(payload, binding=binding)
    return InstallPlan(
        binding=binding,
        target_metadata=target_metadata,
        target_skill_dir=target_root / target_metadata.target_dir,
        payload_version=payload_version,
        payload_fingerprint=compute_payload_fingerprint(binding, payload=payload),
    )


def path_exists_or_is_symlink(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def describe_existing_target_path(path: Path) -> str:
    if path.is_symlink():
        if path.exists():
            return "existing target path is a symlink"
        return "existing target path is a broken symlink"
    if path.is_dir():
        return "existing target path is a directory"
    if path.is_file():
        return "existing target path is a file"
    return "existing target path already exists"


def collect_path_conflicts(plans: list[InstallPlan]) -> list[PathConflict]:
    conflicts: list[PathConflict] = []
    for plan in plans:
        if not path_exists_or_is_symlink(plan.target_skill_dir):
            continue
        conflicts.append(
            PathConflict(
                skill_id=plan.binding.skill_id,
                path=plan.target_skill_dir,
                detail=describe_existing_target_path(plan.target_skill_dir),
            )
        )
    return conflicts


def collect_legacy_path_conflicts(plans: list[InstallPlan], target_root: Path) -> list[PathConflict]:
    """Check for occupied legacy directories that install will not clean up."""
    conflicts: list[PathConflict] = []
    for plan in plans:
        for legacy_dir_name in plan.target_metadata.legacy_target_dirs:
            legacy_path = target_root / legacy_dir_name
            if not legacy_path.exists():
                continue
            marker_path = managed_skill_marker_path(legacy_path)
            if marker_path.is_file():
                marker = load_runtime_marker(marker_path)
                if marker is not None and marker.backend == plan.binding.backend:
                    if marker.skill_id == plan.binding.skill_id or marker.skill_id in plan.target_metadata.legacy_skill_ids:
                        continue
            conflicts.append(
                PathConflict(
                    skill_id=plan.binding.skill_id,
                    path=legacy_path,
                    detail=f"legacy directory {legacy_dir_name} is occupied by unmanaged content",
                )
            )
    return conflicts


def format_path_conflicts(conflicts: list[PathConflict]) -> str:
    lines = ["target path conflicts:"]
    for conflict in conflicts:
        lines.append(f"- {conflict.skill_id}: {conflict.path} ({conflict.detail})")
    return "\n".join(lines)


def verify_source_binding(binding: SkillBinding) -> list[VerifyIssue]:
    issues: list[VerifyIssue] = []

    if not binding.payload_dir.is_dir():
        issues.append(
            VerifyIssue(
                code="missing-backend-payload-source",
                path=binding.payload_dir,
                detail=f"missing backend payload source for skill {binding.skill_id}",
            )
        )
        return issues

    try:
        payload = load_json_file(binding.payload_path)
    except DeployError as exc:
        issues.append(
            VerifyIssue(
                code="payload-contract-invalid",
                path=binding.payload_path,
                detail=str(exc),
            )
        )
        return issues

    try:
        canonical_source = payload_canonical_source_metadata(payload, binding)
    except DeployError as exc:
        issues.append(
            VerifyIssue(
                code="payload-contract-invalid",
                path=binding.payload_path,
                detail=str(exc),
            )
        )
        canonical_source = None

    canonical_dir_value = payload.get("canonical_dir")
    canonical_dir = REPO_ROOT / (
        canonical_source.canonical_dir
        if canonical_source is not None
        else str(canonical_dir_value)
    )
    if not canonical_dir.is_dir():
        issues.append(
            VerifyIssue(
                code="missing-canonical-source",
                path=canonical_dir,
                detail=f"missing canonical directory for skill {binding.skill_id}",
            )
        )
    if canonical_source is not None and Path(canonical_source.canonical_dir).name != binding.skill_id:
        issues.append(
            VerifyIssue(
                code="payload-contract-invalid",
                path=binding.payload_path,
                detail=(
                    f"payload canonical_dir must end with {binding.skill_id} for skill "
                    f"{binding.skill_id}"
                ),
            )
        )
    for included_path, canonical_file in (
        canonical_source.canonical_files_by_relative_path.items()
        if canonical_source is not None
        else []
    ):
        if not canonical_file.is_file():
            issues.append(
                VerifyIssue(
                    code="missing-canonical-source",
                    path=canonical_file,
                    detail=f"missing canonical file {included_path} for skill {binding.skill_id}",
                )
            )

    expected_payload_version = EXPECTED_PAYLOAD_VERSIONS[binding.backend]
    if payload.get("payload_version") != expected_payload_version:
        issues.append(
            VerifyIssue(
                code="payload-contract-invalid",
                path=binding.payload_path,
                detail=(
                    f"payload payload_version must be {expected_payload_version} for "
                    f"backend {binding.backend} skill {binding.skill_id}"
                ),
            )
        )

    if payload.get("backend") != binding.backend:
        issues.append(
            VerifyIssue(
                code="payload-contract-invalid",
                path=binding.payload_path,
                detail=f"payload backend must be {binding.backend} for skill {binding.skill_id}",
            )
        )

    if payload.get("skill_id") != binding.skill_id:
        issues.append(
            VerifyIssue(
                code="payload-contract-invalid",
                path=binding.payload_path,
                detail=f"payload skill_id must be {binding.skill_id}",
            )
        )

    try:
        target_metadata = payload_target_metadata(payload, binding)
    except DeployError as exc:
        issues.append(
            VerifyIssue(
                code="payload-contract-invalid",
                path=binding.payload_path,
                detail=str(exc),
            )
        )
    else:
        expected_required_payload_files = [
            *(canonical_source.included_paths if canonical_source is not None else []),
            "payload.json",
            MANAGED_SKILL_MARKER,
        ]
        if target_metadata.required_payload_files != expected_required_payload_files:
            issues.append(
                VerifyIssue(
                    code="payload-contract-invalid",
                    path=binding.payload_path,
                    detail=(
                        "payload required_payload_files must equal payload canonical_paths plus "
                        "payload.json and aw.marker "
                        f"for skill {binding.skill_id}"
                    ),
                )
            )
    expected_payload_policy = EXPECTED_PAYLOAD_POLICIES[binding.backend]
    if payload.get("payload_policy") != expected_payload_policy:
        issues.append(
            VerifyIssue(
                code="payload-policy-mismatch",
                path=binding.payload_path,
                detail=(
                    f"payload_policy must be {expected_payload_policy} for backend "
                    f"{binding.backend} skill {binding.skill_id}"
                ),
            )
        )

    expected_reference_distribution = EXPECTED_REFERENCE_DISTRIBUTION[binding.backend]
    if payload.get("reference_distribution") != expected_reference_distribution:
        issues.append(
            VerifyIssue(
                code="reference-policy-mismatch",
                path=binding.payload_path,
                detail=(
                    f"reference_distribution must be {expected_reference_distribution} for backend "
                    f"{binding.backend} skill {binding.skill_id}"
                ),
            )
        )

    return issues


def install_backend_payloads(backend: str, args: argparse.Namespace) -> None:
    bindings = collect_skill_bindings(backend)
    if not bindings:
        raise DeployError(f"No payload bindings found for backend {backend}.")

    validation_issues: list[VerifyIssue] = []
    for binding in bindings:
        validation_issues.extend(verify_source_binding(binding))
    if validation_issues:
        details = "\n".join(
            f"  - {issue.code}: {issue.path} ({issue.detail})" for issue in validation_issues
        )
        raise DeployError(f"Cannot install because source validation failed:\n{details}")

    target_root = target_root_for(backend, args)
    target_root_issues = [
        issue
        for issue in verify_target_root(backend, target_root)
        if issue.code != "missing-target-root"
    ]
    if target_root_issues:
        details = "\n".join(
            f"  - {issue.code}: {issue.path} ({issue.detail})" for issue in target_root_issues
        )
        raise DeployError(f"Cannot install because target root is not ready:\n{details}")

    current_target_dirs_by_skill_id(bindings)
    plans = [build_install_plan(binding, target_root) for binding in bindings]
    conflicts = collect_path_conflicts(plans)
    conflicts.extend(collect_legacy_path_conflicts(plans, target_root))
    if conflicts:
        raise DeployError(
            f"[{backend}] install blocked by {len(conflicts)} existing target path(s)\n\n"
            f"{format_path_conflicts(conflicts)}"
        )

    ensure_install_target_root(target_root)
    for plan in plans:
        binding = plan.binding
        for legacy_dir_name in plan.target_metadata.legacy_target_dirs:
            legacy_path = target_root / legacy_dir_name
            if not legacy_path.exists():
                continue
            marker = load_runtime_marker(managed_skill_marker_path(legacy_path))
            if marker is not None and marker.backend == binding.backend:
                if marker.skill_id == binding.skill_id or marker.skill_id in plan.target_metadata.legacy_skill_ids:
                    shutil.rmtree(legacy_path)
                    print(f"removed legacy skill dir {binding.skill_id} -> {legacy_path}")
    for plan in plans:
        binding = plan.binding
        target_metadata = plan.target_metadata
        target_skill_dir = plan.target_skill_dir
        payload = load_binding_payload(binding)
        target_skill_dir.mkdir(parents=True, exist_ok=False)
        for relative_name in target_metadata.required_payload_files:
            target_path = target_skill_dir / relative_name
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if relative_name == MANAGED_SKILL_MARKER:
                target_path.write_text(
                    runtime_marker_text(
                        build_runtime_marker(
                            binding.backend,
                            binding.skill_id,
                            plan.payload_version,
                            plan.payload_fingerprint,
                        )
                    ),
                    encoding="utf-8",
                )
                continue
            source_path = source_path_for_target_relative_file(
                binding,
                relative_name,
                payload=payload,
            )
            shutil.copy2(source_path, target_path)
        print(f"installed skill {binding.skill_id} -> {target_skill_dir}")


def check_backend_target_paths(backend: str, args: argparse.Namespace) -> None:
    bindings = collect_skill_bindings(backend)
    if not bindings:
        raise DeployError(f"No payload bindings found for backend {backend}.")

    validation_issues: list[VerifyIssue] = []
    for binding in bindings:
        validation_issues.extend(verify_source_binding(binding))
    if validation_issues:
        details = "\n".join(
            f"  - {issue.code}: {issue.path} ({issue.detail})" for issue in validation_issues
        )
        raise DeployError(f"Cannot check target paths because source validation failed:\n{details}")

    target_root = target_root_for(backend, args)
    target_root_issues = [
        issue
        for issue in verify_target_root(backend, target_root)
        if issue.code != "missing-target-root"
    ]
    if target_root_issues:
        details = "\n".join(
            f"  - {issue.code}: {issue.path} ({issue.detail})" for issue in target_root_issues
        )
        raise DeployError(f"Cannot check target paths because target root is not ready:\n{details}")

    current_target_dirs_by_skill_id(bindings)
    plans = [build_install_plan(binding, target_root) for binding in bindings]
    conflicts = collect_path_conflicts(plans)
    conflicts.extend(collect_legacy_path_conflicts(plans, target_root))

    if conflicts:
        raise DeployError(
            f"[{backend}] found {len(conflicts)} conflicting target path(s)\n\n"
            f"{format_path_conflicts(conflicts)}"
        )

    print(f"[{backend}] ok: no conflicting target paths at {target_root}")


def verify_deployed_skill(binding: SkillBinding, target_root: Path) -> list[VerifyIssue]:
    try:
        plan = build_install_plan(binding, target_root)
    except DeployError as exc:
        return [
            VerifyIssue(
                code="payload-contract-invalid",
                path=binding.payload_path,
                detail=str(exc),
            )
        ]

    issues: list[VerifyIssue] = []
    target_metadata = plan.target_metadata
    target_skill_dir = plan.target_skill_dir
    if not target_skill_dir.exists():
        return [
            VerifyIssue(
                code="missing-target-entry",
                path=target_skill_dir,
                detail=f"missing deployed skill directory for skill {binding.skill_id}",
            )
        ]

    if target_skill_dir.is_symlink() or not target_skill_dir.is_dir():
        return [
            VerifyIssue(
                code="wrong-target-entry-type",
                path=target_skill_dir,
                detail=f"deployed skill directory must be a real directory for skill {binding.skill_id}",
            )
        ]

    marker_path = managed_skill_marker_path(target_skill_dir)
    marker = load_runtime_marker(marker_path)
    if marker is None:
        return [
            VerifyIssue(
                code="unrecognized-target-directory",
                path=target_skill_dir,
                detail=f"existing deployed directory has no recognized {MANAGED_SKILL_MARKER}",
            )
        ]
    if (
        marker.backend != plan.binding.backend
        or marker.skill_id != plan.binding.skill_id
        or marker.payload_version != plan.payload_version
    ):
        return [
            VerifyIssue(
                code="unrecognized-target-directory",
                path=target_skill_dir,
                detail=(
                    f"recognized {MANAGED_SKILL_MARKER} does not match current backend/skill/"
                    "payload_version"
                ),
            )
        ]

    skill_payload = load_binding_payload(binding)
    expected_marker = build_runtime_marker(
        plan.binding.backend,
        plan.binding.skill_id,
        plan.payload_version,
        plan.payload_fingerprint,
    )
    marker_matches_source = marker.payload_fingerprint == plan.payload_fingerprint
    if not marker_matches_source:
        issues.append(
            VerifyIssue(
                code="target-payload-drift",
                path=marker_path,
                detail=(
                    f"deployed payload fingerprint drifted from adapter source for skill "
                    f"{binding.skill_id}"
                ),
            )
        )

    for relative_name in target_metadata.required_payload_files:
        target_path = target_skill_dir / relative_name
        if not target_path.exists():
            issues.append(
                VerifyIssue(
                    code="missing-required-payload",
                    path=target_path,
                    detail=f"missing deployed payload file {relative_name} for skill {binding.skill_id}",
                )
            )
            continue
        if target_path.is_symlink() or not target_path.is_file():
            issues.append(
                VerifyIssue(
                    code="wrong-target-entry-type",
                    path=target_path,
                    detail=(
                        f"deployed payload file {relative_name} must be a real file for skill "
                        f"{binding.skill_id}"
                    ),
                )
            )
            continue
        if relative_name == MANAGED_SKILL_MARKER:
            if marker_matches_source and target_path.read_text(encoding="utf-8") != runtime_marker_text(
                expected_marker
            ):
                issues.append(
                    VerifyIssue(
                        code="target-payload-drift",
                        path=target_path,
                        detail=(
                            f"deployed payload file {relative_name} drifted from adapter source "
                            f"for skill {binding.skill_id}"
                        ),
                    )
                )
            continue
        source_path = source_path_for_target_relative_file(
            binding,
            relative_name,
            payload=skill_payload,
        )
        if source_path.read_text(encoding="utf-8") != target_path.read_text(encoding="utf-8"):
            issues.append(
                VerifyIssue(
                    code="target-payload-drift",
                    path=target_path,
                    detail=(
                        f"deployed payload file {relative_name} drifted from adapter source "
                        f"for skill {binding.skill_id}"
                    ),
                )
            )

    target_entry = target_skill_dir / target_metadata.target_entry_name
    if not target_entry.exists():
        issues.append(
            VerifyIssue(
                code="missing-target-entry",
                path=target_entry,
                detail=(
                    f"missing target entry {target_metadata.target_entry_name} "
                    f"for skill {binding.skill_id}"
                ),
            )
        )
    elif target_entry.is_symlink() or not target_entry.is_file():
        issues.append(
            VerifyIssue(
                code="wrong-target-entry-type",
                path=target_entry,
                detail=(
                    f"target entry {target_metadata.target_entry_name} must be a real file "
                    f"for skill {binding.skill_id}"
                ),
            )
        )

    return issues


def unexpected_managed_target_dirs(
    backend: str,
    target_root: Path,
    expected_target_dir_names: set[str],
) -> list[VerifyIssue]:
    if not target_root.is_dir():
        return []

    issues: list[VerifyIssue] = []
    for child in sorted(target_root.iterdir()):
        if child.is_symlink() or not child.is_dir():
            continue
        if child.name in expected_target_dir_names:
            continue

        marker = load_runtime_marker(managed_skill_marker_path(child))
        if marker is None or marker.backend != backend:
            continue

        issues.append(
            VerifyIssue(
                code="unexpected-managed-directory",
                path=child,
                detail=(
                    f"recognized managed install for skill {marker.skill_id} is not part of the "
                    "current source bindings"
                ),
            )
        )

    return issues


def verify_backend(backend: str, args: argparse.Namespace) -> VerifyResult:
    target_root = target_root_for(backend, args)
    issues = verify_target_root(backend, target_root)

    bindings = collect_skill_bindings(backend)
    for binding in bindings:
        issues.extend(verify_source_binding(binding))

    expected_target_dir_names: set[str] = set()
    if not issues:
        try:
            expected_target_dir_names = expected_target_dirs(bindings)
        except DeployError as exc:
            issues.append(
                VerifyIssue(
                    code="payload-contract-invalid",
                    path=adapter_skills_dir_for(backend),
                    detail=str(exc),
                )
            )

    if not issues and target_root.is_dir():
        for binding in bindings:
            issues.extend(verify_deployed_skill(binding, target_root))
        issues.extend(
            unexpected_managed_target_dirs(backend, target_root, expected_target_dir_names)
        )

    return VerifyResult(
        backend=backend,
        target_root=target_root,
        issues=issues,
    )


def prune_all_managed_target_dirs(backend: str, args: argparse.Namespace) -> None:
    target_root = target_root_for(backend, args)
    target_root_issues = [
        issue
        for issue in verify_target_root(backend, target_root)
        if issue.code != "missing-target-root"
    ]
    if target_root_issues:
        details = "\n".join(
            f"  - {issue.code}: {issue.path} ({issue.detail})" for issue in target_root_issues
        )
        raise DeployError(f"Cannot prune managed installs because target root is not ready:\n{details}")

    if not target_root.exists():
        print(f"no managed skill dirs found at {target_root}")
        return

    removed_count = 0
    for child in sorted(target_root.iterdir()):
        if child.is_symlink() or not child.is_dir():
            continue

        marker = load_runtime_marker(managed_skill_marker_path(child))
        if marker is None or marker.backend != backend:
            continue

        try:
            shutil.rmtree(child)
        except Exception as exc:
            raise DeployError(f"Failed to remove managed skill dir {child}: {exc}") from exc
        removed_count += 1
        print(f"removed managed skill dir {child}")

    if removed_count == 0:
        print(f"no managed skill dirs found at {target_root}")


def print_verify_result(result: VerifyResult) -> None:
    if not result.issues:
        print(f"[{result.backend}] ok: target root is ready at {result.target_root}")
        return

    print(
        f"[{result.backend}] drift: {len(result.issues)} issue(s) in target root at {result.target_root}"
    )
    for issue in result.issues:
        print(f"  - {issue.code}: {issue.path} ({issue.detail})")


def target_root_status(path: Path) -> str:
    if path.is_symlink():
        if path.exists():
            return "symlink"
        return "broken-symlink"
    if path.is_dir():
        return "directory"
    if path.exists():
        return "wrong-type"
    return "missing"


def managed_install_dirs(backend: str, target_root: Path) -> list[Path]:
    if not target_root.is_dir():
        return []

    managed_dirs: list[Path] = []
    for child in sorted(target_root.iterdir()):
        if child.is_symlink() or not child.is_dir():
            continue
        marker = load_runtime_marker(managed_skill_marker_path(child))
        if marker is not None and marker.backend == backend:
            managed_dirs.append(child)
    return managed_dirs


def is_update_blocking_issue(issue: VerifyIssue, managed_delete_paths: set[Path]) -> bool:
    if issue.code in UPDATE_RECOVERABLE_ISSUE_CODES:
        return False
    if issue.code == "unrecognized-target-directory" and issue.path in managed_delete_paths:
        return False
    return True


def collect_update_target_entry_issues(
    backend: str,
    target_root: Path,
    known_target_dir_names: set[str],
) -> list[VerifyIssue]:
    if not target_root.is_dir():
        return []

    issues: list[VerifyIssue] = []
    for child in sorted(target_root.iterdir()):
        if child.is_symlink() or not child.is_dir():
            if child.name in known_target_dir_names:
                issues.append(
                    VerifyIssue(
                        code="wrong-target-entry-type",
                        path=child,
                        detail="update target path must be a real directory before reinstall",
                    )
                )
            continue

        marker = load_runtime_marker(managed_skill_marker_path(child))
        if marker is None:
            issues.append(
                VerifyIssue(
                    code="unrecognized-target-directory",
                    path=child,
                    detail="update will not remove target directories without a recognized marker",
                )
            )
            continue

        if marker.backend != backend:
            issues.append(
                VerifyIssue(
                    code="foreign-managed-directory",
                    path=child,
                    detail=(
                        f"update will not remove managed directory for backend {marker.backend}"
                    ),
                )
            )

    return issues


def dedupe_issues(issues: list[VerifyIssue]) -> list[VerifyIssue]:
    seen: set[tuple[str, str]] = set()
    unique_issues: list[VerifyIssue] = []
    for issue in issues:
        key = (issue.code, str(issue.path))
        if key in seen:
            continue
        seen.add(key)
        unique_issues.append(issue)
    return unique_issues


def issue_to_dict(issue: VerifyIssue) -> dict[str, str]:
    return {
        "code": issue.code,
        "path": str(issue.path),
        "detail": issue.detail,
    }


def diagnostic_summary(result: VerifyResult) -> dict[str, Any]:
    issue_codes = sorted({issue.code for issue in result.issues})
    managed_dirs = managed_install_dirs(result.backend, result.target_root)
    unrecognized_issues = [
        issue for issue in result.issues if issue.code in UNRECOGNIZED_ISSUE_CODES
    ]
    conflict_issues = [
        issue for issue in result.issues if issue.code in CONFLICT_ISSUE_CODES
    ]

    return {
        "backend": result.backend,
        "source_root": str(REPO_ROOT),
        "target_root": str(result.target_root),
        "target_root_status": target_root_status(result.target_root),
        "target_root_exists": result.target_root.exists(),
        "binding_count": len(collect_skill_bindings(result.backend)),
        "managed_install_count": len(managed_dirs),
        "managed_installs": [str(path) for path in managed_dirs],
        "issue_count": len(result.issues),
        "issue_codes": issue_codes,
        "issues": [issue_to_dict(issue) for issue in result.issues],
        "unrecognized_count": len(unrecognized_issues),
        "unrecognized": [issue_to_dict(issue) for issue in unrecognized_issues],
        "conflict_count": len(conflict_issues),
        "conflicts": [issue_to_dict(issue) for issue in conflict_issues],
    }


def print_diagnostic_summary(summary: dict[str, Any]) -> None:
    print(
        f"[{summary['backend']}] diagnose: {summary['issue_count']} issue(s), "
        f"{summary['managed_install_count']} managed install(s) at {summary['target_root']}"
    )
    if summary["issue_codes"]:
        print(f"issue codes: {', '.join(summary['issue_codes'])}")
    if summary["unrecognized_count"]:
        print(f"unrecognized target entries: {summary['unrecognized_count']}")
    if summary["conflict_count"]:
        print(f"conflict entries: {summary['conflict_count']}")


def update_plan_summary(backend: str, args: argparse.Namespace) -> dict[str, Any]:
    result = verify_backend(backend, args)
    target_root = result.target_root
    bindings = collect_skill_bindings(backend)

    plan_issues: list[VerifyIssue] = []
    plans: list[InstallPlan] = []
    known_target_dir_names: set[str] = set()
    if not bindings:
        plan_issues.append(
            VerifyIssue(
                code="missing-backend-payload-source",
                path=adapter_skills_dir_for(backend),
                detail=f"No payload bindings found for backend {backend}.",
            )
        )
    else:
        try:
            known_target_dir_names = all_known_target_dirs(bindings)
            plans = [build_install_plan(binding, target_root) for binding in bindings]
        except DeployError as exc:
            plan_issues.append(
                VerifyIssue(
                    code="payload-contract-invalid",
                    path=adapter_skills_dir_for(backend),
                    detail=str(exc),
                )
            )

    target_entry_issues = collect_update_target_entry_issues(
        backend,
        target_root,
        known_target_dir_names,
    )
    managed_installs_to_delete = managed_install_dirs(backend, target_root)
    managed_delete_paths = set(managed_installs_to_delete)
    all_issues = dedupe_issues([*result.issues, *plan_issues, *target_entry_issues])
    blocking_issues = [
        issue for issue in all_issues if is_update_blocking_issue(issue, managed_delete_paths)
    ]

    return {
        "backend": backend,
        "source_root": str(REPO_ROOT),
        "target_root": str(target_root),
        "operation_sequence": [
            "prune --all",
            "check_paths_exist",
            "install",
            "verify",
        ],
        "managed_installs_to_delete": [str(path) for path in managed_installs_to_delete],
        "planned_target_paths": [str(plan.target_skill_dir) for plan in plans],
        "issue_count": len(all_issues),
        "issues": [issue_to_dict(issue) for issue in all_issues],
        "blocking_issue_count": len(blocking_issues),
        "blocking_issues": [issue_to_dict(issue) for issue in blocking_issues],
    }


def print_update_plan(summary: dict[str, Any]) -> None:
    print(f"[{summary['backend']}] update plan for {summary['target_root']}")
    print("sequence: " + " -> ".join(summary["operation_sequence"]))
    print(f"managed installs to delete: {len(summary['managed_installs_to_delete'])}")
    for path in summary["managed_installs_to_delete"]:
        print(f"  - {path}")
    print(f"target paths to write: {len(summary['planned_target_paths'])}")
    for path in summary["planned_target_paths"]:
        print(f"  - {path}")
    print(f"blocking preflight issues: {summary['blocking_issue_count']}")
    for issue in summary["blocking_issues"]:
        print(f"  - {issue['code']}: {issue['path']} ({issue['detail']})")


def run_update_backend(backend: str, args: argparse.Namespace) -> int:
    if args.json and args.yes:
        raise DeployError("update --json is only supported for dry-run plans; omit --json with --yes")

    summary = update_plan_summary(backend, args)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 1 if summary["blocking_issue_count"] else 0

    print_update_plan(summary)
    if summary["blocking_issue_count"]:
        raise DeployError(
            f"[{backend}] update blocked by {summary['blocking_issue_count']} preflight issue(s)"
        )

    if not args.yes:
        print(f"[{backend}] dry-run only; pass --yes to apply update")
        return 0

    print(f"[{backend}] applying update")
    prune_all_managed_target_dirs(backend, args)
    check_backend_target_paths(backend, args)
    install_backend_payloads(backend, args)
    result = verify_backend(backend, args)
    if result.issues:
        print_verify_result(result)
        raise DeployError(f"[{backend}] update failed strict verify with {len(result.issues)} issue(s)")
    print_verify_result(result)
    print(f"[{backend}] update complete")
    return 0


def main(
    argv: list[str] | None = None,
    *,
    prog: str | None = None,
    description: str | None = None,
) -> int:
    args = parse_args(argv, prog=prog, description=description)
    try:
        if args.mode == "verify":
            results = [verify_backend(backend, args) for backend in iter_backends(args.backend)]
            for result in results:
                print_verify_result(result)
            return 1 if any(result.issues for result in results) else 0

        if args.mode == "diagnose":
            results = [verify_backend(backend, args) for backend in iter_backends(args.backend)]
            summaries = [diagnostic_summary(result) for result in results]
            if args.json:
                payload: dict[str, Any]
                if len(summaries) == 1:
                    payload = summaries[0]
                else:
                    payload = {"backends": summaries}
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                for summary in summaries:
                    print_diagnostic_summary(summary)
            return 0

        if args.mode == "prune":
            if not args.all:
                raise DeployError("prune currently requires --all")
            for backend in iter_backends(args.backend):
                prune_all_managed_target_dirs(backend, args)
            return 0

        if args.mode == "check_paths_exist":
            for backend in iter_backends(args.backend):
                check_backend_target_paths(backend, args)
            return 0

        if args.mode == "install":
            for backend in iter_backends(args.backend):
                install_backend_payloads(backend, args)
            return 0

        if args.mode == "update":
            exit_code = 0
            for backend in iter_backends(args.backend):
                exit_code = max(exit_code, run_update_backend(backend, args))
            return exit_code
    except DeployError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
