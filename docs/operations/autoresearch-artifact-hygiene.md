---
title: "Autoresearch artifact 最小留删规则"
status: active
updated: 2026-04-02
owner: aw-kernel
last_verified: 2026-04-02
---
# Autoresearch artifact 最小留删规则

> 目的：只为当前 `autoresearch` closeout 真会触碰的 `.autoworkflow` 热区冻结最小留删规则。本文回答当前对象默认是 `保留 / 归档 / 删除` 哪一类、为什么，以及未覆盖对象如何 `fail closed`。

## 一、适用范围

本文只覆盖当前 closeout 已暴露出来的热区：

- `.autoworkflow/autoresearch/`
- `.autoworkflow/autoresearch-archive/`
- `.autoworkflow/manual-runs/`
- 上述目录下当前已出现或与 closeout 直接相关的特殊子目录，例如：
  - `acceptance-runs/`
  - `acceptance-worktrees/`
  - `worktrees/`
  - `.run-id-state/`

本文不是全仓库 retention policy，也不是下一阶段 `autoresearch` runtime 设计文档。

## 二、动作语义与判定原则

先固定三种默认动作的语义：

- `保留`：对象继续留在当前活跃位置，因为它仍是当前 closeout 的输入、代表性 retained artifact，或 active state。
- `归档`：对象属于历史 lineage，可继续存在，但不应再占据活跃入口或和定义输入混放；`G-105` 做真实清理时，可以保留在 archive 位置，或移入 archive lineage。
- `删除`：对象默认视为运行期副产物、临时控制对象或空壳目录，不作为长期证据位。

判定时再遵守下面四条：

1. 先按“对象形态”判定，再按父目录判定；更具体的子规则优先。
2. 根目录被判定为 `保留` 或 `归档` 时，内部对象默认继承该动作，除非本文另有更细的子目录规则。
3. 本文只冻结默认动作，不在这里直接执行真实移动、归档或删除；真实处置由 `G-105` 负责。
4. 本文未覆盖的对象，默认不做真实处置，转 `需要显式特批`，遵守 [Autoresearch 收口边界与例外决策规则](./autoresearch-closeout-decision-rules.md)。

## 三、热区规则表

### A. `.autoworkflow/autoresearch/`

| 规则单元 | 当前对象示例 | 默认动作 | 为什么 | 允许例外 | 恢复路径 |
| --- | --- | --- | --- | --- | --- |
| active retained run 根目录 | `manual-cr-codex-loop-3round-r000001-m000642/`、`manual-cr-codex-loop-6-3-3-r000001-m046830/` | `保留` | 当前 closeout 已把这两条 run 当作代表性 retained artifact 和 runtime 残留检查对象；它们仍是 `G-301/G-401` 的直接输入。 | 只有在 retained index 与正式清理记录已经补齐，且明确说明“为何不再保留在 active 位”时，才允许降级为 `归档`。 | `可部分恢复`：可由对应 `manual-runs` 定义包、champion branch/sha 和 research CLI 重新 materialize；原始时间戳与局部运行痕迹不保证完全重建。 |
| attached acceptance 结果快照目录 | `manual-cr-codex-loop-6-3-3-r000001-m046830/acceptance-runs/` 下的 `baseline/`、`round-001/`、`round-002/`、`round-003/` | `保留` | 这些结果仍是当前 retained run 的附属证据，尚未被 `G-401` 的正式验收记录替代。 | 当正式 closeout gate 与验收记录落盘后，允许按清理记录把它们降级为 `归档`；未落盘前不默认移动。 | `可部分恢复`：可依赖 retained run、suite manifests 和 acceptance runner 重新执行；但原始输出文件与时间戳不保证 bit-for-bit 一致。 |

### B. `.autoworkflow/autoresearch-archive/`

