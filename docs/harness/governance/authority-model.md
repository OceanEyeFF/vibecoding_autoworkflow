---
title: "Authority Model"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Authority Model

Harness 是控制器，但不是最高 authority。

## 可提议者

- Harness 自身
- 执行 agent
- review / validation agent
- human operator

## 常规自动授权

在边界已冻结且合同已批准时，Harness 可以自动执行：

- `Observe`
- `Decide`
- `Dispatch`
- `Verify`
- 初步 `Judge`
- 非破坏性 `Recover`

## 高风险动作

默认不应由低级自动流程自行批准：

- `change-goal`
- `hard-fail` override
- 带残余高风险的最终放行
- 合并到长期 baseline
- 废弃或重置仍有活跃依赖的 worktrack
