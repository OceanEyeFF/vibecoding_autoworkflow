# Evals

`toolchain/evals/` 只保留已准入、可复用的 eval 资产入口，不承载临时运行结果，也不表示这里已经存在完整的评测平台。

当前布局：

- `prompts/`
- `fixtures/`
- `memory-side/`

目录说明：

- `prompts/` 当前承载 repo-local 的 eval prompt 模板，按 task 分文件保存，供 `autoresearch/src/run_skill_suite.py` 在 eval 阶段读取。
- `fixtures/` 当前承载稳定的 fixture 资产，主要是 schema 参考与 suite manifest。
- `memory-side/` 当前承载已准入主题的 eval 入口；它依然不等于完整的 `program / scenarios / scoring database` 平台，但也不是“未来再说”的纯占位目录。

这里还需要和 live acceptance 区分：

- deterministic fixture / schema / suite 资产可以稳定入库
- `backend acceptance matrix` 属于真实 backend 验收路径，运行入口在 `autoresearch/src/run_backend_acceptance_matrix.py`
- 它仍然会复用这里的 prompt / schema 资产，但不应被理解成 cheap CI fixture

稳定资产与运行时产物要分开理解：

- `fixtures/schemas/eval-result.schema.json` 是通用 eval 结果 contract 模板，不是 runner 直接原样交给所有 judge 的最终 schema。
- `run_skill_suite.py` 会结合 `autoresearch/src/common.py` 中的 `EVAL_SCORE_DIMENSIONS`，按 task 物化出固定 score keys 的结构化 judge schema。
- 除了 `scores` 之外，task-scoped schema 还会固定 `dimension_feedback` 的维度 key，用来记录每个评分维度“做得好的点”和“需要改进的点”。
- 这些 task-scoped schema 属于运行时产物：未开启 `--save-dir` 时通常写到临时文件；开启 `--save-dir` 时会作为某次 run 的 artifact 保存到该次输出目录。
- `fixtures/schemas/run-summary.schema.json` 用来约束保存出的 `run-summary.json` 结构，描述一次 suite/direct run 的汇总元数据与 artifact 索引。

`fixtures/` 当前内容：

- `fixtures/schemas/`
- `eval-result.schema.json`：通用 eval 结果字段模板，约束 `skill / repo / backend / judge_backend / scores / dimension_feedback / total_score / max_score / overall / key_issues / key_strengths` 等基础字段。
- `run-summary.schema.json`：一次运行的汇总 contract，覆盖 `runner`、时间戳、`suite_file`、每条 result 的 phase、耗时、schema_file、structured_output、artifacts 等字段。
- `fixtures/suites/`
- `memory-side-skills.v1.yaml`：当前最小 suite manifest 示例，声明默认 backend / judge_backend / with_eval，并对目标 repo 运行 memory-side skills 任务集。

这里现在没有什么：

- 没有完整的 V1 `scoring program`
- 没有数据库式的历史结果系统
- 没有内置的场景仓库 checkout
- 没有应长期保存在仓库内的 run logs 或临时 benchmark 输出
- 没有把 live acceptance matrix 固定成默认每次都跑的快速回归

这里适合放：

- 稳定、可复跑的 prompt / fixture / manifest 资产
- 被 runner 代码稳定依赖的 schema 参考
- 后续明确准入的最小测量格式

这里不适合放：

- 业务源码
- 临时运行产物
- 本地日志
- 尚未收口的整套评测体系描述
