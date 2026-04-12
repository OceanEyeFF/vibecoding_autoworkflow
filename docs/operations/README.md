# Operations

`docs/operations/` 只保存当前仓库的 repo-local 执行、参考、治理与使用帮助，不承载 canonical truth。

`operations/` 不长期承载 `suspended` 文档；暂停中的共享 runbook 应转为 `superseded`，非共享草稿应移出 `docs/`。

当前入口分层：

1. `runbooks/`：日常执行步骤
2. `references/`：CLI、参数、输出面与 repo-local contracts
3. `governance/`：review、gate、check 与 branch/PR 规则
4. `usage-help/`：按 backend 聚合的 repo-local 使用帮助

主入口：

- [runbooks/README.md](./runbooks/README.md)
- [references/README.md](./references/README.md)
- [governance/README.md](./governance/README.md)
- [usage-help/README.md](./usage-help/README.md)

AI 默认阅读顺序以 [AGENTS.md](../../AGENTS.md) 为准。
本页只做入口导航，不重复主线 `read_first/read_next/do_not_read_yet` 合同。
