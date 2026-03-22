# AGENTS.md

> 这是当前仓库的 agent-facing 最小工作规则入口。若与 `docs/knowledge/` 冲突，以知识层文档为准。

## First Read

1. `docs/README.md`
2. `docs/knowledge/foundations/root-directory-layering.md`
3. `docs/knowledge/foundations/path-governance-ai-routing.md`
4. `docs/knowledge/foundations/toolchain-layering.md`
5. `docs/knowledge/memory-side/layer-boundary.md`
6. `docs/knowledge/memory-side/overview.md`
7. `docs/knowledge/memory-side/skill-agent-model.md`

## Root Rules

- `product/` 是业务代码唯一源码根。
- `docs/` 是文档层，内部再分 `knowledge / operations / analysis / reference / ideas / archive`。
- `toolchain/` 只放脚本、评测、测试、打包、部署工具。
- `.agents/` 和 `.claude/` 只属于 repo-local mount layer，是 deploy target，不是源码层。
- `.autoworkflow/`、`.spec-workflow/`、`.serena/` 只属于 repo-local state layer。
- `.nav/` 只是 compatibility navigation layer，不能当真实结构定义。

## Write Rules

- 通用规则和知识正文写到 `docs/knowledge/`。
- repo-local runbook 写到 `docs/operations/`。
- benchmark 与研究说明写到 `docs/analysis/`。
- 外部参考资料写到 `docs/reference/`。
- 未准入主线的想法写到 `docs/ideas/`，并保持目录与 `status` 一致。
- canonical skill 源码写到 `product/memory-side/skills/`。
- backend adapter 源码写到 `product/memory-side/adapters/`。
- 部署、评测、测试、打包脚本写到 `toolchain/`。
- 不要把项目真相写进 `.agents/`、`.claude/`、`.nav/`。

## Rule Of Separation

- 先区分通用合同层和仓库实现层，再写文档或 prompt。
- 通用层优先写“目标仓库”。
- 仓库实现层才允许默认写“本仓库”。
- `.agents/` 与 `.claude/` 只保留部署结果，不手工维护源码。

## Current Warnings

- `.nav/` 里有历史导航位，部分链接仍是兼容入口。
- 如果一个新目录说不清 owner 和层级，不要直接加到根目录。

## Canonical References

- `docs/README.md`
- `docs/knowledge/foundations/root-directory-layering.md`
- `docs/knowledge/foundations/path-governance-ai-routing.md`
- `docs/knowledge/memory-side/layer-boundary.md`
- `docs/knowledge/memory-side/overview.md`
- `docs/knowledge/memory-side/skill-agent-model.md`
