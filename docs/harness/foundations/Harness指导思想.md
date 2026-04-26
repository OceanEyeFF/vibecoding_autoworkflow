---
title: Harness 指导思想
status: draft
updated: 2026-04-15
owner: OceanEye
last_verified: 2026-04-15
---

# Harness 指导思想

> 目的：定义 `Harness` 在 repo 演进中的控制对象、分层边界、核心交付物与状态闭环，避免把它误写成“执行器本身”或“普通任务流”。

## 一、总定义

**Harness 是对 Repo 演进过程的分层闭环控制系统。**

它在 `Repo` 级维护长期基线与系统不变量，在 `Worktrack` 级约束局部状态转移，并通过 `Evidence + Gate` 决定状态是否允许推进为新的基线。

换句话说，Harness 关注的不是“把任务做完”本身，而是：

- 给系统输入
- 观察系统输出
- 和目标状态对比
- 判断当前状态是否允许继续推进
- 在失败时阻断、恢复、重试、回滚或重新规划

## 二、它不是什么

- 不是直接执行编码的主体
- 不是 `Task Contract` 的上游真相层
- 不是某个 backend 的 repo-local runtime wrapper
- 不是把一组 skill 顺序串起来的 open-loop 流程图
- 不是可以在常规控制里随意改写目标的任务管理器

## 三、Harness 控制什么

Harness 控制的不是每一行代码，而是 **Repo 演进的偏差、风险、熵，以及状态转移的合法性**。

当前至少有 6 个被控变量：

| 被控变量 | 说明 |
|---|---|
| `目标偏差` | 当前 `Repo` / `Worktrack` 距离目标状态还有多远 |
| `范围漂移` | 实际改动是否越出了声明的 scope |
| `集成风险` | 当前改动是否破坏主线或引入不可接受问题 |
| `治理债务` | 文档、测试、结构、规则是否出现缺口 |
| `分支熵` | 活跃分支是否过多、过老、失去用途或偏离基线 |
| `证据完备度` | 当前 `review / test / rule-check` 是否足以支持放行 |

## 四、两层控制对象

Harness 只覆盖两个时间尺度不同的层次：

### 1. Repo

`Repo` 是慢变量，负责长期基线。

它关心：

- Repo goal
- 架构与模块地图
- 主分支现状
- 活跃分支及用途
- 治理状况
- 系统不变量
- 已知风险

### 2. Worktrack

`Worktrack` 是快变量，负责局部状态转移。

它关心：

- 当前任务目标
- 工作范围与非目标
- 验收条件
- 当前 branch 与 baseline 的差异
- 当前子任务序列
- 回滚、拆分、恢复路径

`Repo` 与 `Worktrack` 必须分开建模。前者负责长期参考信号，后者负责局部转移；两者不能混成同一份“工作状态”。

## 五、三轴模型

当前文档应按 3 个正交维度组织，而不是把 skill、文档、状态和动作混排在一起。

### 1. Scope 轴

- `Repo`
- `Worktrack`

### 2. Function 轴

- `Observe`
- `Decide`
- `Dispatch`
- `Verify`
- `Judge`
- `Recover`
- `Close`

### 3. Artifact 轴

- `Goal / Charter`
- `Snapshot / Status`
- `Contract`
- `Plan / Task Queue`
- `Evidence`
- `Cursor / Control State`
- `ChangeRequest`

这 3 轴的作用不同：

- `Scope` 回答“在什么层上控制”
- `Function` 回答“控制器此刻在做什么”
- `Artifact` 回答“控制器依赖什么正式对象”

补充约束：

- 在 doctrine 层，`Scope / Function / Artifact` 仍然是最稳的三轴
- 在 `Codex / Claude` 的实践层，还必须补上一层 `Skill / SubAgent` 绑定
- 这层绑定负责把控制算子落成可执行转移，但它不应反过来取代 doctrine 本体

## 六、控制平面与执行平面

Harness 本体属于 **控制平面**，不属于 **执行平面**。

### 控制平面

负责：

- 决定下一步做什么
- 决定谁来执行
- 决定需要哪些证据
- 决定当前状态能否继续推进
- 在失败时安排恢复动作

