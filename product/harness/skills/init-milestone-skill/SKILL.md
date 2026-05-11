---
name: init-milestone-skill
description: 当 Harness 处于 RepoScope 且需要创建或注册一个新的 Milestone 到 Pipeline 中时使用这个技能；它是 RepoScope.Init 的 Milestone 初始化算子，负责创建 milestone artifact、upsert milestone-backlog、处理 latest-override 和激活规则，不修改 version/release 状态。
---

# 初始化 Milestone 技能

## 概览

把这个技能作为 `Codex` 中 `RepoScope` 下的 Milestone 初始化算子使用。

本技能实现 `RepoScope.Init` 状态转移算子的 Milestone 维度，对应 Harness 控制回路中为 Milestone Pipeline 创建/注册新 milestone 的初始化动作。它是 Pipeline 的**入口算子**：接收 programmer 或 harness 的 milestone 规格，验证唯一性和依赖合法性，按 latest-override 语义写入 milestone artifact 和 milestone-backlog，处理激活规则（同一时刻仅一个 active），并产出结构化的初始化结果供 `RepoScope.Decide` 和 `harness-skill` 消费。

它的角色是**初始化 Milestone**，而不是分析 Milestone 状态或驱动 next action。它产出的是经验证、已写入的 Milestone 初始化结果，包括新 milestone 的 artifact 路径、pipeline 位置和激活状态。

它的主要输入是 programmer 或 harness 提供的 milestone 规格：

- Programmer 直接提供的 milestone 规格（title、purpose、worktrack_list、priority、activation_rules 等）
- Harness 从 Goal Charter 和 repo snapshot 推理出的 milestone 建议（需经本技能验证后写入）
- 当前 milestone-backlog（`.aw/repo/milestone-backlog.md`）用于唯一性检查和 pipeline 上下文
- 当前 control-state（`.aw/control-state.md`）用于 active milestone 状态

本技能对 `.aw/milestone/` 的写入是创建或 upsert 单个 milestone artifact；对 `.aw/repo/milestone-backlog.md` 的写入是按 milestone_id upsert 条目。本技能不修改 version/release 状态，不触发 worktrack 初始化。

## 何时使用

当当前问题不是"milestone 进展如何"，而是"需要创建或注册一个 milestone"时，使用这个技能：

- Programmer 显式声明一个新的 milestone 目标
- Harness 在 `RepoScope.Decide` 阶段推理出需要创建新 milestone 来组织 worktrack
- `repo-whats-next-skill` 输出 `suggested_milestone_action == "create"` 时（goal-driven 或 work-collection 路径）
- 需要更新已有 milestone（upsert）——如补充 worktrack_list、调整 priority
- Pipeline 中没有符合条件的 planned milestone 可激活时
- 向已有 goal-driven milestone 追加 worktrack 时（触发信号覆盖判定）

## 工作流

1. 确认这是一轮 Milestone 初始化轮次，不是 Milestone 状态分析或 Worktrack 初始化。
2. 读取当前 milestone-backlog（`.aw/repo/milestone-backlog.md`）和 control-state（`.aw/control-state.md`）获取 pipeline 上下文。
3. 解析输入来源：
   - 若来自 programmer：直接使用提供的 milestone 规格
   - 若来自 harness 推理：验证规格完整性（至少包含 title、purpose），缺失关键字段时标记为规格不完整并停止
   - 若两者同时存在：programmer 规格优先，harness 推理作为补充建议
4. 确定 milestone_id：
   - 若输入提供了 milestone_id：检查是否与已有 milestone 冲突
   - 若未提供：自动生成，格式 `MS-YYYYMMDD-NNN`（如 `MS-20260510-001`）
   - 若 milestone_id 已存在：进入 upsert 模式（latest-override）
5. 验证依赖合法性：
   - 若 `depends_on_milestones` 非空，逐一检查是否存在于 milestone-backlog 中
   - 引用的 milestone 不存在时标记为 `unknown_dependency` 并停止
   - 检查是否存在循环依赖（遍历 depends_on 链）
6. 确定 priority：
   - 输入提供的 priority 直接使用
   - 未提供时自动分配：取当前 pipeline 中最大 priority + 1
7. 确定 `milestone_kind`：
   - 若输入来自 programmer 且提供了 `milestone_kind`：直接使用
   - 若输入来自 programmer 但未提供 `milestone_kind`：默认 `goal-driven`
   - 若输入来自 harness（work-collection 路径）：`milestone_kind = "work-collection"`
   - work-collection 路径的自动生成字段：
     - `title`：`工作集合 MS-YYYYMMDD-NNN`（按创建时间自动编号）
     - `purpose`：`"工作集合 {milestone_id}"`
     - `completion_signals`：从 worktrack_list 逐条自动生成（每条映射为一个 signal）
     - `acceptance_criteria`：空（不适用）
     - `priority`：最低（取当前 pipeline 最大 priority + 1，确保不阻塞 goal-driven milestone）
     - `created_by`：`harness`
8. 追加 worktrack 时的信号覆盖判定（仅当向已有 goal-driven milestone 追加 worktrack 时执行）：
   a. 读取已有 milestone 的 `completion_signals` 和 `acceptance_criteria`
   b. 对每个新 worktrack，AI 辅助判定其验收是否被已有 signals 覆盖
   c. 输出 `coverage_verdict` ∈ {`fully_covered`, `partially_covered`, `not_covered`}
   d. 分支处理：
      - `fully_covered`：append + programmer 确认。"新 worktrack [X] 的验收已被已有 signals 覆盖，确认追加？"。标记 `signals_coverage_reviewed = true`
      - `partially_covered`：提示补充 signals → programmer 确认 → append。建议追加 signal 的自动推导内容。programmer 确认后更新 signals
      - `not_covered`：拒绝归入。"新 worktrack [X] 与当前 milestone 的 purpose 不匹配。建议：创建新 milestone 或归入 work-collection milestone"
   e. 关键设计原则：不静默写入。AI 判断是提示，决策权在 programmer
