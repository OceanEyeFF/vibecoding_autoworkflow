---
title: "Harness Skill Catalog / RepoScope"
status: draft
updated: 2026-04-20
owner: aw-kernel
last_verified: 2026-04-20
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

- [../../../../product/harness/skills/repo-status-skill/SKILL.md](../../../../product/harness/skills/repo-status-skill/SKILL.md)

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
- 用 `Facts / Inferences / Unknowns`、单一 `Current Primary Contradiction`、`Primary Aspect`、`Top Priority Now`、`Do Not Do`、`Recommended Repo Action` 与 `Minimal Missing Info` 压缩 repo 级优先级判断
- 该模式属于 `RepoScope` 分析模式，不是新的 skill，也不是 `WorktrackScope` skill

主要依赖：

- `Repo Goal / Charter`
- `Repo Snapshot / Status`
- `Harness Control State`
- `Goal Change Request`

canonical executable source：

- [../../../../product/harness/skills/repo-whats-next-skill/SKILL.md](../../../../product/harness/skills/repo-whats-next-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed, with bounded priority reframe mode folded into the same skill`
- `first-wave deploy subset is narrower than the canonical action space and must be restated on the copied skill surface`

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

### 3. goal-change-control-skill

说明：

- 这是保留的 repo-level change-control 槽位，不是当前首要主路径 skill
- 在很多实际使用场景里，programmer 可能直接改 `Repo Goal / Charter`，因此这一 skill 可视为可选能力，而不是每次都要经过的固定环节

职责：

- 处理目标层的独立变更请求
- 评估对现有 worktracks 和 baseline 的影响

主要依赖：

- `Goal Change Request`
- `Repo Goal / Charter`
- `Repo Snapshot / Status`
- `Harness Control State`

canonical executable source：

- [../../../../product/harness/skills/goal-change-control-skill/SKILL.md](../../../../product/harness/skills/goal-change-control-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`

### 4. repo-refresh-skill

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

- [../../../../product/harness/skills/repo-refresh-skill/SKILL.md](../../../../product/harness/skills/repo-refresh-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`
