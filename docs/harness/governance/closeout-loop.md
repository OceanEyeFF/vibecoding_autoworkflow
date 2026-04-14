---
title: "Closeout Loop"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Closeout Loop

Harness 的 closeout 不止是 “任务完成”，而是：

1. gate verdict 明确
2. PR / merge / cleanup 完成
3. 残余风险与 override 被记录
4. `Repo Snapshot / Status` 被刷新
5. 控制权回到 `RepoScope`

如果只做到局部 merge，而没有把 repo 级观测面更新回来，闭环仍未完成。
