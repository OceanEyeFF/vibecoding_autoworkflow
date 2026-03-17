---
title: "docs/planning/ - 计划与状态管理区"
status: active
updated: 2026-03-17
owner: aw-kernel
last_verified: 2026-03-17
---
# docs/planning/ - 计划与状态管理区

> 本目录只负责一件事：把“已准入的工作”维护成单一真相。
> 最后更新：2026-03-17

## 当前架构

```text
docs/planning/
├── README.md        # 本文件：规划栈说明与状态机
├── WORKBOARD.md     # 单一任务台账（当前真相）
├── SPRINT.md        # 当前迭代切片
├── CHANGELOG.md     # 已完成变更记录
└── BACKLOG.md       # 兼容跳转页（已废弃）
```

## 各文档职责

| 文档 | 角色 | 何时更新 |
|------|------|----------|
| `WORKBOARD.md` | 所有已准入任务的真实状态 | 任务状态变化时立即更新 |
| `SPRINT.md` | 当前迭代承诺、风险、下一步 | 迭代开始、范围变更、迭代结束 |
| `CHANGELOG.md` | 实际完成的文档/结构/流程变化 | 每次完成后更新 |
| `BACKLOG.md` | 提示迁移到 `WORKBOARD.md` | 只在迁移期保留 |

## 为什么不再单独维护 Backlog

旧结构里 `BACKLOG` 同时承担“总台账”和“未排期池”两种职责，结果会和 `SPRINT` 发生状态冲突。现在改成：

- 尚未准入的想法：放在 `docs/ideas/`
- 已准入但未开工的任务：放在 `WORKBOARD.md`，状态为 `ready` 或 `queued`
- 当前承诺的任务：放在 `SPRINT.md`

这样每个文档只维护一种视角。

## 状态定义

| 状态 | 含义 |
|------|------|
| `queued` | 已被接受，但前置条件还没满足 |
| `ready` | 已定义清楚，可以进入后续迭代 |
| `active` | 当前正在执行 |
| `blocked` | 因外部条件或决策缺失暂停 |
| `done` | 已完成且已写入 `CHANGELOG.md` |
| `archived` | 历史遗留，仅为追溯保留 |

## 生命周期

```text
docs/ideas/ -> WORKBOARD(queued/ready) -> SPRINT(active) -> CHANGELOG(done)
                          ^                 |
                          |                 v
                          +---- blocked / rescope ----+
```

## 维护规则

1. 新任务先进入 `docs/ideas/` 或直接登记到 `WORKBOARD.md`，禁止直接写进 `SPRINT.md`。
2. `SPRINT.md` 里的每一项都必须能在 `WORKBOARD.md` 找到对应 ID。
3. 一项工作只有在 `CHANGELOG.md` 留痕后，才能把 `WORKBOARD` 状态改为 `done`。
4. `docs/overview/roadmap.md` 只提供优先级，不承担状态维护。

## 当前迁移说明

2026-03-17 起，`WORKBOARD.md` 正式替代旧 `BACKLOG.md` 作为主台账。历史文件 `BACKLOG.md` 保留为兼容入口，避免旧链接直接失效。
