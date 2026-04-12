# Project Maintenance

`docs/project-maintenance/` 只保存当前仓库的项目维护文档，包括 foundations、governance、deploy 与 backend 使用帮助，不承载 deployable skill 合同正文。

`project-maintenance/` 不长期承载 `suspended` 文档；暂停中的共享 runbook 应转为 `superseded`，非共享草稿应移出 `docs/`。

当前入口分层：

1. `foundations/`：项目级基础结构与分层真相
2. `governance/`：review、gate、check 与 branch/PR 规则
3. `deploy/`：deploy 与 deploy maintenance
4. `usage-help/`：按 backend 聚合的 repo-local 使用帮助

主入口：

- [foundations/README.md](./foundations/README.md)
- [governance/README.md](./governance/README.md)
- [deploy/README.md](./deploy/README.md)
- [usage-help/README.md](./usage-help/README.md)

AI 默认阅读顺序以 [AGENTS.md](../../AGENTS.md) 为准。
本页只做入口导航，不重复主线 `read_first/read_next/do_not_read_yet` 合同。
