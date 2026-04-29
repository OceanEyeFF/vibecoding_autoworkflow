# Claude Adapter

`product/harness/adapters/claude/` 承接 Claude backend 的 Harness skill payload descriptor source。

当前 payload model：

- payload source: `product/harness/adapters/claude/skills/<skill>/payload.json`
- canonical source: `product/harness/skills/<skill>/`
- target root: `<target_repo>/.claude/skills`
- target dir: `aw-<skill_id>`
- payload policy: `canonical-copy`
- payload version: `claude-skill-payload.v1`

这里不承接 repo-local `.claude/skills/` 安装结果。
