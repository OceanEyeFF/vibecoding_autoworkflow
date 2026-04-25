---
title: "Policy Profiles"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Policy Profiles

> 目的：把可复用的 workflow 经验收敛成 profile / variant，而不是直接把它们当 ontology。

当前处理原则：

- workflow/profile 名称只作为 profile 语义来源，不直接作为 repo 当前 skill/source 入口
- 如果后续重新引入 policy profile，应先在 `docs/harness/` 固定 profile 语义，再决定是否需要新的 executable package

这些 profile 经验可以继续回收其 prompt、gate、entrypoint 设计，但不承接 Harness 主线定义。
