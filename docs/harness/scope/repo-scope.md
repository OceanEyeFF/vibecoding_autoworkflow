---
title: "RepoScope"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# RepoScope

> 目的：固定 `RepoScope` 作为 Harness 的慢变量控制层。

`RepoScope` 负责长期基线——repo goal、架构与模块地图、主分支现状、活跃分支及用途、治理状况、系统不变量、已知风险——其核心职责不是推进单个任务，而是判断是否需要新建/恢复/刷新 worktrack、当前 baseline 是否仍可信、以及目标是否需要进入 change control。
