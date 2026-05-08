---
name: milestone-status-skill
description: 当 Harness 处于 RepoScope 且需要分析当前活跃 Milestone 的进度、验收状态和是否触发 handback 边界时使用这个技能；它是 RepoScope.Observe 的传感器/分析器，不选择下一 Worktrack、不初始化 worktrack、不修改 version/release 状态。
---

# Milestone 状态技能

## 概览

把这个技能作为 `Codex` 中 `RepoScope` 下的 Milestone 聚合观测/验收分析器使用。

本技能实现 `RepoScope.Observe` 状态的 Milestone 维度传感器算子，对应 Harness 控制回路中状态估计阶段的 Milestone 专项分析。它是控制回路的 **Milestone 传感器/分析器**层：通过读取当前活跃 Milestone artifact、worktrack backlog、gate evidence 和 repo snapshot 等输入，执行 Milestone 级双重验收检查（`worktrack_list_finished` + `purpose_achieved`），产出结构化的 Milestone 进度报告、验收判决和 developer 决策边界。

它的角色是**分析 Milestone 状态**，而不是驱动 next action。它产出的是经过聚合计算的 Milestone 观测结果，供 `RepoScope.Decide` 算子（如 repo-whats-next-skill）和 `harness-skill` 的 continuous execution 判断使用。

它的主要观测依据是 Milestone 级产物和工作追踪边界证据：

- 当前活跃 Milestone artifact（`.aw/milestone/{milestone_id}.md`）
- Worktrack backlog（`.aw/repo/worktrack-backlog.md`）
- Gate evidence（`.aw/worktrack/gate-evidence.md`）
- Repo snapshot（`.aw/repo/snapshot-status.md`）

本技能对 `.aw/worktrack/*` 的唯一合法行为是读取为边界证据；更新或重写 `.aw/worktrack/*` 的行为必须标记为超出本技能权限。本技能不对 Milestone artifact 执行写入操作 —— 进度计数器的更新应由上游调用方（如 harness-skill）在收到本技能输出后决策执行。

## 何时使用

当当前问题不是"下一步该做什么"，而是"当前 Milestone 进展到哪一步、是否已达到验收边界"时，使用这个技能：

- 在 `RepoScope.Observe` 阶段，harness-skill 需要 Milestone 级别的状态估计
- Worktrack closeout 后，repo-refresh 完成后需要检查 Milestone 进度是否推进
- Programmer 显式请求 Milestone 状态检查（如"Milestone X 完成了多少？"）
- Continuous execution 流程中需要判断是否触发 handback 边界
- 在 `repo-whats-next-skill` 决策前需要 Milestone 验收状态作为依据
- 需要聚合多个 worktrack 的 evidence 来判定 Milestone 目的是否达成

## 工作流

1. 确认这是一轮 Milestone 状态分析轮次，不是工作追踪分派、下一步决策或直接执行。
2. 识别当前活跃 Milestone：从 Harness 控制状态或 repo snapshot 中获取当前 active milestone_id。
3. 读取 Milestone artifact（`.aw/milestone/{milestone_id}.md`），解析其字段结构（worktrack_list、completion_signals、acceptance_criteria、progress_counter、depends_on_milestones 等）。
4. 读取 worktrack backlog（`.aw/repo/worktrack-backlog.md`），获取所有声明的 worktrack 的当前状态。backlog 存储的状态值为 `done / deferred / blocked / resolved`，读取时须做归一化映射：`done → completed`、`resolved → completed`、`blocked → blocked`、`deferred → deferred`。映射后按 `worktrack_id` 去重（保留最新条目），以 `completed / blocked / deferred` 三类参与 progress 计算。
5. 读取 gate evidence：先读取 Milestone artifact 的 `aggregated_evidence` 引用列表（包含各 worktrack 的 evidence 路径），逐条读取；若 `aggregated_evidence` 为空，回退读取 `.aw/worktrack/gate-evidence.md` 获取最近关闭 worktrack 的 evidence 记录。聚合所有 evidence 后参与 `purpose_achieved` 判定。
6. 读取 repo snapshot（`.aw/repo/snapshot-status.md`），获取当前 repo 基准状态和治理信号。
7. 检查前置 Milestone 依赖：若 `depends_on_milestones` 非空，验证前置 Milestone 是否已完成。
8. 计算 Milestone 进度计数器：
   - 遍历 `worktrack_list`，对照 backlog 统计 total / completed / blocked / deferred 数量
   - 计算 `completion_pct`
9. 执行双重验收检查：
   - **worktrack_list_finished**：声明的 worktrack 列表是否全部处理（已完成 / 被明确移出 / 阻塞有决策）
   - **purpose_achieved**：Milestone 原始目的是否经聚合 evidence 证明达成（对照 `completion_signals` 和 `acceptance_criteria`）
10. 根据双重验收结果判定 `milestone_acceptance_verdict`：
    - `achieved`：两者同时满足
    - `not_achieved`：worktrack 列表未处理完成，或目的未达成
    - `blocked`：存在不可推进的阻塞项
    - `deferred`：存在被明确推迟的 worktrack 且不影响目的达成判定
11. 判断 `handback_required`：当 `milestone_acceptance_verdict` 为 `achieved` 或 `blocked` 时，触发 Milestone 验收边界，handback 为 true。
12. 给出 `release_version_consideration` hint：基于 Milestone 目的达成情况和 completion_signals 满足程度，给出对 version bump 或 release 的提示性建议（不接管 decision）。
13. 明确 `developer_decisions_needed`：列出必须由 developer 做出的决定（如"前置依赖未完成，是否跳过"、"purpose_achieved 存疑，是否手动判定"等）。
14. 生成 `recommendations`：对 `RepoScope.Decide` 的建议（如"建议 handback 让 developer 验收"、"建议推进到下一 Milestone"、"建议补充 evidence 后重新检查"）。
15. 向 Harness 返回结构化的 Milestone 状态报告。
16. 如果没有命中正式停止条件，允许监督器直接进入下一个合法判定。

