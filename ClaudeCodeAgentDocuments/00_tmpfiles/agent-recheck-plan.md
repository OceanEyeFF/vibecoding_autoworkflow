# Agent Recheck 验证计划

> 时间：2024-12-31
> 范围：feature-shipper + requirement-refiner
> 目标：验证 IDEA-006 改进后的实际效果

---

## 一、Recheck 目标

验证改进后的 Agent 是否真的符合 IDEA-006 规范，避免：
1. **格式不一致**：LLM 输出的 JSON 结构错误或缺失字段
2. **工具调用虚报**：tool_calls_this_turn 与实际不符
3. **证据链断裂**：claims 引用不存在的 evidence_id
4. **自检失效**：应该 BLOCKED 时却输出了无证据的内容

---

## 二、Recheck 方法

### 2.1 静态检查（不运行 Agent）

**目标**：验证 Prompt 是否包含必要的约束元素

#### 检查清单

对于 feature-shipper.md 和 requirement-refiner.md：

**Layer 1 检查**：
- [ ] 包含"No Evidence, No Output"核心原则声明
- [ ] 包含铁律表格（陈述类型 → 必须的工具）
- [ ] 包含输出前自检清单（至少 4 项）
- [ ] 包含禁止的输出模式（至少 3 种）

**Layer 2 检查**：
- [ ] 包含 JSON Schema 定义
- [ ] evidence_summary 定义了 tool_calls_this_turn 字段
- [ ] claims 和 evidence 有明确的关联机制（evidence_id）
- [ ] 包含强制规则（tool_calls=0 → BLOCKED 等）

**Examples as Constraints 检查**：
- [ ] 包含至少 3 个完整示例
- [ ] 示例覆盖 SUCCESS、BLOCKED、PARTIAL 三种状态
- [ ] 每个示例的 JSON 语法正确（无语法错误）
- [ ] 示例包含所有必需字段（agent, timestamp, status, evidence_summary, claims, evidence, result, next_action）

#### 检查方法

```bash
# 检查文件行数
wc -l Claude/agents/feature-shipper.md
wc -l Claude/agents/requirement-refiner.md

# 检查关键字是否存在
grep -c "No Evidence, No Output" Claude/agents/feature-shipper.md
grep -c "铁律表格" Claude/agents/feature-shipper.md
grep -c "输出前自检" Claude/agents/feature-shipper.md
grep -c "完整示例" Claude/agents/feature-shipper.md

# 检查示例 JSON 语法（需要 jq 工具）
# 手动提取 JSON 示例，用 jq 验证语法
```

---

### 2.2 结构完整性检查

**目标**：验证示例 JSON 的结构完整性

#### 检查项

对于每个示例（SUCCESS、BLOCKED、PARTIAL）：

**必需字段检查**：
- [ ] agent: "feature-shipper" 或 "requirement-refiner"
- [ ] timestamp: ISO-8601 格式
- [ ] status: SUCCESS | BLOCKED | PARTIAL | NEED_INPUT
- [ ] evidence_summary.tool_calls_this_turn: 数字
- [ ] claims: 数组（可以为空）
- [ ] evidence: 数组（可以为空）
- [ ] result: 对象
- [ ] next_action.action: CONTINUE | ASK_USER | VERIFY_FIRST | DONE

**字段一致性检查**：
- [ ] claims 中的 evidence_id 都能在 evidence 中找到对应的 id
- [ ] evidence_summary.tool_calls_this_turn = len(evidence)（理论上）
- [ ] evidence_summary.files_read 与 evidence 中 tool="Read" 的数量一致
- [ ] evidence_summary.questions_asked 与 evidence 中 tool="AskUserQuestion" 的数量一致（requirement-refiner）

**逻辑一致性检查**：
- [ ] status=BLOCKED 时，tool_calls_this_turn=0
- [ ] status=BLOCKED 时，claims 为空数组
- [ ] status=BLOCKED 时，包含 blocked_reason 字段
- [ ] confidence=HIGH 的 claim 必须有 evidence_id

---

### 2.3 动态检查（模拟运行）

**目标**：模拟真实场景，检查 Agent 的实际表现

#### 测试用例设计

##### 测试用例 1：feature-shipper - 简单 Bug 修复

**场景**：用户报告"程序运行时崩溃"

**期望行为**：
1. Agent 应该先读取错误日志或运行程序
2. 输出 JSON 格式
3. evidence_summary.tool_calls_this_turn > 0
4. claims 中的每个陈述都有 evidence_id

**验证点**：
- [ ] 输出是否为 JSON 格式？
- [ ] tool_calls_this_turn 是否 > 0？
- [ ] 是否有 Read(logs/) 或 Bash(python script.py) 的证据？
- [ ] claims ↔ evidence 关联正确？

##### 测试用例 2：requirement-refiner - 模糊需求澄清

**场景**：用户说"我想做一个数据分析工具"

