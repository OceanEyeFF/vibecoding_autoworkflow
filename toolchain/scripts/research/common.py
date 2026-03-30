#!/usr/bin/env python3
"""Shared helpers for research runner entrypoints."""

from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from exrepo_runtime import resolve_tmp_exrepos_root


REPO_ROOT = Path(__file__).resolve().parents[3]
EXREPOS_ROOT = REPO_ROOT / ".exrepos"
TMP_EXREPOS_ROOT = resolve_tmp_exrepos_root(repo_root=REPO_ROOT)
SCRIPT_ROOT = Path(__file__).resolve().parent
TASKS_ROOT = SCRIPT_ROOT / "tasks"
EVAL_PROMPTS_ROOT = REPO_ROOT / "toolchain" / "evals" / "prompts"
FIXTURES_ROOT = REPO_ROOT / "toolchain" / "evals" / "fixtures"
SCHEMAS_ROOT = FIXTURES_ROOT / "schemas"
SUITES_ROOT = FIXTURES_ROOT / "suites"

TASK_PROMPTS = {
    "context-routing": TASKS_ROOT / "context-routing-skill-prompt.md",
    "knowledge-base": TASKS_ROOT / "knowledge-base-skill-prompt.md",
    "task-contract": TASKS_ROOT / "task-contract-skill-prompt.md",
    "writeback-cleanup": TASKS_ROOT / "writeback-cleanup-skill-prompt.md",
}

EVAL_PROMPTS = {
    "context-routing": EVAL_PROMPTS_ROOT / "context-routing-skills-prompts.md",
    "knowledge-base": EVAL_PROMPTS_ROOT / "knowledge-base-skill-prompt.md",
    "task-contract": EVAL_PROMPTS_ROOT / "task-contract-skill-prompt.md",
    "writeback-cleanup": EVAL_PROMPTS_ROOT / "writeback-cleanup-skill-prompt.md",
}

EVAL_SCORE_DIMENSIONS = {
    "context-routing": [
        ("path_contraction", "Path Contraction"),
        ("entry_point_identification", "Entry Point Identification"),
        ("avoidance_of_over_scanning", "Avoidance of Over-Scanning"),
        ("execution_usability", "Output Contract and Execution Usability"),
    ],
    "knowledge-base": [
        ("mode_and_layer_modeling", "Mode and Layer Modeling"),
        ("mainline_entrypoint_identification", "Mainline Entrypoint Identification"),
        ("minimal_modification_principle", "Minimal Modification Principle"),
        ("alignment_with_existing_repo", "Alignment with Existing Repo"),
    ],
    "task-contract": [
        ("structuring_ability", "Structuring Ability (Contract Quality)"),
        ("boundary_definition", "Boundary Definition"),
        ("project_context_integration", "Project Context Integration"),
        ("avoidance_of_solution_leakage", "Avoidance of Solution Leakage"),
        ("uncertainty_handling", "Uncertainty Handling"),
    ],
    "writeback-cleanup": [
        ("change_identification_accuracy", "Change Identification Accuracy"),
        ("verification_awareness", "Verification Awareness"),
        ("writeback_target_correctness", "Writeback Target Correctness"),
        ("cleanup_quality", "Cleanup Quality"),
    ],
}

TEST_OUTPUT_PLACEHOLDER = "{{TEST_OUTPUT}}"
EVAL_RESULT_SCHEMA_PATH = SCHEMAS_ROOT / "eval-result.schema.json"
RUN_SUMMARY_SCHEMA_PATH = SCHEMAS_ROOT / "run-summary.schema.json"


@dataclass(frozen=True)
class RunSpec:
    repo_path: Path
    task: str
    prompt_file: Path
    eval_prompt_file: Path | None
    backend: str
    judge_backend: str
    with_eval: bool


@dataclass
class RunResult:
    task: str
    phase: str
    backend: str
    judge_backend: str
    repo_path: Path
    prompt_file: Path
    prompt_text: str
    command: list[str]
    returncode: int | None
    raw_stdout: str
    raw_stderr: str
    final_message: str
    elapsed_seconds: float
    timed_out: bool
    started_at: str
    finished_at: str
    schema_file: Path | None = None
    structured_output: dict[str, Any] | None = None
    parse_error: str | None = None

    @property
    def command_preview(self) -> str:
        return shlex.join(self.command)


