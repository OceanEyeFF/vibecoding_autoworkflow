# Harness Agents Skill Payloads

`product/harness/adapters/agents/skills/` 保存 `agents` backend 的 canonical-copy payload descriptor source。当前 deploy contract 下，`install --backend agents` 会消费这里声明的 live payload，并把 payload 列出的 canonical skill 文件复制到当前 backend 的 target root。

当前结构：

- 每个 skill 一个目录：`<skill>/`
- 每个 payload 目录最小只包含：
  - `payload.json`：machine-readable payload descriptor

当前 `agents` skill set：

- `close-worktrack-skill`
- `dispatch-skills`
- `gate-skill`
- `harness-skill`
- `init-worktrack-skill`
- `recover-worktrack-skill`
- `repo-change-goal-skill`
- `repo-refresh-skill`
- `repo-status-skill`
- `repo-whats-next-skill`
- `review-evidence-skill`
- `rule-check-skill`
- `schedule-worktrack-skill`
- `set-harness-goal-skill`
- `test-evidence-skill`
- `worktrack-status-skill`

规则：

- canonical source 继续留在 `product/harness/skills/`
- `target_dir` 相对 backend skills root；当前实例统一使用 `aw-<skill_id>`，并保留 `<skill_id>` 作为 `legacy_target_dirs` 用于升级清理，在当前 live bindings 内必须唯一
- payload 声明 canonical files 和 deploy target 命名
- `payload.json` 的 `required_payload_files` 仍声明顶层 `aw.marker`；但 marker 只在 `install --backend agents` 写入 target 时运行时生成，不作为 source 文件存放在 adapter 目录中
- target 中的 `aw.marker` 只表达 deploy 指纹：`marker_version / backend / skill_id / payload_version / payload_fingerprint`
- `prune --all` 只会删除带可识别、且属于当前 backend 的 marker 目录
- `check_paths_exist` 与 `install` 只承接当前 source 声明的 live payload，不承接 archive/history 或旧版本保活
- install 会复制 payload 声明的 canonical workflow 正文、references 或 templates
- payload 不把 installed target root 当 source of truth
