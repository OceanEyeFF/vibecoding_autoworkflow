---
title: "Strict Workflow Prompt"
status: active
updated: 2026-04-08
owner: aw-kernel
last_verified: 2026-04-08
---
# Strict Workflow Prompt

> 说明：本文已降级为 compatibility shim。canonical source 已迁到 [strict-workflow](../../../product/harness-operations/skills/strict-workflow/references/prompt.md)。本页只保留旧路径兼容入口，不再定义主线语义。

## Canonical Source

- [strict-workflow/SKILL.md](../../../product/harness-operations/skills/strict-workflow/SKILL.md)
- [strict-workflow/references/prompt.md](../../../product/harness-operations/skills/strict-workflow/references/prompt.md)
- [strict-workflow/references/entrypoints.md](../../../product/harness-operations/skills/strict-workflow/references/entrypoints.md)
- [docs/knowledge/README.md](../../knowledge/README.md)

> 定位：跨模块、高风险或需要更强审计的任务模板。

## Prompt 模板

```text
[filepath or filename]

准备落地这个文档提到的开发需求。请严格执行“边界冻结 + 分阶段签收 + 失败即停”的执行流程。

【总原则】
- 唯一依据：原始需求文档 + 仓库真相层 + Step 1 执行合同。
- 执行前必须冻结 In-scope / Out-of-scope；冻结后不得私自扩边。
- 所有阶段均需产出可审计证据。
- 禁止未授权降级：不得在未明确说明和未获确认的情况下，自行 fallback 到不完整方案。

【Step 0：限定阅读入口】
先按 `AGENTS.md` 的权威路由确定阅读范围。
本模板只额外要求：在 route 已收口后，只继续读取与当前任务直接相关的 `docs/`、`product/`、`toolchain/` 文件，不自行扩读 repo-local state、mount 或 deploy target。

【Step 1：执行合同生成 + 边界冻结】
先生成执行合同，至少包含：
- Goal / Non-goals
- In-scope Files / Out-of-scope Files
- Preconditions / Blocking Risks
- Plan（分阶段）
- Validation Plan
- Exit Criteria

并增加风险预分析：
- Blocking Risks
- Rework Risks
- 每个风险的处理策略：立即处理 / 延后处理 / 请求人工决策

冻结规则：
- Step 1 输出后，In-scope 与 Out-of-scope 默认锁定。
- 如需扩边，必须先停止并提交扩边申请。

【Step 2：分阶段执行】
每阶段结束都要输出：
- 已完成项
- 证据列表
- 与 Goal / Non-goals 的一致性检查
- 是否触发阻塞

【Step 3：严格出口 Gate】
必须完成并回报：
1. Scope Gate
2. Spec Gate
3. Static Gate
4. Test Gate
5. Smoke Gate
6. Risk Report

【最终输出格式】
- 执行合同摘要（含冻结边界）
- 分阶段执行证据摘要
- 实际修改文件列表
- 完成情况（完成 / 部分完成 / 阻塞）
- Gate 结果总表
- 残留风险与后续建议

【失败协议】
触发以下任一条件，必须立即停止并升级：
- 任务边界不清
- 需要修改 Out-of-scope Files
- 真相层与需求文档冲突
- 构建或测试环境缺失
- 中途运行中断
- 关键依赖不存在
- 任一关键 Gate 无法完成且无替代证据
```

## 相关文档

- [docs/knowledge/README.md](../../knowledge/README.md)
- [AGENTS.md](../../../AGENTS.md)
- [Task Contract 基线](../../knowledge/task-interface/task-contract.md)
- [Execution Contract 模板](./execution-contract-template.md)
- [Task Planning Contract Prompt](./task-planning-contract.md)
