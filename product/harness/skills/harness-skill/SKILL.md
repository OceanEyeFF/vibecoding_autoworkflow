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
- 不是已批准输入或工作追踪合同的替代物
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

**执行载体偏好**：当实现、审查或验证任务可以被打包成边界清楚、信息充分、权限安全的单轮任务时，Harness 默认应优先通过真实 `SubAgent` 执行，而不是让控制器自己完成执行平面工作。只有在运行时缺少稳定分派壳层、权限边界禁止委派，或任务包不满足安全分派条件时，才允许当前载体回退执行；回退原因必须显式记录。

---

## 三、系统组件

Harness 作为控制系统，包含以下系统组件：

### 3.1 传感器（Sensor）

**定义**：Harness 通过什么知道状态是真的？

**示例**：
- git / diff / branch metadata
- release/package/VCS version facts（package version、git commit/tag/branch、SVN revision 如适用、registry dist-tag）
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

控制平面不应因为没有命中一个完全匹配的专用技能，就直接吸收执行责任。正确路径是先把任务压缩成受约束的执行包，再选择专用技能、通用 `SubAgent` 或明确的当前载体回退。

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
- `ChangeGoal` —— 目标变更
- `SetGoal` —— 初始化参考信号

**约束**：`Function` 不是 skill 名字，而是状态转移算子。`Skill` 是这些算子在 `Codex / Claude` 里的相对稳定实现。`SubAgent` 是被 Harness 调度的执行载体。

### 6.3 Artifact 轴

回答"控制器依赖什么正式对象"：
- `Goal / Charter` —— 长期目标，并承载 `Engineering Node Map`
- `Snapshot / Status` —— 当前状态
- `Contract` —— 局部状态转移合同，并绑定从 Goal 派生的 `Node Type`
- `Plan / Task Queue` —— 可执行子任务序列
- `Evidence` —— 状态转移证据
- `Cursor / Control State` —— 控制面当前模式
- `ChangeRequest` —— 目标变更请求

**关键约束**：`Control State` 只保存控制面状态，不承载业务真相。业务真相应分别保存在 `Repo` 与 `Worktrack` 的正式文档里。
`Engineering Node Map` 属于 Repo 级目标真相；`Node Type` 与 `baseline_form`、`merge_required`、`gate_criteria`、`if_interrupted_strategy` 属于 Worktrack Contract 的执行约束。下游状态、调度、证据、关卡、恢复和收尾交接只能引用或携带这些字段，不应重新发明策略。

---

## 七、两层控制律

### 7.1 RepoScope 控制律

`RepoScope` 是对长期基线的控制模式。

```
参考信号设定（循环外，Goal 在循环中不可变）：
SetGoal (set-harness-goal-skill) ──→ 仅在 .aw/ 未初始化时
ChangeGoal (repo-change-goal-skill) ──→ 由外部目标变更请求触发
                                    ↓
                              设定/重设完成后启动常规循环

RepoScope 控制回路（Goal 在此回路中不可变）：
Observe (repo-status-skill)
    ↓
Decide (repo-whats-next-skill)
    ↓
    ├─→ 保持并观察 ───────────────────────────────→ 回到 Observe
    └─→ 准备进入 WorktrackScope ──────────────────→ [Scope 切换]
                                                       ↓
WorktrackScope 控制回路（局部状态转移）：               Init (init-worktrack-skill)
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
                                ┌──────────┼──────────┐
                                ↓          ↓          ↓
                              通过      失败/阻塞    恢复
                                ↓          ↓          ↓
                            Close      Recover    Recover
                                ↓          ↓          ↓
                        [Scope 切换]   回到 Observe/  回到 RepoScope
                                ↓          Decide       或等待审批
                        RepoScope.Refresh (repo-refresh-skill)
                                ↓
                            回到 Observe
                                ↓
                        [git hash 对比守卫：若 HEAD 未变则跳过刷新]
```

其中 `Close` 绑定到 `close-worktrack-skill`，`Recover` 绑定到 `recover-worktrack-skill`。

**控制目标**：维护 Repo 的长期基线稳定，判断是否需要进入局部执行。

