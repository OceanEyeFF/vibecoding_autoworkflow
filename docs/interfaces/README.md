# docs/interfaces/ - 接口层文档

> 细颗粒度文档，提供 Agent 和 Skill 的接口参考。

## 何时读我？

- ✅ 需要查阅 Agent/Skill 的具体用法
- ✅ 需要了解工具链的接口定义
- ❌ 不在规划阶段阅读

## 文档导航

本目录为 `toolchain/` 目录提供索引和补充说明。

### Agent 接口

| Agent | 职责 | 入口文档 |
|-------|------|----------|
| ship | 功能开发闭环 | [toolchain/agents/aw-kernel/ship.md](../../toolchain/agents/aw-kernel/ship.md) |
| review | 代码结构分析 | [toolchain/agents/aw-kernel/review.md](../../toolchain/agents/aw-kernel/review.md) |
| logs | 日志分析诊断 | [toolchain/agents/aw-kernel/logs.md](../../toolchain/agents/aw-kernel/logs.md) |
| clean | 代码清理重构 | [toolchain/agents/aw-kernel/clean.md](../../toolchain/agents/aw-kernel/clean.md) |
| clarify | 需求澄清细化 | [toolchain/agents/aw-kernel/clarify.md](../../toolchain/agents/aw-kernel/clarify.md) |
| knowledge-researcher | 技术资料研究 | [toolchain/agents/aw-kernel/knowledge-researcher.md](../../toolchain/agents/aw-kernel/knowledge-researcher.md) |

### Skill 接口

| Skill | 职责 | 入口文档 |
|-------|------|----------|
| autodev | 自动化开发流程 | [toolchain/skills/aw-kernel/autodev/SKILL.md](../../toolchain/skills/aw-kernel/autodev/SKILL.md) |
| autodev-worktree | 并行开发管理 | [toolchain/skills/aw-kernel/autodev-worktree/SKILL.md](../../toolchain/skills/aw-kernel/autodev-worktree/SKILL.md) |

## 与其他层的关系

```
overview/ (概览)
    ↓
modules/ (模块设计)
    ↓
interfaces/ (本目录)
```

---

**版本**：v1.0
**创建日期**：2026-03-11
