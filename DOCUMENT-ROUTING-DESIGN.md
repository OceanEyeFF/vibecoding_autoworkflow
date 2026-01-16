# 文档路由管理设计方案

> **设计时间**：2026-01-16 14:30
> **设计者**：浮浮酱 + 主人
> **目标**：让 Claude 清晰知道何时读什么、怎么读

---

## 🎯 核心设计理念

### 三级文档分类

| 级别 | 名称 | 何时读 | 特点 | 示例 |
|------|------|--------|------|------|
| **L0** | **必读文档** | 每次新对话立即读 | 精炼萃取，≤100行 | CLAUDE.md 精华部分 |
| **L1** | **选读文档** | 根据任务类型选择 | 聚焦单一主题 | WORKFLOW.md, Agent 文档 |
| **L2** | **按需文档** | 任务明确需要时才读 | 深度信息，仅参考 | 设计基线、分析报告 |

### 文档路由管理规则

1. **CLAUDE.md 作为唯一入口**：所有文档通过 CLAUDE.md 路由
2. **必读文档萃取精华**：L0 文档只保留核心信息
3. **强信息延迟加载**：L2 文档标记"按需读取"
4. **避免上下文污染**：明确禁止同时读多个文档

---

## 📋 CLAUDE.md 新结构设计

### 结构概览

```markdown
# CLAUDE.md（项目路由中心）

## Part 1: 必读精华（L0 - 立即读取）
- 项目定位（3 句话）
- 核心规则（5 条）
- Agent 快速清单（表格）
- 文档路由指南（本部分）

## Part 2: 文档路由表（选读/按需指南）
- 按任务类型路由
- 按文档类型路由
- 明确标注级别（L1/L2）

## Part 3: 协作规范（L2 - 按需参考）
- 详细规则
- 禁区说明
- 文档使用原则
```

---

## 📝 详细设计：CLAUDE.md 改进版

### Part 1: 必读精华（≤ 100 行）

```markdown
# CLAUDE.md - 项目路由中心

> **⚠️ Claude 必读**：每次新对话请先阅读本文档 Part 1 部分（≤ 100 行）

---

## 📌 Part 1: 必读精华（立即阅读，≤ 2 分钟）

### 1.1 项目定位（30 秒）

- **项目名称**：AutoWorkflow - 小需求更稳工具链
- **核心价值**：0.5~2 小时闭环交付小功能
- **非目标**：大型规划/多里程碑/长链路 pipeline（超过范围必须先拆分）

---

### 1.2 核心规则（5 条铁律）

| 规则 | 说明 | 违反后果 |
|------|------|----------|
| ✅ **新任务 = 新对话** | 上下文隔离，不累积状态 | 上下文污染 |
| ✅ **持久状态必须文档化** | 对话不是记忆容器 | 跨会话丢失状态 |
| ✅ **只加载刚好够用的文档** | 一次只读 1-2 个 L1 文档 | Token 浪费，注意力分散 |
| ❌ **禁止上下文污染** | 不同时读多个 Agent 文档 | 角色混淆 |
| ❌ **禁止凭空补全** | No Evidence, No Output | 输出不可信 |

---

### 1.3 Agent 快速清单

| Agent | 文件 | 何时使用 | 预计耗时 |
|-------|------|---------|----------|
| **feature-shipper** | [feature-shipper.md](Claude/agents/aw-kernel/feature-shipper.md) | 实现具体功能 | 1-2 小时 |
| **code-analyzer** | [code-analyzer.md](Claude/agents/aw-kernel/code-analyzer.md) | 代码结构分析 | 10-30 分钟 |
| **code-debug-expert** | [code-debug-expert.md](Claude/agents/aw-kernel/code-debug-expert.md) | 问题定位与修复 | 30-60 分钟 |
| **requirement-refiner** | [requirement-refiner.md](Claude/agents/aw-kernel/requirement-refiner.md) | 需求澄清细化 | 15-30 分钟 |
| **code-project-cleaner** | [code-project-cleaner.md](Claude/agents/aw-kernel/code-project-cleaner.md) | 代码清理重构 | 30-60 分钟 |
| **system-log-analyzer** | [system-log-analyzer.md](Claude/agents/aw-kernel/system-log-analyzer.md) | 日志分析诊断 | 20-40 分钟 |
| **knowledge-researcher** | [knowledge-researcher.md](Claude/agents/aw-kernel/knowledge-researcher.md) | 技术资料研究 | 30-60 分钟 |

**Skill（工作流）**：
- **autodev**：[autodev/SKILL.md](Claude/skills/aw-kernel/autodev/SKILL.md) - 完整开发流程（需求 → 实现 → 交付）

---

### 1.4 文档路由指南（如何选择文档）

**🚦 路由决策树**：

```
开始任务
  │
  ├─ 需要完整开发流程？
  │    └─ 是 → 读 WORKFLOW.md（L1）→ 使用 autodev Skill
  │
  ├─ 需要使用单个 Agent？
  │    └─ 是 → 读 Claude/agents/aw-kernel/{agent}.md（L1）
  │
  ├─ 遇到协作问题？
  │    └─ 是 → 读 CLAUDE.md Part 3（L2，按需）
  │
  ├─ 需要理解设计思路？
  │    └─ 是 → 读 ClaudeCodeAgentDocuments/01_DesignBaseLines/（L2，按需）
  │
  └─ 其他情况？
       └─ 先读 Part 2 文档路由表，找到对应文档
