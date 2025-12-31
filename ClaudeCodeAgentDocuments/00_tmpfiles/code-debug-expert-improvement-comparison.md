# code-debug-expert 改进对比

> 时间：2024-12-31
> 改进范围：IDEA-006 Layer 1 + Layer 2 + "示例即约束"原则
> 文件：`Claude/agents/code-debug-expert.md`

---

## 一、改动统计

### 1.1 总体改进

| 指标 | 原始版本 | 最终版本 | 总变化 |
|------|---------|---------|-------|
| 总行数 | 111 行 | 645 行 | +534 行 (+481%) |
| 工具纪律 | 3 行简述 | 62 行详细规范 | +59 行 |
| 输出格式 | 无结构化格式 | 83 行结构化规范 | +83 行 |
| 完整示例 | 0 个 | 3 个完整 JSON 示例 | +389 行 |
| 约束强度 | 弱（建议） | 强（强制 + 示例锚定） | 质变 |

---

## 二、核心改进点

### 2.1 工具纪律强化（Layer 1）

#### 改进前（第 10-14 行）

```markdown
## 工具纪律（强制）

- **先查证后输出；先调用再回答**：能通过工具（`Read/Grep/Glob/Bash`）确认的点，必须先查证再下结论；无法查证就明确"不确定/需要更多信息"，并列出最小补充信息。
- **标准步骤**：意图拆解 → 工具调用（先定位再细读/复现）→ 限制输出边界 → 提纯信息 → 限制噪声 → 输出（结论 + 证据 + 下一步）。
- **长上下文**：把关键错误行、复现命令、定位到的文件路径与结论写入 `.autoworkflow/state.md` 或 `.autoworkflow/tmp/code-debug-expert-notes.md`，对话只保留摘要与引用。
```

**问题**：
- 只是"建议"，没有强制机制
- 没有具体的检查步骤
- 没有违反后的处理方式

#### 改进后（第 10-76 行）

新增内容：

1. **核心原则声明**（第 12-14 行）
   ```markdown
   ### 核心原则：No Evidence, No Output

   遵循 IDEA-006 强制规范：**任何涉及代码内容、错误原因、运行结果的陈述,必须有本轮工具调用证据**。
   ```

2. **铁律表格**（第 16-23 行）
   ```markdown
   | 陈述类型 | 必须的工具调用 | 示例 |
   |---------|--------------|------|
   | "代码在X行有Y错误" | Read(文件) | ❌ "应该是空指针错误" → ✅ Read(src/main.py, lines 50-55) |
   | "程序崩溃/抛出异常" | Bash(运行命令) | ❌ "可能会崩溃" → ✅ Bash('python main.py') |
   | "函数在N处被调用" | Grep(搜索模式) | ❌ "应该有多处调用" → ✅ Grep('function_name') |
   | "这个模块/库存在" | Glob 或 Read(配置文件) | ❌ "项目应该有X依赖" → ✅ Read(package.json) |
   ```

3. **输出前自检**（第 25-34 行）
   ```markdown
   □ **检查1**：我的每个关于"错误原因"的陈述都有本轮工具调用结果吗？
   □ **检查2**：我有没有假设某段代码的行为而没有读取验证？
   □ **检查3**：我有没有引用"之前对话"的错误信息而没有重新验证？
   □ **检查4**：我复现错误了吗？还是只是推测？
   ```

4. **禁止的输出模式**（第 36-60 行）
   - 4 种具体的禁止模式
   - 每种都有错误示例 + 正确做法
   - 特别针对调试场景（推断替代读取、假设性错误复现、臆测调用关系）

**效果**：
- 从"建议"变成"强制"
- 有明确的检查步骤和阻断机制
- 针对调试场景的特殊约束

---

### 2.2 输出格式结构化（Layer 2）

#### 改进前（第 70-110 行）

```markdown
## 🎯 输出规范

### 语言适配原则
- 根据用户提供的代码语言，自动调整解释风格和技术术语
- 如果语言未知，使用语言无关的伪代码 + 多语言示例
- 保持专业性，避免使用过于复杂的语言特性

### 表达方式
- 使用清晰的段落结构和要点列表
- 避免过度技术化的术语，必要时提供简单解释
- 包含实用的代码示例（如果是伪代码则保持抽象）

### 质量标准
- 确保每个建议都有明确的理由和实施指导
- 提供可操作的步骤，而非抽象概念
- 平衡详细性和可读性
```

**问题**：
- 纯自由文本输出
- 无法机器解析
- "有没有证据"不可检查

#### 改进后（第 157-242 行）

新增内容：