### 执行平面

负责：

- 实际编码
- 实际 review
- 实际测试
- 实际合并、回滚、清理

因此，旧语义里的 `work` 不应再被理解为 “Harness 自己做工作”，而应改成更明确的控制动作，例如：

- `dispatch-subtask`
- `execute-via-agent`

这样才不会把控制器和执行器粘在一起。

## 七、核心交付物

Harness 的核心交付物应至少覆盖下面几类正式对象。

### 1. Repo Goal / Charter

**职责**：定义 `Repo` 的长期目标和方向。

**应包含内容**：

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

### 2. Repo Snapshot / Status

**职责**：描述 `Repo` 的当前状态，作为控制器的慢变量观测面。

**应包含内容**：

- 主线现状
- 架构与模块地图
- 活跃分支及用途
- 治理状况
- 已知问题与风险

### 3. Worktrack Contract

**职责**：定义单个 `Worktrack` 的局部状态转移合同。

**应包含内容**：

- 任务目标
- `Node Type`（从 Goal Charter 的 Engineering Node Map 绑定）
- 工作范围
- 非目标
- 影响模块
- 计划中的 next state
- 验收条件
- 回滚条件

### 4. Plan / Task Queue

**职责**：把 `Worktrack Contract` 展开成可执行的子任务序列。

**应包含内容**：

- 子任务列表
- 执行顺序
- 依赖关系
- 当前阻塞
- 当前下一动作
- 验收条件与任务队列的对齐关系

### 5. Gate Evidence

**职责**：为状态转移裁决提供证据，而不是只记录口头结论。

**应包含内容**：

- 实际变更摘要
- 检查结果
- review verdict
- 未解决问题
- 是否通过 gate
- 为什么通过 / 不通过
- 后续动作

### 6. Harness Cursor / Control State

**职责**：保存控制面当前处于哪个模式，而不是保存业务真相。

建议将旧名字 `Harness 工作Scope 文档` 改成：

- `Harness Cursor`
- 或 `Harness Control State`

**应包含内容**：

- 当前控制级别（`RepoScope` / `WorktrackScope`）
- 当前活跃 worktrack
- 当前 baseline branch
- 当前需要执行的下一动作
- 关联正式文档路径

它不应承载业务真相。业务真相应分别保存在 `Repo` 与 `Worktrack` 的正式文档里。

### 7. Goal Change Request

**职责**：管理目标本身的变更，而不是把目标变更混入常规控制。

**应包含内容**：

- 变更理由
- 影响分析
- 对现有 worktrack 的影响
- 是否需要重建 baseline
- 单独 gate 结论

## 八、Function 视角下的技能分类

这里要补一条关键约束：

- `Function` 不是 skill 名字，而是状态转移算子
- `Skill` 是这些算子在 `Codex / Claude` 里的相对稳定实现
- `SubAgent` 是被 Harness 调度的执行载体

因此，Harness 在实践层不能脱离 `Skills` 而存在；但在 ontology 上，`Skills` 也不能反过来取代 `Function`。

### RepoScope

`RepoScope` 是对长期基线的控制模式。

#### Observe

- `status`
- `structure`
- `status-detail`

这些更适合作为 `Observe` 的稳定 skill realization，而不是直接把 `Observe` 本身写成 skill 名字。

#### Decide

- `whats-next`
- `verify-next`
- `go-next`

这里的重点不是“列出 skill 名称”，而是固定：什么证据足以支持下一次 repo 级状态切换。

#### ChangeGoal（参考信号设定）

- `change-goal`（由外部目标变更请求触发）

`ChangeGoal` 不是常规控制回路中的状态转移算子，而是参考信号设定层。它和 `SetGoal` 同属循环外的参考信号设定操作：在常规控制回路中 `Goal` 不可变，只有在收到外部目标变更请求时，才由 `ChangeGoal` 触发分析→草案→确认→执行的完整闭环。设定/重设完成后，系统重新启动常规循环。常规 `Decide` 不得主动选择目标变更作为下一步动作，否则会出现"移动球门"问题。

#### Close

