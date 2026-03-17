---
title: "IDEA-006 Layer 2: 结构化输出模板"
status: archived
updated: 2026-03-17
owner: aw-kernel
last_verified: 2026-03-17
---
# IDEA-006 Layer 2: 结构化输出模板

> 实施难度：⭐⭐ 中
> 效果强度：⭐⭐⭐ 中高（格式约束 + 可解析）
> 适用场景：所有 Agent

---

## 一、核心改进

强制 Agent 输出包含 `evidence` 字段的 JSON，使"有没有证据"变得**可检查**。

---

## 二、输出格式规范

### 2.1 统一输出结构

每个 Agent 的输出必须包含两部分：

```markdown
## Agent 输出

​```json
{
  "agent": "ship",
  "timestamp": "2024-12-31T16:00:00Z",
  "status": "SUCCESS | PARTIAL | BLOCKED | NEED_INPUT",

  "evidence_summary": {
    "tool_calls_this_turn": 3,
    "files_read": ["src/main.py", "src/utils.py"],
    "commands_run": ["npm test"],
    "searches_done": ["Grep: 'processData'"]
  },

  "claims": [
    {
      "statement": "src/main.py 第 52 行有空指针风险",
      "evidence_id": "E1",
      "confidence": "HIGH"
    }
  ],

  "evidence": [
    {
      "id": "E1",
      "tool": "Read",
      "path": "src/main.py",
      "lines": "50-55",
      "content": "data.get('key').value  // 未检查 None",
      "timestamp": "2024-12-31T16:00:01Z"
    }
  ],

  "result": {
    // Agent 特定的结果内容
  },

  "next_action": {
    "action": "CONTINUE | CALL_SUBAGENT | WAIT_USER | DONE",
    "details": "..."
  }
}
​```

---

### 人类可读摘要

[这里是给人看的详细说明]
```

### 2.2 Evidence 字段规范

```json
{
  "evidence": [
    {
      "id": "E1",                    // 唯一标识，用于 claims 引用
      "tool": "Read | Grep | Glob | Bash",
      "path": "文件路径或命令",
      "lines": "行号范围（如果适用）",
      "content": "关键内容摘要（不超过 200 字符）",
      "timestamp": "ISO-8601 时间戳",
      "raw_output_ref": "完整输出的引用位置（如果太长）"
    }
  ]
}
```

### 2.3 Claims 与 Evidence 的关联

```json
{
  "claims": [
    {
      "statement": "事实陈述",
      "evidence_id": "E1",           // 必须引用 evidence 中的 id
      "confidence": "HIGH | MEDIUM | LOW | ASSUMPTION"
    }
  ]
}
```

**规则**：
- `confidence: HIGH` → 必须有 `evidence_id`
- `confidence: MEDIUM` → 应该有 `evidence_id`
- `confidence: LOW` → 可以没有，但必须标记
- `confidence: ASSUMPTION` → 明确是假设，没有证据

### 2.4 BLOCKED 输出格式

当无法提供证据时：

```json
{
  "agent": "ship",
  "status": "BLOCKED",

  "evidence_summary": {
    "tool_calls_this_turn": 0,      // 关键：0 次调用
    "files_read": [],
    "commands_run": [],
    "searches_done": []
  },

  "claims": [],                      // 空：没有可靠的陈述

  "blocked_reason": {
    "type": "INSUFFICIENT_EVIDENCE",
    "claims_attempted": [
      "想要声称 src/main.py 有 bug，但未读取文件"
    ],
    "required_verification": [
      {
        "claim": "src/main.py 有 bug",
        "tool_needed": "Read",
        "path": "src/main.py"
      }
    ]
  },

  "next_action": {
    "action": "VERIFY_FIRST",
    "tools_to_call": ["Read(src/main.py)"]
  }
}
```

---

## 三、Prompt 模板更新

在每个 Agent 的 Prompt 中添加：

