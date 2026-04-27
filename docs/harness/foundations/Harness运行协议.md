---
title: Harness 运行协议
status: draft
updated: 2026-04-25
owner: OceanEye
last_verified: 2026-04-25
---

# Harness 运行协议

> 目的：定义 `Harness` 在仓库演进中的控制协议本体，明确它作为**分层闭环控制系统**如何围绕 `Repo` 与 `Worktrack` 两层状态工作、消费哪些正式对象、调用哪些控制算子，以及如何在 `Codex` 环境里把这些算子实现为 `Skills` 与 workflow。

---

## 一、协议总定义

**Harness 是对 Repo 演进过程的分层闭环控制系统。**

它不是执行器本身，而是驱动 repo 演进闭环的控制协议。

最小职责：

- 在 `Repo` 层观察长期基线
- 在 `Worktrack` 层约束局部状态转移
- 通过 `Evidence + Gate` 判断当前状态是否允许继续推进
- 在失败、漂移或噪声出现时触发恢复动作
- 在 closeout 后把验证过的状态回写到 repo 级真相层

因此，`Harness 运行协议` 关注的不是"谁来写代码"，而是**"什么状态允许转移、由什么对象执行、凭什么证据放行"**。

---

## 二、控制系统架构

Harness 的运行基于一条完整的控制回路：

```
状态估计 → 选择算子 → 绑定技能 → 打包任务/信息 → 分派子代理 → 收集证据 → 裁决 → 状态更新
    ↑                                                                            ↓
    └──────────────────────────── 反馈环 ────────────────────────────────────────┘
```

每个阶段的控制语义：

| 阶段 | Function 算子 | 职责 |
|------|--------------|------|
| **状态估计** | `Observe` | 通过传感器读取当前系统状态，与参考信号对比 |
| **选择算子** | `Decide` | 基于状态估计结果，选择合法的状态转移算子 |
| **绑定技能** | `Bind` | 将算子映射到具体的 Skill 实现 |
| **打包任务** | `Package` | 为 SubAgent 准备受约束的任务与信息包 |
| **分派子代理** | `Dispatch` | 将任务交给执行载体，而不是 Harness 自己执行 |
| **收集证据** | `Verify` | 通过多维度传感器收集证据，证明"当前状态是什么" |
| **裁决** | `Judge` | 通过 Gate 判断"当前状态是否允许推进" |
| **状态更新** | `Update` | 更新 Control State，闭合控制回路 |

**关键约束**：单个 skill 的 `bounded round` 约束的是这次局部判断或局部执行包的边界，它**不自动等价于**"整个 Harness 本轮必须停机"。只要没有命中正式 stop condition，supervisor 应继续推进到下一个合法状态转移。

---

## 三、系统组件

### 3.1 控制器（Controller）

`Harness` 本体是控制器，负责：

- 选择下一合法动作（算子选择）
- 决定谁来执行（技能绑定 + 子代理分派）
- 决定需要什么证据（定义 Verify 维度）
- 判断当前状态能否推进（Gate 裁决）
- 在 fail / drift / blocked 时选择恢复路径

### 3.2 传感器（Sensor）

传感器负责把系统真实状态暴露给 `Harness`。

典型来源：

- git / diff / branch metadata
- repo scan
- test results
- code review results
- diff impact analysis
- 文档 freshness 检查

没有这些，state 只是"自报状态"。

### 3.3 执行器（Executor）

执行器负责实际改变系统状态，但它不等于 `Harness` 本体。

典型执行器：

- human developer
- coding agent（SubAgent）
- review agent（SubAgent）
- merge / rebase / archive 操作
- 文档更新动作

### 3.4 扰动源（Noise）

协议必须承认扰动存在，否则控制律会过于理想化。

典型扰动：

- 需求变化
- agent 幻觉
- 隐式依赖
- branch 漂移
- review 漏检
- 文档过时

### 3.5 恢复器（Recovery）

