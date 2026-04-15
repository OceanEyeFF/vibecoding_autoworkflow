---
title: "Harness Skill Catalog / WorktrackScope"
status: draft
updated: 2026-04-15
owner: aw-kernel
last_verified: 2026-04-15
---
# WorktrackScope Skill Catalog

> 目的：固定 `WorktrackScope` 下直接面向 `Codex` 的 Harness skills catalog。

这里记录的是 worktrack 闭环里实际会被 supervisor 选择和调用的 skills，而不是再额外维持一组抽象 function 名字。

## 当前原则

- `WorktrackScope` skills 负责局部状态转移闭环
- 它们消费 `contract / plan / evidence / control state`
- 它们可以派发下游 subagent，但自身不应伪装成“控制平面 + 执行平面一体”

## Catalog

### 1. init-worktrack-skill

职责：

- 初始化 branch、baseline 和 `Worktrack Contract`
- 建立最小 `Plan / Task Queue`

主要依赖：

- `Worktrack Contract`
- `Plan / Task Queue`
- `Harness Control State`

canonical executable source：

- [../../../../product/harness/skills/init-worktrack-skill/SKILL.md](../../../../product/harness/skills/init-worktrack-skill/SKILL.md)
- [../../../../product/harness/skills/init-worktrack-skill/references/entrypoints.md](../../../../product/harness/skills/init-worktrack-skill/references/entrypoints.md)

当前状态：

- `initial canonical executable skeleton landed`

### 2. schedule-worktrack-skill

职责：

- 根据当前 contract、证据和阻塞情况刷新任务队列
- 决定当前下一动作

主要依赖：

- `Worktrack Contract`
- `Plan / Task Queue`
- `Gate Evidence`

canonical executable source：

- [../../../../product/harness/skills/schedule-worktrack-skill/SKILL.md](../../../../product/harness/skills/schedule-worktrack-skill/SKILL.md)
- [../../../../product/harness/skills/schedule-worktrack-skill/references/entrypoints.md](../../../../product/harness/skills/schedule-worktrack-skill/references/entrypoints.md)

当前状态：

- `initial canonical executable skeleton landed`

### 3. dispatch-skills

职责：

- 接收当前 `Worktrack` 的下一任务
- 组装 bounded task 和最小信息包
- 优先选择合适的专门 skill 或 subagent 执行方式
- 当系统中没有合适的专门 skill 时，自动 fallback 到通用任务完成 `SubAgent`
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
  - `verification_requirements`
  - `done_signal`
- `Dispatch Info Packet`
  - `current_worktrack_state`
  - `relevant_artifacts`
  - `required_context`
  - `known_risks`
  - `executor_candidates`
  - `fallback_reason`
- `Dispatch Result`
  - `selected_executor`
  - `selection_reason`
  - `fallback_used`
  - `actions_taken`
  - `files_touched_or_expected`
  - `evidence_collected`
  - `open_issues`
  - `recommended_next_action`

选择规则：

- 只有在专门 skill 对当前 work item 有清晰语义贴合时，才优先绑定该 skill
- 没有清晰贴合的专门 skill 时，必须 fallback 到通用任务完成 `SubAgent`
- fallback 不得扩大 scope，也不得绕过 `verification_requirements`

canonical executable source：

- [../../../../product/harness/skills/dispatch-skills/SKILL.md](../../../../product/harness/skills/dispatch-skills/SKILL.md)
- [../../../../product/harness/skills/dispatch-skills/references/entrypoints.md](../../../../product/harness/skills/dispatch-skills/references/entrypoints.md)

当前状态：

- `initial canonical executable skeleton landed`

### 4. review-evidence-skill

职责：

- 汇总 code review、静态检查和结构评估结果
- 形成 review 证据面

主要依赖：

- `Gate Evidence`

canonical executable source：

- [../../../../product/harness/skills/review-evidence-skill/SKILL.md](../../../../product/harness/skills/review-evidence-skill/SKILL.md)
- [../../../../product/harness/skills/review-evidence-skill/references/entrypoints.md](../../../../product/harness/skills/review-evidence-skill/references/entrypoints.md)

当前状态：

- `initial canonical executable skeleton landed`

### 5. test-evidence-skill

职责：

- 汇总测试执行结果与验收条件覆盖情况
- 形成 validation 证据面

主要依赖：

- `Gate Evidence`
- `Worktrack Contract`

canonical executable source：

- [../../../../product/harness/skills/test-evidence-skill/SKILL.md](../../../../product/harness/skills/test-evidence-skill/SKILL.md)
- [../../../../product/harness/skills/test-evidence-skill/references/entrypoints.md](../../../../product/harness/skills/test-evidence-skill/references/entrypoints.md)

当前状态：

- `initial canonical executable skeleton landed`

### 6. rule-check-skill

职责：

- 检查项目规则、边界和治理约束
- 形成 policy 证据面

主要依赖：

- `Gate Evidence`
- repo governance rules

canonical executable source：

- [../../../../product/harness/skills/rule-check-skill/SKILL.md](../../../../product/harness/skills/rule-check-skill/SKILL.md)
- [../../../../product/harness/skills/rule-check-skill/references/entrypoints.md](../../../../product/harness/skills/rule-check-skill/references/entrypoints.md)

当前状态：

- `initial canonical executable skeleton landed`

### 7. gate-skill

职责：

- 汇总 implementation / validation / policy 三类证据
- 生成当前 round 的 gate verdict

主要依赖：

- `Gate Evidence`

canonical executable source：

- [../../../../product/harness/skills/gate-skill/SKILL.md](../../../../product/harness/skills/gate-skill/SKILL.md)
- [../../../../product/harness/skills/gate-skill/references/entrypoints.md](../../../../product/harness/skills/gate-skill/references/entrypoints.md)

当前状态：

- `initial canonical executable skeleton landed`

### 8. recover-worktrack-skill

职责：

- 在 gate fail 或 blocked 时，选择重试、回滚、拆分或刷新 baseline

主要依赖：

- `Gate Evidence`
- `Plan / Task Queue`
- `Harness Control State`

canonical executable source：

- [../../../../product/harness/skills/recover-worktrack-skill/SKILL.md](../../../../product/harness/skills/recover-worktrack-skill/SKILL.md)
- [../../../../product/harness/skills/recover-worktrack-skill/references/entrypoints.md](../../../../product/harness/skills/recover-worktrack-skill/references/entrypoints.md)

当前状态：

- `initial canonical executable skeleton landed`

### 9. close-worktrack-skill

职责：

- 处理 `PR -> merge -> cleanup -> repo refresh handoff`
- 明确 closeout 后的下一层级动作

主要依赖：

- `Gate Evidence`
- `Harness Control State`

canonical executable source：

- [../../../../product/harness/skills/close-worktrack-skill/SKILL.md](../../../../product/harness/skills/close-worktrack-skill/SKILL.md)
- [../../../../product/harness/skills/close-worktrack-skill/references/entrypoints.md](../../../../product/harness/skills/close-worktrack-skill/references/entrypoints.md)

当前状态：

- `initial canonical executable skeleton landed`
