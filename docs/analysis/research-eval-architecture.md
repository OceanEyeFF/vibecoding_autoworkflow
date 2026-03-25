---
title: "Research 评测架构"
status: active
updated: 2026-03-25
owner: aw-kernel
last_verified: 2026-03-25
---
# Research 评测架构

> 目的：基于当前已经跑通的 `Claude skills + eval skills` 闭环，固定一个最小可扩展的 research / eval 架构，供后续接入 `Codex` 和预留 `OpenCode` 使用。

## 一、当前已验证的闭环

当前仓库已经验证通过的最小闭环只有一条：

1. 对 `.exrepos/<repo>` 里的目标仓库运行 repo-local skill prompt
2. 捕获 skill 最终输出
3. 把 skill 输出注入 eval rubric prompt 中的 `{{TEST_OUTPUT}}`
4. 再次调用后端 CLI，产出评测结果
5. 可选把 prompt / response / meta / summary 落到外部目录

当前已验证的 active 实现：

- `toolchain/scripts/research/run_claude_skill_eval.py`
- `toolchain/scripts/research/tasks/`
- `toolchain/evals/prompts/`

说明：

- 当前 `run_claude_skill_eval.py` 是已验证基线
- 下一步不应再平行新增 `Codex` 专用 runner，而应把它抽成多 backend 通用执行器，并把当前脚本保留为兼容壳

当前已验证的 active backend：

- `Claude`

当前已知但尚未接入的 backend：

- `Codex`
- `OpenCode`

## 二、当前架构边界

### 1. `toolchain/scripts/research/`

职责：

- 承载执行型 runner
- 负责把 prompt 送进某个 CLI
- 负责捕获结果与保存元数据

不负责：

- 保存长期评测资产
- 定义评分规则正文
- 保存运行产物

### 2. `toolchain/evals/`

职责：

- 承载稳定的评测 prompt、fixture、schema 和 suite 描述

当前 active 内容：

- `toolchain/evals/prompts/`

不负责：

- 业务源码
- repo-local mount
- 临时日志
- 本地运行缓存

### 3. `product/*/adapters/`

职责：

- 提供各 backend 的 repo-local skill adapter 源码

当前已存在：

- `product/memory-side/adapters/claude/`
- `product/memory-side/adapters/agents/`
- `product/task-interface/adapters/claude/`
- `product/task-interface/adapters/agents/`

说明：

- `.claude/skills/` 与 `.agents/skills/` 是 deploy target，不是架构真相层

## 三、从当前闭环吸收出的约束

### 1. backend 执行与 judge 执行必须解耦

当前闭环虽然是 `Claude -> Claude judge`，但后续必须允许：

- `backend=codex, judge=claude`
- `backend=opencode, judge=claude`
- `backend=codex, judge=codex`

原因：

- 执行后端与评测后端不一定相同
- 本地某个 backend 可能暂时不可用，但 judge 仍可运行

### 2. non-interactive prompt 必须显式约束

当前已经验证出几个必要条件：

- 明确指定 repo-local skill
- 明确要求单轮直接输出
- 明确禁止追问
- 信息不足时要求降级输出，而不是扩扫或继续追问

### 3. eval prompt 必须有统一插槽

当前统一使用：

- `{{TEST_OUTPUT}}`

后续任何评测 prompt 都应保持同一占位符，避免 runner 为不同模板写特判。

### 4. 运行产物不能写回 `toolchain/`

当前已经验证的合理做法是：

- 显式传 `--save-dir`
- 把结果写到外部目录，例如 `/tmp/...`

后续如果要沉淀到 repo-local state，也应落到状态层，而不是 `toolchain/` 本体。

### 5. 评分结果不应长期依赖自然语言抓分

这轮研究已经能工作，但仍然依赖从自然语言里抓：

- `Total Score`
- `Overall Feeling`

这只适合研究期。

后续准入方向应是：

- judge 输出结构化 JSON
- `toolchain/evals/fixtures/schemas/` 提供 schema
- runner 直接汇总结构化结果

## 四、建议的最小扩展形态

下一阶段不要再按 backend 复制 runner，也不要新增一个 `Codex` 专用平行脚本，而是把当前 runner 抽象成统一外壳，并保留 `run_claude_skill_eval.py` 作为兼容入口。

建议形态：