恢复器不是单独角色，而是一组在 gate fail 之后恢复控制的动作集合。

典型恢复动作：

- 回滚
- 重试
- 拆分 worktrack
- 降级目标
- 暂停并刷新 repo baseline

---

## 四、被控变量

Harness 控制的不是每一行代码，而是 **Repo 演进的偏差、风险、熵，以及状态转移的合法性**。

当前有 6 个被控变量：

| 被控变量 | 说明 |
|---|---|
| `目标偏差` | 当前 `Repo` / `Worktrack` 距离目标状态还有多远 |
| `范围漂移` | 实际改动是否越出了声明的 scope |
| `集成风险` | 当前改动是否破坏主线或引入不可接受问题 |
| `治理债务` | 文档、测试、结构、规则是否出现缺口 |
| `分支熵` | 活跃分支是否过多、过老、失去用途或偏离基线 |
| `证据完备度` | 当前 `review / test / rule-check` 是否足以支持放行 |

---

## 五、控制平面与执行平面

### 控制平面（Harness 本体）

负责：
- 决定下一步做什么（选择算子）
- 决定谁来执行（绑定技能 + 分派子代理）
- 决定需要哪些证据（定义 Verify 维度）
- 决定当前状态能否继续推进（Gate 裁决）
- 在失败时安排恢复动作（Recover）

### 执行平面（SubAgent / Human）

负责：
- 实际编码
- 实际 review
- 实际测试
- 实际合并、回滚、清理

因此，Harness 内部的动作应使用控制语义命名：
- `dispatch-subtask`（分派子任务）
- `execute-via-agent`（通过代理执行）

这样才不会把控制器和执行器粘在一起。

---

## 六、三轴模型

Harness 文档与控制逻辑应按 3 个正交维度组织：

### 6.1 Scope 轴

回答"在什么层上控制"：
- `RepoScope` —— 慢变量，长期基线
- `WorktrackScope` —— 快变量，局部状态转移

### 6.2 Function 轴

回答"控制器此刻在做什么"：
- `Observe` —— 状态估计
- `Decide` —— 选择算子
- `Init` —— 初始化局部状态
- `Dispatch` —— 分派执行
- `Verify` —— 收集证据
- `Judge` —— 裁决
- `Recover` —— 恢复控制
- `Close` —— 关闭并交接
- `Update` —— 状态更新（由 Supervisor 执行，不属于 Skill 层）

**约束**：`Function` 不是 skill 名字，而是状态转移算子。`Skill` 是这些算子在 `Codex` 里的相对稳定实现。`SubAgent` 是被 Harness 调度的执行载体。

`Update` 算子负责更新 Control State 以闭合控制回路。它不由 Skill 实现，而是由 Harness Supervisor 在执行裁决后执行。

### 6.3 Artifact 轴

回答"控制器依赖什么正式对象"：
- `Goal / Charter` —— 长期目标，并承载 `Engineering Node Map`
- `Snapshot / Status` —— 当前状态
- `Contract` —— 局部状态转移合同，并绑定 `Node Type`
- `Plan / Task Queue` —— 可执行子任务序列
- `Evidence` —— 状态转移证据
- `Cursor / Control State` —— 控制面当前模式
- `ChangeRequest` —— 目标变更请求
- `AppendRequest` —— 追加请求分类与路由

**关键约束**：`Control State` 只保存控制面状态，不承载业务真相。业务真相应分别保存在 `Repo` 与 `Worktrack` 的正式文档里。

---

## 七、系统覆盖层次

`Harness` 只覆盖两个控制层次：

### 7.1 Repo

`Repo` 是慢变量层，负责长期基线。

它关心：

- repo 目标
- repo 现状
- repo 活跃分支
- repo 治理状况
- 系统不变量
- 已知风险

### 7.2 Worktrack

`Worktrack` 是快变量层，负责局部状态转移。

它关心：

