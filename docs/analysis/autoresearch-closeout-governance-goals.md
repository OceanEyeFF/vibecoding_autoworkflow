---
title: "Autoresearch：收口治理目标"
status: superseded
updated: 2026-04-08
owner: aw-kernel
last_verified: 2026-04-08
---
# Autoresearch：收口治理目标

> 说明：本文归档已完成的 `autoresearch` 阶段收口治理目标、边界与完成判断，用来约束“这段时间为什么做治理、治理做到什么算完成”，现在仅作为本轮 closeout 的 lineage 基线与 audit 证据，不再代表当前执行入口。

> 入口位说明：本文是 closeout lineage-only 的目标正文叶子页，只在复核 closeout 完成或 gate 审计时查阅；默认分流入口先回到 [Analysis README](./README.md)，日常 active 入口仍以 `overview + minimal-loop + research-cli-help + tmp-exrepo-maintenance + Analysis README` 为准。

## 一、当前定位

当前收口治理期只回答三件事：

- 当前阶段应该留下什么，应该清掉什么
- 当前哪些文档和入口仍然有效，哪些只保留 lineage
- 如何证明这次收口已经完成，而不是表面整理

当前收口治理期不回答：

- 下一阶段先改哪段 `autoresearch` 实现
- 下一阶段如何重构 `feedback distill / mutation / prompt`
- 下一阶段需要哪些 canary、评测口径或开发入口

## 二、治理目标

### 1. 锁定收口边界

要做什么：

- 明确收口期 `allowed / forbidden changes`
- 明确谁能拍板 `superseded / archive / delete / retain / waiver`

为什么要做：

- 如果边界和 authority 不先冻结，后面的文档清理、artifact 清理和 gate 都会被反复打回

完成收益：

- 收口期不再一边治理一边重新滑回开发期

### 2. 理顺当前入口与生命周期

要做什么：

- 校准 `docs/analysis/README.md` 当前入口
- 给历史 planning 补 `superseded` 与前跳说明
- 为保留但非默认入口的文档补“不是当前执行入口”提示

为什么要做：

- 当前最大的治理风险不是“没有文档”，而是“文档太多但入口状态不清楚”

完成收益：

- 新进入者能快速知道当前主入口是什么，不会停在历史 planning 上打转

### 3. 固定运行产物的留删规则

要做什么：

- 给 `.autoworkflow` 建 retention policy
- 回答哪些 artifact 必留、可归档、可删除
- 给关键目录建立单独保留规则

为什么要做：

- 运行产物是当前最容易膨胀、最容易返工、也最容易失去解释链的区域

完成收益：

- 每个 artifact 都能回答“为什么还在”或“为什么可以删”

### 4. 让保留下来的证据可追溯

要做什么：

- 给 retained run 建 manifest / index
- 统一命名与标签
- 给代表性 run 补保留原因和复查信息

为什么要做：

- “保留”不等于“以后找得到、看得懂、追得回”

完成收益：

- 后续复盘和 handoff 不再依赖目录猜测或个人记忆

### 5. 用可执行 gate 证明收口成立

要做什么：

- 把 closeout 退出条件做成脚本检查
- 检查残留运行态、deploy sync 状态，并把结果落盘

为什么要做：

- 没有 gate 的收口只是主观判断，不是可复核状态

完成收益：

- 可以明确证明“本阶段已经可信收口”，而不是靠口头确认

## 三、完成判断

当下面几句话都成立时，说明这次收口治理期达标：

- 不再有人需要追问“这件事现在算不算 closeout scope”
- `docs/analysis/` 当前入口不会把人带进历史 planning
- `.autoworkflow` 下的运行产物有清楚的保留、归档、删除解释
- 被保留的代表性 runs 已登记进 manifest，并带有最小 retention metadata
- closeout gate 能检查关键残留状态，并留下正式验收记录

### 当前状态（2026-04-02）

截至 `2026-04-02`，上面的完成判断已满足：

- 当前 closeout 的边界、默认判定、最小 authority 与例外口径已冻结到 [`../operations/autoresearch-closeout-decision-rules.md`](../operations/autoresearch-closeout-decision-rules.md)。
- `docs/analysis/README.md` 已承担唯一目录页型默认入口，历史 planning 已退回叶子页并补齐非默认入口提示。
- `.autoworkflow` 热区对象的最小 `保留 / 归档 / 删除` 规则已落到 [`../operations/autoresearch-artifact-hygiene.md`](../operations/autoresearch-artifact-hygiene.md)，真实清理记录与 retained index 已落到 [`../operations/autoresearch-closeout-cleanup-and-retained-index.md`](../operations/autoresearch-closeout-cleanup-and-retained-index.md)。
- closeout gate 已承接到 [`../operations/autoresearch-closeout-acceptance-gate.md`](../operations/autoresearch-closeout-acceptance-gate.md)，并已有 `.autoworkflow/closeout/autoresearch-closeout-governance-task-list-20260402/integration-acceptance.json` 作为正式验收记录。

## 四、明确不做

- 不写下一阶段 implementation task plan
- 不做 P2 问题审计、低分 taxonomy 或瓶颈优先级
- 不做 `feedback contract`、`mutation`、prompt 改写等开发准备
- 不重构下一阶段验证体系，也不在这里冻结新的 canary 方案
- 不把当前收口治理期写成新的长期真相层

## 五、升级路径

当前状态：

- 本轮 closeout 已完成；稳定下来的维护规则已经承接到 `docs/operations/` 的治理维护文档。
- 本文继续保留为本轮 closeout 的目标基线和 lineage 入口，不承担默认入口或运行规则承接位。

## 六、相关文档

- [Autoresearch：收口治理任务清单](./autoresearch-closeout-governance-task-list.md)
- [Autoresearch 收口边界与例外决策规则](../operations/autoresearch-closeout-decision-rules.md)
- [Autoresearch closeout 入口层级规则](../operations/autoresearch-closeout-entry-layering.md)
- [Autoresearch artifact 最小留删规则](../operations/autoresearch-artifact-hygiene.md)
- [Autoresearch P2：TMP Exrepo 运行时迁移与维护脚本任务规划](./autoresearch-p2-tmp-exrepo-runtime-task-plan.md)
- [Analysis README](./README.md)