| 规则单元 | 当前对象示例 | 默认动作 | 为什么 | 允许例外 | 恢复路径 |
| --- | --- | --- | --- | --- | --- |
| archive batch 根目录 | `20260401T105205/` | `归档` | 它是一次真实 closeout archive 的容器，负责承接历史 lineage，不应再回到默认活跃入口。 | 只有在 archive batch 被证明混入了不属于同一批次的对象，且已有书面拆分方案时，才允许移动其子对象。 | `可恢复`：若 batch 误移位，可按同名 archive batch 重新组织；容器本身不承担独立运行语义。 |
| archived 完整 run 包 | `manual-cr-exrepos-codex-first-pass-r000001-m051512/`、`manual-cr-typer-claude/` | `归档` | 这些对象有完整或近完整的 run lineage，适合作为历史审计对象，但不再是当前 retained evidence。 | 只有在后续明确把其中某个对象提升为 retained representative 时，才允许从 archive 提升到 `保留`。 | `可部分恢复`：可由对应定义包和 CLI 重新 materialize，但 archive 中的原始时间戳和局部副产物不保证完全重建。 |
| archived 轻量 lineage 对象 | `demo-run/`、`smoke-init-run/`、`manual-cr-smoke-live/`、`test-p1-logs-run-2/` | `归档` | 这些对象不是完整 retained run，但仍有最小 contract/history/value，可解释历史步骤；它们不应占 active 位，也不需要默认提升成 retained。 | 只有在能够证明对象没有任何 lineage 价值，且删除理由已经写入正式清理记录时，才允许从 `归档` 变为 `删除`。 | `可部分恢复`：多半可由原始 contract/suite 重新生成最小运行结果；若对象只剩历史摘要，则只能恢复语义，不能恢复全部副产物。 |

### C. `.autoworkflow/manual-runs/`

| 规则单元 | 当前对象示例 | 默认动作 | 为什么 | 允许例外 | 恢复路径 |
| --- | --- | --- | --- | --- | --- |
| manual run definition package | `context-routing-codex-loop-3round/`、`context-routing-codex-loop-6-3-3/`、`context-routing-exrepos-codex-first-pass/`、`minimal-context-routing-typer-claude/` | `保留` | 这些目录承接 contract、suite、seed、README 等定义输入，仍是 retained run、archive run 和后续复核的 rerun 基线。 | 只有在明确证明某个定义包已无任何 retained/archive lineage 依赖时，才允许降级为 `归档` 或 `删除`。 | `可部分恢复`：可由已有 analysis 文档、历史命令和 suite manifests 重新拼装，但原目录下的说明文件与人工注记不一定能完整重建。 |
| manual run loose definition file | `manual-cr-smoke-live.contract.json` | `保留` | 它虽然不是目录包，但仍是可执行输入定义；在没有正式替代承接位之前，不应被当成临时垃圾清掉。 | 只有在它被并入正式 definition package，并留下明确前跳说明后，才允许删除旧单文件。 | `可恢复`：可从调用历史或等价 contract 模板重建，但应优先避免误删。 |
| manual run result snapshot family | `acceptance-httpx-high/`、`check-suite-acceptance-high/`、`check-suite-acceptance-default300/`、`check-single-run-typer-high/`、`retry-train-high-full-auto/` | `归档` | 这些目录的主体是时间戳结果快照和 `run-summary.json`，它们属于历史执行结果，不应继续和定义输入混放在 active `manual-runs/` 语义里。 | 如果某个 snapshot family 被后续 gate 或 retained index 明确选为长期证据，可单独提升为 `保留`；否则 `G-105` 应把它们移到 archive lineage，而不是继续留在 active 定义层。 | `可部分恢复`：通常可由对应 definition package、suite manifests 和 runner 重新执行；原始输出日志与 judge 响应不保证完全一致。 |
| `.run-id-state/` | `.run-id-state/context-routing-codex-loop-6-3-3/manual-cr-codex-loop-6-3-3.json` | `保留` | 这是当前 repo-local run id allocator state，仍被运行说明直接引用；它不是历史快照，也不应并入 archive lineage。 | 只有在相关 definition package 被正式退役且 run id state 有替代机制时，才允许重置或迁移。 | `可恢复但有代价`：可手工重建 state 文件，但会引入 run id 连续性中断风险，所以不作为默认清理对象。 |

