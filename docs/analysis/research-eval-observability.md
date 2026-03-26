---
title: "Research 评测观测与输出规范"
status: active
updated: 2026-03-26
owner: aw-kernel
last_verified: 2026-03-26
---
# Research 评测观测与输出规范

> 目的：固定 Research/Eval 的输出边界、运行记录口径与评分结果 contract，确保多 backend 下的结果可保存、可复盘、可汇总。

## 一、落盘产物与观测边界

`toolchain/scripts/research/run_skill_suite.py` 在传入 `--save-dir` 时，会创建时间戳命名的 run 目录，并为每个 task phase 写出一组稳定产物：

- `*.prompt.txt`：实际发送给 backend 的 prompt。
- `*.response.md`：供人工快速查看的展示产物，内容为 `final_message`，若提取不到则退回 `raw_stdout`。
- `*.final.txt`：仅保存 runner 提取出的最终回答；允许为空字符串。
- `*.raw.stdout.txt`：子进程 stdout 原始捕获结果，不做归一化改写。
- `*.raw.stderr.txt`：子进程 stderr 原始捕获结果，仅在 stderr 非空时生成。
- `*.stderr.txt`：与 `raw.stderr` 内容相同的 legacy 别名，仅为兼容保留。
- `*.meta.json`：单条运行记录，包含命令、计时字段、解析状态、schema 路径与 artifact 索引。
- `*.structured.json`：仅当 runner 为该 eval 生成了非空 `structured_output` 时生成；其中可能来自 JSON 主路径，也可能来自文本 rubric 回退解析后的归一化结果。
- `run-summary.json`：整个 run 的聚合摘要，schema 指向 `toolchain/evals/fixtures/schemas/run-summary.schema.json`。

如果当前 phase 是 eval，且 schema 文件写入在 run 目录内，还会额外出现：

- `*.eval-schema.<judge>.json`：本次 eval 实际使用的 task-scoped schema。

## 二、`raw stdout/stderr` 与 `final message` 的分离

当前实现不是把“最终回答”直接等同于 stdout，而是显式维护三条观测通道：

- `raw_stdout`：`subprocess.run(..., capture_output=True)` 捕获到的 stdout 原文。
- `raw_stderr`：同一调用捕获到的 stderr 原文。
- `final_message`：由 backend-specific 提取逻辑得到的“最终可用回答”。

这个分离是当前 output contract 的核心，因为不同 backend 的“最终回答载体”并不一致：

- Claude backend:
  - skill/eval 都从 stdout 取值。
  - 若 stdout 可解析为 JSON object，优先取其中 `structured_output`，否则取 `result`。
  - 若两者都不存在，再退回 `stdout.strip()`。
- Codex backend:
  - runner 使用 `--output-last-message <tmpfile>`。
  - `final_message` 优先读取该临时文件内容。
  - 若文件不存在或未写入，再退回 `stdout.strip()`。

当前不把 `OpenCode` 纳入这套 observability contract：

- `OpenCode` 在 research runner 中仍是 reserved backend
- 因此当前没有正式的 OpenCode `final_message`、stdout 或 stderr 观测口径

因此：

- `response.md` 是“便于阅读的最终展示结果”，不是原始 stdout transcript。
- `final.txt` 是 backend 提取后的最终回答快照。
- `raw.stdout.txt` / `raw.stderr.txt` 才是诊断 backend CLI 行为时应看的原始信号。

CLI 打印行为也遵循同一规则：先显示 `final_message or raw_stdout`，仅当 `raw_stdout` 与 `final_message` 不同，才额外打印 `--- raw stdout ---` 区块。

## 三、计时字段口径

当前实现同时记录 wall-clock 时间戳和 monotonic duration，但两者语义不同：

- `started_at` / `finished_at`
  - 来自 `datetime.now(timezone.utc).isoformat()`。
  - 表示 UTC wall-clock 时间点。
  - 适合跨 run 对齐、排序与外部日志关联。
- `elapsed_seconds`
  - 来自 `time.perf_counter()` 的差值。
  - 表示单次 phase 的 monotonic duration。
  - 不承诺与 `finished_at - started_at` 的 wall-clock 差值逐字相等。

这意味着文档和下游消费者不应把 `elapsed_seconds` 当成由时间戳反推出来的字段；它是独立测量值。即使 timeout 发生，runner 仍会写出：

- `started_at`
- `finished_at`
- `elapsed_seconds`
- `timed_out: true`
- `returncode: null`