1. **结构化 JSON 输出**（第 165-218 行）
   ```json
   {
     "agent": "code-debug-expert",
     "status": "SUCCESS | PARTIAL | BLOCKED",

     "evidence_summary": {
       "tool_calls_this_turn": 0,
       "files_read": [],
       "commands_run": [],
       "searches_done": []
     },

     "claims": [
       {
         "statement": "事实陈述（关于错误原因或代码行为）",
         "evidence_id": "E1",
         "confidence": "HIGH | MEDIUM | LOW | ASSUMPTION"
       }
     ],

     "evidence": [
       {
         "id": "E1",
         "tool": "Read | Grep | Glob | Bash",
         "path": "文件路径或命令",
         "lines": "行号范围（如适用）",
         "content": "关键内容摘要"
       }
     ],

     "result": {
       "diagnosis": {
         "error_type": "错误类型",
         "root_cause": "根本原因描述",
         "affected_files": [],
         "affected_functions": []
       },
       "fix_suggestions": [
         {
           "approach": "修复方案名称",
           "code": "伪代码或关键代码片段",
           "pros": "优点",
           "cons": "缺点"
         }
       ]
     },

     "next_action": {
       "action": "WAIT_USER | CONTINUE | VERIFY_FIRST | DONE",
       "details": "下一步行动描述"
       }
   }
   ```

2. **code-debug-expert 特有字段**（第 196-211 行）
   - `diagnosis`：诊断结果（error_type, root_cause, affected_files, affected_functions）
   - `fix_suggestions`：修复方案列表（approach, code, pros, cons）
   - 相比 feature-shipper 和 requirement-refiner，更关注错误诊断和修复方案

3. **人类可读摘要**（第 220-225 行）
   - 保留原有的 Markdown 格式
   - 作为第二部分补充

4. **强制规则**（第 227-242 行）
   - tool_calls_this_turn = 0 → status 必须 BLOCKED
   - confidence = HIGH → 必须有 evidence_id
   - 违反格式 → 输出 BLOCKED

**效果**：
- 机器可解析 + 人类可读
- evidence_summary 可验证"有没有调用工具"
- claims ↔ evidence 关联使证据可追溯
- diagnosis 和 fix_suggestions 专为调试场景设计

---

### 2.3 "示例即约束"原则（新增）

#### 理论基础（来自 IDEA-006 修订）

```markdown
**原理说明**：
对于复杂的结构化输出（如 JSON Schema、格式化报告），**具体示例**比抽象描述对 LLM 的约束力强 10 倍。

**核心机制**：
- LLM 通过**模式匹配**学习任务要求
- 具体示例提供了**强锚点**（Anchoring Effect）
- 抽象描述容易被 LLM "自由发挥"
- 完整示例确保输出格式的**一致性和稳定性**

**验证效果**：
- 有完整示例：格式一致性 > 95%，工具调用合规率 > 95%
- 仅抽象描述：格式一致性 < 60%，工具调用合规率 < 70%
```

#### 实施内容（第 245-643 行）

新增 **3 个完整 JSON 示例**，每个示例包含：

1. **示例 1：SUCCESS 输出**（第 249-445 行）
   - 场景：用户报告"程序运行崩溃"
   - 完整工作流程：Read 代码 → Bash 复现 → Grep 搜索调用 → 诊断完成
   - evidence_summary 记录 4 次工具调用
   - 4 个 claims 对应 4 个 evidence（E1-E4）
   - diagnosis 包含 error_type, root_cause, affected_files, affected_functions
   - 3 个 fix_suggestions（防御性检查、安全访问、类型注解）
   - 包含完整的人类可读摘要（Markdown 格式，带文件链接）

2. **示例 2：BLOCKED 输出**（第 447-521 行）
   - 场景：用户说"程序崩溃"但未提供错误日志
   - tool_calls_this_turn = 0
   - claims = []
   - blocked_reason 详细说明缺失的信息
   - required_tool_calls 列出需要的工具
   - 包含人类可读摘要（引导用户提供信息）

3. **示例 3：PARTIAL 输出**（第 523-642 行）
   - 场景：发现一个错误，但需要继续验证
   - tool_calls_this_turn = 2
   - 包含测试失败的真实场景
   - next_action 指示 CONTINUE（需要继续工作）
   - 包含人类可读摘要（显示进度）

**效果**：
- 从"抽象规范"变成"具体模板"
- LLM 可以直接模仿示例结构
- 大幅降低格式偏差风险
- 调试场景的真实性强（空指针错误、类型检查错误）

---

## 三、差异化设计（与其他 Agent 对比）

### 3.1 evidence_summary 字段

| Agent | 字段 | 说明 |
|-------|------|------|
| feature-shipper | files_read, commands_run, searches_done | 通用字段 |
| requirement-refiner | + questions_asked | 增加提问次数 |
| **code-debug-expert** | **与 feature-shipper 相同** | **调试也需要读取、运行、搜索** |

**设计合理性**：✅ 调试场景与 feature-shipper 类似，都需要读取代码、运行程序、搜索引用

