# Task List Workflow Bindings

## Required

- `${HARNESS_STATE_FILE}`：当前 task-list workflow 的 harness 状态文件。
- `${HARNESS_CONTRACT_FILE}`：当前 task-list workflow 的 contract 文件。
- `${SCOPE_GATE_CMD}`：当前仓库的 scope gate 命令。
- `${BACKFILL_CMD}`：当前仓库的 gate backfill 命令。
- `${GOVERNANCE_DIMENSIONS}`：当前仓库治理收口维度列表，默认应覆盖 `rule / folders / document / code`。

## Optional

- `${GATE_SEQUENCE}`：如果宿主仓库需要显式回报 gate 顺序，可注入统一 gate 列表。
- `${SCOPE_INCLUDE}`：宿主仓库附加允许修改的路径前缀。
- `${SCOPE_EXCLUDE}`：宿主仓库明确排除的路径前缀。

## Runtime Placeholders

- `${WORKFLOW_ID}`：当前 task-list workflow 的 workflow 标识。
- `${TASK_SOURCE_REF}`：当前任务文件路径。