- 任务目标
- `Node Type`
  - `type`
  - `source_from_goal_charter`
  - `baseline_form`
  - `merge_required`
  - `gate_criteria`
  - `if_interrupted_strategy`
- 工作范围
- 验收条件
- 当前 branch 与 baseline 的差异
- 子任务序列
- 回滚、拆分、恢复路径

`Repo` 与 `Worktrack` 必须分开建模。`Repo` 提供长期参考信号，`Worktrack` 负责当前局部闭环；两者不能混成同一份"工作状态"。

---

## 八、协议交付物

`Harness` 运行协议至少依赖下面几类正式对象。

### 8.1 Repo Goal / Charter

负责定义 `Repo` 的长期目标和方向。

最小字段：

- 项目愿景
- 核心功能目标
- 技术栈与演进方向
- `Engineering Node Map`
  - `Node Type Registry`
  - `This Goal's Node Types`
  - `Node Dependency Graph`
  - `Default Baseline Policy`
- 成功标准
- 系统不变量

### 8.2 Repo Snapshot / Status

负责描述 `Repo` 当前状态，作为慢变量观测面。

最小字段：

- 主线现状
- 架构与模块地图
- 活跃分支及用途
- 治理状况
- 已知问题与风险

### 8.3 Worktrack Contract

负责定义单个 `Worktrack` 的局部状态转移合同。

最小字段：

- 任务目标
- 工作范围
- 非目标
- 影响模块
- 计划中的 next state
- 验收条件
- 约束条件
- 验证要求
- 回滚条件

### 8.4 Plan / Task Queue

负责把 `Worktrack Contract` 展开成可执行的子任务序列。

最小字段：

- 子任务列表
- 执行顺序
- 依赖关系
- 当前阻塞
- 当前下一动作
- 当前下一动作的稳定标识
- 当前 round 的 dispatch handoff packet
- 验收条件与任务队列的对齐关系

### 8.5 Gate Evidence

负责为状态转移裁决提供证据，而不是只记录口头结论。

最小字段：

- review / validation / policy 三类证据面
- 每条证据面的 freshness 或缺失状态
- 每条证据面的残余风险与上游约束信号
- 是否已经满足 gate intake
- gate verdict 与 route decision
- 为什么通过或不通过
- 后续动作

### 8.6 Harness Control State

负责保存控制面当前所处模式，而不是保存业务真相。

最小字段：

- 当前控制级别
- 当前活跃 worktrack
- 当前 baseline branch
- 当前需要执行的下一动作
- 关联正式文档路径

### 8.7 Goal Change Request

负责管理目标本身的变更，而不是把目标变更混入常规控制。

最小字段：

- 变更理由
- 影响分析
- 对现有 worktrack 的影响
- 是否需要重建 baseline
- 单独 gate 结论

### 8.8 Append Request

负责管理外部追加请求的分类与路由，而不是直接执行追加内容。

支持两个 mode：

- `append-feature`
- `append-design`

最小分类结果：

- `goal change` —— 追加请求会改变 repo 长期参考信号，必须进入目标变更控制
- `new worktrack` —— 追加请求在当前目标内，但应独立初始化新的 worktrack
- `scope expansion` —— 追加请求试图扩大当前活跃 worktrack，必须显式审批
- `design-only` —— 追加请求只要求设计判断或设计产物
- `design-then-implementation` —— 追加请求要求先设计、设计 gate 通过后再实现

关键约束：

- `Append Request` 只表达分类与路由，不授权执行。
- `Append Request` 不替代 `Goal Change Request` 或 `Worktrack Contract`。
- `goal change` 与 `scope expansion` 分类必须暴露 programmer authority boundary。

---

## 九、状态与作用域

### 9.1 RepoScope 状态

`RepoScope` 是对长期基线的控制模式。

最小状态：

- `observing`
- `deciding`
- `change-control`
- `ready-for-worktrack`

### 9.2 WorktrackScope 状态