## 四、特殊子目录与临时对象规则

| 规则单元 | 当前对象示例 | 默认动作 | 为什么 | 允许例外 | 恢复路径 |
| --- | --- | --- | --- | --- | --- |
| `worktrees/` | active/archived run 下的 `worktrees/` 空目录 | `删除` | `worktrees/` 是运行期 scratch 位，不是 closeout 默认长期证据；当前已观察到的同类目录都是空目录。 | 只有当 `runtime.json` 仍有 `active_round`，或有未完成的 forensics 明确需要保留候选工作树时，才允许暂时保留。 | `可恢复`：可通过 `prepare-round`、重新 checkout candidate branch 或重新 materialize run 来恢复。 |
| `acceptance-worktrees/` | `manual-cr-codex-loop-6-3-3-r000001-m046830/acceptance-worktrees/` | `删除` | 它是 acceptance 运行期 scratch 位，不承接最终 acceptance 结果；当前对象还是空目录。 | 只有在 acceptance 过程尚未收束，且确实存在未整理出的候选工作树内容时，才允许暂留。 | `可恢复`：可通过重新运行 acceptance materialization 或重新 checkout acceptance candidate 来恢复。 |
| 空的生成型目录 | `manual-cr-typer-claude/baseline/validation/20260327T143546Z-validation/` | `删除` | 这类目录只保留了时间戳壳，没有任何结果内容，不能独立承担证据语义。 | 只有在能证明外部进程仍绑定该路径，或目录即将被同轮命令继续写入时，才允许暂留。 | `可恢复`：直接重新 materialize 对应 baseline/validation 输出即可。 |
| 临时控制文件 | `acceptance-run.pid`、`acceptance-run.log`、`acceptance-run.sh` | `删除` | 它们是进程控制或一次性启动脚本，不是 retained/archived evidence。即使日志里含少量信息，也不应替代正式 run summary 或 acceptance record。 | 只有在当前 closeout 正在调查一次未完成或异常退出的 acceptance 执行时，才允许短暂保留日志用于排障。 | `可恢复`：可通过重新生成启动脚本、重跑 acceptance 命令或从正式结果文件补日志摘要来恢复。 |

## 五、未覆盖对象的 fail-closed 处理

遇到下面任一情况，默认不做真实处置，转 `需要显式特批`：

- 对象不属于本文列出的规则单元。
- 同一对象同时混合了“定义输入”和“结果快照”两种语义，无法直接归类。
- 调用方想把 `归档` 直接改判成 `删除`，但没有最小记录说明为什么该对象已无 lineage 价值。
- 调用方想把 `删除` 类对象临时提升成 retained evidence，但没有正式承接位。

最小处理方式：

1. 先在 `G-105` 的清理记录里写明对象路径和冲突原因。
2. 再按 [Autoresearch 收口边界与例外决策规则](./autoresearch-closeout-decision-rules.md) 走显式批准。
3. 如果同类对象反复出现，下一步应回到本文补规则，而不是继续口头判定。

## 六、与后续任务的承接关系

- `G-105`：按本文执行真实 `保留 / 归档 / 删除` 动作，并留下最小记录。
- `G-301`：只为本文判定为 `保留`，或经显式批准后提升为 `保留` 的对象建 retained index。
- `G-401`：可使用本文保留的 retained run 和 acceptance 结果做 gate 输入，但不把 `worktrees/`、`acceptance-worktrees/` 或 `.pid/.log/.sh` 重新提升为正式证据位。

一句话判断：

- 仍是 closeout 当前输入或代表性 evidence：`保留`
- 只剩历史 lineage 价值：`归档`
- 只是运行期副产物、空壳目录或临时控制对象：`删除`
