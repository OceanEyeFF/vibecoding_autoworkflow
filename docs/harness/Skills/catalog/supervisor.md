---
title: "Harness Skill Catalog / Supervisor"
status: active
updated: 2026-04-15
owner: aw-kernel
last_verified: 2026-04-15
---
# Supervisor Skill Catalog

> 目的：固定顶层 Harness supervisor skill 的职责与当前承接位。

## 当前 canonical skill

### harness-skill

职责：

- 判断当前在 `RepoScope` 还是 `WorktrackScope`
- 在当前层级内跑完一轮 bounded Harness loop
- 汇总本轮动作、证据、状态和下一步建议
- 在 authority boundary 停下并向 programmer 请求批准

canonical executable source：

- [../../../../product/harness/skills/harness-skill/SKILL.md](../../../../product/harness/skills/harness-skill/SKILL.md)
- [../../../../product/harness/skills/harness-skill/references/entrypoints.md](../../../../product/harness/skills/harness-skill/references/entrypoints.md)

固定输出：

- `Harness Turn Report`

说明：

- 这是当前唯一已经落地的 Harness canonical skill
- 其余 repo/worktrack skills 目前仍停留在 catalog target 层
