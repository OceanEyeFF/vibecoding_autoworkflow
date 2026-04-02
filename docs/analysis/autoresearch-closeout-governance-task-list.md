---
title: "Autoresearch：收口治理任务清单"
status: active
updated: 2026-04-02
owner: aw-kernel
last_verified: 2026-04-02
---
# Autoresearch：收口治理任务清单

> 说明：本文是当前 `autoresearch` 收口治理期的执行任务清单。本版按 `2026-04-02` 的复审结果收缩任务，只保留会改变当前仓库状态、入口结构或验收结论的主任务；不再把同一问题拆成多个文档导向工单。

> 入口位说明：本文是当前 closeout 的任务正文叶子页，不单独承担默认入口；当前 `analysis/` 层分流入口仍以 [Analysis README](./README.md) 为准。

## 一、任务收缩原则

- 只保留当前 closeout 的真实 blocker，不为“看起来完整”补治理制度。
- 如果某条内容只是另一主任务里的章节、判断规则或输出要求，不再单列任务。
- `authority`、`waiver`、`cleanup log`、`retention metadata` 这类内容，只有在它们单独构成阻塞时才拆出；否则吸收到主任务。
- 能作为默认入口的文件，必须是“目录页型文件”：
  - 只负责说明本层语义，并链接下一级正文。
  - 非目录页正文可以被链接，但不能和目录页竞争同层默认入口地位。

## 二、执行顺序

当前建议按下面顺序推进：

1. `G-001`：冻结 closeout 边界与例外决策口径
2. `G-101`：固定当前 autoresearch artifact 的最小留删规则
3. `G-201`：固定 closeout 入口页层级规则，并把历史 planning 退回叶子页地位
4. `G-105`：按规则执行一次真实清理并留下最小记录
5. `G-205`：收敛唯一 closeout 入口页
6. `G-301`：登记 closeout 期明确保留的代表性 artifact
7. `G-401`：执行一次可重复的 closeout acceptance gate

说明：

- `G-101` 和 `G-201` 都依赖 `G-001`，但两者可以并行推进。
- `G-105` 必须建立在 `G-101` 已基本稳定之后。
- `G-205` 必须建立在 `G-201` 已明确“目录页型入口 vs 叶子页正文”之后。
- `G-301` 应建立在 `G-105` 之后，不先给“还没决定留不留”的对象做 central index。
- `G-401` 只在最后收尾，用来证明当前阶段已可信收口。

## 三、当前进度（2026-04-02）

本节按收缩后的 `7` 条主任务重新计数，不继承旧版 `22` 条拆分工单的统计。

当前跟踪口径：

- `已完成`：仓库内已经有稳定承接位，且基本满足本版主任务的完成标准。
- `部分完成`：已有局部规则、局部动作或可复核证据，但还没有收成正式承接位。
- `未开始`：尚未看到满足本版主任务完成标准的正式落点。

当前统计：

- `已完成`：`3 / 7`
- `部分完成`：`3 / 7`
- `未开始`：`1 / 7`

当前可直接复核的证据快照：

- `docs/analysis/README.md` 已区分“当前执行规划”和“历史执行规划”。
- `python3 toolchain/scripts/test/path_governance_check.py` 在本次复核中已通过，说明当前文档入口与生命周期状态没有明显结构性回退。
- `python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents|claude|opencode` 在本次复核中都已通过，说明当前 repo-local deploy target 没有明显 drift。
- `docs/operations/autoresearch-closeout-decision-rules.md` 已冻结当前 closeout 的 `允许 / 不允许 / 需要显式特批` 判定口径，并把最小 authority 与例外处理口径收进同一承接位。
- `docs/operations/autoresearch-artifact-hygiene.md` 已把 `.autoworkflow/autoresearch/`、`.autoworkflow/autoresearch-archive/`、`.autoworkflow/manual-runs/` 及特殊子目录的最小 `保留 / 归档 / 删除` 规则收成正式 runbook。
- `docs/operations/autoresearch-closeout-entry-layering.md` 已冻结“目录页型入口 vs 叶子页正文”的 closeout 口径，并明确当前由 `docs/analysis/README.md` 承担 `analysis/` 层目录页分流。
- `.autoworkflow/autoresearch-archive/20260401T105205/` 已存在一次真实归档结果，说明收口清理不只是纸面动作。
- 当前保留的两条 autoresearch 主 run：`.autoworkflow/autoresearch/manual-cr-codex-loop-3round-r000001-m000642/runtime.json` 和 `.autoworkflow/autoresearch/manual-cr-codex-loop-6-3-3-r000001-m046830/runtime.json` 都显示 `active_round: null`。
- 部分手工 run 包已经带本地 `README.md` 或 `run-summary.json`，说明 retained artifact 的局部说明位已经存在，但还没有 central retained index。
- `docs/operations/` 里现在已经有 closeout 专用的 artifact hygiene runbook；但 retained index 和 acceptance gate 文档仍未落盘，相关承接位仍然缺失。
- 当前 closeout 正文虽然已经退回 leaf page，但仓库里仍没有单独承担 closeout 分流职责的唯一目录页型入口；当前仍借 `docs/analysis/README.md` 临时分流。
- 五份 `status: superseded` 的历史 planning 页都已补“不是当前默认入口”的页首说明，并回跳到 `Analysis README` 或仍 active 的承接文档。

