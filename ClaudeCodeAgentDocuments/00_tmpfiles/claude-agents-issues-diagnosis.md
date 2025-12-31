# Claude Agents 架构问题诊断报告

> 生成时间：2024-12-31
> 分析范围：`Claude/agents/` 目录下所有 Agent 定义
> 分析方法：逐文件阅读 Prompt 内容，对照实际使用场景

---

## 一、问题总览

| 编号 | 问题类别 | 严重程度 | 状态 |
|------|---------|---------|------|
| P01 | SubAgent 标注缺失 | 🔴 高 | 待改进 |
| P02 | Agent 边界不清晰 | 🔴 高 | 待改进 |
| P03 | 缺少鉴权 Agent | 🟠 中高 | 待改进 |
| P04 | 交互格式不明确 | 🟠 中 | 待改进 |
| P05 | 核心 Agent 无本地化文档缓存 | 🔴 高 | 待改进 |
| P06 | Prompt 没有强制"先访问数据" | 🔴 高 | 待改进 |
| P07 | Skills 设计过于简单 | 🟡 中 | 待改进 |
| P08 | 缺少错误恢复机制 | 🟡 中 | 待改进 |
| P09 | 会话状态管理缺失 | 🟡 中 | 待改进 |

---

## 二、问题详细分析

### P01：SubAgent 标注缺失

**严重程度**：🔴 高

#### 现状描述

所有 Agent 的 YAML Front Matter 中只定义了 `tools`，没有 `subagents` 字段：

```yaml
# feature-shipper.md 第 7 行
tools: Read, Grep, Glob, Bash
# ❌ 缺失：subagents: requirement-refiner, code-analyzer, code-debug-expert
```

#### 问题表现

1. feature-shipper 在 Prompt 中提到"用需求收敛把它收敛成可执行的验收标准"
2. 但没有显式声明调用 `requirement-refiner` 的能力
3. Agent 之间的协作完全靠"口头约定"，无法强制执行

#### 影响范围

- feature-shipper **没有能力真正调用** requirement-refiner
- "需求收敛"只是文字描述，实际执行时 LLM 会**自己编造**需求精炼流程
- Agent 协作是**幻觉**，不是真正的多 Agent 系统

#### 涉及文件

- `Claude/agents/feature-shipper.md`
- `Claude/agents/requirement-refiner.md`
- `Claude/agents/code-analyzer.md`
- `Claude/agents/code-debug-expert.md`

---

### P02：Agent 边界不清晰

**严重程度**：🔴 高

#### 现状描述

| Agent | 职责声明 | 实际重叠 |
|-------|---------|---------|
| feature-shipper | "需求收敛 + 实现 + 验证" | 自己做需求收敛，与 requirement-refiner 冲突 |
| requirement-refiner | "五阶段需求精炼" | 自己有完整流程，但 feature-shipper 不调用它 |
| code-debug-expert | "四步诊断框架" | feature-shipper 的"失败定位修复"与此重叠 |

#### 证据

```markdown
# feature-shipper.md 第 35 行
如果用户只给了模糊需求，你先用"需求收敛"把它收敛成可执行的验收标准，再进入实现。

# requirement-refiner.md 第 8 行
你是一位专业的需求精炼师，擅长将模糊、宽泛的用户需求转化为清晰、可执行的最小可行迭代方案。
```

#### 问题表现

1. feature-shipper 自己做"需求收敛"，那 requirement-refiner 存在的意义是什么？
2. **职责边界完全模糊**，没有明确的"何时用哪个 Agent"的判断逻辑
3. 用户困惑：应该先调用谁？

#### 涉及文件

- `Claude/agents/feature-shipper.md`
- `Claude/agents/requirement-refiner.md`
- `Claude/agents/code-debug-expert.md`
- `Claude/agents/CLAUDE.md`（模块指南，但没有明确边界定义）

---

### P03：缺少鉴权 Agent

**严重程度**：🟠 中高

#### 现状描述

```yaml
# 所有 Agent 的权限模式
permissionMode: default
# 或者根本没有 permissionMode 字段
```

#### 问题表现

