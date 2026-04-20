---
title: Harness 运行协议
status: draft
updated: 2026-04-20
owner: vibecoding
last_verified: 2026-04-20
---

# Harness 运行协议

> 目的：定义 `Harness` 在仓库演进中的最小运行协议，明确它如何围绕 `Repo` 与 `Worktrack` 两层状态工作、消费哪些正式对象、调用哪些控制算子，以及如何在 `Codex` 环境里把这些算子实现为 `Skills` 与 workflow。

## 一、协议总定义

`Harness` 不是执行器本身，而是驱动 repo 演进闭环的控制协议。

它的最小职责是：

- 在 `Repo` 层观察长期基线
- 在 `Worktrack` 层约束局部状态转移
- 通过 `Evidence + Gate` 判断当前状态是否允许继续推进
- 在失败、漂移或噪声出现时触发恢复动作
- 在 closeout 后把验证过的状态回写到 repo 级真相层

因此，`Harness 运行协议` 关注的不是“谁来写代码”，而是“什么状态允许转移、由什么对象执行、凭什么证据放行”。

## 二、系统覆盖层次

`Harness` 只覆盖两个控制层次：

### 1. Repo

`Repo` 是慢变量层，负责长期基线。

它关心：

- repo 目标
- repo 现状
- repo 活跃分支
- repo 治理状况
- 系统不变量
- 已知风险

### 2. Worktrack

`Worktrack` 是快变量层，负责局部状态转移。

它关心：

- 任务目标
- 工作范围
- 验收条件
- 当前 branch 与 baseline 的差异
- 子任务序列
- 回滚、拆分、恢复路径

`Repo` 与 `Worktrack` 必须分开建模。`Repo` 提供长期参考信号，`Worktrack` 负责当前局部闭环；两者不能混成同一份“工作状态”。

## 三、协议角色

### 1. 控制器

`Harness` 本体是控制器，负责：

- 选择下一合法动作
- 决定谁来执行
- 决定需要什么证据
- 判断当前状态能否推进
- 在 fail / drift / blocked 时选择恢复路径

### 2. 传感器

传感器负责把系统真实状态暴露给 `Harness`。

典型来源：

- git / diff / branch metadata
- repo scan
- test results
- code review results
- diff impact analysis
- 文档 freshness 检查

没有这些，state 只是“自报状态”。

### 3. 执行器

执行器负责实际改变系统状态，但它不等于 `Harness` 本体。

典型执行器：

- human developer
- coding agent
- review agent
- merge / rebase / archive 操作
- 文档更新动作

### 4. 扰动源

协议必须承认扰动存在，否则控制律会过于理想化。

典型扰动：

- 需求变化
- agent 幻觉
- 隐式依赖
- branch 漂移
- review 漏检
- 文档过时

### 5. 恢复器

恢复器不是单独角色，而是一组在失败后恢复控制的动作集合。

典型恢复动作：

- 回滚
- 重试
- 拆分 worktrack
- 降级目标
- 暂停并刷新 repo baseline

## 四、协议交付物

`Harness` 运行协议至少依赖下面几类正式对象。

### 1. Repo Goal / Charter

负责定义 `Repo` 的长期目标和方向。

最小字段：

- 项目愿景
- 核心功能目标
- 技术栈与演进方向
- 成功标准
- 系统不变量

### 2. Repo Snapshot / Status

负责描述 `Repo` 当前状态，作为慢变量观测面。

最小字段：

- 主线现状
- 架构与模块地图
- 活跃分支及用途
- 治理状况
- 已知问题与风险

### 3. Worktrack Contract

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

### 4. Plan / Task Queue

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

### 5. Gate Evidence

负责为状态转移裁决提供证据，而不是只记录口头结论。

最小字段：

- review / validation / policy 三类证据面
- 每条证据面的 freshness 或缺失状态
- 每条证据面的残余风险与上游约束信号
- 是否已经满足 gate intake
- gate verdict 与 route decision
- 为什么通过或不通过
- 后续动作

### 6. Harness Control State

负责保存控制面当前所处模式，而不是保存业务真相。

最小字段：

- 当前控制级别
- 当前活跃 worktrack
- 当前 baseline branch
- 当前需要执行的下一动作
- 关联正式文档路径

### 7. Goal Change Request

负责管理目标本身的变更，而不是把目标变更混入常规控制。

最小字段：

- 变更理由
- 影响分析
- 对现有 worktrack 的影响
- 是否需要重建 baseline
- 单独 gate 结论

## 五、状态与作用域

### 1. RepoScope

`RepoScope` 是对长期基线的控制模式。

最小状态：

- `observing`
- `deciding`
- `change-control`
- `ready-for-worktrack`

### 2. WorktrackScope

`WorktrackScope` 是对局部状态转移的控制模式。

最小状态：

- `initializing`
- `executing`
- `verifying`
- `judging`
- `recovering`
- `integrating`
- `blocked`
- `closed`

