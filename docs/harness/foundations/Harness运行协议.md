---
title: Harness 运行协议
status: active
updated: 2026-05-14
owner: OceanEye
last_verified: 2026-05-14
---

# Harness 运行协议

> 目的：固定 Harness 如何从状态估计推进到执行、验证、裁决和状态更新。Doctrine 边界见 [Harness指导思想.md](./Harness指导思想.md)；正式对象字段见 [artifact/](../artifact/README.md)。

> Split plan：本文件仍是 runtime protocol 的当前入口和权威正文；拆章计划见 [runtime-protocol-chapter-plan.md](./runtime-protocol-chapter-plan.md)。迁移完成前，不把 runtime 细节写入 [Harness指导思想.md](./Harness指导思想.md)，也不把 artifact fields、catalog inventory、workflow policy、design analysis 或 executable skill source 混入本文件。

## 一、协议总定义

Harness 是 repo 演进的分层闭环控制协议。它不直接替代执行器，而是决定：

- 处于 `RepoScope` 还是 `WorktrackScope`
- 允许哪个 `Function` 算子
- 消费哪些 `Artifact`
- 由哪个 `Skill` 或执行载体完成本轮动作
- 需要哪些 `Evidence`
- `Gate` 是否允许状态推进
- 失败或阻塞时走哪个恢复路径

最小控制链：

```text
state estimate
-> choose operator
-> bind skill or execution carrier
-> package task/info
-> dispatch
-> collect evidence
-> judge
-> update control state
```

单个 skill 的 bounded round 只限制本轮局部动作。未命中正式 stop condition 时继续推进到下一合法状态转移。

## 二、控制平面与执行平面

Harness 本体属于控制平面。

控制平面负责：

- 选择下一合法算子
- 绑定 skill 或执行载体
- 打包任务与信息
- 定义证据面
- 裁决状态能否推进
- 安排恢复或收尾

执行平面负责实际改变 repo：

- 编码
- review
- test
- 文档更新
- merge / cleanup / rollback

需实际执行时，Harness 先按 [Dispatch Decision Policy](./dispatch-decision-policy.md) 判断执行载体，再 dispatch 给独立 `SubAgent`、human executor、专用 skill、通用执行载体或明确的 current-carrier。`auto` 不表示"能委派就委派"；它表示根据任务耦合度、共享状态需求、并行价值、风险、权限边界和上下文预算选择载体。回退标记为 `runtime fallback`、`permission blocked` 或 `dispatch package unsafe`。

`Dispatch` 与 `Implement` 的边界：`Dispatch` 属控制平面——选择载体、打包任务并分派，不直接执行 repo 变更。`Implement` 属执行平面——接收 dispatch packet，执行编码、review、测试、文档更新等变更动作，返回结构化执行结果与证据。`Implement` 是 bounded execution 的运行时载体。一次 `Dispatch` 对应一次 `Implement` 往返，`Implement` 完成后控制权回到 `Verify`/`Judge`。控制平面决定"做什么、谁来做、怎么验收"；执行平面完成"实际做并回传结果"。

## 三、Scope 与状态

### RepoScope

`RepoScope` 管 repo 长期参考信号与慢变量。

最小状态：

- `observing`
- `deciding`
- `change-control`
- `ready-for-worktrack`

合法算子：

| 算子 | 作用 |
| --- | --- |
| `Observe` | 读取 repo goal、snapshot、branch、治理和已知风险 |
| `Decide` | 判断下一步为开 worktrack、处理 append request、刷新状态或进入目标变更 |
| `RouteAppend` | 对 `append-feature` / `append-design` 做分类与路由 |
| `ChangeGoal` | 处理外部目标变更请求，禁止常规 `Decide` 移动目标 |
| `Close / Refresh` | worktrack closeout 后刷新 repo snapshot |

**Milestone Pipeline** 是 RepoScope 下的中短期目标队列：

- 多个 milestone 可同时处于 `planned` 状态，按 `pipeline_priority` 排列
- 同一时刻仅一个 `active` milestone
- 当前 `active` milestone 完成后，pipeline 按优先级激活下一个满足前置条件的 `planned` milestone
- goal-driven milestone 完成采用双重验收模型：`worktrack_list_finished` AND `purpose_achieved`；其中 `purpose_achieved` 前置独立 `Milestone Gate`
- `Milestone Gate` 位于所有相关 worktrack 关闭后、`purpose_achieved` 检查前，最少包含黑盒测试、白盒测试和反作弊检测
- goal-driven milestone 在 `planned` → `active` 前，harness 必须先向 programmer 输出结构化 brief（goal / signals / criteria / worktrack list / threshold / dependencies / activation reason）并等待确认；work-collection milestone 维持既有自动激活语义
- 修改 milestone 的 `completion_signals`、`acceptance_criteria` 或 `completion_threshold_pct` 时，必须重新评估 milestone；仅追加归属当前 milestone 的 worktrack 不触发该重评估
- `milestone-status-skill` 负责进度观测，`harness-skill` 负责状态转移和 pipeline 推进
- goal-driven milestone 的执行推进以逐 worktrack 闭环为节奏：当前轮次从 `worktrack_list` 中选择一个 current worktrack，为其建立独立 branch、contract、plan、verify、closeout 与 repo-refresh 追踪；闭环完成后再返回 milestone 上下文继续推进
- 详细合同见 [milestone.md](../artifact/control/milestone.md) 和 [milestone-backlog.md](../artifact/repo/milestone-backlog.md)