```text
toolchain/scripts/research/
  run_skill_suite.py
  run_claude_skill_eval.py
  backends/
    base.py
    claude.py
    codex.py
    opencode.py
  prompts/
    templates/
toolchain/evals/
  prompts/
  fixtures/
    schemas/
      eval-result.schema.json
      run-summary.schema.json
    suites/
      memory-side-skills.v1.yaml
```

其中：

- `run_skill_suite.py`：统一编排
- `run_claude_skill_eval.py`：兼容壳，内部应委托统一 runner
- `backends/base.py`：backend contract
- `claude.py`：当前已验证 backend
- `codex.py`：下一步优先接入
- `opencode.py`：先保留 stub
- `prompts/templates/`：放 backend-neutral 的 scenario body 或包装模板
- `toolchain/evals/fixtures/schemas/`：放结构化评测结果与运行汇总 schema
- `toolchain/evals/fixtures/suites/`：放 repo / task / backend / judge 的 suite 清单

## 五、backend contract 的最小字段

后续 backend adapter 最少需要统一这几类能力：

- `backend_id`
- `healthcheck()`
- `skill_mount_path`
- `build_skill_command(...)`
- `build_eval_command(...)`
- `extract_final_message(...)`
- `supports_stdin_prompt`
- `supports_output_file`
- `supports_json_schema`

目的不是做复杂抽象，而是把三个 backend 的差异收敛到命令构造层。

## 六、运行记录与评测结果约束

这轮研究已经暴露出两个需要尽快固定的基础约束：

- `elapsed_seconds` 不应继续用 wall-clock 差值，后续应改为 `time.perf_counter()`
- runner 应显式区分 `raw stdout/stderr` 与 `final message`

原因：

- Claude 输出可能混入 chatter
- Codex 更适合走 `stdin prompt + output file final message`
- 如果不拆开原始输出与最终回答，后续多 backend 汇总会变脆

结构化评测结果也应尽快固定为 schema，而不是继续从自然语言里抓：

```json
{
  "skill": "context-routing",
  "repo": "typer",
  "backend": "codex",
  "judge_backend": "claude",
  "scores": {
    "path_contraction": 3,
    "entry_point_identification": 2,
    "avoidance_of_over_scanning": 3,
    "execution_usability": 2
  },
  "total_score": 10,
  "max_score": 12,
  "overall": "Okay",
  "key_issues": ["..."],
  "key_strengths": ["..."]
}
```

最小结论：

- Claude judge 后续应优先输出受 schema 约束的 JSON
- Codex judge 后续可优先走 `--output-schema`
- OpenCode 若暂时不支持 schema，再退回 text + parser

## 七、当前已知 backend 状态

### `Claude`

当前状态：

- 本机可用
- 已验证 `-p/--print` 非交互调用
- 已验证 skill + eval 双阶段运行

### `Codex`

当前状态：

- 本机 `codex` CLI 可用
- 已知非交互入口是 `codex exec`

当前已知能力：

- `--cd`
- `--sandbox`
- `--full-auto`
- `--output-last-message`
- `--json`
- `--output-schema`

结论：

- 可以作为下一步优先接入的 backend
- 推荐优先走 `stdin` 喂 prompt，并通过单独 final message 通道抓最终回答

### `OpenCode`

当前状态：

- 本机存在 `opencode` 命令入口
- 当前安装状态异常，help 未正常工作

结论：

- 现在只适合预留 adapter contract
- 不应在本轮文档中假定其稳定参数形状

## 八、推荐的准入顺序

1. 保留当前 `Claude` runner 作为已验证基线
2. 抽出统一 runner 外壳，并把 `run_claude_skill_eval.py` 降为兼容壳
3. 接入 `Codex` backend
4. 把 eval 输出升级为结构化 schema
5. 再接 `OpenCode`

## 九、非目标

当前这套 research / eval 架构明确不做下面这些事：

- 不做 benchmark 平台
- 不做长期结果数据库
- 不把运行结果入库到 `toolchain/`
- 不把 backend-specific mount 当成真相层
- 不先扩成多 agent 编排系统

## 十、相关文档

- [Toolchain 分层](../knowledge/foundations/toolchain-layering.md)
- [toolchain/evals/README.md](../../toolchain/evals/README.md)
- [toolchain/scripts/research/README.md](../../toolchain/scripts/research/README.md)
- [Codex Memory Side Repo-local Adapter 部署帮助](../operations/memory-side/codex-deployment-help.md)
- [Codex Task Interface Repo-local Adapter 部署帮助](../operations/task-interface/codex-deployment-help.md)