#### A. 当前跟踪结果：收口边界与决策口径

- `G-001`：`已完成`。`docs/operations/autoresearch-closeout-decision-rules.md` 已把 `allowed / forbidden`、默认判定、最小 authority 和例外规则冻结到同一份 repo-local 承接文档，不再需要继续拆 `authority matrix` 或 `waiver` 子任务。

#### B. 当前跟踪结果：artifact 留删与实清理

- `G-101`：`已完成`。`docs/operations/autoresearch-artifact-hygiene.md` 已把当前 closeout 真会触碰的热区对象收成最小 `保留 / 归档 / 删除` 规则，并覆盖 `.autoworkflow/autoresearch/`、`.autoworkflow/autoresearch-archive/`、`.autoworkflow/manual-runs/`、`acceptance-runs/`、`acceptance-worktrees/`、`worktrees/`、`.run-id-state/` 与临时控制文件的默认动作。
- `G-105`：`部分完成`。仓库里已经发生过一次真实归档，但这轮动作还没有和正式留删规则、最小记录模板绑定；当前也还看不到一个能直接回答“处置了什么、为什么、是否可恢复、由谁判断”的正式记录位。

#### C. 当前跟踪结果：入口层级与 closeout surface

- `G-201`：`已完成`。`docs/operations/autoresearch-closeout-entry-layering.md` 已把“目录页型入口 vs 叶子页正文”的 closeout 口径冻结成正式规则；`docs/analysis/README.md` 已明确承担目录页分流，历史 planning 也已退回叶子页并补齐非默认入口提示。
- `G-205`：`未开始`。当前目录页与叶子页关系虽然已经澄清，但仓库里还没有一个单独承担 closeout 分流职责的唯一目录页型入口；当前仍借 `docs/analysis/README.md` 临时分流。

#### D. 当前跟踪结果：保留证据登记

- `G-301`：`部分完成`。局部 run 包已有 `README.md` 或 `run-summary.json`，但还没有一个只登记“本轮明确保留对象”的 retained index；当前仍需要分别进入 manual run 包或 acceptance artifact 目录才能解释“为什么还在”。

#### E. 当前跟踪结果：收口验收

- `G-401`：`部分完成`。`path_governance_check.py`、三路 `adapter_deploy.py verify` 和 retained run 的 runtime 状态都能提供局部证据，但还没有把这些检查收成统一的 closeout acceptance gate，也还没有正式验收记录。

## 四、主任务清单

### A. 收口边界与决策口径

#### G-001：冻结 closeout 边界与例外决策口径

- 要做什么：把 closeout 允许项、禁止项、默认判定规则写清，并在同一承接位里补最小 authority 口径和例外处理口径。
- 依赖：无
- 完成标准：任何变更请求都能直接判断成 `允许 / 不允许 / 需要显式特批`，不再继续拆成单独的 `authority matrix` 任务和 `waiver` 任务。

### B. Artifact 留删与实清理

#### G-101：固定当前 autoresearch artifact 的最小留删规则

- 要做什么：只对当前 closeout 会真正触碰的热区目录写最小留删规则，至少覆盖：
  - `.autoworkflow/autoresearch/`
  - `.autoworkflow/autoresearch-archive/`
  - `.autoworkflow/manual-runs/`
  - 必要时补 `acceptance-worktrees/` 这类特殊子目录
- 依赖：`G-001`
- 完成标准：当前会被清理的对象都能回答 `保留 / 归档 / 删除，为什么`。
- 说明：目录级细化和 runbook 承接位都并入本任务；不再把“基线”和“runbook 落盘”拆成两条任务。

#### G-105：按规则执行一次真实清理并留下最小记录

- 要做什么：按 `G-101` 的规则执行一次真实清理，并留下最小记录，至少说明：
  - 处置了什么
  - 为什么这样处置
  - 是否可恢复
  - 由谁判断
- 依赖：`G-101`
- 完成标准：规则已经改变了当前仓库状态，而不只是停留在纸面说明。
- 说明：最小记录要求直接并入本任务；不再单列“cleanup log 规则”。

### C. 入口层级与 Closeout Surface

#### G-201：固定 closeout 入口页层级规则，并把历史 planning 退回叶子页地位

- 要做什么：把“目录页型入口 vs 叶子页正文”的层级规则写清，并确保历史 planning 只保留 lineage，不再和目录页竞争同层默认入口地位。
- 依赖：`G-001`
- 完成标准：默认入口只由目录页型文件承担；历史 planning 虽然仍可读，但已经退回叶子页地位。
- 说明：历史 planning 的退役说明、非默认入口提示都并入本任务；阶段复盘只在已有稳定事实缺少落点时补，不再作为 closeout 主清单 blocker。

#### G-205：收敛唯一 closeout 入口页

