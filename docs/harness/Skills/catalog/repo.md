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
- `RepoScope` 下的 structured handoff 优先使用 `recommended_next_route` 与 canonical approval 字段，而不是继续扩散旧的 next-action prose
- `RepoScope` 内可以挂载有界分析模式，但不应为了分析框架本身继续新增 skill 数量或层级
- 如果一轮需要实际改动系统状态，应由 supervisor 决定是否切入 `WorktrackScope` 或派发下游执行体

## Catalog

### 1. repo-status-skill

职责：

- 读取当前 repo 基线
- 汇总主线、活跃分支、治理状态和已知风险
- 产出适合 `RepoScope.deciding` 消费的 observation packet
- 明确这一轮 observation 是否已经足够进入下一步 repo judgment

主要依赖：

- `Repo Goal / Charter`
- `Repo Snapshot / Status`

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
- 在默认 next-step 判断仍偏松时，启用轻量 `priority reframe / contradiction analysis` 模式
- 用 `Facts / Inferences / Unknowns`、单一 `Current Primary Contradiction`、`Primary Aspect`、`Top Priority Now`、`Do Not Do`、`Recommended Repo Action` 与 `Minimal Missing Info` 压缩 repo 级优先级判断
- 该模式属于 `RepoScope` 分析模式，不是新的 skill，也不是 `WorktrackScope` skill

主要依赖：

- `Repo Snapshot / Status`
- `Goal Change Request`

canonical executable source：

- [../../../../product/harness/skills/repo-whats-next-skill/SKILL.md](../../../../product/harness/skills/repo-whats-next-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed, with bounded priority reframe mode folded into the same skill`

preferred decision fields：

- `recommended_repo_action`
- `recommended_next_route`
- `continuation_ready`
- `continuation_blockers`
- `approval_required`
- `approval_scope`
- `approval_reason`

### 3. goal-change-control-skill

职责：

- 处理目标层的独立变更请求
- 评估对现有 worktracks 和 baseline 的影响

主要依赖：

- `Goal Change Request`
- `Repo Goal / Charter`

canonical executable source：

- [../../../../product/harness/skills/goal-change-control-skill/SKILL.md](../../../../product/harness/skills/goal-change-control-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`

### 4. repo-refresh-skill

职责：

- 在 worktrack closeout 后刷新 repo 慢变量状态
- 把已验证结果回收到 repo 级正式对象

主要依赖：

- `Repo Snapshot / Status`
- `Gate Evidence`

canonical executable source：

- [../../../../product/harness/skills/repo-refresh-skill/SKILL.md](../../../../product/harness/skills/repo-refresh-skill/SKILL.md)

当前状态：

- `initial canonical executable skeleton landed`
