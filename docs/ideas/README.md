---
title: "docs/ideas/ - 想法与研究区"
status: active
updated: 2026-03-17
owner: aw-kernel
last_verified: 2026-03-17
---
# docs/ideas/ - 想法与研究区

> 本目录只存“尚未进入正式计划”的想法、探索和验证。
> 最后更新：2026-03-17

## 目录结构

```text
docs/ideas/
├── README.md
├── active/       # 正在验证中的研究
└── archived/     # 已实现、已放弃或已吸收进计划的想法
```

## 与规划栈的关系

```text
灵感 / 想法 -> docs/ideas/
验证可行 -> docs/planning/WORKBOARD.md
进入当前迭代 -> docs/planning/SPRINT.md
完成落地 -> docs/planning/CHANGELOG.md
```

## 维护规则

1. 还没决定是否投入执行的内容，放这里。
2. 一旦某个 Idea 被正式接受，就把执行状态迁到 `docs/planning/WORKBOARD.md`。
3. 已经被实现或明确放弃的内容，移到 `archived/`。

## 当前说明

- 旧文档里“研究完成的 Idea -> design/ + planning/”的写法已经失效。
- `archive/` 中的设计基线仍可作为背景，但不再决定当前排期。