`WorktrackScope` 是对局部状态转移的控制模式。

最小状态：

- `initializing` —— 对应 Init 算子
- `observing` —— 对应 Observe 算子
- `scheduling` —— 对应 Decide 算子
- `dispatching` —— 对应 Dispatch 算子
- `verifying` —— 对应 Verify 算子
- `judging` —— 对应 Judge 算子
- `recovering` —— 对应 Recover 算子
- `closing` —— 对应 Close 算子
- `blocked` —— 非算子状态，Gate verdict 的投影
- `closed` —— 吸收状态，进入后自动转移回 RepoScope

### 9.3 最小状态闭环

```
RepoScope.Observe ──→ RepoScope.Decide ──→ WorktrackScope.Init
                                                          ↓
                                               WorktrackScope.Observe
                                                          ↓
                                               WorktrackScope.Decide
                                                          ↓
                                               WorktrackScope.Dispatch
                                                          ↓
                                               WorktrackScope.Verify
                                                          ↓
                                               WorktrackScope.Judge
                                                          ↓
                                          ┌───────────────┼───────────────┐
                                          ↓               ↓               ↓
                                        通过            失败/阻塞        恢复
                                          ↓               ↓               ↓
                                      Worktrack       Worktrack      Worktrack
                                       .Close          .Recover       .Recover
                                          ↓               ↓               ↓
                                   RepoScope.Refresh  回到 Observe/ 回到 RepoScope
                                                        Decide       或等待审批
                                          ↓
                                   RepoScope.Observe ──→ [循环]
```

完整闭环步骤：

1. 在 `RepoScope.observing` 下观测当前 repo 状态
2. 在 `RepoScope.deciding` 下确认下一步是切入 worktrack 还是进入 change control
3. 在 `WorktrackScope.initializing` 下建立 branch、baseline、contract 与初始 plan
4. 在 `WorktrackScope.observing` 下读取当前 worktrack 状态（worktrack-status-skill）
5. 在 `WorktrackScope.scheduling` 下选择下一步动作（schedule-worktrack-skill）
6. 在 `WorktrackScope.dispatching` 下分派执行（dispatch-skills）
7. 在 `WorktrackScope.verifying` 下收集 `review / test / rule-check` 证据
8. 在 `WorktrackScope.judging` 下形成 gate verdict
9. fail 则进入 `recovering`，pass 则进入 `closing`
10. 关闭 worktrack 后返回 `RepoScope.observing` **刷新 repo 状态**

**关键约束**：`PR` 不是闭环终点。完整的 closeout 是 `merge → refresh repo snapshot → cleanup → return RepoScope`。只有这样，Repo 的慢变量才会被真实更新，而不是停留在"PR 已发出"的半闭环状态。

---

## 十、连续推进与停止条件

`Harness` 的默认语义应当是连续推进，而不是每完成一个局部 skill round 就自动把控制权交还给 programmer。

也就是说：

- 单个 skill 的 `bounded round` 约束的是这次局部判断或局部执行包的边界
- 它不自动等价于"整个 Harness 本轮必须停机"
- 只要没有命中正式 stop condition，supervisor 应继续推进到下一个合法状态转移

### 10.1 最小 stop conditions

- 需要 programmer 明确批准的 goal change、scope expansion、destructive action 或其他 authority boundary
- 必需 artifact 或 evidence 缺失、过时、冲突，导致当前状态估计不再可靠
- `Gate` 给出 `soft-fail`、`hard-fail` 或 `blocked`
- 当前 host runtime 缺少合法的 execution carrier / dispatch shell，无法按受约束的 task/info 包继续执行
- 下一动作会把系统推出已批准的 `Task Contract`、`Worktrack Contract` 或 repo baseline
- 同一个交接边界在连续无变化轮次中再次被确认（稳定交接）

### 10.2 补充约束

