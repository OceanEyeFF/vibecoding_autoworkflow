# AGENTS.md

> 这是当前仓库的 agent-facing 最小工作规则入口。若与 `docs/knowledge/` 冲突，以知识层文档为准。

## Project Core

- 本项目是一个 AI coding 的 repo-side contract layer。
- 它的目标不是提供完整执行编排，而是统一 AI 进入仓库时的阅读入口、上下文边界、静态真相层，以及任务结束后的回写与清理。
- 如果你开始把本项目理解成宿主工作流系统、复杂 agent catalog 或 subagents 编排系统，通常已经偏离主线。
- `docs/` 负责路径与 truth boundary，`product/` 负责 canonical skills 与 adapters，`toolchain/` 负责部署、评测与治理脚本，`.agents/` 与 `.claude/` 只是 deploy target。

## First Read

1. `docs/README.md`
2. `docs/knowledge/foundations/root-directory-layering.md`
3. `docs/knowledge/foundations/path-governance-ai-routing.md`
4. `docs/knowledge/foundations/toolchain-layering.md`
5. `docs/knowledge/foundations/partition-model.md`
6. `docs/knowledge/task-interface/task-contract.md`
7. `docs/knowledge/memory-side/layer-boundary.md`
8. `docs/knowledge/memory-side/overview.md`
9. `docs/knowledge/memory-side/skill-agent-model.md`

## Root Rules

- `product/` 是业务代码唯一源码根。
- `docs/` 是文档层，内部再分 `knowledge / operations / analysis / reference / ideas / archive`。
- `toolchain/` 只放脚本、评测、测试、打包、部署工具。
- `.agents/` 和 `.claude/` 只属于 repo-local mount layer，是 deploy target，不是源码层。
- `.autoworkflow/`、`.spec-workflow/` 只属于 repo-local state layer。
- `.serena/` 属于 repo-local state/config layer，可保留受控入库的项目级配置与记忆，但不是主线真相层。
- `.nav/` 只是 compatibility navigation layer，不能当真实结构定义。

## Write Rules

- 通用规则和知识正文写到 `docs/knowledge/`。
- repo-local runbook 写到 `docs/operations/`。
- benchmark 与研究说明写到 `docs/analysis/`。
- 外部参考资料写到 `docs/reference/`。
- 未准入主线的想法写到 `docs/ideas/`，并保持目录与 `status` 一致。
- canonical skill 源码写到 `product/` 下对应 partition 的 `skills/`。
- backend adapter 源码写到 `product/` 下对应 partition 的 `adapters/`。
- 部署、评测、测试、打包脚本写到 `toolchain/`。
- 不要把项目真相写进 `.agents/`、`.claude/`、`.nav/`。

## Rule Of Separation

- 先区分通用合同层和仓库实现层，再写文档或 prompt。
- 通用层优先写“目标仓库”。
- 仓库实现层才允许默认写“本仓库”。
- `.agents/` 与 `.claude/` 只保留部署结果，不手工维护源码。

## Current Warnings

- `.nav/` 现在只保留 `@docs` 与 `@skills` 两个有效兼容入口。
- 如果一个新目录说不清 owner 和层级，不要直接加到根目录。

## Canonical References

- `docs/README.md`
- `docs/knowledge/foundations/partition-model.md`
- `docs/knowledge/foundations/root-directory-layering.md`
- `docs/knowledge/foundations/path-governance-ai-routing.md`
- `docs/knowledge/task-interface/task-contract.md`
- `docs/knowledge/memory-side/layer-boundary.md`
- `docs/knowledge/memory-side/overview.md`
- `docs/knowledge/memory-side/skill-agent-model.md`
