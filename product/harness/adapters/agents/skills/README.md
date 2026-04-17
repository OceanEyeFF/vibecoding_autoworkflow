# Harness Agents Skill Payloads

`product/harness/adapters/agents/skills/` 保存 `agents` backend 的 first-wave skill thin-shell payload source。当前 deploy contract 下，`install --backend agents` 只会消费这里声明的 live payload，并把它写入当前 backend 的 target root。

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
- `target_dir` 相对 backend skills root；当前首发实例统一使用 `<skill_id>`，并且在当前 live bindings 内必须唯一
- payload 只声明 backend-specific 路由、首发冻结约束和 deploy target 命名
- `payload.json` 的 `required_payload_files` 仍声明顶层 `aw.marker`；但 marker 只在 `install --backend agents` 写入 target 时运行时生成，不作为 source 文件存放在 adapter 目录中
- target 中的 `aw.marker` 只表达 deploy 指纹：`marker_version / backend / skill_id / payload_version / payload_fingerprint`
- `prune --all` 只会删除带可识别、且属于当前 backend 的 marker 目录
- `check_paths_exist` 与 `install` 只承接当前 source 声明的 live payload，不承接 archive/history 或旧版本保活
- payload 不复制 canonical workflow 正文
- payload 不把 installed target root 当 source of truth