- 不得把"skill 已经返回结构化结果"本身当作 stop condition
- 不得把"没有专门 skill"本身当作 stop condition；命中这种情况时应优先转入 fallback execution carrier
- 如果 stop 的根因只是 runtime dispatch shell 缺位，必须显式报告为 runtime gap，而不是伪装成已完成的 subagent 执行

### 10.3 结构化交接字段

为了让 bounded rounds 可以被 supervisor 连续拼接，scope skills 在 handoff 时应优先显式给出：

- `allowed_next_routes`
- `recommended_next_route`
- `continuation_ready`
- `continuation_blockers`
- `approval_required`
- `approval_scope`
- `approval_reason`

在兼容迁移期内，runtime 或 backend 仍可镜像旧字段，例如 `recommended_next_action`、`needs_programmer_approval`、`approval_to_apply`；但这些旧字段应被视为兼容投影，而不是新的 authority source。

---

## 十一、Function 与 Skill 的关系

`Function` 是协议层的控制算子，`Skill` 是这些算子在 `Codex` 环境中的可执行实现。

也就是说：

- `Function` 回答"控制器此刻在做什么"
- `Skill` 回答"在 `Codex` 里这一轮实际调用什么能力"

在当前项目的 `Codex` 语境里，不应为了文档整洁再额外引入一层脱离运行时的 `Function -> Skill` 转译目录。对实际 product 生成更重要的是：

- supervisor 当前会选什么 skills
- 当前 work item 会如何被 dispatch
- 没有专门 skill 时 fallback 到什么执行体

### 11.1 四层映射

在 `Codex / Claude` 里更完整的实践映射应当是：

| 层级 | 本体 | 说明 |
|------|------|------|
| `Function` | 状态转移算子 | 回答"控制器此刻在做什么" |
| `Skill` | 算子实现 | 回答"在 Codex 里这一轮实际调用什么能力" |
| `Harness Dispatch` | 技能绑定 + 任务打包 | 选择合适的 skill binding，向执行载体提供受约束的 task 和 info |
| `SubAgent` | 执行载体 | 实际承接这次执行的运行时载体 |

补充约束：

- `Skill` 不是严格数学意义上的状态转移函数
- 它更接近"受约束的近似转移器"
- 正因为 skill 和 subagent 的行为不是完全确定的，所以一次转移是否成立，仍然必须通过 `Evidence + Gate` 来判定

### 11.2 Worktrack dispatch fallback

`WorktrackScope` 下允许存在一个 `dispatch-skills` 类能力，用来为当前任务选择下游执行方式。

它必须遵守下面的 fallback 规则：

- 如果存在合适的专门 skill，优先使用该专门 skill
- 如果不存在合适的专门 skill，不得因此让系统停摆
- 此时必须自动 fallback 到一个通用任务完成执行载体
- fallback 仍然必须保持 bounded task、最小信息包和 evidence 回传

也就是说，系统不应把"没有专门 skill"解释成"不能继续执行"；它只意味着本轮应退化到通用任务完成执行体。

在当前 canonical worktrack chain 中，`schedule-worktrack-skill` 应当是 `current next action` 与 dispatch handoff packet 的唯一 authority。`init-worktrack-skill` 只负责种下 queue 和 schedule-facing handoff，`dispatch-skills` 只负责消费 schedule 已确认的 packet，而不是重新生成它。

### 11.3 Dispatch Contract

无论命中专门 skill 还是 fallback 到通用执行载体，`dispatch-skills` 都必须保持同一套最小 dispatch contract：

- `Dispatch Task Brief`
  - `task`
  - `goal`
  - `in_scope`
  - `out_of_scope`
  - `constraints`
  - `acceptance_criteria_for_this_round`
  - `verification_requirements`
  - `done_signal`
- `Dispatch Info Packet`
  - `current_worktrack_state`
  - `acceptance_alignment_used`
  - `relevant_artifacts`
  - `required_context`
  - `known_risks`
  - `executor_candidates`
  - `fallback_reason`
