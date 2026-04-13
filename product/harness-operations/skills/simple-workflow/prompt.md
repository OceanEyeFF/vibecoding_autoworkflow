# Simple Workflow Prompt

```text
[filepath or filename]

准备落地这个文档提到的开发需求。请把这次任务当作一次“受仓库 contract 约束的执行流程”，严格按下面步骤顺序执行，不要跳步，不要扩展任务边界。

【总原则】
- 本次任务以“原始需求文档 + 仓库真相层 + Step 1 产出的执行合同”为唯一依据。
- 未经明确允许，不扩大修改范围，不顺手重构，不处理无关问题。
- 若遇到信息不足、运行中断、依赖缺失、测试无法执行、边界冲突，必须停止在当前阶段并报告阻塞。
- 默认把未明确允许的额外改动视为越界。
- 禁止静默降级：如需 fallback，必须先说明影响并等待确认。

【Step 0：限定阅读入口】
先按 `references/entrypoints.md` 指向的权威路由确定阅读范围。
本模板只额外要求：在 route 已收口后，只继续读取与当前任务直接相关的 `docs/`、`product/`、`toolchain/` 文件，不自行扩读 repo-local state、mount 或 deploy target。

【Step 1：任务规划 / 执行合同生成】
基于原始需求文档、仓库真相层文档和实际代码，输出一个执行合同，必须包含：
- Goal
- Non-goals
- In-scope Files
- Out-of-scope Files
- Preconditions
- Plan
- Validation Plan
- Exit Criteria
- Risks

【Step 2：按合同执行】
- 只能修改 In-scope Files；若需要扩边，先停止并说明原因。
- 不把优化建议自动转成实现。
- 每完成一个关键改动，都要对照 Goal / Non-goals 自检一次。

【Step 3：出口 Gate】
至少完成以下检查：
1. Scope Gate
2. Spec Gate
3. Static Gate
4. Test Gate
5. Smoke Gate
6. Risk Report

【最终输出格式】
- Step 1 执行合同摘要
- 实际修改文件列表
- 完成情况（完成 / 部分完成 / 阻塞）
- 已执行的静态检查
- 已执行的测试与烟测
- 残留风险与人工后续建议

【失败协议】
出现以下任一情况时立即停止：
- 任务边界不清
- 需要修改 Out-of-scope Files
- 仓库真相层与原始文档冲突
- 构建或测试环境缺失
- 中途运行中断
- 关键依赖不存在
```
