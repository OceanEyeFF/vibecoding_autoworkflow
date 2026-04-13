# Review Loop Workflow Bindings

## Required

- `${HARNESS_STATE_FILE}`：当前 review-loop 的 harness 状态文件。
- `${HARNESS_CONTRACT_FILE}`：当前 review-loop 的 contract 文件。
- `${SCOPE_GATE_CMD}`：当前仓库的 scope gate 命令。
- `${BACKFILL_CMD}`：当前仓库的 gate backfill 命令。
- `${GOVERNANCE_DIMENSIONS}`：当前仓库治理收口维度列表，默认应覆盖 `rule / folders / document / code`。

## Optional

- `${GATE_SEQUENCE}`：如果宿主仓库需要显式回报 gate 顺序，可注入统一 gate 列表。

## Runtime Placeholders

- `${WORKFLOW_ID}`：当前 review-loop 的 workflow 标识。
- `${TASK_SOURCE_REF}`：commit / PR / diff range / target path；它是当前 workflow 的来源锚点。
- 若宿主同时提供显式输入与 `runtime.task_source_ref`，显式输入优先。
