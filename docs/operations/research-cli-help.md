---
title: "Research CLI 指令"
status: active
updated: 2026-03-26
owner: aw-kernel
last_verified: 2026-03-26
---
# Research CLI 指令

> 目的：给当前仓库的 research runner 提供一份 repo-local 操作说明，并把 `run_skill_suite.py` 与 `run_claude_skill_eval.py` 的当前 CLI 形状、suite 限制、artifact 输出和 backend 状态固定到代码真实行为。

## 一、当前入口

当前 active 入口有两个：

```bash
python3 toolchain/scripts/research/run_skill_suite.py
```

```bash
python3 toolchain/scripts/research/run_claude_skill_eval.py
```

```bash
python3 toolchain/scripts/research/run_backend_acceptance_matrix.py
```

当前定位：

- `run_skill_suite.py`：统一主入口
- `run_claude_skill_eval.py`：Claude 兼容壳
- `run_backend_acceptance_matrix.py`：live acceptance 入口

边界：

- 不再新增 `run_codex_skill_eval.py` 这类 backend-specific wrapper
- `run_skill_suite.py` 是唯一主实现
- `run_claude_skill_eval.py` 只保留兼容用途，不扩成第二套主 CLI
- `run_backend_acceptance_matrix.py` 也不是第二套 runner，它只是把固定矩阵组织成 suite 后委托统一 runner

## 二、统一主入口的当前用法

### 1. 单 task，只有 skill

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --repo typer \
  --backend claude \
  --task context-routing
```

### 2. 单 task，skill + eval

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --repo typer \
  --backend codex \
  --task context-routing \
  --with-eval \
  --judge-backend claude \
  --save-dir /tmp/skill-evals
```

### 3. 单 repo 全量 task

`--task` 在 `--repo` 模式下默认就是 `all`，所以这两种写法等价：

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --repo typer \
  --backend claude
```

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --repo typer \
  --backend claude \
  --task all
```

### 4. suite manifest

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --suite memory-side-skills.v1.yaml \
  --save-dir /tmp/skill-evals
```

`toolchain/evals/fixtures/suites/memory-side-skills.v1.yaml` 当前内容等价于：

- `version: 1`
- `defaults.backend: claude`
- `defaults.judge_backend: claude`
- `defaults.with_eval: true`
- `runs[0].repo: typer`
- `runs[0].task: all`

### 5. backend acceptance matrix

```bash
python3 toolchain/scripts/research/run_backend_acceptance_matrix.py \
  --repo typer \
  --save-dir /tmp/backend-acceptance