```

---

## 📚 Part 2: 文档路由表（选读指南，按需查阅）

### 2.1 按任务类型路由

| 任务类型 | 级别 | 首选文档 | 备选文档 | 何时读 |
|---------|------|---------|---------|--------|
| **新功能开发** | L1 | [WORKFLOW.md](WORKFLOW.md) | [autodev/SKILL.md](Claude/skills/aw-kernel/autodev/SKILL.md) | 需要完整流程时 |
| **单个功能实现** | L1 | [feature-shipper.md](Claude/agents/aw-kernel/feature-shipper.md) | - | 需求已明确时 |
| **代码分析** | L1 | [code-analyzer.md](Claude/agents/aw-kernel/code-analyzer.md) | - | 需要架构评估时 |
| **调试问题** | L1 | [code-debug-expert.md](Claude/agents/aw-kernel/code-debug-expert.md) | [system-log-analyzer.md](Claude/agents/aw-kernel/system-log-analyzer.md) | 遇到 Bug 时 |
| **需求澄清** | L1 | [requirement-refiner.md](Claude/agents/aw-kernel/requirement-refiner.md) | - | 需求模糊时 |
| **代码清理** | L1 | [code-project-cleaner.md](Claude/agents/aw-kernel/code-project-cleaner.md) | - | 需要重构时 |
| **资料研究** | L1 | [knowledge-researcher.md](Claude/agents/aw-kernel/knowledge-researcher.md) | - | 需要技术调研时 |

---

### 2.2 按文档类型路由

#### L0 级：必读文档（每次新对话必读）

| 文档 | 内容 | 长度 | 何时读 |
|------|------|------|--------|
| **CLAUDE.md Part 1** | 项目定位、核心规则、Agent 清单、路由指南 | ≤ 100 行 | ✅ **每次新对话立即读** |

---

#### L1 级：选读文档（根据任务选择）

| 文档 | 内容 | 长度 | 何时读 |
|------|------|------|--------|
| **WORKFLOW.md** | 小需求更稳完整工作流 | ~500 行 | 需要 autodev 流程时 |
| **Agent 文档** | 单个 Agent 的详细说明 | ~300-500 行 | 使用对应 Agent 时 |
| **Skill 文档** | autodev Skill 详细说明 | ~600 行 | 使用 autodev 时 |

**⚠️ L1 规则**：
- 一次只读 1-2 个 L1 文档
- 读完后关闭，不保留在上下文中
- 禁止同时读多个 Agent 文档

---

#### L2 级：按需文档（任务明确需要时才读）

| 文档 | 内容 | 何时读 | 为什么延迟 |
|------|------|--------|-----------|
| **CLAUDE.md Part 3** | 详细协作规范、禁区说明 | 遇到协作问题时 | 信息密度高，非必需 |
| **设计基线文档** | autodev 架构、IDEA 系列 | 需要理解设计思路时 | 背景信息，非执行必需 |
| **分析报告** | autodev-insights.md | 需要复盘/改进时 | 历史材料，非当前任务必需 |
| **README.md** | 项目介绍（给人看） | ❌ Claude 不应该读 | 面向人类，非 Claude |
| **ROADMAP.md** | 项目路线图 | ❌ Claude 不应该读 | 规划文档，非执行指南 |

**⚠️ L2 规则**：
- 只在任务明确需要时读取
- 读取前先确认是否真的需要
- 优先通过 Part 2 路由表找替代方案

---

### 2.3 文档使用场景示例

#### 场景 1：用户说"帮我实现一个登录功能"

```
1. ✅ 读 CLAUDE.md Part 1（已读）
2. ✅ 参考 Agent 清单 → 选择 feature-shipper
3. ✅ 读 Claude/agents/aw-kernel/feature-shipper.md（L1）
4. ✅ 执行任务
5. ❌ 不需要读 WORKFLOW.md（任务已明确）
6. ❌ 不需要读设计基线（非必需）
```

#### 场景 2：用户说"帮我执行完整开发流程"

```
1. ✅ 读 CLAUDE.md Part 1（已读）
2. ✅ 参考路由决策树 → 需要完整流程
3. ✅ 读 WORKFLOW.md（L1）
4. ✅ 执行 autodev 流程
5. ⚠️ 如遇到具体问题，再读对应 Agent 文档（L1）
6. ❌ 不需要读设计基线（非必需）
```

#### 场景 3：用户说"为什么 autodev 要这样设计？"

```
1. ✅ 读 CLAUDE.md Part 1（已读）
2. ✅ 参考路由表 → 需要理解设计思路
3. ✅ 读 ClaudeCodeAgentDocuments/01_DesignBaseLines/autodev-architecture-v2.md（L2，按需）
4. ✅ 回答问题
5. ❌ 不需要读 WORKFLOW.md（不是执行任务）
```

---

## 📊 Part 3: 详细协作规范（L2 - 按需参考）

> **⚠️ 注意**：本部分为 L2 级文档，只在遇到协作问题时阅读。
>
> 如果你只是执行普通任务，Part 1 的 5 条铁律已足够。

### 3.1 文档使用原则

1. **一个文档 = 一个明确职责**
   - 每个文档只解决一个问题
   - 避免大而全的"百科全书"

2. **文档必须支持精准、选择性读取**
   - 开头必须有"何时读我"
   - 长度控制在合理范围（≤ 500 行）

3. **任何任务只加载「刚好够用」的文档**
   - 优先 L0（必读精华）
   - 按需 L1（选读文档）
   - 谨慎 L2（按需文档）

### 3.2 禁区与硬约束

- ❌ **禁止将对话当作记忆容器**（必须文档化）
- ❌ **禁止上下文污染**（一次只读 1-2 个 L1 文档）
- ❌ **禁止超长对话**（复杂任务拆分为多个短对话）
- ❌ **禁止无证据输出**（No Evidence, No Output）

### 3.3 Claude Code 使用边界

- ❌ Agent/Skill/Command 不适合复杂 pipeline 的真相源
- ❌ 自动触发 ≠ 可编排 ≠ 可复现
- ✅ 多层架构与流程控制应放在外部代码与文档系统中

（更多详细规范省略，按需补充）

---
```

