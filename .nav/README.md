# .nav/ - AI 快速导航层

> 本目录提供软链接快速导航，便于 AI 和开发者快速遍历文档。

## 导航符号说明

| 链接 | 目标 | 用途 |
|------|------|------|
| `@agents` | `toolchain/agents/aw-kernel/` | Agent 定义文档 |
| `@skills` | `toolchain/skills/aw-kernel/` | Skill 工作流文档 |
| `@docs` | `docs/` | 文档中心（三层架构） |
| `@ideas` | `ideas/` | 研究 Idea 区 |
| `@planning` | `planning/` | 任务管理区 |

## 使用方式

```bash
# 快速进入 agents 目录
cd .nav/@agents

# 快速查看所有 skill
ls .nav/@skills/

# AI 可以通过 .nav/ 快速定位任意模块
```

## 何时使用？

- ✅ 需要快速跨模块导航时
- ✅ AI 需要遍历多个目录时
- ❌ 不要在文档引用中使用 .nav/ 路径（使用真实路径）

## 已归档目录

以下目录已归档到 `archive/`，不再提供导航链接：
- `design/` → `archive/design/`
- `modules/` → `archive/modules-spec/`

---

**版本**：v1.1
**创建日期**：2026-03-11
