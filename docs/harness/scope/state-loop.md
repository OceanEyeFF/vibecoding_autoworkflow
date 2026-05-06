---
title: "Harness 状态闭环"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Harness 状态闭环

> 目的：固定 Harness 在 `RepoScope` 与 `WorktrackScope` 之间的闭环。

最小闭环：RepoScope 下观测并决定 -> 生成 Worktrack Contract -> 初始化 Worktrack 与 baseline -> 调度执行并收集 verify evidence -> gate verdict（失败则 recover）-> PR/merge/cleanup -> 回到 RepoScope 刷新 Repo Snapshot/Status。失败信号：只做到”PR 已发出”就结束、closeout 结果未回写 repo 级状态、RepoScope 与 WorktrackScope 被混成同一份状态文档。
