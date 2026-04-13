# Harness Operations Product Source

这里保存 `Harness Operations` 的业务源码，而不是部署结果。

- `skills/`：Harness Operations canonical skill
- `adapters/agents/`：Codex / OpenAI adapter 源码
- `adapters/claude/`：Claude adapter 源码
- `adapters/opencode/`：OpenCode adapter 源码
- `manifests/`：打包和分发预留位

repo-local `.claude/skills/`、`.agents/skills/` 与 `.opencode/skills/` 由部署脚本生成。

当前 `harness-operations` 分发形态：

- canonical：`prompt.md`（backend-agnostic）+ shared `harness-standard.md`
- adapter source：backend-specific `header.yaml`（及必要 metadata）
- build/deploy：`adapter_deploy.py build` 先组装最终 `SKILL.md`，再执行 `local/global` 部署
