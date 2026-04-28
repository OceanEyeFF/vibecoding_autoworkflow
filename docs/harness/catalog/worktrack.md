---
title: "Harness Skill Catalog / WorktrackScope"
status: draft
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# WorktrackScope Skill Catalog

> 目的：固定 `WorktrackScope` 下直接面向 `Codex` 的 Harness skills catalog。

这里记录的是 worktrack 闭环里实际会被 supervisor 选择和调用的 skills，而不是再额外维持一组抽象 function 名字。

## 当前原则

- `WorktrackScope` skills 负责局部状态转移闭环
- 它们消费 `contract / plan / evidence / control state`
- 它们可以派发下游 subagent，但自身不应伪装成“控制平面 + 执行平面一体”
- `schedule-worktrack-skill` 是当前 `selected_next_action` 与 dispatch handoff packet 的唯一 authority
- `dispatch-skills` 只消费 scheduling packet，不反向改写 queue 选择
- `generic-worker-skill` 是没有更窄专用 skill 时的通用执行载体
- `doc-catch-up-worker-skill` 是 worktrack closeout 前推荐使用的文档基线追平载体
- 在 freshly seeded 或 autonomous continuation 的首个 execution-facing round，初始 slice 必须先收紧到最小可验证子片段，再允许 dispatch
- `dispatch-skills` 的 `runtime_dispatch_mode` 读取顺序：
  - `.aw/control-state.md` 的 `subagent_dispatch_mode_override_scope`
  - 默认 `worktrack-contract-primary` 下，`.aw/worktrack/contract.md` 的 `runtime_dispatch_mode` 优先
  - 只有 `global-override` 下，`.aw/control-state.md` 的 `subagent_dispatch_mode` 才作为显式覆盖
  - contract 未声明时，`.aw/control-state.md` 的 `subagent_dispatch_mode` 作为 repo 级默认值
  - host runtime 默认能力（有能力则 delegate）
- `runtime_dispatch_mode` 支持 `auto` / `delegated` / `current-carrier`，默认值为 `auto`，`auto` 需显式写出 fallback 原因

## Catalog

### 1. init-worktrack-skill

职责：

- 创建 bounded branch、初始化 baseline 和 `Worktrack Contract`
- 建立最小 `Plan / Task Queue`
- 产出面向 `schedule-worktrack-skill` 的 seed / handoff，而不是新鲜的权威 dispatch packet

主要依赖：

- `Worktrack Contract`
- `Plan / Task Queue`
- `Harness Control State`

canonical executable source：

