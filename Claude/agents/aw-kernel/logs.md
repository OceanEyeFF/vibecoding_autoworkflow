---
name: logs
version: 1.0.0
created: 2026-01-16
updated: 2026-01-16
description: >
  路由入口（别名）：用于日志/系统输出诊断，实际规范见 system-log-analyzer.md。
model: sonnet
tools: Read, Grep, Glob, Bash, TodoWrite
---

## 📖 使用指南
- **何时读**: 需要解析日志、错误堆栈或系统输出以定位根因时
- **何时不读**: 仅做代码审查、需求澄清或功能实现时
- **阅读时长**: 1-2 分钟
- **文档级别**: L1 (选读)

## 正文说明
本文件为路由入口（别名），实际执行规范请阅读：
- `Claude/agents/aw-kernel/system-log-analyzer.md`
