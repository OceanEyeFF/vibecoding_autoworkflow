---
title: "First-Wave Skill Freeze"
status: active
updated: 2026-04-22
owner: aw-kernel
last_verified: 2026-04-22
---
# First-Wave Skill Freeze

> 目的：冻结首发 skill 产品化范围，作为后续 payload contract、模板初始化、`agents` payload 与 deploy/verify 阶段的前瞻性实现约束；它不描述当前 deploy 脚本已经具备的行为。

本页属于 [Deploy Runbooks](./README.md) 系列文档。

阅读本页前，建议先看：

- [Deploy Mapping Spec](./deploy-mapping-spec.md)
- [Template Consumption Spec](./template-consumption-spec.md)
- [Skill 生命周期维护](./skill-lifecycle.md)

## 一、范围

本冻结只回答三个问题：

- 首发要产品化哪些 canonical skills（规范 skill）
- 当前哪些 skills 明确不进入首发
- 首发链路在什么边界停止，不把后续实现假设提前写死

本页不定义：

- payload descriptor schema
- `.aw_template` 初始化脚本
- backend payload 文件形态
- deploy 脚本如何读取 payload descriptor
- 第二批 skill 的排期承诺

本页也不重写 canonical skill 本体合同。
如果 canonical skill 当前允许更多分支，本页只定义首发实现阶段实际需要承接的子集。

## 二、冻结原则

首发 skill 子集必须满足下面四条：

- 能覆盖 `canonical skill -> adapter payload（适配器载荷） -> deploy target -> verify / contract smoke（验证与合同冒烟）` 的完整主链路
- 覆盖 supervisor、`RepoScope`（仓库作用域） 全算子集（Observe / Decide / Close / ChangeGoal）、`WorktrackScope`（工作追踪作用域） 全算子集（Init / Observe / Decide / Dispatch / Verify / Judge / Recover / Close）
- 验证、gate 判定、恢复与收尾链路已进入首发，作为完整控制回路的必要组成
- 所有 canonical skills 均具备 adapter payload 与 deploy target 支持

因此，首发冻结到"完整 Harness 控制回路可运行"为止，覆盖从 repo judgment 到 worktrack 全生命周期再到 handback 的最小闭环。

## 三、首发 skill 子集

当前首发范围固定为以下十六个 canonical skills（规范 skill）：

**RepoScope（仓库作用域）**
- `set-harness-goal-skill`
- `repo-status-skill`
- `repo-whats-next-skill`
- `repo-refresh-skill`
- `repo-change-goal-skill`

**WorktrackScope（工作追踪作用域）**
- `init-worktrack-skill`
- `worktrack-status-skill`
- `schedule-worktrack-skill`
- `dispatch-skills`
- `review-evidence-skill`
- `test-evidence-skill`
- `rule-check-skill`
- `gate-skill`
- `recover-worktrack-skill`
- `close-worktrack-skill`

**Supervisor（监督器）**
- `harness-skill`

各自承担的最小角色如下：

- `harness-skill`
  - 顶层 supervisor 入口
  - 负责识别当前层级并在未命中 formal stop condition 前继续推进合法状态转移
- `set-harness-goal-skill`
  - `RepoScope.SetGoal`
  - 在 `.aw/` 未初始化时，将用户自然语言需求转化为结构化的 `Goal Charter`、`Control State` 和 `Repo Snapshot`
  - 设置默认 autonomy 策略（小步推进、逐层验证）
  - 需要用户确认后才写入文件
- `repo-status-skill`
  - `RepoScope.Observe`
  - 为 repo 级判断提供最小 repo baseline（仓库基线状态）
- `repo-whats-next-skill`
  - `RepoScope.Decide`
  - repo 级 next-direction（下一步方向） 判断入口，输出 `enter-worktrack` / `hold-and-observe`
  - `refresh-repo-state` 保留为标准动作，但在首发中标记为 `范围外`
- `repo-refresh-skill`
  - `RepoScope.Close`
  - worktrack 完成后刷新 repo 级状态快照与 control-state
- `repo-change-goal-skill`
  - `RepoScope.ChangeGoal`（参考信号设定层，在常规循环外）
  - 由外部目标变更请求触发，不是 `Decide` 的常规选项
  - 处理目标级变更请求，分析影响、生成草案，用户确认后直接改写 `Goal Charter`
  - 设定/重设完成后才启动（或重新启动）常规循环
