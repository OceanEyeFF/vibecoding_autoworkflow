# AutoWorkflow 工具链集成指南

本文档说明 `feature-shipper` Agent 如何与 `.autoworkflow/` 工具链集成。

---

## 概述

`feature-shipper` Agent 内置自动化能力，支持通过 `.autoworkflow/` 工具链实现：
- 自动化项目诊断与状态管理
- 统一的 Gate 验证机制
- 计划评审与质量门禁
- 执行历史与日志追踪

首次使用时会自动初始化 `.autoworkflow/` 工具链。

---

## 推荐自动流程（懒人一键）

执行顺序（在 Claude Code 中提示用户直接执行或复制到终端）：

1. `aw-init` - 初始化工具链
2. `aw-auto` - 自动诊断项目
3. `autoworkflow plan gen` - 生成执行计划
4. `autoworkflow plan review` - 评审计划（score≥85 才通过）
5. `aw-gate` - 执行验证（如需跳过审核可加 `--allow-unreviewed`，不推荐）

> 随附脚本：`.claude/agents/scripts/claude_aw.ps1` / `.sh` 一键执行 1→5，失败时会将 highlights/tail 追加到 `.autoworkflow/state.md`。

---

## 自动行为

### 1. 启动时

- 检查 `.autoworkflow/` 是否存在；若缺失提示 init
- 可选自动运行 `doctor` 了解项目状态

### 2. 规划/实现时

- 每轮迭代前先 `plan review`；未批准默认阻断继续（可显式 `--allow-unreviewed` 覆盖）
- 每完成一小步，运行 `gate` 验证；失败时提取关键错误行记录到 `state.md`

### 3. 结束时

- 更新 `state.md`
- 释放所有权（如适用）

---

## Claude Code 快捷命令

### Windows / PowerShell

```powershell
# 全局安装版本
powershell -ExecutionPolicy Bypass -File "$HOME\.claude\agents\scripts\claude_aw.ps1" --root . --dry-run

# 项目内安装版本（随仓库分发）
powershell -ExecutionPolicy Bypass -File .claude/agents/scripts/claude_aw.ps1 --root . --dry-run
```

### Linux/WSL (Bash)

```bash
# 全局安装版本
bash ~/.claude/agents/scripts/claude_aw.sh --root .

# 项目内安装版本（随仓库分发）
bash .claude/agents/scripts/claude_aw.sh --root .
```

**脚本参数**：
- `--root` 目标仓库路径
- `--allow-unreviewed` 跳过 plan 审核（谨慎使用）
- `--dry-run` 仅演示不执行

---

## Claude Code 专用命令

> 若使用"项目内安装/随仓库分发"方式，把路径中的 `~/.claude` 替换为 `.claude` 即可。

### 初始化（首次使用）

```bash
python ~/.claude/agents/scripts/claude_autoworkflow.py init
```

### 诊断项目

```bash
python ~/.claude/agents/scripts/claude_autoworkflow.py doctor --write --update-state
```

### 配置 Gate

```bash
python ~/.claude/agents/scripts/claude_autoworkflow.py set-gate --create --test "npm test"
```

### 执行 Gate 验证

```bash
python ~/.claude/agents/scripts/claude_autoworkflow.py gate
```

### 智能模型推荐

```bash
python ~/.claude/agents/scripts/claude_autoworkflow.py recommend-model --intent debug
```

---

## 本地 Gate 统一入口（推荐）

如果项目里已经有 `.autoworkflow/tools/autoworkflow.py`，优先使用它：

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 doctor --write --update-state
```

### WSL/Ubuntu

```bash
bash .autoworkflow/tools/aw.sh doctor --write --update-state
```

其中 `gate` 命令会把最近一次 gate 结果自动写入 `.autoworkflow/state.md`（失败时附带关键失败行与尾部日志），用于减少返工和信息丢失。

**传统方式（兼容）**：
- Windows：运行 `.autoworkflow/tools/gate.ps1`
- WSL/Ubuntu：运行 `.autoworkflow/tools/gate.sh`

---

## 相关文档

- [feature-shipper Agent 文档](../agents/feature-shipper.md) - Agent 核心行为与工作流程
- [仓库 CLAUDE.md 历史](./repo-CLAUDE.md) - 历史文档归档