## 四、结构化 eval 的当前行为

当前 runner 的主路径是：

- judge backend 若 `supports_json_schema = true`，则走结构化 eval。
- 结构化 eval 失败时，runner 仍会尝试从文本 rubric 中回退解析。

就当前代码基线而言：

- Claude judge：`supports_json_schema = true`
- Codex judge：`supports_json_schema = true`

因此 Claude 和 Codex 都已经进入结构化 eval 主路径，只是 transport 方式不同。

### Claude judge

- `run_skill_suite.py` 会先生成 schema 文件。
- Claude eval 调用时把 `--output-format` 强制切到 `json`。
- 同时通过 `--json-schema <schema_text>` 把 schema 文本直接内联传入 CLI。
- `final_message` 从 stdout JSON payload 中提取。

### Codex judge

- `run_skill_suite.py` 同样会先生成 schema 文件。
- Codex eval 调用时通过 `--output-schema <schema_path>` 传入 schema 路径。
- prompt 通过 stdin 传给 `codex exec -`。
- `final_message` 优先从 `--output-last-message` 指向的临时文件读取，而不是直接依赖 stdout。

### 解析与归一化

无论 judge 是 Claude 还是 Codex，runner 都执行同一套解析逻辑：

1. 先对 `final_message or raw_stdout` 尝试 `parse_json_object()`。
2. 若成功，交给 `normalize_eval_payload()` 按 task 维度白名单归一化。
3. 若 JSON 解析失败，再尝试 `parse_rubric_text()`。
4. 若仍没有识别到任何 score，保留归一化 payload，并写入 `parse_error`。

`result.structured_output` 与 `run-summary.json` 中的 `structured_output` 保存的是 runner 归一化后的结果，不要求与 judge 原始输出逐字一致；其 `source_format` 会标记本次结果来自 `json` 还是 `rubric-text`。

## 五、`eval-result.schema.json` 的角色

`toolchain/evals/fixtures/schemas/eval-result.schema.json` 当前是一个 reference contract，不是每个 task 直接拿去执行的最终 schema。

它提供的是共用外壳：

- 顶层字段集合
- 基础类型约束
- `overall` / `key_issues` / `key_strengths` 等通用字段定义
- `dimension_feedback` 这类按维度解释“做得好/需改进”的共享字段外形

真正喂给 judge backend 的 schema 由 runner 在运行时 materialize：

- `common.py` 读取 `eval-result.schema.json`
- 按 task 对应的 `EVAL_SCORE_DIMENSIONS` 重写 `scores.properties` 与 `dimension_feedback.properties`
- 把 `scores.required` 固定为该 task 的精确维度 key 集
- 把 `source_format` 收紧为 `enum: ["json"]`
- 最终写成 task-scoped schema 文件，再交给 Claude/Codex judge

因此：

- fixture schema 是共享模板和参考 contract。
- run 期间产生的 `*.eval-schema.<judge>.json` 才是该 task 真实执行时的约束版本。

## 六、`run-summary.json` 的准确理解

`run-summary.json` 受 `toolchain/evals/fixtures/schemas/run-summary.schema.json` 约束，当前重点字段含义如下：

- `runner`：固定为 `run_skill_suite.py`
- `generated_at`：summary 写出时的 UTC 时间
- `suite_file`：suite 模式下的 manifest 路径；非 suite run 可为 `null`
- `summary_schema`：run-summary schema 的路径
- `results[].schema_file`：该 phase 使用的 schema 路径；非 eval 或无 schema 时为 `null`
- `results[].structured_output`：归一化后的 eval 结构化结果；skill phase 为 `null`
- `results[].artifacts`：run 目录下 artifact 文件名映射，不是绝对路径

结合 `/tmp/research-run-suite/20260325T155954Z-memory-side-skills-v1/run-summary.json` 可以看到，Claude skill phase 没有 `schema_file` 和 `structured_output`，而 Claude eval phase 同时记录：

- `schema_file`
- `structured_output`
- `artifacts.schema`
- `artifacts.structured_output`

这正是当前 runner 对 observability 和输出 contract 的基线行为。

## 七、相关文档

- [Research 评测契约与边界](./research-eval-contracts.md)
- [Research CLI 指令](../operations/research-cli-help.md)
- [toolchain/evals/README.md](../../toolchain/evals/README.md)
- [toolchain/scripts/research/README.md](../../toolchain/scripts/research/README.md)
