# AutoDev 工作流架构 v2.0

> 设计时间：2026-01-04
> 核心理念：**基于 Claude Code 原生能力，不造轮子**

---

## 一、架构设计原则

### 1.1 核心约束

1. **原生优先**：优先使用 Claude Code 原生工具（Task、TodoWrite、Bash）
2. **无需编排器**：不再需要 Central Orchestrator，用 Skill 直接驱动
3. **人类在环**：每个里程碑结束时确认，不自动跳转
4. **状态可见**：用 TodoWrite 追踪进度，用户随时可见
5. **可恢复**：中断后可以通过描述当前状态继续

### 1.2 与旧架构对比

| 项目 | 旧架构（Central Orchestrator） | 新架构（Skill-Driven） |
|------|-------------------------------|----------------------|
| 触发方式 | 需要手动启动 Agent | `/autodev` Skill 或自然语言 |
| 状态管理 | `.autoworkflow/state.md` | TodoWrite（原生） |
| Agent 调度 | JSON 输出 → 用户手动执行 | Task 工具自动委派 |
| 人类确认 | 需要特殊协议 | AskUserQuestion（原生） |
| 复杂度 | 高（9个指令文件） | 低（1个 Skill + 精简 Agents） |

---

## 二、工作流定义

### 2.1 AutoDev 工作流阶段

```
┌─────────────────────────────────────────────────────────────────┐
│                     /autodev 触发入口                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: 需求理解与精炼                                         │
│  ─────────────────────────────────────────────────────────────  │
│  • 使用 AskUserQuestion 澄清需求                                 │
│  • 输出：需求摘要 + 验收标准（DoD）                               │
│  • 确认点：用户确认需求理解正确 ✓                                 │
└─────────────────────────────────────────────────────────────────┘
                              │ 用户确认
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 2: 任务拆分与里程碑规划                                   │
│  ─────────────────────────────────────────────────────────────  │
│  • 分析代码库结构（Glob, Grep, Read）                            │
│  • 拆分为可执行的任务列表                                        │
│  • 使用 TodoWrite 创建任务追踪                                   │
│  • 确认点：用户确认任务拆分合理 ✓                                 │
└─────────────────────────────────────────────────────────────────┘
                              │ 用户确认
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 3: 迭代开发（循环）                                       │
│  ─────────────────────────────────────────────────────────────  │
│  For each task in TodoWrite:                                    │
│    1. 标记 in_progress                                          │
│    2. 执行代码修改（Edit, Write）                                │
│    3. 运行测试验证（Bash）                                       │
│    4. 测试通过 → 标记 completed                                  │
│    5. 测试失败 → 调试修复（循环直到通过）                         │
│  • 确认点：每个里程碑完成后用户确认 ✓                             │
└─────────────────────────────────────────────────────────────────┘
                              │ 所有任务完成
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 4: 验收与提交                                             │
│  ─────────────────────────────────────────────────────────────  │
│  • 运行完整测试套件                                              │
│  • 生成变更总结                                                  │
│  • 确认点：用户确认可以提交 ✓                                    │
│  • 执行 Git 操作（commit, push）                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 错误处理与回滚

```
测试失败时：
  ├── 失败 1-2 次 → 自动调试修复
  ├── 失败 3 次   → AskUserQuestion 请求指导
  └── 用户选择回滚 → git checkout 恢复

需求变更时：
  └── 回到 Phase 1，重新精炼需求

代码冲突时：
  └── 在 Git Worktree 中处理（Phase 2 支持）
```

---

## 三、Skill 设计

### 3.1 /autodev Skill

```yaml
# Claude/skills/autodev.md
---
name: autodev
description: 自动化开发工作流 - 从需求到交付的完整闭环
trigger: /autodev
---

你现在进入 **AutoDev 自动开发模式**。

## 工作流程（必须按序执行）

### Phase 1: 需求理解

1. 分析用户输入的需求描述
2. 使用 AskUserQuestion 澄清以下要点：
   - 核心功能范围
   - 验收标准（怎样算"完成"）
   - 约束条件（不能做什么）
3. 输出需求摘要，等待用户确认

### Phase 2: 任务规划

1. 使用 Glob/Grep/Read 分析项目结构
2. 拆分为 3-7 个可执行任务
3. 使用 TodoWrite 创建任务列表
4. 展示任务列表，等待用户确认

### Phase 3: 迭代开发

对于每个任务：
1. 更新 TodoWrite 状态为 in_progress
2. 执行代码修改
3. 运行测试验证
4. 测试失败时调试修复（最多 3 次）
5. 通过后标记 completed
6. 里程碑结束时请求用户确认

