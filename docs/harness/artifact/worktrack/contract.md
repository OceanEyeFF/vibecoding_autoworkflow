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

Worktrack Contract 是执行前边界对象：用户讨论、已批准需求、append request、repo goal、恢复路径或人工授权都不能直接变成执行计划，必须先收束进本合同再展开为 Plan/Task Queue。收束时至少明确已批准目标、工作范围、非目标、验收标准、约束条件、风险与依赖、验证要求。未确认事实应作为风险/阻塞/待审批项暴露，不应猜测补全。

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

Execution Policy 控制本 worktrack 的执行载体选择，不替代 repo 级 Harness Control State 或任务目标/范围/验收标准。标准字段：runtime_dispatch_mode 默认 auto（支持 auto/delegated/current-carrier，与 control-state 的 subagent_dispatch_mode 使用同一组值）；dispatch_mode_source 默认 worktrack-contract；fallback_reason_required 默认 yes。

auto 语义：优先委派 SubAgent，无法安全委派时显式 runtime fallback；delegated：必须委派否则返回 gap/block；current-carrier：显式关闭委派。默认优先级：worktrack-contract-primary 下 runtime_dispatch_mode 优先；仅 global-override 时 control-state 覆盖；contract 未声明时使用 control-state 的 repo 级默认值。
