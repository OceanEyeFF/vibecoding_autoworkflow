---
name: harness-skill
description: 当需要运行 Harness 分层闭环控制系统时，使用这个技能。它是 Codex 中顶层监督控制器的入口，负责状态估计、算子选择、技能绑定、子代理分派、证据收集、裁决与状态更新，而不是直接执行编码。
---

# Harness 技能

## 一、本体定位

**Harness 是对 Repo 演进过程的分层闭环控制系统。**

它在 `Repo` 级维护长期基线与系统不变量，在 `Worktrack` 级约束局部状态转移，并通过 `Evidence + Gate` 决定状态是否允许推进为新的基线。

Harness 关注的不是"把任务做完"本身，而是：

- 给系统输入
- 观察系统输出
- 和目标状态对比
- 判断当前状态是否允许继续推进
- 在失败时阻断、恢复、重试、回滚或重新规划

### 它不是什么

- 不是直接执行编码的主体
- 不是 `Task Contract` 的上游真相层
- 不是某个 backend 的 repo-local runtime wrapper
- 不是把一组 skill 顺序串起来的 open-loop 流程图
- 不是可以在常规控制里随意改写目标的任务管理器

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

**关键约束**：下游技能的轮次是本地控制步骤，不是隐式停止信号。Harness 应消费下游结构化输出持续推进，直到真正命中正式停止条件。

---

## 三、系统组件

Harness 作为控制系统，包含以下系统组件：

### 3.1 传感器（Sensor）

**定义**：Harness 通过什么知道状态是真的？

**示例**：
- git / diff / branch metadata
- test results
- code review results
- diff impact analysis
- 文档 freshness 检查
- `Harness Control State` 中的控制面信号

没有这些，state 只是"自报状态"。

### 3.2 执行器（Executor）

**定义**：什么对象实际改变系统状态？

**示例**：
- human developer
- coding agent（SubAgent）
- review agent（SubAgent）
- merge / rebase / archive 操作
- 文档更新动作

执行器是被 Harness 调度的对象，不等于 Harness 本体。

### 3.3 扰动源（Noise）

**定义**：什么会让系统偏离？

**示例**：
- 需求变化
- agent 幻觉
- 隐式依赖
- branch 漂移
- review 漏检
- 文档过时

扰动必须显式写出来，否则控制律会过于理想化。

### 3.4 恢复策略（Recovery）

**定义**：gate fail 之后如何恢复控制？

**示例**：
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
- `ChangeControl` —— 目标变更控制
- `SetGoal` —— 初始化参考信号

**约束**：`Function` 不是 skill 名字，而是状态转移算子。`Skill` 是这些算子在 `Codex / Claude` 里的相对稳定实现。`SubAgent` 是被 Harness 调度的执行载体。

### 6.3 Artifact 轴

回答"控制器依赖什么正式对象"：
- `Goal / Charter` —— 长期目标
- `Snapshot / Status` —— 当前状态
- `Contract` —— 局部状态转移合同
- `Plan / Task Queue` —— 可执行子任务序列
- `Evidence` —— 状态转移证据
- `Cursor / Control State` —— 控制面当前模式
- `ChangeRequest` —— 目标变更请求

**关键约束**：`Control State` 只保存控制面状态，不承载业务真相。业务真相应分别保存在 `Repo` 与 `Worktrack` 的正式文档里。

---

## 七、两层控制律

### 7.1 RepoScope 控制律

`RepoScope` 是对长期基线的控制模式。

```
SetGoal (set-harness-goal-skill) ──→ 仅在 .aw/ 未初始化时运行 ──→ Observe
    ↓
Observe (repo-status-skill)
    ↓
Decide (repo-whats-next-skill)
    ↓
    ├─→ ChangeControl (goal-change-control-skill) ─→ [等待审批] ─→ 回到 Observe
    ├─→ 保持并观察 ───────────────────────────────→ 回到 Observe
    └─→ 进入 WorktrackScope ──────────────────────→ Init
```