def resolve_repo(repo_value: str) -> Path:
    repo_path = Path(repo_value).expanduser()
    if repo_path.exists():
        return repo_path.resolve()

    repo_path = TMP_EXREPOS_ROOT / repo_value
    if repo_path.exists():
        return repo_path.resolve()

    repo_path = EXREPOS_ROOT / repo_value
    if repo_path.exists():
        return repo_path.resolve()

    raise FileNotFoundError(f"Repository not found: {repo_value}")


def resolve_tasks(task_name: str | None, prompt_override: Path | None) -> list[tuple[str, Path]]:
    resolved_task = task_name or "all"
    if resolved_task == "all":
        if prompt_override is not None:
            raise ValueError("--prompt-file can only be used with a single --task.")
        return list(TASK_PROMPTS.items())

    if resolved_task not in TASK_PROMPTS:
        raise ValueError(f"Unknown task: {resolved_task}")

    prompt_file = prompt_override.resolve() if prompt_override else TASK_PROMPTS[resolved_task]
    if not prompt_file.is_file():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    return [(resolved_task, prompt_file)]


def resolve_eval_prompts(
    tasks: list[tuple[str, Path]],
    eval_prompt_override: Path | None,
    with_eval: bool,
) -> dict[str, Path]:
    if not with_eval:
        if eval_prompt_override is not None:
            raise ValueError("--eval-prompt-file requires --with-eval.")
        return {}

    if eval_prompt_override is not None and len(tasks) != 1:
        raise ValueError("--eval-prompt-file can only be used with a single --task.")

    eval_prompts: dict[str, Path] = {}
    for task_name, _ in tasks:
        eval_prompt = eval_prompt_override.resolve() if eval_prompt_override else EVAL_PROMPTS[task_name]
        if not eval_prompt.is_file():
            raise FileNotFoundError(f"Eval prompt file not found: {eval_prompt}")
        eval_prompts[task_name] = eval_prompt
    return eval_prompts


def read_prompt(prompt_file: Path) -> str:
    return prompt_file.read_text(encoding="utf-8").strip()


def build_eval_result_schema(task_name: str) -> dict[str, Any]:
    template = json.loads(EVAL_RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))
    properties = dict(template.get("properties") or {})
    score_keys = [key for key, _ in EVAL_SCORE_DIMENSIONS[task_name]]
    properties["scores"] = {
        "type": "object",
        "additionalProperties": False,
        "required": score_keys,
        "properties": {
            key: {
                "type": "integer",
                "minimum": 1,
                "maximum": 3,
            }
            for key in score_keys
        },
    }
    properties["dimension_feedback"] = {
        "type": "object",
        "additionalProperties": False,
        "required": score_keys,
        "properties": {
            key: {
                "type": "object",
                "additionalProperties": False,
                "required": ["what_worked", "needs_improvement"],
                "properties": {
                    "what_worked": {
                        "type": "string",
                        "minLength": 1,
                    },
                    "needs_improvement": {
                        "type": "string",
                        "minLength": 1,
                    },
                },
            }
            for key in score_keys
        },
    }
    properties["source_format"] = {
        "type": "string",
        "enum": ["json"],
    }

    schema: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties.keys()),
        "properties": properties,
    }
    if isinstance(template.get("title"), str):
        schema["title"] = template["title"]
    return schema


