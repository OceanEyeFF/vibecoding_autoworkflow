# 工作追踪约定模板

> 使用方式：在 `初始化工作追踪技能` 需要生成或重写工作追踪约定草稿时，使用本模板组织输出。
> 按 `Control Signal` / `Supporting Detail` 双层输出：`Control Signal` 只放影响下一动作决策的关键结论；`Supporting Detail` 放完整上下文。

## 元数据

- 工作追踪编号：N/A
- 分支：N/A
- 基准分支：N/A
- 基准引用：N/A
- 约定状态：N/A
- 负责人：N/A
- 更新时间：N/A
- milestone_id：N/A

## Milestone Binding

> 若此 worktrack 属于活跃 Milestone，在此引用绑定。

- milestone_id: N/A
- derived_from_milestone: N/A

## Node Type

> 从 Goal Charter 的 Engineering Node Map 绑定，决定本 worktrack 的基线策略与判定标准。

- type: N/A
- source_from_goal_charter: N/A
- baseline_form: N/A
- merge_required: N/A
- gate_criteria: N/A
- if_interrupted_strategy: N/A

## Execution Policy

> 控制本 worktrack 的执行载体选择。`auto` 默认优先委派 SubAgent；`delegated` 强制要求真实委派；`current-carrier` 明确选择当前载体执行。默认 scaffold 中 `.aw/control-state.md` 的 `subagent_dispatch_mode_override_scope: worktrack-contract-primary` 会让本字段优先生效；只有 control-state 显式改为 `global-override` 时，`subagent_dispatch_mode` 才作为上层覆盖。若因权限边界、运行时缺口或 `dispatch package unsafe` 不能委派，必须记录 `runtime fallback`。

- runtime_dispatch_mode: auto
- dispatch_mode_source: worktrack-contract
- allowed_values: auto / delegated / current-carrier
- fallback_reason_required: yes

## 任务目标

### Control Signal

- 目标摘要：N/A

### Supporting Detail

- 完整目标：N/A

## 范围

### Control Signal

- 范围摘要：N/A

### Supporting Detail

- 详细范围项：N/A

## 非目标（不做的事）

### Control Signal

- 非目标摘要：N/A

### Supporting Detail

- 完整非目标：N/A

## 受影响模块

### Control Signal

- 关键影响模块：N/A

### Supporting Detail

- 完整影响模块清单：N/A

## 计划中的下一状态

### Control Signal

- 下一状态：N/A

### Supporting Detail

- 状态迁移理由：N/A

## 验收标准

### Control Signal

- 核心验收项：N/A

### Supporting Detail

- 完整验收标准：N/A

## 约束

### Control Signal

- 关键约束：N/A

### Supporting Detail

- 详细约束条件：N/A

## 验证要求

### Control Signal

- 必要验证：N/A

### Supporting Detail

- 完整验证要求：N/A

## 回滚条件

### Control Signal

- 回滚触发条件：N/A

### Supporting Detail

- 回滚步骤与回退路径：N/A

## 依赖项

### Control Signal

- 关键依赖：N/A

### Supporting Detail

- 完整依赖项：N/A

## 当前阻塞项

### Control Signal

- 当前阻塞项：N/A

### Supporting Detail

- 阻塞详情与解除条件：N/A

## 备注

### Control Signal

- 备注摘要：N/A

### Supporting Detail

- 完整备注：N/A