### WorktrackScope

`WorktrackScope` 管局部状态转移。

最小状态：

- `initializing`
- `observing`
- `scheduling`
- `dispatching`
- `implementing`
- `verifying`
- `judging`
- `recovering`
- `closing`
- `blocked`
- `closed`

合法算子：

| 算子 | 作用 |
| --- | --- |
| `Init` | 建立 branch、baseline、contract 与初始 plan |
| `Observe` | 读取 worktrack artifact、diff、测试和阻塞 |
| `Decide` | 从 task queue 选择下一动作 |
| `Dispatch` | 选择载体、打包任务、分派并等待返回 |
| `Implement` | 接收分派任务包，执行实际变更，返回结构化执行结果与证据 |
| `Verify` | 收集 review / test / rule-check 等证据 |
| `Judge` | 汇总证据形成 gate verdict |
| `Recover` | 在 fail / blocked / drift 后选择恢复动作 |
| `Close` | PR / merge / cleanup / handoff，交给 `RepoScope` refresh |

## 四、最小闭环

```text
RepoScope.Observe (含 milestone pipeline 状态)
-> RepoScope.Decide (milestone-first: 无 active milestone 则建议创建/激活)
    ├─→ 无 active milestone → RepoScope.Init (init-milestone-skill)
    └─→ 有 active milestone → WorktrackScope.Init (从 milestone 派生 worktrack)
-> WorktrackScope.Observe
-> WorktrackScope.Decide
-> WorktrackScope.Dispatch
-> WorktrackScope.Implement
-> WorktrackScope.Verify
-> WorktrackScope.Judge
-> WorktrackScope.Close 或 WorktrackScope.Recover
-> RepoScope.Refresh (含 milestone progress 写回 + worktrack-backlog 更新)
-> RepoScope.Observe (goal-driven: worktrack 全部关闭后先执行 Milestone Gate，再做 purpose_achieved 检查)
    ├─→ milestone achieved → pipeline 推进 (激活下一 planned → active)
    └─→ milestone 未完成 → 继续当前 milestone 的下一 worktrack
```

每个 current worktrack 都走自己的完整闭环；milestone 通过这些独立闭环的累计结果形成聚合进度、Milestone Gate 输入和最终完成判定。

`PR` 不是闭环终点。完整 closeout：

```text
merge -> refresh repo snapshot -> update milestone progress -> cleanup -> return RepoScope
```

Milestone 验收分层：

- Worktrack Gate 属于 `WorktrackScope.Judge`，裁决单个 worktrack 是否允许 closeout。
- Milestone Gate 属于 `RepoScope.Observe` 的 milestone 集成验证步骤，只在相关 worktrack 全部关闭后执行。
- Milestone Gate 消费已关闭 worktrack 的 gate evidence，并补充 milestone 级黑盒/白盒/反作弊检查；它不替代 worktrack gate，也不引入第三 Scope。
- 每个 worktrack 的 closeout record、repo-refresh checkpoint 和 gate evidence 共同构成 milestone 级聚合输入，使逐项执行与 milestone 完成语义保持连续可追踪。

## 五、正式对象

本协议只列对象职责。字段细节由对应 artifact 文档承接。

| 对象 | 承接位 |
| --- | --- |
| `Repo Goal / Charter` | [goal-charter.md](../artifact/repo/goal-charter.md) |
| `Repo Snapshot / Status` | [snapshot-status.md](../artifact/repo/snapshot-status.md) |
| `Worktrack Contract` | [contract.md](../artifact/worktrack/contract.md) |
| `Plan / Task Queue` | [plan-task-queue.md](../artifact/worktrack/plan-task-queue.md) |
| `Gate Evidence` | [gate-evidence.md](../artifact/worktrack/gate-evidence.md) |
| `Milestone` | [milestone.md](../artifact/control/milestone.md) |
| `Milestone Pipeline / Backlog` | [milestone-backlog.md](../artifact/repo/milestone-backlog.md) |
| `Worktrack Backlog` | [worktrack-backlog.md](../artifact/repo/worktrack-backlog.md) |
| `Harness Control State` | [control-state.md](../artifact/control/control-state.md) |
| `Goal Change Request` | [goal-change-request.md](../artifact/control/goal-change-request.md) |
| `Append Request` | [append-request.md](../artifact/control/append-request.md) |

