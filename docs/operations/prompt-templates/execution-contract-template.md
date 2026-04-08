---
title: "Execution Contract 模板"
status: active
updated: 2026-04-08
owner: aw-kernel
last_verified: 2026-04-08
---
# Execution Contract 模板

> 说明：本文已降级为 compatibility shim。canonical source 已迁到 [execution-contract-template](../../../product/harness-operations/skills/execution-contract-template/references/prompt.md)。本页只保留旧路径兼容入口，不再定义主线语义。

## Canonical Source

- [execution-contract-template/SKILL.md](../../../product/harness-operations/skills/execution-contract-template/SKILL.md)
- [execution-contract-template/references/prompt.md](../../../product/harness-operations/skills/execution-contract-template/references/prompt.md)
- [execution-contract-template/references/entrypoints.md](../../../product/harness-operations/skills/execution-contract-template/references/entrypoints.md)
- [docs/knowledge/README.md](../../knowledge/README.md)

> 目的：为 repo-local 执行流程提供一份最小执行合同，锁定目标、边界、验证与退出条件。

它不是：

- `docs/knowledge/foundations/task-contract-template.md` 的替代品
- 产品设计文档
- 运行时编排器规范

适用场景：

- 任务已经收敛到可以执行，但还需要先冻结本轮边界
- 需要在编码前明确验证计划和退出标准

## 模板

```md
# Execution Contract

## Goal
- 本次必须完成的交付目标：

## Non-goals
- 本次明确不做：

## In-scope Files
- 允许修改的文件或目录：

## Out-of-scope Files
- 禁止修改的文件或目录：

## Preconditions
- 执行前提（依赖、环境、前置信息）：
- 当前阻塞项（如有）：

## Plan
1.
2.
3.

## Validation Plan
- Static Gate：
- Test Gate：
- Smoke Gate：

## Exit Criteria
- 满足以下条件才算完成：

## Risks
- Blocking Risks：
- Rework Risks：
- 未验证点：
- 需人工接手事项：
```

## 使用约束

- 先以 `docs/knowledge/` 主线文档为事实基线
- 未确认内容不要伪装成已确认前提
- 如果执行中需要扩边，必须先更新合同再继续

## 相关文档

- [docs/knowledge/README.md](../../knowledge/README.md)
- [Task Contract 模板](../../knowledge/foundations/task-contract-template.md)
- [Task Contract 基线](../../knowledge/task-interface/task-contract.md)
- [Review / Verify 承接位](../review-verify-handbook.md)
