---
title: "根目录索引"
status: active
updated: 2026-03-26
owner: aw-kernel
last_verified: 2026-03-26
---
# 根目录索引

> 用来按任务目标快速定位当前主线入口。项目定位看 [`README.md`](./README.md)，任务分流看本页。

## 先看哪些基础合同

| 目的 | 入口 |
|------|------|
| 建立 docs 模块边界 | [`docs/README.md`](./docs/README.md) |
| 进入知识主线 | [`docs/knowledge/README.md`](./docs/knowledge/README.md) |
| 进入 foundations 主线 | [`docs/knowledge/foundations/README.md`](./docs/knowledge/foundations/README.md) |
| 建立根目录边界 | [`docs/knowledge/foundations/root-directory-layering.md`](./docs/knowledge/foundations/root-directory-layering.md) |
| 建立路径与文档治理边界 | [`AGENTS.md`](./AGENTS.md) |

## 按任务进入

| 任务目标 | 入口 |
|------|------|
| 理解项目是什么、根目录怎么分层 | [`README.md`](./README.md) |
| 看文档真相层与阅读顺序 | [`docs/README.md`](./docs/README.md) |
| 看稳定规则与分层合同 | [`docs/knowledge/README.md`](./docs/knowledge/README.md) |
| 改 `Memory Side` 主线文档 | [`docs/knowledge/memory-side/README.md`](./docs/knowledge/memory-side/README.md) |
| 改 `Task Interface` 主线文档 | [`docs/knowledge/task-interface/README.md`](./docs/knowledge/task-interface/README.md) |
| 改业务源码 | [`product/README.md`](./product/README.md) |
| 改工具脚本、部署或评测 | [`toolchain/README.md`](./toolchain/README.md) |
| 看 repo-local runbook | [`docs/operations/README.md`](./docs/operations/README.md) |
| 运行路径治理检查 | [`docs/operations/path-governance-checks.md`](./docs/operations/path-governance-checks.md) |
| 看 agent-facing 最小规则 | [`AGENTS.md`](./AGENTS.md) |

## 根目录对象怎么理解

- `product/`：业务代码唯一源码根
- `docs/`：文档真相与知识主线
- `toolchain/`：脚本、部署、测试、评测工具
- `.agents/`、`.claude/`、`.opencode/`：repo-local mount / deploy target
- `.autoworkflow/`、`.spec-workflow/`、`.serena/`：repo-local state / config
- `.nav/`：compatibility navigation

## 默认先不要读

- `.agents/`
- `.claude/`
- `.opencode/`
- `.autoworkflow/`
- `.spec-workflow/`
- `.serena/`
- `.nav/`

## 停止继续扩读的条件

- 已确认任务落在 `product/`、`docs/` 或 `toolchain/` 的哪一块正式内容区
- 已定位到最小局部入口
- 继续扩读只会重复背景，而不会增加决策价值