1. ❌ 没有 `permission-guard` / `auth-agent` 来判断"这个操作是否需要人工确认"
2. ❌ 没有敏感操作分级（如：读文件=低风险，删文件=高风险，git push=需确认）
3. ❌ 没有"无人值守模式"下的自动鉴权逻辑

#### 影响范围

- 在 CI/无人值守环境中，**无法安全运行**
- 要么全部放行（危险），要么全部阻塞（无法自动化）

#### 涉及文件

- 所有 Agent 文件
- 缺失：`Claude/agents/permission-guard.md`

---

### P04：交互格式不明确

**严重程度**：🟠 中

#### 现状描述

| Agent | 交互格式定义 | 问题 |
|-------|------------|------|
| feature-shipper | 有输出格式模板（第 219-235 行） | 格式不够严格，没有 JSON Schema |
| requirement-refiner | 每阶段有输出格式 | **格式是嵌入 Markdown**，不是机器可解析的结构 |
| code-analyzer | 有三文档规范 | 输出格式是自由文本，非结构化 |
| system-log-analyzer | ✅ 有 JSON Schema | **唯一一个有严格格式的** |

#### 证据

```markdown
# requirement-refiner.md 阶段1输出格式
## 需求澄清结果
**核心价值主张**：[简述]
**原子任务清单**：
1. [任务1]

# ❌ 这不是机器可解析的格式，是给人看的
```

#### 问题表现

1. Agent 之间传递信息时，**无法可靠地解析前一个 Agent 的输出**
2. 没有统一的交互协议（如 JSON Schema / Structured Output）
3. 人可以看懂，但下游 Agent 无法可靠提取信息

#### 涉及文件

- `Claude/agents/feature-shipper.md`
- `Claude/agents/requirement-refiner.md`
- `Claude/agents/code-analyzer.md`
- `Claude/agents/system-log-analyzer.md`（这个是正例）

---

### P05：核心 Agent 无本地化文档缓存

**严重程度**：🔴 高

#### 现状描述

feature-shipper 是中枢 Agent，Prompt 共 236 行：

```markdown
# feature-shipper.md 有 236 行
# 全部内容都在 System Prompt 里
# 每轮对话都要完整加载
```

#### 问题表现

1. 每次对话都要加载 **236 行的完整 Prompt**
2. 长对话后，**原始指令会被稀释**，LLM 会"忘记"核心约束
3. 没有"本地化文档缓存"机制来保持指令清晰度

#### 期望设计

```markdown
# 核心约束应该写入 .autoworkflow/agent-instructions/feature-shipper-core.md
# Prompt 只保留"读取并遵循 {path} 的指令"
# 这样可以避免上下文污染
```

#### 涉及文件

- `Claude/agents/feature-shipper.md`
- `Claude/agents/requirement-refiner.md`
- `Claude/agents/code-analyzer.md`

---

### P06：Prompt 没有强制"先访问数据"

**严重程度**：🔴 高

#### 现状描述

| Agent | 工具纪律声明 | 实际强制力 |
|-------|------------|-----------|
| feature-shipper | "先查证后输出；先调用再回答" | ❌ 只是文字要求，没有机制保障 |
| requirement-refiner | 同上 | ❌ 五阶段流程没有"必须先调用工具"的硬性检查点 |
| code-analyzer | 同上 | ❌ 没有"若未调用工具则拒绝输出"的逻辑 |

#### 证据

```markdown
# feature-shipper.md 第 25 行
工具纪律：**先查证后输出；先调用再回答**。能用工具确认的内容先查证...

# ❌ 但这只是"建议"，不是强制
# ❌ 没有类似这样的硬性规定：
#    "如果本轮没有任何工具调用，必须输出 [BLOCKED: 需要先查证]"
```

#### 问题表现

1. LLM 很容易"偷懒"，直接基于被污染的上下文回答
2. 没有机制阻止 LLM 编造信息
3. "工具纪律"形同虚设

#### 涉及文件

- 所有 Agent 文件

---

### P07：Skills 设计过于简单

**严重程度**：🟡 中

#### 现状描述

```yaml
# autoworkflow/SKILL.md 只有 37 行
# git-workflow/SKILL.md 只有 61 行
# 内容主要是"命令列表"，没有真正的能力封装
```

