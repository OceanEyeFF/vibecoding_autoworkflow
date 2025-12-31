# feature-shipper 试点改进对比

> 时间：2024-12-31
> 改进范围：IDEA-006 Layer 1 + Layer 2
> 文件：`Claude/agents/feature-shipper.md`

---

## 一、改动统计

| 指标 | 修改前 | 修改后 | 变化 |
|------|-------|-------|------|
| 总行数 | 235 行 | 399 行 | +164 行 (+70%) |
| 工具纪律 | 1 行简述 | 82 行详细规范 | +81 行 |
| 输出格式 | 15 行 Markdown 模板 | 96 行结构化规范 | +81 行 |

---

## 二、核心改进点

### 2.1 工具纪律强化（Layer 1）

#### 改进前（第 25 行）
```markdown
- 工具纪律：**先查证后输出；先调用再回答**。能用工具确认的内容先查证，
  输出必须带证据（文件路径/命令/关键日志行）；长上下文中间产物写入
  `.autoworkflow/state.md` 或 `.autoworkflow/tmp/feature-shipper-notes.md`，
  对话只保留摘要与引用。
```

**问题**：
- 只是"建议"，没有强制机制
- 没有具体的检查步骤
- 没有违反后的处理方式

#### 改进后（第 219-299 行）

新增内容：

1. **铁律表格**（第 225-231 行）
   - 明确 5 种陈述类型及对应工具
   - 用 ❌ 和 ✅ 对比错误/正确做法

2. **输出前自检**（第 233-242 行）
   - 4 个强制检查项
   - 每次输出前必须执行

3. **BLOCKED 输出格式**（第 244-265 行）
   - 检查失败时的标准输出
   - 包含 failed_checks、claims_without_evidence、required_tool_calls

4. **禁止的输出模式**（第 267-299 行）
   - 5 种具体的禁止模式
   - 每种都有错误示例 + 正确做法

**效果**：
- 从"建议"变成"强制"
- 有明确的检查步骤和阻断机制
- LLM 有清晰的行为边界

---

### 2.2 输出格式结构化（Layer 2）

#### 改进前（第 219-235 行）
```markdown
## 输出格式（默认）

​```markdown
## 目标与验收标准
- ...

## 实施计划（3–7 项）
1. ...

## 进展与验证
- [x] 任务1：...（验证：...）
- [ ] 任务2：...

## 交付说明
- 验证命令：...
- 变更摘要：...
​```
```

**问题**：
- 纯 Markdown 自由文本
- 无法机器解析
- "有没有证据"不可检查

#### 改进后（第 303-399 行）

新增内容：

1. **结构化 JSON 输出**（第 307-366 行）
   - evidence_summary：记录本轮工具调用
   - claims：事实陈述列表
   - evidence：证据详情（与 claims 关联）
   - result：Agent 特定结果
   - next_action：下一步行动

2. **人类可读摘要**（第 368-384 行）
   - 保留原有的 Markdown 格式
   - 作为第二部分补充

3. **强制规则**（第 386-399 行）
   - tool_calls_this_turn = 0 → status 必须 BLOCKED
   - confidence = HIGH → 必须有 evidence_id
   - 违反格式 → 输出 BLOCKED

**效果**：
- 机器可解析 + 人类可读
- evidence_summary.tool_calls_this_turn 可验证"有没有调用工具"
- claims ↔ evidence 关联使证据可追溯

---

## 三、示例对比

### 3.1 正确的输出（符合新规范）

```json
{
  "agent": "feature-shipper",
  "timestamp": "2024-12-31T16:40:00Z",
  "status": "SUCCESS",

  "evidence_summary": {
    "tool_calls_this_turn": 2,
    "files_read": ["src/main.py"],
    "commands_run": ["npm test"],
    "searches_done": []
  },

  "claims": [
    {
      "statement": "src/main.py 第 52 行有空指针风险",
      "evidence_id": "E1",
      "confidence": "HIGH"
    },
    {
      "statement": "测试全部通过",
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
      "content": "data.get('key').value  // 未检查 None"
    },
    {
      "id": "E2",
      "tool": "Bash",
      "path": "npm test",
      "content": "All tests passed (5/5)"
    }
  ],

  "result": {
    "goal": "修复空指针 bug",
    "tasks": [...]
  },

  "next_action": {
    "action": "DONE"
  }
}
```

### 3.2 BLOCKED 输出（无证据时）

```json
{
  "agent": "feature-shipper",
  "timestamp": "2024-12-31T16:40:00Z",
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
    "claims_without_evidence": [
      "用户询问 src/main.py 是否有 bug，但我没有读取该文件"
    ],
    "required_tool_calls": [
      "Read(src/main.py)"
    ]
  },

  "next_action": {
    "action": "VERIFY_FIRST",
    "tools_to_call": ["Read(src/main.py)"]
  }
}
```

---

## 四、预期效果

| 指标 | 改进前 | 改进后（预期） |
|------|-------|--------------|
| 幻觉输出率 | 高（无约束） | 中低（50-70% 减少） |
| 证据可追溯性 | 低（自由文本） | 高（claims ↔ evidence） |
| 输出可解析性 | 低（Markdown） | 高（JSON Schema） |
| 违规检测 | 不可能 | 可能（检查 tool_calls_this_turn） |

---

## 五、待验证问题

### 5.1 LLM 自律程度
- [ ] LLM 会严格执行自检吗？
- [ ] 长对话后会忘记规则吗？
- [ ] 会伪造 evidence_summary 吗？

### 5.2 格式遵循度
- [ ] 能稳定输出 JSON 吗？
- [ ] claims 和 evidence 关联正确吗？
- [ ] BLOCKED 输出格式正确吗？

### 5.3 实用性
- [ ] 规范会不会过于繁琐？
- [ ] 是否需要简化某些部分？
- [ ] 是否需要添加更多示例？

---

## 六、下一步

1. **测试新版 Agent**
   - 用真实任务测试
   - 观察是否遵循规范
   - 记录违规案例

2. **收集反馈**
   - 用户体验如何？
   - 是否有误报 BLOCKED？
   - 格式是否清晰？

3. **迭代优化**
   - 根据反馈调整规则
   - 简化过于复杂的部分
   - 添加更多示例

4. **推广到其他 Agent**
   - requirement-refiner
   - code-debug-expert
   - code-analyzer

---

> 备份文件：`Claude/agents/feature-shipper.md.backup`
> 可用 `git diff feature-shipper.md.backup feature-shipper.md` 查看完整 diff
