---
title: "项目协作指南"
status: active
updated: 2026-03-17
owner: aw-kernel
last_verified: 2026-03-17
---
# 项目协作指南

> 本文档定义当前主线的协作规则、文档路由和单一事实源。
> 最后更新：2026-03-17

## 项目定位

AutoWorkflow 是面向“小需求闭环交付”的 aw-kernel 工具链仓库。当前主线不是继续扩写 1 月份的实验性流程文档，而是先把规划、执行、验证、沉淀这四类信息分开维护。

## 当前单一事实源

| 问题 | 当前文档 |
|------|----------|
| 协作规则、读文档顺序 | `docs/overview/guide.md` |
| 战略优先级、退出条件 | `docs/overview/roadmap.md` |
| 所有已准入任务的真实状态 | `docs/planning/WORKBOARD.md` |
| 当前迭代承诺与风险 | `docs/planning/SPRINT.md` |
| 已完成事项与结构调整 | `docs/planning/CHANGELOG.md` |
| 新想法与研究验证 | `docs/ideas/` |
| 背景分析与复盘结论 | `docs/knowledge/analysis/` |

## 何时读什么

### 首次进入仓库

1. 读 `README.md`
2. 读 `docs/overview/guide.md`
3. 按需要读 `docs/overview/roadmap.md` 或 `docs/planning/WORKBOARD.md`

### 需要做规划判断

1. 先读 `docs/overview/roadmap.md`
2. 再读 `docs/planning/WORKBOARD.md`
3. 只有在要排本周承诺时才读 `docs/planning/SPRINT.md`

### 需要执行具体任务

1. 先看 `docs/planning/SPRINT.md` 是否已承诺
2. 再看对应 Agent / Skill 文档
3. 必要时补充读 `docs/knowledge/analysis/`

## 当前不再作为主线 SoT 的内容

- 1 月份生成的 `v0.1` 说明、分阶段实验流程、旧版合并设计文档
- 根目录缺失的 `AUTODEV_*.md` 引用
- 把 `ROADMAP` 当任务流水账、把 `BACKLOG` 当总台账的旧做法

这些内容可以保留在历史位置作为背景，但不能继续代表“当前计划”。

## 协作铁律

1. 新任务先确认是否已经进入 `docs/planning/WORKBOARD.md`，没有准入就不要直接开干。
2. `roadmap` 只讲方向和退出条件，不记任务状态。
3. `WORKBOARD` 才是任务状态真相；`SPRINT` 只是当前切片。
4. 交付完成后必须回写 `CHANGELOG`，否则视为没有真正完成。
5. 无证据不宣称完成，无状态更新不宣称进入下一阶段。

## 文档分层

| 层级 | 目录 | 职责 |
|------|------|------|
| L0 | `README.md` / `INDEX.md` | 项目入口与总导航 |
| L1 | `docs/overview/` | 协作规则与路线图 |
| L2 | `docs/planning/` | 任务状态、迭代承诺、变更记录 |
| L2 | `docs/ideas/` | 尚未准入的想法和研究 |
| L2 | `docs/knowledge/` | 分析沉淀与参考资料 |
| L3 | `toolchain/` | Agent / Skill / Script 源资产 |

## 计划状态机

```text
docs/ideas/ -> docs/planning/WORKBOARD.md -> docs/planning/SPRINT.md -> docs/planning/CHANGELOG.md
            ^                           |
            |                           v
            +-------- blocked / rescope / follow-up -------+
```

状态解释以 `docs/planning/README.md` 为准。

## 冲突处理

1. 如果 `roadmap` 和 `WORKBOARD` 冲突，以 `WORKBOARD` 的状态为准，以 `roadmap` 的优先级为准。
2. 如果 `SPRINT` 承诺了未准入任务，先补 `WORKBOARD` 再继续。
3. 如果历史文档与当前规划冲突，历史文档自动降级为背景资料。

---

**当前主线判断**：先收口计划体系，再推进 P0 工作流控制链。
