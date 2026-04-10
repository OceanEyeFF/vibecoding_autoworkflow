# AGENTS.md

> 这是当前仓库的 agent-facing 最小工作规则入口。若与 `docs/knowledge/` 冲突，以知识层文档为准。

## Core

- 本项目是一个 AI coding 的 repo-side contract layer。
- `docs/` 负责 truth boundary，`product/` 负责 canonical skills 与 adapters，`toolchain/` 负责部署、评测与治理脚本。
- `.agents/`、`.claude/`、`.opencode/` 只是 deploy target，不是源码层。
- 如果一个新目录说不清 owner 和层级，不要直接加到根目录。

## Read First

1. `docs/README.md`
2. `docs/knowledge/README.md`
3. `docs/knowledge/foundations/README.md`
4. `docs/knowledge/foundations/root-directory-layering.md`
5. `docs/operations/deploy/review-verify-handbook.md`
6. `toolchain/toolchain-layering.md`
7. `docs/knowledge/task-interface/task-contract.md`
8. `docs/knowledge/memory-side/layer-boundary.md`
9. `docs/knowledge/memory-side/overview.md`
10. `docs/knowledge/memory-side/skill-agent-model.md`

## Route Contract

- `read_next`：
  - `docs/knowledge/memory-side/overview.md`
  - `docs/knowledge/memory-side/skill-agent-model.md`
  - `docs/knowledge/task-interface/task-contract.md`
  - 按任务进入 `product/`、`docs/` 或 `toolchain/` 的局部入口页
  - 需要 Harness Operations prompt entrypoints 或旧路径兼容 shim 时，先进入 `docs/operations/README.md`，再下钻 `docs/operations/prompt-templates/`
- `do_not_read_yet`：
  - `.agents/`
  - `.claude/`
  - `.opencode/`
  - `.autoworkflow/`
  - `.spec-workflow/`
  - `.serena/`
  - `.nav/`
- `stop_reading_when`：
  - 已确认当前任务落在哪一块正式内容区
  - 已拿到当前任务所需的最小模块入口
  - 继续扩读只会重复背景，而不会增加决策价值

## Default Flow

1. `plan`：先固定目标、范围、非目标、验收、风险和验证要求。
2. `implement`：只做当前任务，不顺手扩边界。
3. `verify`：先跑与改动面匹配的检查和测试。
4. `review`：把 diff、计划和验收标准对齐，确认没有遗漏同步项。
5. `writeback`：把已验证事实写回知识层或 operations 层，并清理失效上下文。

## Required Sync

- 根目录分层、一级子目录、hidden/state/mount 层或 `.nav/` 规则变化时，必须同步更新 foundations 文档和对应治理检查。
- `AGENTS.md`、review/verify 流程或退出标准变化时，必须同步更新 `docs/operations/deploy/review-verify-handbook.md`。
- deployment / adapter 行为变化时，必须同步更新相关 operations runbook 和 verify 命令说明。
- 只有已验证结果才可以回写为长期真相；未验证的结论不要写进知识层。

## Root Rules

- `product/` 是业务代码唯一源码根。
- `docs/` 是文档层，内部再分 `knowledge / operations / analysis / ideas / archive`。
- `toolchain/` 只放脚本、评测、测试、打包、部署工具。
- `.autoworkflow/`、`.spec-workflow/` 只属于 repo-local state layer。
- `.serena/` 是 repo-local state/config layer，可保留受控入库的项目级配置与记忆，但不是主线真相层。
- `.nav/` 只是 compatibility navigation layer，不能当真实结构定义。

## Docs Governance Baseline

- `docs/README.md`、`docs/knowledge/README.md` 和 `docs/*/README.md` 只做入口导航，不承载独占规则正文。
- `docs/` 下除 `README.md` 外的正文文档必须有 frontmatter：`title / status / updated / owner / last_verified`。
- `status` 只允许：
  - `docs/knowledge/` 与 `docs/operations/`：`active | draft | superseded`
- 不在 `docs/` 长期使用 `status: suspended`。共享保留内容转 `superseded`，非共享草稿移出 `docs/`。
- 研究结论准入后必须升格到承接层：
  - 稳定规则写 `docs/knowledge/`
  - runbook 写 `docs/operations/`
  - 实现合同落 `product/` 或 `toolchain/`
- 新增或接管文档作用域时，必须同步更新最近入口页并清理旧入口，避免双份主线。

## Review / Verify

- 常规复核入口见 `docs/operations/deploy/review-verify-handbook.md`。
- 修复类任务不得只压住当前症状；必须检查相邻状态、恢复路径和 operator-facing 语义，避免引入新的问题源，并尽量把修复做完整。
- 涉及根目录、路径、分层或治理规则时，优先跑：
  - `python3 toolchain/scripts/test/folder_logic_check.py`
  - `python3 toolchain/scripts/test/path_governance_check.py`
  - `python3 toolchain/scripts/test/governance_semantic_check.py`
- 涉及 closeout 或 gate 变更时，再跑：
  - `python3 toolchain/scripts/test/closeout_acceptance_gate.py --json`
- 涉及 adapter / deploy 变更时，再补对应 `adapter_deploy.py verify`。

## Writeback

- 通用规则和知识正文写到 `docs/knowledge/`。
- repo-local runbook、维护流和复核入口写到 `docs/operations/`。
- template / checklist 只在它们能稳定承接执行时才保留。
- 不要把项目真相写进 `.agents/`、`.claude/`、`.opencode/`、`.nav/`。

## Current Warnings

- `.nav/` 现在只保留 `@docs` 与 `@skills` 两个有效兼容入口。
- `tools/` 只是 compatibility shim，真逻辑仍应落在 `toolchain/scripts/test/`。

## Canonical References

- `docs/README.md`
- `docs/knowledge/README.md`
- `docs/knowledge/foundations/README.md`
- `docs/knowledge/foundations/root-directory-layering.md`
- `docs/knowledge/task-interface/task-contract.md`
- `docs/knowledge/memory-side/layer-boundary.md`
- `docs/knowledge/memory-side/overview.md`
- `docs/knowledge/memory-side/skill-agent-model.md`
