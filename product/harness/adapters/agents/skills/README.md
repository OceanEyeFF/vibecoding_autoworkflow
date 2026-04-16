# Harness Agents Skill Payloads

`product/harness/adapters/agents/skills/` 保存 `agents` backend 的 first-wave skill thin-shell payload source。

当前结构：

- 每个 skill 一个目录：`<skill>/`
- 每个 payload 目录最小只包含：
  - `SKILL.md`：面向 `agents` 的 thin-shell runtime entry
  - `payload.json`：machine-readable payload descriptor

当前首发 skill：

- `harness-skill`
- `repo-status-skill`
- `repo-whats-next-skill`
- `init-worktrack-skill`
- `dispatch-skills`

规则：

- canonical source 继续留在 `product/harness/skills/`
- `target_dir` 相对 backend skills root；当前首发实例统一使用 `<skill_id>`
- payload 只声明 backend-specific 路由、首发冻结约束和 deploy target 命名
- 当前 payload form 只对 repo-local `agents` target 有效；global payload form 仍待后续 contract 落定
- payload 不复制 canonical workflow 正文
- payload 不把 repo-local target 当 source of truth
