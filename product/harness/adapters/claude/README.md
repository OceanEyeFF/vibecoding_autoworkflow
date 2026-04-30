# Claude Adapter

`product/harness/adapters/claude/` 承接 Claude backend 的 Harness skill payload descriptor source。

当前 payload model：

- payload source: `product/harness/adapters/claude/skills/<skill>/payload.json`
- canonical source: `product/harness/skills/<skill>/`
- target root: `<target_repo>/.claude/skills`
- target dir: `<skill_id>`
- legacy target dir: `aw-<skill_id>` for managed cleanup during migration
- payload policy: `canonical-copy`
- payload version: `claude-skill-payload.v1`
- side-effecting skill protection: payload descriptors may request Claude frontmatter overrides such as `disable-model-invocation: true`

这里不承接 repo-local `.claude/skills/` 安装结果。
