# requirement-refiner 改进对比

> 时间：2024-12-31
> 改进范围：IDEA-006 (No Evidence, No Output + Examples as Constraints)
> 文件：`Claude/agents/requirement-refiner.md`
> 优先级：P0（需求精炼是工作流入口，影响最大）

---

## 一、改动统计

| 指标 | 修改前 | 修改后 | 变化 |
|------|-------|-------|------|
| 总行数 | 194 行 | 619 行 | +425 行 (+219%) |
| 工具纪律 | 3 行简述 | 69 行详细规范 | +66 行 |
| 输出格式 | 无结构化输出 | 78 行 JSON Schema | +78 行 |
| 完整示例 | 0 个 | 3 个 JSON 示例 | +281 行 |

---

## 二、核心改进点

### 2.1 工具纪律强化（Layer 1）

#### 改进前（第 10-14 行）

```markdown
## 工具纪律（强制）

- **先查证后输出；先调用再回答**：当用户给出 repo/文档路径时，先用工具查证现有约束/现状...
- **标准步骤**：意图拆解 → 工具调用 → 限制输出边界...
- **长上下文**：把决策落盘到 .autoworkflow/state.md...
```

**问题**：
- 只是"建议"，没有强制检查机制
- 没有明确的"项目现状 vs 用户需求"区分
- 缺少 AskUserQuestion 的强制使用规范

#### 改进后（第 10-69 行）

新增内容：

1. **核心原则声明**（第 12-14 行）
   - 明确 IDEA-006：No Evidence, No Output
   - 强调"项目现状、文件内容、代码逻辑"必须有工具调用证据

2. **铁律表格**（第 16-23 行）
   - 4 种陈述类型及对应工具
   - 特别强调 AskUserQuestion 用于用户需求澄清
   - 用 ❌ 和 ✅ 对比错误/正确做法

3. **输出前自检**（第 25-34 行）
   - 4 个强制检查项
   - 特别关注"假设"和"记忆替代验证"
   - 检查失败 → BLOCKED 输出

4. **禁止的输出模式**（第 36-54 行）
   - 模式1：假设性陈述（"应该有认证模块"）
   - 模式2：记忆替代验证（"之前讨论过"）
   - 模式3：未提问直接推断用户意图

**效果**：
- 从"建议"变成"强制"
- 区分项目现状验证（Read/Grep）和用户需求澄清（AskUserQuestion）
- 有明确的检查步骤和阻断机制

---

### 2.2 结构化输出格式（Layer 2）

#### 改进前

完全没有结构化输出，所有阶段都是自由文本 Markdown。

**问题**：
- 无法机器解析
- "有没有证据"不可检查
- 用户需求和项目现状混淆

#### 改进后（第 252-327 行）

新增内容：

1. **JSON Schema 定义**（第 258-303 行）
   - evidence_summary：记录本轮工具调用（增加 questions_asked 字段）
   - claims：事实陈述列表（项目现状 + 用户需求）
   - evidence：证据详情（支持 AskUserQuestion 类型）
   - result.current_stage：明确当前阶段（1-5）
   - result.stage_output：该阶段的具体输出
   - next_action：下一步行动（CONTINUE | ASK_USER | VERIFY_FIRST | DONE）

2. **人类可读摘要**（第 305-310 行）
   - 保留原有的 Markdown 格式
   - 作为第二部分补充 JSON

3. **强制规则**（第 312-326 行）
   - tool_calls_this_turn = 0 → status 必须 BLOCKED/NEED_INPUT
   - confidence = HIGH → 必须有 evidence_id
   - 违反格式 → 输出 BLOCKED

**效果**：
- 机器可解析 + 人类可读
- evidence_summary.questions_asked 可验证"是否澄清需求"
- claims ↔ evidence 关联使证据可追溯
- current_stage 确保阶段推进的可追踪性

---

### 2.3 "示例即约束"原则（新增）

#### 理论基础（来自 IDEA-006 修订）

```markdown
**原理说明**：
对于复杂的结构化输出（如 JSON Schema、格式化报告），**具体示例**比抽象描述对 LLM 的约束力强 10 倍。

**验证效果**：
- 有完整示例：格式一致性 > 95%，工具调用合规率 > 95%
- 仅抽象描述：格式一致性 < 60%，工具调用合规率 < 70%
```

#### 实施内容（第 330-619 行）

新增 **3 个完整 JSON 示例**，每个示例包含：

1. **示例 1：SUCCESS - 需求澄清成功**（第 334-441 行）
   - 场景：用户说"我想做一个数据分析工具"
   - 工具调用：Read(package.json) + 2 次 AskUserQuestion
   - evidence_summary 记录 3 次调用（2 次提问）
   - claims ↔ evidence 完整关联
   - 包含人类可读摘要（阶段1完成）

2. **示例 2：BLOCKED - 需要更多信息**（第 443-521 行）
   - 场景：用户说"优化系统性能"过于宽泛
   - tool_calls_this_turn = 0
   - blocked_reason 详细说明缺失的信息
   - required_questions 列出需要提问的具体问题
   - next_action: VERIFY_FIRST（先提问澄清）

3. **示例 3：PARTIAL - 范围收缩进行中**（第 523-619 行）
   - 场景：阶段2范围收缩，等待用户确认排除项
   - 工具调用：1 次 AskUserQuestion
   - status: PARTIAL（部分完成）
   - stage_output 包含 must_have 和 nice_to_have_deferred
   - next_action: ASK_USER（确认排除项）

**效果**：
- 从"抽象规范"变成"具体模板"
- 示例覆盖 3 种典型场景（成功、阻断、进行中）
- LLM 可以直接模仿示例结构
- 大幅降低格式偏差风险

