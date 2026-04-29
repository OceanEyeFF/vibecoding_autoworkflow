---
title: "Harness Skill Catalog / RepoScope"
status: draft
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# RepoScope Skill Catalog

> 目的：固定 `RepoScope` 下直接面向 `Codex` 的 Harness skills catalog。

这里不再先定义一层中间 operator 名称，再把它翻译成 skill。对当前项目而言，`Codex` 最终消费的就是 skills 本身。

## 当前原则

- `RepoScope` skills 负责长期基线的观察、判断、目标变更和 repo 状态刷新
- 这些 skills 不直接承担编码执行
- `repo-status-skill` 对应 `RepoScope.observing`，`repo-whats-next-skill` 对应 `RepoScope.deciding`
- `repo-status-skill` 是给 `harness-skill` 顺手调用的稳定观测包，不是 `repo-whats-next-skill` 的强制前置
- `repo-whats-next-skill` 必须可以在没有 `repo-status-skill` 产物的前提下，直接基于 repo truth 跑完一轮判断
- `repo-status-skill`、`repo-whats-next-skill`、`repo-refresh-skill` 都不负责 worktrack 级 `.aw/worktrack/*` 文档维护
- `RepoScope` 下的 structured handoff 优先使用 `recommended_next_route` 与 canonical approval 字段，而不是继续扩散旧的 next-action prose
- `RepoScope` 内可以挂载有界分析模式，但不应为了分析框架本身继续新增 skill 数量或层级
- `Repo Analysis` 是 RepoScope 的决策支撑 artifact；它可以喂给 `repo-whats-next-skill`，但不能替代 `Goal / Charter` 或 `Snapshot / Status`
- `append-feature` 与 `append-design` 追加请求由同一个 `repo-append-request-skill` 分类和路由，不拆分为两个 skill
- 如果一轮需要实际改动系统状态，应由 supervisor 决定是否切入 `WorktrackScope` 或派发下游执行体

## Catalog

### 1. repo-status-skill

职责：

- 读取当前 repo 基线
- 汇总主线、活跃分支、治理状态和已知风险
- 为 `harness-skill` 产出格式稳定、字段稳定的 observation packet
- 明确这一轮 observation 是否已经足够进入下一步 repo judgment

主要依赖：

- `Repo Goal / Charter`
- `Repo Snapshot / Status`
- `Harness Control State`

canonical executable source：