### 3.2 result 字段

| Agent | 字段 | 说明 |
|-------|------|------|
| feature-shipper | goal, tasks, verification | 实施计划 |
| requirement-refiner | current_stage, stage_output | 5 阶段工作流 |
| **code-debug-expert** | **diagnosis, fix_suggestions** | **诊断结果 + 修复方案** |

**设计合理性**：✅ 专为调试场景设计，包含错误类型、根本原因、受影响文件、修复方案

### 3.3 示例场景

| Agent | 示例场景 | 真实性 |
|-------|---------|--------|
| feature-shipper | Bug 修复（空指针在 src/main.py） | ✅ 真实 |
| requirement-refiner | 需求澄清（数据分析工具） | ✅ 真实 |
| **code-debug-expert** | **空指针错误、类型检查错误** | **✅ 真实且常见** |

**设计合理性**：✅ 选择了最常见的调试场景（空指针、类型检查），贴近实际使用

---

## 四、示例对比

### 4.1 正确的输出（符合新规范）

```json
{
  "agent": "code-debug-expert",
  "timestamp": "2024-12-31T21:00:00Z",
  "status": "SUCCESS",

  "evidence_summary": {
    "tool_calls_this_turn": 4,
    "files_read": ["src/main.py"],
    "commands_run": ["python src/main.py"],
    "searches_done": ["Grep: 'processData'"]
  },

  "claims": [
    {
      "statement": "程序在 src/main.py:52 抛出 AttributeError",
      "evidence_id": "E1",
      "confidence": "HIGH"
    },
    {
      "statement": "错误原因是 data.get('key') 返回 None 时未做检查",
      "evidence_id": "E2",
      "confidence": "HIGH"
    }
  ],

  "evidence": [
    {
      "id": "E1",
      "tool": "Bash",
      "path": "python src/main.py",
      "content": "AttributeError: 'NoneType' object has no attribute 'value'\\n  File 'src/main.py', line 52, in processData"
    },
    {
      "id": "E2",
      "tool": "Read",
      "path": "src/main.py",
      "lines": "50-55",
      "content": "def processData(data):\\n    result = data.get('key').value  # Line 52\\n    return result"
    }
  ],

  "result": {
    "diagnosis": {
      "error_type": "AttributeError (NullPointerError)",
      "root_cause": "data.get('key') 返回 None 时未做检查,直接调用 .value 属性",
      "affected_files": ["src/main.py", "src/api.py", "src/handler.py", "src/test.py"],
      "affected_functions": ["processData"]
    },
    "fix_suggestions": [
      {
        "approach": "防御性检查（推荐）",
        "code": "value = data.get('key')\\nif value is None:\\n    raise ValueError('Missing required key')\\nresult = value.value",
        "pros": "显式错误信息,便于调试",
        "cons": "需要调用方处理异常"
      }
    ]
  },

  "next_action": {
    "action": "WAIT_USER",
    "details": "诊断完成,等待用户选择修复方案"
  }
}
```

### 4.2 BLOCKED 输出（无证据时）

```json
{
  "agent": "code-debug-expert",
  "timestamp": "2024-12-31T21:00:00Z",
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
      "用户说'程序崩溃'但未提供错误日志或错误信息",
      "需要查看实际错误信息才能诊断"
    ],
    "required_tool_calls": [
      "Bash(运行程序) 或用户提供错误堆栈",
      "Read(错误日志文件) 如果有日志"
    ]
  },

  "next_action": {
    "action": "VERIFY_FIRST",
    "tools_to_call": [
      "Bash('python src/main.py') 或等待用户提供错误信息"
    ]
  }
}
```

---

## 五、预期效果

### 5.1 定量预期

| 指标 | 改进前 | 改进后（预期） | 提升 |
|------|-------|--------------|------|
| 格式一致性 | 低（<60%） | 高（>95%） | +35% |
| 工具调用合规率 | 低（<70%） | 高（>95%） | +25% |
| 证据可追溯性 | 低（自由文本） | 高（claims ↔ evidence） | 质变 |
| 输出可解析性 | 低（Markdown） | 高（JSON Schema） | 质变 |
| 幻觉阻断率 | 无机制 | 预期 70-80% | 从无到有 |

### 5.2 定性预期

| 维度 | 改进前 | 改进后 |
|------|-------|-------|
| **约束强度** | 弱（建议） | 强（强制 + 示例锚定） |
| **诊断流程** | 不明确 | 明确（Read → Bash → Grep → 诊断） |
| **修复方案** | 自由文本 | 结构化（approach, code, pros, cons） |
| **证据链** | 无 | 有（claims ↔ evidence） |
| **示例清晰度** | 无示例 | 3 个完整示例 |

### 5.3 特有改进

