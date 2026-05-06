---
title: Harness 运行协议
status: draft
updated: 2026-05-05
owner: OceanEye
last_verified: 2026-05-05
---

# Harness 运行协议

> 目的：固定 Harness 如何从状态估计推进到执行、验证、裁决和状态更新。Doctrine 边界见 [Harness指导思想.md](./Harness指导思想.md)；正式对象字段见 [artifact/](../artifact/README.md)。

## 一、协议总定义

Harness 是 repo 演进的分层闭环控制协议，不直接替代执行器，而是决定当前 Scope、合法 Function 算子、需消费的 Artifact、绑定 Skill/执行载体、需要的 Evidence、Gate 是否允许推进、以及失败/阻塞的恢复路径。

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

单个 skill 的 bounded round 只限制本轮局部动作，不自动等价于 Harness 停机；只要没有命中正式 stop condition，supervisor 应继续推进到下一个合法状态转移。

## 二、控制平面与执行平面

Harness 本体属于控制平面，负责选择合法算子、绑定 skill/执行载体、打包任务与信息、定义证据面、裁决推进、安排恢复/收尾；执行平面负责实际改变 repo（编码、review、test、文档更新、merge/cleanup/rollback）。Harness 应优先 dispatch 给独立 SubAgent、human executor 或通用执行载体；只有缺乏稳定分派壳层、权限边界阻断或任务包不满足安全分派条件时才允许当前载体回退，但回退必须写成 runtime fallback、permission blocked 或 dispatch package unsafe，不能声称已真实委派 SubAgent。

## 三、Scope 与状态

### RepoScope

`RepoScope` 管 repo 长期参考信号与慢变量。最小状态：observing、deciding、change-control、ready-for-worktrack。

合法算子：

| 算子 | 作用 |
| --- | --- |
| `Observe` | 读取 repo goal、snapshot、branch、治理和已知风险 |
| `Decide` | 判断下一步是开 worktrack、处理 append request、刷新状态，还是进入目标变更 |
| `RouteAppend` | 对 `append-feature` / `append-design` 做分类与路由，不直接授权执行 |
| `ChangeGoal` | 处理外部目标变更请求；常规 `Decide` 不得主动移动目标 |
| `Close / Refresh` | worktrack closeout 后刷新 repo snapshot |

### WorktrackScope

`WorktrackScope` 管当前局部状态转移。最小状态：initializing、observing、scheduling、dispatching、verifying、judging、recovering、closing、blocked、closed。

合法算子：

| 算子 | 作用 |
| --- | --- |
| `Init` | 建立 branch、baseline、contract 与初始 plan |
| `Observe` | 读取当前 worktrack artifact、diff、测试和阻塞 |
| `Decide` | 从 task queue 选择当前下一动作 |
| `Dispatch` | 选择专用 skill、通用 `SubAgent` 或显式 current-carrier fallback |
| `Verify` | 收集 review / test / rule-check 等证据 |
| `Judge` | 汇总证据形成 gate verdict |
| `Recover` | 在 fail / blocked / drift 后选择恢复动作 |
| `Close` | PR / merge / cleanup / handoff，并交给 RepoScope refresh |

## 四、最小闭环

```text
RepoScope.Observe
-> RepoScope.Decide
-> WorktrackScope.Init
-> WorktrackScope.Observe
-> WorktrackScope.Decide
-> WorktrackScope.Dispatch
-> WorktrackScope.Verify
-> WorktrackScope.Judge
-> WorktrackScope.Close 或 WorktrackScope.Recover
-> RepoScope.Refresh
-> RepoScope.Observe
```

`PR` 不是闭环终点。完整 closeout 是：

```text
merge -> refresh repo snapshot -> cleanup -> return RepoScope
```

只有回到 `RepoScope.Observe` 并刷新慢变量，repo 状态才算被真实更新。

## 五、正式对象

本协议只列对象职责（字段细节由对应 artifact 文档承接）：

| 对象 | 承接位 |
| --- | --- |
| `Repo Goal / Charter` | [goal-charter.md](../artifact/repo/goal-charter.md) |
| `Repo Snapshot / Status` | [snapshot-status.md](../artifact/repo/snapshot-status.md) |
| `Worktrack Contract` | [contract.md](../artifact/worktrack/contract.md) |
| `Plan / Task Queue` | [plan-task-queue.md](../artifact/worktrack/plan-task-queue.md) |
| `Gate Evidence` | [gate-evidence.md](../artifact/worktrack/gate-evidence.md) |
| `Harness Control State` | [control-state.md](../artifact/control/control-state.md) |
| `Goal Change Request` | [goal-change-request.md](../artifact/control/goal-change-request.md) |
| `Append Request` | [append-request.md](../artifact/control/append-request.md) |

