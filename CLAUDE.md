# CLAUDE.md（本仓库宪法）

> 本文档是本项目的最高准则，定义 Claude Code 协作的根本规则与文档路由。

## Part 1: 必读精华

### 项目定位（3句）
AutoWorkflow 是面向小需求交付的 Claude Code Agent 工具链，目标是把 0.5～2 小时内可闭环的任务做稳做快。核心价值是用结构化文档对抗上下文污染，用短对话完成具体任务。设计原则是文档承载状态与证据，对话只用于一次性推理并可审计。

### 核心规则（5铁律）
1. 新任务必须新对话（除非明确要求继承上下文）。
2. 持久状态必须文档化，对话不充当长期记忆。
3. 结果必须证据化并沉淀到文档（No Evidence, No Output）。
4. 只加载刚好够用的文档，禁止上下文污染。
5. 每个文档必须写清楚“何时读我 / 何时不读 / 冲突声明”。

### Agent 快速清单
| 任务/意图 | 首选 Agent | 入口文档 |
|---|---|---|
| 新功能开发 | feature-shipper | [Claude/agents/aw-kernel/feature-shipper.md](Claude/agents/aw-kernel/feature-shipper.md) |
| 代码分析 | code-analyzer | [Claude/agents/aw-kernel/code-analyzer.md](Claude/agents/aw-kernel/code-analyzer.md) |
| 调试问题 | code-debug-expert | [Claude/agents/aw-kernel/code-debug-expert.md](Claude/agents/aw-kernel/code-debug-expert.md) |
| 日志/系统排查 | system-log-analyzer | [Claude/agents/aw-kernel/system-log-analyzer.md](Claude/agents/aw-kernel/system-log-analyzer.md) |
| 清理重构 | code-project-cleaner | [Claude/agents/aw-kernel/code-project-cleaner.md](Claude/agents/aw-kernel/code-project-cleaner.md) |
| 需求澄清 | requirement-refiner | [Claude/agents/aw-kernel/requirement-refiner.md](Claude/agents/aw-kernel/requirement-refiner.md) |
| 资料研究 | knowledge-researcher | [Claude/agents/aw-kernel/knowledge-researcher.md](Claude/agents/aw-kernel/knowledge-researcher.md) |

### 文档路由指南（decision tree）
开始
├─ 是否首次进入项目 / 不确定协作规则？→ 读 Part 1
├─ 是否执行具体任务？
│  ├─ 是 → 读 Part 2「按任务类型路由表」→ 选择对应 Agent/Skill
│  └─ 否 → 继续
├─ 是否在找“某类文档如何读”？→ 读 Part 2「按文档类型路由表」
└─ 是否需要细则、边界或文档原则？→ 读 Part 3

## Part 2: 路由表

### 2.1 按任务类型路由表
| 任务类型 | 首选文档 | 备选文档 |
|---|---|---|
| 新功能开发 | [autodev Skill](Claude/skills/aw-kernel/autodev/SKILL.md) | [feature-shipper Agent](Claude/agents/aw-kernel/feature-shipper.md) |
| 代码分析 | [code-analyzer Agent](Claude/agents/aw-kernel/code-analyzer.md) | - |
| 调试问题 | [code-debug-expert Agent](Claude/agents/aw-kernel/code-debug-expert.md) | [system-log-analyzer Agent](Claude/agents/aw-kernel/system-log-analyzer.md) |
| 清理重构 | [code-project-cleaner Agent](Claude/agents/aw-kernel/code-project-cleaner.md) | - |
| 需求澄清 | [requirement-refiner Agent](Claude/agents/aw-kernel/requirement-refiner.md) | - |
| 资料研究 | [knowledge-researcher Agent](Claude/agents/aw-kernel/knowledge-researcher.md) | - |

