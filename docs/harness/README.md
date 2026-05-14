# Harness

`docs/harness/` 是当前仓库的 Harness-first 文档主线，承接 Harness doctrine、runtime protocol、scope、artifact contracts、skill inventory、workflow family policy 与设计分析。

本文只做 Harness 文档域入口导航：帮助读者选择最近 owner 和下一跳路径，不承载 doctrine、runtime protocol、artifact contract、workflow policy、设计正文或历史迁移规则。

## 当前分层

| 路径 | 功能 |
| --- | --- |
| [foundations/README.md](./foundations/README.md) | Harness 指导思想、运行协议、跨 skill 公共约束和执行载体选择策略 |
| [scope/README.md](./scope/README.md) | `RepoScope`、`WorktrackScope` 与两层状态闭环 |
| [artifact/README.md](./artifact/README.md) | Repo / Worktrack / Control 正式对象合同与标准字段 |
| [catalog/README.md](./catalog/README.md) | Codex 语境下的 skill inventory、控制层级映射和 skill 影响矩阵 |
| [workflow-families/README.md](./workflow-families/README.md) | 可复用 workflow family、route pattern 与 policy profile |
| `design/` | 尚未升格为 doctrine、artifact contract 或 workflow family 的 Harness 设计方案与变更分析 |

## 阅读边界

| 路径 | 何时读取 |
| --- | --- |
| `foundations/` | 查 Harness 为什么这样运行、运行时怎样停顿/交接/继续 |
| `scope/` | 查 RepoScope、WorktrackScope 或 scope 间状态转移 |
| `artifact/` | 查运行时对象字段、证据、队列、control state、milestone 或 worktrack 合同 |
| `catalog/` | 查有哪些 skill、每个 skill 的职责摘要、控制层级和状态 |
| `workflow-families/` | 查一组 worktrack 如何组成可复用流程或 policy profile |
| `design/` | 查尚未升格的方案比较、影响分析或迁移设计 |

完整 docs 阅读顺序、章节边界和路径维护规则见 [../book.md](../book.md)。Agent boot 与 route contract 见 [../../AGENTS.md](../../AGENTS.md)。

## Owner 边界

| 主题 | 权威 owner |
| --- | --- |
| Doctrine / 指导思想 | [foundations/README.md](./foundations/README.md) |
| Runtime protocol / 运行协议 | [foundations/README.md](./foundations/README.md) |
| Scope / 状态闭环 | [scope/README.md](./scope/README.md) |
| Artifact contracts / 正式对象字段 | [artifact/README.md](./artifact/README.md) |
| Skill inventory / skill 清单 | [catalog/README.md](./catalog/README.md) |
| Workflow policy / workflow family | [workflow-families/README.md](./workflow-families/README.md) |
| Design analysis / 未升格方案分析 | `design/` |
| Executable root / 实现层入口 | [../../product/harness/README.md](../../product/harness/README.md) |
| Executable skill source / 可执行技能源 | [../../product/harness/skills/README.md](../../product/harness/skills/README.md) |

`catalog/` 不承接 doctrine、runtime protocol、artifact contract、workflow policy、设计分析或 executable source。若 catalog 页面为了定位 skill 而引用这些内容，只能作为摘要和反向链接；权威正文仍在对应 owner。
