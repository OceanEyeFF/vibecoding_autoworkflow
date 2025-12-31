# Agent 改进路线图 - 基于 IDEA-006 推广

> 生成时间：2024-12-31
> 基于：feature-shipper 试点成功经验
> 原则：No Evidence, No Output + Examples as Constraints

---

## 一、改进优先级

### P0 优先级（本周完成）

| Agent | 优先级理由 | 预计行数变化 | 示例类型 |
|-------|----------|------------|---------|
| **requirement-refiner** | 1. 需求精炼是工作流入口，影响最大<br>2. 当前无结构化输出，完全自由文本<br>3. P06 问题：没有强制"先访问数据" | 200 → 450 (+125%) | 需求澄清对话 + 精炼结果 + BLOCKED |
| **code-debug-expert** | 1. 诊断过程最容易产生幻觉<br>2. 当前无证据链，推理过程不可追溯<br>3. P06 问题：推断替代验证 | 180 → 420 (+133%) | 诊断成功 + 诊断失败 + 部分诊断 |

### P1 优先级（下周完成）

| Agent | 优先级理由 | 预计行数变化 | 示例类型 |
|-------|----------|------------|---------|
| **code-analyzer** | 1. 分析结果需要结构化<br>2. 当前 JSON 输出但无 evidence 字段<br>3. P06 问题：假设性搜索 | 250 → 500 (+100%) | 架构分析 + 依赖分析 + BLOCKED |
| **system-log-analyzer** | 1. 已有 JSON 输出，改进成本低<br>2. 需要添加 evidence 字段<br>3. 日志分析容易产生臆测 | 150 → 320 (+113%) | 日志诊断 + 错误定位 + 无日志 |

### P2 优先级（按需）

| Agent | 优先级理由 | 预计行数变化 | 示例类型 |
|-------|----------|------------|---------|
| **code-project-cleaner** | 1. 操作简单，幻觉风险低<br>2. 主要是文件操作，工具调用强制性高 | 120 → 250 (+108%) | 清理成功 + 危险操作 |
| **stage-development-executor** | 1. 执行型 Agent，依赖明确<br>2. 已有较好的阶段划分 | 160 → 340 (+113%) | 阶段执行 + 失败恢复 |

---

## 二、改进模板设计

### 2.1 requirement-refiner 示例场景

**场景设定**：用户说"我想做一个数据分析工具"

**示例 1：SUCCESS - 需求精炼成功**
```json
{
  "agent": "requirement-refiner",
  "status": "SUCCESS",
  "evidence_summary": {
    "tool_calls_this_turn": 2,
    "files_read": ["README.md", "package.json"],
    "questions_asked": 3
  },
  "claims": [
    {
      "statement": "项目已有 pandas 和 matplotlib 依赖",
      "evidence_id": "E1",
      "confidence": "HIGH"
    },
    {
      "statement": "用户确认需要 CSV 导入功能",
      "evidence_id": "E2",
      "confidence": "HIGH"
    }
  ],
  "evidence": [
    {
      "id": "E1",
      "tool": "Read",
      "path": "package.json",
      "content": "dependencies: {pandas: ^1.5.0, matplotlib: ^3.6.0}"
    },
    {
      "id": "E2",
      "tool": "AskUserQuestion",
      "content": "用户回答：是的，需要支持 CSV 和 Excel"
    }
  ],
  "result": {
    "refined_requirements": [
      {
        "id": "REQ-001",
        "description": "CSV/Excel 文件导入",
        "acceptance_criteria": [
          "支持上传 CSV 和 Excel 文件",
          "自动检测文件编码",
          "显示前 10 行预览"
        ],
        "evidence_ids": ["E1", "E2"]
      }
    ]
  },
  "next_action": {
    "action": "DONE",
    "details": "需求已精炼为 3 个可执行的验收标准"
  }
}
```

**示例 2：BLOCKED - 需要更多信息**
```json
{
  "agent": "requirement-refiner",
  "status": "BLOCKED",
  "evidence_summary": {
    "tool_calls_this_turn": 0,
    "files_read": [],
    "questions_asked": 0
  },
  "claims": [],
  "blocked_reason": {
    "type": "INSUFFICIENT_INFORMATION",
    "missing_info": [
      "用户说'数据分析工具'过于宽泛",
      "需要明确：分析什么数据？数据来源？输出格式？"
    ],
    "required_questions": [
      "你要分析什么类型的数据（财务、销售、日志等）？",
      "数据来源是什么（CSV、数据库、API）？",
      "需要什么样的分析结果（图表、报告、仪表板）？"
    ]
  },
  "next_action": {
    "action": "ASK_USER",
    "questions": ["你要分析什么类型的数据？", "..."]
  }
}
```

---

### 2.2 code-debug-expert 示例场景

**场景设定**：用户报告"程序运行崩溃"

