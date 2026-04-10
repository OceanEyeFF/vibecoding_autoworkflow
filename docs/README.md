# Docs

`docs/` 是当前仓库的第二块正式内容区，负责承载文档真相、仓库操作说明和外部参考。

## 核心定位

- 本项目是一个 AI coding 的 repo-side contract layer。
- `docs/` 只负责路径、分层、阅读边界和真相落点，不负责具体 `skills / agents / subagents` 的实现设计。
- 具体的 canonical skills 与 adapters 在 `product/`，部署、评测和治理脚本在 `toolchain/`。
- 如果 AI 进入仓库后能立刻知道先读什么、先不要读什么、改完后写回哪里，那么 `docs/` 就发挥了作用。

## 当前结构

- `knowledge/`：canonical truth、基础治理、文档治理基线与稳定模块入口
- `operations/`：repo-local runbook、部署和维护说明
- `reference/`：外部导入资料

## 阅读顺序

默认阅读顺序以 [AGENTS.md](../AGENTS.md) 为唯一权威。
本页只保留 `docs/` 模块入口，不重复 `read_first/read_next/do_not_read_yet` 细则。

## 文档治理规则

- `knowledge/` 不放 repo-local guide、benchmark 说明或外部参考
- `operations/` 不冒充真相层
- `docs/` 不长期承载 `suspended` / scratch 文档；需要共享保留的暂停文档应转为 `superseded`，非共享草稿应移出 `docs/`
- `reference/` 只做参考，不做执行入口
- `docs/` 下除 `README.md` 之外的正文文档，都应保持 `title / status / updated / owner / last_verified` frontmatter
- 新增正文文档后，至少更新最近的 `README.md` 入口，不留下孤儿文档
- 研究结论一旦准入主线，必须同步升格到 `knowledge/`、`operations/`、`toolchain/` 或 `product/` 的承接位

## AI 默认路径

- 先读 `knowledge/` 的主线入口
- 需要 repo-local 步骤时再进入 `operations/`
- 需要外部背景时再进入 `reference/`
