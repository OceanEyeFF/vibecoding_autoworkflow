# Claude Code 安装脚本说明

> 作者：浮浮酱 ฅ'ω'ฅ
> 日期：2026-01-04

---

## 📋 目录结构

```
Claude/scripts/
├── README.md                   # 本文档
├── install-global.sh           # 全局安装脚本 (Linux/macOS/WSL)
├── install-global.ps1          # 全局安装脚本 (Windows PowerShell)
├── claude_autoworkflow.py      # 工作流脚本
├── claude_aw.sh                # 入口脚本（Bash）
└── claude_aw.ps1               # 入口脚本（PowerShell）
```

---

## 🎯 设计理念

### 命名空间隔离

为了避免不同来源的 Agents/Skills 冲突，采用**命名空间隔离**机制：

```
~/.claude/
├── agents/
│   ├── aw-kernel/              # AutoWorkflow Kernel（本仓库默认命名空间）
│   │   ├── code-analyzer.md
│   │   ├── feature-shipper.md
│   │   ├── requirement-refiner.md
│   │   ├── code-debug-expert.md
│   │   ├── ...
│   │   ├── CLAUDE.md           # 使用文档
│   │   ├── TOOLCHAIN.md        # 工具链文档
│   │   └── .installed          # 安装标记文件
│   │
│   ├── my-custom-agents/       # 其他来源的 Agents
│   │   └── ...
│   │
│   └── zcf/                    # 用户自己的 Agents
│       └── ...
│
├── skills/
│   ├── aw-kernel/              # AutoWorkflow Kernel Skills
│   │   ├── autodev/
│   │   ├── autodev-worktree/
│   │   └── ...
│   │
│   └── my-custom-skills/
│       └── ...
│
└── commands/
    └── aw-kernel/
        └── ...
```

### 优势

1. **隔离冲突**：不同来源的同名 Agent 不会互相覆盖
2. **易于管理**：每个命名空间可以独立安装、更新、卸载
3. **清晰追溯**：通过 `.installed` 文件记录安装来源和时间
4. **灵活组织**：用户可以创建多个命名空间，按项目或用途分类

---

## 🚀 快速开始

### 标准安装（推荐）

**Linux / macOS / WSL:**
```bash
cd /path/to/Agents-Prompt
bash Claude/scripts/install-global.sh
```

**Windows PowerShell:**
```powershell
cd C:\path\to\Agents-Prompt
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1
```

安装后，Agents 和 Skills 将位于：
- `~/.claude/agents/aw-kernel/`（AutoWorkflow Kernel）
- `~/.claude/skills/aw-kernel/`

---

## 📖 详细用法

### 安装选项

| 选项 | 说明 | 示例 |
|------|------|------|
| `-n, --namespace` | 指定命名空间 | `--namespace my-agents` |
| `-f, --force` | 强制覆盖已存在文件 | `--force` |
| `-d, --dry-run` | 预览操作但不实际执行 | `--dry-run` |
| `-u, --uninstall` | 卸载指定命名空间 | `--uninstall` |
| `-h, --help` | 显示帮助信息 | `--help` |

### 使用示例

#### 1. 预览安装操作

```bash
# Linux/macOS/WSL
bash Claude/scripts/install-global.sh --dry-run

# Windows
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1 -DryRun
```

#### 2. 使用自定义命名空间

```bash
# Linux/macOS/WSL
bash Claude/scripts/install-global.sh --namespace my-project-agents

# Windows
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1 -Namespace my-project-agents
```

#### 3. 强制覆盖更新

```bash
# Linux/macOS/WSL
bash Claude/scripts/install-global.sh --force

# Windows
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1 -Force
```

#### 4. 卸载命名空间

```bash
# Linux/macOS/WSL
bash Claude/scripts/install-global.sh --uninstall --namespace aw-kernel

# Windows
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1 -Uninstall -Namespace aw-kernel
```

---

## 🛠️ 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CLAUDE_HOME` | Claude Code 全局目录 | `~/.claude` (Linux/macOS)<br>`%USERPROFILE%\.claude` (Windows) |
| `NAMESPACE` | 默认命名空间 | `aw-kernel` |

### 自定义安装位置

```bash
# Linux/macOS/WSL
export CLAUDE_HOME="/custom/path/.claude"
bash Claude/scripts/install-global.sh

# Windows PowerShell
$env:CLAUDE_HOME = "C:\custom\path\.claude"
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1
```

---

## 📂 安装内容

### Agents（7 个）

| Agent | 文件名 | 功能 |
|-------|-------|------|
| feature-shipper | feature-shipper.md | 功能交付中枢 |
| requirement-refiner | requirement-refiner.md | 需求精炼 |
| code-analyzer | code-analyzer.md | 代码架构分析 |
| code-debug-expert | code-debug-expert.md | 系统化调试 |
| system-log-analyzer | system-log-analyzer.md | 日志分析 |
| code-project-cleaner | code-project-cleaner.md | 项目清理 |
| knowledge-researcher | knowledge-researcher.md | 知识研究与资料沉淀 |

### Skills（3 个）

| Skill | 目录 | 功能 |
|-------|------|------|
| autodev | autodev/ | 完整自动化开发工作流 |
| autodev-worktree | autodev-worktree/ | Git Worktree 并行开发 |
| review-loop | review-loop/ | PR/commit/diff 代码审查与修复闭环 |

### 文档