- [../../../product/harness/skills/repo-status-skill/SKILL.md](../../../product/harness/skills/repo-status-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`

preferred handoff fields：

- `repo_judgment_ready`
- `recommended_next_route`
- `continuation_ready`
- `continuation_blockers`
- `approval_required`
- `approval_reason`

### 2. repo-whats-next-skill

职责：

- 基于当前 repo 状态判断下一步最合理的演进方向
- 明确是切入 worktrack、刷新 baseline，还是进入 goal change control
- 保留 repo judgment 字段 `recommended_repo_action`，同时回写 supervisor 可消费的 `recommended_next_route`
- 可以直接基于 `Repo Goal / Charter`、`Repo Snapshot / Status` 与 `Harness Control State` 跑完一轮，不要求先有 `repo-status-skill` 产物
- canonical skill 保留完整 `RepoScope.deciding` 动作空间，但如果当前 deploy profile 已收窄支持分支，输出必须反映 active route boundary，而不是继续暴露全量 canonical 路由
- 主要依据 `Repo Goal / Charter`、`Repo Snapshot / Status` 与当前 `Harness Control State` 做 repo 级判断；`Worktrack Contract` / `Plan / Task Queue` 只能作为活跃或刚关闭 worktrack 的边界证据，不能当成 repo 级任务队列
- 在默认 next-step 判断仍偏松时，启用轻量 `priority reframe / contradiction analysis` 模式
- 在默认模式和优先级重构都完全找不到可更新内容时，启用 `overview fallback` 模式，用于生成未来 worktrack 候选建议
- 用 `Facts / Inferences / Unknowns`、单一 `Current Primary Contradiction`、`Primary Aspect`、`Top Priority Now`、`Do Not Do`、`Recommended Repo Action` 与 `Minimal Missing Info` 压缩 repo 级优先级判断
- 当存在新鲜 `Repo Analysis` artifact 时，可以把它作为该模式的结构化输入；没有该 artifact 时仍必须直接基于 Goal、Snapshot 与 Control State 完成判定
- `Repo Analysis` 的 `recommended_repo_action` 必须再投影成 `recommended_next_route`、approval 字段与 continuation 字段，不能把分析结论当成已执行状态更新
- `overview fallback` 可以参考 `project-dialectic-planning-skill` 的基本面与矛盾分析方法，使用 `Facts / Inferences / Unknowns` 区分事实、推断和未知项，但必须压缩为 repo 级候选建议，不得变成大型战略报告
- `overview fallback` 只返回 `candidate_worktracks` 与 `top_candidate` 等候选建议，不创建工作追踪，不改变 Harness 控制状态
- 这些模式属于 `RepoScope` 分析模式，不是新的 skill，也不是 `WorktrackScope` skill

主要依赖：

- `Repo Goal / Charter`
- `Repo Snapshot / Status`
- `Harness Control State`
- `Goal Change Request`

canonical executable source：

- [../../../product/harness/skills/repo-whats-next-skill/SKILL.md](../../../product/harness/skills/repo-whats-next-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed, with bounded priority reframe mode folded into the same skill`
- `agents deploy copies the canonical skill surface directly; runtime route boundaries should come from current repo artifacts and control state, not legacy payload metadata`
- `overview fallback mode landed for no-action-found cases`

preferred decision fields：

- `recommended_repo_action`
- `recommended_next_route`
- `allowed_repo_actions`
- `route_boundary_source`
- `continuation_ready`
- `continuation_blockers`
- `approval_required`
- `approval_scope`
- `approval_reason`
- `overview_trigger_reason`
- `candidate_worktracks`
- `top_candidate`

### 3. repo-append-request-skill

说明：

- 在 `RepoScope` 下处理外部追加请求 intake
- 支持 `append-feature` 与 `append-design` 两个 mode
- 只做分类与路由，不执行目标变更、scope expansion、设计或实现

职责：

- 接收追加请求并判断它应归入哪条控制路由
- 在 `goal change`、`new worktrack`、`scope expansion`、`design-only`、`design-then-implementation` 中选择一个分类结果
- 输出 `Append Request` 路由结果、建议下一 route / scope、suggested node type、审批边界与最小缺失信息
- 当追加请求命中目标变更或范围扩展时，显式返回 authority boundary，而不是静默执行
- 保持 `approval_required`、`continuation_ready` 与 `continuation_blockers` 一致，避免在待审批或缺失信息阻塞时继续推进

主要依赖：

- `Append Request`
- `Repo Goal / Charter`
- `Repo Snapshot / Status`
- `Harness Control State`
- 必要的活跃 `Worktrack Contract` 摘要

canonical executable source：

- [../../../product/harness/skills/repo-append-request-skill/SKILL.md](../../../product/harness/skills/repo-append-request-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`

preferred decision fields：

- `append_mode`
- `append_classification`
- `classification_confidence`
- `recommended_next_route`
- `recommended_next_scope`
- `suggested_node_type`
- `approval_required`
- `approval_scope`
- `approval_reason`
- `continuation_ready`
- `continuation_blockers`

### 4. repo-change-goal-skill

说明：

- 在 `RepoScope` 下执行目标变更，负责 repo 级参考信号（Goal）的分析与改写
- 不是"只出报告"的分析型 skill，而是包含"分析 → 草案 → 确认 → 执行改写"完整闭环
- 在当前 carrier 直接分析，不再打包给 SubAgent 做限定范围简报

职责：

- 接收并分析目标级变更请求
- 评估对现有 worktracks、baseline 和不变条件的影响
- 生成 `goal-charter` 草案，等待用户确认
- 用户确认后直接执行对 `goal-charter.md`、`repo/snapshot-status.md`、`control-state.md` 的改写

主要依赖：

- `Goal Change Request`
- `Repo Goal / Charter`
- `Repo Snapshot / Status`
- `Harness Control State`

canonical executable source：

- [../../../product/harness/skills/repo-change-goal-skill/SKILL.md](../../../product/harness/skills/repo-change-goal-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`

### 5. repo-refresh-skill

职责：

- 在 worktrack closeout 后刷新 repo 慢变量状态
- 把已验证结果回收到 repo 级正式对象
- 只处理 repo 级 writeback，不处理 `.aw/worktrack/*` 维护

主要依赖：

- `Repo Goal / Charter`
- `Repo Snapshot / Status`
- `Gate Evidence`
- `Harness Control State`

canonical executable source：

- [../../../product/harness/skills/repo-refresh-skill/SKILL.md](../../../product/harness/skills/repo-refresh-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`
