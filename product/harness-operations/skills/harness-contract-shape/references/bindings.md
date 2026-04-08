# Harness Contract Shape Bindings

## Required

- `${SCOPE_INCLUDE}`：宿主仓库允许修改的路径前缀或路径列表。
- `${SCOPE_EXCLUDE}`：宿主仓库禁止修改的路径前缀或路径列表。
- `${GATE_SEQUENCE}`：宿主仓库定义的 gate 顺序。
- `${GOVERNANCE_DIMENSIONS}`：宿主仓库治理收口维度列表。

## Runtime Placeholders

- `${WORKFLOW_ID}`：当前 harness workflow 标识。
- `${TASK_SOURCE_REF}`：当前 workflow 的来源对象，例如 commit、PR、task file。