```

当前固定矩阵：

- `codex -> codex`
- `claude -> codex`

当前固定覆盖：

- 每条 lane 都跑 `task: all`
- 因此会覆盖四个 skills
- 这是 live acceptance，不是 cheap regression

### 6. 并发执行

`run_skill_suite.py` 支持：

- `--jobs <N>`

含义：

- 按 spec pipeline 并发执行
- 每个 pipeline 内仍保持 `skill -> eval` 串行
- 默认 `1`

对 `--repo typer --task all` 这类单仓全量运行，`--jobs 4` 可以把四个 skills 并行跑掉。

## 三、统一主入口的参数语义

### 1. 作用域

二选一，且必须提供其一：

- `--repo`
- `--suite`

说明：

- `--repo` 支持 `.exrepos/<name>` 下的仓库名，也支持显式路径
- `--suite` 支持显式路径；如果显式路径不存在，会继续尝试 `toolchain/evals/fixtures/suites/` 下的 `<name>`、`<name>.yaml`、`<name>.yml`、`<name>.json`

### 2. 直接 repo 模式

`--repo` 模式下：

- `--backend` 必填
- `--task` 可省略，默认 `all`
- `--judge-backend` 默认等于 `--backend`
- `--with-eval` 不传时只跑 skill

当前 task 选择只有：

- `context-routing`
- `knowledge-base`
- `task-contract`
- `writeback-cleanup`
- `all`

### 3. eval 相关参数

只有传了 `--with-eval`，下面这些参数才合法：

- `--judge-backend`
- `--eval-prompt-file`
- `--eval-model`
- `--eval-timeout`

否则会直接报错。

### 4. prompt 覆盖

- `--prompt-file`：只允许和单个 `--task` 一起使用
- `--eval-prompt-file`：只允许和单个 `--task` + `--with-eval` 一起使用

所以：

- `--task all --prompt-file ...` 不合法
- `--task all --eval-prompt-file ...` 不合法

### 5. 模型与超时

- `--model`：skill 阶段 model override
- `--eval-model`：eval 阶段 model override，默认继承 `--model`
- `--timeout`：每个 skill task 的超时，默认 `300`
- `--eval-timeout`：每个 eval task 的超时，默认继承 `--timeout`

### 6. backend-specific 运行参数

另有一个 runner-level 参数：

- `--jobs`

说明：

- `--jobs` 控制并发的 spec pipeline 数量
- 结果打印顺序、artifact 编号、`run-summary.json` 顺序仍按输入 spec 顺序保持稳定
- 如果希望最保守地观察真实 backend 行为，可以继续使用 `--jobs 1`

当前统一 CLI 还暴露这些 backend-specific 参数：

- `--claude-bin`
- `--permission-mode`
- `--output-format`
- `--codex-bin`
- `--sandbox`
- `--full-auto` / `--no-full-auto`
- `--opencode-bin`

当前默认值：

- Claude executable：`claude`
- Claude permission mode：`bypassPermissions`
- Claude output format：`text`
- Codex executable：`codex`
- Codex sandbox：`workspace-write`
- Codex `full-auto`：默认开启
- OpenCode executable 名：`opencode`

说明：

- 这些参数都由统一入口接受
- 只有实际被构建的 backend 会消费对应参数

## 四、suite 模式的真实限制

### 1. CLI 层明确禁止的参数

只要传了 `--suite`，下面这些 CLI 参数就不能再同时传：

- `--backend`
- `--judge-backend`
- `--task`
- `--with-eval`
- `--prompt-file`
- `--eval-prompt-file`

这是 `validate_args()` 的显式限制。

### 2. suite 里由 manifest 决定的字段

当前 suite manifest 自己负责决定：

- `repo`
- `backend`
- `judge_backend`
- `with_eval`
- `task`
- `prompt_file`
- `eval_prompt_file`

解析规则：

- `version` 当前只支持 `1`
- `runs` 必须是非空列表
- 每个 run 都必须有 `repo`
- `backend` 必须来自 run 自身或 `defaults.backend`
- `judge_backend` 默认回退到 run/backend
- `with_eval` 默认回退到 `defaults.with_eval`，再回退到 `false`
- `task` 默认 `all`

### 3. suite 模式仍然允许的 CLI 参数

`--suite` 模式下，下面这些参数依然可以从 CLI 传：

- `--model`
- `--eval-model`
- `--timeout`
- `--eval-timeout`
- `--save-dir`
- backend executable / runtime 参数，例如 `--claude-bin`、`--codex-bin`、`--sandbox`、`--no-full-auto`

说明：

- suite 只禁止“会和 manifest scope 冲突”的那组参数
- 它没有禁止 model、timeout、save-dir 或 backend runtime 细节

### 4. suite 内路径解析

suite 中的 `prompt_file` 与 `eval_prompt_file`：

- 绝对路径直接使用
- 相对路径按 suite 文件所在目录解析

suite 中的 `repo`：

- 先按普通 `resolve_repo()` 规则找
- 找不到时，再尝试按 suite 文件所在目录的相对路径解析

## 五、Claude 兼容壳的真实行为

`run_claude_skill_eval.py` 不是第二套 runner，它只是把旧调用转发到 `run_skill_suite.py`。

它固定做的事只有：

- 总是补上 `--backend claude`
- 只支持 `--repo`，不支持 `--suite`
- 透传 `--repo`、`--task`、`--prompt-file`、`--with-eval`、`--eval-prompt-file`、`--claude-bin`、`--model`、`--permission-mode`、`--output-format`、`--timeout`、`--eval-model`、`--eval-timeout`、`--save-dir`

它不会无条件补 `--judge-backend claude`。
只有当传了 `--with-eval` 时，它才额外补：

```bash
--judge-backend claude
```

因此当前更准确的描述是：

- `run_claude_skill_eval.py` 是兼容壳
- 它唯一的 judge-specific 行为，是在 `--with-eval` 打开时自动补 `--judge-backend claude`

示例：

```bash
python3 toolchain/scripts/research/run_claude_skill_eval.py \
  --repo typer \
  --task all \
  --with-eval \
  --save-dir /tmp/claude-skill-evals