#### 问题表现

1. Skills 只是"命令参考文档"，不是真正的能力封装
2. 没有状态管理
3. 没有错误处理

#### 涉及文件

- `Claude/skills/autoworkflow/SKILL.md`
- `Claude/skills/git-workflow/SKILL.md`

---

### P08：缺少错误恢复机制

**严重程度**：🟡 中

#### 现状描述

```markdown
# 没有任何 Agent 定义了：
# - Gate 失败后的自动重试策略
# - 死循环检测（如果连续 5 次 Gate 失败怎么办？）
# - 回滚机制
```

#### 问题表现

1. Gate 失败后只是"记录到 state.md"，没有自动恢复策略
2. 可能陷入无限循环
3. 没有"放弃并上报"的逻辑

#### 涉及文件

- `Claude/agents/feature-shipper.md`
- `Claude/agents/TOOLCHAIN.md`

---

### P09：会话状态管理缺失

**严重程度**：🟡 中

#### 现状描述

```markdown
# state.md 的设计是好的，但：
# - 没有定义"如何从 state.md 恢复中断的工作"
# - 没有"会话 ID"概念
# - 多次对话之间无法可靠续接
```

#### 问题表现

1. 用户中断对话后，下次启动无法可靠续接
2. 没有"检查点"概念
3. state.md 格式不够结构化，难以机器解析

#### 涉及文件

- `Claude/agents/feature-shipper.md`
- `Claude/agents/assets/templates/state-template.md`

---

## 三、问题关联图

```
┌─────────────────────────────────────────────────────────────┐
│                      根本问题                                │
│  "这是一套精心设计的单 Agent Prompt，被拆分成多个文件，      │
│   但没有真正的协作能力"                                      │
└────────────────────────────┬────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
    ┌─────────┐       ┌─────────────┐     ┌─────────────┐
    │ P01     │       │ P02         │     │ P05/P06     │
    │ SubAgent│       │ 边界不清晰  │     │ 上下文污染  │
    │ 缺失    │       │             │     │             │
    └────┬────┘       └──────┬──────┘     └──────┬──────┘
         │                   │                   │
         │                   │                   │
         ▼                   ▼                   ▼
    ┌─────────────────────────────────────────────────┐
    │              协作失效                            │
    │  Agent 无法调用 → 边界模糊 → 上下文污染         │
    │  → 输出不可靠 → 无法无人值守                    │
    └─────────────────────────────────────────────────┘
         │                   │                   │
         ▼                   ▼                   ▼
    ┌─────────┐       ┌─────────────┐     ┌─────────────┐
    │ P03     │       │ P04         │     │ P07/P08/P09 │
    │ 鉴权缺失│       │ 交互格式    │     │ 工程化缺失  │
    │         │       │ 不严格      │     │             │
    └─────────┘       └─────────────┘     └─────────────┘
```

---

## 四、改进优先级建议

| 优先级 | 问题编号 | 改进方向 | 预期收益 |
|-------|---------|---------|---------|
| **P0** | P01 | 添加 `subagents:` YAML 字段，定义调用链 | Agent 可真正协作 |
| **P0** | P06 | 添加硬性检查点："无工具调用 → 输出 BLOCKED" | 阻止幻觉输出 |
| **P0** | P05 | 核心指令外置到 `.autoworkflow/agent-instructions/` | 避免上下文污染 |
| **P1** | P02 | 重新定义职责矩阵，明确"何时用哪个 Agent" | 清晰的使用指南 |
| **P1** | P04 | 统一使用 JSON Schema 定义输入/输出 | Agent 间可靠通信 |
| **P1** | P03 | 设计 `permission-guard` Agent | 支持无人值守 |
| **P2** | P07 | 将 Skills 升级为真正的能力封装 | 可复用性提升 |
| **P2** | P08 | 添加重试策略、死循环检测、回滚机制 | 健壮性提升 |
| **P2** | P09 | 添加会话 ID 和恢复协议 | 可续接性提升 |

---

## 五、下一步行动

1. 将改进思路提炼到 `01_DesignBaseLines/` 目录
2. 针对 P0 级问题设计具体改进方案
3. 逐个问题迭代改进

---

> 文档结束
