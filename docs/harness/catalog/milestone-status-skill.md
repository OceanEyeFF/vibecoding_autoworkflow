---
title: "Milestone Status Skill"
status: active
updated: 2026-05-10
owner: aw-kernel
last_verified: 2026-05-10
---

# Milestone Status Skill

> 独立 Milestone 分析 skill。它是 RepoScope 下的聚合观测/验收分析器，不选择下一 Worktrack、不初始化 worktrack、不修改 version/release 状态。

## 定位

- Scope: `RepoScope`
- Function: 作为 `RepoScope.Observe` 的 sensor/analyzer
- 输入: Milestone artifact + 已关闭/待办 worktrack + 聚合 evidence
- 输出: milestone progress + acceptance verdict + handback_required + release/version consideration hint + developer decision boundary

## 职责

- 读取 Milestone artifact 和关联的 worktrack 状态
- 计算 progress counter
- 执行双重验收检查（worktrack_list_finished + purpose_achieved）
- 标记是否触发 Milestone 验收边界（影响 continuous execution 是否 handback）
- 给出 release/version consideration hint（不接管 decision）
- 明确 developer decision boundary

## 非职责

- 不选择下一 Worktrack
- 不初始化 worktrack
- 不修改 version/release 状态
- 不替代 gate-skill 的 verdict
- 不膨胀 harness-skill（harness-skill 继续只做 supervisor）

## 输入

| 输入 | 来源 | 说明 |
|------|------|------|
| Milestone artifact | `.aw/milestone/{milestone_id}.md` | 当前 active Milestone |
| Milestone backlog | `.aw/repo/milestone-backlog.md` | Pipeline 全集，获取前置依赖状态和下一个候选 milestone |
| Worktrack backlog | `.aw/repo/worktrack-backlog.md` | 已关闭和待办 worktrack；按 milestone_id 过滤；缺失视为空 backlog，存在但损坏或不可解析时必须停止 |
| Gate evidence | `.aw/worktrack/gate-evidence.md` | 最近关闭 worktrack 的 evidence |
| Repo snapshot | `.aw/repo/snapshot-status.md` | 当前 repo 状态 |

## 输出

| 字段 | 类型 | 说明 |
|------|------|------|
| milestone_id | string | 分析的 Milestone |
| milestone_status | enum | planned / active / completed / superseded |
| progress | object | total / completed / blocked / deferred / completion_pct |
| worktrack_list_finished | boolean | 声明的 worktrack 列表是否全部处理 |
| purpose_achieved | boolean | 目的是否经聚合 evidence 证明达成 |
| milestone_acceptance_verdict | enum | achieved / not_achieved / blocked / deferred |
| handback_required | boolean | 是否触发 Milestone 验收边界 |
| proceed_blockers | array | 阻止推进的因素列表 |
| milestone_input_checkpoint | string | 本次分析输入指纹，格式为 `sha256:<64 位小写 hex>`，供 harness-skill 写回 control-state 用于幂等性对比 |
| release_version_consideration | string | 对 version/release 的提示 |
| developer_decisions_needed | array | 需要 developer 做出的决定 |
| recommendations | array | 对 RepoScope.Decide 的建议 |
| pipeline_advancement | string | 若当前 milestone achieved，推荐激活的下一个 milestone_id |
| pipeline_state | object | Pipeline 快照（planned/active/completed/superseded 计数） |

## Checkpoint 合同

`milestone_input_checkpoint` 使用 `milestone-input-checkpoint/v1` 算法：从 milestone artifact、worktrack backlog、gate evidence 与 repo snapshot 提取会影响 progress counter 或 `purpose_achieved` 的关键字段，构造键排序的 UTF-8 JSON payload 后计算 SHA-256。路径一律使用 repo-relative POSIX path；缺失的 backlog 以 `state: missing` 和空 entries 表示；存在但损坏、不可读或不可解析的 backlog 不允许产出 partial checkpoint，必须作为 `proceed_blockers` 返回。

纳入字段至少覆盖 milestone 的 `milestone_id`、`status`、`worktrack_list`、`completion_signals`、`acceptance_criteria`、`depends_on_milestones`、`aggregated_evidence`；backlog 中按 `worktrack_id` 去重后的最新有效条目及归一化状态；gate evidence 中的 verdict、review/validation/policy 维度结论、absorbed issues 与 freshness / missing 状态；repo snapshot 中的 baseline/checkpoint/governance/risk 关键信号。不得纳入文件 mtime、分析时间戳、绝对路径、上次 checkpoint 或 progress counter。

每次 RepoScope.Observe 至少重算输入指纹；只有新指纹等于 control-state 中已有的 `milestone_input_checkpoint`，且 `latest_observed_checkpoint` 等于当前 git HEAD 时，才允许跳过 Milestone 进度和 evidence 聚合的完整重算。

## 调用时机

- `RepoScope.Observe` 阶段（harness-skill 在状态估计时调用）
- Worktrack closeout 后（repo-refresh 完成后检查 Milestone 进度）
- Milestone 验收边界触发时（判定 handback 或 pipeline 推进）
- programmer 显式请求 Milestone 状态检查
