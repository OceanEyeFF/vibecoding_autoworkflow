---
title: "Claude Code Agent 设计基线：结构化交互协议"
status: archived
updated: 2026-03-22
owner: aw-kernel
last_verified: 2026-03-22
---
# Claude Code Agent 设计基线：结构化交互协议

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

> 编号：IDEA-004
> 优先级：P1
> 关联问题：P04（交互格式不明确）

---

## 一、问题回顾

当前 Agent 的输出格式：
- 大多数是 Markdown 自由文本
- 只有 system-log-analyzer 有 JSON Schema
- Agent 之间传递信息时无法可靠解析

导致：
- 下游 Agent 无法自动提取上游输出
- 协作依赖 LLM"理解"，而非结构化解析

---

## 二、设计目标

1. 定义统一的 Agent 交互协议
2. 所有 Agent 输出遵循相同的 Schema
3. 支持机器可解析 + 人类可读

---

## 三、设计方案

### 3.1 统一输出 Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AgentOutput",
  "type": "object",
  "required": ["agent", "timestamp", "status", "result"],
  "properties": {
    "agent": {
      "type": "string",
      "description": "输出此结果的 Agent 名称"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "status": {
      "type": "string",
      "enum": ["SUCCESS", "PARTIAL", "FAILED", "BLOCKED", "NEED_INPUT"]
    },
    "result": {
      "type": "object",
      "description": "Agent 特定的输出内容"
    },
    "next_action": {
      "type": "object",
      "properties": {
        "action": {
          "type": "string",
          "enum": ["CONTINUE", "CALL_SUBAGENT", "WAIT_USER", "PERMISSION_REQUEST", "DONE"]
        },
        "target": { "type": "string" },
        "input": { "type": "object" }
      }
    },
    "evidence": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": { "type": "string", "enum": ["file", "command", "log"] },
          "path": { "type": "string" },
          "content": { "type": "string" }
        }
      }
    },
    "human_readable": {
      "type": "string",
      "description": "人类可读的摘要（可选）"
    }
  }
}
```

### 3.2 各 Agent 的 Result Schema

#### requirement-refiner

```json
{
  "type": "object",
  "properties": {
    "core_value": { "type": "string" },
    "atomic_tasks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "integer" },
          "description": { "type": "string" },
          "priority": { "type": "string", "enum": ["must-have", "nice-to-have"] }
        }
      }
    },
    "scope": {
      "type": "object",
      "properties": {
        "included": { "type": "array", "items": { "type": "string" } },
        "excluded": { "type": "array", "items": { "type": "string" } }
      }
    },
    "steps": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "step": { "type": "integer" },
          "task": { "type": "string" },
          "deliverable": { "type": "string" },
          "estimated_effort": { "type": "string" }
        }
      }
    }
  }
}
```

#### feature-shipper

```json
{
  "type": "object",
  "properties": {
    "goal": { "type": "string" },
    "acceptance_criteria": {
      "type": "array",
      "items": { "type": "string" }
    },
    "tasks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "integer" },
          "description": { "type": "string" },
          "status": { "type": "string", "enum": ["pending", "in_progress", "done", "failed"] },
          "files_changed": { "type": "array", "items": { "type": "string" } },
          "verification": { "type": "string" }
        }
      }
    },
    "gate_result": {
      "type": "object",
      "properties": {
        "status": { "type": "string", "enum": ["PASS", "FAIL", "NOT_RUN"] },
        "build": { "type": "string" },
        "test": { "type": "string" },
        "lint": { "type": "string" }
      }
    }
  }
}
```

#### code-debug-expert

```json
{
  "type": "object",
  "properties": {
    "design_intent": { "type": "string" },
    "error_diagnosis": {
      "type": "object",
      "properties": {
        "error_type": { "type": "string" },
        "root_cause": { "type": "string" },
        "evidence": { "type": "array", "items": { "type": "string" } }
      }
    },
    "fix_proposal": {
      "type": "object",
      "properties": {
        "pseudocode": { "type": "string" },
        "language_specific": {
          "type": "object",
          "additionalProperties": { "type": "string" }
        }
      }
    },
    "prevention": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

### 3.3 输出格式规范

每个 Agent 必须输出：

```markdown
## Agent 输出

​```json
{
  "agent": "feature-shipper",
  "timestamp": "2024-12-31T16:00:00Z",
  "status": "SUCCESS",
  "result": {
    // Agent 特定内容
  },
  "next_action": {
    "action": "DONE"
  },
  "evidence": [
    { "type": "file", "path": "src/main.py", "content": "..." }
  ],
  "human_readable": "完成了用户认证功能的实现，所有测试通过。"
}
​```

---

### 人类可读摘要

[这里是给人看的详细说明，可以用 Markdown 格式]
```

### 3.4 Prompt 模板改进

在每个 Agent 的 Prompt 中添加：

```markdown
## 输出格式（强制）

你的每次输出必须包含一个 JSON 代码块，遵循 AgentOutput Schema：

​```json
{
  "agent": "{{agent_name}}",
  "timestamp": "ISO-8601 格式",
  "status": "SUCCESS | PARTIAL | FAILED | BLOCKED | NEED_INPUT",
  "result": {
    // 根据你的 Agent 类型填充
  },
  "next_action": {
    "action": "CONTINUE | CALL_SUBAGENT | WAIT_USER | PERMISSION_REQUEST | DONE",
    "target": "如果是 CALL_SUBAGENT，填写目标 Agent",
    "input": {}
  },
  "evidence": [
    // 你的结论依据
  ],
  "human_readable": "一句话摘要"
}
​```

如果你没有按此格式输出，你的响应将被视为无效。
```

---

## 四、实现路径

### 阶段 1：定义 Schema
- 创建 `toolchain/schemas/agent-output.json`
- 创建各 Agent 的 Result Schema

### 阶段 2：更新 Agent Prompt
- 在每个 Agent 中添加输出格式强制要求
- 添加示例输出

### 阶段 3：验证工具
- 创建 Schema 验证脚本
- 在 Gate 中添加输出格式检查

---

## 五、验收标准

- [ ] 所有 Agent 输出遵循统一 Schema
- [ ] 有机器可解析的 JSON 部分
- [ ] 有人类可读的摘要部分
- [ ] Agent 之间可以可靠解析彼此的输出

---

## 六、相关文件

- 待创建：`toolchain/schemas/agent-output.json`
- 待创建：`toolchain/schemas/requirement-refiner-result.json`
- 待创建：`toolchain/schemas/feature-shipper-result.json`
- 待创建：`toolchain/schemas/code-debug-expert-result.json`

---

> 核心思想：机器可解析 + 人类可读，两者兼得
