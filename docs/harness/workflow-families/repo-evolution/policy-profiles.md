---
title: "Policy Profiles"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Policy Profiles

> 目的：把 legacy workflow 资产重新降级为 profile / variant，而不是继续拿旧 skill 名称当 ontology。

当前处理原则：

- `execution-contract-template`：`split`
- `harness-contract-shape`：`split`
- `task-planning-contract`：`split`
- `simple-workflow`：legacy profile
- `strict-workflow`：legacy profile
- `task-list-workflow`：workflow/profile 变体
- `review-loop-workflow`：legacy workflow asset
- `repo-governance-evaluation`：治理子能力

这些资产可以继续回收其 prompt、gate、entrypoint 经验，但不再承接 Harness 主线定义。

当前对应的 product source：

- [../../../../product/harness/profiles/simple.profile.md](../../../../product/harness/profiles/simple.profile.md)
- [../../../../product/harness/profiles/strict.profile.md](../../../../product/harness/profiles/strict.profile.md)
- [../../../../product/harness/profiles/task-list.variant.md](../../../../product/harness/profiles/task-list.variant.md)
