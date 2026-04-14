---
title: "Standard Worktrack"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Standard Worktrack

> 目的：固定 repo-evolution family 下的标准 worktrack 闭环。

最小序列：

1. 冻结目标、范围、非目标、验收、风险与验证要求
2. 初始化 `Worktrack Contract` 与 task queue
3. 调度执行并生成变更
4. 收集 evidence，执行 verify
5. 形成 gate verdict
6. fail 时 recover，pass 时 integrate / close
7. 回写 repo 级状态
