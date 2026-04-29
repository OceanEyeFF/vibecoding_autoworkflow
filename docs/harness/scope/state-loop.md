---
title: "Harness 状态闭环"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Harness 状态闭环

> 目的：固定 Harness 在 `RepoScope` 与 `WorktrackScope` 之间的闭环。

一个最小闭环应当是：

1. 在 `RepoScope` 下观测现状并决定下一步
2. 生成 `Worktrack Contract`
3. 初始化 `Worktrack` 与 baseline
4. 调度执行并收集 verify evidence
5. 汇总 gate verdict，失败则进入 recover
6. 通过后发起 `PR -> merge -> cleanup`
7. 回到 `RepoScope`，刷新 `Repo Snapshot / Status`

失败信号：

- 只做到 “PR 已发出” 就结束
- 没有把 closeout 结果回写到 repo 级状态
- `RepoScope` 与 `WorktrackScope` 被混成同一份状态文档
