---
title: "Worktrack Contract"
status: active
updated: 2026-04-20
owner: aw-kernel
last_verified: 2026-04-20
---
# Worktrack Contract

定义单个 `Worktrack` 的局部状态转移合同。

最少应包含：

- `Node Type`（从 Goal Charter 的 Engineering Node Map 绑定）
  - `type`
  - `source_from_goal_charter`
  - `baseline_form`
  - `merge_required`
  - `gate_criteria`
  - `if_interrupted_strategy`
- 任务目标
- 工作范围
- 非目标
- 影响模块
- 计划中的 next state
- 验收条件
- 约束条件
- 验证要求
- 回滚条件