`Control State` 只保存控制面状态。业务真相写回 repo / worktrack 正式文档和对应源码层。

每次启动从 `.aw/control-state.md` 恢复控制配置，再判断 Scope / Function。最小读取面包括 linked formal documents、approval boundary、continuation authority、handback guard、baseline traceability 和 autonomy ledger。缺失配置按 [control-state.md](../artifact/control/control-state.md) 默认值降级，输出暴露 `config_hydration_gaps`。不得因缺失扩大自动性、绕过审批或忽略上次 handback 边界。

如果 programmer 给出长期权限、自动性或分派策略变更，Harness 必须区分一次性审批和持久配置。一次性审批写入 evidence / handoff；持久配置变更写入 `.aw/control-state.md` 对应 policy / ledger 字段。改变 canonical 字段语义或默认值时，同步更新 control-state artifact 合同与初始化模板。

## 六、连续推进与停止条件

默认语义是连续推进，而不是每完成一个 skill round 就自动把控制权交还给 programmer。

最小 stop conditions：

- 需要 programmer 批准的 goal change、scope expansion、destructive action 或 authority boundary
- goal-driven milestone 激活前的结构化 brief 需要 programmer 确认
- 必需 artifact / evidence 缺失、过时或互相冲突
- `Gate` 给出 `soft-fail`、`hard-fail` 或 `blocked`
- host runtime 没有合法 execution carrier / dispatch shell
- 下一动作越过已批准输入、`Worktrack Contract` 或 repo baseline
- 同一交接边界在连续无变化轮次中再次被确认

补充约束：

- "skill 已返回结构化结果"不构成 stop condition。
- 无专门 skill 时进入 fallback execution carrier。
- runtime dispatch shell 缺位报告为 `runtime gap`，不伪装成已完成 `SubAgent` 委派。

当 programmer 明确指示连续执行时，`Worktrack Close` 只是 repo refresh 或 milestone progress update 的状态刷新点，不默认触发 handback。连续推进仅在以下条件 handback：
- 命中必要审批（goal change、scope expansion、destructive action 或 authority boundary）
- 命中 goal-driven milestone 激活简报确认边界
- 证据缺失/冲突、路由阻塞、运行时缺口或范围阻塞
- 命中 Milestone 验收边界（`milestone_acceptance_verdict == achieved` 或 `blocked`）
- Pipeline advancement 触发（当前 milestone 完成，自动激活下一 planned milestone）

`autonomy_budget` 消费规则：每个 autonomous slice 开启时消费 1 个 budget 单位。budget 耗尽后不得自动开启新 slice，必须 handback。`handback guard` 与连续执行：连续执行模式下 handback guard 仍然生效。stable-handback 判定、交接锁激活与 unlock signal 验证逻辑不因连续执行跳过。连续执行只改变 handback 的默认触发时机，不改变 handback guard 语义。

bounded round handoff 应优先给出 `allowed_next_routes`、`recommended_next_route`、`continuation_ready`、`continuation_blockers`、`approval_required`、`approval_scope`、`approval_reason`。

## 六-A、Handback 与交接锁

Handback 是 Harness 将控制权交还给 programmer 的正式交接动作，由明确的触发条件驱动。

### 触发条件

Handback 在以下条件触发：
- 审批门控：需要 programmer 批准的 goal change、scope expansion、destructive action 或 authority boundary
- 证据门控：必需 artifact / evidence 缺失、过时或冲突，且无法在本轮自动补齐
- 路由阻塞：`Gate` 给出 `soft-fail`/`hard-fail`/`blocked`，且 Recover 无法自动恢复
- 运行时缺口：host runtime 缺少合法 execution carrier / dispatch shell
- 约定边界：下一动作越过已批准输入、`Worktrack Contract` 或 repo baseline
- 稳定交接：同一交接边界在连续无变化轮次中被再次确认

### stable-handback 定义

stable-handback 指同一交接边界（相同的 `last_stop_reason` 与 `last_handback_signature`）在连续 `handback_reaffirmed_rounds` 轮次中被再次确认。默认阈值 `stable_handback_threshold = 2`，即连续 2 轮无变化确认后触发 stable-handback。

### 交接锁激活语义

一旦 stable-handback 达成，运行时进入 `handoff_state = awaiting-handoff`，`handback_lock_active = true`，所有控制回路阶段进入阻断状态。

### unlock signal 定义

