---
title: "Recovery Model"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Recovery Model

恢复策略用于 gate fail、scope drift、evidence 缺口或外部噪声后的控制恢复。

典型恢复动作：

- rollback
- retry
- split worktrack
- downgrade / refresh baseline
- pause and escalate

选择恢复动作时，应优先说明：

- 问题属于局部修复还是结构性失败
- 是否仍在同一 `Worktrack Contract` 内
- 是否需要回到 `RepoScope`