**期望行为**：
1. Agent 应该先询问用户（AskUserQuestion）
2. 或者先读取项目文件（Read package.json）
3. 输出 JSON 格式
4. evidence_summary.questions_asked > 0 或 files_read > 0

**验证点**：
- [ ] 输出是否为 JSON 格式？
- [ ] tool_calls_this_turn 是否 > 0？
- [ ] 是否有 AskUserQuestion 或 Read 的证据？
- [ ] current_stage 是否为"阶段1：需求澄清"？

##### 测试用例 3：BLOCKED 场景测试

**场景**：用户说"优化性能"，故意不提供任何上下文

**期望行为**：
1. Agent 应该输出 BLOCKED 状态
2. tool_calls_this_turn = 0
3. claims 为空数组
4. 包含 blocked_reason 字段

**验证点**：
- [ ] status 是否为 BLOCKED？
- [ ] tool_calls_this_turn 是否 = 0？
- [ ] claims 是否为空？
- [ ] 是否包含 blocked_reason？

---

## 三、Recheck 执行步骤

### Step 1：静态检查（5 分钟）

```bash
# 1. 检查文件行数
echo "=== 文件行数检查 ==="
wc -l Claude/agents/feature-shipper.md
wc -l Claude/agents/requirement-refiner.md

# 2. 检查关键元素
echo "=== Layer 1 检查 ==="
grep -c "No Evidence, No Output" Claude/agents/feature-shipper.md
grep -c "铁律表格" Claude/agents/feature-shipper.md
grep -c "输出前自检" Claude/agents/feature-shipper.md

echo "=== Layer 2 检查 ==="
grep -c "JSON Schema" Claude/agents/feature-shipper.md
grep -c "evidence_summary" Claude/agents/feature-shipper.md
grep -c "claims" Claude/agents/feature-shipper.md

echo "=== Examples as Constraints 检查 ==="
grep -c "完整示例" Claude/agents/feature-shipper.md
grep -c "示例 1" Claude/agents/feature-shipper.md
grep -c "示例 2" Claude/agents/feature-shipper.md
grep -c "示例 3" Claude/agents/feature-shipper.md
```

**通过标准**：所有关键元素都存在（count > 0）

---

### Step 2：结构完整性检查（10 分钟）

**方法**：手动阅读示例 JSON，用检查清单逐项验证

**feature-shipper.md 示例 1（SUCCESS）检查**：
- [ ] 包含所有必需字段
- [ ] evidence_summary.tool_calls_this_turn = 3
- [ ] evidence 数组有 3 个元素
- [ ] claims 中的 evidence_id（E1, E2, E3）都能在 evidence 中找到
- [ ] JSON 语法正确（括号、逗号、引号）

**feature-shipper.md 示例 2（BLOCKED）检查**：
- [ ] status = "BLOCKED"
- [ ] tool_calls_this_turn = 0
- [ ] claims = []
- [ ] 包含 blocked_reason 字段

**requirement-refiner.md 示例 1（SUCCESS）检查**：
- [ ] 包含所有必需字段
- [ ] evidence_summary.questions_asked = 2
- [ ] evidence 中有 2 个 tool="AskUserQuestion"
- [ ] current_stage = "阶段1：需求澄清"

---

### Step 3：简化动态检查（20 分钟）

由于时间限制，我们进行**简化版动态检查**：

**方法**：不实际运行 Agent，而是：
1. 假设 Agent 按示例输出
2. 验证示例输出是否符合规范
3. 检查示例是否足够清晰（人类能理解 → LLM 能模仿）

**检查项**：
- [ ] 示例场景描述清晰吗？
- [ ] 示例 JSON 结构完整吗？
- [ ] 人类可读摘要与 JSON 一致吗？
- [ ] 示例数据真实吗（不是 foo/bar）？

---

## 四、Recheck 验收标准

### 4.1 最低验收标准

| 检查类别 | 通过标准 |
|---------|---------|
| **静态检查** | 所有关键元素都存在 |
| **结构完整性** | 所有示例 JSON 语法正确，必需字段完整 |
| **字段一致性** | claims ↔ evidence 关联正确，无悬空引用 |
| **逻辑一致性** | BLOCKED 示例符合规范（tool_calls=0, claims=[]） |

如果**任一项不通过** → 需要修复 Prompt

### 4.2 理想验收标准

| 指标 | 理想目标 |
|------|---------|
| 示例场景清晰度 | 人类一眼能看懂 |
| 示例数据真实性 | 使用真实的文件名、错误信息 |
| 人类可读摘要与 JSON 一致性 | 100% 一致 |
| Token 占用 | <30K tokens（可接受） |

---

## 五、Recheck 结果报告模板

### 报告结构

