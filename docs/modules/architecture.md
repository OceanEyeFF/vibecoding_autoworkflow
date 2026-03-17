---
title: "modules/ - 概念模块总览"
status: active
updated: 2026-03-17
owner: aw-kernel
last_verified: 2026-03-17
---
# modules/ - 概念模块总览

> 本文件描述当前主线里的四个概念模块，用来统一规划语言。
> 它定义的是能力域，不代表这些目录已经在仓库中拆分落地。

## 当前说明

- `gate / workflow / verification / knowledge` 是概念模块，不是现有文件夹结构。
- 当前任务状态和排期以 `docs/planning/` 为准。
- 当前实现入口以 `toolchain/` 为准。

## 四个概念模块

### gate

**职责**：任务入口筛选、阶段放行控制

| 组件 | 说明 | 关联路线图 |
|------|------|------------|
| Intake Gate (G0) | 入口规模评估，判定任务是否进入默认流程 | P0-1 |
| Spec Gate (G1) | 需求契约放行 | P0-3 |
| Evidence Gate (G3) | 证据验证放行 | P0-4 |
| Delivery Gate (G4) | 交付完整性检查 | P0-6 |

### workflow

**职责**：任务编排、阶段流转、回路控制

| 组件 | 说明 | 关联路线图 |
|------|------|------------|
| Level 0 Loop | 最多 3 次修复回路 | P0-5 |
| Goal Tracker | 目标列表持续更新 | P0-7 |
| 2-3-1 Orchestration | 需求-实现-交付编排 | 规划约束 |

### verification

**职责**：证据收集、合规检查、诚实度保障

| 组件 | 说明 | 关联路线图 |
|------|------|------------|
| Evidence Collector | 最小证据集收集 | P0-4 |
| Compliance Checker | 约束符合度对照 | P0-4 |
| Honesty Guard | 无证据不宣称通过 | P0-4 |

### knowledge

**职责**：知识沉淀、检索增强、长期记忆

| 组件 | 说明 | 关联路线图 |
|------|------|------------|
| Knowledge Gate | 提交前知识更新门禁 | P0-8 |
| Doc Indexer | 文档元数据标准化 | P2-3 |
| Search Prep | 本地检索前置准备 | P2-4 |

## 关系图

```text
docs/overview/roadmap.md
        ↓
docs/modules/architecture.md
        ↓
docs/planning/WORKBOARD.md
        ↓
toolchain/
```

## 未来拆分规则

如果后续要把概念模块拆成独立目录，每个模块至少应包含：

```markdown
# [模块名] - 模块概述

## 职责边界
## 核心组件
## 交互接口
## 当前状态
## 关联任务
```

## 与其他目录的关系

| 目录 | 角色 |
|------|------|
| `docs/overview/` | 定义规则和方向 |
| `docs/planning/` | 维护当前要做什么 |
| `docs/modules/` | 定义概念模块和能力域 |
| `toolchain/` | 实际实现入口 |

**设计 → 规划 → 实现**：`docs/modules/` 定义能力域，`docs/planning/` 决定当前做什么，`toolchain/` 负责真正落地。