- `Dispatch Result`
  - `selected_executor`
  - `runtime_dispatch_mode`
  - `dispatch_packet_status`
  - `dispatch_contract_gaps`
  - `actions_taken`
  - `files_touched_or_expected`
  - `evidence_collected`
  - `open_issues`
  - `recommended_next_action`

补充约束：

- `Dispatch Task Brief` 是面向当前 round 的 bounded execution contract，不替代上游 `Task Contract`
- `Dispatch Task Brief` 与 `Dispatch Info Packet` 必须保留当前任务对应的 acceptance boundary，而不是让执行载体自行猜测本轮在覆盖哪些验收条件
- 当前 round 的 `Dispatch Task Brief` 与 `Dispatch Info Packet` 应优先由 `schedule-worktrack-skill` 产出并由 `dispatch-skills` 消费；若 packet 缺失，应返回 scheduling，而不是让 dispatch 侧重建权威合同
- `Dispatch Info Packet` 只允许携带本轮必需上下文，不应退化成"把整个 repo 扔给 subagent"
- fallback 到通用执行载体时，输入输出结构不得放宽；变化的只是执行载体，不是控制边界
- `runtime_dispatch_mode` 必须显式区分"delegated subagent dispatch"和"current-carrier runtime fallback"

### 11.4 实践操作链

在 `Codex / Claude` 里，一个最小可执行链应当是：

`state estimate -> choose operator -> bind skill(s) -> package task/info -> dispatch subagent -> collect evidence -> adjudicate -> update state`

这里每一环的职责是：

- `state estimate`：通过传感器形成当前状态估计，而不是只接受自报状态
- `choose operator`：在当前 `Scope + State + Authority` 下选择合法转移算子
- `bind skill(s)`：把该算子映射到相对稳定的 skills
- `package task/info`：给 subagent 明确边界、目标、非目标、验证要求和必需上下文
- `dispatch subagent`：把这次局部执行交给运行时载体
- `collect evidence`：收集 review / test / rule-check / trace / diff 等证据
- `adjudicate`：形成 gate verdict
- `update state`：只有在证据支持下，才更新 repo/worktrack/control state

如果当前 host runtime 支持真实 subagent dispatch shell，且权限边界允许委派，则默认必须走 `dispatch subagent`。只有在 host runtime 没有稳定分派壳层、权限边界禁止委派，或当前 dispatch package 不满足安全分派条件时，才允许暂时退化为：

- `runtime_dispatch_mode` 可被显式配置，优先级如下：
  - `.aw/control-state.md` 的 `subagent_dispatch_mode` 显式覆盖（`auto` / `delegated` / `current-carrier`）
  - `current worktrack contract` 的 `runtime_dispatch_mode`（`auto` / `delegated` / `current-carrier`）
  - 默认策略：`auto`

- `auto` 语义：
  - 优先尝试 delegated subagent dispatch；
  - 当检测到 `permission blocked` 或 `dispatch package unsafe` 时，自动降级为 current-carrier；
  - 每次降级必须在 dispatch 结果中写明 runtime fallback 原因。

此时才允许暂时退化为：

`state estimate -> choose operator -> bind skill(s) -> package task/info -> execute in current carrier -> collect evidence -> adjudicate -> update state`

但此时必须显式标注：

- 当前是 runtime fallback，而不是完整 `subagent dispatch`
- 没有使用 SubAgent 的明确阻断原因，例如 `runtime fallback`、`permission blocked` 或 `dispatch package unsafe`
- 不得在报告里把"当前 carrier 内执行"写成"已经成功派发独立 subagent"

---

## 十二、Scope 下的最小控制算子

### 12.1 RepoScope 算子

#### Observe

- `status`
- `structure`
- `status-detail`

#### Decide

- `whats-next`
- `verify-next`
- `go-next`

#### RouteAppend（追加请求路由）

- `append-request`（由外部 append-feature / append-design 请求触发）

