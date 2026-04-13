---
title: Harness 指导思想
status: draft
updated: 2026-04-14
owner: OceanEye
last_verified: 2026-04-14
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
- `ChangeControl`

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

### RepoScope

`RepoScope` 是对长期基线的控制模式。

#### Observe

- `status`
- `structure`
- `status-detail`

#### Decide

- `whats-next`
- `verify-next`
- `go-next`

#### ChangeControl

- `change-goal`

这里不再建议使用旧命名 `add / remove`。原因是它们实质上是在改参考信号，不是普通的 Repo 状态转移。

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

#### Decide

- `schedule`

#### Dispatch

- `dispatch-subtask`

这里替代旧命名 `work`，用于强调 Harness 派发执行而不是亲自执行。

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

## 九、显式状态机

Harness 不应只有概念闭环，还应有最小可执行的状态机约束。

### 1. RepoScope 状态

| 状态 | 含义 | 进入条件 | 合法退出 |
|---|---|---|---|
| `observing` | 收集 `Repo Snapshot / Status`，确认当前主线状态 | 进入 `RepoScope` 或 `Worktrack` closeout 完成 | `deciding` |
| `deciding` | 判断下一步是否需要新建、恢复或刷新 worktrack | `observing` 完成且证据足够 | `ready-for-worktrack`、`change-control`、`observing` |
| `change-control` | 处理目标本身的变更申请 | 提出 `Goal Change Request` | `observing`、`ready-for-worktrack` |
| `ready-for-worktrack` | 已确认下一步局部状态转移，等待生成或切入 `Worktrack` | `deciding` 或 `change-control` 通过 | `WorktrackScope.initializing` |

### 2. WorktrackScope 状态

| 状态 | 含义 | 进入条件 | 合法退出 |
|---|---|---|---|
| `initializing` | 建立 branch、baseline、contract 与初始 plan | 从 `RepoScope.ready-for-worktrack` 切入 | `executing`、`blocked` |
| `executing` | 派发子任务并产生实际变更 | 已有 worktrack contract 与 task queue | `verifying`、`blocked` |
| `verifying` | 收集 review、test、rule-check 等证据 | 当前轮执行结束或需要阶段性验证 | `judging`、`recovering`、`blocked` |
| `judging` | 汇总 gate verdict，决定是否允许推进 | verify 证据足够 | `integrating`、`recovering`、`blocked` |
| `recovering` | 对 fail / drift / noise 进行回滚、拆分、重试、刷新 | gate 未通过或发现偏差 | `executing`、`verifying`、`blocked`、`closed` |
| `integrating` | 发起 PR、合并、清理、刷新基线 | 最终 gate 通过 | `closed`、`recovering` |
| `blocked` | 当前无法安全推进，需要补证、补权或人工决策 | 缺证据、缺权限、缺依赖、冲突未解 | 回到触发前状态或 `closed` |
| `closed` | 当前 worktrack 生命周期结束 | merge 完成、显式终止或废弃 | `RepoScope.observing` |

### 3. 非法转移

下面这些都应视为非法转移：

- `RepoScope.observing -> WorktrackScope.executing`
- `WorktrackScope.executing -> integrating`，但未经过 verify / judge
- `WorktrackScope.judging -> closed`，但未经过 merge 或显式 abort
- `blocked -> integrating`，但没有补证或补权

如果发生非法转移，Harness 应停止推进并报告状态机违例，而不是“尽量继续”。

## 十、Goal Change Control

目标本身是参考信号，不能和常规控制混在一起。

如果 Harness 在常规 `RepoScope` 操作里直接修改目标，就会出现典型的“移动球门”问题：控制器为了让误差变小，不去修系统，而去改目标。

因此，目标变更应单独进入 `ChangeControl` 流程，至少回答：

- 为什么要改目标
- 改目标会影响哪些现有 worktrack
- 是否需要废弃现有计划
- 是否需要重新定义 baseline
- 是否通过单独 gate

## 十一、Evidence 与 Gate

Harness 不能只有 `Gate`，必须同时有 `Evidence`。

没有证据层时，Harness 会退化成任务管理；没有 gate 时，Harness 就没有裁决能力。

在控制语义上：

- `Evidence` 负责证明“当前状态是什么”
- `Gate` 负责判断“当前状态是否允许推进”

二者必须分开。

### Gate Verdict 语义