## 正式停止条件

至少在以下任一条件成立时停止并返回控制权：

- 当前无活跃 Milestone（Milestone artifact 不存在或 status 非 active）
- Milestone artifact 关键字段缺失或损坏，无法执行有效分析
- Worktrack backlog 与 Milestone 声明的 worktrack_list 之间存在不可自动解决的矛盾
- 前置 Milestone 依赖未完成，且无法自动判定是否应阻塞当前 Milestone
- 双重验收检查中 `purpose_achieved` 的判断需要 developer 主观裁定，且无足够的自动判定依据
- 聚合 evidence 不足以支撑 purpose_achieved 判定，且无法通过限定范围探查补全
- Milestone 依赖的 artifact 跨域或以当前权限不可访问
- 观察依据缺失、过期或相互矛盾到足以让 Milestone 验收判定只能靠猜

## 硬约束

- 本技能是 RepoScope.Observe 的传感器/分析器层，负责 Milestone 状态分析；唯一合法行为是读取、计算、报告 Milestone 状态。
- 唯一合法行为是产出结构化的 Milestone 观测结果；选择下一 Worktrack、初始化 worktrack、修改 version/release 的行为必须标记为超出本技能权限。
- 对 `.aw/worktrack/*` 的唯一合法行为是将其读取为边界证据；重写 `.aw/worktrack/*` 的行为必须标记为超出本技能权限。
- 不替代 gate-skill 的 verdict：本技能聚合 gate evidence 用于 Milestone 级判定，但不重新执行 gate 逻辑。
- 不膨胀 harness-skill：harness-skill 继续只做 supervisor，本技能是独立的 Milestone 分析器，由 harness-skill 在需要时调用。
- Milestone 完成判定必须通过双重验收模型（worktrack_list_finished + purpose_achieved）：两者缺一时不得自动判定 Milestone 完成。
- Milestone 是 RepoScope 下的聚合观测变量，不是第三 Scope：不得创建独立 Scope、不得创建独立状态转移路径。
- 输出中的 `release_version_consideration` 是 hint，不是 decision：不得自动触发 release/publish/version bump。
- `developer_decisions_needed` 中的项目不得由本技能自动判定；它们必须作为显式边界交还给 developer。
- 如果 `depends_on_milestones` 中的前置 Milestone 未完成，必须标记为 blocked 并在 `developer_decisions_needed` 中列出是否跳过前置依赖的决策。
- 仅当 `milestone_input_checkpoint` 已存在且与当前 Milestone 输入指纹（milestone artifact + worktrack backlog + gate evidence + repo snapshot 的关键字段组合摘要）一致、同时 `latest_observed_checkpoint` 也与当前 `git rev-parse HEAD` 一致时，才可跳过重新计算 progress counter。仅 git HEAD 一致不足以跳过（`.aw/` 下运行时 artifact 不受 git 追溯）；任一 fingerprint 不匹配或缺失时必须完整重算，重算后返回新的 `milestone_input_checkpoint` 供 harness-skill 写入 control-state。

## 预期输出

使用这个技能时，产出一份至少包含以下章节的 Milestone 状态报告：

- `Milestone 基本信息`
- `进度计数`
- `双重验收检查`
- `验收判决`
- `Handback 判定`
- `Release/Version 提示`
- `Developer 决策边界`
- `建议`
- `交接给 Harness`

结果中至少应包含以下字段或等价表达：

- `milestone_id`
- `milestone_title`
- `milestone_status`：planned / active / completed / superseded
- `progress`：
  - `total`：声明的 worktrack 总数
  - `completed`：已完成或等效处理的 worktrack 数
  - `blocked`：被阻塞的 worktrack 数
  - `deferred`：被明确推迟的 worktrack 数
  - `completion_pct`：完成百分比
- `worktrack_list_finished`：boolean
- `purpose_achieved`：boolean
- `milestone_acceptance_verdict`：achieved / not_achieved / blocked / deferred
- `handback_required`：boolean
- `release_version_consideration`：string
- `developer_decisions_needed`：array of strings
- `recommendations`：array of strings
- `depends_on_status`：前置 Milestone 检查结果（如有）
- `aggregated_evidence_summary`：聚合 evidence 摘要
- `analysis_timestamp`：分析时间戳
- `input_artifacts_used`：使用的输入 artifact 列表及各自的时效性
- `observation_ready`：当前观察是否足以支撑下游判定
- `can_proceed`：boolean
- `proceed_blockers`：阻止推进的因素列表
- `handoff_signal`：交接信号
- `requires_developer_decision`：boolean

## 资源

使用当前活跃 Milestone artifact（`.aw/milestone/{milestone_id}.md`）、当前 worktrack backlog（`.aw/repo/worktrack-backlog.md`）、gate evidence（`.aw/worktrack/gate-evidence.md`）和 repo snapshot（`.aw/repo/snapshot-status.md`）作为主要输入。只有当工作追踪本地产物会实质影响 Milestone 进度计数或目的达成判定时才读取额外的 worktrack 细节文件；仅允许将它们作为辅助边界证据使用，禁止将它们当作 Milestone 真相的替代品。

结果应保持聚焦于 Milestone 级别的聚合分析，而不是扩张成单个 worktrack 的逐条审查或下一 worktrack 的选择规划。输出应可直接作为 `RepoScope.Decide` 和 `harness-skill` continuous execution 流程中的 handback 判断依据。
