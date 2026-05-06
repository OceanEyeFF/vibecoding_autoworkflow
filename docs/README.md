# Docs

`docs/` 是当前仓库的第二块正式内容区，负责承载文档真相和仓库操作说明。

## 核心定位

- 本项目的核心目标是构建 `Codex-first` 的 AI coding harness 平台，作为 repo-side contract layer 分发到多个项目中使用
- `Harness` 是一级文档域，负责 repo 演进控制面的 doctrine、artifact、catalog 与 workflow family
- 已退役的 `memory-side`、`task-interface` 和 adjacent-system 文档域不再作为独立 truth layer；相关执行边界由 `AGENTS.md`、`docs/harness/artifact/` 与 `docs/project-maintenance/governance/` 承接
- canonical skills 与 adapters 在 `product/`，部署、评测和治理脚本在 `toolchain/`

## 当前结构

- [project-maintenance/README.md](./project-maintenance/README.md)：项目维护、治理、deploy 与 backend usage
- [harness/README.md](./harness/README.md)：Harness 主线 doctrine、scope、artifact、catalog 与 workflow families

## 阅读顺序

默认阅读顺序以 [AGENTS.md](../AGENTS.md) 为唯一权威。本页只保留 `docs/` 模块入口，不重复细则。

## 文档治理规则

- `project-maintenance/` 不冒充能力合同层；`harness/` 承接 Harness-first 主线，不恢复已退役 adjacent-system
- `docs/` 不长期承载 `suspended`/scratch 文档；暂停共享文档应转为 `superseded`，非共享草稿移出 `docs/`
- `docs/` 下除 `README.md` 外正文文档都应保持 `title/status/updated/owner/last_verified` frontmatter
- 新增正文文档后至少更新最近的 `README.md` 入口，不留孤儿文档
- 研究结论一旦准入主线，必须同步升格到 `project-maintenance/`、`harness/`、`toolchain/` 或 `product/` 的承接位

## AI 默认路径

- 先读 `project-maintenance/` 与 `harness/` 入口，确认任务类型
- 需 repo-local workflow 步骤时进 `project-maintenance/`
- 需 Harness doctrine、artifact、catalog 或 workflow family 时进 `harness/`
