# Research Scripts

本目录放 research runner 脚本与 prompt 入口，不承载研究产物本身。

当前结构：

- `run_skill_suite.py`：统一 runner，支持 direct run 和 suite run
- `run_claude_skill_eval.py`：Claude 兼容壳，参数翻译后委托 `run_skill_suite.py`
- `run_backend_acceptance_matrix.py`：live acceptance 入口，固定跑 `codex -> codex` 与 `claude -> codex` 两条矩阵
- `run_autoresearch.py`：autoresearch P0.1/P0.2/P0.3 入口，负责 baseline 数据面、worktree 控制壳和 round 外环
- `autoresearch_contract.py`：P0.1 contract 读取、schema 校验、suite/path 边界校验
- `autoresearch_scoreboard.py`：P0.1 baseline scoreboard 聚合与校验
- `autoresearch_round.py`：P0.3 的 mutation / round scoreboard / decision 聚合与固定 keep-discard 规则
- `worktree_manager.py`：P0.2 的 git worktree 生命周期管理器
- `backends/`：backend registry、抽象 contract、以及 `claude / codex / opencode` 适配层
- `common.py`：repo/task/suite/eval schema/artifact 的共享解析与写盘逻辑
- `tasks/`：skill research prompt 模板

## 运行模型

`run_skill_suite.py` 是主入口。

- `--repo` 模式：对单个 repo 执行一个 task 或全部 task
- `--suite` 模式：从 `toolchain/evals/fixtures/suites/` 或显式 manifest 路径加载一组 runs
- `--with-eval`：每个 skill run 后追加对应 eval run；judge backend 默认继承 `--backend`
- `--save-dir`：可选；runner 会在该目录下创建一个 `UTC 时间戳 + slug(label)` 的 run 子目录
- `--jobs`：可选；按 spec pipeline 并发执行。每条 pipeline 内仍保持 `skill -> eval` 顺序，默认 `1`

兼容入口 `run_claude_skill_eval.py` 只保留 Claude 旧调用方式：

- 固定转发为 `--backend claude`
- `--with-eval` 时固定转发 `--judge-backend claude`
- 其余参数仍使用当前 unified runner 的执行与落盘逻辑

`run_backend_acceptance_matrix.py` 则是另一层定位：

- 它不是新的 runner，只是为 live acceptance 生成一份临时 suite，再委托 `run_skill_suite.py`
- 固定矩阵是 `codex -> codex` 与 `claude -> codex`
- 每条 lane 都跑 `task: all`，因此会覆盖四个 skills
- 这是高成本、真实 backend 的系统级验收，不是普通 deterministic regression

`run_autoresearch.py` 当前覆盖三层边界：

- `init`：读取并校验 contract，初始化 `.autoworkflow/autoresearch/<run-id>/contract.json` 与 `history.tsv`
- `baseline`：按 contract 分开执行 train/validation suite，写 `scoreboard.json` 并记录 baseline 历史行
- baseline 只跑 train/validation；acceptance suite 仅作为 contract fixture 引用，不在 P0.1 默认 baseline 中执行
- `prepare-round`：在不切换当前工作树的前提下创建 `candidate/<run-id>/rNNN` 和独立 worktree，并写 `runtime.json`、`round.json`、`worktree.json`
- `prepare-round --mutation`：在创建 candidate worktree 后把本轮人工提供的 `mutation.json` 写入 `rounds/round-NNN/`，并校验 `target_paths` 必须落在 contract 的 `mutable_paths` 内
- `run-round`：要求 `agent-report.md` 已写入 round 目录；脚本会先校验 candidate 改动只能触达 `mutation.json` 的 `target_paths`、且动作类型符合 `allowed_actions`，然后提交 candidate 改动、从 candidate worktree 运行 train / validation suites，并写 round 级 `scoreboard.json`
- `decide-round`：读取 baseline scoreboard 和本轮 scoreboard，按固定规则写 `decision.json`，然后调用 promote 或 discard；fixed rule 同时约束 score、parse_error、timeout 与 hard-fail/pass_rate 非回退
- `promote-round`：只允许 fast-forward 语义，把 `champion/<run-id>` 前进到 active candidate commit，然后清理 candidate branch/worktree
- `discard-round`：直接删除 active candidate branch/worktree，不走 `git revert`
- `cleanup-round`：按 `.autoworkflow/autoresearch/<run-id>/runtime.json` 回收中断残留的 active candidate
- P0.3 仍不实现自动 mutation 搜索、多角色 planner / proposer / critic、或 acceptance 每轮必跑
- candidate 内容改动与 `agent-report.md` 仍由 Codex / subagent 完成；脚本只负责 git 生命周期、评测与 keep / discard

### Autoresearch P0.1 Contract And Data Plane

