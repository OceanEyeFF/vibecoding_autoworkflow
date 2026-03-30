# Task Planning Contract Prompt（需求/问题清单 → 可执行任务合同）

> 定位：把“需求文档或问题列表”转换成可直接驱动多 Agent 执行的 **Task Unit 合同集合**。
> 
> 目标不是产出“好看的任务列表”，而是产出可路由、可并行、可验证、可失败收敛的执行合同。

## Prompt 模板

```text
我们需要基于该文档，制定一份“可执行的任务规划文档”，用于后续直接驱动多 Agent 执行。

【总体目标】
- 将文档中的问题/需求拆分为多个“可独立执行的任务单元（Task Unit）”
- 每个任务必须具备明确边界、依赖关系、执行建议和完成标准
- 输出结果必须可以直接对接执行型 Prompt（无需再加工）

【任务拆分原则】
- 优先拆分为“最小可独立验证单元”，避免过大任务
- 避免跨模块模糊任务，尽量明确到文件/子系统级
- 将高风险/高复杂度任务单独拆出
- 区分代码任务 vs 文档任务（代码优先级更高）
- 明确哪些任务可以并行，哪些必须串行

【每个任务必须使用以下结构】

任务ID：T-{编号}
任务名称：{一句话总结目标}
任务类型（Task Type）：Explore / Implement / Refactor / Debug / Review / Document

1. 任务目标（Goal）
   - 明确要解决的问题或实现的功能
   - 必须是可验证结果，不要写成过程

2. 非目标（Non-goals）
   - 明确不在本任务范围内的内容
   - 防止执行阶段扩边

3. 任务边界（Scope）
   - In-scope：
     - 明确允许修改/新增的文件、模块、目录
   - Out-of-scope：
     - 明确禁止修改的区域

4. 输入上下文（Context）
   - 必须阅读的文件
   - 可选参考文件
   - 不需要读取的区域（如果有）

5. 执行策略（Execution Strategy）
   - 推荐执行方式（例如：局部修改 / 重构 / 补测试 / 调试）
   - 是否需要先做小范围验证
   - 是否需要分步骤执行

6. 模型与推理建议（Execution Profile）
   - 推荐模型（如 CodeX / Claude / Gemini）
   - 推理等级（low / medium / high / xhigh）
   - 原因（例如：上下文大 / 推理复杂 / 逻辑风险高）

7. 依赖关系（Dependencies）
   - 前置任务（必须完成）
   - 可并行任务
   - 是否属于某个批次（Batch）

8. 风险与不确定性（Risks）
   - 潜在失败点
   - 可能缺失的信息
   - 是否需要人工介入

9. 验证计划（Validation Plan）
   - Static：lint / type / build
   - Test：是否需要新增测试
   - Runtime：是否需要运行验证
   - 是否可以做 smoke test

10. 完成标准（Exit Criteria）
   - 明确什么条件下任务可以结束
   - 必须包含“验证通过”的定义

11. 失败协议（Failure Handling）
   - 在什么情况下必须停止
   - 如何报告阻塞
   - 是否允许请求更多上下文

---

【额外要求】

- 在所有任务之后，输出：

1. 任务依赖图（文字描述即可）
2. 推荐执行顺序（Batch 划分）
3. 可并行执行的任务组
4. 高风险任务列表（需要优先关注）
5. 推荐整体执行策略（例如：先清理 P0 问题再扩展功能）

---

【输出要求】
输出为结构化任务规划文档，确保：
- 每个任务可以独立交付给执行 Agent
- 不依赖隐含上下文
- 不存在模糊边界
```

## 对接关系（怎么接后续流程）
- 对接 simple / strict 执行模板：使用 Goal、Scope、Context、Execution Strategy、Exit Criteria。
- 对接 Router：使用 Task Type、Execution Profile、Dependencies、Risks。
- 对接 review-loop：使用 Scope、Validation Plan、Exit Criteria。
- 对接 integration worktree：使用 Batch、Dependencies、Changed files（由 In-scope 推导）。
