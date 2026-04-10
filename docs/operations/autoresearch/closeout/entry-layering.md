---
title: "Autoresearch closeout 入口层级规则"
status: superseded
updated: 2026-04-11
owner: aw-kernel
last_verified: 2026-04-11
---

# Autoresearch closeout 入口层级规则

> 非默认入口。本文只保留 closeout 入口层级规则的 lineage / audit 记录；只有在复核已完成 closeout 的入口退场语义时才进入。日常入口先回到 [README.md](../README.md) 中的 `autoresearch-minimal-loop / research-cli-help / tmp-exrepo-maintenance`。

> 目的：冻结当前 `autoresearch` closeout 在 `docs/analysis/` 的入口层级，明确什么文件可以承担目录页型入口，什么文件只能作为叶子页正文，以及历史 planning 如何退回 lineage 地位。

## 一、适用范围

本文只治理已经收起的 closeout surface：

- `docs/analysis/README.md`
- 当前 closeout 正文：
  - `autoresearch-closeout-governance-goals.md`
  - `autoresearch-closeout-governance-task-list.md`
- 当前仍保留的历史 planning 文档

本文不负责：

- 选择最终唯一 closeout 入口长什么样
- 下一阶段 implementation planning
- 把 `analysis/` 升格成 repo 主线真相层

## 二、术语

- `目录页型入口`：只负责说明本层语义、当前状态和分流路径，本身不承载大段执行细节。只有这类文件可以承担默认入口。
- `叶子页正文`：承接具体目标、任务、复盘、gate 结果或某一版规划细节。它可以被目录页链接，但不能和目录页竞争同层默认入口地位。
- `历史 planning 叶子页`：`status: superseded` 的旧任务规划或阶段规划，只保留 lineage，不再承担当前执行入口。

## 三、默认层级规则

按下面规则判断：

1. 如果一个文件主要职责是“告诉读者先看哪里、再看哪里”，它才有资格做 `目录页型入口`。
2. 如果一个文件主要职责是“展开目标、任务、证据或细节正文”，它默认是 `叶子页正文`，即使内容仍然有效。
3. `叶子页正文` 可以在页首声明自己的定位和最近承接位，但不能自称“当前默认入口”。
4. `status: superseded` 的 planning 文档一律按 `历史 planning 叶子页` 处理；它们可以解释 lineage，但不能再并列承担当前入口。
5. 如果无法证明某页应当承担目录页职责，默认把它降为 `叶子页正文`，并回到现有目录页补分流。

## 四、当前 closeout 映射

当前仓库内，closeout surface 现在按下面映射执行：

- `docs/analysis/README.md`：
  - 当前 `analysis/` 层的唯一目录页型入口。
  - closeout 相关内容只保留在单独的 lineage / audit 分流块里，不再占用“当前执行规划”。
- `autoresearch-closeout-governance-goals.md`：
  - 已完成 closeout 的目标正文叶子页。
  - 应使用 `status: superseded`，只保留 lineage / audit 价值。
- `autoresearch-closeout-governance-task-list.md`：
  - 一次已收起的“收口后中期治理”任务设想。
  - 应使用 `status: superseded`，只保留 lineage / audit 价值。
- 历史 planning 文档：
  - 一律保留为 lineage 叶子页。
  - 只说明“它曾经是什么”和“现在应该去哪里”，不再承担当前入口分流。

## 五、历史 planning 的最小去入口要求

每一份历史 planning 文档至少要满足下面三条：

1. frontmatter 使用 `status: superseded`。
2. 页首明确写出：
   - 本文只保留 lineage
   - 本文不是当前默认入口
   - 当前应先回到哪个目录页，再进入哪份 active 文档
3. 如果页首仍需要提到“当前优先以什么为准”，目标必须是仍 active 的目录页或正文，不能再把另一份 superseded planning 当成前跳入口。

## 六、fail-closed 处理

遇到下面情况，默认按“不是入口页”处理：

- 一个正文页想同时承担总结、分流和执行细节。
- 两份同层正文页都声称自己是当前入口。
- 历史 planning 页仍把另一份历史 planning 当成当前优先入口。

最小处理方式：

1. 先把有争议的页面降回叶子页。
2. 再回到现有目录页补说明和链接。
3. 如果仍需要唯一 closeout 入口，再交给 `G-205` 收口，而不是让正文页继续并列抢入口。

## 七、与后续任务的关系

- `G-201` 到此冻结的是“谁能当入口、谁只能当叶子页”。
- `G-205` 的结果已经收束到 `docs/analysis/README.md` 的分流结构中。
- 现在不允许把 goals、task list 或历史 planning 重新提升为并列默认入口。