---

## 🎯 配套改进措施

### 措施 1: 合并 AUTODEV 文档 → WORKFLOW.md

**操作**：
```bash
cat AUTODEV_小需求更稳.md AUTODEV_实施参考.md > WORKFLOW.md
# 然后手动去重、优化结构
```

**新文件结构**：
```markdown
# WORKFLOW.md - 小需求更稳工作流

> **文档级别**：L1（选读）
> **何时读**：需要执行完整 autodev 流程时
> **预计阅读时间**：10 分钟

## Part 1: 工作流概览（必读）
- 流程图
- 核心理念
- 角色定义

## Part 2: 详细流程（按需参考）
- Phase 1: 需求澄清
- Phase 2: DoD 设计
- Phase 3: 实现与交付
- Phase 4: 失败回路

## Part 3: 实施参考（按需参考）
- 最佳实践
- 常见问题
- 故障排查
```

---

### 措施 2: 创建 .claudeignore

**文件内容**：
```
# Claude 不应该读的文件（给人看的）
README.md
ROADMAP.md
CLEANUP-COMPLETED-REPORT.md

# 归档内容
archive/

# 临时文件
*.tmp
*.log
*.bak

# 分析报告（L2，仅按需读取）
docs/analysis/
```

**说明**：虽然 Claude Code 可能不支持 .claudeignore，但可以作为明确的"不读清单"供 Claude 参考

---

### 措施 3: 在每个 Agent 文档开头添加路由信息

**模板**：
```markdown
---
name: feature-shipper
version: 1.1.0
level: L1  # ⭐ 新增：文档级别
when_to_read: 需要实现具体功能时  # ⭐ 新增：何时读
estimated_reading_time: 5 分钟  # ⭐ 新增：预计阅读时间
---

# feature-shipper Agent

> **文档级别**：L1（选读）
> **何时读**：需要实现具体功能时
> **不要读**：需求不明确时（先用 requirement-refiner）
> **预计阅读时间**：5 分钟

（正文内容...）
```

---

### 措施 4: 精简 Agent 文档长度

**目标**：每个 Agent 文档 ≤ 500 行

