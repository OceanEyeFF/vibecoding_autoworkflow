---
name: task-list-workflow
version: 1.0.0
created: 2026-03-27
updated: 2026-03-27
description: >
  任务列表执行工作流。用于处理“一个任务文件中包含多个任务”的场景，
  自动完成任务识别、依赖分组、分批执行、逐任务验收与汇总交付。
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, AskUserQuestion, Task
---

# Task List SubAgent Workflow（多任务清单执行）

你现在进入 **task-list-workflow** 模式。

## 适用场景
- 输入是任务文件（markdown/txt/yaml/json）且包含多个任务。
- 原有单任务 workflow 无法稳定处理多任务依赖与并行关系。

## 触发判定（必须执行）
1. 读取传入任务文件。
2. 检测任务数量（按标题、编号、清单项、结构化字段综合判断）。
3. 若任务数 <= 1：
   - 直接降级为单任务流程（simple/strict workflow）。
4. 若任务数 >= 2：
   - 进入本 workflow 的 Task List 模式。

## 总原则
- 任务单位最小化：每个子任务必须可独立验证。
- 边界硬约束：每个子任务必须有 In-scope / Out-of-scope。
- 先规划后执行：先产出 Task Execution Matrix，再进入执行。
- 失败可控：任何关键阻塞都必须显式上报，不允许 silent fail。

## Phase 0：输入归一化
输出 `Task Inventory`：
- Task ID
- Task 标题
- 来源位置（文件+行区间）
- 初始优先级（P0/P1/P2）
- 初始类型（Implement/Refactor/Debug/Review/Document）

若任务描述缺失关键字段（目标、范围、验收），标记为 `Needs Clarification`，先不执行。

## Phase 1：任务规划（Task Execution Matrix）
为每个任务生成执行矩阵字段：
- Goal
- Non-goals
- In-scope / Out-of-scope
- Context（必读/可选/禁读）
- Execution Profile（模型 + 推理等级 + 理由）
- Dependencies（前置任务 / 可并行任务 / Batch）
- Validation Plan（Static/Test/Smoke）
- Exit Criteria
- Failure Handling

输出物：
- 任务依赖图（文字版）
- Batch 划分
- 并行执行组
- 高风险任务清单

## Phase 2：分批执行（SubAgent）
- 同一 Batch 内可并行执行；跨 Batch 必须串行。
- 每个子任务执行前，必须回显本任务合同（Goal/Scope/Exit Criteria）。
- 每个子任务执行后，必须产出：
  - 状态：Done / Partial / Blocked
  - 变更文件
  - 验证结果（Static/Test/Smoke）
  - 残留风险

## Phase 3：多任务 Review Loop（可选但推荐）
当满足任一条件时触发 review-loop：
- 存在 P0/P1 代码风险
- 任意子任务为 Partial/Blocked
- 多任务合并后出现冲突或回归迹象

触发后使用 `review-loop` 规则做 Inspector/Fixer/Meta-Reviewer 复查。

## Phase 4：Integration Gate（必须）
- 所有子任务不得直接视为最终交付。
- 必须在 integration worktree 汇总并统一验证。
- 至少执行：
  1. Scope Gate（无未授权扩边）
  2. Spec Gate（目标满足、非目标未违反）
  3. Static Gate（至少一次静态检查）
  4. Test Gate（可补则补，不可补需说明）
  5. Smoke Gate（可跑则跑，不可跑需说明）

## 终止条件
仅在以下条件同时满足时结束：
- 所有 Batch 已处理完成。
- 所有任务状态明确（Done / Partial / Blocked）。
- Integration Gate 完成并有证据。
- 已输出残留风险与人工接手建议。

## 最终输出格式
- Task Inventory 摘要
- Task Execution Matrix 摘要
- Batch 执行结果
- 任务状态总表（Done/Partial/Blocked）
- Integration Gate 结果
- 残留风险与后续建议

## 部署路径（本仓库）
源路径：
- `Claude/skills/aw-kernel/task-list-workflow/SKILL.md`

安装后（默认 namespace）：
- `~/.claude/skills/aw-kernel/task-list-workflow/SKILL.md`

安装命令：
```bash
bash Claude/scripts/install-global.sh --force
# 或
bash Claude/scripts/install-global.sh --force --namespace <namespace>
```
