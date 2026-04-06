# Eval Fixtures

`toolchain/evals/fixtures/` 只承载稳定的 fixture 资产：公共 schema 参考、suite manifest 和 copy-ready 模板。临时运行结果不会写回这里。

当前 fixture：

- `schemas/eval-result.schema.json`
- `schemas/run-summary.schema.json`
- `schemas/autoresearch-contract.schema.json`
- `schemas/autoresearch-scoreboard.schema.json`
- `suites/memory-side-skills.v1.yaml`
- `suites/memory-side-train.v1.yaml`
- `suites/memory-side-validation.v1.yaml`
- `suites/memory-side-acceptance.v1.yaml`
- `templates/autoresearch-p2-claude-claude/`

## Schemas

`schemas/eval-result.schema.json`

- 这是通用 eval 结果 contract 的参考模板。
- 它定义了结果对象的共享外形：`skill`、`repo`、`backend`、`judge_backend`、`scores`、`dimension_feedback`、`total_score`、`max_score`、`overall`、`key_issues`、`key_strengths`，以及可选的 `source_format`。
- 其中 `scores` 在这个公共 schema 里只约束为至少一个 `1..3` 的整数分值，不固定具体维度 key。
- `dimension_feedback` 在公共 schema 里约束为“按维度输出 `what_worked / needs_improvement`”的对象模板；实际运行时仍会被 runner 收紧成 task-scoped 的固定 key 集。
- 当 judge backend 支持 JSON Schema 时，runner 会按 task 的 `EVAL_SCORE_DIMENSIONS` 物化一个 task-scoped schema 文件，再把那个生成文件传给结构化 judge。
- 因此，这里的 `eval-result.schema.json` 是公共参考 contract，不是每次 eval 运行时直接下发给 judge 的最终 schema 文件。

`schemas/run-summary.schema.json`

- 这是 `run_skill_suite.py` 在 `--save-dir` 下写出的 `run-summary.json` 的 schema。
- 顶层字段包括 `runner`、`generated_at`、`suite_file`、`summary_schema` 和 `results`。
- `results` 里的每一项对应一次 `skill` 或 `eval` phase，记录 repo、task、backend、prompt 文件、返回码、超时状态、耗时、起止时间，以及生成的 artifact 文件名映射。
- 对 eval phase，条目还可带 `schema_file`、`structured_output` 和 `parse_error`。

`schemas/autoresearch-contract.schema.json`

- 固定 autoresearch P0.1 的 run contract 字段边界。
- 用于校验 `run_id`、suite 分层、path boundary、指标字段和预算字段。

`schemas/autoresearch-scoreboard.schema.json`

- 固定 autoresearch P0.1 的 scoreboard 聚合外形。
- 覆盖 run-level、lane-level、repo/task-level 的最小比较字段。

## Suite Manifests

`suites/memory-side-skills.v1.yaml`

- 这是 version `1` 的 suite manifest 示例。
- `defaults` 用来提供运行默认值；当前包含 `backend`、`judge_backend` 和 `with_eval`。
- `runs` 是执行列表；每个 entry 至少提供 `repo`，可选覆盖 `task`、`backend`、`judge_backend`、`with_eval`、`prompt_file`、`eval_prompt_file`。
- `task: all` 表示对该 repo 展开所有已注册 task prompt，而不是单个 task。
- `--suite` 支持显式路径，也支持直接引用 `toolchain/evals/fixtures/suites/` 下的文件名。

`suites/memory-side-train.v1.yaml`

- autoresearch P0.1 的 train lane fixture。

`suites/memory-side-validation.v1.yaml`

- autoresearch P0.1 的 validation lane fixture。

`suites/memory-side-acceptance.v1.yaml`

- autoresearch P0.1 的 acceptance lane fixture。
- 该 lane 在 P0.1 baseline 默认流程中不自动执行，只用于 contract/suite 分层固定。

## Templates

`templates/autoresearch-p2-claude-claude/`

- 这是一个 copy-ready 的最小 P2 manual-run 模板包。
- bundle 内包含：
  - `contract.template.json`
  - `train.template.yaml`
  - `validation.template.yaml`
  - `acceptance.template.yaml`
  - `manual-mutation.template.json`
- 默认配置固定到：
  - `target_task = context-routing-skill`
  - `target_prompt_path = toolchain/scripts/research/tasks/context-routing-skill-prompt.md`
  - `worker_backend = claude`
  - `expected_backend = claude`
  - `expected_judge_backend = claude`
- 这组文件不是直接运行产物目录；推荐先复制到 `.autoworkflow/manual-runs/...` 再按实际 repo 路径改值。

适合放在这里的内容：

- 被 runner 复用的稳定 schema fixture
- 被 `--suite` 直接消费的版本化 suite manifest
- 被人工复制后再落到 run-local state 的稳定模板

不适合放在这里的内容：

- 外部 repo checkout
- 临时 benchmark 产物
- 本地运行日志
- `--save-dir` 产生的 run artifacts
