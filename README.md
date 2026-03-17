---
title: "AutoWorkflow"
status: active
updated: 2026-03-17
owner: aw-kernel
last_verified: 2026-03-17
---
# AutoWorkflow

> aw-kernel 是一套面向小需求闭环交付的 Agent + Skill 工具链。
> 当前主线：先收口规划体系，再推进 P0 工作流控制链。

## 当前入口

- 项目协作规则：`docs/overview/guide.md`
- 项目路线图：`docs/overview/roadmap.md`
- 统一任务台账：`docs/planning/WORKBOARD.md`
- 当前迭代：`docs/planning/SPRINT.md`

## 当前仓库状态

- `6` 个 aw-kernel Agents：`toolchain/agents/aw-kernel/`
- `2` 个核心 Skills：`toolchain/skills/aw-kernel/`
- 当前任务状态集中维护在 `docs/planning/`，不再让 `roadmap` 兼任任务看板

## 目录速览

| 目录 | 职责 |
|------|------|
| `docs/overview/` | 协作规则、路线图 |
| `docs/planning/` | 任务台账、迭代承诺、完成记录 |
| `docs/ideas/` | 想法与研究验证 |
| `docs/knowledge/` | 分析沉淀与参考资料 |
| `docs/archive/` | 历史设计与旧资料 |
| `toolchain/` | Agent / Skill / Script 源资产 |

## 使用建议

1. 首次进入仓库，先读 `docs/overview/guide.md`
2. 需要判断优先级时，读 `docs/overview/roadmap.md`
3. 需要知道当前计划状态时，读 `docs/planning/WORKBOARD.md`
4. 需要执行本轮任务时，再读 `docs/planning/SPRINT.md`

## 说明

- 1 月份的实验性流程文档仍保留在仓库中，但不再代表当前主线。
- 根目录的 `GUIDE.md` 和 `ROADMAP.md` 仅保留为兼容入口，真正内容在 `docs/overview/`。
