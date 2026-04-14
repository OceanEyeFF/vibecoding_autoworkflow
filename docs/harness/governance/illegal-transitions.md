---
title: "非法状态转移"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# 非法状态转移

Harness 不应允许下列转移：

- `RepoScope.observing -> WorktrackScope.executing`
- `WorktrackScope.executing -> integrating`，但未经过 verify / judge
- `WorktrackScope.judging -> closed`，但未经过 merge 或显式 abort
- `blocked -> integrating`，但没有补证或补权

出现非法转移时，Harness 应停止推进并报告状态机违例，而不是“尽量继续”。
