---
title: "Repo Analysis"
status: active
updated: 2026-04-26
owner: aw-kernel
last_verified: 2026-04-26
---
# Repo Analysis

`Repo Analysis` 是 `RepoScope` 的决策支撑 artifact，用来把仓库事实压缩成可复核的优先级判断。

它回答：

- 当前仓库事实是什么
- 哪些只是推断或未知项
- 当前主要矛盾是什么
- 当前最高优先级是什么
- 这个判断应投影到哪条合法 Harness 路由
- 哪些结论可以写回长期 truth layer，哪些只能保留为 research evidence

它不回答：

- 新目标是什么
- 某个 worktrack 的任务队列是什么
- 某个实现切片应该怎么编码
- 未验证研究结论应不应该直接进入长期文档

## Position

`Repo Analysis` 位于 `Repo Goal / Charter` 与 `Repo Snapshot / Status` 下游。

- `Goal / Charter` 定义长期参考信号和 Engineering Node Map
- `Snapshot / Status` 定义当前 repo 慢变量状态
- `Repo Analysis` 基于两者做阶段性矛盾分析和优先级判断
- `repo-whats-next-skill` 可以消费它，但不能把它当成目标真相的替代品

## Required Inputs

一份合格的 `Repo Analysis` 至少引用：

- `Repo Goal / Charter`
- `Repo Snapshot / Status`
- `Harness Control State`
- 本轮必要的入口文档或模块证据
- 如果刚关闭 worktrack 影响判断，则引用对应 contract / plan / evidence 的最小边界摘要

禁止把 deploy target、本地挂载结果或未验证报告当作唯一事实来源。

## Required Fields

`Repo Analysis` 至少包含以下 Control Signal 字段：

- `analysis_status`
- `baseline_branch`
- `baseline_ref`
- `facts`
- `inferences`
- `unknowns`
- `current_main_contradiction`
- `main_aspect`
- `current_highest_priority`
- `long_term_highest_priority`
- `do_not_do_now`
- `recommended_repo_action`
- `recommended_next_route`
- `suggested_node_type`
- `continuation_ready`
- `continuation_blockers`
- `writeback_eligibility`

Supporting Detail 可以包含完整分析、证据引用、任务建议和复盘机制，但下一步路由所需字段必须出现在 Control Signal 层。

## Analysis Rules

- 事实、推断、未知项必须分开写。
- 当前主要矛盾只能有一个。
- 当前最高优先级只能有一个。
- 如果证据不足以选择主要矛盾，`continuation_ready` 必须为 false，并列出最小缺失信息。
- 不要把 task list 当成 repo 分析；任务列表只能作为分析结论的下游投影。
- 不要把分析报告写成新的 Goal Charter；目标变更只能走 `repo-change-goal-skill`。

## Lifecycle

1. `RepoScope.Observe` 读取当前 Goal、Snapshot 和 Control State。
2. `RepoScope.Decide` 在需要优先级重构时生成或消费 `Repo Analysis`。
3. `Repo Analysis` 输出一个建议 repo action 和路由投影。
4. 如果路由进入 `WorktrackScope.Init`，worktrack contract 只能引用分析结论，不能把分析全文复制成任务队列。
5. Worktrack closeout 后，`RepoScope.Refresh` 根据验证事实更新 snapshot；未经验证的分析判断不进入长期 truth。

## Writeback Policy

可以写回长期 truth layer 的内容：

- 已被后续 worktrack 验证的 repo 状态变化
- 被 gate 接受的 artifact / workflow / skill contract 规则
- 已经同步到对应 docs/product/toolchain 承接位的执行约定

不能直接写回长期 truth layer 的内容：

- 未验证市场判断
- 未验证外部用户需求
- 只来自一次分析报告的战略推断
- 与 Goal Charter 冲突但没有走目标变更控制的结论

## Consumer Contract

`repo-whats-next-skill` 可以使用最新 `Repo Analysis` 作为判定输入，前提是：

- 分析引用的 baseline 仍匹配当前 repo snapshot 或明确标注过期
- Control Signal 字段完整
- 没有把目标变更、实现任务或 worktrack 队列混入分析 artifact

如果没有新鲜 `Repo Analysis`，`repo-whats-next-skill` 仍必须能直接基于 Goal、Snapshot 和 Control State 完成一轮限定范围判定。
