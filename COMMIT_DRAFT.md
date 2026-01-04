# Git Commit Message Draft

## 提交类型
```
refactor(Claude): 实现命名空间隔离，重组源目录结构为 aw-kernel
```

## 详细描述

### 📋 变更摘要

将 `Claude/` 源目录重组为命名空间隔离架构，采用 `aw-kernel` 作为默认命名空间，使源目录结构与安装后的 `~/.claude/` 目录完全一致。

### 🎯 核心改进

#### 1. 命名空间隔离设计
- **重组前**：扁平结构 `Claude/agents/*.md`
- **重组后**：命名空间隔离 `Claude/agents/aw-kernel/*.md`
- **收益**：源目录与安装目标一致，支持多命名空间并存

#### 2. 层次结构优化
- **assets/** 从 `Claude/agents/assets/` 提升到 `Claude/assets/`
- **scripts/** 合并工作流脚本到 `Claude/scripts/`（含 autoworkflow.py）
- **职责分离**：通用资源与 Agent 专属内容明确区分

#### 3. 安装脚本适配
- 更新 `install-global.sh` 路径为 `$CLAUDE_SRC/agents/aw-kernel/`
- 更新 `install-global.ps1` 路径为 `$CLAUDE_SRC\agents\aw-kernel\`
- 更新 Skills 路径为 `$CLAUDE_SRC/skills/aw-kernel/`

### 📁 新目录结构

```
Claude/
├── README.md
├── agents/
│   └── aw-kernel/                  # 命名空间隔离
│       ├── code-analyzer.md
│       ├── code-debug-expert.md
│       ├── code-project-cleaner.md
│       ├── feature-shipper.md
│       ├── requirement-refiner.md
│       ├── system-log-analyzer.md
│       ├── CLAUDE.md
│       ├── TOOLCHAIN.md
│       └── RECHECK-REPORT.md
├── skills/
│   └── aw-kernel/                  # 命名空间隔离
│       ├── autodev/
│       └── autodev-worktree/
├── assets/                         # 提升到上层
│   └── templates/
│       ├── agent-config.json
│       ├── spec-template.md
│       ├── state-template.md
│       └── tools/
└── scripts/                        # 统一管理
    ├── claude_autoworkflow.py      # 工作流脚本
    ├── claude_aw.ps1               # 入口脚本
    ├── claude_aw.sh                # 入口脚本
    ├── install-global.sh           # 安装脚本（已更新路径）
    ├── install-global.ps1          # 安装脚本（已更新路径）
    └── README.md
```

### 🔄 文件移动详情

#### Agents (9 个文件)
- 从：`Claude/agents/*.md`
- 到：`Claude/agents/aw-kernel/*.md`
- 包括：code-analyzer, feature-shipper, requirement-refiner, code-debug-expert, system-log-analyzer, code-project-cleaner, CLAUDE.md, TOOLCHAIN.md, RECHECK-REPORT.md

#### Skills (2 个目录)
- 从：`Claude/skills/autodev/`, `Claude/skills/autodev-worktree/`
- 到：`Claude/skills/aw-kernel/autodev/`, `Claude/skills/aw-kernel/autodev-worktree/`

#### Assets（提升到上层）
- 从：`Claude/agents/assets/`
- 到：`Claude/assets/`
- 包括：templates/, agent-config.json, spec/state-template.md, tools/

#### Scripts（合并到上层）
- 从：`Claude/agents/scripts/`
- 到：`Claude/scripts/`
- 合并：claude_autoworkflow.py, claude_aw.ps1, claude_aw.sh

### ✅ 验证结果

- ✓ 9 个 Agent 文件位于 `aw-kernel/`
- ✓ 2 个 Skills 位于 `aw-kernel/`
- ✓ assets/ 成功提升到上层
- ✓ scripts/ 成功合并（6 个文件）
- ✓ 旧嵌套目录已清理
- ✓ 安装脚本路径已更新

### 🎨 命名空间设计

**默认命名空间**：`aw-kernel` (AutoWorkflow Kernel)
- 与现有 "autoworkflow" 品牌对齐
- 明确标识为核心组件
- 避免与其他来源 Agents 冲突

**未来扩展**：
- `aw-custom` - 个人定制版本
- `aw-dev` - 开发/实验版本
- `project-name` - 项目专用 Agents

### 📊 变更统计

**删除**：21 个旧位置文件（7204 行）
**新增**：相同内容重新组织到命名空间结构

**净变更**：
- 目录层次更清晰
- 命名空间隔离机制建立
- 安装脚本适配完成

### 🔗 相关文档

- 命名空间设计：[Claude/scripts/README.md](Claude/scripts/README.md)
- 安装脚本：[install-global.sh](Claude/scripts/install-global.sh), [install-global.ps1](Claude/scripts/install-global.ps1)

---

## Breaking Changes

⚠️ **安装脚本内部路径变更**（对用户透明）

虽然脚本内部从 `Claude/agents/` 改为 `Claude/agents/aw-kernel/` 读取，但：
- 安装命令保持不变
- 安装后目录保持为 `~/.claude/agents/aw-kernel/`
- 用户无需修改任何配置

## 兼容性

✅ **完全向后兼容**
- 已安装的 `~/.claude/agents/aw-kernel/` 不受影响
- 安装命令和参数完全相同
- 文档和使用方式无变化

---

**Commit Type**: `refactor`
**Scope**: `Claude`
**Subject**: 实现命名空间隔离，重组源目录结构为 aw-kernel

**浮浮酱 ฅ'ω'ฅ**
