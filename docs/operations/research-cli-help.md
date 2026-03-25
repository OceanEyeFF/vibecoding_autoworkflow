---
title: "Research CLI 指令"
status: active
updated: 2026-03-25
owner: aw-kernel
last_verified: 2026-03-25
---
# Research CLI 指令

> 目的：给当前仓库的 research runner 一个 repo-local 使用说明，并固定后续 `Codex` / `OpenCode` runner 的 CLI 形状约束。

## 一、当前 active CLI

当前已经可运行的 research CLI 只有：

```bash
python3 toolchain/scripts/research/run_claude_skill_eval.py
```

它当前负责两类动作：

1. 运行 skill prompt
2. 可选运行 eval rubric prompt

演进约束：

- 不应再平行新增 `run_codex_skill_eval.py` 之类的 backend-specific 脚本
- 后续应新增通用入口 `run_skill_suite.py`
- 当前 `run_claude_skill_eval.py` 应保留为兼容壳，而不是继续长成第二套主实现

## 二、当前 active 用法

### 1. 单 skill

```bash
python3 toolchain/scripts/research/run_claude_skill_eval.py \
  --repo typer \
  --task context-routing
```

### 2. skill + eval

```bash
python3 toolchain/scripts/research/run_claude_skill_eval.py \
  --repo typer \
  --task context-routing \
  --with-eval \
  --save-dir /tmp/claude-skill-evals
```

### 3. 全量 task

```bash
python3 toolchain/scripts/research/run_claude_skill_eval.py \
  --repo typer \
  --task all \
  --with-eval \
  --save-dir /tmp/claude-skill-evals
```

## 三、当前参数语义

### 必填

- `--repo`

说明：

- 可以传 `.exrepos/<name>` 下的仓库名
- 也可以传显式路径

### 选择 task

- `--task context-routing`
- `--task knowledge-base`
- `--task task-contract`
- `--task writeback-cleanup`
- `--task all`

### prompt 覆盖

- `--prompt-file`
- `--eval-prompt-file`

约束：

- 只有单 task 时才允许覆盖单个 prompt

### eval 开关

- `--with-eval`

说明：

- 不传时只跑 skill
- 传入后会把 skill 输出注入 `toolchain/evals/prompts/` 里的 rubric

### 输出控制

- `--save-dir`

说明：

- 不传时只打印
- 传入后会保存 `prompt / response / meta / summary`

## 四、当前输出约定

如果显式传了 `--save-dir`，当前会保存：

- `*.prompt.txt`
- `*.response.md`
- `*.stderr.txt`（有 stderr 才写）
- `*.meta.json`
- `run-summary.json`

当前 `eval` 阶段会额外保存：

- `*.eval.prompt.txt`
- `*.eval.response.md`
- `*.eval.meta.json`

后续如果进入多 backend 通用 runner，建议新增并固定：

- `*.final.txt`：最终回答
- `*.raw.stdout.txt`：原始 stdout
- `*.raw.stderr.txt`：原始 stderr

补充约束：

- `elapsed_seconds` 后续应改为基于 `time.perf_counter()` 计算
- 不应继续把最终回答与原始命令输出混成一个抓取通道

## 五、后续统一 CLI 形状

后续如果从 `Claude-only` runner 演进为多 backend runner，建议统一成下面这组参数，而不是每个 backend 自己发明一套：

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --backend claude \
  --judge-backend claude \
  --repo typer \
  --task all \
  --with-eval \
  --save-dir /tmp/skill-evals
```

例如：

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --backend codex \
  --judge-backend claude \
  --repo typer \
  --task all \
  --with-eval \
  --save-dir /tmp/skill-evals
```

最小参数集合建议固定为：

- `--backend`
- `--judge-backend`
- `--repo`
- `--task`
- `--with-eval`
- `--prompt-file`
- `--eval-prompt-file`
- `--timeout`
- `--eval-timeout`
- `--save-dir`

说明：

- `run_claude_skill_eval.py` 后续应转成对 `run_skill_suite.py` 的兼容封装
- 不建议继续为 `Codex` 单独复制一份 CLI

## 六、Codex runner 的指令约束

基于当前本机 `codex exec --help` 可确认的信息，后续 `Codex` backend 应优先走：

```bash
codex exec \
  --cd <repo> \
  --sandbox workspace-write \
  --full-auto \
  --output-last-message <file> \
  -
```

当前可以写死的事实：

- 非交互入口是 `codex exec`
- 可以通过 `stdin` 传 prompt
- 可以通过 `--output-last-message` 抓最终回答
- 可以通过 `--output-schema` 约束结构化输出

推荐原因：

- 比直接抓 stdout 更适合区分 `final message` 与 `raw stdout/stderr`
- 可以降低 chatter 混入最终评测输入的概率

当前不要在 CLI 文档里写死的东西：

- skill 自动发现是否一定等价于 `.agents/skills/`
- `Codex` 对 eval judge 的最终 prompt 拼接细节
- 任何未经本机 runner 验证过的 `Codex` 输出格式假设

## 七、OpenCode runner 的指令约束

当前只记录一条边界：

- 需要保留 `OpenCode` backend 位置
- 但本机 `opencode` 当前不可作为 active backend 文档化

因此当前 CLI 文档只允许写：

- `OpenCode` 预留支持位
- 不写死命令参数
- 不把它写成当前可跑能力

## 八、当前推荐工作流

### 1. 研究 prompt 调整

先改：

- `toolchain/scripts/research/tasks/`

### 2. 评测 prompt 调整

再改：

- `toolchain/evals/prompts/`

### 3. 运行整套验证

最后跑：

```bash
python3 toolchain/scripts/research/run_claude_skill_eval.py \
  --repo <repo> \
  --task all \
  --with-eval \
  --save-dir /tmp/claude-skill-evals
```

## 九、非目标

本页不是：

- benchmark 结论文档
- backend 抽象设计全文
- 运行结果存档位置说明
- suite manifest 设计全文

本页只负责：

- 当前 active CLI 用法
- 下一步 `Codex` / `OpenCode` runner 的命令行约束

## 十、相关文档

- [Research 评测契约与边界](../analysis/research-eval-contracts.md)
- [Research 评测观测与输出规范](../analysis/research-eval-observability.md)
- [toolchain/scripts/research/README.md](../../toolchain/scripts/research/README.md)
- [toolchain/evals/README.md](../../toolchain/evals/README.md)
- [Codex Memory Side Repo-local Adapter 部署帮助](./memory-side/codex-deployment-help.md)
- [Codex Task Interface Repo-local Adapter 部署帮助](./task-interface/codex-deployment-help.md)
