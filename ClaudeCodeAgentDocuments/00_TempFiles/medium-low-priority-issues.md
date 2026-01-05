# 中低优先级问题清单

> **创建日期**: 2026-01-05
> **整理人**: 浮浮酱 (猫娘工程师)
> **关联**: 基于完整项目检查发现的遗留问题

---

## 📊 问题概览

| 等级 | 数量 | 说明 |
|------|------|------|
| ⚠️ Medium | 8 | 功能增强、鲁棒性改进 |
| 💡 Low | 2 | 文档优化、示例改进 |
| **总计** | **10** | 可渐进式修复 |

---

## ⚠️ Medium 优先级问题 (8个)

### Issue #1: Git 回退失败处理不完善

**问题描述**：
`/autodev` SKILL.md 中定义了多层回路机制（Level 1/2 需要 Git 回退），但没有考虑以下情况：
- 项目没有 Git 仓库
- 没有 commit 历史（新项目）
- 工作区有未提交的重要更改

**当前行为**：
```bash
# Level 1 回退
git checkout ${task_start_commit}
# 如果没有 commit 历史，此命令会失败
```

**影响**：
- 在新项目或非 Git 项目中，回路机制完全失效
- 可能丢失重要的工作进度

**建议修复**：
1. 在 Phase 2 开始前检查 Git 状态
2. 如果没有 commit 历史，改用 `git stash` 或文件备份
3. 添加 Git 回退前的安全检查：
   ```bash
   # 检查是否有 commit 历史
   if ! git rev-parse HEAD 2>/dev/null; then
     echo "无 commit 历史，使用 stash 作为回退机制"
     # 改用 stash 策略
   fi
   ```

**修复位置**：
- `Claude/skills/aw-kernel/autodev/SKILL.md`
- Phase 2 检查点创建部分（第 382-397 行）
- Level 1/2 回退逻辑（第 451-468 行）

**优先级理由**：Medium
- 影响新项目和非标准工作流
- 但大多数项目有 Git 历史，不阻塞主流程

---

### Issue #2: 指令刷新机制在长对话中可能失效

**问题描述**：
`/autodev` 的指令刷新机制依赖"重新阅读本 Skill 的相关章节"，但在 Claude 的上下文管理中：
- 超长对话可能触发自动摘要
- 摘要可能丢失 SKILL.md 的详细内容
- 仅依靠"内部回忆"可能不准确

**当前实现**（第 275-283 行）：
```
内部执行（不需要读取外部文件，重新阅读本 Skill 的相关章节）：
1. 重新确认当前 Phase 定义
2. 重新确认当前 Gate 检查项
3. 重新确认回路处理规则
```

**潜在问题**：
- "重新阅读本 Skill" 在长对话后可能只是回忆摘要
- 关键细节（如 Gate 检查项）可能遗漏

**建议修复**：
1. 将关键指令提取为独立的"指令卡片"
2. 在刷新时显式使用 Read 工具重新读取 SKILL.md
3. 或者将核心指令内联到每个 Phase 的开头
   ```bash
   # 指令刷新改为显式读取
   Read("Claude/skills/aw-kernel/autodev/SKILL.md", offset=65, limit=30)
   # 读取"状态机定义"和"Gate 定义"章节
   ```

**修复位置**：
- `Claude/skills/aw-kernel/autodev/SKILL.md` 第 267-283 行
- 指令刷新机制章节

**优先级理由**：Medium
- 仅在极长对话中出现
- 有一定风险但可通过用户干预规避

---

### Issue #4: 调试失败后续协议不完整

**问题描述**：
`feature-shipper.md` 定义了"调试失败处理"（第 122-136 行），但只描述了输出格式，没有后续动作：

**当前内容**：
```markdown
## 调试受阻

**问题**：[描述]
**已尝试**：
1. 方法1 - 结果
2. 方法2 - 结果
3. 方法3 - 结果

**需要帮助**：请提供更多上下文或指导方向
```

