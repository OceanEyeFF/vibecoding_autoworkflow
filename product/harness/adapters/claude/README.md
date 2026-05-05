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

当前稳定边界：

- canonical truth 仍在 `product/harness/skills/<skill>/`
- payload source 固定在 `product/harness/adapters/claude/skills/<skill>/payload.json`
- `required_payload_files` 必须等于 `canonical_paths` 对应文件，再加上 `payload.json` 与 runtime-generated `aw.marker`
- `aw.marker` 不存在于 adapter source 中，只在 install 写入 target 时生成
- `update --backend claude --yes` 只包装 `prune --all -> check_paths_exist -> install -> verify`
- `claude_frontmatter.disable-model-invocation: true` 这类字段只影响 target 写入结果，不回写 canonical source
- repo-local `.claude/skills/` 是 deploy target，不是 source truth

这里不承接 repo-local `.claude/skills/` 安装结果。