`RouteAppend` 是执行前的 intake / route 操作。它不属于实现执行，不创建 worktrack，不改写目标，也不扩展当前 worktrack；它只把追加请求分类为 `goal change`、`new worktrack`、`scope expansion`、`design-only` 或 `design-then-implementation`，再返回显式下一路由与审批边界。

#### ChangeGoal（参考信号设定）

- `change-goal`（由外部目标变更请求触发）

`ChangeGoal` 不是常规控制回路中的 `Function` 算子，而是循环外的参考信号重设操作。它和 `SetGoal` 同属参考信号设定层，设定/重设完成后才启动（或重新启动）常规循环。

#### Close

- `refresh-repo-state`

### 12.2 WorktrackScope 算子

#### Init

- `init-worktrack`

#### Observe

- `status` —— 读取 Worktrack 当前状态形成结构化状态估计
- `status-detail` —— 深入读取形成详细状态估计

> 由 `worktrack-status-skill` 实现

#### Decide

- `schedule` —— 由 `schedule-worktrack-skill` 实现

> 消费 `worktrack-status-skill` 产出的状态估计结果

#### Dispatch

- `dispatch-subtask`
- `execute-via-agent`

#### Verify

- `review`
- `test`
- `rule-check`

#### Judge

- `gate`

#### Recover

由 `recover-worktrack-skill` 实现：

- `retry` —— 在相同目标与基准下重试当前路径
- `rollback` —— 回滚到安全状态
- `split-worktrack` —— 拆分为更小的 Worktrack
- `refresh-baseline` —— 刷新分支基准
- `replan` —— 当前路径整体不可行，需回到 RepoScope 重新 Decide（跨 Scope 转移）

#### Close

`Close` 算子包含以下子阶段，由 `close-worktrack-skill` 统一实现：

- `pr` —— 准备并发起合并请求
- `merge` —— 执行合并（需审批边界）
- `cleanup-branch` —— 清理已合并分支
- `close-worktrack` —— 正式关闭 Worktrack 并生成 repo refresh 交接

---

## 十三、Gate 协议

`Gate` 不应只等于"拼接 review 和 test 结果"，而应对**正交检查面**的裁决做统一汇总。

Harness 不能只有 `Gate`，必须同时有 `Evidence`。

- `Evidence` 负责证明"当前状态是什么"
- `Gate` 负责判断"当前状态是否允许推进"

二者必须分开。

### 13.1 最小判定面

| 校验面 | 判定内容 | 对应 Verify 算子 |
|--------|---------|----------------|
| `implementation-gate` | 代码正确性、结构合理性 | `review` |
| `validation-gate` | 测试、验收条件、运行结果 | `test` |
| `policy-gate` | 规则、边界、不变量、治理要求 | `rule-check` |

最后由汇总 `gate` 生成最终 verdict。

### 13.2 最小 verdict

- `pass`
- `soft-fail`
- `hard-fail`
- `blocked`

补充约束：

- `pass` 不等于"没有瑕疵"，而是"残余风险可接受"
- `soft-fail` 允许在当前 worktrack 内补证或返工
- `hard-fail` 意味着当前方案或路径需要结构性调整
- `blocked` 禁止继续猜测或强推

---

## 十四、恢复策略

当 Gate 裁决为失败或阻塞时，Harness 必须进入恢复模式。合法恢复算子：

| 恢复算子 | 适用条件 | 限制 |
|---------|---------|------|
| `重试` | 当前目标、排除目标与基准仍然有效 | 不得扩大范围或重定义验收 |
| `回滚` | 当前状态已不可安全继续 | 除非程序员明确批准，否则执行破坏性变更前必须停止 |
| `拆分 Worktrack` | 当前范围过宽或包含多个独立验收切片 | 不得静默创建新 Worktrack；必须明确验收标准分配 |
| `刷新基准` | 上游真相变化使当前分支比较失效 | 不得改写 Repo Snapshot/Status 或目标/章程 |
| `重新规划` | 当前路径整体不可行 | 必须回到 RepoScope 重新 Decide |

