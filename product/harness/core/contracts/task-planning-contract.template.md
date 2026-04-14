# Task Planning Contract

## Task Item Template

任务ID：`T-{编号}`

任务名称：`{一句话总结目标}`

任务类型：`Explore | Implement | Refactor | Debug | Review | Document`

### 1. 任务目标（Goal）

### 2. 非目标（Non-goals）

### 3. 任务边界（In-scope / Out-of-scope）

### 4. 输入上下文（必读 / 可选 / 不需要读取）

### 5. 执行策略（Execution Strategy）

### 6. 模型与推理建议（Execution Profile）

### 7. 依赖关系（Dependencies）

### 8. 风险与不确定性（Risks）

### 9. 验证计划（Validation Plan）

### 10. 完成标准（Exit Criteria）

### 11. 失败协议（Failure Handling）

## Planning Rollup

在所有任务之后，必须额外输出：

1. 任务依赖图
2. 推荐执行顺序（Batch 划分）
3. 可并行执行的任务组
4. 高风险任务列表
5. 推荐整体执行策略

## Extraction rule

- 每个任务必须可独立交付给执行 Agent。
- 不依赖隐含上下文。
- 不允许模糊边界。