### 2.2 按文档类型路由表
| 文档类型 | 级别 | 何时读 | 代表文件 | 冲突/不读 |
|---|---|---|---|---|
| CLAUDE.md Part 1 | L0 必读 | 首次进入项目、协作规则不确定 | 本文件 Part 1 | 不与其他文档并读 |
| Agent 文档 | L1 选读 | 明确任务执行 | Claude/agents/aw-kernel/*.md | 不与其它 Agent 文档并读 |
| Skill 文档 | L1 选读 | 需要工作流步骤/编排 | Claude/skills/**/SKILL.md | 不与同任务的多 Skill 并读 |
| AUTODEV 规范文档 | L1 选读 | 小需求流程与门禁 | AUTODEV_小任务工作流.md | 不与背景/分析文档并读 |
| 项目介绍 | L2 按需 | 了解全局与上手 | README.md | 不在具体任务执行时读 |
| 路线图与计划 | L2 按需 | 了解里程碑与方向 | ROADMAP.md | 不在问题诊断时读 |
| 分析/设计/历史 | L2 按需 | 需要背景或复盘 | docs/analysis/ / ClaudeCodeAgentDocuments/ / archive/ | 不与任务执行并读 |
| 索引清单（已被本表替代） | L2 按需 | 只在需要全量清单时读 | INDEX.md | 默认不读 |

## Part 3: 详细规范

### 3.1 协作规则
- ✅ 新任务 = 新对话（上下文隔离是正确的）
- ✅ 持久状态必须文档化（对话不充当长期记忆）
- ✅ 已完成结果必须沉淀为文档（代码 + 文档）
- ✅ 证据化输出（必须引用文件或数据）
- ❌ 自动触发 ≠ 可编排 ≠ 可复现
- ✅ 多层架构与流程控制应放在外部代码与文档系统中

### 3.2 禁区与硬约束
**禁止事项**
- ❌ 禁止将对话当作记忆容器（必须文档化）
- ❌ 禁止上下文污染（每次任务只加载必需文档）
- ❌ 禁止超长对话（复杂任务拆分为多个短对话）
- ❌ 禁止无证据输出（No Evidence, No Output）

**硬约束**
- ✅ 新任务必须新对话（除非明确需要上下文）
- ✅ 完成结果必须文档化（代码 + 文档）
- ✅ 文档必须明确“何时读我”（无此声明视为噪声）
- ✅ Agent 输出必须有证据支撑（必须引用文件或数据）

### 3.3 文档使用原则
**基本原则**
- ✅ 一个文档 = 一个明确职责
- ✅ 文档必须支持精准、选择性读取
- ✅ 任何任务只加载“刚好够用”的文档
- ❌ 无法说明“何时该读我”的文档就是噪声

**文档三要素**
1. ✅ 我解决什么问题？（明确价值）
2. ✅ 什么时候才应该被读？（使用场景）
3. ✅ 读我时，哪些文档不应同时被读？（冲突声明）

**文档维护规范**
- ✅ 每月一次价值评估（删除冗余）
- ✅ 季度一次结构优化（整合相关）
- ✅ 新增前必须检查重复（避免爆炸）

### 3.4 工具纪律
- ✅ 能用工具确认的内容先调用工具后输出（Read/Grep/Glob/Bash 等）
- ✅ 输出必须可追溯证据：文件路径/命令输出/日志行
- ✅ 无证据即 BLOCKED，并列出所需的工具调用

### 3.5 状态管理
- ✅ 长任务用 `.autoworkflow/state.md` 或 `.autoworkflow/tmp/<agent>-notes.md` 记录中间状态
- ✅ 对话仅保留摘要与结论，不承载长期记忆
- ✅ 每次输出前复查当前仓库状态，避免依赖旧对话

### 3.6 证据化输出
- ✅ 结论必须附证据引用（文件路径/命令输出）
- ✅ 不确定必须明确说明并列出最小补充信息

**单一事实源（SoT）**
- 工作流结构与门禁标准：AUTODEV_小需求更稳流程设计.md
- 角色职责与产物契约：AUTODEV_小需求更稳_Agent全量定义.md
- 资料萃取（背景材料，非规范）：AUTODEV_资料萃取_用于Agent重写与工作流实现.md

---

**版本**：v0.4
**最后更新**：2026-01-16
**下次评审**：2026-04-10