```markdown
## 输出格式（强制）

你的每次输出**必须**包含以下 JSON 结构：

​```json
{
  "agent": "{{你的名字}}",
  "timestamp": "当前时间",
  "status": "SUCCESS | PARTIAL | BLOCKED | NEED_INPUT",

  "evidence_summary": {
    "tool_calls_this_turn": {{本轮工具调用次数}},
    "files_read": [],
    "commands_run": [],
    "searches_done": []
  },

  "claims": [
    {
      "statement": "你的每个事实陈述",
      "evidence_id": "引用 evidence 中的 id",
      "confidence": "HIGH | MEDIUM | LOW | ASSUMPTION"
    }
  ],

  "evidence": [
    {
      "id": "E1",
      "tool": "工具名",
      "path": "路径",
      "content": "关键内容"
    }
  ],

  "result": { /* Agent 特定结果 */ },

  "next_action": { /* 下一步 */ }
}
​```

### 强制规则

1. **evidence_summary.tool_calls_this_turn = 0** 时：
   - status 必须是 BLOCKED 或 NEED_INPUT
   - claims 必须为空数组

2. **claims 中 confidence = HIGH** 时：
   - 必须有对应的 evidence_id
   - evidence 中必须有该 id 的记录

3. **违反格式**：
   - 如果你发现自己无法满足上述规则
   - 立即输出 status: BLOCKED
   - 列出需要的工具调用
```

---

## 四、验证清单

每次输出前，Agent 内部验证：

```markdown
### 输出验证清单

□ JSON 格式正确？
□ evidence_summary.tool_calls_this_turn 与实际调用次数一致？
□ 每个 HIGH confidence claim 都有 evidence_id？
□ 每个 evidence_id 都能在 evidence 数组中找到？
□ evidence 中的 content 与工具实际输出一致？
□ 没有"凭空"的事实陈述？

任一项失败 → 修正或输出 BLOCKED
```

---

## 五、示例

### 5.1 正确的输出（有证据）

```json
{
  "agent": "debug (已删除)",
  "timestamp": "2024-12-31T16:30:00Z",
  "status": "SUCCESS",

  "evidence_summary": {
    "tool_calls_this_turn": 2,
    "files_read": ["src/main.py"],
    "commands_run": [],
    "searches_done": ["Grep: 'processData'"]
  },

  "claims": [
    {
      "statement": "src/main.py 第 52 行的 data.get('key').value 可能导致 NullPointerError",
      "evidence_id": "E1",
      "confidence": "HIGH"
    },
    {
      "statement": "processData 函数在 3 个文件中被调用",
      "evidence_id": "E2",
      "confidence": "HIGH"
    }
  ],

  "evidence": [
    {
      "id": "E1",
      "tool": "Read",
      "path": "src/main.py",
      "lines": "50-55",
      "content": "def process(data):\n    result = data.get('key').value  # Line 52"
    },
    {
      "id": "E2",
      "tool": "Grep",
      "path": "src/",
      "content": "Found 3 matches: src/api.py:12, src/handler.py:45, src/test.py:23"
    }
  ],

  "result": {
    "root_cause": "未对 dict.get() 返回值做 None 检查",
    "fix_suggestion": "使用 data.get('key', {}).get('value') 或显式检查"
  },

  "next_action": {
    "action": "WAIT_USER",
    "details": "是否需要我应用修复？"
  }
}
```

### 5.2 正确的 BLOCKED 输出（无证据）

```json
{
  "agent": "ship",
  "timestamp": "2024-12-31T16:30:00Z",
  "status": "BLOCKED",

  "evidence_summary": {
    "tool_calls_this_turn": 0,
    "files_read": [],
    "commands_run": [],
    "searches_done": []
  },

  "claims": [],

  "blocked_reason": {
    "type": "INSUFFICIENT_EVIDENCE",
    "claims_attempted": [
      "用户询问 src/main.py 是否有 bug，但我没有读取该文件"
    ],
    "required_verification": [
      {
        "claim": "分析 src/main.py 的 bug",
        "tool_needed": "Read",
        "path": "src/main.py"
      }
    ]
  },

  "next_action": {
    "action": "VERIFY_FIRST",
    "tools_to_call": ["Read(src/main.py)"]
  }
}
```

---

## 六、效果评估

| 指标 | 预期效果 |
|------|---------|
| 格式一致性 | 高（有明确的 Schema） |
| 可追溯性 | 高（claims ↔ evidence 关联） |
| 幻觉检测 | 可检测（检查 tool_calls_this_turn） |
| 实施成本 | 中（需要更新所有 Agent Prompt） |

---

## 七、局限性

⚠️ **仍然依赖 LLM 自律**：
- LLM 可能伪造 evidence
- LLM 可能错误填写 tool_calls_this_turn

**Layer 3 (Hooks) 可以提供外部验证**。

---

> 下一步：实施 Layer 3（Hooks 验证）