---

## 十五、运行禁令

下面这些都不应被视为合法运行：

- 把 `Harness` 当成直接执行编码的主体
- 在常规控制流程里直接改写目标
- 跳过 `verify / judge` 直接进入 `PR` 或 `merge`
- 把 `PR` 当成闭环终点
- 把 runtime state 回写到 canonical product source
- 把 `Task Contract` 改写成 `Harness` 自己的 truth
- 把 `Control State` 当成业务真相的容器
- 跳过 Evidence 直接做 Gate 裁决
- 把三个正交校验面压缩成一个笼统判定

---

## 十六、与当前仓库主线的关系

在当前仓库里，这份协议应与现有主线保持兼容：

- `Task Contract` 仍然是 `discussion -> execution` 之间的正式执行基线
- `Harness` 可以消费 `Task Contract`，但不能改写它的 truth 边界
- `docs/harness/` 当前承接 Harness doctrine、workflow family 与运行协议真相层
- `product/harness/` 是当前仓库中的 Harness executable root，但当前阶段只建立最小骨架
- `memory-side` 与 `task-interface` 当前只保留 adjacent-system 合同层，不再在本仓库维持独立 `product/` skill roots
- 当前仓库中的具体 executable source 只保留在 `product/harness/`
- repo-local runtime state 应继续留在 repo-local state layer

---

## 十七、判断标准

如果下面几句话能成立，说明这份 `Harness 运行协议` 是清楚的：

- 它把 `Repo` 与 `Worktrack` 分成了两个时间尺度不同的控制层
- 它把 `Scope`、`Function`、`Artifact` 三个维度分开了
- 它把 `Function` 与 `Skill` 区分开了
- 它补上了 `Harness Dispatch` 与 `SubAgent` 这层实践操作链
- 它把 `Function` 理解为状态转移算子，而不是平面动作名词
- 它把 `Evidence` 与 `Gate` 同时立起来了
- 它把 `PR` 之后的闭环补完整了
- 它没有把 `Harness` 和执行器粘在一起
- 它显式定义了被控变量、扰动源和恢复策略

---

## 十八、外部证据摘要

外部证据支持这份协议的主要方向：

- 工业界越来越把 `Harness` 视为模型外部的 orchestration / eval / governance / environment layer
- 学术界越来越强调 verifier、retrieval、trace、versioned snapshots 与 long-horizon loop
- 控制论视角更支持把 `Harness` 写成 `hierarchical supervisory controller`
- 多 `SubAgent` 是容量扩展和并行探索手段，但不是 ontology 本体

这些证据共同支持下面的整合结论：

- `Harness` 不能脱离 `Skills` 这种相对稳定的转移实现而存在
- 但 `Harness` 也不能退化成 `Skills` 本身
- 因此，runtime 层必须显式补上 `operator -> skill binding -> subagent dispatch` 这条最后一环

---

## 十九、代表性外部来源

工业界与研究界中，最能直接支撑本协议判断的来源包括：

- OpenAI, `Harness engineering: leveraging Codex in an agent-first world`
  - <https://openai.com/index/harness-engineering/>
- OpenAI, `Unrolling the Codex agent loop`
  - <https://openai.com/index/unrolling-the-codex-agent-loop/>
- Anthropic, `Demystifying evals for AI agents`
  - <https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents>
- Anthropic, `Trustworthy agents in practice`
  - <https://www.anthropic.com/research/trustworthy-agents>
- Anthropic, `Scaling Managed Agents: Decoupling the brain from the hands`
  - <https://www.anthropic.com/engineering/managed-agents>
- ContextBench
  - <https://arxiv.org/abs/2602.05892>
- TDFlow
  - <https://aclanthology.org/2026.eacl-long.70.pdf>
- SWE-EVO
  - <https://arxiv.org/abs/2512.18470>
