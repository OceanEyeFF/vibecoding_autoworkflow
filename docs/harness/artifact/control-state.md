---
title: "Harness Control State"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Harness Control State

保存控制面当前处于哪个模式，而不是保存业务真相。

最少应包含：

- 当前控制级别
- 当前活跃 worktrack
- 当前 baseline branch
- 当前需要执行的下一动作
- 关联正式文档路径

它不应替代 `Repo Snapshot / Status` 或 `Worktrack Contract`。