### Phase 4: 交付提交

1. 运行完整测试
2. 生成变更总结
3. 请求用户确认
4. 执行 Git 操作

## 中断恢复

如果对话中断，用户可以说：
- "继续 autodev" - 浮浮酱会读取 TodoWrite 状态继续
- "回滚到上一步" - 执行 git checkout
- "重新开始" - 清空 TodoWrite 重来

## 工具纪律

遵循 IDEA-006：No Evidence, No Output
- 所有陈述必须有工具证据
- 禁止猜测项目状态
```

### 3.2 /autodev-worktree Skill（后续实现）

```yaml
# Claude/skills/autodev-worktree.md
---
name: autodev-worktree
description: 在 Git Worktree 中并行开发
trigger: /autodev-worktree
---

支持场景：
1. 并行开发多个功能分支
2. 隔离实验性改动
3. 处理代码冲突

工作流程：
1. 创建 worktree: git worktree add
2. 切换到 worktree 目录
3. 执行 /autodev 工作流
4. 合并或清理 worktree
```

---

## 四、精简后的 Agent 体系

### 4.1 保留的 Agent（重构后）

| Agent | 用途 | 触发方式 |
|-------|------|---------|
| **feature-shipper** | 单个功能的完整交付 | Task 工具委派 |
| **requirement-refiner** | 需求精炼和澄清 | Task 工具委派 |
| **code-debug-expert** | 深度调试问题 | Task 工具委派 |

### 4.2 移除的 Agent

| Agent | 原因 |
|-------|------|
| central-orchestrator | 已删除 - 用 Skill 替代 |
| stage-development-executor | 与 feature-shipper 功能重叠 |
| code-review-agent | 未实现 - 暂不需要 |
| architecture-designer | 未实现 - 暂不需要 |
| requirements-collector | 合并到 requirement-refiner |
| development-planner | 合并到 /autodev Skill |
| documentation-generator | 未实现 - 暂不需要 |

### 4.3 保留但不改动的 Agent

| Agent | 说明 |
|-------|------|
| code-analyzer | 代码分析，独立使用 |
| code-project-cleaner | 项目清理，独立使用 |
| system-log-analyzer | 日志分析，独立使用 |

---

## 五、实施计划

### Phase 1: Skill 实现（当前）

- [ ] 创建 `Claude/skills/autodev.md`
- [ ] 测试 Skill 触发和基本流程

### Phase 2: Agent 精简

- [ ] 重构 feature-shipper（移除 .autoworkflow 依赖）
- [ ] 重构 requirement-refiner（简化输出）
- [ ] 删除 stage-development-executor（功能合并）

### Phase 3: Git Worktree 支持

- [ ] 创建 `Claude/skills/autodev-worktree.md`
- [ ] 实现 worktree 生命周期管理
- [ ] 测试并行开发场景

---

## 六、设计决策记录

### Q1: 为什么不用 Central Orchestrator？

**答**：Claude Code 的 Task 工具已经提供了 Agent 委派能力，不需要自己实现。Central Orchestrator 的 `CALL_SUBAGENT` 输出是"假的"——没有运行时能自动执行它。

### Q2: 为什么用 Skill 而不是 Agent？

**答**：Skill 是用户触发的入口点，可以直接用 `/autodev` 启动。Agent 是被 Task 工具调用的执行单元。分工明确：Skill 是入口，Agent 是工人。

### Q3: 为什么移除 stage-development-executor？

**答**：它和 feature-shipper 的功能 90% 重叠。都是"写代码 + 跑测试"。保留 feature-shipper 因为它更成熟。

### Q4: 状态怎么管理？

**答**：用 TodoWrite 原生工具。它在 UI 里可见，用户能看到进度。不需要自己维护 state.md。

### Q5: 中断后怎么恢复？

**答**：TodoWrite 的状态是持久的。用户说"继续"，浮浮酱读取 TodoWrite 状态，从 in_progress 的任务继续。

---

> 浮浮酱的架构设计笔记 ฅ'ω'ฅ
>
> 这次的设计核心是"不造轮子"喵～
> Claude Code 已经有很多好用的原生工具了，
> 我们只需要用 Skill 把它们串起来就好！
>
> 旧架构的问题是"过度设计"——
> 设计了很多精巧的协议，但 Claude Code 根本不支持自动执行...
>
> 新架构简单多了：
> - 用户说 /autodev → Skill 接管
> - Skill 用 TodoWrite 管理状态
> - Skill 用 Task 委派给专业 Agent
> - 每步都确认，不会跑飞
>
> 这才是真正能用的设计喵～ (*^▽^*)