- [../../../product/harness/skills/init-worktrack-skill/SKILL.md](../../../product/harness/skills/init-worktrack-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`

preferred initialization fields：

- `worktrack_id`
- `initial_queue_items`
- `queue_seed_status`
- `schedule_handoff_packet`
- `recommended_next_route`
- `approval_required`

### 2. schedule-worktrack-skill

职责：

- 根据当前 contract、验收条件、证据和阻塞情况刷新任务队列
- 决定当前下一动作
- 在首个 execution-facing round 优先选择最小可验证的 acceptance slice 或依赖解阻步骤，而不是直接放大成端到端包
- 显式说明当前下一动作与剩余队列如何对齐验收条件
- 产出唯一权威的 dispatch handoff packet

主要依赖：

- `Worktrack Contract`
- `Plan / Task Queue`
- `Gate Evidence`

canonical executable source：

- [../../../product/harness/skills/schedule-worktrack-skill/SKILL.md](../../../product/harness/skills/schedule-worktrack-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`

preferred scheduling fields：

- `selected_next_action_id`
- `selected_next_action`
- `slice_boundary_reason`
- `dispatch_task_brief_draft`
- `dispatch_info_packet_draft`
- `dispatch_packet_ready`
- `recommended_next_route`

### 3. dispatch-skills

职责：

- 接收当前 `Worktrack` 的下一任务
- 校验 scheduling 产出的 handoff packet
- 拒收超过单轮边界的 oversized packet，并把它退回 `schedule-worktrack-skill`
- 优先选择合适的专门 skill 或 subagent 执行方式
- 当系统中没有合适的专门 skill 时，自动 fallback 到 `generic-worker-skill` 承载的通用任务完成 `SubAgent`
- 当当前任务主要是文档追平时，优先绑定 `doc-catch-up-worker-skill`
- 按 `runtime_dispatch_mode` 选择执行载体：`auto` 在 runtime 支持且权限边界允许时优先委派，无法安全委派时必须显式记录 `runtime fallback`、权限阻塞或 `dispatch package unsafe`；`delegated` 必须真实委派，无法委派时返回运行时缺口或权限阻塞；`current-carrier` 显式关闭委派
- 跑一轮 bounded execution
- 回传 evidence 和状态结果

主要依赖：

- `Worktrack Contract`
- `Plan / Task Queue`
- `Harness Control State`
- 当前任务相关的最小上下文

dispatch contract：

- `Dispatch Task Brief`
  - `task`
  - `goal`
  - `in_scope`
  - `out_of_scope`
  - `constraints`
  - `acceptance_criteria_for_this_round`
  - `atomicity_justification`
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
  - `selection_reason`
  - `fallback_used`
  - `dispatch_packet_status`
  - `packet_boundedness_verdict`
  - `dispatch_contract_gaps`
  - `actions_taken`
  - `files_touched_or_expected`
  - `evidence_collected`
  - `open_issues`
  - `recommended_next_action`

选择规则：

- 只有在专门 skill 对当前 work item 有清晰语义贴合时，才优先绑定该 skill
- 没有清晰贴合的专门 skill 时，必须 fallback 到 `generic-worker-skill` 承载的通用任务完成 `SubAgent`
- 文档追平任务优先绑定 `doc-catch-up-worker-skill`
- fallback 不得扩大 scope，也不得绕过 `verification_requirements`
- handoff packet 缺失或不完整时，必须返回 `schedule-worktrack-skill`，而不是由 `dispatch-skills` 自己补齐
- handoff packet 如果已经膨胀成多 acceptance slices、多队列项或“整包做完”的 execution tranche，也必须返回 `schedule-worktrack-skill`

canonical executable source：

- [../../../product/harness/skills/dispatch-skills/SKILL.md](../../../product/harness/skills/dispatch-skills/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`

### 4. generic-worker-skill

职责：

- 接收限定范围 Prompt，并在当前权限边界内完成实现、修复、调查或验证任务
- 作为无专用 skill 时的通用执行载体，避免 Harness 主控制器吸收执行责任
- 返回执行报告、触及文件、验证结果和残留风险

主要依赖：

- `Dispatch Task Brief`
- `Dispatch Info Packet`
- 当前任务相关的最小上下文

canonical executable source：

- [../../../product/harness/skills/generic-worker-skill/SKILL.md](../../../product/harness/skills/generic-worker-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`

### 5. doc-catch-up-worker-skill

职责：

- 将已验证实现事实追平到正确长期文档层
- 清理旧路径、旧数量、旧命令、旧流程和旧边界描述
- 在 closeout 前降低后续开发引用过期上下文的风险

主要依赖：

- 当前 diff 与验证证据
- `docs/project-maintenance/`
- `docs/harness/`
- 相关入口页和承接层正文

canonical executable source：

- [../../../product/harness/skills/doc-catch-up-worker-skill/SKILL.md](../../../product/harness/skills/doc-catch-up-worker-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`

### 6. review-evidence-skill

职责：

- 汇总 code review、静态检查和结构评估结果
- 形成 review lane envelope，供 gate 汇总
- 对低严重度噪声做截断，并把重复症状标成可能的上游约束问题

主要依赖：

- `Gate Evidence`

canonical executable source：

- [../../../product/harness/skills/review-evidence-skill/SKILL.md](../../../product/harness/skills/review-evidence-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`

preferred review-lane fields：

- `lane_id`
- `freshness`
- `lane_verdict`
- `confidence_reason`
- `low_severity_absorption_applied`
- `ready_for_gate`

### 7. test-evidence-skill

职责：

- 汇总测试执行结果与验收条件覆盖情况
- 形成 validation lane envelope

主要依赖：

- `Gate Evidence`
- `Worktrack Contract`

canonical executable source：

- [../../../product/harness/skills/test-evidence-skill/SKILL.md](../../../product/harness/skills/test-evidence-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`

preferred validation-lane fields：

- `lane_id`
- `freshness`
- `lane_verdict`
- `confidence`
- `confidence_reason`
- `ready_for_gate`

### 8. rule-check-skill

职责：

- 检查项目规则、边界和治理约束
- 形成 policy 证据面

主要依赖：

- `Gate Evidence`
- repo governance rules

canonical executable source：

- [../../../product/harness/skills/rule-check-skill/SKILL.md](../../../product/harness/skills/rule-check-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`

### 9. gate-skill

职责：

- 汇总 review / test lane envelopes，并兼容 `policy` 旧入口
- 生成当前 round 的 gate verdict
- 吸收低严重度 residual risks，并在命中上游约束信号时强制改道路由

主要依赖：

- `Gate Evidence`

canonical executable source：

- [../../../product/harness/skills/gate-skill/SKILL.md](../../../product/harness/skills/gate-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`

preferred gate fields：

- `required_evidence_lanes`
- `evidence_lanes`
- `overall_confidence`
- `freshness_blockers`
- `allowed_next_routes`
- `recommended_next_route`

### 10. recover-worktrack-skill

职责：

- 在 gate fail 或 blocked 时，选择重试、回滚、拆分或刷新 baseline

主要依赖：

- `Gate Evidence`
- `Plan / Task Queue`
- `Harness Control State`

canonical executable source：

- [../../../product/harness/skills/recover-worktrack-skill/SKILL.md](../../../product/harness/skills/recover-worktrack-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`

### 11. close-worktrack-skill

职责：

- 处理 `PR -> merge -> cleanup -> repo refresh handoff`
- 明确 closeout 后的下一层级动作

主要依赖：

- `Gate Evidence`
- `Harness Control State`

canonical executable source：

- [../../../product/harness/skills/close-worktrack-skill/SKILL.md](../../../product/harness/skills/close-worktrack-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`