`Control State` 只保存控制面状态，不承载业务真相。业务真相分别写回 repo / worktrack 正式文档和对应源码层。

## 六、连续推进与停止条件

默认语义是连续推进，不因 skill round 完成就自动交还控制权。

最小 stop conditions：需要 programmer 批准的 goal change/scope expansion/destructive action/authority boundary；必需 artifact/evidence 缺失、过时或冲突；Gate 给出 soft-fail/hard-fail/blocked；host runtime 无合法 execution carrier/dispatch shell；下一动作会越过已批准输入、Worktrack Contract 或 repo baseline；同一交接边界在连续无变化轮次中再次被确认。

补充约束：”skill 已返回结构化结果”不是 stop condition；”没有专门 skill”不是 stop condition，应进入 fallback execution carrier；runtime dispatch shell 缺位必须报告为 runtime gap，不能伪装成已完成 SubAgent 委派。

bounded round handoff 应优先给出：allowed_next_routes、recommended_next_route、continuation_ready、continuation_blockers、approval_required、approval_scope、approval_reason。

## 七、Dispatch Contract

`Dispatch` 必须在专用 skill、通用 SubAgent 和 current-carrier fallback 之间保持同一份最小合同。执行载体开关默认值为 auto，subagent_dispatch_mode 支持 auto/delegated/current-carrier，subagent_dispatch_mode_override_scope 默认 worktrack-contract-primary；只有显式 global-override 时 control-state 的 subagent_dispatch_mode 才压过 worktrack contract。

| 模式 | 语义 |
| --- | --- |
| `auto` | 宿主支持真实 SubAgent 且权限边界允许时默认委派；否则显式 `runtime fallback` |
| `delegated` | 必须真实委派；无法委派时返回运行时缺口或权限阻塞 |
| `current-carrier` | 显式关闭 SubAgent 委派，由当前载体执行同一份 bounded task/info contract |

最小 dispatch packet 包含当前 work item id 与目标、scope/non-goals/acceptance、允许读取的 artifact 和代码入口、禁止扩展的边界、预期输出、evidence 回传格式、rollback/recovery hint。没有匹配专用 skill 时 dispatch-skills 可生成一次性任务指令并绑定通用执行载体，但不得写成新的 canonical skill。

## 八、Verify 与 Gate

Verify 收集证据，Judge 做放行裁决，二者不能混成一层。最小证据面：implementation/review、validation/test、policy/governance、artifact freshness。最小 verdict：pass、soft-fail、hard-fail、blocked。Gate 输出至少包含 verdict、route decision、evidence 摘要、unresolved risks、required recovery 或 next route。

## 九、Recover

Recover 只处理已经被 gate、状态估计或 authority boundary 证明不能继续直推的情况。

合法恢复动作：

- `retry`
- `replan`
- `rollback`
- `split-worktrack`
- `refresh-baseline`
- `return RepoScope`
- `wait-for-approval`

恢复动作必须说明：

- 触发原因
- 保留哪些 artifact
- 废弃哪些 artifact
- 是否需要用户确认
- 回到哪个 Scope / Function

## 十、运行禁令

不恢复已退役的 Task Contract、Route Card、Writeback Card 或 adjacent-system 文档域；不把 Skill 当作上位 ontology（Skill 只是 Function 的实践实现）；不在普通 Decide 中修改 repo 目标；不把 deploy target、.agents/、.claude/ 或 .aw/ 写成源码真相；不把 current-carrier fallback 说成真实 SubAgent 委派；不用 PR 创建替代 merge 后的 repo refresh；不把未验证结论写回长期 truth layer。

## 十一、与当前仓库主线的关系

docs/harness/ 承接 Harness doctrine、protocol、artifact、scope、catalog 和 workflow family；product/harness/ 承接 executable source；已批准输入必须收束进 Worktrack Contract 与 Plan/Task Queue；阅读路由由 AGENTS.md 承接，写回边界由项目维护治理承接，adjacent-systems/ 已退役；.aw/ 是 repo-local runtime control-plane state，不替代 docs/、product/、toolchain/。

## 十二、判断标准

协议清楚时应同时满足：RepoScope 与 WorktrackScope 分开；每个状态只允许有限合法算子；Function -> Skill -> SubAgent/current-carrier 绑定边界明确；subagent_dispatch_mode 与 runtime_dispatch_mode 是可开关合同；Evidence 与 Gate 分开；Gate fail 有明确 recovery route；closeout 以 repo refresh 结束而非 PR 创建。
