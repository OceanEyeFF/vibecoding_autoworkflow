# Claude Code Agent 设计基线：强制数据访问机制

> 编号：IDEA-006
> 优先级：P0
> 关联问题：P06（Prompt 没有强制"先访问数据"）

---

## 一、问题回顾

当前问题：
- 所有 Agent 都声明了"先查证后输出"
- 但这只是文字建议，没有强制机制
- LLM 很容易"偷懒"，直接编造答案
- 基于被污染的上下文输出不可靠结论

---

## 二、设计目标

1. 从"建议"变成"强制"
2. 没有工具调用就不能输出结论
3. 有明确的检查点和阻断机制
4. 可验证、可审计

---

## 三、设计方案

### 3.1 核心原则：No Evidence, No Output

#### 补充原则：示例即约束（Examples as Constraints）

**原理说明**：

对于复杂的结构化输出（如 JSON Schema、格式化报告），**具体示例**比抽象描述对 LLM 的约束力强 10 倍。

**核心机制**：
- LLM 通过**模式匹配**学习任务要求
- 具体示例提供了**强锚点**（Anchoring Effect）
- 抽象描述容易被 LLM "自由发挥"
- 完整示例确保输出格式的**一致性和稳定性**

**实践指南**：

| 场景 | 错误做法 ❌ | 正确做法 ✅ |
|------|-----------|-----------|
| JSON 输出 | "输出必须包含 status、evidence、claims 字段" | 提供完整 JSON 示例（含所有字段、嵌套结构、枚举值） |
| 错误处理 | "出错时输出 BLOCKED 状态" | 提供完整 BLOCKED 状态 JSON 示例（含所有必需字段） |
| 格式约束 | "使用 Markdown 格式" | 提供完整 Markdown 模板（含章节标题、列表格式） |
| 工具纪律 | "必须先调用工具再输出" | 提供禁止模式的对比示例（错误示例 vs 正确示例） |

**Token 优化权衡**：
- ⚠️ **不推荐删除**：JSON 输出模板、BLOCKED 状态示例、证据链示例
- ✅ **可以精简**：多个重复的反模式示例（保留 1-2 个典型示例即可）
- ⚠️ **谨慎删除**：自检清单（Self-verification 是强制机制的关键）

**验证效果**：
```
有完整示例：格式一致性 > 95%，工具调用合规率 > 95%
仅抽象描述：格式一致性 < 60%，工具调用合规率 < 70%
```

---

```markdown
## 数据访问强制原则（DAEP - Data Access Enforcement Principle）

任何涉及以下内容的输出，必须有对应的工具调用证据：

| 输出类型 | 必须的证据 | 示例 |
|---------|-----------|------|
| 文件存在/不存在 | Glob 或 Read 调用 | "src/main.py 存在" |
| 文件内容描述 | Read 调用 | "这个函数的逻辑是..." |
| 代码搜索结果 | Grep 调用 | "找到 5 处调用" |
| 命令执行结果 | Bash 调用 | "测试通过" |
| 目录结构描述 | Glob 调用 | "src/ 下有 10 个文件" |

如果没有对应的工具调用，必须输出：

​```json
{
  "status": "BLOCKED",
  "reason": "INSUFFICIENT_EVIDENCE",
  "missing_verification": ["需要读取 src/main.py 确认"],
  "next_action": {
    "action": "VERIFY_FIRST",
    "tools_to_call": ["Read(src/main.py)"]
  }
}
​```
```

### 3.2 检查点设计

在 Agent Prompt 中添加强制检查点：

```markdown
## 输出前检查清单（强制执行）

在生成任何结论之前，你必须检查：

### 检查点 1：证据完整性
- [ ] 我的每个事实陈述都有对应的工具调用结果吗？
- [ ] 我有没有"假设"某个文件存在而没有验证？
- [ ] 我有没有"假设"某段代码的行为而没有读取？

### 检查点 2：上下文验证
- [ ] 我引用的信息是来自本轮工具调用，还是来自之前的对话？
- [ ] 如果是之前的对话，那些信息现在还准确吗？
- [ ] 项目状态可能已经变化，我需要重新验证吗？

### 检查点 3：输出分类
- [ ] 这是事实陈述（需要证据）还是推理分析（可以基于已验证事实）？
- [ ] 如果是事实陈述，证据在哪里？

### 如果任一检查失败

输出 BLOCKED 状态并列出需要验证的内容。
```