### 3. 最小状态闭环

1. 在 `RepoScope.observing` 下观测当前 repo 状态
2. 在 `RepoScope.deciding` 下确认下一步是切入 worktrack 还是进入 change control
3. 在 `WorktrackScope.initializing` 下建立 branch、baseline、contract 与初始 plan
4. 在 `WorktrackScope.executing` 下调度执行器产出变更
5. 在 `WorktrackScope.verifying` 下收集 `review / test / rule-check` 证据
6. 在 `WorktrackScope.judging` 下形成 gate verdict
7. fail 则进入 `recovering`，pass 则进入 `integrating`
8. 关闭 worktrack 后返回 `RepoScope.observing` 刷新 repo 状态

### 4. 连续推进与停止条件

`Harness` 的默认语义应当是连续推进，而不是每完成一个局部 skill round 就自动把控制权交还给 programmer。

也就是说：

- 单个 skill 的 `bounded round` 约束的是这次局部判断或局部执行包的边界
- 它不自动等价于“整个 Harness 本轮必须停机”
- 只要没有命中正式 stop condition，supervisor 应继续推进到下一个合法状态转移

最小 stop conditions 至少包括：

- 需要 programmer 明确批准的 goal change、scope expansion、destructive action 或其他 authority boundary
- 必需 artifact 或 evidence 缺失、过时、冲突，导致当前状态估计不再可靠
- `Gate` 给出 `soft-fail`、`hard-fail` 或 `blocked`
- 当前 host runtime 缺少合法的 execution carrier / dispatch shell，无法按受约束的 task/info 包继续执行
- 下一动作会把系统推出已批准的 `Task Contract`、`Worktrack Contract` 或 repo baseline

补充约束：

- 不得把“skill 已经返回结构化结果”本身当作 stop condition
- 不得把“没有专门 skill”本身当作 stop condition；命中这种情况时应优先转入 fallback execution carrier
- 如果 stop 的根因只是 runtime dispatch shell 缺位，必须显式报告为 runtime gap，而不是伪装成已完成的 subagent 执行

为了让 bounded rounds 可以被 supervisor 连续拼接，scope skills 在 handoff 时应优先显式给出：

- `allowed_next_routes`
- `recommended_next_route`
- `continuation_ready`
- `continuation_blockers`
- `approval_required`
- `approval_scope`
- `approval_reason`

在兼容迁移期内，runtime 或 backend 仍可镜像旧字段，例如 `recommended_next_action`、`needs_programmer_approval`、`approval_to_apply`；但这些旧字段应被视为兼容投影，而不是新的 authority source。

## 六、Function 与 Skill 的关系

`Function` 是协议层的控制算子，`Skill` 是这些算子在 `Codex` 环境中的可执行实现。

也就是说：

- `Function` 回答“控制器此刻在做什么”
- `Skill` 回答“在 `Codex` 里这一轮实际调用什么能力”

在当前项目的 `Codex` 语境里，不应为了文档整洁再额外引入一层脱离运行时的 `Function -> Skill` 转译目录。对实际 product 生成更重要的是：

- supervisor 当前会选什么 skills
- 当前 work item 会如何被 dispatch
- 没有专门 skill 时 fallback 到什么执行体

### 1. Worktrack dispatch fallback

`WorktrackScope` 下允许存在一个 `dispatch-skills` 类能力，用来为当前任务选择下游执行方式。

它必须遵守下面的 fallback 规则：

- 如果存在合适的专门 skill，优先使用该专门 skill
- 如果不存在合适的专门 skill，不得因此让系统停摆
- 此时必须自动 fallback 到一个通用任务完成执行载体
- fallback 仍然必须保持 bounded task、最小信息包和 evidence 回传

也就是说，系统不应把“没有专门 skill”解释成“不能继续执行”；它只意味着本轮应退化到通用任务完成执行体。

在当前 canonical worktrack chain 中，`schedule-worktrack-skill` 应当是 `current next action` 与 dispatch handoff packet 的唯一 authority。`init-worktrack-skill` 只负责种下 queue 和 schedule-facing handoff，`dispatch-skills` 只负责消费 schedule 已确认的 packet，而不是重新生成它。

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
- `Dispatch Info Packet` 只允许携带本轮必需上下文，不应退化成“把整个 repo 扔给 subagent”
- fallback 到通用执行载体时，输入输出结构不得放宽；变化的只是执行载体，不是控制边界
- `runtime_dispatch_mode` 必须显式区分“delegated subagent dispatch”和“current-carrier runtime fallback”
- `Skill` 回答“在当前 backend / agent 环境里，哪个执行单元来实现这个控制动作”

因此，在 `Codex` 内部，真正被调度的是 `Skills`；但在 doctrine 层，仍应先保留 `Function` 这个更稳定的协议抽象。

还需要再补两层：

- `Harness Dispatch`：选择合适的 skill binding，并向执行载体提供受约束的 task 和 info
- `SubAgent`：实际承接这次执行的运行时载体

