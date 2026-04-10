---
title: "Autoresearch 收口边界与例外决策规则"
status: superseded
updated: 2026-04-11
owner: aw-kernel
last_verified: 2026-04-11
---

# Autoresearch 收口边界与例外决策规则

> 非默认入口。本文只保留已完成 closeout 的边界与例外判定记录；只有在复核 closeout lineage / audit 或 retained evidence 时才进入。日常入口先回到 [README.md](../README.md) 中的 `autoresearch-minimal-loop / research-cli-help / tmp-exrepo-maintenance`。

> 目的：把当前 `autoresearch` 收口治理期的允许项、禁止项、默认判定、最小 authority 和例外处理口径冻结成同一份 repo-local 规则，避免再把同一问题拆成单独的 `authority matrix` 或 `waiver` 任务。

## 一、适用范围

本文只治理当前这轮 `autoresearch` closeout：

- 收口边界是否还清楚
- 当前入口和 lineage 是否还清楚
- artifact 的留删规则、实清理、保留登记和 acceptance gate 应该如何推进

本文不负责：

- 下一阶段 implementation 规划
- `feedback`、`mutation`、prompt、runtime 等开发面重构
- 把运行时状态、deploy target 或 `analysis/` 研究页提升成新的长期真相层

## 二、三种判定结果

任何变更请求只允许落到下面三类结果之一：

- `允许`：当前执行者可直接推进，不需要额外特批。
- `不允许`：不属于本轮 closeout，或会直接破坏当前分层、真相边界或证据链。
- `需要显式特批`：只有在最小 authority 明确书面批准后才可执行；没有批准时默认不做。

## 三、默认判定规则

按下面顺序判断：

1. 如果请求只服务当前 closeout 的边界、入口、留删、记录或 gate，而且不改变实现语义、authority 来源或真相层级，判定为 `允许`。
2. 如果请求会把工作重新带回下一阶段开发、运行时重构、评测扩张或目录结构漂移，判定为 `不允许`。
3. 如果请求本身仍属于 closeout，但带有不可逆处置、跨层改动、降标准验收或 authority 不明确，判定为 `需要显式特批`。
4. 如果无法在现有文档中证明它属于 `允许`，默认按 `需要显式特批` 处理，而不是按沉默同意放行。

## 四、允许项

下面这些动作默认 `允许`：

- 为当前 closeout 补规则正文、入口回链、frontmatter、状态字段和最小说明。
- 把已接受的 closeout 结论承接到正确层级：
  - 稳定规则进 `docs/knowledge/`
  - repo-local 执行规则、runbook、gate、记录模板进 `docs/operations/`
- 收敛当前 closeout 的目录页入口、历史 planning 的 lineage 提示和非默认入口说明。
- 编写或更新当前 closeout 所需的 retention runbook、retained index、acceptance gate 文档与最小辅助脚本，只要这些改动不改变 `autoresearch` 运行时语义。
- 做只读核对和无损验证，例如检查 deploy sync、runtime 残留、链接可达性、frontmatter 完整性。
- 记录“哪些对象还未有明文留删规则”，并把实际处置延后到对应规则完成之后。

## 五、禁止项

下面这些动作默认 `不允许`：

- 新开下一阶段 implementation task plan、roadmap、重构计划或开发优先级排序。
- 借 closeout 名义修改 `autoresearch` 的 runtime、round、decision、mutation、feedback、prompt 或 eval 语义。
- 把 `.autoworkflow/`、`.agents/`、`.claude/`、`.opencode/` 或 `docs/analysis/` 研究页当成新的主线真相层。
- 仅为了让 gate 看起来通过而改运行时状态、验收证据、归档结果或历史记录。
- 在根目录新增说不清 owner 和层级的目录，或把 repo-local 维护规则写回错误层级。
- 为“看起来完整”额外扩出已经被本轮任务清单删除的治理制度，例如容量预算制度、独立命名制度、下一阶段 canary 体系。

