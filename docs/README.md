# Docs

`docs/` 是当前仓库的第二块正式内容区，负责承载文档真相、仓库操作说明、研究记录、外部参考和 ideas 生命周期。

## 当前结构

- `knowledge/`：canonical truth 与基础治理文档
- `operations/`：repo-local runbook、部署和维护说明
- `analysis/`：benchmark、评测、研究闭环
- `reference/`：外部导入资料
- `ideas/`：未准入主线的想法，按生命周期管理
- `archive/`：已退役资料

## 阅读顺序

1. `knowledge/foundations/root-directory-layering.md`
2. `knowledge/foundations/path-governance-ai-routing.md`
3. `knowledge/foundations/toolchain-layering.md`
4. 目标领域目录，例如 `knowledge/memory-side/`
5. 需要实际部署或评测时，再读 `operations/` 与 `analysis/`

## 文档治理规则

- `knowledge/` 不放 repo-local guide、benchmark 说明或外部参考
- `operations/` 不冒充真相层
- `analysis/` 不承载当前主线规则
- `reference/` 只做参考，不做执行入口
- `ideas/active/`、`ideas/incubating/`、`ideas/archived/` 的目录语义必须和 frontmatter `status` 一致

## AI 默认路径

- 先读 `knowledge/` 的主线入口
- 需要 repo-local 步骤时再进入 `operations/`
- 需要评测和研究时再进入 `analysis/`
- 不默认把 `reference/`、`ideas/`、`archive/` 推进执行主线
