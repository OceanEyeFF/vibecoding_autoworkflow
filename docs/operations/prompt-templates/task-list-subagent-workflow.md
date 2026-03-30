# Task List SubAgent Workflow Prompt（多任务文件专用）

> 用途：当输入文件内包含多个任务时，使用本模板替代单任务 workflow，避免范围漂移、依赖错序和验证遗漏。

## Prompt 模板

```text
[task file path]

请先判断该任务文件是否包含多个任务项；若是，则使用“Task List SubAgent Workflow”执行，不得按单任务流程直接推进。

【目标】
- 识别并归一化任务列表
- 生成可执行任务矩阵（每项含边界/依赖/验证/失败协议）
- 分 Batch 执行并在 integration worktree 统一验收

【Step 0：任务检测】
1. 读取任务文件并识别任务数量。
2. 若仅 1 个任务：降级到单任务 workflow（simple/strict）。
3. 若 >=2 个任务：继续本流程。

【Step 1：Task Inventory】
输出每个任务的：
- Task ID
- 标题
- 来源位置（文件+行）
- 优先级（P0/P1/P2）
- 任务类型（Implement/Refactor/Debug/Review/Document）
- 是否信息不足（Needs Clarification）

【Step 2：Task Execution Matrix】
为每个任务生成：
- Goal / Non-goals
- In-scope / Out-of-scope
- Context（必读/可选/禁读）
- Execution Profile（模型+推理等级+理由）
- Dependencies（前置/并行/Batch）
- Validation Plan（Static/Test/Smoke）
- Exit Criteria
- Failure Handling

并额外输出：
- 任务依赖图（文字）
- Batch 执行顺序
- 可并行任务组
- 高风险任务列表

【Step 3：分批执行】
- 同 Batch 并行，跨 Batch 串行。
- 每个任务执行时必须回显 Goal/Scope/Exit Criteria。
- 每个任务结束必须输出：Done / Partial / Blocked + Changed Files + Validation + Residual Risks。

【Step 4：Integration Gate】
在 integration worktree 统一执行：
1. Scope Gate
2. Spec Gate
3. Static Gate（至少一次）
4. Test Gate（可补则补，不可补说明）
5. Smoke Gate（可跑则跑，不可跑说明）

【Step 5：失败协议】
触发以下任一情况必须停止并报告：
- 关键任务信息缺失且无法澄清
- 需要修改 Out-of-scope 文件
- 构建/测试环境缺失
- 多任务合并冲突无法消解
- 任一 P0 风险未被验证

【最终输出】
- Task Inventory 摘要
- Task Execution Matrix 摘要
- Batch 执行结果
- 任务状态总表
- Integration Gate 结果
- 残留风险与人工后续建议
```