### 7.2 完整状态闭环

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
                                   RepoScope.Refresh (repo-refresh-skill)  回到 Observe/ 回到 RepoScope
                                                        Decide       或等待审批
                                          ↓
                                   RepoScope.Observe ──→ [循环]
                                          ↓
                                   [git hash 对比守卫：若 HEAD 未变则跳过刷新]
```

其中 `Close` 绑定到 `close-worktrack-skill`，`Recover` 绑定到 `recover-worktrack-skill`。

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
3. **Git Commit Hash 基线对比（幂等性守卫）**：
   - 读取 `.aw/control-state.md` 的 `Baseline Traceability` 段，获取 `latest_observed_checkpoint`（即上次刷新时记录的 git commit hash）
   - 执行 `git rev-parse HEAD` 获取当前 HEAD hash
   - 对比两个 hash：若一致，说明 repo 代码基线自上次刷新后未变化，跳过 `repo-refresh-skill` 绑定，仅在状态估计中标记 `repo_baseline_unchanged: true`
   - 若 hash 不一致（或 `latest_observed_checkpoint` 缺失），说明代码基线已变化，必须在本轮合适阶段绑定 `repo-refresh-skill` 刷新 Repo 级慢变量
   - 此检查确保不会对同一基线重复执行 repo-refresh，避免不必要的刷新开销
4. **文档 Freshness 基线对比**：如果发现本轮涉及 release、deploy、adapter、package、VCS baseline、CLI 版本或 operator-facing docs，且文档版本事实可能落后于代码/registry/VCS 证据，应标记 `doc_catch_up_needed: true`，并在合适阶段绑定 `doc-catch-up-worker-skill`；如果上次 `doc-catch-up` 执行时的 git hash 与当前 HEAD 一致且无新的文档变更，可跳过重复追平
5. 如果标准快照缺失、过期或明显不足，只收集解释缺口所需的最小探查证据
6. 产出结构化状态估计结果，而不是文字摘要

### 10.2 算子选择阶段

1. 基于状态估计结果，评估合法的状态转移算子集合
2. 在 `RepoScope` 下，评估是否需要：
   - `Observe`（继续观察）
   - `Init`（进入 WorktrackScope）

   **关键约束**：`ChangeGoal` 不由常规 Decide 选择。目标变更由外部请求触发，完成后系统重新进入 Observe。
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
2. 读取执行载体开关：先看 `.aw/control-state.md` 的 `subagent_dispatch_mode_override_scope`。默认 `worktrack-contract-primary` 表示当前 `Worktrack Contract` 的 `runtime_dispatch_mode` 优先；只有显式 `global-override` 才让 `.aw/control-state.md` 的 `subagent_dispatch_mode` 压过 worktrack。若 worktrack 未声明，再使用 control-state 作为 repo 级默认值，最终默认值为 `auto`
3. `runtime_dispatch_mode` / `subagent_dispatch_mode` 支持 `auto` / `delegated` / `current-carrier`
4. `auto` 表示宿主运行时提供真实的子代理分派壳层且权限边界允许时，默认使用委派式 SubAgent；运行时没有稳定分派壳层、权限边界禁止委派，或任务包不满足安全分派条件时，必须显式 fallback
5. `delegated` 表示必须真实创建委派载体；如果无法委派，应返回运行时缺口或权限阻塞，而不是自动改为当前载体执行
6. `current-carrier` 表示本轮显式关闭 SubAgent 委派，允许当前载体在同一份限定范围约定内执行
7. 发生当前载体运行时回退时，必须显式记录回退原因、未委派原因和保持的任务/信息边界
8. 不要声称已经分派了子代理，除非宿主运行时真的创建了委派载体

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
2. 如果是 `通过` → 进入 `Close` → 然后 `RepoScope.Refresh`：
   - **显式绑定 `repo-refresh-skill`**，从已验证 `关卡证据` 刷新 `Repo Snapshot/Status`
   - 刷新完成后，执行 `git rev-parse HEAD` 获取当前 HEAD hash，将其写入 `.aw/control-state.md` 的 `Baseline Traceability.latest_observed_checkpoint` 字段，作为下次状态估计时 git hash 对比的锚点
   - 此 hash 存储确保下次 Harness 轮次启动时能正确判断是否需要重新刷新
3. 如果是 `失败/阻塞` → 进入 `Recover`
4. **文档追平收口**：在 Close、handback 或 release/post-smoke 收口前，如果本轮改变了代码版本、package/release 事实、git/SVN baseline、deploy/adapter 行为、验证命令或 operator-facing 文档，必须调用或显式安排 `doc-catch-up-worker-skill`；版本事实场景使用 `version fact sync`，并记录 source version、published version、VCS tracking facts 与未更新文档理由。如果 `doc-catch-up` 成功执行，将当前 git hash 写入 `.aw/control-state.md` 的 `Baseline Traceability.last_doc_catch_up_checkpoint`，作为下次文档 freshness 检查的对比锚点
5. 如果命中正式停止条件 → 向程序员返回控制权
6. 不要直接把子代理的返回结果当成状态更新的唯一依据；必须经过 Gate 裁决

### 10.8 Git Commit Hash 幂等性守卫

Harness 使用 git commit hash 作为幂等性锚点，避免对同一代码基线重复执行 `repo-refresh-skill` 和 `doc-catch-up-worker-skill`。

**存储位置**：`.aw/control-state.md` 的 `Baseline Traceability` 段。

**字段定义**：

| 字段 | 含义 | 更新时机 |
|------|------|---------|
| `latest_observed_checkpoint` | 上次 `repo-refresh-skill` 执行后记录的 git HEAD hash | `RepoScope.Refresh` 完成后写入 |
| `last_doc_catch_up_checkpoint` | 上次 `doc-catch-up-worker-skill` 执行后记录的 git HEAD hash | 文档追平完成后写入 |
| `verified_at` | 最近一次 checkpoint 验证时间 | 每次检查更新 |

**工作逻辑**：

```text
Harness 启动 → 状态估计阶段
  ├─ git rev-parse HEAD → 当前 hash
  ├─ 读取 latest_observed_checkpoint
  │   ├─ hash 一致 → repo_baseline_unchanged: true → 跳过 repo-refresh-skill
  │   └─ hash 不一致/缺失 → repo_baseline_changed: true → 绑定 repo-refresh-skill
  ├─ 读取 last_doc_catch_up_checkpoint
  │   ├─ hash 一致且本轮无文档变更 → 跳过 doc-catch-up-worker-skill
  │   └─ hash 不一致或有文档变更 → doc_catch_up_needed: true → 绑定 doc-catch-up-worker-skill
  └─ 继续正常控制回路