## 六、需要显式特批的情形

下面这些动作默认 `需要显式特批`：

- 任何不可逆或难恢复的处置：
  - `delete`
  - `archive`
  - `superseded`
  - `retain`
  - 其他会改变历史可见性或默认入口地位的动作
- 目录级留删规则尚未落盘前，对 `.autoworkflow/`、`acceptance-worktrees/` 或 retained artifact 做真实处置。
- 修改 closeout acceptance gate 的通过门槛、跳过失败检查，或用替代证据覆盖原定检查链。
- 当前规则没有明说允许，但请求方声称“这次是特殊情况”的边界穿越动作。
- 任何会同时触碰 closeout 和下一阶段开发面的混合请求，即使其中一部分看起来与收口有关。

## 七、最小 authority 口径

当前最小 authority 只保留下面三条：

- `允许` 项由当前任务执行者直接处理，但仍必须遵守现有文档分层和最近入口回链规则。
- `需要显式特批` 项只能由当前收口治理 owner 明确拍板；当前文档 owner 为 `aw-kernel`，因此最小 authority 以该 owner 的书面批准为准。
- AI、脚本或执行者不能自行宣称“已经默认获批”；没有可追溯书面记录时，一律视为未获批。

可接受的 authority 记录必须满足两点：

- 能在仓库内或与仓库绑定的执行上下文中被复核。
- 能明确指出批准对象、动作范围和是否仅对本次例外有效。

最小可接受载体包括：

- 当前任务说明
- `Task Contract`
- 评审评论或 PR 说明
- 直接写入承接文档的明确决策记录

## 八、例外处理口径

任何例外申请至少要写清下面五件事：

1. 具体要动什么对象。
2. 为什么现有 `允许` 项无法覆盖。
3. 为什么不做这次例外会阻塞当前 closeout。
4. 这次动作是否可恢复，以及恢复路径是什么。
5. 例外结束后要回写到哪一份正式文档或记录。

例外批准后还必须满足：

- 只按批准范围执行，不自动外溢到相邻对象。
- 不把一次性例外自动升级成长期规则。
- 如果同类例外重复出现，下一步应回到主规则文档补规则，而不是继续靠特批运行。

## 九、快速判定表

| 变更请求 | 判定 | 说明 |
| --- | --- | --- |
| 为 closeout 补规则文档、README 回链、状态字段、lineage 说明 | `允许` | 这是当前 closeout 的直接工作面 |
| 为 `G-101/G-105/G-201/G-205/G-301/G-401` 编写 repo-local runbook、记录页或 gate 说明 | `允许` | 只要不改 runtime 语义 |
| 执行只读检查、验证 deploy sync、核对 retained run 状态 | `允许` | 属于无损验证 |
| 在尚无目录级留删规则时直接删 run、归档目录或降级入口 | `需要显式特批` | 真实处置先 fail closed |
| 调低 acceptance gate、跳过失败检查或改证据来“过关” | `需要显式特批` | 属于降标准动作 |
| 声称“顺手”补下一阶段实现规划或代码重构 | `不允许` | 已越出 closeout 边界 |
| 修改 `autoresearch` runtime、prompt、mutation、feedback、eval 语义 | `不允许` | 这是开发面，不是收口面 |
| 把 `.autoworkflow/`、deploy target 或 `analysis/` 研究页当成最终真相 | `不允许` | 直接违反当前分层 |

## 十、与后续任务的关系

本文冻结的是“怎么判定”，不是“所有子规则都已写完”。

因此：

- `G-101` 继续负责目录级留删规则本体。
- `G-105` 继续负责真实清理和最小记录。
- `G-201/G-205` 继续负责 closeout surface 与唯一入口。
- `G-301` 继续负责 retained index。
- `G-401` 继续负责 acceptance gate 与正式验收记录。

但从本文生效开始，任何新增请求都应先按本页判定成 `允许 / 不允许 / 需要显式特批`，而不是再拆新的 authority 或 waiver 子任务。