### 3.3 证据链追踪

每个输出必须包含证据链：

```json
{
  "agent": "feature-shipper",
  "status": "SUCCESS",
  "result": {
    "statement": "src/main.py 中的 process_data 函数有一个 bug",
    "evidence_chain": [
      {
        "claim": "src/main.py 存在",
        "tool": "Read",
        "call_id": "read_001",
        "result_summary": "成功读取 150 行"
      },
      {
        "claim": "process_data 函数定义在第 45-60 行",
        "tool": "Grep",
        "call_id": "grep_001",
        "result_summary": "找到函数定义"
      },
      {
        "claim": "函数第 52 行有空指针风险",
        "tool": "Read",
        "call_id": "read_002",
        "result_summary": "读取第 45-65 行，发现 data.get() 后直接访问属性"
      }
    ]
  }
}
```

### 3.4 禁止的输出模式

在 Prompt 中明确禁止：

```markdown
## 禁止的输出模式

以下输出模式是**严格禁止**的：

### 1. 凭空陈述文件内容
❌ "根据 src/main.py 的实现..."（如果本轮没有 Read 调用）
✅ 先调用 Read(src/main.py)，然后引用具体行号

### 2. 假设性搜索结果
❌ "代码库中应该有类似的实现..."
✅ 先调用 Grep 或 Glob，然后报告实际结果

### 3. 记忆替代验证
❌ "之前我们讨论过这个文件..."（然后直接使用旧信息）
✅ "让我重新验证一下这个文件的当前状态"，然后调用工具

### 4. 推断替代读取
❌ "根据文件名推断，这应该是..."
✅ 读取文件内容，然后描述实际内容

### 违反后果
如果你发现自己违反了上述任何模式：
1. 立即停止输出
2. 输出 BLOCKED 状态
3. 列出需要验证的内容
4. 等待工具调用完成后再继续
```

### 3.5 自检脚本

Agent 在输出前运行自检：

```markdown
## 输出前自检（内部执行）

在最终输出之前，运行以下自检逻辑：

​```pseudocode
function self_check_before_output(output):
    # 提取所有事实陈述
    claims = extract_factual_claims(output)

    for claim in claims:
        # 检查是否有对应证据
        evidence = find_evidence_for_claim(claim, tool_calls_this_turn)

        if evidence is None:
            # 没有证据，阻断输出
            return {
                "status": "BLOCKED",
                "reason": "CLAIM_WITHOUT_EVIDENCE",
                "claim": claim,
                "suggested_verification": suggest_tool_call(claim)
            }

    # 所有陈述都有证据，允许输出
    return { "status": "PASS" }
​```
```

---

## 四、实现路径

### 阶段 1：更新 Prompt
- 在每个 Agent 中添加检查点
- 添加禁止的输出模式清单
- 添加 BLOCKED 输出格式

### 阶段 2：添加证据链要求
- 在输出 Schema 中添加 evidence_chain 字段
- 更新输出格式模板

### 阶段 3：外部验证（可选）
- 创建验证脚本，检查 Agent 输出是否有对应的工具调用
- 在 CI 中添加验证步骤

---

## 五、验收标准

- [ ] 每个 Agent 都有强制检查点
- [ ] 有明确的"禁止输出模式"清单
- [ ] 输出必须包含 evidence_chain
- [ ] 没有证据时输出 BLOCKED 而非编造

---

## 六、相关文件

- 待修改：所有 `toolchain/agents/*.md`
- 待创建：`toolchain/schemas/evidence-chain.json`
- 待添加：`toolchain/agents/assets/templates/tool-discipline-strict.md`

---

> 核心思想：No Evidence, No Output —— 没有证据就不输出