P0.1 当前代码侧的最小 contract / 数据面行为固定为：

- `autoresearch_contract.py` 会先按 `toolchain/evals/fixtures/schemas/autoresearch-contract.schema.json` 校验 contract JSON
- `load_contract()` 会解析并缓存：
  - `run_id`
  - `train_suites` / `validation_suites` / `acceptance_suites`
  - `mutable_paths` / `frozen_paths`
- suite manifest 的解析顺序是：
  - 先看 contract 文件同目录
  - 再看显式绝对路径
  - 最后回退到 `toolchain/evals/fixtures/suites/`
- `mutable_paths` / `frozen_paths` 会先被归一化为 repo-relative path，再检查是否越过 repo root 或彼此重叠
- `history.tsv` 列顺序当前固定为：
  - `round`
  - `kind`
  - `base_sha`
  - `candidate_sha`
  - `train_score`
  - `validation_score`
  - `train_parse_error_rate`
  - `validation_parse_error_rate`
  - `decision`
  - `notes`
- `autoresearch_scoreboard.py` 当前只聚合 `train` 和 `validation` 两条 lane；lane 指标来自 `run-summary.json` 中 `phase=eval` 的结果
- round 级字段 `rounds_completed` / `best_round` 在 baseline scoreboard 中会初始化为 `0`，留给后续阶段更新

### Autoresearch P0.1 Baseline Flow And Artifacts

P0.1 在共享 CLI 下的实际入口是：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  init \
  --contract /path/to/contract.json

python3 toolchain/scripts/research/run_autoresearch.py \
  baseline \
  --contract /path/to/contract.json
