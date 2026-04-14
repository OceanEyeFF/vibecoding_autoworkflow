# Docs

`docs/` 是当前仓库的第二块正式内容区，负责承载文档真相和仓库操作说明。

## 核心定位

- 本项目的核心目标，是构建一个 `Codex-first` 的 AI coding harness 平台、将其分发到多个项目中使用，并建设一个面向 skills 的 `autoresearch` 系统。
- 当前仓库以 AI coding 的 repo-side contract layer 形态承接这些目标。
- `docs/` 只负责路径、分层、阅读边界和真相落点，不负责具体 `skills / agents / subagents` 的实现设计。
- 具体的 canonical skills 与 adapters 在 `product/`，部署、评测和治理脚本在 `toolchain/`。
- 如果 AI 进入仓库后能立刻知道先读什么、先不要读什么、改完后写回哪里，那么 `docs/` 就发挥了作用。

## 当前结构

- [project-maintenance/README.md](./project-maintenance/README.md)：项目维护、治理、deploy 与 backend usage
- [deployable-skills/README.md](./deployable-skills/README.md)：可部署能力的 canonical truth 与合同
- [autoresearch/README.md](./autoresearch/README.md)：`autoresearch` 模块的 knowledge、references 与 runbooks

## 阅读顺序

默认阅读顺序以 [AGENTS.md](../AGENTS.md) 为唯一权威。
本页只保留 `docs/` 模块入口，不重复 `read_first/read_next/do_not_read_yet` 细则。

## 文档治理规则

- `project-maintenance/` 不冒充能力合同层
- `deployable-skills/` 不承载 repo-local runbook 或 operator 手册
- `autoresearch/` 只承接 `autoresearch` 模块本身的文档，不替代通用知识层
- `docs/` 不长期承载 `suspended` / scratch 文档；需要共享保留的暂停文档应转为 `superseded`，非共享草稿应移出 `docs/`
- `docs/` 下除 `README.md` 之外的正文文档，都应保持 `title / status / updated / owner / last_verified` frontmatter
- 新增正文文档后，至少更新最近的 `README.md` 入口，不留下孤儿文档
- 研究结论一旦准入主线，必须同步升格到 `project-maintenance/`、`deployable-skills/`、`autoresearch/`、`toolchain/` 或 `product/` 的承接位

## AI 默认路径

- 先读 `project-maintenance/` 与 `deployable-skills/` 的入口，确认当前任务是维护问题还是能力合同问题
- 需要 repo-local workflow 步骤时进入 `project-maintenance/`
- 需要技能合同与格式时进入 `deployable-skills/`
- 任务明确属于 `autoresearch` 模块时，再进入 `autoresearch/`