Close/Refresh 完成 → 状态更新阶段
  ├─ repo-refresh-skill 执行成功 → 写入 latest_observed_checkpoint = HEAD hash
  └─ doc-catch-up-worker-skill 执行成功 → 写入 last_doc_catch_up_checkpoint = HEAD hash
```

**硬约束**：

- git hash 对比仅作为"跳过重复刷新"的条件，不得作为"跳过首次验证"的借口
- `doc-catch-up` 的 hash 对比只能跳过"代码未变且文档未变"的重复追平；如果本轮明确修改了文档，即使 hash 未变也必须触发文档追平检查

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

以上恢复策略由 `recover-worktrack-skill` 实现。Gate 裁决为失败或阻塞时，应绑定 `recover-worktrack-skill` 执行恢复动作；恢复成功后的收尾由 `close-worktrack-skill` 负责。`close-worktrack-skill` 同时负责 WorktrackScope 的正常收尾（Gate 通过后的 Close 路径）。

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

## 十四、Artifact Output Protocol

所有 skill 产出的 artifact 必须遵守以下全局协议：

1. **先完整生成，再做压缩**：每个 skill 先生成尽可能长且完整的原始内容，确保信息不丢失；然后通过压缩步骤提取 `Control Signal` 层。
2. **控制结论优先**：影响下一动作决策的信息放在 `Control Signal` 层；完整证据、日志、原始输出放在 `Supporting Detail` 层。
3. **禁止平铺重复**：已在其他 artifact 中记录的信息，使用引用（文件路径 + section）而不是内联全文复制。
4. **空值压缩**：无实质内容的字段使用 `N/A`，删除占位符行（如 `- ` 或 `待填写`）。
5. **引用格式**：引用其他 artifact 时使用 `[artifact-path#section]` 格式，例如 `[.aw/worktrack/contract.md#Task Goal]`。
6. **压缩不是省略**：`Supporting Detail` 层必须保留完整内容，只是不纳入传递/决策上下文；后续如需查阅细节，可直接读取。

## 十五、硬约束

- **Harness 输出只能是控制决策结构体**（Scope/Function/Route/Verdict/Evidence 引用）；代码块和直接执行指令禁止出现在 Harness 输出中。
- **Function 算子必须在控制面上显性化**为 `Observe → Decide → Dispatch → Verify → Judge → Recover → Close → ChangeGoal` 的控制语义；禁止仅通过技能名称隐式传达当前算子。
- **Harness 仅负责选择算子、绑定技能和裁决 Gate**；具体代码仓库动作、任务列表内容和执行任务的细节由下游技能的算子实现负责。
- **SubAgent 使用必须是可开关参数，而不是硬编码行为。** 控制态字段 `subagent_dispatch_mode` 与工作追踪约定字段 `runtime_dispatch_mode` 支持 `auto` / `delegated` / `current-carrier`；控制态字段 `subagent_dispatch_mode_override_scope` 默认是 `worktrack-contract-primary`，只有显式 `global-override` 才是全局覆盖；默认 `auto` 才表示在宿主运行时支持真实 SubAgent 委派且权限边界允许时优先委派。未委派时必须将原因记录为 `runtime fallback`、`permission blocked` 或 `dispatch package unsafe`。
- **约定后自动工作追踪仅当 `Harness Control State` 明确授予 `约定后自动性：最小委派` 时才可开启**；否则必须保持手动交接模式。
- **自动继续推进的边界严格等于当前 `Worktrack Contract` 的 scope**；超出 scope 的改动、目标重定义或预算超支必须触发审批门控。
- **自动切片仅可在当前切片未收束时串接**；一旦切片收束且 `要求自动切片后停止` 为真，必须停止执行并重新交接。
- **稳定交接达成后，运行时唯一合法状态是 `等待交接`**；仅当观测到显式解锁信号时方可退出此状态。
- **解锁信号必须是程序员显式发出的新指令或实质性新信息**；裸 `重试`、裸 `继续工作` 或重复文字摘要不构成解锁信号。
- **交接锁激活时，所有控制回路阶段的进入必须被阻断**；仅当有效解锁信号出现后控制回路方可恢复。
- **技能轮次返回结构化输出是正常控制回路产物**；停止条件仅由 [十一、正式停止条件] 定义的六种正式条件触发。
- **Evidence、Verdict 和 NextAction 必须在输出中分节独立呈现**；每节仅包含对应类型的内容，禁止将三者合并为一段叙述。
- **相邻系统的引用仅当本轮证据确实消费了其输出时才可包含**；否则 `adjacent_system_referenced` 必须为 `false`。
- **Control State 仅保存控制面位置信息**（Scope/Function/Route）；业务真相必须保存在 `Repo` 与 `Worktrack` 的正式文档中，禁止写入 Control State。
- **git hash 一致仅授权跳过重复刷新和重复文档追平**；首次验证和 Gate 裁决在任何情况下都不可跳过。

---

## 十五、资源

使用当前 `Harness Control State`、当前 Scope 所需的正式产物，以及下游技能的结构化输出作为本轮的权威依据。

判断下一次合法继续推进是否被允许时，应优先使用下游结构化输出，而不是本地叙述性摘要。

三轴参考：
- `Scope` 回答"在什么层上控制"
- `Function` 回答"控制器此刻在做什么"
- `Artifact` 回答"控制器依赖什么正式对象"

---

## 十六、结构化输出字段约定

Inside the result, include at least these fields or equivalents:

- `current_scope`
- `artifacts_read`
- `status_or_verdict`
- `allowed_next_routes`
- `recommended_next_route`
- `continuation_ready`
- `recommended_next_scope`
- `recommended_next_action`
- `continuation_decision`
- `stop_conditions_hit`
- `approval_required`
- `needs_approval`
