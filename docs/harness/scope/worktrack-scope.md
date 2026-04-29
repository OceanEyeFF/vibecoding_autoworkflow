---
title: "WorktrackScope"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# WorktrackScope

> 目的：固定 `WorktrackScope` 作为 Harness 的快变量控制层。

`WorktrackScope` 负责局部状态转移，关心的是：

- 当前任务目标
- 工作范围与非目标
- 验收条件
- 当前 branch 与 baseline 的差异
- 子任务序列
- 回滚、拆分、恢复路径

它依赖的最小正式对象通常包括：

- `Worktrack Contract`
- `Plan / Task Queue`
- `Gate Evidence`
- `Control State`

`WorktrackScope` 不应吸收 repo 级长期真相；它消费 `RepoScope` 给出的 baseline，并在局部闭环完成后把结果回传给 `RepoScope`。
