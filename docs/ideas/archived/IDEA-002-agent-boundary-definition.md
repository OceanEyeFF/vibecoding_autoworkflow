---
title: "Claude Code Agent 设计基线：Agent 职责边界定义"
status: archived
updated: 2026-03-22
owner: aw-kernel
last_verified: 2026-03-22
---
# Claude Code Agent 设计基线：Agent 职责边界定义

> ⚠️ **归档原因**：本设计基于"运行时 Agent 调用"假设，与 ClaudeCode 实际工作流程不兼容
>
> **ClaudeCode 限制**：
> - Agent 是独立会话，无法嵌套调用
> - 无运行时 Orchestrator 解析 JSON 命令
> - 无强制 Schema 验证机制
>
> **可行替代方案**：参见 [Ideas 模块入口](../README.md)
>
> **归档时间**：2026-01-04

---

> 编号：IDEA-002
> 优先级：P1
> 关联问题：P02（Agent 边界不清晰）

---

## 一、问题回顾

当前多个 Agent 职责重叠：
- feature-shipper 自己做"需求收敛"
- requirement-refiner 也做需求精炼
- code-debug-expert 的调试流程与 feature-shipper 的"失败修复"重叠

导致用户困惑：应该用哪个 Agent？

---

## 二、设计目标

1. 每个 Agent 有明确的**单一职责**
2. 有清晰的**决策树**指导"何时用哪个 Agent"
3. Agent 之间的**边界不重叠**

---

## 三、设计方案

### 3.1 职责矩阵（重新定义）

| Agent | 核心职责 | 输入条件 | 输出物 | 不做什么 |
|-------|---------|---------|--------|---------|
| **requirement-refiner** | 需求精炼 | 模糊需求 | spec.md + DoD | 不写代码、不运行测试 |
| **feature-shipper** | 代码交付 | 明确的 spec/DoD | 可运行代码 + 测试 | 不做需求精炼（必须调用 requirement-refiner） |
| **code-analyzer** | 架构分析 | 代码库路径 | 架构文档 | 不修改代码 |
| **code-debug-expert** | 深度调试 | 失败日志 + 代码 | 根因分析 + 修复建议 | 不做完整交付 |
| **system-log-analyzer** | 日志分析 | 日志文本 | JSON 诊断报告 | 不分析代码逻辑 |

### 3.2 决策树

```
用户输入
   │
   ├─ 是模糊需求？ ───Yes──→ requirement-refiner
   │                           │
   │                           ▼
   │                      输出 spec.md
   │                           │
   ├─ 有明确 spec？ ───Yes──→ feature-shipper
   │                           │
   │                           ├─ Gate 失败？
   │                           │      │
   │                           │      ├─ 简单错误 → 自己修复
   │                           │      │
   │                           │      └─ 复杂问题 → 调用 code-debug-expert
   │                           │
   │                           └─ 需要理解架构？ → 调用 code-analyzer
   │
   ├─ 只是分析代码？ ───Yes──→ code-analyzer
   │
   ├─ 只是分析日志？ ───Yes──→ system-log-analyzer
   │
   └─ 只是调试问题？ ───Yes──→ code-debug-expert
```

### 3.3 边界强制机制

在每个 Agent 的 Prompt 中添加**硬性约束**：

```markdown
## 职责边界（不可违背）

### 我做什么
- [明确列出]

### 我不做什么
- [明确列出]

### 当遇到边界外任务时
输出：
​```json
{
  "action": "BOUNDARY_VIOLATION",
  "requested_task": "用户请求的任务",
  "my_scope": "我的职责范围",
  "suggested_agent": "建议的 Agent",
  "reason": "为什么这不是我的职责"
}
​```
```

---

## 四、feature-shipper 改进方案

### 4.1 移除自带的"需求收敛"

当前 Prompt（第 35 行）：
```markdown
如果用户只给了模糊需求，你先用"需求收敛"把它收敛成可执行的验收标准，再进入实现。
```

改进后：
```markdown
如果用户只给了模糊需求，你必须先调用 requirement-refiner：

​```json
{
  "action": "CALL_SUBAGENT",
  "subagent": "requirement-refiner",
  "input": { "raw_requirement": "..." }
}
​```

只有在获得 spec.md 和明确 DoD 后，才能开始实现。
```

### 4.2 调试边界

当前：feature-shipper 自己做"失败定位修复"

改进后：
```markdown
Gate 失败时：
1. 先尝试自己定位（最多 2 轮）
2. 如果 2 轮内无法解决，必须调用 code-debug-expert：

​```json
{
  "action": "CALL_SUBAGENT",
  "subagent": "code-debug-expert",
  "input": {
    "error_log": "...",
    "failed_test": "...",
    "attempted_fixes": ["..."]
  }
}
​```
```

---

## 五、验收标准

- [ ] 每个 Agent 有明确的"我做什么/我不做什么"声明
- [ ] 有可视化的决策树文档
- [ ] Agent 在遇到边界外任务时，能正确输出 BOUNDARY_VIOLATION
- [ ] feature-shipper 不再自己做需求精炼，必须调用 requirement-refiner

---

## 六、相关文件

- `toolchain/agents/GUIDE.md`（需要添加决策树）
- `toolchain/agents/feature-shipper.md`
- `toolchain/agents/requirement-refiner.md`
- `toolchain/agents/code-debug-expert.md`

---

> 关键改进：从"大而全的中枢"变成"专注交付的执行者 + 明确的 SubAgent 调用"
