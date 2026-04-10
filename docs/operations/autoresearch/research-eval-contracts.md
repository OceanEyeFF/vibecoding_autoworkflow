---
title: "Research 评测契约与边界"
status: active
updated: 2026-04-11
owner: aw-kernel
last_verified: 2026-04-11
---
# Research 评测契约与边界

> 目的：基于当前代码基线，固定 Research/Eval 的最小执行契约、backend 边界、suite 口径与结构化 judge 行为；这里是 research boundary 文档，不是运行日志。

## 一、当前主实现与闭环口径

当前 active 入口已经不是单一的 Claude-only runner，而是：

- `toolchain/scripts/research/run_skill_suite.py`
- `toolchain/scripts/research/run_claude_skill_eval.py`
- `toolchain/scripts/research/backends/`
- `toolchain/evals/prompts/`
- `toolchain/evals/fixtures/`

其中：

- `run_skill_suite.py` 是统一主实现
- `run_claude_skill_eval.py` 只是兼容壳，内部委托统一 runner
- 闭环形态是 `skill backend -> optional judge backend`
- `skill` 与 `eval` 都走同一套 backend registry / invocation contract
- 是否落盘由 `--save-dir` 显式决定，运行产物不回写到 `toolchain/`

当前最小闭环仍然是两阶段：

1. 对目标仓库执行 repo-local skill prompt
2. 捕获 final message / raw stdout
3. 把 skill 输出注入 eval prompt 的 `{{TEST_OUTPUT}}`
4. 可选再调用 judge backend 产出结构化或可解析的 eval 结果
5. 可选把 prompt / response / meta / summary 写到外部运行目录

## 二、验证口径：默认 suite 覆盖 vs live acceptance matrix

当前需要明确区分两类“已验证”：

- 默认 suite 覆盖：`toolchain/evals/fixtures/suites/memory-side-skills.v1.yaml` 当前默认是 `backend=claude`、`judge_backend=claude`、`with_eval=true`
- 运行样例证据：`/tmp/research-run-suite/20260325T155954Z-memory-side-skills-v1/run-summary.json` 体现的是这条默认 suite 路径，而不是全部 backend/judge 组合
- live acceptance matrix：`toolchain/scripts/research/run_backend_acceptance_matrix.py` 固定跑 `codex -> codex` 与 `claude -> codex`，并对四个 skills 全量执行 `task: all`

因此，当前正确表述应是：

- 固化在 checked-in suite 资产里的默认覆盖仍然是 `claude -> claude`
- 但研究 runner 的 active 验证口径不应被缩写成“只验证了 Claude -> Claude”
- `backend acceptance matrix` 是单独的 live acceptance 入口，不应冒充默认 suite，也不应被降格理解成 deterministic unit/regression
- 这条矩阵依赖真实 backend，有成本与波动，不应被文档写成默认快速 CI

## 三、当前 backend 状态

当前 backend registry 暴露三个 id：

- `claude`
- `codex`
- `opencode`

当前 active 状态是：

- `claude`：active backend
- `codex`：active backend
- `opencode`：active MVP backend；可跑 skill/eval，但当前不宣称 schema judge 支持，也没有被纳入 live acceptance matrix

当前准确边界：

- 三个 backend 都会通过 `build_backend()` 进入统一 runner
- `opencode` 当前只承诺 MVP CLI 透传与 final-message 提取，不承诺 live acceptance 或 schema judge

## 四、统一 runner 与 backend contract

`run_skill_suite.py` 当前统一承担：

- `--repo` 直跑模式
- `--suite` manifest 模式
- `skill backend` 与 `judge backend` 的拆分
- run dir 初始化、过程输出、artifact 落盘与 `run-summary.json` 汇总

backend contract 的最小形状在 `backends/base.py`，不是按 backend 复制 runner：

- `backend_id`
- `skill_mount_path`
- `healthcheck()`
- `build_skill_command(...)`
- `build_eval_command(...)`
- `extract_final_message(...)`
- `supports_stdin_prompt`
- `supports_output_file`
- `supports_json_schema`

每次调用都落在统一的 `BackendInvocation` 上：

- `command`
- `stdin_text`
- `final_message_path`
- `cleanup_paths`

这层抽象的目的只是收敛 CLI 差异，不是引入新的 orchestrator 层。

## 五、当前 backend 差异

当前代码中的差异已经收敛到 backend adapter：

