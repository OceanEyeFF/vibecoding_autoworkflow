---
title: "Worktrack Contract"
status: active
updated: 2026-04-27
owner: aw-kernel
last_verified: 2026-04-27
---
# Worktrack Contract

定义单个 `Worktrack` 的局部状态转移合同。

## 上游输入

`Worktrack Contract` 是当前仓库的执行前边界对象。用户讨论、已批准需求、append request、repo goal、恢复路径或人工授权不能直接变成执行计划；它们必须先被收束进本合同，再展开为 `Plan / Task Queue`。

收束时至少明确：

- 已批准目标
- 工作范围
- 非目标
- 验收标准
- 约束条件
- 风险与依赖
- 验证要求

未确认事实应作为风险、阻塞或待审批项暴露，不应被猜测补全。

最少应包含：

- `Node Type`（从 Goal Charter 的 Engineering Node Map 绑定）
  - `type`
  - `source_from_goal_charter`
  - `baseline_form`
  - `merge_required`
  - `gate_criteria`
  - `if_interrupted_strategy`
- `Execution Policy`
  - `runtime_dispatch_mode`
  - `dispatch_mode_source`
  - `allowed_values`
  - `fallback_reason_required`
- 任务目标
- 工作范围
- 非目标
- 影响模块
- 计划中的 next state
- 验收条件
- 约束条件
- 验证要求
- 回滚条件

## Execution Policy

`Execution Policy` 控制本 worktrack 的执行载体选择，不替代 repo 级 `Harness Control State`，也不改变任务目标、范围或验收标准。

标准字段：

- `runtime_dispatch_mode`
  - `auto`
  - `delegated`
  - `current-carrier`
  - 默认应为 `auto`
- `dispatch_mode_source`
  - 默认应为 `worktrack-contract`
- `allowed_values`
  - `auto / delegated / current-carrier`
- `fallback_reason_required`
  - 默认应为 `yes`

`runtime_dispatch_mode` 与 `.aw/control-state.md` 的 `subagent_dispatch_mode` 使用同一组值：

- `auto`：宿主运行时支持真实 SubAgent 委派且权限边界允许时优先委派；如果没有稳定分派壳层、权限阻塞或 `dispatch package unsafe`，必须显式记录 `runtime fallback`
- `delegated`：必须真实创建委派载体；无法委派时返回运行时缺口或权限阻塞，不得自动改为当前载体执行
- `current-carrier`：显式关闭 SubAgent 委派，允许当前载体在同一份限定范围约定内执行

优先级规则：

- 默认 scaffold 中 `.aw/control-state.md` 应写入 `subagent_dispatch_mode_override_scope: worktrack-contract-primary`
- 在 `worktrack-contract-primary` 下，本 artifact 的 `runtime_dispatch_mode` 优先于 control-state 的 `subagent_dispatch_mode`
- 只有 control-state 显式写成 `subagent_dispatch_mode_override_scope: global-override` 时，control-state 的 `subagent_dispatch_mode` 才作为全局覆盖
- 如果本 artifact 未声明 `runtime_dispatch_mode`，control-state 的 `subagent_dispatch_mode` 才作为 repo 级默认值
