# AutoWorkflow 资源索引

本仓库提供专为 Claude Code 设计的 Agent + Skill 工具链，采用 `aw-kernel` 命名空间隔离设计。

## 核心资源

### Agents（`Claude/agents/aw-kernel/`）

| Agent | 文件 | 用途 |
|-------|------|------|
| **feature-shipper** | `feature-shipper.md` | 功能交付闭环（spec → plan → implement → test → deliver） |
| **code-analyzer** | `code-analyzer.md` | 代码分析与架构洞察 |
| **requirement-refiner** | `requirement-refiner.md` | 需求澄清与 DoD 细化 |
| **code-debug-expert** | `code-debug-expert.md` | 调试专家（问题定位、根因分析） |
| **system-log-analyzer** | `system-log-analyzer.md` | 系统日志分析 |
| **code-project-cleaner** | `code-project-cleaner.md` | 代码清理与重构 |

### Skills（`Claude/skills/aw-kernel/`）

| Skill | 目录 | 用途 |
|-------|------|------|
| **autodev** | `autodev/` | 自动化开发流程（需求分析 → 任务拆解 → 迭代开发） |
| **autodev-worktree** | `autodev-worktree/` | Git worktree 并行开发管理 |

### 脚本工具（`Claude/scripts/`）

| 脚本 | 用途 |
|------|------|
| `install-global.sh` | 全局安装（Linux/macOS/WSL） |
| `install-global.ps1` | 全局安装（Windows） |
| `claude_autoworkflow.py` | 工作流脚本 |
| `claude_aw.sh` / `claude_aw.ps1` | 入口脚本 |

## 安装

```bash
# Linux/macOS/WSL
bash Claude/scripts/install-global.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1
```

安装后资源位于 `~/.claude/agents/aw-kernel/` 和 `~/.claude/skills/aw-kernel/`。

## 目录结构

```
AutoWorkflow/
├── Claude/                         # 源资产
│   ├── agents/aw-kernel/           # Agents
│   ├── skills/aw-kernel/           # Skills
│   ├── assets/                     # 通用资源
│   └── scripts/                    # 脚本工具
├── ClaudeCodeAgentDocuments/       # 设计文档
│   └── 01_DesignBaseLines/         # 设计基线
├── docs/                           # 附加文档
├── README.md                       # 主文档
└── INDEX.md                        # 本文件
```

## 相关链接

- [主 README](README.md)
- [Claude/ 源资产说明](Claude/README.md)
- [安装脚本文档](Claude/scripts/README.md)
- [设计基线](ClaudeCodeAgentDocuments/01_DesignBaseLines/README.md)
