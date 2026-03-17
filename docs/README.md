---
title: "docs/ - 文档中心"
status: active
updated: 2026-03-17
owner: aw-kernel
last_verified: 2026-03-17
---
# docs/ - 文档中心

> 本目录是当前项目文档的主容器。
> 最后更新：2026-03-17

## 当前结构

```text
docs/
├── overview/      # 协作规则、路线图
├── planning/      # 任务台账、迭代承诺、变更记录
├── ideas/         # 尚未准入的想法与研究
├── modules/       # 模块设计与中层说明
├── interfaces/    # Agent / Skill 接口入口
├── knowledge/     # 分析沉淀、指南、参考资料
└── archive/       # 历史设计与旧资料
```

## 怎么读

### 先看规则和方向

- `overview/guide.md`
- `overview/roadmap.md`

### 再看状态和计划

- `docs/planning/WORKBOARD.md`
- `docs/planning/SPRINT.md`
- `docs/planning/CHANGELOG.md`

### 需要背景时补充读

- `docs/ideas/`
- `docs/knowledge/`
- `docs/archive/`

## 各目录职责

| 目录 | 职责 | 何时进入 |
|------|------|----------|
| [overview/](overview/) | 当前协作规则和路线图 | 判断主线方向、确认文档路由时 |
| [planning/](planning/) | 已准入任务的真实状态 | 看计划、排迭代、查完成情况时 |
| [ideas/](ideas/) | 尚未进入正式计划的想法 | 记录或筛选新方向时 |
| [modules/](modules/) | 模块级设计说明 | 理解模块边界时 |
| [interfaces/](interfaces/) | 接口与使用入口 | 选择 Agent / Skill 时 |
| [knowledge/](knowledge/) | 分析、指南、参考资料 | 需要背景、复盘、参考时 |
| [archive/](archive/) | 历史资料 | 追溯旧方案、旧设计时 |

## 当前边界

- `docs/` 是文档容器，根目录只保留 `README.md`、`GUIDE.md`、`ROADMAP.md` 作为项目入口或兼容入口。
- `docs/planning/` 和 `docs/ideas/` 已并入 `docs/`，不再视为仓库根层独立文档区。
- `docs/archive/` 只用于追溯，不参与当前主线判断。

## 最小阅读路径

1. 首次进入项目：`overview/guide.md`
2. 看当前方向：`overview/roadmap.md`
3. 看当前状态：`docs/planning/WORKBOARD.md`
4. 看当前迭代：`docs/planning/SPRINT.md`