```

## 六、当前 artifact 输出

### 1. 没有 `--save-dir`

不落盘，只打印结果。

打印内容包含：

- `repo`
- `task`
- `phase`
- `backend`
- eval 阶段时的 `judge_backend`
- `prompt_file`
- `status`
- `elapsed_seconds`
- `command`
- `final_message` 或 `raw_stdout`
- 必要时追加 `raw stdout`
- 必要时追加 `raw stderr`
- 必要时追加 `parse_error`

### 2. 传了 `--save-dir`

会先创建一个时间戳 run 目录：

```text
<save-dir>/<YYYYMMDDTHHMMSSZ>-<label>/
```

其中：

- direct repo 模式的 `label` 是 repo 名
- suite 模式的 `label` 是 suite 文件名去后缀

### 3. 每个 skill / eval 结果的文件

每个结果都会按顺序号写一组 artifact。

固定会写：

- `*.prompt.txt`
- `*.response.md`
- `*.final.txt`
- `*.raw.stdout.txt`
- `*.meta.json`

有 stderr 才写：

- `*.raw.stderr.txt`
- `*.stderr.txt`

有可归一化结构化结果才写：

- `*.structured.json`

命名规则：

- skill：`NN.<repo>.<task>.skill.<backend>.*`
- eval：`NN.<repo>.<task>.eval.<backend>-judge-<judge_backend>.*`

说明：

- `*.response.md` 保存 `final_message`，若没有则回退到 `raw_stdout`
- `*.final.txt` 只保存 `final_message`
- `*.structured.json` 来自 eval 结果的归一化结构
- 即使 parse 后发现 score 不完整，只要形成了 `structured_output`，仍会写 `*.structured.json`，同时在 `meta` / console 中保留 `parse_error`

### 4. eval schema 文件

当 eval judge backend 支持 JSON schema 时，runner 会为该 eval run 生成 schema 文件。

当前支持 JSON schema 的 backend：

- `claude`
- `codex`

传了 `--save-dir` 时，会额外落盘：

- `NN.<repo>.<task>.eval-schema.<judge_backend>.json`

这个文件不是静态拷贝，而是由 `toolchain/evals/fixtures/schemas/eval-result.schema.json` 按 task 动态展开后的结果。
其中 `scores` 字段会被收紧为该 task 的固定 score keys，`dimension_feedback` 也会被收紧为同一组维度 key，并要求输出 `what_worked / needs_improvement`。

不传 `--save-dir` 时：

- schema 仍会生成
- 但会写到临时文件
- run 结束后会被清理，不会保留为 artifact

### 5. 元数据与 summary

每个结果的 `*.meta.json` 当前包含：

- `task`
- `phase`
- `backend`
- `judge_backend`
- `repo_path`
- `prompt_file`
- `command`
- `returncode`
- `timed_out`
- `elapsed_seconds`
- `started_at`
- `finished_at`
- `schema_file`
- `parse_error`
- `artifacts`
- `structured_output`（如果存在）

整个 run 还会在 run 根目录写：

- `run-summary.json`

当前 summary 结构包含：

- `runner`
- `generated_at`
- `suite_file`
- `summary_schema`
- `results[]`

其中：

- `summary_schema` 指向 `toolchain/evals/fixtures/schemas/run-summary.schema.json`
- `results[].structured_output` 保存归一化后的结构化结果
- `results[].artifacts` 保存各落盘文件名映射

## 七、当前成功 / 失败判定

runner 只有在所有结果都成功时才返回 `0`。

当前任一结果出现下面情况都会让整体返回 `1`：

- 子进程超时
- 子进程返回码非 `0`
- eval 阶段没有拿到 `structured_output`
- eval 阶段存在 `parse_error`

这意味着：

- judge 命令本身返回 `0` 并不等于整次 eval 成功
- 结构化输出缺失或 rubric 无法解析，同样算失败

## 八、当前 backend 状态

### 1. Claude

状态：

- active backend
- 可作为 skill backend
- 可作为 eval judge backend
- 支持 JSON schema judge

当前 runner 级事实：

- 通过 Claude CLI 直接把 prompt 当作命令行参数传入
- 当 eval 传入 schema 时，runner 会强制该次 Claude judge 使用 `--output-format json`
- Claude 返回 JSON 信封时，runner 会优先取其中的 `structured_output`，否则再取 `result`

### 2. Codex

状态：

- active backend
- 可作为 skill backend
- 可作为 eval judge backend
- 支持 JSON schema judge

当前 runner 明确依赖的行为只有：

```bash
codex exec \
  --cd <repo> \
  --sandbox <mode> \
  --output-last-message <file> \
  [--full-auto] \
  [--model <model>] \
  [--output-schema <schema>] \
  -
