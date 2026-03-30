---
name: review-loop
version: 1.0.0
created: 2026-03-27
updated: 2026-03-27
description: >
  代码改动审查与修复闭环工作流（commit/PR/diff range/target path）。
  以代码问题为最高优先级，支持 Inspector/Fixer/Meta-Reviewer 三角色循环，
  并强制使用 fix worktree + integration worktree 形成最终交付。
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, AskUserQuestion, Task
---

# Review Loop（Code-first 审查闭环）

你现在进入 **review-loop** 模式。

## 定位与边界
- 这是一个 repo-side execution contract，不是新的编排平台。
- 目标是对指定改动执行多轮代码审查与修复，优先解决代码问题，文档问题仅在影响代码交付时提升优先级。
- 默认审查范围限定在：`commit / PR / diff range / target path` 与其直接影响文件。
- 禁止静默降级：修复阶段不得自行 fallback 到不完整方案；如需降级必须先报告影响并等待确认。

## 输入
用户必须提供至少一项：
- commit SHA
- PR 编号或 PR 对比分支
- diff range（如 `main...feature-x`）
- target path

若输入不足以定位范围，立即 BLOCKED 并请求补充。

## 角色与职责

### You（Loop Controller）
- 冻结本轮审查/修复范围。
- 确认进入修复的问题清单。
- 决定继续下一轮或终止。
- 处理阻塞、越界、冲突与优先级裁决。

### SubAgent1（Inspector）
- 审查指定改动，输出结构化问题报告。
- 只负责发现问题，不负责修复。
- 代码优先：正确性、边界条件、异常处理、回归风险、测试缺口、静态问题。
- 文档问题只记录到 `Deferred Doc Issues`，不抢占代码问题优先级。

### SubAgent2（Fixer）
- 在独立 `fix branch + fix worktree` 修复经确认的问题。
- 严禁自行扩边；仅处理确认清单。
- 每个问题必须给出状态：已修 / 未修 / 阻塞。
- 每个修复必须给出最小必要验证。

### SubAgent3（Meta-Reviewer）
- 复核 Inspector 的审查质量。
- 输出漏查假设、薄弱审查点、下一轮补查清单。
- 对是否终止给出明确建议。

## 执行流程

### Phase A：首轮审查
1. SubAgent1 输出：
   - Review Scope
   - Findings
   - Severity
   - Evidence
   - Recommended Fix Scope
   - Deferred Doc Issues
   - Risk Triage（Blocking Risks / Rework Risks）
2. You 确认本轮修复范围（冻结）。

### Phase B：并行处理
3. SubAgent2 在新 worktree 修复，输出：
   - Fixed Issues
   - Unfixed / Blocked Issues
   - Changed Files
   - Validation Per Fix
   - Minimal Repro Test Per Issue（每个问题至少一个最小测试：修复前失败、修复后通过）
4. SubAgent3 输出：
   - Missed-risk Hypotheses
   - Weak Review Areas
   - Next-round Checklist
   - Stop / Continue Recommendation

### Phase B.5：验证关卡（必须）
5. 在进入 Phase C 前统一执行：
   - Static Code Check（lint/type/build check）
   - Static Semantic Simulation（关键路径、边界条件、规则一致性静态模拟）
   - White-box Tests（修复点白盒测试）
6. 若 Phase B.5 任一项不通过，返回 Phase B 继续修复。

### Phase C：复查
7. SubAgent1 读取上轮报告 + 修复结果 + 补查清单，执行定向复查：
   - 修复是否真正解决原问题
   - 是否引入新问题
   - 上轮漏查方向是否命中
   - 是否仍有高优先级代码问题
8. You 判断是否进入下一轮。

## Integration Phase（硬约束）
- Fixer 改动不得直接作为最终交付提交。
- 每个 Fixer 必须在独立 fix branch + fix worktree 工作。
- 每轮修复后，由 Loop Controller 创建 integration branch + integration worktree。
- 按既定顺序将所有 fix branches 合并到 integration branch。
- 统一在 integration worktree 执行静态检查 / 测试 / 烟测 / 残留风险审查。
- 仅 integration worktree 的状态可形成最终提交。
- 最终交付或放弃后，清理 fix worktrees 与 integration worktree。

## 终止条件（必须同时满足）
- Inspector 未发现新的高优先级代码问题。
- Meta-Reviewer 明确无重要异议，且无高风险补查方向。
- Fixer 对范围内问题给出明确状态（已修 / 未修 / 阻塞）。
- 至少完成一轮“对修复结果的复查”。

## 失败协议
触发以下任一条件，立即停止并报告：
- 环境缺失或运行中断
- 范围冲突或需要越界修复
- 无法定位审查对象（commit/PR/diff/path 信息不足）
- 关键验证无法执行且无替代证据

## 统一输出格式
- 审查轮数
- 已确认并处理的问题列表
- 仍未解决的问题与原因
- 本轮实际修改文件
- 已执行静态检查 / 测试 / 烟测
- 残留风险
- 终止理由

## 多端部署路径（Claude / CodeX / OpenCode）
源路径（仓库内）：
- `Claude/skills/aw-kernel/review-loop/SKILL.md`

部署目标（按端侧 Skills 根目录 + namespace 映射）：
- Claude：`~/.claude/skills/<namespace>/review-loop/SKILL.md`
- CodeX：`~/.codex/skills/<namespace>/review-loop/SKILL.md`
- OpenCode：`~/.opencode/skills/<namespace>/review-loop/SKILL.md`

Claude 端推荐安装命令：
```bash
bash Claude/scripts/install-global.sh --force
# 或自定义 namespace
bash Claude/scripts/install-global.sh --force --namespace <namespace>
```
