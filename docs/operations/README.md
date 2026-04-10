# Operations

`docs/operations/` 只保存当前仓库的 repo-local runbook、deploy/verify/maintenance 说明与 compatibility shims，不承载 canonical truth。

`operations/` 不长期承载 `suspended` 文档；暂停中的共享 runbook 应转为 `superseded`，非共享草稿应移出 `docs/`。

当前入口分层：

1. `deploy/`：deploy / verify / maintenance
2. `autoresearch/`：autoresearch daily runbook 与 closeout appendix
3. `memory-side/`：Memory Side 的 repo-local usage help
4. `task-interface/`：Task Interface 的 repo-local usage help
5. `prompt-templates/`：`product/harness-operations/` 的 compatibility prompt shims

主入口：

- [deploy/README.md](./deploy/README.md)
- [autoresearch/README.md](./autoresearch/README.md)
- [memory-side/README.md](./memory-side/README.md)
- [task-interface/README.md](./task-interface/README.md)
- [prompt-templates/README.md](./prompt-templates/README.md)

AI 默认阅读顺序以 [AGENTS.md](../../AGENTS.md) 为准。
本页只做入口导航，不重复主线 `read_first/read_next/do_not_read_yet` 合同。