```

当前可以写死的事实：

- prompt 通过 `stdin` 传入
- 最终消息通过 `--output-last-message` 指定的临时文件回收
- judge 场景会在支持 schema 时传 `--output-schema`
- `--full-auto` 默认开启，可用 `--no-full-auto` 关闭

当前不要写死的东西：

- `Codex` 如何自动发现 skill mount
- `Codex` CLI 在 runner 之外的更多输出语义
- 任何未在当前 backend 实现里被实际使用的参数假设

### 3. OpenCode

状态：

- 仍然出现在统一 CLI 的 backend choices 中
- 但当前 research runner 里是 `reserved but not implemented`

真实行为：

- backend registry 会尝试构建它
- 即使本机存在 `opencode` 可执行文件，healthcheck 也会返回 unavailable
- 所以当前把 `opencode` 用作 `--backend` 或 `--judge-backend` 都会在执行前失败

因此当前文档只能写：

- `OpenCode` 是预留位
- 不是当前可运行 backend
- 不应该在示例命令里把它写成 active 路径

## 九、backend acceptance matrix 的真实边界

`run_backend_acceptance_matrix.py` 当前只解决一件事：把 active 的 live acceptance lane 固定成稳定命名的 repo-local 入口。

它当前不会做的事：

- 不引入新的 runner 实现
- 不改变 `run_skill_suite.py` 的 suite 解析规则
- 不把 OpenCode 纳入 live acceptance
- 不承诺这条矩阵适合作为每次都跑的快速 CI

它当前实际做的事：

- 为给定 repo 生成一份临时 suite manifest
- 把两条 lane 固定为 `codex -> codex` 与 `claude -> codex`
- 把每条 lane 固定为 `task: all`
- 继续复用统一 runner 的 artifact、schema 和 summary 逻辑

## 十、相关文档

- [Research 评测契约与边界](../analysis/research-eval-contracts.md)
- [Research 评测观测与输出规范](../analysis/research-eval-observability.md)
- [Autoresearch 最小闭环运行说明](./autoresearch-minimal-loop.md)
- [toolchain/scripts/research/README.md](../../toolchain/scripts/research/README.md)
- [toolchain/evals/README.md](../../toolchain/evals/README.md)
- [Codex Memory Side Repo-local Adapter 部署帮助](./memory-side/codex-deployment-help.md)
- [Codex Task Interface Repo-local Adapter 部署帮助](./task-interface/codex-deployment-help.md)