- 要做什么：为当前 closeout 收敛唯一默认入口；它可以是目录页型 summary entry，也可以是 `docs/analysis/README.md` 里的唯一 closeout block，但不能再让多个正文页并列承担入口职责。
- 依赖：`G-201`
- 完成标准：新进入者只需先看一个目录页型入口，就能分流到 goals、task list、runbook 和 gate。
- 说明：“补承接回链”和“审视最短路径”都属于本任务的验收要求，不再单列。

### D. 保留证据登记

#### G-301：登记 closeout 期明确保留的代表性 artifact

- 要做什么：建立一个 retained index，只记录本轮明确决定保留的 run / archive 及其保留原因，不追求全量 `.autoworkflow` 编目。
- 依赖：`G-105`
- 完成标准：任何被刻意保留的对象，都能在统一入口回答“为什么还在”。
- 说明：代表性保留对象和最小保留说明都并入本任务；不再单列命名 / 标签制度。

### E. 收口验收

#### G-401：执行一次可重复的 closeout acceptance gate

- 要做什么：统一执行：
  - 文档入口检查
  - deploy sync verify
  - autoresearch runtime 残留检查
  - 一次正式验收结果落盘
- 依赖：`G-105`、`G-205`、`G-301`
- 完成标准：可以重复证明“当前已可信收口”，而不是靠口头确认。
- 说明：检查项和 summary 输出都属于 gate 的组成部分，不再拆成两条后续工单。

## 五、本轮明确不再单列

- authority / exception 规则：并入 `G-001`，不再单列。
- 目录级留删细化、runbook 承接位：并入 `G-101`，不再拆开。
- cleanup log：并入 `G-105` 的最小记录要求。
- 容量预算与超限提醒：删除；当前 closeout 的真实 blocker 不是容量预算，而是没有最小留删规则。
- 历史 planning 的退役说明、非默认入口提示：并入 `G-201`。
- 阶段复盘：降级为备注；只有在已有稳定事实缺少落点时才补，不再作为关键路径任务。
- 最短路径审视与承接回链：并入 `G-205`。
- 独立的 manual run 命名 / 标签制度：删除；fresh `run_id` 规则已经存在，不是当前 closeout blocker。
- 代表性保留对象说明与 retention metadata：并入 `G-301`。
- gate 检查项和 readable summary：并入 `G-401`。

## 六、最小里程碑

### 当前里程碑状态（2026-04-02）

- `Milestone 1：Freeze`：`达标`。当前 closeout 的边界、默认判定、最小 authority 和例外口径都已经冻结到统一承接位。
- `Milestone 2：Retention & Cleanup`：`部分推进`。最小留删规则已经冻结，也已经发生过一次真实归档；当前剩余缺口主要是按规则执行一次真实清理并留下最小记录。
- `Milestone 3：Closeout Surface`：`部分推进`。目录页型入口原则已经冻结，历史 planning 也已退回叶子页；当前剩余缺口主要是把 closeout 收敛成唯一默认入口。
- `Milestone 4：Retained Evidence`：`早期推进`。局部 README / manifest 已存在，但 central retained index 还没有建立。
- `Milestone 5：Gate`：`早期推进`。已有可复用检查组件，但还没有统一的 closeout acceptance gate 和验收记录。

### Milestone 1：Freeze

- 包含任务：`G-001`
- 达标判断：closeout 边界、默认判定和最小例外口径已冻结。

### Milestone 2：Retention & Cleanup

- 包含任务：`G-101`、`G-105`
- 达标判断：当前热区目录的留删规则已经成形，并且已经按规则做过一次真实清理。

### Milestone 3：Closeout Surface

- 包含任务：`G-201`、`G-205`
- 达标判断：默认入口只由目录页型文件承担，历史 planning 已退回叶子页地位，closeout 入口只剩一个默认落点。

### Milestone 4：Retained Evidence

- 包含任务：`G-301`
- 达标判断：本轮刻意保留的对象已有统一登记入口，不再靠个人记忆解释。

### Milestone 5：Gate

- 包含任务：`G-401`
- 达标判断：closeout acceptance gate 能正式证明当前阶段已可信收口。

## 七、明确不纳入本清单

- 下一阶段 implementation task plan
- P2 问题审计、低分 taxonomy、瓶颈排序
- `feedback contract`、`mutation`、prompt 改写和其他开发准备
- 下一阶段 canary 和验证体系重构
- 容量预算与超限提醒
- 独立的 manual run 命名 / 标签制度

## 八、相关文档

- [Autoresearch：收口治理目标](./autoresearch-closeout-governance-goals.md)
- [Autoresearch 收口边界与例外决策规则](../operations/autoresearch-closeout-decision-rules.md)
- [Autoresearch closeout 入口层级规则](../operations/autoresearch-closeout-entry-layering.md)
- [Autoresearch artifact 最小留删规则](../operations/autoresearch-artifact-hygiene.md)
- [Autoresearch P2：TMP Exrepo 运行时迁移与维护脚本任务规划](./autoresearch-p2-tmp-exrepo-runtime-task-plan.md)
- [Analysis README](./README.md)