- `refresh-repo-state`

`Worktrack` 关闭后，`RepoScope` 需要重新刷新 snapshot，而不是直接假定主线状态已经完成切换。

### WorktrackScope

`WorktrackScope` 是对局部状态转移的控制模式。

#### Init

- `init-worktrack`

#### Observe

- `status`
- `status-detail`

在实践层，这一块往往还需要显式的 retrieval / localization 组件，否则 `Observe` 只会退化成自报状态。

#### Decide

- `schedule`

#### Dispatch

- `dispatch-subtask`

- `execute-via-agent`

这里替代旧命名 `work`，用于强调 Harness 派发执行而不是亲自执行。

这也是实践层的最后一环：Harness 不直接写代码，而是选择合适的 `skill binding`，并向 `SubAgent` 提供受约束的 task 和 info。

#### Verify

- `review`
- `test`
- `rule-check`

#### Judge

- `gate`

`gate` 不应只意味着“把几个结果拼起来”。它应汇总正交校验面的裁决。

建议把旧命名 `second-gate / third-gate` 收敛成下面几类判定面：

- `implementation-gate`：代码正确性、结构合理性
- `validation-gate`：测试、验收条件、运行结果
- `policy-gate`：规则、边界、不变量、治理要求

最后由汇总 `gate` 生成最终 verdict。

#### Recover

- `replan`
- `rollback`
- `split-worktrack`
- `refresh-baseline`

#### Close

- `pr`
- `merge`
- `cleanup-branch`
- `close-worktrack`

这里要强调：`pr` 不是闭环终点，`merge -> refresh repo snapshot -> cleanup -> return RepoScope` 才是完整 closeout。

## 十五、思路层与实践层的差距

当前最需要补上的，不是更多抽象名词，而是 doctrine 到 runtime 之间的最后一环。

思路层回答：

- 当前处于哪个 `Scope`
- 当前状态是什么
- 哪个 `Function` 才是合法转移算子
- 需要哪些 `Artifact` 才能支持这次转移

实践层回答：

- 这次算子由哪个 `Skill` 实现
- 需要向哪个 `SubAgent` 派发
- `SubAgent` 需要收到哪些 task 和 info
- 返回什么 evidence 才能让 gate 认可这次转移

因此，在 `Codex / Claude` 里，更完整的链条应当是：

`state estimate -> choose operator -> bind skill(s) -> package task/info -> dispatch subagent -> collect evidence -> adjudicate -> update state`

当宿主运行时支持真实 SubAgent 委派且权限边界允许时，`dispatch subagent` 是默认执行模式。只有运行时没有稳定分派壳层、权限边界禁止委派，或当前任务包不满足安全分派条件时，才允许退化为当前载体内执行；退化时必须显式说明 `runtime fallback`、`permission blocked` 或 `dispatch package unsafe` 等原因，不能把 current-carrier fallback 写成已经委派了 SubAgent。

这里有两个关键约束：

- `Skill` 不是严格数学意义上的状态转移函数，而是受约束的近似转移器
- 正因为 skill 和 subagent 的行为不是完全确定的，所以 `Evidence + Gate` 仍然是必需层，不能省掉

## 十六、外部证据摘要

外部研究和工业实践给出的信号已经比较一致：

- 工业界越来越把 `Harness` 视为模型外部的 orchestration / eval / governance / environment layer，而不是 prompt 包本身
- 学术界最强的进展不只是更强执行 agent，而是更强 verifier、retrieval、trace 和 long-horizon 闭环
- 控制论视角更支持把 `Harness` 写成 `hierarchical supervisory controller`，而不是普通 workflow
- 多 `SubAgent` 主要解决容量和并行探索问题，但不能取代 supervisor 语义本体

这说明当前最稳的整合结论是：

- `Harness` = 监督控制器
- `Function` = 状态转移算子
- `Skill` = 算子实现
- `SubAgent` = 执行载体
- `Workflow / Profile` = 控制策略

代表性外部来源见 [Harness运行协议.md](./Harness运行协议.md) 的“代表性外部来源”。

## 九、目标变更（ChangeGoal）