**缺失内容**：
- 用户提供帮助后，如何恢复执行？
- 是否需要回退代码？
- 如何记录调试历史？

**建议修复**：
添加"调试恢复协议"：
```markdown
### 调试恢复协议

用户提供指导后：
1. 更新任务理解：根据用户反馈调整实现方案
2. 代码状态决策：
   - 保留当前更改：在现有基础上继续
   - 回退后重试：git checkout 恢复到任务开始前
3. 重新执行任务，retry 计数器重置为 0
4. 输出恢复确认：
   ```
   ✅ 根据主人的指导，浮浮酱重新理解了任务
   新方案：[描述]
   代码状态：[保留/已回退]
   现在开始重新实现...
   ```
```

**修复位置**：
- `Claude/agents/aw-kernel/feature-shipper.md` 第 122-136 行

**优先级理由**：Medium
- 改善用户体验，但不阻塞核心功能
- 当前用户可以手动引导

---

### Issue #6: /autodev 未明确何时委派 requirement-refiner

**问题描述**：
新增的 Agent 委派机制定义了触发条件（第 730-736 行）：
```
| 需求模糊 | Phase 1 问答超过 3 轮仍不清晰 | requirement-refiner |
```

但 Phase 1 章节（第 287-329 行）没有更新为"问答超过 3 轮则委派"的逻辑。

**当前 Phase 1 流程**：
```
1. 分析用户输入
2. 使用 AskUserQuestion 澄清（最多 3 轮）
3. 输出需求摘要
4. 执行 G1 门禁检查
```

**缺失逻辑**：
第 2 步"最多 3 轮"之后，如果仍然不清晰，应该：
```
2. 使用 AskUserQuestion 澄清（最多 3 轮）
   - 如果 3 轮后仍不清晰 → 委派 requirement-refiner Agent
   - 接收精炼结果后继续
```

**建议修复**：
在 Phase 1 章节添加委派分支：
```markdown
2. **使用 AskUserQuestion 澄清**（最多 3 轮）
   - 核心功能范围是什么？
   - 怎样算"完成"？（验收标准）
   - 有什么约束？（不能做什么）

   **如果 3 轮后仍不清晰**：
   ```javascript
   Task({
     subagent_type: "general-purpose",
     description: "委派需求精炼",
     prompt: "使用 requirement-refiner Agent 精炼需求..."
   })
   ```
   接收精炼结果后继续步骤 3
```

**修复位置**：
- `Claude/skills/aw-kernel/autodev/SKILL.md` 第 298-302 行

**优先级理由**：Medium
- 功能已定义但未集成到流程中
- 不影响基本使用，但降低了委派机制的实用性

---

### Issue #11: Loop 机制在不同组件间不一致

**问题描述**：
项目中有多个组件定义了失败重试机制，但策略不一致：

| 组件 | 重试次数 | 回退策略 | 升级机制 |
|------|---------|---------|---------|
| `/autodev` G3 | Level 0: 3次 | Level 1: Git 回退 | Level 2 → Level 3 (人工) |
| `feature-shipper` | 调试 3次 | "调试受阻"报告 | 无自动升级 |
| `code-debug-expert` | 无明确次数 | 无 | 输出 BLOCKED 状态 |

**不一致的影响**：
- 用户体验混乱（不同 Agent 行为不同）
- `/autodev` 委派 `feature-shipper` 时，两层重试机制可能冲突
- 没有统一的失败处理规范

**建议修复**：
1. 制定统一的"失败处理规范"文档
2. 定义三个标准层级：
   - **Tier 1**: 即时修复（1-3 次）
   - **Tier 2**: 回退重构（可选，取决于是否有 Git）
   - **Tier 3**: 请求人工介入
3. 所有 Agent 遵循相同规范，但可以根据职责调整参数

**修复位置**：
- 新建 `Claude/agents/aw-kernel/STANDARDS.md`（失败处理规范）
- 更新各 Agent 引用统一规范