- `CLAUDE.md` - Agents 使用指南
- `TOOLCHAIN.md` - 工具链详细文档

---

## 🔍 验证安装

### 检查安装状态

```bash
# Linux/macOS/WSL
ls -la ~/.claude/agents/aw-kernel/
cat ~/.claude/agents/aw-kernel/.installed

# Windows PowerShell
Get-ChildItem $env:USERPROFILE\.claude\agents\aw-kernel\
Get-Content $env:USERPROFILE\.claude\agents\aw-kernel\.installed
```

### `.installed` 文件示例

```yaml
# 安装信息
namespace: aw-kernel
installed_at: 2026-01-04T10:30:00Z
installed_by: your-username
source_repo: /path/to/Agents-Prompt
version: 1.0.0
```

---

## 🔄 更新与维护

### 更新已安装的 Agents/Skills

```bash
# 1. 更新源仓库
cd /path/to/Agents-Prompt
git pull origin develop

# 2. 强制重新安装
bash Claude/scripts/install-global.sh --force
```

### 维护多个命名空间

```bash
# 安装到不同命名空间
bash Claude/scripts/install-global.sh --namespace project-a
bash Claude/scripts/install-global.sh --namespace project-b

# 列出所有命名空间
ls -d ~/.claude/agents/*/

# 卸载特定命名空间
bash Claude/scripts/install-global.sh --uninstall --namespace project-a
```

---

## 🎨 最佳实践

### 1. 命名空间命名建议

| 场景 | 命名空间 | 说明 |
|------|---------|------|
| 默认安装 | `aw-kernel` | AutoWorkflow Kernel（本仓库默认） |
| 个人定制 | `aw-custom` | 个人修改的 AutoWorkflow 版本 |
| 项目专用 | `project-name` | 特定项目的专用 Agents |
| 实验性 | `aw-dev` | 测试 AutoWorkflow 新功能 |

### 2. 版本管理策略

```bash
# 安装稳定版到默认命名空间（aw-kernel）
bash Claude/scripts/install-global.sh

# 安装开发版到实验命名空间
bash Claude/scripts/install-global.sh --namespace aw-dev

# 在项目中使用不同版本
claude --agent aw-kernel/feature-shipper    # 使用稳定版
claude --agent aw-dev/feature-shipper       # 使用开发版
```

### 3. 团队协作

```bash
# 1. 团队统一使用的命名空间
bash Claude/scripts/install-global.sh --namespace team-agents

# 2. 每个成员创建 .env 或配置文件指定命名空间
export NAMESPACE=team-agents

# 3. CI/CD 环境中使用特定命名空间
bash Claude/scripts/install-global.sh --namespace ci-agents
```

---

## ⚠️ 注意事项

### 1. 文件覆盖

- 默认情况下，安装脚本**不会覆盖**已存在的文件
- 使用 `--force` 选项可以强制覆盖
- 建议在覆盖前备份重要的自定义内容

### 2. 命名空间冲突

- 不同命名空间的 Agents 互不影响
- 同一命名空间内的同名文件会被覆盖（使用 `--force` 时）

### 3. 权限问题

```bash
# 如果遇到权限错误，确保 ~/.claude 目录可写
chmod -R u+w ~/.claude

# Windows 中确保有管理员权限（如果安装到系统目录）
# 或使用用户目录（推荐）
```

### 4. 路径空间

- 脚本会自动处理带空格的路径
- 建议使用不含空格的路径以避免潜在问题

---

## 🐛 故障排查

### 问题 1: 脚本执行权限

**Linux/macOS/WSL:**
```bash
chmod +x Claude/scripts/install-global.sh
bash Claude/scripts/install-global.sh
```

**Windows:**
```powershell
# 临时允许执行脚本
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1
```

### 问题 2: 找不到源目录

```bash
# 确保在仓库根目录执行
cd /path/to/Agents-Prompt
pwd  # 应该显示仓库根目录

# 或使用绝对路径
bash /absolute/path/to/Agents-Prompt/Claude/scripts/install-global.sh
```

### 问题 3: CLAUDE_HOME 不存在

```bash
# 手动创建
mkdir -p ~/.claude/agents ~/.claude/skills ~/.claude/commands

# 或让脚本自动创建（默认行为）
bash Claude/scripts/install-global.sh
```

---

## 📚 相关文档

- [CLAUDE.md](../docs/aw-kernel/CLAUDE.md) - Agents 使用指南
- [TOOLCHAIN.md](../docs/aw-kernel/TOOLCHAIN.md) - 工具链详细文档
- [../README.md](../README.md) - Claude 目录总说明

---

## 🔗 快速链接

| 操作 | Linux/macOS/WSL | Windows PowerShell |
|------|-----------------|-------------------|
| 标准安装 | `bash Claude/scripts/install-global.sh` | `powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1` |
| 预览安装 | `bash Claude/scripts/install-global.sh --dry-run` | `powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1 -DryRun` |
| 强制更新 | `bash Claude/scripts/install-global.sh --force` | `powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1 -Force` |
| 卸载 | `bash Claude/scripts/install-global.sh --uninstall` | `powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1 -Uninstall` |
| 帮助 | `bash Claude/scripts/install-global.sh --help` | `powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1 -Help` |

---

**Happy Coding! ฅ'ω'ฅ**

浮浮酱祝主人使用愉快喵～ o(*￣︶￣*)o
