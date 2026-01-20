# aw-kernel 文档与配置

> **目录说明**：本目录存放 aw-kernel Agent 体系的全局配置、规范文档和开发指南。

## 📁 目录结构

```
Claude/docs/aw-kernel/
├── README.md              # 本文件 - 目录说明
├── CLAUDE.md              # Agent 全局配置与使用指南
├── CHANGELOG.md           # 变更日志
├── STANDARDS.md           # 失败处理规范
├── LOGGING.md             # 日志系统说明
├── TOOLCHAIN.md           # 工具链说明（.autoworkflow）
├── VERSIONING.md          # 版本管理规范
└── reports/               # 报告目录
    └── RECHECK-REPORT.md  # Agent 重检报告
```

## 📋 文档说明

### 核心配置

| 文档 | 用途 | 何时读 |
|------|------|--------|
| **CLAUDE.md** | Agent 全局配置与使用指南 | 首次使用 aw-kernel Agent / 不确定 Agent 职责时 |
| **STANDARDS.md** | 失败处理规范 | 需要了解错误处理标准 / Agent 失败时如何响应 |
| **LOGGING.md** | 日志系统说明 | 需要查看 Agent 执行日志 / 配置日志系统时 |

### 工具与规范

| 文档 | 用途 | 何时读 |
|------|------|--------|
| **TOOLCHAIN.md** | .autoworkflow 工具链说明 | 需要使用跨会话状态管理 / Gate 命令时 |
| **VERSIONING.md** | 版本管理规范 | 修改 Agent 文件时 / 需要了解版本号规则时 |
| **CHANGELOG.md** | 变更日志 | 需要查看历史变更 / 了解最新更新时 |

### 报告

| 文档 | 用途 |
|------|------|
| **reports/RECHECK-REPORT.md** | Agent 质量重检报告 |

## 🔗 相关目录

- **Agent 定义**: `Claude/agents/aw-kernel/` - Agent 的实际定义文件（12个）
- **资源模板**: `Claude/assets/aw-kernel/templates/` - Agent 使用的模板资源
- **Skills**: `Claude/skills/aw-kernel/` - 工作流编排（如 autodev）

## 📖 使用指南

### 首次使用 aw-kernel

1. **读这些文档**:
   - [CLAUDE.md](CLAUDE.md) - 了解 Agent 全局配置和职责
   - 项目根目录的 [CLAUDE.md](../../../CLAUDE.md) Part 2 - 了解路由表

2. **选择 Agent**:
   - 查看项目根 CLAUDE.md Part 2 的按任务类型路由表
   - 选择合适的 Agent（在 `Claude/agents/aw-kernel/` 目录）

3. **可选：配置工具链**:
   - 如需跨会话状态管理，阅读 [TOOLCHAIN.md](TOOLCHAIN.md)

### 修改 Agent 时

1. **更新版本号**: 参考 [VERSIONING.md](VERSIONING.md)
2. **记录变更**: 更新 [CHANGELOG.md](CHANGELOG.md)
3. **遵循规范**: 参考 [STANDARDS.md](STANDARDS.md)

## ⚠️ 重要提示

- ✅ 本目录的文档是 **配置和规范**，不是 Agent 定义
- ✅ 实际的 Agent 定义在 `Claude/agents/aw-kernel/`
- ✅ 修改本目录文档时，需要考虑对所有 Agent 的影响
- ❌ 不要在本目录存放 Agent 定义文件

## 📊 目录重构历史

**2026-01-20**: 目录结构重构
- **原因**: 配置/文档文件混在 Agent 定义目录中，职责不清
- **变更**:
  - 移动 7 个配置/文档文件到 `Claude/docs/aw-kernel/`
  - 移动资源目录到 `Claude/assets/aw-kernel/templates/`
  - `Claude/agents/aw-kernel/` 现在只包含 Agent 定义文件（12个）
- **好处**: 职责单一，易于维护和查找

---

**版本**: v1.0
**最后更新**: 2026-01-20
**维护者**: 浮浮酱
