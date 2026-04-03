# 文档路由中心

> **本文档是项目的「路由器」**，帮助您快速找到所需文档和资源。

## 当前开发方向（小需求更稳）

- 范围与非目标：以 `CLAUDE.md` 的"当前开发方向/非目标"为准；大任务必须先拆分后再进入流程。
- 工作流文档（单一事实源）：[`AUTODEV_小任务工作流.md`](AUTODEV_小任务工作流.md) - 包含流程设计、角色定义、实施参考

## 🎯 快速导航

### 按角色快速进入

**👨‍💼 项目管理者**
- [分析精华](docs/analysis/autodev-insights.md) - 理解失败模式与改进抓手
- [路线图](ROADMAP.md) - 掌握优化优先级与里程碑

**👨‍💻 Claude Code 用户**
- [快速开始](README.md#快速开始) - 5分钟上手
- [Agent 列表](#agents) - 选择合适工具
- [Skill 列表](#skills) - 了解工作流
- [Prompt 模板](docs/operations/prompt-templates/) - repo-side contract 执行模板

**🔧 开发者**
- [源资产目录](Claude/README.md) - 了解目录结构
- [安装脚本](Claude/scripts/README.md) - 详细安装选项
- [设计基线](ClaudeCodeAgentDocuments/01_DesignBaseLines/README.md) - 理解设计理念

### 按任务类型快速定位

| 任务类型 | 首选工具 | 备选工具 |
|---------|---------|---------|
| **新功能开发** | [autodev Skill](Claude/skills/aw-kernel/autodev/SKILL.md) | [ship Agent](Claude/agents/aw-kernel/ship.md) |
| **代码分析** | [review Agent](Claude/agents/aw-kernel/review.md) | - |
| **日志分析** | [logs Agent](Claude/agents/aw-kernel/logs.md) | - |
| **清理重构** | [clean Agent](Claude/agents/aw-kernel/clean.md) | - |
| **需求澄清** | [clarify Agent](Claude/agents/aw-kernel/clarify.md) | - |
| **资料研究** | [knowledge-researcher Agent](Claude/agents/aw-kernel/knowledge-researcher.md) | - |

---

## 🤖 Agents

> **用途**：单任务专家，每个Agent专注一个领域

### 核心 Agents

| Agent | 文件 | 何时使用 | 核心能力 |
|-------|------|---------|----------|
| **ship** | [ship.md](Claude/agents/aw-kernel/ship.md) | 功能开发闭环 | Spec → Plan → Implement → Test → Deliver |
| **review** | [review.md](Claude/agents/aw-kernel/review.md) | 代码结构分析 | 架构洞察、依赖分析、质量评估 |
| **logs** | [logs.md](Claude/agents/aw-kernel/logs.md) | 日志分析诊断 | 日志解读、异常检测、趋势分析 |
| **clean** | [clean.md](Claude/agents/aw-kernel/clean.md) | 代码清理重构 | 死代码清理、重构建议、依赖优化 |
| **clarify** | [clarify.md](Claude/agents/aw-kernel/clarify.md) | 需求澄清细化 | DoD细化、边界确认、验收标准 |
| **knowledge-researcher** | [knowledge-researcher.md](Claude/agents/aw-kernel/knowledge-researcher.md) | 技术资料研究与归档 | 官方文档检索、最佳实践整理、知识沉淀 |

### 位置
```
Claude/agents/aw-kernel/
├── ship.md                      # 功能交付
├── review.md                    # 代码分析
├── logs.md                      # 日志分析
├── clean.md                     # 代码清理
├── clarify.md                   # 需求澄清
└── knowledge-researcher.md      # 资料研究
```

### Agent 使用提示
- ✅ **每个Agent专注一个领域**（避免万能主义）
- ✅ **输入明确，输出结构化**（JSON格式）
- ✅ **No Evidence, No Output**（必须有证据支撑）
- ❌ **不要串行调用多个Agent**（使用Skill工作流）

---

## ⚡ Skills

> **用途**：多任务工作流编排，连接多个Agent完成复杂流程

### 核心 Skills

| Skill | 目录 | 何时使用 | 核心能力 |
|-------|------|---------|----------|
| **autodev** | [autodev/](Claude/skills/aw-kernel/autodev/SKILL.md) | 自动化开发流程 | 需求分析 → 任务拆解 → 迭代开发 → 交付 |
| **autodev-worktree** | [autodev-worktree/](Claude/skills/aw-kernel/autodev-worktree/SKILL.md) | 并行开发管理 | Git worktree、隔离工作区、智能合并 |
| **review-loop** | [review-loop/](Claude/skills/aw-kernel/review-loop/SKILL.md) | 代码评审修复闭环 | 审查→修复→复查→integration worktree 统一验证 |
| **task-list-workflow** | [task-list-workflow/](Claude/skills/aw-kernel/task-list-workflow/SKILL.md) | 多任务清单执行 | 任务检测→Batch 执行→Integration Gate |

### 位置
```
Claude/skills/aw-kernel/
├── autodev/                     # 自动化开发流程
│   ├── SKILL.md
│   └── v0.1/
├── autodev-worktree/            # Worktree管理
│   └── SKILL.md
├── review-loop/                 # 代码审查修复闭环
│   └── SKILL.md
└── task-list-workflow/          # 多任务清单执行
    └── SKILL.md
```

### Skill 使用提示
- ✅ **适合复杂流程**（多阶段、多Agent协作）
- ✅ **用户一个命令启动**（简化操作）
- ✅ **可配置参数**（适应不同场景）
- ❌ **不要用于单次任务**（用Agent即可）

---

## 📦 安装与配置

### 安装位置
```
~/.claude/                    # 全局安装目录
├── agents/aw-kernel/         # Agents（从 Claude/agents/aw-kernel/ 安装）
├── skills/aw-kernel/          # Skills（从 Claude/skills/aw-kernel/ 安装）
└── commands/aw-kernel/       # Commands（如有）
```

### 安装方式

**Linux/macOS/WSL:**
```bash
bash Claude/scripts/install-global.sh
```

**Windows PowerShell:**
```powershell
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1
```

### 安装选项

| 选项 | 说明 | 适用场景 |
|------|------|---------|
| `--dry-run` | 预览模式（不实际安装） | 了解安装内容 |
| `--force` | 强制覆盖安装 | 强制更新 |
| `--namespace <name>` | 自定义命名空间 | 多版本并存 |
| `--uninstall` | 卸载 | 清理环境 |

### 详细文档
- [安装脚本详细文档](Claude/scripts/README.md)

---

## 📚 文档体系

### 文档类型与职责

| 类型 | 职责 | 示例 |
|------|------|------|
| **宪法文档** | 协作规则与禁区 | [CLAUDE.md](CLAUDE.md) |
| **项目文档** | 项目介绍与快速开始 | [README.md](README.md) |
| **索引文档** | 文档路由与快速导航 | [INDEX.md](INDEX.md)（本文件） |
| **技术文档** | 详细技术说明 | Agent、Skill、脚本文档 |
| **设计文档** | 设计理念与架构 | [设计基线](ClaudeCodeAgentDocuments/01_DesignBaseLines/README.md) |
| **分析文档** | 问题分析与改进 | [分析精华](docs/analysis/autodev-insights.md) |

### 按使用频率分类

#### 🔥 常用（每天）
- [CLAUDE.md](CLAUDE.md) - 协作规则
- [INDEX.md](INDEX.md) - 文档路由（本文件）
- Agent文档 - 工具使用

#### 📖 常用（每周）
- [README.md](README.md) - 项目介绍
- Skill文档 - 工作流执行
- [安装脚本](Claude/scripts/README.md) - 安装配置

#### 📚 备用（每月）
- [设计基线](ClaudeCodeAgentDocuments/01_DesignBaseLines/README.md) - 设计理解
- [分析精华](docs/analysis/autodev-insights.md) - 失败模式与改进要点
- [路线图](ROADMAP.md) - 改进排期与里程碑

---

## 📁 目录结构（完整地图）

```
AutoWorkflow/
├── 📄 CLAUDE.md                    # 【宪法】协作规则与禁区
├── 📄 README.md                    # 【项目】项目介绍与快速开始
├── 📄 INDEX.md                     # 【索引】文档路由中心（本文件）
├── 📄 ROADMAP.md                   # 【项目】路线图
├── 📄 AUTODEV_小任务工作流.md      # 【SoT】工作流设计与实施参考（合并版）
│
├── 📁 Claude/                      # 【源资产】Claude Code 资源
│   ├── 📁 agents/aw-kernel/       # 【技术】Agents
│   │   ├── ship.md
│   │   ├── review.md
│   │   ├── logs.md
│   │   ├── clean.md
│   │   ├── clarify.md
│   │   └── knowledge-researcher.md
│   │
│   ├── 📁 docs/aw-kernel/          # 【配置】Agent 全局配置与规范
│   │   ├── CLAUDE.md              # Agent全局配置
│   │   ├── STANDARDS.md           # 失败处理规范
│   │   ├── LOGGING.md             # 日志系统
│   │   ├── VERSIONING.md          # 版本管理
│   │   ├── CHANGELOG.md           # 变更日志
│   │   ├── TOOLCHAIN.md           # 工具链说明
│   │   └── reports/               # 报告目录
│   │
│   ├── 📁 skills/aw-kernel/        # 【技术】Skills
│   │   ├── autodev/
│   │   ├── autodev-worktree/
│   │   ├── review-loop/
│   │   └── task-list-workflow/
│   │
│   ├── 📁 assets/                  # 【通用】模板资源
│   │   └── templates/
│   │
│   ├── 📁 scripts/                 # 【工具】脚本工具
│   │   ├── install-global.sh
│   │   ├── install-global.ps1
│   │   ├── claude_autoworkflow.py
│   │   ├── claude_aw.sh
│   │   ├── claude_aw.ps1
│   │   └── README.md              # 脚本说明
│   │
│   └── 📄 README.md                # 【技术】源资产说明
│
├── 📁 ClaudeCodeAgentDocuments/    # 【设计】设计文档
│   ├── 📁 01_DesignBaseLines/      # 设计基线
│   │   ├── README.md              # 设计基线索引
│   │   ├── autodev-architecture-v2.md
│   │   ├── autodev-iteration-plan.md
│   │   ├── IDEA-005-localized-instruction-cache.md
│   │   ├── IDEA-006-mandatory-data-access.md
│   │   ├── 📁 IDEA-006-implementation/
│   │   └── 📁 archived/           # 已归档设计
│   │
│   └── 📁 00_TempFiles/           # 临时文件
│
├── 📁 docs/                       # 【用户】附加文档
│   ├── README.md                  # docs 目录入口
│   ├── AI高效使用指南.md
│   ├── 📁 analysis/               # 【分析】精华沉淀
│       ├── README.md
│       └── autodev-insights.md
│   └── 📁 operations/             # 【运行】runbook 与执行模板
│       ├── README.md
│       └── 📁 prompt-templates/
│           ├── simple-subagent-workflow.md
│           ├── strict-subagent-workflow.md
│           ├── execution-contract-template.md
│           ├── harness-contract-template.json
│           ├── review-loop-code-review.md
│           ├── repo-governance-evaluation.md
│           ├── task-planning-contract.md
│           └── task-list-subagent-workflow.md
│
├── 📁 archive/                    # 【归档】历史文档
│   ├── work-docs/                 # 【归档】工作留档（阶段性记录）
│   │   ├── OPTIMIZATION_SUMMARY.md
│   │   ├── DOCUMENTATION_OPTIMIZATION_REPORT.md
│   │   └── ROADMAP_legacy_v0.2.md
│   ├── claude-agents/
│   └── Trae-agents/
│
└── 📁 Claude_Official_Docs/       # 【外部】官方文档映射
    ├── README.md
    ├── skills.md
    ├── hooks-guide.md
    └── ...
```

### 图例说明
- 📄 文档文件
- 📁 目录
- 【类型】文档分类

---

## 🔍 搜索指南

### 文档内容搜索

**已知文档名**：
- 直接在对应目录查找
- 使用 [INDEX.md](#) 导航

**未知文档名**：
- 搜索文档内容：`rg "关键词" -g "*.md" --type md`

**代码搜索**：
- 搜索Agent实现：`rg "agent_name" --type md`

### 快速查找技巧

1. **按角色**：管理者看 [docs/analysis/](docs/analysis/)，开发者看 [Claude/](Claude/)
2. **按类型**：宪法看 [CLAUDE.md](CLAUDE.md)，索引看 [INDEX.md](INDEX.md)
3. **按任务**：开发看 [autodev](Claude/skills/aw-kernel/autodev/SKILL.md)，分析看 [review](Claude/agents/aw-kernel/review.md)

---

## ⚠️ 重要提示

### 文档使用规范
- ✅ **首次使用项目**：先读 [CLAUDE.md](CLAUDE.md) 了解规则
- ✅ **寻找资源**：使用 [INDEX.md](INDEX.md) 快速导航
- ✅ **具体任务**：只读相关Agent/Skill文档
- ❌ **不要同时读多个同类文档**（避免冲突）

### 维护规范
- ✅ **新增文档前检查重复**（避免信息冗余）
- ✅ **明确「何时读我」**（标注使用场景）
- ✅ **每月评估价值**（删除低价值文档）
- ❌ **不要在多个地方写相同内容**（避免同步困难）

---

**版本**：v1.0
**最后更新**：2026-01-11
**维护者**：浮浮酱
