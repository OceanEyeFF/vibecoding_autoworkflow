---
title: "First-Wave Skill Freeze"
status: active
updated: 2026-04-19
owner: aw-kernel
last_verified: 2026-04-19
---
# First-Wave Skill Freeze

> 目的：冻结首发 skill 产品化范围，作为后续 B1（`manifest` 阶段）、B2（模板初始化阶段）、B3（`agents` payload 阶段）、B4（deploy/verify 阶段）的前瞻性实现约束；它不描述当前 deploy 脚本已经具备的行为。

本页属于 [Deploy Runbooks](./README.md) 系列文档。

阅读本页前，建议先看：

- [Deploy Mapping Spec](./deploy-mapping-spec.md)
- [Template Consumption Spec](./template-consumption-spec.md)
- [Skill 生命周期维护](./skill-lifecycle.md)

## 一、范围

本冻结只回答三个问题：

- 首发要产品化哪些 canonical skills（规范 skill）
- 当前哪些 skills 明确不进入首发
- 首发链路在什么边界停止，不把 B1 之后的实现假设提前写死

本页不定义：

- `manifest` schema
- `.aw_template` 初始化脚本
- backend payload 文件形态
- deploy 脚本如何读取 `manifest`
- 第二批 skill 的排期承诺

本页也不重写 canonical skill 本体合同。
如果 canonical skill 当前允许更多分支，本页只定义首发实现阶段实际需要承接的子集。

## 二、冻结原则

首发 skill 子集必须满足下面四条：

- 能覆盖 `canonical skill -> adapter payload（适配器载荷） -> deploy target -> verify / contract smoke（验证与合同冒烟）` 的最小主链路
- 优先覆盖 supervisor、`RepoScope`（仓库作用域） 判断、`Worktrack`（工作追踪单元） 初始化与 dispatch，不提前进入验证、gate 判定、恢复与收尾
- 依赖关系尽量短，避免 B1-B4 一开始就承接整棵 skill 树
- 不把当前未稳定的 owner 模板、closeout（收尾） 流程或 recovery（恢复） 策略一起产品化

因此，首发只冻结到“能把一条最小 worktrack（工作追踪单元） 启动并交给执行载体”为止。

## 三、首发 skill 子集

当前首发范围固定为以下五个 canonical skills（规范 skill）：

- `harness-skill`
- `repo-status-skill`
- `repo-whats-next-skill`
- `init-worktrack-skill`
- `dispatch-skills`

各自承担的最小角色如下：

- `harness-skill`
  - 顶层 supervisor 入口
  - 负责识别当前层级并在未命中 formal stop condition 前继续推进合法状态转移
- `repo-status-skill`
  - `RepoScope`（仓库作用域） 的状态观察入口
  - 为下一步判断提供最小 repo baseline（仓库基线状态）
- `repo-whats-next-skill`
  - `RepoScope`（仓库作用域） 的 next-direction（下一步方向） 判断入口
  - 在首发里只产品化 `enter-worktrack` 与 `hold-and-observe` 两条输出分支
- `init-worktrack-skill`
  - 建立 branch、baseline、`Worktrack Contract`（工作追踪契约） 与初始 `Plan / Task Queue`（计划与任务队列）
  - 在首发里只覆盖“初始化后首个任务可直接 dispatch”的最小场景，不承接队列重排
- `dispatch-skills`
  - 把当前 work item 绑定到 execution carrier（执行载体）
  - 在首发里只要求证明 fallback / general executor（通用执行器） 路径，不要求同步产品化下游 specialized skill（专用 skill） 包装

## 四、首发实际承接的 canonical 分支子集

首发不会重写 canonical skill 合同，但会把真正需要落地的可达分支收窄为下面这个子集：

- `repo-whats-next-skill`
  - 首发必须承接：
    - `enter-worktrack`
    - `hold-and-observe`
  - 首发明确不承接：
    - `goal-change-control`
    - `refresh-repo-state`
- `init-worktrack-skill`
  - 首发必须承接：
    - branch / baseline / contract / initial queue 的建立
    - 一个可直接交给 `dispatch-skills` 的首任务 handoff
  - 首发明确不承接：
    - 初始化后的队列重排
    - 基于新证据重新选择 current next action
- `dispatch-skills`
  - 首发必须承接：
    - bounded dispatch contract 的组装
    - fallback / general executor 路径
  - 首发明确不承接：
    - 以 specialized downstream skills 为主的 dispatch packaging 完整覆盖

如果当前 canonical skill 合同允许更宽的动作空间，应继续保留在 canonical source 中；只是这些分支不进入首发 B1-B4 的实现闭环。

## 五、首发停止边界

当前 `agents` first-wave deploy / contract smoke 的最小合同链路止于 `dispatch-skills`，当前不把下面这些能力纳入已落地 deploy 闭环：

