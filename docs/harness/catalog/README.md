---
title: Harness Skill Catalog
status: active
updated: 2026-04-27
owner: aw-kernel
last_verified: 2026-04-27
---

# Harness Skill Catalog

`docs/harness/catalog/` 承接 `Codex` 语境下的 Harness skill catalog。

这里不再额外维护一层 `Function -> Skill` 的转译目录，而是直接回答：

- 当前 Harness 在 `Codex` 中需要哪些 skills
- 这些 skills 分别服务于哪个控制层级
- 哪些已有 canonical executable source
- 哪些仍只是 catalog 目标位

当前入口：

- [supervisor.md](./supervisor.md)：顶层 supervisor 入口
- [repo.md](./repo.md)：RepoScope 能力入口
- [worktrack.md](./worktrack.md)：WorktrackScope 能力入口

边界：

- 这里是 skill catalog，不是 doctrine 主文档
- 这组规则依托上游 [../foundations/Harness指导思想.md](../foundations/Harness指导思想.md) 和 [../foundations/Harness运行协议.md](../foundations/Harness运行协议.md)
- 可执行源入口仍以 [../../../product/harness/skills/README.md](../../../product/harness/skills/README.md) 为准