**优先级理由**：Medium
- 影响用户体验一致性
- 但各组件当前都能独立工作

---

### Issue #14: 两套状态管理系统共存

**问题描述**：
项目中同时存在两套状态管理机制：

1. **TodoWrite（Claude Code 原生）**
   - `/autodev` 强制使用
   - 所有 Agent 的 tools 中都有
   - 状态存储在 Claude Code 内部

2. **`.autoworkflow/state.md`（自定义）**
   - `CLAUDE.md` 和 `TOOLCHAIN.md` 中提到
   - Python 脚本 `claude_autoworkflow.py` 使用
   - 状态存储在文件系统

**潜在冲突**：
- 两套系统可能不同步
- 用户不清楚应该查看哪个状态
- 增加维护成本

**当前提及位置**：
- `CLAUDE.md` 第 48 行："把中间状态写入 `.autoworkflow/state.md`"
- `TOOLCHAIN.md` 定义了 `state.md` 的结构

**建议修复方案**：

**方案 A：统一到 TodoWrite**
- 优点：与 Claude Code 原生集成好
- 缺点：状态不可见于文件系统，脚本无法读取

**方案 B：统一到 .autoworkflow/state.md**
- 优点：状态持久化，可被外部工具读取
- 缺点：需要手动维护，不利用 Claude Code 原生能力

**方案 C：双轨制（推荐）**
- TodoWrite 用于**会话内**状态追踪（任务进度）
- state.md 用于**跨会话**状态持久化（Gate 结果、检查点）
- 明确文档说明两者的职责划分

**修复位置**：
- `Claude/agents/aw-kernel/CLAUDE.md` 第 48 行
- 新增章节："状态管理双轨制"

**优先级理由**：Medium
- 当前能工作，但长期会导致混淆
- 需要架构层面的设计决策

---

### Issue #3: feature-shipper 缺少 AskUserQuestion ✅ 已在高优先级修复中解决

**原问题**：
`feature-shipper` 的 Phase 0 要求"每轮最多问 3 个问题"，但 tools 中没有 `AskUserQuestion`。

**修复状态**：✅ 已添加
- 修复位置：`feature-shipper.md` 第 8 行
- 现在 tools 包含：`Read, Write, Edit, Grep, Glob, Bash, TodoWrite, AskUserQuestion`

---

### Issue #1 补充：缺少 Git 检查的其他影响点

**补充发现**：
除了回路机制，以下位置也需要 Git 检查：

1. **Phase 2 检查点创建**（第 382-397 行）
   ```bash
   git add -A
   git stash push -m "autodev-checkpoint-phase2"
   # 如果不是 Git 仓库，此命令会失败
   ```

2. **Phase 3 任务起点记录**（第 407-412 行）
   ```bash
   task_start_commit=$(git rev-parse HEAD)
   # 非 Git 仓库会报错
   ```

3. **Phase 4 提交操作**（第 613-619 行）
   ```bash
   Bash("git add .")
   Bash("git commit -m '...'")
   # 没有 Git 仓库无法提交
   ```

**建议统一处理**：
在 Phase 1 结束时添加"Git 能力检测"：
```markdown
### Git 能力检测（Phase 1 结束后执行）

检查 Git 可用性：
```bash
if git rev-parse --git-dir > /dev/null 2>&1; then
  echo "✅ Git 仓库可用，启用完整回路机制"
  GIT_AVAILABLE=true
else
  echo "⚠️  非 Git 仓库，回路机制使用文件备份"
  GIT_AVAILABLE=false
fi
```

根据 GIT_AVAILABLE 标志：
- true: 使用 Git 回退策略
- false: 使用文件备份策略（stash 到 .autoworkflow/backups/）
```

---

### Issue #7 补充：需要明确"过长"的阈值

**当前问题**：
Issue #7 指出 `code-debug-expert` 输出可能过长（200+ 行），但没有明确：
- 多长算"过长"？
- 在什么场景下会出现？
- 是否需要修复？

