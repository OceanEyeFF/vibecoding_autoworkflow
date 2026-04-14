# Harness Operations Product Source

这里是 `Harness Operations` 的 Harness 平台源码与分发承接入口，保存的是业务源码，而不是部署结果。

- `skills/`：Harness Operations canonical skill 源码，作为平台搭建的核心输入
- `adapters/agents/`：Codex / OpenAI adapter 源码，承接平台分发到对应执行面
- `adapters/claude/`：Claude adapter 源码，承接平台分发到对应执行面
- `adapters/opencode/`：OpenCode adapter 源码，承接平台分发到对应执行面
- `manifests/`：打包和分发预留位，承接平台发布所需的清单与元数据

repo-local `.claude/skills/`、`.agents/skills/` 与 `.opencode/skills/` 由部署脚本生成。

当前 `harness-operations` 的平台搭建与分发链路：

- canonical：`prompt.md`（backend-agnostic）+ shared `harness-standard.md`
- adapter source：backend-specific `header.yaml`（及必要 metadata）
- build/deploy：`adapter_deploy.py build` 先组装最终 `SKILL.md`，再执行 `local/global` 部署