- `init-worktrack-skill`
  - `WorktrackScope.Init`
  - 建立 branch、baseline、`Worktrack Contract`（工作追踪契约） 与初始 `Plan / Task Queue`（计划与任务队列）
- `worktrack-status-skill`
  - `WorktrackScope.Observe`
  - 在 worktrack 执行过程中提供状态估计，供后续 Decide / Dispatch / Verify 使用
- `schedule-worktrack-skill`
  - `WorktrackScope.Decide`
  - 刷新当前 `Plan / Task Queue`，选出 `current next action`，形成交给 `dispatch-skills` 的最小 handoff
- `dispatch-skills`
  - `WorktrackScope.Dispatch`
  - 把当前 work item 绑定到 execution carrier（执行载体），包括 specialized downstream skills 与 fallback / general executor 路径
- `review-evidence-skill`
  - `WorktrackScope.Verify`（implementation lane）
  - 审查实现层证据：代码变更、设计一致性、约定遵循
- `test-evidence-skill`
  - `WorktrackScope.Verify`（validation lane）
  - 验证测试层证据：测试覆盖、验收标准满足度、回归安全
- `rule-check-skill`
  - `WorktrackScope.Verify`（policy lane）
  - 检查策略层证据：编码规范、安全规则、架构约束
- `gate-skill`
  - `WorktrackScope.Judge`
  - 基于三维度证据做关卡判定：通过 / 软失败 / 硬失败 / 阻塞
- `recover-worktrack-skill`
  - `WorktrackScope.Recover`
  - 在 worktrack 偏离或失败后执行恢复：修复、重试、重新定界或终止
- `close-worktrack-skill`
  - `WorktrackScope.Close`
  - 完成 worktrack 收尾：证据归档、约定更新、状态切换、repo handback

## 四、首发实际承接的 canonical 分支子集

首发不会重写 canonical skill 合同，但会把真正需要落地的可达分支收窄为下面这个子集：

- `set-harness-goal-skill`
  - 首发必须承接：
    - 检查 `.aw/` 和 `goal-charter.md` 是否存在
    - 将用户需求转化为结构化 `Goal Charter`
    - 生成初始 `Control State`（含默认 autonomy 参数）
    - 生成初始 `Repo Snapshot`
    - 等待用户确认后写入文件
  - 首发明确不承接：
    - 覆盖已存在的 `goal-charter.md`
    - 代替用户做目标级决策
- `repo-whats-next-skill`
  - 首发必须承接：
    - `enter-worktrack`
    - `hold-and-observe`
  - 首发标记为 `范围外`（标准技能支持但不部署）：
    - `refresh-repo-state`
- `repo-refresh-skill`
  - 首发必须承接：
    - worktrack 完成后刷新 repo 状态快照
    - 更新 control-state 中的 handoff 标记与 autonomy ledger
- `repo-change-goal-skill`
  - 首发必须承接：
    - 接收并分析目标变更请求
    - 输出目标变更分析报告（变更幅度、影响面、建议决策）
    - 生成可直接写入的 `goal-charter` 草案
    - 用户确认后执行对 `goal-charter.md`、`repo/snapshot-status.md`、`control-state.md` 的改写
  - 首发明确不承接：
    - 在用户确认前直接改写文件
    - 代替程序员做目标级决策
- `init-worktrack-skill`
  - 首发必须承接：
    - branch / baseline / contract / initial queue 的建立
    - 一个可继续进入 `schedule-worktrack-skill` 的最小初始化结果
- `worktrack-status-skill`
  - 首发必须承接：
    - 在 worktrack 执行轮次中读取当前 worktrack 产物与 repo 状态
    - 输出结构化的 `WorktrackStateEstimate`
- `schedule-worktrack-skill`
  - 首发必须承接：
    - 从当前 `Plan / Task Queue` 中刷新队列状态
    - 选出一个 `current next action`
    - 为 `dispatch-skills` 形成最小 handoff
  - 首发明确不承接：
    - 基于验证 / gate / recovery 证据重建整个 worktrack 策略（由 `recover-worktrack-skill` 承接）