`gate` 至少应区分下面 4 种裁决，而不是只有通过 / 不通过：

| verdict | 含义 | 典型后续动作 |
|---|---|---|
| `pass` | 当前证据充分，允许进入下一合法状态 | 进入 `integrating` 或返回上一级 closeout |
| `soft-fail` | 存在问题，但问题可在当前 worktrack 内通过补证或返工修复 | `replan`、补测、补 review、补 rule-check |
| `hard-fail` | 当前方案、目标或实现路径存在结构性问题，不能直接局部修补 | `rollback`、`split-worktrack`、刷新 baseline、重新评估目标 |
| `blocked` | 当前无法形成有效 verdict，因为缺少证据、依赖或审批 | 等待人工确认、等待外部依赖、补充上下文或权限 |

补充约束：

- `pass` 不等于“没有瑕疵”，而是“残余风险在可接受边界内”
- `soft-fail` 仍处于同一控制问题内，通常不要求改写 `Goal`
- `hard-fail` 往往意味着当前 `Worktrack Contract` 或执行路径需要被重构
- `blocked` 不是失败，而是“禁止继续猜测或强推”

## 十二、Authority Model

Harness 是控制器，但不是最高 authority。它必须知道谁能提议、谁能裁决、谁能 override。

### 1. 可提议者

下面这些对象可以提出观察、计划或变更建议：

- Harness 自身
- 执行 agent
- review / validation agent
- human operator

### 2. 常规控制授权

在边界已冻结且 `Worktrack Contract` 已批准的前提下，Harness 可以自动执行：

- `Observe`
- `Decide`
- `Dispatch`
- `Verify`
- 初步 `Judge`
- 非破坏性 `Recover`

### 3. 高风险动作授权

下面这些动作不应默认由低级自动流程自行批准：

- `change-goal`
- 对 `hard-fail` 的 override
- 带残余高风险的最终放行
- 合并到长期 baseline
- 废弃或重置仍有活跃依赖的 worktrack

这些动作应要求更高 authority。默认应由 human maintainer、repo owner，或被明确委托的高权限控制者确认。

### 4. Override 原则

如果发生 override，至少要留下：

- override 发起者
- override 理由
- override 影响范围
- override 后的附加验证要求

没有这些记录时，override 不应被视为合法控制动作。

## 十三、系统组件

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

## 十四、状态闭环

一个更完整的 `Worktrack` 闭环应当是：

1. 在 `RepoScope` 下观测现状并决定下一步
2. 生成 `Worktrack Contract`
3. 初始化 `Worktrack` 与 branch，对齐 baseline
4. 调度执行、收集 evidence、执行 verify
5. 汇总 gate verdict，失败则进入 recover
6. 通过后发起 `PR -> merge -> cleanup`
7. 回到 `RepoScope`，刷新 `Repo Snapshot / Status`

只有这样，`Repo` 的慢变量才会被真实更新，而不是停留在“PR 已发出”的半闭环状态。

## 十五、附录：与当前仓库主线的绑定关系

这一节只说明当前仓库里的局部绑定关系，不属于 Harness doctrine 本体。

当前仓库里，Harness 不应抢占其他对象的 truth。

- `Task Contract` 仍然是 `discussion -> execution` 之间的正式执行基线
- Harness 可以消费 `Task Contract`，但不能把它改写成自己的 truth
- Harness runtime 绑定与状态文件应留在 repo-local runtime layer，而不是回写进 canonical doc

在本仓库里，这和现有主线是一致的：

- `docs/deployable-skills/task-interface/task-contract.md` 负责固定 `Task Contract` 的职责与字段边界
- `product/harness-operations/skills/harness-standard.md` 已明确区分 `contract` 与 `runtime`

更具体的 repo-local adapter、runtime state file、deploy 绑定，应继续落在 `product/harness-operations/` 与 `docs/project-maintenance/`，而不是继续堆进这份指导思想。

## 十六、判断标准

如果下面几句话能成立，说明这套 Harness 定义是清楚的：

- 它把 `Repo` 与 `Worktrack` 分成了两个不同时间尺度的控制层
- 它把 `Scope`、`Function`、`Artifact` 三个维度分开了
- 它把目标变更从常规控制里剥离出来了
- 它把 Harness 和执行层分开了
- 它把 `Evidence` 与 `Gate` 同时立起来了
- 它把 `PR` 之后的闭环补完整了
