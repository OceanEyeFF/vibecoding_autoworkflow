# Strict Workflow Bindings

本对象默认不要求 repo-specific harness bindings。

## Optional

- `${GATE_SEQUENCE}`：如果宿主仓库需要显式命名 gate 顺序，可注入统一 gate 列表。

## Runtime Placeholders

- `${TASK_SOURCE_REF}`：当前任务来源文档或文件路径。
