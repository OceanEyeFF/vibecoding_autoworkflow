# .nav/ - 兼容导航层

> 本目录提供兼容性的软链接导航，便于 AI 和开发者快速跳转。它属于根目录的兼容导航层，不是主线目录真相。

根层级说明见：

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `AGENTS.md`

## 导航符号说明

| 链接 | 目标 | 用途 |
|------|------|------|
| `@skills` | `product/harness/skills/` | canonical skill 资产 |
| `@docs` | `docs/` | 文档中心 |

## 使用方式

```bash
# 快速进入 docs 模块
cd .nav/@docs

# 快速查看所有 skill
ls .nav/@skills/
```

## 何时使用？

- ✅ 需要快速跳到仍然有效的兼容入口时
- ✅ 需要保留历史路径的过渡说明时
- ❌ 不要在正式文档引用中使用 `.nav/` 路径
- ❌ 不要把 `.nav/` 当成真实目录结构定义

## 当前状态提醒

- `.nav/` 只应服务兼容导航，不应反向决定主线结构
- 当前只保留仍然有效的 `@skills` 与 `@docs`
- 失效的历史软链 `@agents`、`@ideas`、`@planning` 已移除

---

**版本**：v1.1
**创建日期**：2026-03-11