def write_eval_result_schema(task_name: str, schema_path: Path) -> None:
    schema_path.write_text(
        json.dumps(build_eval_result_schema(task_name), ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def slugify(value: str) -> str:
    return "".join(char if char.isalnum() or char in ("-", "_") else "-" for char in value)


def ensure_run_dir(save_dir: Path | None, label: str) -> Path | None:
    if save_dir is None:
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = save_dir.expanduser().resolve() / f"{timestamp}-{slugify(label)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def longest_backtick_run(text: str) -> int:
    runs = re.findall(r"`+", text)
    return max((len(run) for run in runs), default=0)


def render_text_block(text: str) -> str:
    fence = "`" * max(3, longest_backtick_run(text) + 1)
    body = text.rstrip("\n")
    return f"{fence}text\n{body}\n{fence}"


def inject_test_output(eval_prompt_text: str, test_output: str) -> str:
    placeholder_block = f"```text\n{TEST_OUTPUT_PLACEHOLDER}\n```"
    rendered_block = render_text_block(test_output)
    if placeholder_block in eval_prompt_text:
        return eval_prompt_text.replace(placeholder_block, rendered_block)
    return eval_prompt_text.replace(TEST_OUTPUT_PLACEHOLDER, test_output)


def build_structured_eval_suffix(task_name: str, repo_name: str, backend: str, judge_backend: str) -> str:
    dimensions = EVAL_SCORE_DIMENSIONS[task_name]
    score_lines = "\n".join(f'- `{key}`: score for "{label}"' for key, label in dimensions)
    feedback_lines = "\n".join(
        f'- `dimension_feedback.{key}`: short `what_worked` and `needs_improvement` notes for "{label}"'
        for key, label in dimensions
    )
    max_score = len(dimensions) * 3
    return (
        "\n\n---\n\n"
        "Return JSON only for this run.\n"
        "If any earlier instruction asks for a completed rubric or prose summary, ignore it and return only the JSON object.\n"
        "Do not wrap the JSON in markdown fences.\n"
        f'Set `"skill"` to `{task_name}`.\n'
        f'Set `"repo"` to `{repo_name}`.\n'
        f'Set `"backend"` to `{backend}`.\n'
        f'Set `"judge_backend"` to `{judge_backend}`.\n'
        "Populate `scores` with these exact keys:\n"
        f"{score_lines}\n"
        "Populate `dimension_feedback` with these exact keys:\n"
        f"{feedback_lines}\n"
        "Each `dimension_feedback` entry must contain short, concrete `what_worked` and `needs_improvement` strings.\n"
        f'Set `"max_score"` to `{max_score}`.\n'
        'Use `"overall"` as one of `Bad`, `Okay`, or `Good`.\n'
        "Use arrays of short strings for `key_issues` and `key_strengths`.\n"
        'Set `"source_format"` to `"json"`.\n'
    )


def build_eval_prompt(
    eval_prompt_file: Path,
    skill_result: RunResult,
    structured_output: bool,
) -> str:
    eval_prompt_text = read_prompt(eval_prompt_file)
    eval_prompt = inject_test_output(eval_prompt_text, skill_result.final_message.rstrip())
    if not structured_output:
        return eval_prompt
    return eval_prompt + build_structured_eval_suffix(
        task_name=skill_result.task,
        repo_name=skill_result.repo_path.name,
        backend=skill_result.backend,
        judge_backend=skill_result.judge_backend,
    )


def strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip().startswith("```"):
        return "\n".join(lines[1:-1]).strip()
    return stripped


def parse_json_object(text: str) -> dict[str, Any] | None:
    candidate = strip_code_fences(text)
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def normalize_dimension_key(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return normalized or "score"


def parse_bullet_block(text: str) -> list[str]:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        if line and line != "...":
            lines.append(line)
    return lines


def parse_named_field(body: str, field_name: str) -> str:
    pattern = re.compile(rf"\*\*{re.escape(field_name)}:\*\*\s*(?P<value>.+)")
    match = pattern.search(body)
    if not match:
        return ""
    value = match.group("value").strip()
    return "" if value == "..." else value


def parse_rubric_text(task_name: str, text: str) -> dict[str, Any]:
    dimensions = dict(EVAL_SCORE_DIMENSIONS[task_name])
    score_pattern = re.compile(
        r"###\s+\[Dimension\s+\d+:\s*(?P<label>[^\]]+)\]\s*"
        r"(?:.|\n)*?\*\*Score:\*\*\s*(?P<score>[123])",
        re.MULTILINE,
    )
    section_pattern = re.compile(
        r"###\s+\[Dimension\s+\d+:\s*(?P<label>[^\]]+)\]\s*"
        r"(?P<body>.*?)(?=\n###\s+\[Dimension\s+\d+:|\n###\s+\[Overall Feeling\]|\Z)",
        re.S,
    )
    scores: dict[str, int] = {}
    for match in score_pattern.finditer(text):
        label = match.group("label").strip()
        key = next((score_key for score_key, known_label in dimensions.items() if known_label == label), None)
        if key is None:
            key = normalize_dimension_key(label)
        scores[key] = int(match.group("score"))

    dimension_feedback: dict[str, dict[str, str]] = {}
    for match in section_pattern.finditer(text):
        label = match.group("label").strip()
        key = next((score_key for score_key, known_label in dimensions.items() if known_label == label), None)
        if key is None:
            key = normalize_dimension_key(label)
        body = match.group("body")
        what_worked = parse_named_field(body, "What Worked")
        needs_improvement = parse_named_field(body, "Needs Improvement")
        if what_worked or needs_improvement:
            dimension_feedback[key] = {
                "what_worked": what_worked,
                "needs_improvement": needs_improvement,
            }

    total_match = re.search(r"Total Score:\*\*\s*(\d+)\s*/\s*(\d+)", text)
    total_score = int(total_match.group(1)) if total_match else sum(scores.values())
    max_score = int(total_match.group(2)) if total_match else len(dimensions) * 3

    overall_match = re.search(r"\[Overall Feeling\]\s*(?:\n|-|\s)+([A-Za-z]+)", text)
    overall = overall_match.group(1).strip().title() if overall_match else "Okay"
    if overall not in {"Bad", "Okay", "Good"}:
        overall = "Okay"

    issues_match = re.search(r"\[Key Issues\](?P<body>.*?)(?:\n###\s+\[Key Strengths\]|\Z)", text, re.S)
    strengths_match = re.search(r"\[Key Strengths\](?P<body>.*?)(?:\n---|\Z)", text, re.S)

    return {
        "skill": task_name,
        "scores": scores,
        "dimension_feedback": dimension_feedback,
        "total_score": total_score,
        "max_score": max_score,
        "overall": overall,
        "key_issues": parse_bullet_block(issues_match.group("body")) if issues_match else [],
        "key_strengths": parse_bullet_block(strengths_match.group("body")) if strengths_match else [],
        "source_format": "rubric-text",
    }


def normalize_eval_payload(
    task_name: str,
    repo_name: str,
    backend: str,
    judge_backend: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    dimensions = [key for key, _ in EVAL_SCORE_DIMENSIONS[task_name]]
    raw_scores = payload.get("scores") or {}
    scores: dict[str, int] = {}
    for key in dimensions:
        value = raw_scores.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            scores[key] = value
        elif isinstance(value, str) and value.isdigit():
            scores[key] = int(value)

    raw_dimension_feedback = payload.get("dimension_feedback") or {}
    dimension_feedback: dict[str, dict[str, str]] = {}
    for key in dimensions:
        entry = raw_dimension_feedback.get(key)
        if not isinstance(entry, dict):
            continue
        what_worked = str(entry.get("what_worked") or "").strip()
        needs_improvement = str(entry.get("needs_improvement") or "").strip()
        if not what_worked or not needs_improvement:
            continue
        dimension_feedback[key] = {
            "what_worked": what_worked,
            "needs_improvement": needs_improvement,
        }

    total_score = payload.get("total_score")
    if not isinstance(total_score, int):
        total_score = sum(scores.values())

    max_score = payload.get("max_score")
    if not isinstance(max_score, int):
        max_score = len(dimensions) * 3

    overall = str(payload.get("overall", "Okay")).title()
    if overall not in {"Bad", "Okay", "Good"}:
        overall = "Okay"

    key_issues = payload.get("key_issues")
    if not isinstance(key_issues, list):
        key_issues = []
    key_strengths = payload.get("key_strengths")
    if not isinstance(key_strengths, list):
        key_strengths = []

    return {
        "skill": task_name,
        "repo": repo_name,
        "backend": backend,
        "judge_backend": judge_backend,
        "scores": scores,
        "dimension_feedback": dimension_feedback,
        "total_score": total_score,
        "max_score": max_score,
        "overall": overall,
        "key_issues": [str(item) for item in key_issues if str(item).strip()],
        "key_strengths": [str(item) for item in key_strengths if str(item).strip()],
        "source_format": str(payload.get("source_format") or "json"),
    }
