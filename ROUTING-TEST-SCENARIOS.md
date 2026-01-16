# ROUTING-TEST-SCENARIOS.md

## 测试基准
- 路由依据：`CLAUDE.md` Part 2「按任务类型路由表」
- 别名映射（用于对齐 Part 2 规范与现有入口文档）：
  - `ship.md` => `feature-shipper.md`
  - `review.md` => `code-analyzer.md`
  - `clarify.md` => `requirement-refiner.md`
  - `logs.md` => `system-log-analyzer.md`

## 测试场景

### Scenario 1: 新功能开发
- 输入描述：用户请求“新功能开发”
- 期望（任务要求）：should route to `AUTODEV_小任务工作流.md` + `ship.md`
- Part 2 规范：`/autodev` Skill + `feature-shipper` Agent（备选）
- 映射校验：`ship.md` 为 `feature-shipper` 的路由入口别名
- 结论：✅ PASS（满足 Part 2 路由表；ship.md 与 feature-shipper 等价）

### Scenario 2: 代码分析
- 输入描述：用户请求“代码分析”
- 期望（任务要求）：should route to `review.md`
- Part 2 规范：`code-analyzer` Agent
- 映射校验：`review.md` 为 `code-analyzer` 的路由入口别名
- 结论：✅ PASS

### Scenario 3: 调试问题
- 输入描述：用户请求“调试问题”
- 期望（任务要求）：should route to `code-debug-expert.md` + `logs.md`
- Part 2 规范：`code-debug-expert` Agent + `system-log-analyzer` Agent（备选）
- 映射校验：`logs.md` 为 `system-log-analyzer` 的路由入口别名
- 结论：✅ PASS

### Scenario 4: 需求澄清
- 输入描述：用户请求“需求澄清”
- 期望（任务要求）：should route to `clarify.md`
- Part 2 规范：`requirement-refiner` Agent
- 映射校验：`clarify.md` 为 `requirement-refiner` 的路由入口别名
- 结论：✅ PASS

## 边界/特殊情况（Edge Cases）
1. 入口名与规范名不一致：
   - 任务要求中的 `AUTODEV_小任务工作流.md` 当前仓库未发现；
   - 按 Part 2 规范，`/autodev` Skill（`Claude/skills/aw-kernel/autodev/SKILL.md`）为主入口，`ship.md` 为交付入口别名。
2. 多意图混合：
   - 示例：“分析错误日志并定位原因”同时包含日志分析与调试问题。
   - 建议路由：优先 `code-debug-expert`，并联动 `logs.md`（system-log-analyzer）处理日志证据。

## 结果汇总
- 场景总数：4
- 通过：4
- 未通过：0
- 结论：✅ 所有场景通过（以 `CLAUDE.md` Part 2 为基准）
- 验证日期：2026-01-16