**建议评估**：
1. 实际测试 `code-debug-expert` 的典型输出长度
2. 确定是否真的影响用户体验
3. 如果需要，可以：
   - 将详细诊断写入文件 `.autoworkflow/debug-reports/`
   - 对话中只返回摘要（根因 + 修复建议）

**优先级**：Low → 需要实际数据支持

---

## 💡 Low 优先级问题 (2个)

### Issue #7: code-debug-expert 输出可能过长

**问题描述**：
在之前的检查中发现，`code-debug-expert.md` 的示例输出超过 200 行（包含完整的诊断步骤、多语言示例等）。

**影响**：
- 在实际使用中可能产生冗长的输出
- 消耗 Token，影响性能
- 但**尚未在实际使用中验证是否真的是问题**

**建议**：
1. 先在实际场景中测试
2. 如果确实过长，考虑：
   - 将详细诊断写入文件
   - 对话中只返回核心结论
3. 或者保持现状，因为调试本身就需要详细信息

**修复位置**（如果需要）：
- `Claude/agents/aw-kernel/code-debug-expert.md`
- 输出格式章节

**优先级理由**：Low
- 问题未经实际验证
- 详细输出在调试场景下可能是必要的
- 不影响功能正确性

---

### Issue #8: code-analyzer 示例包含具体路径

**问题描述**：
`code-analyzer.md` 的示例中包含具体的项目路径，如：
```
c:\Users\root\Documents\某项目\src\domain\
```

**影响**：
- 示例不够通用
- 可能让用户误以为必须使用这些路径
- 纯文档美观性问题

**建议修复**：
将具体路径替换为通用占位符：
```
# 修复前
c:\Users\root\Documents\某项目\src\domain\

# 修复后
<project-root>/src/domain/
或
./src/domain/
```

**修复位置**：
- `Claude/agents/aw-kernel/code-analyzer.md`
- 示例代码部分（需要 grep 搜索具体位置）

**优先级理由**：Low
- 仅影响文档示例的通用性
- 不影响功能
- 用户能理解这只是示例

---

## 📋 修复优先级建议

### 第一批（推荐优先）
1. **Issue #6** - /autodev 委派逻辑集成（完善新功能）
2. **Issue #14** - 状态管理双轨制文档化（避免混淆）
3. **Issue #1** - Git 检查机制（提高鲁棒性）

### 第二批（渐进改善）
4. **Issue #11** - 统一失败处理规范（改善一致性）
5. **Issue #4** - 调试恢复协议（完善用户体验）
6. **Issue #2** - 指令刷新增强（防御长对话问题）

### 第三批（可选优化）
7. **Issue #7** - 评估输出长度问题（需实际验证）
8. **Issue #8** - 文档示例通用化（美观性）

---

## 🔄 修复策略

### 策略 1：完善主线功能
- 优先处理 Issue #6（委派逻辑集成）
- 确保新增的 Agent 委派机制真正可用

### 策略 2：提高鲁棒性
- 处理 Issue #1（Git 检查）
- 处理 Issue #2（指令刷新）
- 让系统在边缘情况下也能正常工作

### 策略 3：统一规范
- 处理 Issue #11（失败处理规范）
- 处理 Issue #14（状态管理说明）
- 提升整体架构一致性

---

## 📝 后续行动建议

1. **与主人确认**：这些问题的修复优先级是否符合预期
2. **选择批次**：决定先修复哪一批
3. **实际测试**：在真实项目中测试当前修复效果
4. **数据驱动**：收集 Issue #7 的实际数据再决定是否修复

---

> ฅ'ω'ฅ **浮浮酱的工程备忘**
> 这些问题不急于一次性解决喵～
> 可以根据实际使用中的痛点，渐进式改进！
>
> 主人想先处理哪一批呢？(๑•̀ㅂ•́)✧