目标本身是参考信号，不能和常规控制混在一起。

如果 Harness 在常规 `RepoScope` 操作里直接修改目标，就会出现典型的"移动球门"问题：控制器为了让误差变小，不去修系统，而去改目标。

因此，目标变更不属于常规控制回路的 `Function` 算子，而是由外部请求触发的参考信号重设操作。它对应 `repo-change-goal-skill` 的实现，至少回答：

- 为什么要改目标
- 改目标会影响哪些现有 worktrack
- 是否需要废弃现有计划
- 是否需要重新定义 baseline
- 变更幅度（minor / moderate / major）
- 是否获得用户确认

其工作流为：读取当前状态 → 分析变更影响 → 生成 goal-charter 草案 → 用户确认 → 执行改写 → 返回 `RepoScope.Observe`。在用户确认前不写入任何文件。

## 十、Evidence 与 Gate

Harness 不能只有 `Gate`，必须同时有 `Evidence`。

没有证据层时，Harness 会退化成任务管理；没有 gate 时，Harness 就没有裁决能力。

在控制语义上：

- `Evidence` 负责证明“当前状态是什么”
- `Gate` 负责判断“当前状态是否允许推进”

二者必须分开。

## 十一、系统组件

### 1. 传感器（sensor）

**定义**：Harness 通过什么知道状态是真的？

**示例**：

- git / diff / branch metadata
- test results
- code review results
- diff impact analysis
- 文档 freshness 检查

没有这些，state 只是“自报状态”。

### 2. 执行器（executor）

**定义**：什么对象实际改变系统状态？

**示例**：

- human developer
- coding agent
- review agent
- merge / rebase / archive 操作
- 文档更新动作

执行器是被 Harness 调度的对象，不等于 Harness 本体。

### 3. 扰动源（noise）

**定义**：什么会让系统偏离？

**示例**：

- 需求变化
- agent 幻觉
- 隐式依赖
- branch 漂移
- review 漏检
- 文档过时

扰动必须显式写出来，否则控制律会过于理想化。

### 4. 恢复策略（recovery）

**定义**：gate fail 之后如何恢复控制？

**示例**：

- 回滚
- 重试
- 拆分 worktrack
- 降级目标
- 暂停并刷新 repo baseline

## 十二、状态闭环

一个更完整的 `Worktrack` 闭环应当是：

1. 在 `RepoScope` 下观测现状并决定下一步
2. 生成 `Worktrack Contract`
3. 初始化 `Worktrack` 与 branch，对齐 baseline
4. 调度执行、收集 evidence、执行 verify
5. 汇总 gate verdict，失败则进入 recover
6. 通过后发起 `PR -> merge -> cleanup`
7. 回到 `RepoScope`，刷新 `Repo Snapshot / Status`

只有这样，`Repo` 的慢变量才会被真实更新，而不是停留在“PR 已发出”的半闭环状态。

## 十三、与仓库现有主线的关系

当前仓库里，Harness 不应抢占其他对象的 truth。

- `Task Contract` 仍然是 `discussion -> execution` 之间的正式执行基线
- Harness 可以消费 `Task Contract`，但不能把它改写成自己的 truth
- Harness runtime 绑定与状态文件应留在 repo-local runtime layer，而不是回写进 canonical doc

这和仓库现有主线是一致的：

- `docs/harness/adjacent-systems/task-interface/task-contract.md` 负责固定 `Task Contract` 的职责与字段边界
- 本主文档与 `Harness运行协议` 已继续强调控制平面与执行平面的边界

## 十四、判断标准

如果下面几句话能成立，说明这套 Harness 定义是清楚的：

- 它把 `Repo` 与 `Worktrack` 分成了两个不同时间尺度的控制层
- 它把 `Scope`、`Function`、`Artifact` 三个维度分开了
- 它没有把 `Skill` 误写成上位 ontology，但也没有遗漏 `Skill / SubAgent` 这层实践绑定
- 它把目标变更从常规控制里剥离出来了
- 它把 Harness 和执行层分开了
- 它把 `Evidence` 与 `Gate` 同时立起来了
- 它把 `PR` 之后的闭环补完整了