- review evidence 汇总
- test evidence 汇总
- rule / governance evidence 汇总
- gate adjudication（门槛裁决/准入判定）
- recovery choice（恢复策略选择）
- closeout（收尾） / merge（合并） / cleanup（清理） / repo refresh（仓库刷新）
- `schedule-worktrack-skill` 驱动的队列刷新与 current-next-action 重选

这意味着当前首发 deploy 目标不是“完整 Worktrack 生命周期产品化”，而是“先把最小 supervisor -> repo judgment（仓库判断） -> worktrack init -> direct-dispatch 主链路产品化”。

但这不应被误读为：

- `Harness` 的 canonical protocol 本体只支持单回合停机
- 现有 first-wave contract smoke 已经证明 autonomous continuation（自主连续推进）
- 现有 first-wave dispatch 已经证明 runtime-level `SubAgent` dispatch（子代理派发） 真正落地

当前更准确的解释是：

- 这批首发 deploy / contract smoke 只证明最小 skill contract、payload copy 和 bounded route 可读
- 它不是 live runtime test，也不是 Harness acceptance test
- 它没有完成 `stop/continue policy` 的 autonomy repair
- 它也没有完成 `skill -> subagent dispatch shell` 的 runtime repair

## 六、不进入首发的 skills

当前仓库里其余已存在的 canonical skills（规范 skill），全部不进入首发范围：

- `goal-change-control-skill`
- `repo-refresh-skill`
- `schedule-worktrack-skill`
- `review-evidence-skill`
- `test-evidence-skill`
- `rule-check-skill`
- `gate-skill`
- `recover-worktrack-skill`
- `close-worktrack-skill`

其中可按两类理解：

- 明确延后到首发之后再接入的验证、恢复与收尾链路：
  - `review-evidence-skill`
  - `test-evidence-skill`
  - `rule-check-skill`
  - `gate-skill`
  - `recover-worktrack-skill`
  - `close-worktrack-skill`
- 当前先不纳入首发产品化面的补充性 `RepoScope`（仓库作用域） / `WorktrackScope`（工作追踪作用域） 能力：
  - `goal-change-control-skill`
  - `repo-refresh-skill`
  - `schedule-worktrack-skill`

这些 skill 仍保留为 canonical source（规范来源），但在 B1-B4 中不应被视为必须同时落地的首发对象。

其中 `schedule-worktrack-skill` 需要单独说明：

- canonical workflow 仍然保留“schedule 后再 dispatch”的完整边界
- 首发只是先收窄为“`init-worktrack-skill` 种下的首任务可直接 dispatch”的特例
- 这不构成对 `schedule-worktrack-skill` canonical 角色的删除或改写
- 如果后续要把 Harness 修到“默认连续推进，只在 formal stop condition 停下”，则 `schedule-worktrack-skill` 需要回到 autonomy repair 的主链上，而不能长期停留在 deploy 外

## 七、对后续任务包的约束

本冻结对后续任务包施加以下约束：

- B1 只需要为上述五个首发 skills 提供最小 `manifest` 读取接口
- B2 只需要支持首发链路真正需要的最小模板初始化，不为全 skill 树做通用 orchestrator（编排器）
- B3 只需要在 `agents` backend 下为这五个 skills 准备可追踪 payload，并覆盖 `dispatch-skills` 的 fallback / general executor 路径
- B4 只需要让 `prune --all`、`check_paths_exist`、`install --backend agents` 与 `verify` 能处理首发 skill 子集与上述支持分支，不为暂缓 skill 预留复杂分支

禁止的范围扩大方式：

- 禁止因目录已存在 skeleton（骨架/雏形） 而将全部 skills 一次性纳入 `manifest`
- 禁止以 verify 迟早要做为由，提前把 gate / recover / closeout 链路纳入首发
- 禁止以 `RepoScope` 未来可能使用为由，将 `goal-change-control`、`repo-refresh` 或 `schedule-worktrack` 一并产品化
- 禁止把 `repo-whats-next-skill` 当前 canonical 可输出的全部动作，都默认视为首发必须处理的 deploy 分支
- 禁止把 `dispatch-skills` 的 specialized-skill 全覆盖，当作首发 contract smoke 的必要条件

## 八、验收标准

本冻结完成后，至少应满足：

- 首发 canonical skill（规范 skill） 子集有唯一、可引用的正式清单
- 首发外 skills 有明确的非目标边界，不再默认进入 B1-B4
- 首发支持的 repo / worktrack / dispatch 分支子集是明确的，不会与 canonical 全量动作空间混淆
- 后续实现文档和脚本可直接引用本页确定首发 skill 范围与支持子路径，无需重复讨论
- `agents` 首发 contract smoke 只需证明这五个 skills 的最小可读、`enter-worktrack` / `hold-and-observe` 子集，以及 direct-dispatch + fallback 路径，不承担完整生命周期验证
