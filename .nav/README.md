# .nav/

> 本目录只提供当前有效的快捷导航入口，不承接主线结构定义。

根层级说明见：

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `AGENTS.md`

## 当前入口

| 链接 | 目标 | 用途 |
|------|------|------|
| `@skills` | `product/harness/skills/` | skills 入口 |
| `@docs` | `docs/` | 文档入口 |

## 使用方式

```bash
# 快速进入 docs 模块
cd .nav/@docs

# 快速查看所有 skill
ls .nav/@skills/
```

## 使用边界

- ✅ 需要快速跳到当前正式内容区时
- ❌ 不要在正式文档引用中使用 `.nav/` 路径
- ❌ 不要把 `.nav/` 当成真实目录结构定义

## 当前状态

- `.nav/` 只保留 `@skills` 与 `@docs`
- `.nav/` 只服务快速跳转，不反向定义仓库结构

---

**版本**：v1.1
**创建日期**：2026-03-11
