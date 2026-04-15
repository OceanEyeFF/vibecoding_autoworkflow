---
title: "Harness Skill Catalog / RepoScope"
status: draft
updated: 2026-04-15
owner: aw-kernel
last_verified: 2026-04-15
---
# RepoScope Skill Catalog

> 目的：固定 `RepoScope` 下直接面向 `Codex` 的 Harness skills catalog。

这里不再先定义一层中间 operator 名称，再把它翻译成 skill。对当前项目而言，`Codex` 最终消费的就是 skills 本身。

## 当前原则

- `RepoScope` skills 负责长期基线的观察、判断、目标变更和 repo 状态刷新
- 这些 skills 不直接承担编码执行
- 如果一轮需要实际改动系统状态，应由 supervisor 决定是否切入 `WorktrackScope` 或派发下游执行体

## Catalog

### 1. repo-status-skill

职责：

- 读取当前 repo 基线
- 汇总主线、活跃分支、治理状态和已知风险
- 产出适合 `RepoScope` 判断的状态摘要

主要依赖：

- `Repo Goal / Charter`
- `Repo Snapshot / Status`

canonical executable source：

- [../../../../product/harness/skills/repo-status-skill/SKILL.md](../../../../product/harness/skills/repo-status-skill/SKILL.md)
- [../../../../product/harness/skills/repo-status-skill/references/entrypoints.md](../../../../product/harness/skills/repo-status-skill/references/entrypoints.md)

当前状态：

- `initial canonical executable skeleton landed`

### 2. repo-whats-next-skill

职责：

- 基于当前 repo 状态判断下一步最合理的演进方向
- 明确是切入 worktrack、刷新 baseline，还是进入 goal change control

主要依赖：

- `Repo Snapshot / Status`
- `Goal Change Request`

canonical executable source：

- [../../../../product/harness/skills/repo-whats-next-skill/SKILL.md](../../../../product/harness/skills/repo-whats-next-skill/SKILL.md)
- [../../../../product/harness/skills/repo-whats-next-skill/references/entrypoints.md](../../../../product/harness/skills/repo-whats-next-skill/references/entrypoints.md)

当前状态：

- `initial canonical executable skeleton landed`

### 3. goal-change-control-skill

职责：

- 处理目标层的独立变更请求
- 评估对现有 worktracks 和 baseline 的影响

主要依赖：

- `Goal Change Request`
- `Repo Goal / Charter`

canonical executable source：

- [../../../../product/harness/skills/goal-change-control-skill/SKILL.md](../../../../product/harness/skills/goal-change-control-skill/SKILL.md)
- [../../../../product/harness/skills/goal-change-control-skill/references/entrypoints.md](../../../../product/harness/skills/goal-change-control-skill/references/entrypoints.md)

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
- [../../../../product/harness/skills/repo-refresh-skill/references/entrypoints.md](../../../../product/harness/skills/repo-refresh-skill/references/entrypoints.md)

当前状态：

- `initial canonical executable skeleton landed`
