# Harness Skills

`docs/harness/Skills/` 承接 `Codex` 语境下的 Harness skill catalog。

这里不再额外维护一层 `Function -> Skill` 的转译目录，而是直接回答：

- 当前 Harness 在 `Codex` 中需要哪些 skills
- 这些 skills 分别服务于哪个控制层级
- 哪些已经有 canonical executable source
- 哪些仍只是 catalog 中的目标位

当前入口：

- [catalog/README.md](./catalog/README.md)：按 supervisor / `RepoScope` / `WorktrackScope` 组织的 skill catalog

边界：

- 这里是 skill catalog，不是 doctrine 主文档
- 真正的控制思想以上游 [../foundations/Harness指导思想.md](../foundations/Harness指导思想.md) 和 [../foundations/Harness运行协议.md](../foundations/Harness运行协议.md) 为准
- 真正的 canonical executable source 以下游 [../../../product/harness/skills/README.md](../../../product/harness/skills/README.md) 为准