当前仓库需要特别区分两件事：

- 选择了某个 `Skill`
- 实际已经把该 skill round 交给一个独立 `SubAgent`

前者是当前 canonical executable source 已经具备的合同层能力；后者仍然依赖 host runtime 的 dispatch shell，不应被自动假定为已经发生。

也就是说，在 `Codex / Claude` 里更完整的实践映射应当是：

- `Function` = operator
- `Skill` = operator realization
- `Harness Dispatch` = select skills + provide bounded task/info
- `SubAgent` = execution carrier

补充约束：

- `Skill` 不是严格数学意义上的状态转移函数
- 它更接近“受约束的近似转移器”
- 正因为 skill 和 subagent 的行为不是完全确定的，所以一次转移是否成立，仍然必须通过 `Evidence + Gate` 来判定

### 实践操作链

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

如果当前 host runtime 还没有稳定的 subagent dispatch shell，则允许暂时退化为：

`state estimate -> choose operator -> bind skill(s) -> package task/info -> execute in current carrier -> collect evidence -> adjudicate -> update state`

但此时必须显式标注：

- 当前是 runtime fallback，而不是完整 `subagent dispatch`
- 不得在报告里把“当前 carrier 内执行”写成“已经成功派发独立 subagent”

## 七、Scope 下的最小控制算子

### 1. RepoScope 算子

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

#### Close

- `refresh-repo-state`

### 2. WorktrackScope 算子

#### Init

- `init-worktrack`

#### Observe

- `status`
- `status-detail`

#### Decide

- `schedule`

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

- `replan`
- `rollback`
- `split-worktrack`
- `refresh-baseline`

#### Close

- `pr`
- `merge`
- `cleanup-branch`
- `close-worktrack`

## 八、Gate 协议

`Gate` 不应只等于“拼接 review 和 test 结果”，而应对正交检查面的裁决做统一汇总。

最小判定面：

- `implementation-gate`
- `validation-gate`
- `policy-gate`

最小 verdict：

- `pass`
- `soft-fail`
- `hard-fail`
- `blocked`

补充约束：

- `pass` 不等于“没有瑕疵”，而是“残余风险可接受”
- `soft-fail` 允许在当前 worktrack 内补证或返工
- `hard-fail` 意味着当前方案或路径需要结构性调整
- `blocked` 禁止继续猜测或强推

## 九、运行禁令

下面这些都不应被视为合法运行：

- 把 `Harness` 当成直接执行编码的主体
- 在常规控制流程里直接改写目标
- 跳过 `verify / judge` 直接进入 `PR` 或 `merge`
- 把 `PR` 当成闭环终点
- 把 runtime state 回写到 canonical product source
- 把 `Task Contract` 改写成 `Harness` 自己的 truth

## 十、与当前仓库主线的关系

在当前仓库里，这份协议应与现有主线保持兼容：

- `Task Contract` 仍然是 `discussion -> execution` 之间的正式执行基线
- `Harness` 可以消费 `Task Contract`，但不能改写它的 truth 边界
- `docs/harness/` 当前承接 Harness doctrine、workflow family 与运行协议真相层
- `product/harness/` 是当前仓库中的 Harness executable root，但当前阶段只建立最小骨架
- `memory-side` 与 `task-interface` 当前只保留 adjacent-system 合同层，不再在本仓库维持独立 `product/` skill roots
- 当前仓库中的具体 executable source 只保留在 `product/harness/`
- repo-local runtime state 应继续留在 repo-local state layer

## 十一、判断标准

如果下面几句话能成立，说明这份 `Harness 运行协议` 是清楚的：

- 它把 `Repo` 与 `Worktrack` 分成了两个时间尺度不同的控制层
- 它把 `Function` 与 `Skill` 区分开了
- 它补上了 `Harness Dispatch` 与 `SubAgent` 这层实践操作链
- 它把 `Function` 理解为状态转移算子，而不是平面动作名词
- 它把 `Evidence` 与 `Gate` 同时立起来了
- 它把 `PR` 之后的闭环补完整了
- 它没有把 `Harness` 和执行器粘在一起

## 十二、外部证据摘要

外部证据支持这份协议的主要方向：

- 工业界越来越把 `Harness` 视为模型外部的 orchestration / eval / governance / environment layer
- 学术界越来越强调 verifier、retrieval、trace、versioned snapshots 与 long-horizon loop
- 控制论视角更支持把 `Harness` 写成 `hierarchical supervisory controller`
- 多 `SubAgent` 是容量扩展和并行探索手段，但不是 ontology 本体

这些证据共同支持下面的整合结论：

- `Harness` 不能脱离 `Skills` 这种相对稳定的转移实现而存在
- 但 `Harness` 也不能退化成 `Skills` 本身
- 因此，runtime 层必须显式补上 `operator -> skill binding -> subagent dispatch` 这条最后一环

## 十三、代表性外部来源

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
