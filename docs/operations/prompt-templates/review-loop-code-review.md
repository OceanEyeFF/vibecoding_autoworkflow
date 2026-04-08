---
title: "Review Loop Prompt"
status: active
updated: 2026-04-08
owner: aw-kernel
last_verified: 2026-04-08
---
# Review Loop Prompt

> 说明：本文已降级为 compatibility shim。canonical source 已迁到 [review-loop-workflow](../../../product/harness-operations/skills/review-loop-workflow/references/prompt.md)。本页只保留旧路径兼容入口，不再定义主线语义。

## Canonical Source

- [review-loop-workflow/SKILL.md](../../../product/harness-operations/skills/review-loop-workflow/SKILL.md)
- [review-loop-workflow/references/prompt.md](../../../product/harness-operations/skills/review-loop-workflow/references/prompt.md)
- [review-loop-workflow/references/entrypoints.md](../../../product/harness-operations/skills/review-loop-workflow/references/entrypoints.md)
- [docs/knowledge/README.md](../../knowledge/README.md)

> 定位：代码优先的 repo-side review contract。适用于 commit、PR、diff range 或 target path 的多轮审查与修复闭环。

## Prompt 模板

```text
[commit / PR / diff range / target path]

准备对本次代码改动执行一个 review-loop。请严格按以下角色和阶段工作。目标是优先发现并处理代码问题；文档问题优先级较低，除非它们直接导致代码理解或交付风险。

【总原则】
- 本流程优先审查代码问题，其次才是文档问题。
- 审查范围默认限定在本次指定的 commit / PR / diff range 及其直接影响文件。
- 不要把 review-loop 扩展成大范围重构。
- 若遇到环境缺失、运行中断、范围冲突、修复越界，立即停下并报告。
- 每轮都要留下结构化记录，便于下一轮复查。
- 禁止静默降级：修复阶段不得自行 fallback 到简单但不完整方案；如需降级必须先说明影响并等待确认。
- 启用 Harness 状态管控：每轮阶段切换前后更新 `.autoworkflow/state/harness-review-loop.json`。

【Harness 必选项】
- Contract：维护 `.autoworkflow/contracts/<workflow_id>.json`，结构参考 `docs/operations/prompt-templates/harness-contract-template.md`
- Scope Gate：执行 `python toolchain/scripts/test/scope_gate_check.py ...`，有 violations 不得进入下一阶段
- Gate 回填：执行 `python toolchain/scripts/test/gate_status_backfill.py ...`

【收口治理度评估】
- 在结束前评估 `rule`、`folders`、`document`、`code` 四个维度。
- 每个维度只能给：`通过` / `有条件通过` / `不通过`。
- 必须附证据；若 `code` 维度不通过，整体不得为通过。

【角色定义】

You（Loop Controller）
- 指定本轮审查范围
- 决定哪些问题进入修复范围
- 决定是否继续下一轮
- 处理阻塞、越界、冲突

SubAgent1（Inspector）
- 在当前工作区审查指定改动
- 只负责发现问题，不负责修复
- 优先排查正确性、边界条件、异常处理、回归风险、测试缺口、静态问题

SubAgent2（Fixer）
- 在新的 worktree 中修复已确认问题
- 只修确认清单中的问题，不自行扩边
- 对每个修复给出最小必要验证

SubAgent3（Meta-Reviewer）
- 复核 Inspector 的审查质量
- 生成下一轮补查重点
- 对终止条件给出明确意见

【执行顺序】

Phase A：首轮审查
1. Inspector 输出：
   - Review Scope
   - Findings
   - Severity
   - Evidence
   - Recommended Fix Scope
   - Deferred Doc Issues
   - Risk Triage（Blocking Risks / Rework Risks）
2. Loop Controller 冻结本轮修复范围。

Phase B：并行处理
3. Fixer 在新 worktree 修复，输出：
   - Fixed Issues
   - Unfixed / Blocked Issues
   - Changed Files
   - Validation Per Fix
4. Meta-Reviewer 输出：
   - Missed-risk Hypotheses
   - Weak Review Areas
   - Next-round Checklist
   - Stop / Continue Recommendation

Phase B.5：验证关卡
5. 统一执行：
   - Static Code Check
   - Static Semantic Simulation
   - White-box Tests
6. 若任一项不通过，返回 Phase B。

Phase C：复查
7. Inspector 读取上一轮报告、修复结果和补查清单，再做定向复查。
8. Loop Controller 判断是否进入下一轮。

【Integration Phase】
- 所有修复改动不得直接作为最终交付提交。
- 每个修复 Agent 必须在独立 fix branch + fix worktree 中工作。
- 修复完成后，由 Loop Controller 创建 integration branch + integration worktree。
- 仅 integration worktree 的状态可以形成最终提交。

【终止条件】
- Inspector 未发现新的高优先级代码问题。
- Meta-Reviewer 无重要异议，且无新的高风险补查方向。
- Fixer 对范围内问题给出明确状态。
- 至少完成一轮对修复结果的复查。
```

## 相关文档

- [docs/knowledge/README.md](../../knowledge/README.md)
- [Docs 文档治理基线](../../knowledge/foundations/docs-governance.md)
- [Harness Contract 模板](./harness-contract-template.md)
- [Repo Governance Evaluation Prompt](./repo-governance-evaluation.md)
