---
title: Harness Runtime Protocol Chapter Plan
status: active
updated: 2026-05-14
owner: aw-kernel
last_verified: 2026-05-14
---

# Harness Runtime Protocol Chapter Plan

本文固定 [Harness运行协议.md](./Harness运行协议.md) 的拆章计划。迁移完成前，`Harness运行协议.md` 仍是 runtime protocol 的当前入口和权威正文；本文只规定拆分边界、迁移顺序和不应放入 foundations 的内容。

## Target Shape

拆分后的 runtime protocol 应保持小章聚焦，每章只承接运行协议本身，不重复 doctrine、artifact fields、catalog inventory、workflow family policy 或 executable skill source。

| 目标章节 | 承接内容 | 留在当前协议中的摘要 |
| --- | --- | --- |
| `runtime-control-loop.md` | 控制链、Scope 状态、合法算子、连续推进与 stop condition | 最小闭环、Scope/Function/Artifact 关系和当前入口链接 |
| `runtime-dispatch-contract.md` | Dispatch / Implement 边界、载体选择、dispatch packet、fallback 语义 | Dispatch 的控制面职责和执行载体入口链接 |
| `runtime-evidence-gate-recovery.md` | Verify / Judge 分离、Gate verdict、Recover route、handback 与交接锁 | Evidence/Gate/Recover 的最小判断标准 |
| `runtime-closeout-refresh.md` | closeout、repo refresh、milestone progress 写回、pipeline advancement | PR 不是终点，closeout 后必须回到 RepoScope |
| `runtime-state-hydration.md` | `.aw/control-state.md` 恢复、policy hydration、authority 与 autonomy ledger | runtime state 不替代 docs/product/toolchain truth layer |

## Migration Order

1. 先提取 `runtime-dispatch-contract.md`，因为 Dispatch / Implement 边界直接影响 skill 分派与 current-carrier fallback。
2. 再提取 `runtime-evidence-gate-recovery.md`，保持 Verify、Judge、Recover 和 handback 语义在同一组判断规则内。
3. 再提取 `runtime-control-loop.md`，将 Scope 状态、合法算子与连续推进语义整理成主循环章节。
4. 再提取 `runtime-closeout-refresh.md`，隔离 closeout、repo refresh 与 milestone pipeline 的推进语义。
5. 最后提取 `runtime-state-hydration.md`，只在 control-state artifact 字段稳定后同步 runtime hydration 规则。

每次迁移必须同时更新 [README.md](./README.md) 和 [Harness运行协议.md](./Harness运行协议.md) 的入口链接，并确认原章节没有留下互相冲突的重复正文。

## What Remains In Harness运行协议.md

迁移期间，`Harness运行协议.md` 保留：

- runtime protocol 的总定义和阅读入口
- 当前有效的完整协议正文，直到对应小章被验证接管
- 到 doctrine、artifact contracts、catalog inventory、workflow policy、design analysis 和 executable skill surfaces 的 owner links
- 对已拆小章的短摘要和权威链接

迁移完成后，`Harness运行协议.md` 应降为 runtime protocol index，只保留入口、章节摘要、全局不变量和 owner boundary。

## Outside Runtime Protocol Chapters

下列内容不进入拆分后的 runtime protocol 小章；它们仍由各自 owner 承接：

| 内容类型 | Owner |
| --- | --- |
| Doctrine / why Harness exists | [Harness指导思想.md](./Harness指导思想.md) |
| Formal object fields and schemas | [../artifact/README.md](../artifact/README.md) |
| Skill inventory, Scope/Function mapping and executable source links | [../catalog/README.md](../catalog/README.md) |
| Reusable workflow family policy and route patterns | [../workflow-families/README.md](../workflow-families/README.md) |
| Unpromoted design analysis or migration comparison | [../design/](../design/) |
| Canonical executable skill source | [../../../product/harness/skills/README.md](../../../product/harness/skills/README.md) |
| Project maintenance governance and review/verify rules | [../../project-maintenance/governance/review-verify-handbook.md](../../project-maintenance/governance/review-verify-handbook.md) |

## Acceptance For Future Splits

A future physical split is acceptable only when:

- `Harness指导思想.md` remains doctrine-only.
- `Harness运行协议.md` still gives a clear runtime entry and does not become a second artifact catalog.
- Each new runtime chapter has frontmatter and one clear owner boundary.
- Links from foundations navigation make doctrine, runtime protocol, artifact contracts, catalog inventory, workflow policy, design analysis and executable skill surfaces distinguishable.
- No migrated chapter changes artifact field semantics without updating the corresponding artifact contract.