- `Claude`：prompt 直接拼进命令；schema-backed eval 时改走 `--output-format json`，并把 schema 文本通过 `--json-schema` 传入
- `Codex`：走 `codex exec`；prompt 通过 stdin 输入；final message 通过 `--output-last-message` 文件回收；schema-backed eval 时通过 `--output-schema <path>` 传入
- `OpenCode`：MVP 走 `opencode run`，透传 `model / --dir`，并把统一 output format 归一化到 OpenCode 的 `default/json`；runner 会同时把 subprocess `cwd` 设为 repo 根并显式传 `--dir <repo>`，这是基于当前本地 CLI 帮助页确认后的有意实现；`extract_final_message()` 会从 JSONL `text` 事件和 message-style stdout 中提取最后一个 assistant message，schema judge 仍不支持

因此当前 policy 是：

- 允许 `skill backend != judge backend`
- 不再新增 `run_codex_*` 一类 backend-specific 平行脚本
- `OpenCode` judge 当前继续依赖文本解析回退，不把 schema judge 写成已实现事实

## 六、结构化 judge schema 的当前口径

`toolchain/evals/fixtures/schemas/eval-result.schema.json` 当前是通用参考 schema，不是直接下发给 judge 的最终 task schema。

runner 当前行为是：

- 以通用参考 schema 为底
- 结合 `common.py` 里的 `EVAL_SCORE_DIMENSIONS`
- 按 task 物化出固定 score keys 的 task-scoped schema
- 仅在 judge backend 声明 `supports_json_schema=True` 时，为该次 eval 准备 schema 文件

这意味着：

- 结构化 judge 的 contract 已经是“task-scoped materialized schema”
- 不是“所有任务共用一个静态 eval schema 原样下发”
- `run-summary.json` 与单条 `meta.json` 里的 `schema_file` 指向的是本轮物化出的 schema 工件

## 七、eval 输出归一化口径

当前 eval 路径不是只接受一种输出形态：

- 优先解析 JSON object
- 若 judge 没有给出可用 JSON，再回退到 rubric-text parser
- 最终统一归一化为 `skill / repo / backend / judge_backend / scores / dimension_feedback / total_score / max_score / overall / key_issues / key_strengths / source_format`

但在结构化 judge 路径下，runner 的目标仍然是：

- 通过 task-scoped schema 约束 JSON
- 让 `structured_output` 成为 eval 成功的主路径
- 把 text parser 视为兼容退路，而不是默认 contract

## 八、目录与真相边界

### `toolchain/scripts/research/`

负责：

- 执行 runner
- backend 调用
- 结果采集与临时 artifact 落盘

不负责：

- 长期评测资产沉淀
- 评测真相层定义
- 仓库级知识回写

### `toolchain/evals/`

负责：

- 稳定 prompt
- fixture schema 参考
- suite manifest

不负责：

- 运行日志
- 临时结果目录
- backend deploy mount

### `product/*/adapters/`

负责：

- canonical repo-local adapter 源码

说明：

- `.claude/skills/`、`.agents/skills/` 与 `.opencode/skills/` 仍然只是 deploy target，不是源码真相层

## 九、非交互 prompt 约束

当前已经验证出几个必要条件：

- 明确指定 repo-local skill
- 明确要求单轮直接输出
- 明确禁止追问
- 信息不足时要求降级输出，而不是扩扫或继续追问

## 十、评测 prompt 占位符约束

当前统一使用：

- `{{TEST_OUTPUT}}`

后续任何评测 prompt 都应保持同一占位符，避免 runner 为不同模板写特判。

## 十一、非目标

当前这套 research / eval 架构明确不做下面这些事：

- 不做 benchmark 平台
- 不做长期结果数据库
- 不把运行结果入库到 `toolchain/`
- 不把 backend-specific mount 当成真相层
- 不先扩成多 agent 编排系统

## 十二、相关文档

- [Research 评测观测与输出规范](./research-eval-observability.md)
- [Research CLI 指令](./research-cli-help.md)
- [Toolchain 分层](../../../toolchain/toolchain-layering.md)
- [toolchain/evals/README.md](../../../toolchain/evals/README.md)
- [toolchain/scripts/research/README.md](../../../toolchain/scripts/research/README.md)
- [Codex Memory Side Repo-local Adapter 部署帮助](../memory-side/codex-deployment-help.md)
- [Codex Task Interface Repo-local Adapter 部署帮助](../task-interface/codex-deployment-help.md)
