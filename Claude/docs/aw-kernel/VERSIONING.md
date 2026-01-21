# AW-Kernel 版本管理规范

> 版本：1.0.0
> 创建日期：2026-01-08
> 最后更新：2026-01-08
> 状态：✅ 已发布

---

## 目录

1. [概述](#概述)
2. [版本号规范](#版本号规范)
3. [文档元数据规范](#文档元数据规范)
4. [变更日志规范](#变更日志规范)
5. [版本生命周期](#版本生命周期)
6. [检查清单](#检查清单)

---

## 概述

### 为什么需要版本管理

| 问题 | 影响 | 版本管理解决方案 |
|------|------|-----------------|
| 不知道当前使用的是哪个版本 | 难以追溯问题 | 每个文件头部有版本号 |
| 不知道哪些功能是新增的 | 用户困惑 | CHANGELOG 记录变更 |
| 不知道是否兼容 | 升级风险 | 语义化版本号标识兼容性 |
| 多人协作冲突 | 覆盖他人工作 | 版本号 + 更新日期 |

### 适用范围

本规范适用于 `aw-kernel` 命名空间下的所有资源：

| 类型 | 路径 | 示例 |
|------|------|------|
| **Agents** | `Claude/agents/aw-kernel/*.md` | review.md |
| **Skills** | `Claude/skills/aw-kernel/*/SKILL.md` | autodev/SKILL.md |
| **基础设施文档** | `Claude/agents/aw-kernel/*.md` | LOGGING.md, TOOLCHAIN.md |

---

## 版本号规范

### 语义化版本 (SemVer)

采用 `MAJOR.MINOR.PATCH` 格式：

```
v1.2.3
│ │ └── PATCH: 补丁修复（Bug fix，向后兼容）
│ └──── MINOR: 新功能（向后兼容）
└────── MAJOR: 重大变更（可能不兼容）
```

### 版本号规则

| 变更类型 | 版本号变化 | 示例 |
|---------|-----------|------|
| Bug 修复 | PATCH +1 | 1.0.0 → 1.0.1 |
| 新增功能（兼容） | MINOR +1, PATCH 归零 | 1.0.1 → 1.1.0 |
| 不兼容变更 | MAJOR +1, MINOR/PATCH 归零 | 1.1.0 → 2.0.0 |

### 特殊标识

| 标识 | 含义 | 示例 |
|------|------|------|
| `-alpha` | 内部测试版 | 2.0.0-alpha |
| `-beta` | 公开测试版 | 2.0.0-beta |
| `-rc.N` | 发布候选版 | 2.0.0-rc.1 |

---

## 文档元数据规范

### Agent 元数据

所有 Agent 文件的 YAML frontmatter **必须**包含以下字段：

```yaml
---
name: review
version: 1.0.0
created: 2026-01-06
updated: 2026-01-08
description: |
  Use this agent when you need to analyze code structure...
model: sonnet
tools: Read, Grep, Glob, Bash, TodoWrite
---
```

#### 必需字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `name` | string | Agent 唯一标识符 | `review` |
| `version` | string | 语义化版本号 | `1.0.0` |
| `created` | date | 创建日期 | `2026-01-06` |
| `updated` | date | 最后更新日期 | `2026-01-08` |
| `description` | string | 功能描述（用于 Task 工具选择） | 多行描述 |
| `model` | string | 使用的模型 | `sonnet` / `haiku` / `opus` |
| `tools` | string | 可用工具列表 | `Read, Grep, Glob` |

#### 可选字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `deprecated` | boolean | 是否已废弃 | `true` |
| `superseded_by` | string | 被哪个版本替代 | `review-v2` |
| `min_claude_version` | string | 最低 Claude Code 版本要求 | `1.0.0` |

### Skill 元数据

所有 Skill 文件的 YAML frontmatter **必须**包含：

```yaml
---
name: autodev
version: 0.1.0
created: 2026-01-06
updated: 2026-01-08
description: >
  This skill should be used when the user asks to "开始开发"...
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, AskUserQuestion, Task
agent: false
user-invocable: true
---
```

#### 必需字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `name` | string | Skill 唯一标识符 | `autodev` |
| `version` | string | 语义化版本号 | `0.1.0` |
| `created` | date | 创建日期 | `2026-01-06` |
| `updated` | date | 最后更新日期 | `2026-01-08` |
| `description` | string | 触发条件描述 | 多行描述 |
| `allowed-tools` | string | 可用工具列表 | `Read, Write, Edit` |

#### 可选字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `agent` | boolean | 是否在独立上下文运行 | `true` |
| `user-invocable` | boolean | 是否可通过 `/skill` 调用 | `true` |
| `context` | string | 上下文配置 | `currentContext` |
| `hooks` | string | 关联的 Hooks | `SubagentStop` |

### 基础设施文档元数据

非 Agent/Skill 的基础设施文档，在文件头部使用 blockquote 格式：

```markdown
# 文档标题

> 版本：1.0.0
> 创建日期：2026-01-06
> 最后更新：2026-01-08
> 状态：✅ 已发布

---

正文内容...
```

---

## 变更日志规范

### CHANGELOG.md 位置

```
Claude/agents/aw-kernel/CHANGELOG.md
```

### 格式规范

采用 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 格式：

```markdown
# Changelog

All notable changes to AW-Kernel will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 待发布的新功能

### Changed
- 待发布的变更

### Fixed
- 待发布的修复

---

## [1.1.0] - 2026-01-15

### Added
- review: 支持 Rust 语言分析
- knowledge-researcher: 新增知识获取 Agent

### Changed
- LOGGING.md: 重构为 Hooks 方案

### Fixed
- ship: 修复 Git stash 操作失败问题

---

## [1.0.0] - 2026-01-06

### Added
- 初始版本发布
- 6 个核心 Agents
- 2 个 Skills
- 安装脚本（PowerShell + Bash）
```

### 变更类型

| 类型 | 含义 | 版本影响 |
|------|------|---------|
| **Added** | 新增功能 | MINOR +1 |
| **Changed** | 现有功能变更 | MINOR +1 或 MAJOR +1 |
| **Deprecated** | 即将移除的功能 | MINOR +1 |
| **Removed** | 已移除的功能 | MAJOR +1 |
| **Fixed** | Bug 修复 | PATCH +1 |
| **Security** | 安全修复 | PATCH +1 |

### 更新规则

1. **每次提交**：更新 `[Unreleased]` 部分
2. **发布版本时**：
   - 将 `[Unreleased]` 内容移动到新版本号下
   - 添加发布日期
   - 更新相关文件的 `version` 和 `updated` 字段

---

## 版本生命周期

### 状态定义

| 状态 | 说明 | 元数据标识 |
|------|------|-----------|
| 🚧 开发中 | 功能开发阶段 | `version: x.y.z-alpha` |
| 🧪 测试中 | 内部测试阶段 | `version: x.y.z-beta` |
| ✅ 已发布 | 正式可用 | `version: x.y.z` |
| ⚠️ 已废弃 | 不推荐使用 | `deprecated: true` |
| ❌ 已移除 | 不再可用 | 从代码库删除 |

### 废弃流程

1. **标记废弃**：设置 `deprecated: true` 和 `superseded_by: xxx`
2. **文档说明**：在 CHANGELOG 记录废弃原因和迁移指南
3. **保留期**：至少保留 1 个 MINOR 版本周期
4. **移除**：在下一个 MAJOR 版本移除

### 版本发布流程

```
1. 更新 CHANGELOG.md [Unreleased]
         ↓
2. 确定版本号（根据变更类型）
         ↓
3. 更新各文件的 version 和 updated 字段
         ↓
4. 移动 CHANGELOG 内容到新版本号
         ↓
5. Git commit: "release(aw-kernel): vX.Y.Z"
         ↓
6. Git tag: "aw-kernel-vX.Y.Z"
```

---

## 检查清单

### 创建新文件时

- [ ] 添加完整的 YAML frontmatter
- [ ] 设置初始版本号（通常 `1.0.0` 或 `0.1.0`）
- [ ] 填写 `created` 和 `updated` 日期
- [ ] 更新 CHANGELOG.md 的 `[Unreleased]` 部分

### 修改现有文件时

- [ ] 更新 `updated` 日期
- [ ] 根据变更类型决定是否需要更新 `version`
- [ ] 更新 CHANGELOG.md 的 `[Unreleased]` 部分

### 发布新版本时

- [ ] 确定版本号（MAJOR/MINOR/PATCH）
- [ ] 更新所有变更文件的 `version` 字段
- [ ] 更新 CHANGELOG.md（移动 Unreleased 内容）
- [ ] 创建 Git commit 和 tag

---

## 附录：版本号快速参考

```
当我...                                 版本号应该...
─────────────────────────────────────────────────────
修复了一个 Bug                          PATCH +1  (1.0.0 → 1.0.1)
添加了新功能（不影响现有功能）            MINOR +1  (1.0.1 → 1.1.0)
修改了现有功能的行为                     MINOR +1  (1.1.0 → 1.2.0)
删除了某个功能                          MAJOR +1  (1.2.0 → 2.0.0)
重构了代码但行为不变                     PATCH +1  (2.0.0 → 2.0.1)
修改了 API/接口（不兼容）                MAJOR +1  (2.0.1 → 3.0.0)
```

---

> ฅ'ω'ฅ **浮浮酱的工程笔记**
>
> 版本管理是专业工程的基础喵～
> 每个文件都要有版本号，每次变更都要记录！
>
> 规范 = 信任 = 质量 (๑•̀ㅂ•́)✧