---

## 三、预期效果

### 3.1 格式一致性

| 指标 | 改进前 | 改进后（预期） | 提升 |
|------|-------|--------------|------|
| 格式一致性 | 低（自由文本） | 高（>95%） | 质变 |
| 输出可解析性 | 不可解析 | 高（JSON Schema） | 质变 |
| 工具调用合规率 | 低（<60%） | 高（>95%） | +35% |

### 3.2 证据可追溯性

| 指标 | 改进前 | 改进后（预期） | 提升 |
|------|-------|--------------|------|
| 项目现状陈述有证据 | 不可验证 | 可验证（evidence_id） | 质变 |
| 用户需求澄清有证据 | 不可验证 | 可验证（AskUserQuestion） | 质变 |
| 幻觉阻断率 | 高（无约束） | 预期 70-80% | 显著改善 |

### 3.3 需求精炼质量

| 指标 | 改进前 | 改进后（预期） | 影响 |
|------|-------|--------------|------|
| 假设性陈述 | 高 | 低（强制验证） | 需求更准确 |
| 记忆替代验证 | 常见 | 禁止 | 信息更新鲜 |
| 用户需求澄清 | 不充分 | 强制提问 | 范围更清晰 |

---

## 四、待验证问题

### 4.1 LLM 自律程度
- [ ] LLM 会严格执行自检吗？
- [ ] 长对话后会忘记规则吗？
- [ ] 会伪造 evidence_summary.questions_asked 吗？
- [ ] **新增**：会跳过 AskUserQuestion 直接推断用户意图吗？

### 4.2 格式遵循度
- [ ] 能稳定输出 JSON 吗？
- [ ] claims 和 evidence 关联正确吗？
- [ ] current_stage 字段准确反映阶段吗？
- [ ] **新增**：3 个示例是否足够覆盖五阶段流程？

### 4.3 需求精炼效果
- [ ] 是否真的减少假设性陈述？
- [ ] 用户需求澄清是否更充分？
- [ ] 范围收缩是否更合理？
- [ ] **新增**：五阶段流程是否与结构化输出冲突？

### 4.4 "示例即约束"原则验证
- [ ] 格式一致性是否真的达到 >95%？
- [ ] 工具调用合规率是否真的达到 >95%？
- [ ] 示例场景是否需要扩展（如阶段3-5的示例）？
- [ ] LLM 是否会过度模仿示例而缺乏灵活性？

---

## 五、下一步

### 5.1 立即行动（今天）

1. **✅ 已完成**：应用 IDEA-006 到 requirement-refiner.md
2. **⏳ 进行中**：创建对比文档
3. **待执行**：创建 git commit 保存改进

### 5.2 短期计划（本周）

1. **测试新版 Agent**
   - 用真实任务测试 requirement-refiner
   - 观察是否遵循规范（特别是 AskUserQuestion 使用率）
   - 记录违规案例和格式偏差
   - **重点验证**：格式一致性是否 >95%，用户需求澄清是否充分

2. **收集反馈**
   - 用户体验如何？
   - 五阶段流程是否与结构化输出冲突？
   - 示例是否足够清晰？

3. **迭代优化**
   - 根据反馈调整规则
   - 考虑添加阶段3-5的完整示例
   - 评估是否需要简化某些部分

### 5.3 中期计划（本周后期）

4. **继续 P0 Agent 改进**
   - code-debug-expert（诊断过程最容易幻觉）
   - 应用相同的 IDEA-006 原则

5. **评估效果**
   - 统计 requirement-refiner 的实际效果
   - 决定是否调整其他 Agent 的改进策略

---

## 六、改进总结

### 核心突破点

1. **从"建议"到"强制"**（Layer 1）
   - 添加自检清单和禁止模式
   - 明确 BLOCKED 输出机制
   - 区分项目现状验证和用户需求澄清

2. **从"自由文本"到"结构化数据"**（Layer 2）
   - evidence_summary 可验证（增加 questions_asked）
   - claims ↔ evidence 可追溯
   - current_stage 确保阶段推进可追踪

3. **从"抽象规范"到"具体模板"**（示例即约束）
   - 3 个完整 JSON 示例
   - 覆盖成功、阻断、进行中 3 种场景
   - 锚定效应强化约束
   - 预期格式一致性 >95%

### 改进路径

```
原始版本（194 行）
    ↓
+ Layer 1（工具纪律强化）+69 行
    ↓
+ Layer 2（结构化输出）+78 行
    ↓
+ "示例即约束"原则（3 个完整示例）+281 行
    ↓
最终版本（619 行）

总变化：+425 行（+219%），约束强度质变
```

### 特色改进

相比 feature-shipper，requirement-refiner 的特色改进：

1. **AskUserQuestion 的明确强调**
   - 铁律表格中专门列出"用户要求"类型
   - evidence 支持 AskUserQuestion 类型
   - evidence_summary 增加 questions_asked 字段

2. **五阶段流程集成**
   - result.current_stage 明确阶段（1-5）
   - result.stage_output 包含该阶段的具体输出
   - 示例覆盖阶段1（澄清）和阶段2（收缩）

3. **范围收缩的证据链**
   - must_have vs nice_to_have 的区分有用户确认证据
   - exclusions_pending_confirmation 明确待确认项

---

> **备份文件**：`Claude/agents/requirement-refiner.md.backup`
> **完整 diff**：可用 `git diff requirement-refiner.md.backup requirement-refiner.md` 查看
> **改进时间**：2024-12-31
> **基于**：IDEA-006 (No Evidence, No Output + Examples as Constraints)
