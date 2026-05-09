---
title: "Template Consumption Spec"
status: active
updated: 2026-05-08
owner: aw-kernel
last_verified: 2026-05-08
---
# Template Consumption Spec

> 目的：明确 legacy `product/.aw_template/` 的职责边界，避免误作 artifact truth、skill deploy source 或所有模板的长期 owner。

本页属于 [Deploy Runbooks](./README.md)。根目录分层见 [Root Directory Layering](../foundations/root-directory-layering.md)；当前模板入口见 [`product/.aw_template/README.md`](../../../product/.aw_template/README.md)。

## 当前定位

`product/.aw_template/` 是 repo-local execution template layer，为 `.aw/` 提供 scaffold 样例，不是 artifact truth、skill deploy source 或 backend payload source。

## 允许保留的结构位

仅保留 `control-state.md`、`goal-charter.md`、`repo/`、`worktrack/`、`template/`。`repo/` 与 `worktrack/` 对应 `.aw/repo/` 与 `.aw/worktrack/` 落位；`template/` 用于不直接进入 `.aw/` 的回答流模板。

## 不应长期归属这里的对象

`contract`、`plan-task-queue`、`gate-evidence`、goal change/correction 类回答流不应长期归属 `.aw_template/`。其 artifact truth 由 `docs/harness/artifact/` 定义；可执行模板应由 owning skill 或 `set-harness-goal-skill/assets/` 承担。

## 和 deploy 的关系

`.aw_template/` 不参与 skill 部署包分发，是 legacy `.aw/` scaffold 来源而非 payload descriptor、backend payload 或 target install 设计。`aw_scaffold.py` 已随 P0-067 Python cleanup 移除，不再作为 scaffold 工具。

## 停止线

需改变 artifact 结构时先改 `docs/harness/artifact/`；需改变 skill 初始化资产时先改 owning skill；需改变 deploy target install 行为时回 deploy mapping/entrypoint/provenance 合同页。