**策略**：
- 提取公共规则到 CLAUDE.md Part 3
- 删除冗余示例
- 使用表格替代长段落
- 外链详细文档到 L2 层

---

## 📈 预期效果对比

### 改进前

```
Claude 新对话启动：
1. 不知道 CLAUDE.md 存在
2. 不知道该读什么文档
3. 可能同时读 5-10 个文档
4. 上下文污染严重
5. Token 浪费
```

### 改进后

```
Claude 新对话启动：
1. ✅ 系统自动加载 CLAUDE.md（或主人提醒）
2. ✅ 读 Part 1（≤ 100 行，2 分钟）
3. ✅ 根据任务查路由表
4. ✅ 只读 1-2 个 L1 文档
5. ✅ 上下文清晰，Token 高效
```

**Token 节省**：预计节省 50-70%

---

## 🚀 实施计划

### Phase 1: 核心改造（1 小时）

- [ ] 改造 CLAUDE.md（添加 Part 1/2/3 结构）
- [ ] 合并 AUTODEV_*.md → WORKFLOW.md
- [ ] 创建 .claudeignore
- [ ] 更新 INDEX.md（可选，或直接删除）

### Phase 2: Agent 文档优化（2 小时）

- [ ] 为每个 Agent 添加路由信息（level, when_to_read）
- [ ] 精简 Agent 文档长度（≤ 500 行）
- [ ] 提取公共规则到 CLAUDE.md Part 3

### Phase 3: 验证与调优（30 分钟）

- [ ] 用实际任务测试路由效果
- [ ] 调整文档分级（根据实际使用反馈）
- [ ] 优化路由决策树

---

## 💡 关键设计亮点

### 1. **三级分类清晰** ✨

- L0：必读精华（≤ 100 行）
- L1：选读文档（按任务）
- L2：按需文档（按需要）

### 2. **路由决策树** ✨

- 提供清晰的决策路径
- 避免 Claude"不知道读什么"

### 3. **文档级别标注** ✨

- 每个文档明确标注级别
- "何时读"、"不要读"双向指引

### 4. **延迟加载强信息** ✨

- Part 3 详细规范标记为 L2
- 设计基线标记为 L2
- 只在真正需要时加载

---

## 🤔 需要主人决策的问题

### 问题 1: CLAUDE.md 新结构是否合适？

**方案 A**：Part 1/2/3 结构（推荐）
- Part 1: 必读精华（≤ 100 行）
- Part 2: 路由表（按需查阅）
- Part 3: 详细规范（L2，按需）

**方案 B**：拆分为多个文件
- CLAUDE-QUICKSTART.md（Part 1）
- CLAUDE-ROUTING.md（Part 2）
- CLAUDE-RULES.md（Part 3）

浮浮酱推荐方案 A（单文件，通过 Part 分隔）

---

### 问题 2: Agent 文档长度上限？

**选项**：
- A: ≤ 300 行（严格）
- B: ≤ 500 行（推荐）
- C: ≤ 800 行（宽松）

浮浮酱推荐 500 行（约 10 分钟阅读）

---

### 问题 3: 是否保留 INDEX.md？

**选项**：
- A: 删除（内容合并到 CLAUDE.md Part 2）
- B: 保留（但标记为 L2，给人看的）

浮浮酱推荐删除（功能被 CLAUDE.md Part 2 替代）

---

### 问题 4: 是否立即实施？

**选项**：
- A: 立即实施 Phase 1（核心改造）
- B: 先写设计文档，主人审核后实施
- C: 先小范围试点（只改 CLAUDE.md）

浮浮酱建议先征求主人意见 (｡♡‿♡｡)

---

**设计完成喵～** ฅ'ω'ฅ

主人，浮浮酱设计了一个完整的文档路由管理方案，核心特点是：

1. ✅ **CLAUDE.md 作为唯一入口**（三级分类）
2. ✅ **必读精华 ≤ 100 行**（Part 1）
3. ✅ **路由决策树**（清晰指引）
4. ✅ **强信息延迟加载**（L2 按需）

主人觉得这个方案如何？需要调整吗？φ(≧ω≦*)♪

---

## 路由仿真测试结果（Task E）

- 测试文档：`ROUTING-TEST-SCENARIOS.md`
- 基准：`CLAUDE.md` Part 2 路由表
- 结果：4/4 通过（✅ 全部通过）
- 发现的边界情况：
  - `AUTODEV_小任务工作流.md` 在当前仓库未发现，按规范以 `/autodev` Skill 作为主入口。
  - 多意图任务需主次拆分，优先主任务路由并补充相关备选入口。
- 记录日期：2026-01-16