有效 unlock signal 必须满足以下至少之一（裸"重试"、"继续工作"或重复文字摘要无效）：
- 新目标或新 scope 声明
- 对阻塞原因的实质性分析或新信息
- 显式权限授予或策略变更
- 明确的新任务指令

### handback/re-entry 边界

下一轮启动时，Harness 必须从 `last_handback_signature` 恢复 handback 上下文。不得将 handback 误读为 fresh handoff。re-entry 时：
- 若 `handback_lock_active = true`，必须先验证 unlock signal 有效性，再决定是否解除交接锁
- 若 `handback_lock_active = false`，按 `handoff_state` 与 `continuation_authority` 决定是续跑还是等待
- 不得在 lock_active 状态下跳过交接锁验证直接进入新的 worktrack

## 七、Dispatch Contract

`Dispatch` 在专用 skill、通用 `SubAgent` 和 current-carrier fallback 之间保持同一份最小合同。

执行载体开关：

- 默认值为 `auto`
- `subagent_dispatch_mode`：`auto | delegated | current-carrier`
- `subagent_dispatch_mode_override_scope` 默认为 `worktrack-contract-primary`（`Worktrack Contract` 的 `runtime_dispatch_mode` 优先）
- 仅 `global-override` 时，`.aw/control-state.md` 的 `subagent_dispatch_mode` 压过 worktrack contract
- worktrack 未声明 `runtime_dispatch_mode` 时使用 control-state default

模式语义：

| 模式 | 语义 |
| --- | --- |
| `auto` | 按 Dispatch Decision Policy 选择 SubAgent、专用 skill、generic worker 或 current-carrier；无法安全委派时标记 fallback |
| `delegated` | 必须真实委派。无法委派时返回运行时缺口或权限阻塞 |
| `current-carrier` | 显式关闭 SubAgent 委派，由当前载体执行同一份 bounded contract |

最小 dispatch packet：

- work item id 与目标
- scope / non-goals / acceptance
- 允许读取的 artifact 和代码入口
- 禁止扩展的边界
- shared fact pack
- context budget
- 预期输出
- evidence 回传格式
- rollback / recovery hint

没有匹配专用 skill 时，`dispatch-skills` 可生成一次性任务指令并绑定通用执行载体。不得将此类指令写成新的 canonical skill。

## 八、Verify 与 Gate

`Verify` 收集证据，`Judge` 做放行裁决。二者独立。

最小证据面：

- implementation / review
- validation / test
- policy / governance
- artifact freshness

最小 verdict：

- `pass`
- `soft-fail`
- `hard-fail`
- `blocked`

Gate 输出至少包含：

- verdict
- route decision
- evidence 摘要
- unresolved risks
- required recovery 或 next route

## 九、Recover

Recover 只在 gate、状态估计或 authority boundary 阻断时触发。

合法恢复动作：

- `retry`
- `replan`
- `rollback`
- `split-worktrack`
- `refresh-baseline`
- `return RepoScope`
- `wait-for-approval`

恢复动作说明：

- 触发原因
- 保留的 artifact
- 废弃的 artifact
- 是否需要用户确认
- 回到哪个 Scope / Function

## 十、运行禁令

- 不恢复已退役的 `Task Contract`、`Route Card`、`Writeback Card` 或 adjacent-system 文档域。
- 不把 `Skill` 当作上位 ontology；`Skill` 是 `Function` 的实践实现。
- 不在普通 `Decide` 中修改 repo 目标。
- 不把 deploy target、`.agents/`、`.claude/` 或 `.aw/` 写成源码真相。
- 不把 current-carrier fallback 说成真实 SubAgent 委派。
- 不用 PR 创建替代 merge 后的 repo refresh。
- 不把未验证结论写回 truth layer。

## 十一、与当前仓库主线的关系

- `docs/harness/` 承接 Harness doctrine、protocol、artifact、scope、catalog 和 workflow family。
- `product/harness/` 承接 executable source。
- 已批准输入必须收束进 `Worktrack Contract` 与 `Plan / Task Queue`。
- 阅读路由由 `AGENTS.md` 承接，写回边界由项目维护治理承接；`docs/harness/adjacent-systems/` 已退役。
- `.aw/` 是 repo-local runtime control-plane state，不替代 `docs/`、`product/` 或 `toolchain/`。

## 十二、判断标准

协议清楚时，应同时满足：

- `RepoScope` 与 `WorktrackScope` 分开。
- 每个状态只允许有限合法算子。
- `Function -> Skill -> SubAgent/current-carrier` 的绑定边界明确。
- `subagent_dispatch_mode` 与 `runtime_dispatch_mode` 是可开关合同。
- `Evidence` 与 `Gate` 分开。
- Gate fail 有明确 recovery route。
- Closeout 以 repo refresh 结束。