9. 确定激活状态：
   - work-collection milestone 创建后直接激活（`status = "active"`）
   - goal-driven：若当前无 active milestone 且 `depends_on_milestones` 全部满足（所有前置为 `completed` 或 `superseded`）：设置为 `active`
   - 若 `activation_rules` 非空且条件满足：设置为 `active`
   - 否则：设置为 `planned`
   - 同一时刻仅允许一个 `active`：若设置当前 milestone 为 active 且已有 active milestone，先处理旧 active 的过渡（保持原状，标记冲突由 harness-skill 处理）
10. 创建或更新 milestone artifact：
   - 写入 `.aw/milestone/{milestone_id}.md`
   - 使用 milestone 模板字段结构（milestone_id、title、purpose、status、worktrack_list、completion_signals、acceptance_criteria、progress_counter、aggregated_evidence、release_version_consideration、developer_decision_boundary、depends_on_milestones、priority、activation_rules、created_by、updated、milestone_kind）
   - upsert 时保留已有字段，仅更新变化字段
11. 写入或更新 milestone-backlog：
   - 按 milestone_id upsert 到 `.aw/repo/milestone-backlog.md`
   - 若 backlog 文件不存在则创建
   - 条目包含：milestone_id、title、purpose、status、priority、depends_on_milestones、worktrack_list、created_by、created_at、updated、updated_by、activation_rules、milestone_kind
12. 更新 control-state（若激活状态变化）：
   - 若新 milestone 被设为 active：更新 `active_milestone` 和 `milestone_status`
   - 若仅新增 planned milestone：不改变 `active_milestone`，仅更新 `milestone_pipeline_summary`
13. 产出一份结构化的 Milestone 初始化结果。
14. 如果没有命中正式停止条件，允许监督器直接进入下一个合法判定。

## 正式停止条件

至少在以下任一条件成立时停止并返回控制权：

- milestone_id 已存在且 programmer 未授权 upsert（在交互模式下需 programmer 确认）
- `depends_on_milestones` 引用了不存在的 milestone
- 检测到循环依赖
- 输入规格缺少 title 或 purpose 等关键字段且无法自动补全
- 当前已有 active milestone 且 programmer 未明确指示替换
- milestone-backlog 损坏、不可读或不可解析（同上位 milestone-status-skill 的停止条件）
- 写入 `.aw/milestone/` 或 `.aw/repo/milestone-backlog.md` 失败

## 硬约束

遵循 [docs/harness/foundations/skill-common-constraints.md] 中定义的公共约束 C-1 至 C-7。

- 同一时刻仅允许一个 active milestone：设为 active 前必须检查 pipeline 状态
- latest-override 以 `updated` 时间戳为准；同时间戳 programmer 优先
- 不得静默覆盖 programmer 创建的 milestone；upsert 时需标记 `override_source` 和 `override_reason`
- milestone_id 格式不做强制约束，但建议使用 `MS-YYYYMMDD-NNN` 保持可读性
- 循环依赖检测必须遍历完整 depends_on 链，不得仅检查直接依赖
- 仅当上游调用方（harness-skill 或 repo-whats-next-skill）明确授权时，才可变更 active milestone
- 本技能不创建 worktrack、不触发 worktrack 初始化、不修改 version/release 状态

## 预期输出

使用这个技能时，产出一份至少包含以下章节的 Milestone 初始化结果：

- `初始化决策`
- `Milestone 基本信息`
- `Pipeline 上下文`
- `依赖验证`
- `激活判定`
- `Artifact 写入`
- `Backlog 写入`
- `Control State 更新`
- `交接给 Harness`

结果中至少应包含以下字段或等价表达：

- `milestone_id`
- `milestone_title`
- `milestone_kind`：goal-driven / work-collection
- `milestone_status`：planned / active
- `init_action`：created / upserted
- `priority`
- `pipeline_position`：当前在 pipeline 中的位置
- `depends_on_validation`：依赖检查结果
- `activation_decision`：为何设置为 active/planned
- `previous_active_milestone`：被替换的旧 active milestone（如有）
- `artifact_path`：写入的 milestone artifact 路径
- `backlog_updated`：boolean
- `control_state_updated`：boolean
- `override_source`：programmer / harness / none
- `signals_coverage_reviewed`：boolean — 信号覆盖判定是否已完成 programmer 确认（仅追加 worktrack 时适用）
- `coverage_verdict`：fully_covered / partially_covered / not_covered / N/A（仅追加 worktrack 时适用）
- `can_proceed`：boolean
- `proceed_blockers`：阻止推进的因素列表
- `recommendations`：对 RepoScope.Decide 的建议

## 资源

使用当前 milestone-backlog（`.aw/repo/milestone-backlog.md`）、control-state（`.aw/control-state.md`）、milestone 模板（`.aw/milestone/milestone-template.md`）作为主要输入。当 milestone 规格来自 harness 推理时，还需读取 Goal Charter（`.aw/goal-charter.md`）和 repo snapshot（`.aw/repo/snapshot-status.md`）以验证推理依据。

结果应保持聚焦于 Milestone 的初始化动作，而不是扩张成 pipeline 分析或 worktrack 规划。输出应可直接作为 `RepoScope.Decide` 和 `harness-skill` 的 pipeline 状态输入。
