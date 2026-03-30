# Review Loop Prompt（PR/Commit 代码审查闭环）

> 定位：代码优先的 repo-side review contract。适用于 commit / PR / diff range / target path 的多轮审查与修复闭环。

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

【角色定义】

You（Loop Controller）
- 指定本轮审查范围
- 决定哪些问题进入修复范围
- 决定是否继续下一轮
- 处理阻塞、越界、冲突

SubAgent1（Inspector）
- 在当前工作区审查指定改动
- 输出审查报告、问题列表、证据、严重级别、影响面
- 只负责发现问题，不负责修复
- 优先排查代码正确性、边界条件、异常处理、回归风险、测试缺口、静态问题
- 文档问题只记录，不抢占代码问题优先级

SubAgent2（Fixer）
- 在新的 worktree 中修复经确认进入本轮范围的问题
- 只修问题列表中的已确认问题，不自行扩边
- 记录每个问题的处理结果：已修 / 未修 / 阻塞
- 对每个修复给出最小必要验证

SubAgent3（Meta-Reviewer）
- 复核 SubAgent1 的审查报告质量
- 判断是否存在漏查、审查不仔细、问题描述模糊
- 生成下一轮给 SubAgent1 的补查重点
- 对终止条件给出明确意见

【执行顺序】

Phase A：首轮审查
1. SubAgent1 审查本次代码改动，输出：
   - Review Scope
   - Findings
   - Severity
   - Evidence
   - Recommended Fix Scope
   - Deferred Doc Issues
   - Risk Triage（Blocking Risks / Rework Risks）

2. You 根据 SubAgent1 的报告，确认进入本轮修复的问题范围。

Phase B：并行处理
3. SubAgent2 在新的 worktree 中修复已确认问题，输出：
   - Fixed Issues
   - Unfixed / Blocked Issues
   - Changed Files
   - Validation Per Fix

4. SubAgent3 复盘 SubAgent1 的审查质量，输出：
   - Missed-risk Hypotheses
   - Weak Review Areas
   - Next-round Checklist
   - Stop / Continue Recommendation

Phase C：复查
5. SubAgent1 读取：
   - 自己上一轮报告
   - SubAgent2 的修复结果
   - SubAgent3 的补查清单

   然后执行下一轮定向复查，重点检查：
   - 修复是否真正解决原问题
   - 修复是否引入新问题
   - 上一轮可能漏掉的方向
   - 是否还有高优先级代码问题未处理

6. You 判断是否进入下一轮循环。

【终止条件】
仅当以下条件同时满足时，允许结束循环：
- 当前轮 SubAgent1 未发现新的高优先级代码问题
- SubAgent3 明确表示无重要异议，且没有新的高风险补查方向
- SubAgent2 已对进入范围的问题给出明确状态（已修 / 未修 / 阻塞）
- 至少完成一轮对修复结果的复查

【输出要求】
最终输出：
- 审查轮数
- 已确认并处理的问题列表
- 仍未解决的问题与原因
- 本轮实际修改文件
- 做过的静态检查 / 测试 / 烟测
- 残留风险
- 终止理由

【Integration Phase】
- 所有修复 Agent 的改动不得直接作为最终交付结果提交。
- 每个修复 Agent 必须在独立 fix branch + fix worktree 中工作。
- 当一轮修复结束后，由 Loop Controller 创建一个 integration branch 和 integration worktree。
- 所有 fix branches 按既定顺序合并到 integration branch。
- 仅在 integration worktree 上执行统一的静态检查、测试、烟测、残留风险审查。
- 只有 integration worktree 上的状态可以形成最终提交。
- fix worktrees 在最终交付或放弃后必须清理。
```

## 部署路径说明（本仓库）
- 这个 prompt 文档路径：`docs/operations/prompt-templates/review-loop-code-review.md`
- 若以 Skill 方式使用，请对应安装：`Claude/skills/aw-kernel/review-loop/SKILL.md`
- 安装后默认路径：`~/.claude/skills/aw-kernel/review-loop/SKILL.md`
