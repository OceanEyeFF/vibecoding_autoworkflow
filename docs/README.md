# Docs

`docs/` 承载文档真相与仓库操作说明。

## 核心定位

- 构建 `Codex-first` 的 AI coding harness 平台，作为 repo-side contract layer 分发到多个项目
- `Harness` 是一级文档域，负责 repo 演进控制面的 doctrine、artifact、catalog 与 workflow family
- 退役的 `memory-side`、`task-interface`、adjacent-system 文档域的执行边界由 `AGENTS.md`、`docs/harness/artifact/`、`docs/project-maintenance/governance/` 承接
- canonical skills 与 adapters 在 `product/`，部署/评测/治理脚本在 `toolchain/`

## 当前结构

- [project-maintenance/README.md](./project-maintenance/README.md)：项目维护、治理、部署与 backend usage
- [harness/README.md](./harness/README.md)：Harness 主线 doctrine、scope、artifact、catalog 与 workflow families

## 阅读顺序

以 [AGENTS.md](../AGENTS.md) 为唯一权威。本页只做 `docs/` 模块入口。

## 文档治理规则

- `project-maintenance/` 承接 operator-facing 维护；`harness/` 承接 Harness-first 主线
- `docs/` 下除 `README.md` 外正文文档必须保持 `title/status/updated/owner/last_verified` frontmatter
- `docs/` 不长期承载 `suspended`/scratch 文档；暂停共享文档转为 `superseded`，非共享草稿移出
- 新增正文文档后更新最近 `README.md` 入口，不留孤儿文档
- 研究结论准入主线后，同步升格到 `project-maintenance/`、`harness/`、`toolchain/` 或 `product/` 的承接位

## AI 默认路径

- 读 `project-maintenance/` 与 `harness/` 入口确认任务类型
- repo-local workflow 步骤进 `project-maintenance/`
- Harness doctrine、artifact、catalog 或 workflow family 进 `harness/`
