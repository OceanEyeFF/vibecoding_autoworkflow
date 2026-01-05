# AutoWorkflow - Claude Code Agent 工具链

> **aw-kernel**: 一套专为 Claude Code 设计的 Agent + Skill 工具链，覆盖需求澄清 → 计划 → 实现 → 测试 → 交付的完整闭环。

## 特性

- **命名空间隔离**：`aw-kernel` 命名空间设计，支持多版本并存，避免冲突
- **全局安装**：一次安装，所有项目复用
- **专业 Agents**：代码分析、需求澄清、功能交付、日志分析等专业 Agent
- **Skill 工作流**：autodev 开发流程、Git worktree 管理等
- **跨平台支持**：Linux/macOS/WSL 和 Windows PowerShell

## 快速开始

### 1. 全局安装（推荐）

将 Agents 和 Skills 安装到 `~/.claude/` 全局目录，所有项目可用：

**Linux/macOS/WSL:**
```bash
bash Claude/scripts/install-global.sh
```

**Windows PowerShell:**
```powershell
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1
```

**安装结果：**
```
~/.claude/
├── agents/aw-kernel/           # Agents
│   ├── code-analyzer.md
│   ├── feature-shipper.md
│   ├── requirement-refiner.md
│   └── ...
├── skills/aw-kernel/           # Skills
│   ├── autodev/
│   └── autodev-worktree/
└── commands/aw-kernel/         # Commands（如有）
```

### 2. 验证安装

```bash
# Linux/macOS
ls -la ~/.claude/agents/aw-kernel/

# Windows PowerShell
Get-ChildItem $env:USERPROFILE\.claude\agents\aw-kernel\
```

### 3. 使用 Agent

在任意项目中启动 Claude Code，选择对应的 Agent：

- **feature-shipper**：功能交付闭环（spec → plan → implement → test → deliver）
- **code-analyzer**：代码分析与架构洞察
- **requirement-refiner**：需求澄清与 DoD 细化
- **code-debug-expert**：调试专家
- **system-log-analyzer**：系统日志分析
- **code-project-cleaner**：代码清理与重构

## 安装选项

### 预览模式（不实际安装）

```bash
# Linux/macOS/WSL
bash Claude/scripts/install-global.sh --dry-run

# Windows
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1 -DryRun
```

### 强制覆盖安装

```bash
# Linux/macOS/WSL
bash Claude/scripts/install-global.sh --force

# Windows
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1 -Force
```

### 自定义命名空间

```bash
# Linux/macOS/WSL
bash Claude/scripts/install-global.sh --namespace my-custom

# Windows
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1 -Namespace my-custom
```

### 卸载

```bash
# Linux/macOS/WSL
bash Claude/scripts/install-global.sh --uninstall --namespace aw-kernel

# Windows
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1 -Uninstall -Namespace aw-kernel
```

## 目录结构

```
AutoWorkflow/
├── Claude/                         # Claude Code 源资产
│   ├── agents/aw-kernel/           # Agents（命名空间隔离）
│   │   ├── code-analyzer.md        # 代码分析 Agent
│   │   ├── code-debug-expert.md    # 调试专家 Agent
│   │   ├── code-project-cleaner.md # 代码清理 Agent
│   │   ├── feature-shipper.md      # 功能交付 Agent
│   │   ├── requirement-refiner.md  # 需求澄清 Agent
│   │   ├── system-log-analyzer.md  # 日志分析 Agent
│   │   ├── CLAUDE.md               # Agent 全局配置
│   │   └── TOOLCHAIN.md            # 工具链说明
│   ├── skills/aw-kernel/           # Skills（命名空间隔离）
│   │   ├── autodev/                # 自动化开发流程
│   │   └── autodev-worktree/       # Git worktree 管理
│   ├── assets/                     # 通用资源
│   │   └── templates/              # 配置模板
│   └── scripts/                    # 脚本工具
│       ├── install-global.sh       # 全局安装脚本（Linux/macOS）
│       ├── install-global.ps1      # 全局安装脚本（Windows）
│       └── README.md               # 脚本详细文档
├── ClaudeCodeAgentDocuments/       # 设计文档（归档）
└── README.md                       # 本文件
```

## Agent 说明

| Agent | 用途 | 核心能力 |
|-------|------|----------|
| **feature-shipper** | 功能交付闭环 | Spec 打磨 → Plan → Implement → Gate → Deliver |
| **code-analyzer** | 代码分析 | 架构洞察、依赖分析、代码质量评估 |
| **requirement-refiner** | 需求澄清 | DoD 细化、边界确认、验收标准 |
| **code-debug-expert** | 调试专家 | 问题定位、根因分析、修复建议 |
| **system-log-analyzer** | 日志分析 | 日志解读、异常检测、趋势分析 |
| **code-project-cleaner** | 代码清理 | 死代码清理、重构建议、依赖优化 |

## Skill 说明

| Skill | 用途 | 核心功能 |
|-------|------|----------|
| **autodev** | 自动化开发 | 需求分析 → 任务拆解 → 迭代开发 → 测试验证 |
| **autodev-worktree** | Worktree 管理 | 并行开发分支、隔离工作区、智能合并 |

## 命名空间设计

采用命名空间隔离机制，支持多版本并存：

```
~/.claude/
├── agents/
│   ├── aw-kernel/     # 核心版本（本仓库默认）
│   ├── aw-dev/        # 开发/实验版本
│   └── my-custom/     # 自定义版本
├── skills/
│   ├── aw-kernel/
│   ├── aw-dev/
│   └── my-custom/
└── commands/
    └── ...
```

**命名空间优势**：
- 不同来源的 Agents 不会冲突
- 支持多版本并存（稳定版 + 开发版）
- 便于团队协作（团队共享 + 个人定制）
- 安装/卸载独立管理

## 文档索引

- [安装脚本详细文档](Claude/scripts/README.md)
- [设计基线文档](ClaudeCodeAgentDocuments/01_DesignBaseLines/README.md)

## 兼容性

- **Claude Code**: 全版本支持
- **操作系统**: Linux, macOS, Windows (PowerShell 5.1+), WSL/WSL2
- **Shell**: Bash, Zsh, PowerShell

## 致谢

感谢使用 AutoWorkflow！如有问题或建议，欢迎提交 Issue / PR。

---

**aw-kernel** - AutoWorkflow Kernel | 专为 Claude Code 设计的专业工具链 ฅ'ω'ฅ