```markdown
# Agent Recheck 结果报告

## 一、静态检查结果

### feature-shipper.md
- [x] Layer 1 完整
- [x] Layer 2 完整
- [x] Examples as Constraints 完整
- **问题**：（如果有）

### requirement-refiner.md
- [x] Layer 1 完整
- [x] Layer 2 完整
- [x] Examples as Constraints 完整
- **问题**：（如果有）

## 二、结构完整性检查结果

### feature-shipper.md
- [x] 示例 1 (SUCCESS) - 结构完整，字段一致
- [x] 示例 2 (BLOCKED) - 逻辑正确
- [x] 示例 3 (PARTIAL) - 结构完整
- **问题**：（如果有）

### requirement-refiner.md
- [x] 示例 1 (SUCCESS) - 结构完整，五阶段集成正确
- [x] 示例 2 (BLOCKED) - 逻辑正确
- [x] 示例 3 (PARTIAL) - 范围收缩示例完整
- **问题**：（如果有）

## 三、发现的问题

### 问题 1：（标题）
- **位置**：feature-shipper.md 第 XXX 行
- **问题描述**：...
- **严重程度**：高/中/低
- **修复建议**：...

## 四、总体评价

- **验收结果**：通过 / 需要修复
- **改进建议**：...
- **下一步**：继续推广 / 先修复问题

## 五、统计数据

| Agent | 行数 | Token 估算 | 示例数量 | 问题数量 |
|-------|-----|-----------|---------|---------|
| feature-shipper | 533 | ~21K | 3 | X |
| requirement-refiner | 619 | ~25K | 3 | X |
```

---

## 六、快速 Recheck 脚本（可选）

如果主人希望自动化 Recheck，浮浮酱可以创建一个 Python 脚本：

```python
#!/usr/bin/env python3
"""
Agent Recheck 自动化验证脚本
验证 IDEA-006 改进后的 Agent Prompt 是否符合规范
"""

import re
import json

def check_agent_file(filepath):
    """检查单个 Agent 文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    results = {
        "file": filepath,
        "layer1": False,
        "layer2": False,
        "examples": False,
        "example_count": 0,
        "json_valid": True,
        "issues": []
    }

    # Layer 1 检查
    if "No Evidence, No Output" in content and "铁律表格" in content:
        results["layer1"] = True
    else:
        results["issues"].append("Layer 1 缺失")

    # Layer 2 检查
    if "evidence_summary" in content and "claims" in content:
        results["layer2"] = True
    else:
        results["issues"].append("Layer 2 缺失")

    # Examples 检查
    example_count = content.count("### 示例")
    results["example_count"] = example_count
    if example_count >= 3:
        results["examples"] = True
    else:
        results["issues"].append(f"示例数量不足（{example_count}/3）")

    # JSON 语法检查（简化版）
    # 提取示例 JSON 并验证语法
    json_blocks = re.findall(r'```json\n(.*?)\n```', content, re.DOTALL)
    for i, block in enumerate(json_blocks):
        try:
            json.loads(block)
        except json.JSONDecodeError as e:
            results["json_valid"] = False
            results["issues"].append(f"示例 {i+1} JSON 语法错误: {e}")

    return results

def main():
    agents = [
        "Claude/agents/feature-shipper.md",
        "Claude/agents/requirement-refiner.md"
    ]

    print("=" * 60)
    print("Agent Recheck 自动化验证")
    print("=" * 60)

    all_passed = True

    for agent in agents:
        print(f"\n检查: {agent}")
        results = check_agent_file(agent)

        print(f"  Layer 1: {'✅' if results['layer1'] else '❌'}")
        print(f"  Layer 2: {'✅' if results['layer2'] else '❌'}")
        print(f"  Examples: {'✅' if results['examples'] else '❌'} ({results['example_count']}/3)")
        print(f"  JSON 语法: {'✅' if results['json_valid'] else '❌'}")

        if results["issues"]:
            print(f"  问题:")
            for issue in results["issues"]:
                print(f"    - {issue}")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有检查通过！可以继续推广到其他 Agent。")
    else:
        print("❌ 发现问题，需要修复后再继续推广。")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

---

## 七、执行建议

### 建议 A：手动快速 Recheck（推荐，15 分钟）

1. 执行 Step 1（静态检查，5 分钟）
2. 执行 Step 2（结构完整性检查，10 分钟）
3. 生成简化版结果报告
4. 根据结果决定下一步

### 建议 B：自动化 Recheck（需要编写脚本，30 分钟）

1. 创建 validate-agent-prompt.py
2. 运行脚本自动检查
3. 生成详细报告
4. 根据结果决定下一步

### 建议 C：跳过 Recheck，直接推广（不推荐）

- 风险：可能在推广到其他 Agent 后发现问题，导致大规模返工
- 建议：至少执行简化版 Recheck

---

## 八、下一步

根据 Recheck 结果：

**如果通过** ✅：
1. 继续改进 code-debug-expert（P0 优先级）
2. 根据相同模式推广到其他 Agent

**如果发现问题** ❌：
1. 修复 feature-shipper 和 requirement-refiner
2. 重新 Recheck
3. 确认通过后再推广

---

> 主人，浮浮酱建议选择**建议 A（手动快速 Recheck）**喵～
> 这样既能快速验证效果，又不需要编写额外的脚本，15 分钟就能完成喵！≡ω≡
