---
title: "文档索引"
status: active
updated: 2026-03-17
owner: aw-kernel
last_verified: 2026-03-17
---
# 文档索引

> 用来快速定位当前主线文档，不再承担“解释所有历史背景”的职责。

## 最先读什么

| 目的 | 文档 |
|------|------|
| 了解协作规则 | `docs/overview/guide.md` |
| 了解优先级与阶段目标 | `docs/overview/roadmap.md` |
| 看真实任务状态 | `docs/planning/WORKBOARD.md` |
| 看当前迭代承诺 | `docs/planning/SPRINT.md` |
| 看已完成事项 | `docs/planning/CHANGELOG.md` |

## 目录结构

```text
.
├── README.md
├── GUIDE.md                  # 兼容入口，指向 docs/overview/guide.md
├── ROADMAP.md                # 兼容入口，指向 docs/overview/roadmap.md
├── docs/
│   ├── overview/
│   ├── planning/
│   ├── ideas/
│   ├── modules/
│   ├── interfaces/
│   ├── knowledge/
│   └── archive/
└── toolchain/
```

## 当前文档边界

- `docs/overview/`：规则和方向
- `docs/planning/`：状态和承诺
- `docs/ideas/`：尚未准入的想法
- `docs/archive/`：历史资料，不参与当前主线判断

## 不要再这样用

- 不要把 `roadmap` 当任务流水账
- 不要把 `BACKLOG.md` 当总台账
- 不要用 1 月份的实验文档替代当前规划入口
