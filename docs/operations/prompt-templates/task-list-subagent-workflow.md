---
title: "Task List Workflow Prompt"
status: active
updated: 2026-04-07
owner: aw-kernel
last_verified: 2026-04-07
---
# Task List Workflow Prompt

> 目的：当输入文件内包含多个任务时，替代单任务 workflow，避免范围漂移、依赖错序和验证遗漏。

## Prompt 模板

```text
[task file path]

请先判断该任务文件是否包含多个任务项；若是，则使用“Task List Workflow”执行，不得按单任务流程直接推进。

【目标】
- 识别并归一化任务列表
- 生成可执行任务矩阵（每项含边界、依赖、验证、失败协议）
- 分 Batch 执行并在 integration worktree 统一验收
- 禁止未授权降级到不完整方案
- 启用 Harness 状态管控：持续更新 `.autoworkflow/state/harness-task-list.json`

【Harness 必选项】
- Contract：维护 `.autoworkflow/contracts/<workflow_id>.json`，结构参考 `docs/operations/prompt-templates/harness-contract-template.md`
- Scope Gate：执行 `python toolchain/scripts/test/scope_gate_check.py ...`
- Gate 回填：执行 `python toolchain/scripts/test/gate_status_backfill.py ...`

【收口治理度评估】
- 在最终交付前评估 `rule`、`folders`、`document`、`code` 四个维度。
- `code` 维度不通过时，整体不得评为通过。

【Step 0：任务检测】
1. 读取任务文件并识别任务数量。
2. 若仅 1 个任务：降级到单任务 workflow。
3. 若 >= 2 个任务：继续本流程。

【Step 1：Task Inventory】
输出每个任务的：
- Task ID
- 标题
- 来源位置（文件 + 行）
- 优先级（P0 / P1 / P2）
- 任务类型
- 是否信息不足

【Step 2：Task Execution Matrix】
为每个任务生成：
- Goal / Non-goals
- In-scope / Out-of-scope
- Context
- Execution Profile
- Dependencies
- Validation Plan
- Exit Criteria
- Failure Handling

并额外输出：
- 任务依赖图
- Batch 顺序
- 可并行任务组
- 高风险任务列表

【Step 3：分批执行】
- 同 Batch 并行，跨 Batch 串行。
- 每个任务结束必须输出：Done / Partial / Blocked + Changed Files + Validation + Residual Risks。

【Step 4：Integration Gate】
在 integration worktree 统一执行：
1. Scope Gate
2. Spec Gate
3. Static Gate
4. Test Gate
5. Smoke Gate

【Step 5：失败协议】
触发以下任一情况必须停止并报告：
- 关键任务信息缺失且无法澄清
- 需要修改 Out-of-scope 文件
- 构建或测试环境缺失
- 多任务合并冲突无法消解
- 任一 P0 风险未被验证
```

## 相关文档

- [docs/knowledge/README.md](../../knowledge/README.md)
- [Task Contract 模板](../../knowledge/foundations/task-contract-template.md)
- [Task Planning Contract Prompt](./task-planning-contract.md)
- [Review Loop Prompt](./review-loop-code-review.md)