**示例 1：SUCCESS - 诊断成功**
```json
{
  "agent": "code-debug-expert",
  "status": "SUCCESS",
  "evidence_summary": {
    "tool_calls_this_turn": 4,
    "files_read": ["src/main.py", "logs/error.log"],
    "commands_run": ["python src/main.py"],
    "searches_done": ["Grep: 'NullPointerError'"]
  },
  "claims": [
    {
      "statement": "程序在 main.py:52 抛出 AttributeError",
      "evidence_id": "E1",
      "confidence": "HIGH"
    },
    {
      "statement": "错误原因是 data 为 None 时调用 .value",
      "evidence_id": "E2",
      "confidence": "HIGH"
    },
    {
      "statement": "processData 函数在 3 处被调用",
      "evidence_id": "E3",
      "confidence": "HIGH"
    }
  ],
  "evidence": [
    {
      "id": "E1",
      "tool": "Bash",
      "path": "python src/main.py",
      "content": "AttributeError: 'NoneType' object has no attribute 'value'\n  File 'src/main.py', line 52, in processData"
    },
    {
      "id": "E2",
      "tool": "Read",
      "path": "src/main.py",
      "lines": "50-55",
      "content": "def processData(data):\n    result = data.get('key').value  # Line 52\n    return result"
    },
    {
      "id": "E3",
      "tool": "Grep",
      "path": "src/",
      "content": "Found 3 matches: src/api.py:12, src/handler.py:45, src/test.py:23"
    }
  ],
  "result": {
    "diagnosis": {
      "root_cause": "data.get('key') 返回 None 时未做检查",
      "error_type": "NullPointerError",
      "affected_files": ["src/main.py"],
      "affected_functions": ["processData"]
    },
    "fix_suggestions": [
      {
        "approach": "防御性检查",
        "code": "value = data.get('key')\nif value is None:\n    raise ValueError('Missing key')\nresult = value.value",
        "pros": "显式错误信息",
        "cons": "需要调用方处理异常"
      },
      {
        "approach": "安全访问",
        "code": "result = data.get('key', {}).get('value', default_value)",
        "pros": "简洁，不会崩溃",
        "cons": "可能隐藏问题"
      }
    ]
  },
  "next_action": {
    "action": "WAIT_USER",
    "details": "诊断完成，等待用户选择修复方案"
  }
}
```

**示例 2：BLOCKED - 缺少错误日志**
```json
{
  "agent": "code-debug-expert",
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
    "missing_info": [
      "用户说'程序崩溃'但未提供错误日志",
      "需要查看实际错误信息才能诊断"
    ],
    "required_tool_calls": [
      "Read(logs/error.log) 或要求用户提供错误堆栈"
    ]
  },
  "next_action": {
    "action": "VERIFY_FIRST",
    "tools_to_call": ["Read(logs/error.log)"]
  }
}
```

---

## 三、实施计划

### Week 1（本周）

**Day 1-2：requirement-refiner**
- [ ] 添加 Layer 1 工具纪律（自检清单 + 禁止模式）
- [ ] 添加 Layer 2 结构化输出（evidence_summary + claims + evidence）
- [ ] 添加 3 个完整示例（SUCCESS + BLOCKED + PARTIAL）
- [ ] 更新对比文档
- [ ] Git commit

**Day 3-4：code-debug-expert**
- [ ] 添加 Layer 1 工具纪律
- [ ] 添加 Layer 2 结构化输出
- [ ] 添加 3 个完整示例（诊断成功 + 诊断失败 + 部分诊断）
- [ ] 更新对比文档
- [ ] Git commit

**Day 5：测试验证**
- [ ] 用真实任务测试 requirement-refiner
- [ ] 用真实任务测试 code-debug-expert
- [ ] 记录格式一致性、工具调用合规率
- [ ] 收集问题和改进点

---

### Week 2（下周）

**Day 1-2：code-analyzer**
- [ ] 改进现有 JSON 输出
- [ ] 添加 evidence 字段
- [ ] 添加 3 个完整示例
- [ ] Git commit

**Day 3-4：system-log-analyzer**
- [ ] 改进现有 JSON 输出
- [ ] 添加 evidence 字段
- [ ] 添加 3 个完整示例
- [ ] Git commit

**Day 5：总体评估**
- [ ] 统计所有 Agent 的改进效果
- [ ] 评估是否需要 Layer 3（Hooks 验证）
- [ ] 编写最终改进报告

---

## 四、成功指标

### 定量指标

| 指标 | 目标 | 验证方法 |
|------|------|---------|
| 格式一致性 | >95% | 10 次测试中 ≥9 次输出符合 JSON Schema |
| 工具调用合规率 | >95% | 10 次测试中 ≥9 次有 tool_calls_this_turn > 0 |
| 幻觉阻断率 | >70% | 无证据时正确输出 BLOCKED 状态 |
| 证据链完整性 | 100% | 所有 HIGH confidence claim 都有 evidence_id |

### 定性指标

- [ ] 输出格式稳定，无需反复修正
- [ ] 工具调用符合"先验证后输出"原则
- [ ] 示例足够清晰，LLM 能正确模仿
- [ ] 长对话后仍然遵循规范

---

## 五、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Token 消耗过大 | Prompt 过长 | 精简重复示例，保留 2-3 个典型场景 |
| 示例过于僵化 | LLM 缺乏灵活性 | 示例覆盖多种场景（成功、失败、部分） |
| 改进成本过高 | 难以推广 | 从 P0 优先级开始，逐步推广 |
| 效果不达预期 | 幻觉率仍高 | 考虑启用 Layer 3 Hooks 验证 |

---

## 六、输出文件

每个 Agent 改进后都会生成：

```
Claude/agents/{agent-name}.md           # 更新后的 Agent Prompt
Claude/agents/{agent-name}.md.backup    # 改进前的备份
ClaudeCodeAgentDocuments/00_tmpfiles/{agent-name}-comparison.md  # 对比文档
```

最终汇总：

```
ClaudeCodeAgentDocuments/00_tmpfiles/all-agents-improvement-summary.md
```

---

> 下一步：开始 requirement-refiner 的改进
