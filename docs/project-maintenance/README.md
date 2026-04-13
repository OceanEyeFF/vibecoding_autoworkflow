# Project Maintenance

`docs/project-maintenance/` 只承接当前仓库的 operator-facing 维护文档：结构真相、治理入口、deploy runbook，以及按 backend 聚合的 repo-local usage help。这里不承载 deployable skill 合同正文，也不回退到旧 `docs/operations/*` 分叉结构。

`project-maintenance/` 不长期承载 `suspended` 文档；暂停中的共享 runbook 应转为 `superseded`，非共享草稿应移出 `docs/`。

## 当前入口分层

1. `foundations/`
   固定根目录、truth boundary 与分层规则。
2. `governance/`
   固定 `review / verify / gate` 与路径治理检查入口。
3. `deploy/`
   固定 deploy 文档三分工：
   - quick start: 首次安装、local/global deploy、最小复验
   - lifecycle: add / update / rename / remove 的 source 与同步闭环
   - maintenance: drift、stale、`--prune`、只读 `verify` 与诊断
4. `usage-help/`
   只保留 `agents`、`claude`、`opencode` 的 backend 差异，不再按 `memory-side/` 或 `task-interface/` 拆子树。

## 从这里怎么进

- [foundations/README.md](./foundations/README.md)
- [governance/README.md](./governance/README.md)
- [deploy/README.md](./deploy/README.md)
- [usage-help/README.md](./usage-help/README.md)

## Operator 常见入口

- 第一次给某个 backend 安装 skill：先看 [deploy/deploy-runbook.md](./deploy/deploy-runbook.md)
- 已有 mounts，只想更新或复验：先看 [deploy/skill-deployment-maintenance.md](./deploy/skill-deployment-maintenance.md)
- 新增、改名、删除 skill source：先看 [deploy/skill-lifecycle.md](./deploy/skill-lifecycle.md)
- 只想确认 `agents / claude / opencode` 差异：先看 [usage-help/README.md](./usage-help/README.md)

AI 默认阅读顺序以 [AGENTS.md](../../AGENTS.md) 为准。
本页只做入口导航，不重复主线 `read_first/read_next/do_not_read_yet` 合同。
