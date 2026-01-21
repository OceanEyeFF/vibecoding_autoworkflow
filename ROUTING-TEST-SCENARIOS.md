# ROUTING-TEST-SCENARIOS.md

## 测试基准
- 路由依据：`CLAUDE.md` Part 2「按任务类型路由表」
- Agent 命名策略（2026-01-20 起）：
  - 高频任务：简短命名（ship、review、logs、clean、clarify）
  - 专业领域：完整命名（knowledge-researcher）
  - 已删除：code-debug-expert（调试为复杂流程，留给未来 command/workflow）

## 测试场景

### Scenario 1: 新功能开发
- 输入描述：用户请求"新功能开发"
- 期望（任务要求）：should route to `AUTODEV_小任务工作流.md` + `ship.md`
- Part 2 规范：`/autodev` Skill + `ship` Agent（备选）
- 结论：✅ PASS（ship.md 为功能交付 Agent）

### Scenario 2: 代码分析
- 输入描述：用户请求"代码分析"
- 期望（任务要求）：should route to `review.md`
- Part 2 规范：`review` Agent
- 结论：✅ PASS（review.md 为代码结构分析 Agent）

### Scenario 3: 日志分析
- 输入描述：用户请求"日志分析"
- 期望（任务要求）：should route to `logs.md`
- Part 2 规范：`logs` Agent
- 结论：✅ PASS（logs.md 为日志分析 Agent）

### Scenario 4: 需求澄清
- 输入描述：用户请求"需求澄清"
- 期望（任务要求）：should route to `clarify.md`
- Part 2 规范：`clarify` Agent
- 结论：✅ PASS（clarify.md 为需求澄清 Agent）

### Scenario 5: 清理重构
- 输入描述：用户请求"清理重构"
- 期望（任务要求）：should route to `clean.md`
- Part 2 规范：`clean` Agent
- 结论：✅ PASS（clean.md 为代码清理重构 Agent）

### Scenario 6: 资料研究
- 输入描述：用户请求"资料研究"
- 期望（任务要求）：should route to `knowledge-researcher.md`
- Part 2 规范：`knowledge-researcher` Agent
- 结论：✅ PASS（专业领域保留完整命名）

## 边界/特殊情况（Edge Cases）
1. **调试问题**：
   - code-debug-expert 已删除（调试是复杂流程，不适合单 Agent 解决）
   - 建议：日志分析用 `logs.md`，复杂调试留给未来 debug command/workflow

2. **多意图混合**：
   - 示例："分析错误日志并定位原因"同时包含日志分析与调试问题
   - 建议路由：优先 `logs.md` 处理日志证据，复杂问题引导用户使用未来的 debug command

3. **文档引用**：
   - `AUTODEV_小任务工作流.md` 为工作流规范文档
   - `/autodev` Skill（`Claude/skills/aw-kernel/autodev/SKILL.md`）为主入口

## 结果汇总
- 场景总数：6
- 通过：6
- 未通过：0
- 结论：✅ 所有场景通过（以 `CLAUDE.md` Part 2 为基准）
- 验证日期：2026-01-20

## 变更记录
- 2026-01-20：更新 Agent 命名为简短形式，删除 code-debug-expert，新增 clean 和 knowledge-researcher 场景
- 2026-01-16：初始版本
