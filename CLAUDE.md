# CLAUDE.md（本仓库宪法）

> 本文档是本项目的**最高准则**，定义了 Claude Code 协作的根本规则和文档索引机制。

## 🎯 一、项目定位

- **项目名称**：AutoWorkflow - Claude Code Agent 工具链
- **核心价值**：用结构化文档对抗上下文污染，用短对话完成具体任务
- **设计原则**：文档承载项目状态，对话只用于一次性推理

### 1.1 当前开发方向（小功能自动化工作流）

- **范围**：单个小需求/小任务（建议 0.5～2 小时可闭环交付）。
- **目标**：在“小需求”范围内，把工作流做得更稳（入口规模 Gate + 需求契约 + 2-3-1 角色编排 + 证据型交付 + 失败回路）。
- **工作流重构**：优先重构结构与门禁（可审计、可复现），再做体验优化；避免为“未来的大工程”提前过度设计。
- **Agent 长度压缩**：在不牺牲基线表现（诚实度/证据/门禁）的前提下，把公共硬规则下沉到 Skill/Hooks/模板，让单个 Agent 只保留“职责边界 + 输入输出 + 放行标准”。
- **非目标（暂不考虑）**：大规模任务规划/多里程碑计划/长链路 pipeline 编排；超过范围的任务必须先拆分后再进入流程。

### 1.2 单一事实源（SoT）划分

- **工作流结构与门禁标准**：`AUTODEV_小需求更稳流程设计.md`
- **角色职责与产物契约**：`AUTODEV_小需求更稳_Agent全量定义.md`
- **资料萃取（背景材料，非规范）**：`AUTODEV_资料萃取_用于Agent重写与工作流实现.md`

## 📋 二、协作规则（必须遵守）

### 2.1 任务处理原则
- ✅ **新任务 = 新对话**（上下文隔离是正确的）
- ✅ **持久状态必须文档化**（对话不充当长期记忆）
- ✅ **已完成结果必须沉淀为文档**（不做人肉上下文管理器）

### 2.2 文档使用原则
- ✅ **一个文档 = 一个明确职责**
- ✅ **文档必须支持精准、选择性读取**
- ✅ **任何任务只加载「刚好够用」的文档**
- ❌ **无法说明「何时该读我」的文档就是噪声**

### 2.3 Claude Code 使用边界
- ❌ **Agent / Skill / Command 不适合复杂 pipeline 的真相源**
- ❌ **自动触发 ≠ 可编排 ≠ 可复现**
- ✅ **多层架构与流程控制应放在外部代码与文档系统中**

## 📚 三、文档索引（按需查阅）

### 3.1 快速导航（按角色）

**👨‍💼 项目管理者**
- [项目介绍](README.md) - 了解整体架构
- [分析精华](docs/analysis/autodev-insights.md) - 理解失败模式与改进抓手
- [路线图](ROADMAP.md) - 掌握改进优先级与里程碑

