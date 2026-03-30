# Claude/ 源资产目录

本目录存放 Claude Code 的**源资产**（Agents / Skills / Commands），采用 `aw-kernel` 命名空间隔离设计。

## 目录结构

```
Claude/
├── agents/aw-kernel/           # Agents（命名空间隔离）
│   ├── code-analyzer.md        # 代码分析 Agent
│   ├── code-debug-expert.md    # 调试专家 Agent
│   ├── code-project-cleaner.md # 代码清理 Agent
│   ├── feature-shipper.md      # 功能交付 Agent
│   ├── requirement-refiner.md  # 需求澄清 Agent
│   ├── system-log-analyzer.md  # 日志分析 Agent
│   ├── CLAUDE.md               # Agent 全局配置
│   ├── STANDARDS.md            # 失败处理规范
│   ├── TOOLCHAIN.md            # 工具链说明
│   └── RECHECK-REPORT.md       # 复查报告
├── skills/aw-kernel/           # Skills（命名空间隔离）
│   ├── autodev/                # 自动化开发流程
│   │   ├── SKILL.md
│   │   └── v0.1/
│   ├── autodev-worktree/       # Git worktree 管理
│   │   └── SKILL.md
│   └── review-loop/            # PR/commit 审查修复闭环
│       └── SKILL.md
├── assets/                     # 通用资源
│   └── templates/              # 配置模板
│       ├── agent-config.json
│       ├── spec-template.md
│       ├── state-template.md
│       └── tools/
└── scripts/                    # 脚本工具
    ├── install-global.sh       # 全局安装（Linux/macOS/WSL）
    ├── install-global.ps1      # 全局安装（Windows）
    ├── claude_autoworkflow.py  # 工作流脚本
    ├── claude_aw.sh            # 入口脚本（Bash）
    ├── claude_aw.ps1           # 入口脚本（PowerShell）
    └── README.md               # 脚本详细文档
```

## 安装方式

### 全局安装（推荐）

将源资产安装到 `~/.claude/` 全局目录，所有项目可用：

**Linux/macOS/WSL:**
```bash
bash Claude/scripts/install-global.sh
```

**Windows PowerShell:**
```powershell
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1
```

**安装后结构：**
```
~/.claude/
├── agents/aw-kernel/           # 从 Claude/agents/aw-kernel/ 安装
├── skills/aw-kernel/           # 从 Claude/skills/aw-kernel/ 安装
└── commands/aw-kernel/         # 从 Claude/commands/（如有）安装
```

### 安装选项

```bash
# 预览模式（不实际安装）
bash Claude/scripts/install-global.sh --dry-run

# 强制覆盖
bash Claude/scripts/install-global.sh --force

# 自定义命名空间
bash Claude/scripts/install-global.sh --namespace my-custom

# 卸载
bash Claude/scripts/install-global.sh --uninstall --namespace aw-kernel
```

详细文档请参阅：[scripts/README.md](scripts/README.md)

## 命名空间设计

采用命名空间隔离机制（`aw-kernel`），与安装后的目录结构完全镜像：

| 源目录 | 安装目标 |
|--------|----------|
| `Claude/agents/aw-kernel/` | `~/.claude/agents/aw-kernel/` |
| `Claude/skills/aw-kernel/` | `~/.claude/skills/aw-kernel/` |

**命名空间优势：**
- 源目录与安装目标结构一致，降低认知成本
- 支持多版本并存（aw-kernel, aw-dev, aw-custom）
- 不同来源的 Agents 不会冲突
- 安装/卸载独立管理

## Agent 列表

| Agent | 文件 | 用途 |
|-------|------|------|
| **feature-shipper** | `feature-shipper.md` | 功能交付闭环（spec → plan → implement → test → deliver） |
| **code-analyzer** | `code-analyzer.md` | 代码分析与架构洞察 |
| **requirement-refiner** | `requirement-refiner.md` | 需求澄清与 DoD 细化 |
| **code-debug-expert** | `code-debug-expert.md` | 调试专家（问题定位、根因分析） |
| **system-log-analyzer** | `system-log-analyzer.md` | 系统日志分析 |
| **code-project-cleaner** | `code-project-cleaner.md` | 代码清理与重构 |

## Skill 列表

| Skill | 目录 | 用途 |
|-------|------|------|
| **autodev** | `autodev/` | 自动化开发流程（需求分析 → 任务拆解 → 迭代开发） |
| **autodev-worktree** | `autodev-worktree/` | Git worktree 并行开发管理 |
| **review-loop** | `review-loop/` | commit/PR/diff 代码审查与修复闭环（含 integration worktree） |

## 开发说明

### 添加新 Agent

1. 在 `Claude/agents/aw-kernel/` 下创建 `new-agent.md`
2. 遵循现有 Agent 的格式和规范
3. 运行安装脚本更新全局目录

### 添加新 Skill

1. 在 `Claude/skills/aw-kernel/` 下创建新目录
2. 创建 `SKILL.md` 定义 Skill
3. 运行安装脚本更新全局目录

### 修改后更新

修改源文件后，重新运行安装脚本即可更新全局目录：

```bash
bash Claude/scripts/install-global.sh --force
```

## 相关链接

- [主 README](../README.md)
- [安装脚本详细文档](scripts/README.md)
- [设计基线文档](../ClaudeCodeAgentDocuments/01_DesignBaseLines/README.md)
