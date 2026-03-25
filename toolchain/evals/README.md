# Evals

`toolchain/evals/` 只保留已准入、可复用的 eval 资产入口，不承载临时运行结果，也不表示这里已经存在完整的评测平台。

当前布局：

- `prompts/`
- `fixtures/`
- `memory-side/`

目录说明：

- `prompts/` 当前承载 repo-local 的 eval prompt 模板，按 task 分文件保存，供 `toolchain/scripts/research/run_skill_suite.py` 在 eval 阶段读取。
- `fixtures/` 当前承载稳定的 fixture 资产，主要是 schema 参考与 suite manifest。
- `memory-side/` 当前只保留占位入口，不承载 active 的 `program / scenarios / scoring database` 一类资产。

稳定资产与运行时产物要分开理解：

- `fixtures/schemas/eval-result.schema.json` 是通用 eval 结果 contract 模板，不是 runner 直接原样交给所有 judge 的最终 schema。
- `run_skill_suite.py` 会结合 `toolchain/scripts/research/common.py` 中的 `EVAL_SCORE_DIMENSIONS`，按 task 物化出固定 score keys 的结构化 judge schema。
- 这些 task-scoped schema 属于运行时产物：未开启 `--save-dir` 时通常写到临时文件；开启 `--save-dir` 时会作为某次 run 的 artifact 保存到该次输出目录。
- `fixtures/schemas/run-summary.schema.json` 用来约束保存出的 `run-summary.json` 结构，描述一次 suite/direct run 的汇总元数据与 artifact 索引。

`fixtures/` 当前内容：

- `fixtures/schemas/`
- `eval-result.schema.json`：通用 eval 结果字段模板，约束 `skill / repo / backend / judge_backend / scores / total_score / max_score / overall / key_issues / key_strengths` 等基础字段。
- `run-summary.schema.json`：一次运行的汇总 contract，覆盖 `runner`、时间戳、`suite_file`、每条 result 的 phase、耗时、schema_file、structured_output、artifacts 等字段。
- `fixtures/suites/`
- `memory-side-skills.v1.yaml`：当前最小 suite manifest 示例，声明默认 backend / judge_backend / with_eval，并对目标 repo 运行 memory-side skills 任务集。

这里现在没有什么：

- 没有完整的 V1 `scoring program`
- 没有数据库式的历史结果系统
- 没有内置的场景仓库 checkout
- 没有应长期保存在仓库内的 run logs 或临时 benchmark 输出

这里适合放：

- 稳定、可复跑的 prompt / fixture / manifest 资产
- 被 runner 代码稳定依赖的 schema 参考
- 后续明确准入的最小测量格式

这里不适合放：

- 业务源码
- 临时运行产物
- 本地日志
- 尚未收口的整套评测体系描述
