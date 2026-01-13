# Changelog

All notable changes to AW-Kernel will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- 待发布的新功能

### Changed
- 待发布的变更

### Fixed
- 待发布的修复

---

## [1.1.0] - 2026-01-08

### Added
- **knowledge-researcher**: 新增知识获取与文档整理 Agent
- **VERSIONING.md**: 新增版本管理规范文档
- **CHANGELOG.md**: 新增变更日志文件

### Changed
- **LOGGING.md**: 重构日志系统为 Phase 2 Hooks 方案（零 Token 消耗）
- **所有 Agents**: 移除内嵌日志指令，改用 Hooks 自动记录
- **code-analyzer**: 更新 frontmatter，添加版本信息
- **code-debug-expert**: 更新 frontmatter，添加版本信息
- **code-project-cleaner**: 更新 frontmatter，添加版本信息
- **feature-shipper**: 更新 frontmatter，添加版本信息
- **requirement-refiner**: 更新 frontmatter，添加版本信息
- **system-log-analyzer**: 更新 frontmatter，添加版本信息

### Documentation
- 整理 Claude Code 官方文档知识库（Skills, Hooks, Subagents, MCP 完整指南）

---

## [1.0.0] - 2026-01-06

### Added
- **核心 Agents**（6 个）:
  - `code-analyzer`: 代码结构和架构分析
  - `code-debug-expert`: 调试诊断专家
  - `code-project-cleaner`: 项目清理工具
  - `feature-shipper`: 功能交付执行器
  - `requirement-refiner`: 需求精炼器
  - `system-log-analyzer`: 系统日志分析器

- **Skills**（2 个）:
  - `autodev`: 自动化开发工作流
  - `autodev-worktree`: Git Worktree 并行开发

- **基础设施**:
  - 安装脚本（PowerShell + Bash）
  - 命名空间隔离（`aw-kernel`）
  - CLAUDE.md 项目说明
  - TOOLCHAIN.md 工具链文档
  - STANDARDS.md 失败处理规范

---

## 版本号说明

- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的新功能
- **PATCH**: 向后兼容的 Bug 修复

## 链接

- [版本管理规范](VERSIONING.md)
- [项目路线图](../../../ROADMAP.md)

---

> ฅ'ω'ฅ 浮浮酱会认真记录每一次变更喵～