```

当前 `init` / `baseline` 的实际落盘行为是：

- `init`
  - 校验 contract
  - 写 `.autoworkflow/autoresearch/<run-id>/contract.json`
  - 初始化 `history.tsv`
  - 由于共享同一个入口，也会创建 `runtime.json` 作为后续阶段的前向兼容状态文件
- `baseline`
  - 只运行 `train_suites` 和 `validation_suites`
  - 不运行 `acceptance_suites`
  - 产物会写到：
    - `.autoworkflow/autoresearch/<run-id>/baseline/train/`
    - `.autoworkflow/autoresearch/<run-id>/baseline/validation/`
  - 聚合后写：
    - `.autoworkflow/autoresearch/<run-id>/scoreboard.json`
    - `.autoworkflow/autoresearch/<run-id>/history.tsv`

当前 baseline `scoreboard.json` 的代码行为包括：

- 顶层保留：
  - `run_id`
  - `generated_at`
  - `baseline_sha`
  - `rounds_completed`
  - `best_round`
- lane 级保留：
  - `lane_name`
  - `suite_file`
  - `backend`
  - `judge_backend`
  - `repos_total`
  - `tasks_total`
  - `pass_rate`
  - `timeout_rate`
  - `parse_error_rate`
  - `avg_total_score`
- repo/task 级保留：
  - `repo`
  - `task`
  - `phase`
  - `total_score`
  - `overall`
  - `dimension_feedback`

baseline 写入 `history.tsv` 的约定当前固定为：

- `round = 0`
- `kind = baseline`
- `candidate_sha = -`
- `decision = baseline`

### Autoresearch P0.1 Guardrails

P0.1 当前已固定的校验和边界是：

- contract 必须通过 schema 校验；缺少必填字段会直接失败
- suite manifest 缺失会直接失败
- `mutable_paths` 和 `frozen_paths` 不能重叠
- path 不允许逃出 repo root
- baseline 只消费 `train` / `validation` suites；`acceptance` 当前只作为 contract 引用和后续阶段输入保留
- scoreboard 只基于 `phase=eval` 的结果聚合，不把 skill phase 原始输出直接当分数输入

### Autoresearch P0.1 Verified Scope

当前已验证的范围是：

- contract schema 校验可工作
- 缺字段 contract 会被拒绝
- 缺失 suite manifest 会被拒绝
- `mutable_paths` / `frozen_paths` 重叠会被拒绝
- lane 聚合会正确计算 `pass_rate`、`timeout_rate`、`parse_error_rate`、`avg_total_score`
- repo/task 行会保留 `overall` 与 `dimension_feedback`
- `init` 会写出 `contract.json`、`history.tsv`、`runtime.json`
- `baseline` 会写出 `scoreboard.json`，并追加 baseline 历史行

当前没有承诺或未覆盖的范围是：

- `acceptance_suites` 在 P0.1 baseline 中自动执行
- candidate worktree、round loop、mutation、keep / discard 决策
- qualitative veto 的自动执行逻辑；当前只保留 contract 字段入口

### Autoresearch P0.3 Round Artifacts

单轮 round 目录固定在：

```text
.autoworkflow/autoresearch/<run-id>/rounds/round-NNN/
```

当前脚本会读写或要求存在的最小产物：

- `round.json`：round 编号、`base_sha`、candidate 分支/worktree、当前状态
- `worktree.json`：candidate worktree 路径、分支、`base_sha`、`candidate_sha`、清理时间
- `mutation.json`：本轮单个 mutation spec，至少包含 `round`、`mutation_id`、`kind`、`target_paths`、`allowed_actions`、`instruction`、`expected_effect`
- `agent-report.md`：由 Codex / subagent 写出的本轮内容工作摘要；缺失时 `run-round` 会直接失败
- `train/`：本轮 train suite 的 run artifacts
- `validation/`：本轮 validation suite 的 run artifacts
- `scoreboard.json`：本轮 train / validation 聚合结果
- `decision.json`：固定 keep / discard 规则输出

根目录还会持续维护：

- `contract.json`
- `runtime.json`
- `history.tsv`
- 顶层 `scoreboard.json`：作为 baseline 比较基线，并在 round 裁决后更新 `rounds_completed` 与 `best_round`

### Autoresearch P0.3 Guardrails

P0.3 的脚本侧约束当前固定为：

- `prepare-round --mutation` 会先校验 `mutation.json`：
  - `target_paths` 必须落在 contract 的 `mutable_paths` 内
  - `target_paths` 不得与 `frozen_paths` 重叠
  - `allowed_actions` 只能使用当前脚本支持的动作类型
- `run-round` 只允许在 round 状态为 `candidate_active` 时执行
- `decide-round` 只允许在 round 状态为 `evaluated` 时执行
- `run-round` 会同时校验两类 candidate 改动：
  - candidate 相对 `base_sha` 的全部已提交差异
  - candidate worktree 当前未提交差异
- 上述两类差异都会统一受 `target_paths`、`allowed_actions`、`frozen_paths` 约束
- 这意味着“先在 candidate worktree 手工提交越界改动，再执行 `run-round`”现在也会被拦截，不再能用 clean worktree 绕过校验

### Autoresearch P0.3 Keep / Discard Rule

`decide-round` 当前是固定脚本规则，不接受模型自由裁决：

- `keep` 同时要求：
  - train `avg_total_score` 严格高于 baseline
  - validation `avg_total_score` 不低于 baseline
  - train / validation `pass_rate` 不低于 baseline
  - train / validation `parse_error_rate` 不高于 baseline
  - train / validation `timeout_rate` 不高于 baseline
- `discard` 命中任一非回退检查失败即可
- `qualitative_veto_checks` 当前只保留字段入口，不提供奖励权；脚本不会因为定性描述把硬指标无提升的 round 提升为 `keep`

### Autoresearch P0.3 Verified Scope

当前已验证的范围是：

- `init -> baseline -> prepare-round --mutation -> run-round -> decide-round` 主路径可跑通
- `keep` 路径可跑通
- `discard` 路径可跑通
- committed-change bypass 已修复：candidate 先手工提交越界改动时，`run-round` 会失败
- worktree 生命周期仍由脚本控制，不污染当前用户工作树

当前没有承诺或未覆盖的范围是：

- 自动 mutation 搜索
- planner / proposer / critic 等多角色主控
- acceptance suite 每轮必跑
- 对 candidate 分支“每一个中间提交”做逐提交历史审计；当前只校验相对 `base_sha` 的净变更和当前未提交变更

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

单 repo，全量 task 并发跑四个 skills：

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --repo typer \
  --backend codex \
  --task all \
  --with-eval \
  --jobs 4 \
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

autoresearch P0.1 初始化：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  init \
  --contract /path/to/contract.json
```

autoresearch P0.1 baseline：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  baseline \
  --contract /path/to/contract.json
```

autoresearch P0.3 准备一轮 candidate：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  prepare-round \
  --contract /path/to/contract.json \
  --mutation /path/to/mutation.json
```

在 candidate worktree 内完成允许的改动，并把 `agent-report.md` 写到：

```text
.autoworkflow/autoresearch/<run-id>/rounds/round-NNN/agent-report.md
```

随后运行 round 评测与裁决：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  run-round \
  --contract /path/to/contract.json

python3 toolchain/scripts/research/run_autoresearch.py \
  decide-round \
  --contract /path/to/contract.json
```

autoresearch P0.2 promote / discard / cleanup：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  promote-round \
  --contract /path/to/contract.json

python3 toolchain/scripts/research/run_autoresearch.py \
  discard-round \
  --contract /path/to/contract.json

python3 toolchain/scripts/research/run_autoresearch.py \
  cleanup-round \
  --contract /path/to/contract.json
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
- 开启并发时，runner 会保持结果打印顺序、artifact 编号和 `run-summary.json` 顺序稳定；如果需要最保守的 backend 行为，可退回 `--jobs 1`