**控制目标**：维护 Repo 的长期基线稳定，判断是否需要进入局部执行。

### 7.2 WorktrackScope 控制律

`WorktrackScope` 是对局部状态转移的控制模式。

```
Init (init-worktrack-skill)
    ↓
Observe (worktrack-status-skill)
    ↓
Decide (schedule-worktrack-skill)
    ↓
Dispatch (dispatch-skills)
    ↓
Verify (review-evidence-skill + test-evidence-skill + rule-check-skill)
    ↓
Judge (gate-skill)
    ↓
    ├─→ 通过 ──→ Close (close-worktrack-skill) ──→ RepoScope Refresh (repo-refresh-skill)
    ├─→ 软失败 ─→ Recover (recover-worktrack-skill) ─→ 回到 Observe/Decide
    ├─→ 硬失败 ─→ Recover (recover-worktrack-skill) ─→ 回到 Observe/Decide 或回到 RepoScope
    └─→ 阻塞 ───→ Recover (recover-worktrack-skill) ─→ 回到 Observe/Decide 或等待审批
```

**控制目标**：在已批准的局部范围内安全地执行状态转移，收集证据，通过 Gate 裁决，最终回归 RepoScope。

### 7.3 完整状态闭环

```
RepoScope.SetGoal ──→ RepoScope.Observe ──→ RepoScope.Decide ──→ WorktrackScope.Init
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

**关键约束**：`PR` 不是闭环终点。完整的 closeout 是 `merge → refresh repo snapshot → cleanup → return RepoScope`。只有这样，Repo 的慢变量才会被真实更新，而不是停留在"PR 已发出"的半闭环状态。

---

## 八、Gate 的三轴裁决模型

Harness 不能只有 `Gate`，必须同时有 `Evidence`。

- `Evidence` 负责证明"当前状态是什么"
- `Gate` 负责判断"当前状态是否允许推进"

二者必须分开。

Gate 应汇总**正交校验面**的裁决：

| 校验面 | 判定内容 | 对应 Verify 技能 |
|--------|---------|----------------|
| `implementation-gate` | 代码正确性、结构合理性 | review-evidence-skill |
| `validation-gate` | 测试、验收条件、运行结果 | test-evidence-skill |
| `policy-gate` | 规则、边界、不变量、治理要求 | rule-check-skill |

最后由汇总 `gate-skill` 生成最终 verdict。

---

## 九、何时使用

当任务不是"写代码"，而是"运行当前的 Harness 控制回路"时，使用这个技能：

- 判定当前处于哪个 `Scope` 和哪个 `Function`
- 在控制平面上推进状态估计→算子选择→技能绑定→子代理分派→证据收集→裁决→状态更新
- 为每一轮控制回路收集最小必要证据
- 从下游技能获得结构化输出（`允许的下一路由`、`建议下一路由`、`可继续`、`继续阻塞项`、审批字段），而不是在 Harness 内部自行推断
- 只要下一次状态迁移仍然合法，且没有命中正式停止条件，就继续推进
- 只有在审批、缺失证据、运行时缺口或其他停止条件阻断安全继续时，才向程序员汇报当前状态

---

## 十、控制回路运行规范

### 10.1 状态估计阶段

1. 读取 `Harness Control State`，确定当前 `Scope` 和 `Function`
2. 根据当前 Scope 选择传感器组合：
   - `RepoScope`：读取 `Repo Goal/Charter`、`Repo Snapshot/Status`
   - `WorktrackScope`：读取 `Worktrack Contract`、`Plan/Task Queue`、当前 evidence
3. 如果标准快照缺失、过期或明显不足，只收集解释缺口所需的最小探查证据
4. 产出结构化状态估计结果，而不是文字摘要

### 10.2 算子选择阶段

1. 基于状态估计结果，评估合法的状态转移算子集合
2. 在 `RepoScope` 下，评估是否需要：
   - `Observe`（继续观察）
   - `ChangeControl`（目标变更）
   - `Init`（进入 WorktrackScope）
3. 在 `WorktrackScope` 下，评估是否需要：
   - `Init`（初始化局部状态）
   - `Observe`（状态估计）
   - `Decide`（调度）
   - `Dispatch`（分派执行）
   - `Verify`（收集证据）
   - `Judge`（裁决）
   - `Recover`（恢复）
   - `Close`（收尾）
4. 只推荐一个算子，并投影成显式路由、阻塞项集合与审批状态

### 10.3 技能绑定阶段

1. 将选定的算子映射到具体的 Skill 实现
2. 检查当前部署配置是否支持该 Skill
3. 如果部署配置缩窄了路由空间，把该配置视为硬路由边界

### 10.4 子代理分派阶段

1. 为选定的 Skill 构建限定范围任务简报和信息包
2. 如果宿主运行时提供真实的子代理分派壳层，使用委派式 SubAgent
3. 如果宿主运行时不提供，在当前载体内执行同一份限定范围约定，并明确报告为运行时回退
4. 不要声称已经分派了子代理，除非宿主运行时真的创建了委派载体

### 10.5 证据收集阶段

1. 消费子代理返回的结构化输出
2. 在 `Verify` 阶段，收集三个正交维度的证据：
   - 审查维度（代码正确性、结构合理性）
   - 验证维度（测试、验收条件）
   - 策略维度（规则、边界、不变量）
3. 证据必须结构化，不能是文字摘要

### 10.6 裁决阶段

1. 基于收集到的证据，执行 Gate 裁决
2. 在三个校验面上分别判定
3. 汇总生成最终 verdict：
   - `通过`
   - `软失败`
   - `硬失败`
   - `阻塞`

### 10.7 状态更新阶段

1. 根据裁决结果更新 `Harness Control State`
2. 如果是 `通过` → 进入 `Close` → 然后 `RepoScope.Refresh`
3. 如果是 `失败/阻塞` → 进入 `Recover`
4. 如果命中正式停止条件 → 向程序员返回控制权
5. 不要直接把子代理的返回结果当成状态更新的唯一依据；必须经过 Gate 裁决

---

## 十一、正式停止条件

只有在以下至少一个条件成立时才停止并返回控制权：

- **`审批门控`**：目标变更、范围扩张、破坏性动作或其他权限边界把 `需要审批` 置为 `真`
- **`证据门控`**：所需产物或证据缺失、过期或互相矛盾，已经无法安全继续
- **`路由阻塞`**：当前路由命中 `软失败`、`硬失败`、`阻塞`，或抛出了显式 `继续阻塞项`
- **`运行时缺口`**：宿主运行时缺少供下一个执行载体使用的安全分派壳层
- **`约定边界`**：下一步动作将越出已批准的代码仓库或工作追踪约定
- **`稳定交接`**：同一个交接边界在连续无变化轮次中再次被确认，因此再做一次完整重读只会重复相同的停止判定结果

---

## 十二、恢复策略

当 Gate 裁决为失败或阻塞时，Harness 必须进入恢复模式。合法恢复算子：

| 恢复算子 | 适用条件 | 限制 |
|---------|---------|------|
| `重试` | 当前目标、排除目标与基准仍然有效 | 不得扩大范围或重定义验收 |
| `回滚` | 当前状态已不可安全继续 | 除非程序员明确批准，否则执行破坏性变更前必须停止 |
| `拆分 Worktrack` | 当前范围过宽或包含多个独立验收切片 | 不得静默创建新 Worktrack；必须明确验收标准分配 |
| `刷新基准` | 上游真相变化使当前分支比较失效 | 不得改写 Repo Snapshot/Status 或目标/章程 |
| `重新规划` | 当前路径整体不可行 | 必须回到 RepoScope 重新 Decide |

---

## 十三、预期输出

使用这个技能时，产出一份 `Harness 控制回路报告`，至少包含：

### 控制面章节

- `当前 Scope`
- `当前 Function`
- `控制状态评估`
- `本轮已执行控制动作`
- `已审阅的产物与证据`
- `已运行的下游轮次`

### 状态转移章节

- `状态估计结果`
- `所选算子`
- `绑定技能`
- `分派模式`
- `收集的证据摘要`
- `Gate 裁决结果`

### 路由决策章节

- `允许的下一路由`
- `建议下一路由`
- `建议下一 Scope`
- `建议下一 Function`
- `可继续`
- `继续阻塞项`

### 权限与交接章节

- `需要审批`
- `审批范围`
- `审批理由`
- `待审批`
- `如何审查`

### 控制回路元数据

- `约定后自动性`
- `已使用自动继续`
- `检测到稳定交接`
- `交接状态`
- `交接锁激活`
- `检测到解锁信号`
- `交接解锁条件`
- `继续决策`
- `命中停止条件`

---

## 十四、硬约束

- **不要把 Harness 当成直接写代码的执行者。**
- **不要把 Function 算子隐含在技能名称后面。** 必须在控制面上显性化 `Observe → Decide → Dispatch → Verify → Judge → Recover → Close → ChangeControl` 的控制语义。
- **不要把 `Harness` 自己定义具体代码仓库动作、任务列表内容或执行任务。** 这些由下游技能的算子实现负责。
- **除非 `Harness Control State` 明确授予 `约定后自动性：最小委派`，否则不要开启约定后自动工作追踪。**
- **不要用自动继续推进去重定义代码仓库目标、扩大范围，或消耗超出许可额度的自动工作追踪预算。**
- **不要无限串接自动切片；一旦某个自动切片收束，就在 `要求自动切片后停止` 时重新交接。**
- **一旦 `稳定交接` 达成，保持运行时在 `等待交接` 状态，直到观测到显式解锁信号。**
- **不要把一次裸 `重试`、一句裸 `继续工作`，或没有实质变化的重复文字摘要视为解锁信号。**
- **当 `交接锁激活：真` 时，不要重新进入任何控制回路阶段，直到解锁信号出现。**
- **不要跨越未经批准的权限边界切换 `RepoScope` 与 `WorktrackScope`。**
- **只有当当前路由已经把这次切换标记为可继续，且没有任何正式停止条件要求审批时，范围切换才可以在没有新的程序员交接的情况下继续。**
- **在当前工作项尚未从活动 `Plan/Task Queue` 中选出之前，不要从 `WorktrackScope` 发起分派。**
- **当下游结果已经暴露了显式路由、阻塞项与审批字段时，不要从文字推断继续推进。**
- **当 `建议下一路由` 已存在时，不要把 `建议下一动作` 当成标准路由字段。**
- **不要因为某个下一步看起来很明显，就直接变更控制状态；先暴露请求中的状态迁移。**
- **不要把"某个本地技能轮次返回了结构化输出"本身当成停止条件。**
- **除非宿主运行时真的把执行委派给了一个独立载体，否则不要声称已经分派了 `SubAgent`。**
- **不要把 `证据`、`判定结果` 与 `下一动作` 混成一段模糊叙述。**
- **不要把代码仓库本地挂载结果当成真相来源。**
- **除非当前轮次确实依赖相邻系统，否则不要扩展进去。**
- **不要把 `Control State` 当成业务真相的容器。** 业务真相应分别保存在 `Repo` 与 `Worktrack` 的正式文档里。
- **不要跳过 Evidence 直接做 Gate 裁决。** 二者必须分开。
- **不要把三个正交校验面（implementation/validation/policy）压缩成一个笼统判定。**
- **不要把 `PR 已发出` 当成闭环终点。** 完整的 closeout 是 `merge → refresh repo snapshot → cleanup → return RepoScope`。

---

## 十五、资源

使用当前 `Harness Control State`、当前 Scope 所需的正式产物，以及下游技能的结构化输出作为本轮的权威依据。

判断下一次合法继续推进是否被允许时，应优先使用下游结构化输出，而不是本地叙述性摘要。

三轴参考：
- `Scope` 回答"在什么层上控制"
- `Function` 回答"控制器此刻在做什么"
- `Artifact` 回答"控制器依赖什么正式对象"
