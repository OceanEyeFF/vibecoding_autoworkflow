# Harness Adapters

`product/harness/adapters/` 承接 Harness backend wrapper source。

当前阶段：

- `agents/` 已落 first-wave thin-shell payload source
- adapter wrapper 继续服务于 `product/harness/skills/` 的 canonical executable source
- 后续 adapter 应服务于 `product/harness/skills/` 的 canonical executable source
- `docs/harness/` 仍然是语义上游真相层

当前入口：

- [agents/README.md](./agents/README.md)：`agents` backend 的 first-wave thin-shell payload source

这里适合放：

- backend wrapper 源码
- 后端适配说明

这里不适合放：

- ontology 正文
- repo-local deploy target
- 运行期状态
