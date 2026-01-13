# AutoWorkflow - Claude Code Agent 工具链

> **aw-kernel**: 一套专为 Claude Code 设计的 Agent + Skill 工具链，覆盖需求澄清 → 计划 → 实现 → 测试 → 交付的完整闭环。

## 当前开发方向（小需求更稳）

- 方向：小功能自动化工作流（入口规模 Gate + 需求契约 + 2-3-1 角色编排 + 证据型交付）。
- 范围与非目标：以 `CLAUDE.md` 的“当前开发方向/非目标”为准；大任务必须先拆分后再进入流程。
- 设计文档：
  - [`AUTODEV_小需求更稳流程设计.md`](AUTODEV_小需求更稳流程设计.md)
  - [`AUTODEV_小需求更稳_Agent全量定义.md`](AUTODEV_小需求更稳_Agent全量定义.md)
  - [`AUTODEV_资料萃取_用于Agent重写与工作流实现.md`](AUTODEV_资料萃取_用于Agent重写与工作流实现.md)（背景材料）

## ✨ 核心特性

- **🗂️ 命名空间隔离**：`aw-kernel` 命名空间设计，支持多版本并存，避免冲突
- **🚀 专业 Agents**：7个专业Agent，覆盖代码分析、调试、开发、清理、研究等全流程
- **⚡ Skill 工作流**：autodev 开发流程、Git worktree 管理等复杂工作流编排
- **🔧 强制数据访问**：No Evidence, No Output - 杜绝幻觉输出
- **🌍 跨平台支持**：Linux/macOS/WSL 和 Windows PowerShell

## 🚀 快速开始（5分钟上手）

### 第1步：安装工具

```bash
# Linux/macOS/WSL
bash Claude/scripts/install-global.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1
```

> 详细安装选项请参考：[安装脚本详细文档](Claude/scripts/README.md)

### 第2步：选择合适的工具

根据您的任务类型选择工具：

| 任务类型 | 推荐工具 | 说明 |
|---------|---------|------|
| **新功能开发** | [autodev Skill](Claude/skills/aw-kernel/autodev/SKILL.md) | 完整开发流程，需求→任务→实现→交付 |
| **代码分析** | [code-analyzer Agent](Claude/agents/aw-kernel/code-analyzer.md) | 架构洞察、依赖分析、质量评估 |
| **调试问题** | [code-debug-expert Agent](Claude/agents/aw-kernel/code-debug-expert.md) | 根因分析、调试建议、修复方案 |
| **清理重构** | [code-project-cleaner Agent](Claude/agents/aw-kernel/code-project-cleaner.md) | 死代码清理、重构建议 |
| **需求澄清** | [requirement-refiner Agent](Claude/agents/aw-kernel/requirement-refiner.md) | DoD细化、边界确认 |
| **资料研究** | [knowledge-researcher Agent](Claude/agents/aw-kernel/knowledge-researcher.md) | 官方文档/最佳实践检索与整理 |

### 第3步：启动工具

在任意项目中启动 Claude Code，选择对应的 Agent 或 Skill 即可开始工作。

## 🛠️ 核心工具

### Agents（单任务专家）

| Agent | 核心能力 | 适用场景 |
|-------|---------|---------|
| **feature-shipper** | 功能交付闭环 | 完整功能开发（Spec→Plan→Implement→Test→Deliver） |
| **code-analyzer** | 代码结构分析 | 架构洞察、依赖分析、质量评估 |
| **code-debug-expert** | 问题定位与修复 | 根因分析、调试建议、修复方案 |
| **code-project-cleaner** | 代码清理重构 | 死代码清理、重构建议、依赖优化 |
| **requirement-refiner** | 需求澄清细化 | DoD细化、边界确认、验收标准 |
| **system-log-analyzer** | 日志分析诊断 | 日志解读、异常检测、趋势分析 |
| **knowledge-researcher** | 知识研究与资料沉淀 | 官方文档/最佳实践检索与整理 |

### Skills（工作流编排）

| Skill | 核心能力 | 适用场景 |
|-------|---------|---------|
| **autodev** | 自动化开发流程 | 需求分析 → 任务拆解 → 迭代开发 → 交付 |
| **autodev-worktree** | 并行开发管理 | Git worktree、隔离工作区、智能合并 |

## 📊 核心成就

- ✅ 7 个 aw-kernel Agents：`Claude/agents/aw-kernel/`
- ✅ 2 个核心 Skills：`autodev` / `autodev-worktree`（`Claude/skills/aw-kernel/`）
- ✅ 可选 `.autoworkflow` 工具链：见 [TOOLCHAIN.md](Claude/agents/aw-kernel/TOOLCHAIN.md)

## 📚 文档导航

### 核心文档
- **[CLAUDE.md](CLAUDE.md)** - 项目宪法，协作规则与禁区
- **[INDEX.md](INDEX.md)** - 文档路由中心，快速找到所需资源
- **[快速开始](#快速开始)** - 本章节，5分钟上手指南

### 技术文档
- **[Agent文档](Claude/agents/aw-kernel/)** - 7个专业Agent详细说明
- **[Skill文档](Claude/skills/aw-kernel/)** - 工作流编排详细说明
- **[安装脚本](Claude/scripts/README.md)** - 详细安装选项

### 设计文档
- **[设计基线](ClaudeCodeAgentDocuments/01_DesignBaseLines/README.md)** - 设计理念与架构
- **[分析精华](docs/analysis/autodev-insights.md)** - 失败模式与改进要点（可落地清单）
- **[路线图](ROADMAP.md)** - 改进优先级与里程碑

## 🎯 使用建议

### 正确方式
- ✅ **单次任务用Agent**（专注、高效）
- ✅ **复杂流程用Skill**（编排、自动化）
- ✅ **No Evidence, No Output**（必须有证据支撑）
- ✅ **新任务用新对话**（避免上下文污染）

### 避免方式
- ❌ **不要串行调用多个Agent**（用Skill工作流）
- ❌ **不要超长对话**（复杂任务拆分为多个短对话）
- ❌ **不要无证据输出**（必须引用文件或数据）

## 🔄 持续优化

- 参见：[ROADMAP.md](ROADMAP.md)

## 💡 更多信息

- **完整目录结构** → [INDEX.md#目录结构](INDEX.md#目录结构)
- **安装详细选项** → [Claude/scripts/README.md](Claude/scripts/README.md)
- **设计理念** → [ClaudeCodeAgentDocuments/01_DesignBaseLines/README.md](ClaudeCodeAgentDocuments/01_DesignBaseLines/README.md)

---

**aw-kernel** - AutoWorkflow Kernel | 专为 Claude Code 设计的专业工具链 ฅ'ω'ฅ
