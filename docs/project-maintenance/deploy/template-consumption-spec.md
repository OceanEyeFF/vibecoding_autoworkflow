---
title: "Template Consumption Spec"
status: active
updated: 2026-05-06
owner: aw-kernel
last_verified: 2026-05-06
---
# Template Consumption Spec

> 目的：固定 legacy `product/.aw_template/` 的职责边界，避免把它误写成 artifact truth、skill deploy source 或所有模板的长期 owner。

本页属于 [Deploy Runbooks](./README.md)。根目录分层见 [Root Directory Layering](../foundations/root-directory-layering.md)；当前模板入口见 [`product/.aw_template/README.md`](../../../product/.aw_template/README.md)。

## 当前定位

`product/.aw_template/` 是 repo-local execution template layer。它服务 `.aw/` 运行目录的 scaffold 样例，主要用于生成目录结构和少量直接属于 Harness 运行管理面的文档。

它不是：

- canonical artifact truth
- skill deploy source
- payload descriptor source
- backend payload source
- 所有 artifact 模板的长期 owner

## 允许保留的结构位

当前 `.aw_template/` 只按 legacy scaffold 来源理解：

- `control-state.md`
- `goal-charter.md`
- `repo/`
- `worktrack/`
- `template/`

`repo/` 与 `worktrack/` 对应 `.aw/repo/` 和 `.aw/worktrack/` 的运行落位；`template/` 用于不直接进入 `.aw/` 路径但仍需保留的回答流模板。

## 不应长期归属这里的对象

明显由某个 skill 直接生成、维护或消费的模板，不应把 `.aw_template/` 当作长期 owner。例如：

- `contract`
- `plan-task-queue`
- `gate-evidence`
- goal change / goal correction 类回答流

这些对象的 artifact truth 由 `docs/harness/artifact/` 承接；可执行模板应由 owning skill 或 skill assets 承接。当前 `set-harness-goal-skill/assets/` 已承接 `.aw` 初始化资产；不要再把 `.aw_template/` 扩写成新的独立源码根。

## 和 deploy 的关系

`.aw_template/` 与 deploy mapping 的关系只有两条：

- 说明 `.aw_template/` 不参与 skill 部署包分发。
- 说明它是 legacy `.aw/` scaffold 来源，而不是 payload descriptor、backend payload 或 target install 设计。

`aw_scaffold.py` 的当前命令面由 [`toolchain/scripts/deploy/README.md`](../../../toolchain/scripts/deploy/README.md) 承接。本页不承接脚本实现、验证矩阵或 operator 命令样例。

## 停止线

如果需要改变 artifact 结构，先改 `docs/harness/artifact/`；如果需要改变 skill 初始化资产，先改 owning skill；如果需要改变 deploy target install 行为，回到 deploy mapping / entrypoint / provenance 合同页。