- `dispatch-skills`
  - 首发必须承接：
    - bounded dispatch contract 的组装
    - specialized downstream skills 路径与 fallback / general executor 路径
- `review-evidence-skill`
  - 首发必须承接：
    - 实现层证据的审查与汇总
    - 输出 implementation evidence 报告
- `test-evidence-skill`
  - 首发必须承接：
    - 测试层证据的验证与汇总
    - 输出 validation evidence 报告
- `rule-check-skill`
  - 首发必须承接：
    - 策略层规则的检查与汇总
    - 输出 policy evidence 报告
- `gate-skill`
  - 首发必须承接：
    - 接收三维度证据并做综合判定
    - 输出 gate 报告（通过 / 软失败 / 硬失败 / 阻塞）与允许的下一路由
- `recover-worktrack-skill`
  - 首发必须承接：
    - 分析 worktrack 偏离原因
    - 输出恢复选项（修复 / 重试 / 重新定界 / 终止）
- `close-worktrack-skill`
  - 首发必须承接：
    - worktrack 收尾：证据归档、约定更新、状态切换
    - 返回 repo handback 与 autonomy ledger 更新

如果当前 canonical skill 合同允许更宽的动作空间，应继续保留在 canonical source 中；只是这些分支不进入当前首发实现闭环。

这里的“只是不进入首发实现闭环”不应停留在 adapter metadata。因为当前 `agents` first-wave payload 会直接复制 canonical `SKILL.md`，所以首发收窄必须在被复制的 skill prompt surface 上也明确可见，否则首发运行轮次仍可能产出超出冻结子集的路线。

## 五、首发停止边界

当前 `agents` first-wave deploy / contract smoke 覆盖完整 Harness 控制回路：

- `RepoScope` 全算子：Observe -> Decide -> Close / ChangeGoal
- `WorktrackScope` 全算子：Init -> Observe -> Decide -> Dispatch -> Verify (implementation / validation / policy) -> Judge -> Recover / Close
- repo handback 与 autonomy ledger 更新

当前首发不承诺的能力：

- runtime-level `SubAgent` dispatch（子代理派发） 真正落地（仅证明 skill -> dispatch contract 组装可读）
- 多 worktrack 的 autonomous continuation 的完整证明（仅证明单 worktrack 生命周期内状态机可读）
- stop/continue policy 在复杂场景下的 autonomy repair 完整覆盖

当前更准确的解释是：

- 这批首发 deploy / contract smoke 证明完整 skill contract、payload copy 和全 route 可读
- `contract smoke` 只能作为 deploy / verify 侧的最小合同证明；skills 的测试不能用简单 smoke test 代替，也不能据此判定 skill 行为已经被充分验证
- 它不是 live runtime test，也不是 Harness acceptance test
- 它证明了完整控制回路的"结构可读"，但不证明"运行时正确"

## 七、对后续任务包的约束

本冻结对后续任务包施加以下约束：

- payload contract 为全部十六个首发 skills 提供自描述读取面
- 模板初始化支持所有首发链路需要的模板初始化（contract、plan-task-queue、gate-evidence、goal-change-request）
- `agents` payload 为全部十六个 skills 准备可追踪 payload，覆盖 `dispatch-skills` 的 specialized downstream skills 路径与 fallback / general executor 路径
- deploy / verify 让 `prune --all`、`check_paths_exist`、`install --backend agents` 与 `verify` 能处理完整 skill 树
- 对 `repo-whats-next-skill`，首发 payload / copied skill surface / contract smoke 看到的有效 repo action 子集必须一致：metadata、skill prompt 与 runtime 行为对齐

## 八、验收标准

本冻结完成后，至少应满足：

- 首发 canonical skill（规范 skill） 子集有唯一、可引用的正式清单（共16个）
- 全部 skills 具备 adapter payload 与 deploy target 支持
- 首发支持的 repo / worktrack 全算子分支是明确的，不会与 canonical 全量动作空间混淆
- 后续实现文档和脚本可直接引用本页确定首发 skill 范围与支持子路径，无需重复讨论
- `agents` 首发 contract smoke 证明全部十六个 skills 的最小可读、完整控制回路 route 可读，以及 specialized + fallback dispatch 路径