| 改进点 | 说明 |
|-------|------|
| **铁律表格针对调试** | 明确"代码在X行有Y错误"必须有 Read 调用 |
| **禁止推断替代读取** | ❌ "应该是空指针错误" → ✅ Read + 确认 |
| **禁止假设性错误复现** | ❌ "应该会崩溃" → ✅ Bash 实际运行 |
| **diagnosis 字段** | 包含 error_type, root_cause, affected_files, affected_functions |
| **fix_suggestions 多方案** | 每个方案都有 pros/cons，帮助用户选择 |

---

## 六、待验证问题

### 6.1 LLM 自律程度
- [ ] LLM 会严格执行自检吗？（特别是"我复现错误了吗？"）
- [ ] 长对话后会忘记规则吗？
- [ ] 会伪造 evidence_summary 吗？
- [ ] 示例锚定效应在长对话后是否衰减？

### 6.2 格式遵循度
- [ ] 能稳定输出 JSON 吗？
- [ ] claims 和 evidence 关联正确吗？
- [ ] diagnosis 和 fix_suggestions 字段格式正确吗？
- [ ] BLOCKED 输出格式正确吗？
- [ ] 3 个示例是否足够覆盖所有调试场景？

### 6.3 实用性
- [ ] fix_suggestions 的 pros/cons 是否有帮助？
- [ ] diagnosis 字段是否过于复杂？
- [ ] 示例场景是否贴近实际使用？
- [ ] 是否需要添加更多边缘场景示例（如并发问题、内存泄漏等）？

### 6.4 "示例即约束"原则验证
- [ ] 格式一致性是否真的达到 >95%？
- [ ] 工具调用合规率是否真的达到 >95%？
- [ ] 示例中的"真实数据"是否足够贴近实际调试场景？
- [ ] 调试场景的特殊性（如需要复现错误）是否在示例中充分体现？

---

## 七、下一步

### 7.1 立即行动（今天）

1. **✅ 已完成**：应用 IDEA-006 到 code-debug-expert.md
2. **⏳ 进行中**：创建对比文档
3. **待执行**：创建 git commit 保存改进

### 7.2 短期计划（本周）

1. **测试新版 Agent**
   - 用真实调试任务测试 code-debug-expert
   - 观察是否遵循规范（特别是是否真的运行代码复现错误）
   - 记录违规案例和格式偏差
   - **重点验证**：格式一致性是否 >95%

2. **收集反馈**
   - 用户体验如何？
   - diagnosis 和 fix_suggestions 是否有用？
   - 示例是否足够清晰？

3. **迭代优化**
   - 根据反馈调整规则
   - 根据实际使用调整示例内容

### 7.3 中期计划（下周）

4. **推广到其他 Agent**
   - code-analyzer（重点在结构分析）
   - system-log-analyzer（重点在日志分析）
   - 每个 Agent 设计适合其职责的完整示例

5. **评估 Layer 3 必要性**
   - 观察 Layer 1+2+示例 的实际效果
   - 如果幻觉率 <10%，Layer 3 可能不必要
   - 如果仍有问题，考虑部署 Hooks 验证

---

## 八、改进总结

### 核心突破点

1. **从"建议"到"强制"**（Layer 1）
   - 添加自检清单和禁止模式
   - 明确 BLOCKED 输出机制
   - 特别针对调试场景（推断替代读取、假设性错误复现）

2. **从"自由文本"到"结构化数据"**（Layer 2）
   - evidence_summary 可验证
   - claims ↔ evidence 可追溯
   - diagnosis 和 fix_suggestions 专为调试设计

3. **从"抽象规范"到"具体模板"**（示例即约束）
   - 3 个完整 JSON 示例
   - 锚定效应强化约束
   - 预期格式一致性 >95%

### 改进路径

```
原始版本（111 行）
    ↓
+ Layer 1 + Layer 2 + "示例即约束"（645 行，+534 行）
    ↓
总变化：+534 行（+481%），约束强度质变
```

### 与其他 Agent 的对比

| Agent | 行数变化 | 特有字段 | 示例场景 |
|-------|---------|---------|---------|
| feature-shipper | 235 → 533 (+127%) | goal, tasks | Bug 修复 |
| requirement-refiner | 194 → 619 (+219%) | questions_asked, current_stage | 需求澄清 |
| **code-debug-expert** | **111 → 645 (+481%)** | **diagnosis, fix_suggestions** | **空指针错误、类型检查错误** |

**观察**：code-debug-expert 的行数增幅最大（+481%），因为原始版本最精简（只有 111 行），改进空间最大。

---

> **备份文件**：`Claude/agents/code-debug-expert.md.backup`
> **完整 diff**：可用 `git diff code-debug-expert.md.backup code-debug-expert.md` 查看
> **修订历史**：
> - 2024-12-31：应用 IDEA-006 Layer 1 + Layer 2 + "示例即约束"原则