**👨‍💻 Claude Code 用户**
- [快速开始](README.md#快速开始) - 5分钟上手
- [Agent 列表](INDEX.md#agents) - 选择合适工具
- [Skill 列表](INDEX.md#skills) - 了解工作流

**🔧 开发者**
- [安装脚本](Claude/scripts/README.md) - 详细安装选项
- [源资产目录](Claude/README.md) - 了解目录结构
- [设计基线](ClaudeCodeAgentDocuments/01_DesignBaseLines/README.md) - 理解设计理念
- [小需求更稳：流程设计](AUTODEV_小需求更稳流程设计.md) - 小功能自动化工作流结构与门禁
- [小需求更稳：Agent 定义](AUTODEV_小需求更稳_Agent全量定义.md) - 角色职责/产物契约/放行标准
- [小需求更稳：资料萃取](AUTODEV_资料萃取_用于Agent重写与工作流实现.md) - 背景材料与可复用条目

### 3.2 按任务类型导航

| 任务类型 | 首选文档 | 备选文档 |
|---------|---------|---------|
| **新功能开发** | [autodev Skill](Claude/skills/aw-kernel/autodev/SKILL.md) | [feature-shipper Agent](Claude/agents/aw-kernel/feature-shipper.md) |
| **代码分析** | [code-analyzer Agent](Claude/agents/aw-kernel/code-analyzer.md) | - |
| **调试问题** | [code-debug-expert Agent](Claude/agents/aw-kernel/code-debug-expert.md) | [system-log-analyzer Agent](Claude/agents/aw-kernel/system-log-analyzer.md) |
| **清理重构** | [code-project-cleaner Agent](Claude/agents/aw-kernel/code-project-cleaner.md) | - |
| **需求澄清** | [requirement-refiner Agent](Claude/agents/aw-kernel/requirement-refiner.md) | - |
| **资料研究** | [knowledge-researcher Agent](Claude/agents/aw-kernel/knowledge-researcher.md) | - |

## 🔍 四、文档职责说明（如何选择）

### 4.1 宪法类文档
| 文档 | 何时读 | 何时不读 | 冲突声明 |
|------|-------|---------|---------|
| **CLAUDE.md（本文件）** | 首次使用项目 • 遇到协作问题 • 需要索引 | 日常开发 • 具体任务执行 | ❌ 与详细技术文档同时读 |
| [INDEX.md](INDEX.md) | 寻找特定资源 • 了解工具清单 | 深度开发 • 问题诊断 | ❌ 与具体Agent文档同时读 |

### 4.2 项目类文档
| 文档 | 何时读 | 何时不读 | 冲突声明 |
|------|-------|---------|---------|
| [README.md](README.md) | 首次了解项目 • 快速上手 | 具体问题解决 • 深度开发 | ❌ 与安装文档同时读 |
| [分析精华](docs/analysis/autodev-insights.md) | 理解根因 • 落地门禁与度量 | 具体任务执行 • 细节实现 | ❌ 与具体Agent文档同时读 |

### 4.3 技术类文档
| 文档 | 何时读 | 何时不读 | 冲突声明 |
|------|-------|---------|---------|
| **Agent 文档** | 具体问题解决 • 功能使用 | 了解整体 • 快速导航 | ❌ 与其他Agent文档同时读 |
| **Skill 文档** | 工作流执行 • 流程编排 | 临时问题 • 单次任务 | ❌ 与Agent文档同时读 |

## ⚠️ 五、禁区与硬约束

### 5.1 禁止事项
- ❌ **禁止将对话当作记忆容器**（必须文档化）
- ❌ **禁止上下文污染**（每次任务只加载必需文档）
- ❌ **禁止超长对话**（复杂任务拆分为多个短对话）
- ❌ **禁止无证据输出**（No Evidence, No Output）

### 5.2 硬约束
- ✅ **新任务必须新对话**（除非明确需要上下文）
- ✅ **完成结果必须文档化**（代码 + 文档）
- ✅ **文档必须明确「何时读我」**（无此声明视为噪声）
- ✅ **Agent 输出必须有证据支撑**（必须引用文件或数据）

## 📊 六、文档质量标准

### 6.1 每个文档必须包含
1. ✅ **我解决什么问题？**（明确价值）
2. ✅ **什么时候才应该被读？**（使用场景）
3. ✅ **读我时，哪些文档不应同时被读？**（冲突声明）

### 6.2 文档维护规范
- ✅ **每月一次价值评估**（删除冗余）
- ✅ **季度一次结构优化**（整合相关）
- ✅ **新增前必须检查重复**（避免爆炸）

## 🎭 七、项目状态（当前阶段）

- **状态**：生产就绪（7个 Agent + 2个 Skill 已部署）
- **版本**：aw-kernel v1.0
- **最后更新**：2026-01-11
- **维护者**：浮浮酱

### 核心成就
- ✅ **强制数据访问机制**（IDEA-006）已应用于全部Agent
- ✅ 历史复盘材料已萃取并沉淀到 `docs/analysis/`
- ✅ **技能工作流**（autodev）已稳定运行

### 持续优化
- 🔄 **统一JSON输出格式**（4/7 Agent已完成）
- 🔄 **本地化指令缓存**（IDEA-005）待评估
- 🔄 **文件协作协议**（.agent-handoff/）待探索

## 🔗 相关链接

- **项目介绍** → [README.md](README.md)
- **文档索引** → [INDEX.md](INDEX.md)
- **安装说明** → [Claude/scripts/README.md](Claude/scripts/README.md)
- **设计理念** → [ClaudeCodeAgentDocuments/01_DesignBaseLines/README.md](ClaudeCodeAgentDocuments/01_DesignBaseLines/README.md)

---

**版本**：v0.3
**最后更新**：2026-01-11
**下次评审**：2026-04-10
