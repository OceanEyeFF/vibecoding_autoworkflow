---
title: "Claude Code Agent 设计基线：SubAgent 调用机制"
status: archived
updated: 2026-03-17
owner: aw-kernel
last_verified: 2026-03-17
---
# Claude Code Agent 设计基线：SubAgent 调用机制

> ⚠️ **归档原因**：本设计基于"运行时 Agent 调用"假设，与 ClaudeCode 实际工作流程不兼容
>
> **ClaudeCode 限制**：
> - Agent 是独立会话，无法嵌套调用
> - 无运行时 Orchestrator 解析 JSON 命令
> - 无强制 Schema 验证机制
>
> **可行替代方案**：参见 [归档索引](./README.md)
>
> **归档时间**：2026-01-04

---

> 编号：IDEA-001
> 优先级：P0
> 关联问题：P01（SubAgent 标注缺失）

---

## 一、问题回顾

当前 Agent 定义中只有 `tools:` 字段，没有 `subagents:` 字段，导致：
- Agent 之间**无法真正调用**
- "协作"只是 Prompt 中的文字描述
- 实际执行时 LLM 会自己编造流程

---

## 二、设计目标

1. Agent 可以显式声明"我能调用哪些 SubAgent"
2. 调用时有明确的输入/输出契约
3. Claude Code 运行时能识别并执行 SubAgent 调用

---

## 三、设计方案

### 3.1 YAML Schema 扩展

```yaml
---
name: feature-shipper
description: >
  交付中枢 Agent，负责闭环交付
tools: Read, Grep, Glob, Bash
subagents:
  - name: requirement-refiner
    trigger: "当用户输入模糊需求时"
    input_schema: RequirementInput
    output_schema: RefinedRequirement
  - name: code-debug-expert
    trigger: "当 Gate 失败且根因不清晰时"
    input_schema: DebugInput
    output_schema: DebugReport
  - name: code-analyzer
    trigger: "当需要理解现有代码架构时"
    input_schema: AnalysisInput
    output_schema: ArchitectureReport
---
```

### 3.2 调用协议

```markdown
## SubAgent 调用格式

当需要调用 SubAgent 时，输出：

​```json
{
  "action": "CALL_SUBAGENT",
  "subagent": "requirement-refiner",
  "input": {
    "raw_requirement": "用户的原始需求文本",
    "context": "当前上下文摘要"
  },
  "expected_output": "RefinedRequirement"
}
​```

调用完成后，SubAgent 返回结构化结果，父 Agent 继续处理。
```

### 3.3 运行时行为

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code Runtime                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  feature-shipper 输出 CALL_SUBAGENT                          │
│  → Runtime 识别到调用请求                                     │
│  → 启动 requirement-refiner（独立会话/上下文）                │
│  → 等待返回结果                                              │
│  → 将结果注入 feature-shipper 上下文                          │
│  → feature-shipper 继续执行                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、实现要点

### 4.1 需要验证的假设

- [ ] Claude Code 是否支持自定义 YAML 字段？
- [ ] Claude Code 是否支持运行时解析 Agent 输出并触发新 Agent？
- [ ] 如果不支持，是否需要外部 Orchestrator？

### 4.2 兼容性考虑

- 如果 Claude Code 原生不支持 `subagents:` 字段
- 可以退化为"Prompt 中的指令 + 结构化输出"
- 由用户/外部脚本手动触发 SubAgent

### 4.3 最小可行实现

1. 在 Prompt 中定义 SubAgent 调用格式
2. 当 Agent 输出 `CALL_SUBAGENT` 时，暂停并提示用户
3. 用户手动启动 SubAgent，获取结果后粘贴回来
4. 父 Agent 继续执行

---

## 五、验收标准

- [ ] feature-shipper 可以显式调用 requirement-refiner
- [ ] 调用有明确的输入/输出契约
- [ ] 调用结果可被父 Agent 可靠解析
- [ ] 支持调用链追踪（谁调用了谁）

---

## 六、相关文件

- `toolchain/agents/feature-shipper.md`
- `toolchain/agents/requirement-refiner.md`
- 待创建：`toolchain/schemas/subagent-protocol.json`

---

> 待进一步调研 Claude Code 的运行时能力
