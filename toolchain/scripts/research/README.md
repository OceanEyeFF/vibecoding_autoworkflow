# Research Scripts

本目录放 research runner 脚本与 prompt 入口，不承载研究产物本身。

当前结构：

- `run_skill_suite.py`：统一 runner，支持 direct run 和 suite run
- `run_claude_skill_eval.py`：Claude 兼容壳，参数翻译后委托 `run_skill_suite.py`
- `run_backend_acceptance_matrix.py`：live acceptance 入口，固定跑 `codex -> codex` 与 `claude -> codex` 两条矩阵
- `backends/`：backend registry、抽象 contract、以及 `claude / codex / opencode` 适配层
- `common.py`：repo/task/suite/eval schema/artifact 的共享解析与写盘逻辑
- `tasks/`：skill research prompt 模板

## 运行模型

`run_skill_suite.py` 是主入口。

- `--repo` 模式：对单个 repo 执行一个 task 或全部 task
- `--suite` 模式：从 `toolchain/evals/fixtures/suites/` 或显式 manifest 路径加载一组 runs
- `--with-eval`：每个 skill run 后追加对应 eval run；judge backend 默认继承 `--backend`
- `--save-dir`：可选；runner 会在该目录下创建一个 `UTC 时间戳 + slug(label)` 的 run 子目录

兼容入口 `run_claude_skill_eval.py` 只保留 Claude 旧调用方式：

- 固定转发为 `--backend claude`
- `--with-eval` 时固定转发 `--judge-backend claude`
- 其余参数仍使用当前 unified runner 的执行与落盘逻辑

`run_backend_acceptance_matrix.py` 则是另一层定位：

- 它不是新的 runner，只是为 live acceptance 生成一份临时 suite，再委托 `run_skill_suite.py`
- 固定矩阵是 `codex -> codex` 与 `claude -> codex`
- 每条 lane 都跑 `task: all`，因此会覆盖四个 skills
- 这是高成本、真实 backend 的系统级验收，不是普通 deterministic regression

## Backend Adapter Layer

`backends/base.py` 定义最小 backend contract：

- `healthcheck()`：校验可执行文件是否可用
- `build_skill_command()` / `build_eval_command()`：为 skill 与 eval phase 构造命令
- `extract_final_message()`：从 stdout 或 backend 输出文件中提取最终消息

当前 backend 状态：

- `claude`：直接把 prompt 作为命令参数传入；支持 JSON schema judge
- `codex`：通过 stdin 传 prompt，使用 `--output-last-message` 提取最终消息；支持 JSON schema judge
- `opencode`：仅保留 backend slot，healthcheck 会明确返回未实现

## Eval Behavior

eval prompt 由 `common.py` 统一生成：

- 先把 skill 输出注入 task 对应的 eval prompt
- 如果 judge backend 支持 JSON schema，则按 task 动态物化 score-key 与 `dimension_feedback` key 受限的 schema
- schema 在未落盘时写入临时文件；启用 `--save-dir` 时写入 run 目录
- Claude judge 在 schema 模式下会切到 `--output-format json`
- Codex judge 使用 `--output-schema <schema-path>`
- 不支持 schema 的 judge 仍可返回 rubric text，runner 会解析 `scores` 与按维度的 `What Worked / Needs Improvement` 反馈

这里的差异只停留在执行层：task、prompt、summary、artifact 命名都由 unified runner 统一处理。

## Suite Manifest

suite manifest 支持 YAML 或 JSON，当前 fixture 示例见 `toolchain/evals/fixtures/suites/memory-side-skills.v1.yaml`。

最小形态：

```yaml
version: 1
defaults:
  backend: claude
  judge_backend: claude
  with_eval: true
runs:
  - repo: typer
    task: all
```

`--suite` 模式下，`--backend`、`--judge-backend`、`--task`、`--with-eval`、`--prompt-file`、`--eval-prompt-file` 都不再接受命令行覆盖。

## Examples

单 repo，运行单个 task：

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --repo typer \
  --backend claude \
  --task context-routing
```

单 repo，Codex 执行 skill，Claude 执行 eval，并保存结果：

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --repo typer \
  --backend codex \
  --task all \
  --with-eval \
  --judge-backend claude \
  --save-dir /tmp/skill-evals
```

按 suite 执行：

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --suite memory-side-skills.v1.yaml \
  --save-dir /tmp/skill-evals
```

backend acceptance matrix：

```bash
python3 toolchain/scripts/research/run_backend_acceptance_matrix.py \
  --repo typer \
  --save-dir /tmp/backend-acceptance
```

Claude 兼容壳：

```bash
python3 toolchain/scripts/research/run_claude_skill_eval.py \
  --repo typer \
  --task context-routing \
  --with-eval
```

## Saved Artifacts

默认不落盘。传 `--save-dir` 后，每轮 run 会生成一个独立子目录，并写入：

- `*.prompt.txt`：实际发送给 backend 的 prompt 文本
- `*.response.md`：展示口径的响应副本，内容等于 `final_message`，若没有则回退为 `raw_stdout`
- `*.final.txt`：backend 提取出的最终消息；若 backend 没有单独 final message，可为空文件
- `*.raw.stdout.txt`：进程原始 stdout
- `*.raw.stderr.txt`：进程原始 stderr，仅在 stderr 非空时写入
- `*.stderr.txt`：兼容保留的 stderr 副本，仅在 stderr 非空时写入
- `*.eval-schema.<judge>.json`：本次 eval 实际使用的 task-scoped schema，仅 schema judge 写入
- `*.structured.json`：规范化后的 eval 结构化结果；其中除了分数，还会保留每个维度的 `dimension_feedback`
- `*.meta.json`：单条结果元数据，含 command、returncode、timing、schema_file、parse_error、artifacts
- `run-summary.json`：整轮汇总，含 `summary_schema` 路径、suite 来源和所有 result 记录

artifact 文件名按序号、repo、task、phase、backend 组合生成，例如：

- `01.typer.context-routing.skill.claude.*`
- `02.typer.context-routing.eval.codex-judge-claude.*`

## Minimal Constraints

- 脚本目录只放 runner 与 prompt，不把研究输出直接写回这里
- 需要产物时显式传 `--save-dir`
- 研究输出目录应放在脚本目录之外
- 旧的 Claude-only 调用可以继续走兼容壳，但新的行为应以 `run_skill_suite.py` 为准
- live acceptance matrix 依赖真实 backend，可有成本与波动，不应当作快速 CI 或 cheap regression
