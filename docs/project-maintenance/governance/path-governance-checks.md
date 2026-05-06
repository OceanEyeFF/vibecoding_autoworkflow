---
title: "路径与文档治理检查运行说明"
status: active
updated: 2026-05-06
owner: aw-kernel
last_verified: 2026-05-06
---
# 路径与文档治理检查运行说明

> 目的：说明如何在本仓库本地执行"路径治理与文档治理"相关的最小回归检查，包括结构检查和少量高价值语义检查。

本页属于 [Governance](./README.md) 路径簇。

## 一、适用范围

本页只覆盖轻量治理检查：markdown 相对链接可达性、关键入口文件存在性、AGENTS.md 回链、主线入口完整性、.gitignore hidden layer 忽略、frontmatter 与 status 语义、status:suspended 误用、承接关系一致性、foundations 影子文件、已退役 placeholder 回流、product/harness/ 最小 executable root 骨架、workflow-families 文档真相定位。不替代人工审阅，不检查所有 anchor 片段。根兼容入口当前只保留 `README.md`、`INDEX.md` 与 `AGENTS.md`；已退役的 `GUIDE.md` 和 `ROADMAP.md` 不再作为必需入口。

## 二、脚本入口

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/folder_logic_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/governance_semantic_check.py
```

## 三、脚本当前会检查什么

1. `folder_logic_check.py` — 根目录 object 是否在 allowlist（`product/`、`docs/`、`toolchain/`、`.codex/`、`.agents/`、`.claude/`、`.aw/`、`.autoworkflow/`、`.spec-workflow/`、`.nav/`、`tools/`、`.pytest_cache/`、入口/基础设施文件，包括 Claude Code 适配入口 `CLAUDE.md`）；裸 `.pyc`/`.pyo` 不允许
2. `product/`、`docs/`、`toolchain/` 一级子目录合规；错放内容拦截（product 无 runbook/缓存/state，docs 无可执行/缓存，toolchain 无业务源码/mount，tools 无 Python 缓存）
3. hidden/state/mount 层 tracked 状态受控：`.agents/`、`.claude/` tracked 即失败；`.codex/` 仅 `config.toml`+`rules/repo.rules`；`tools/` 仅显式 compat shim；`.pytest_cache/` tracked 即失败
4. `.nav/` 仅含 `README.md`、`@docs`、`@skills`；`@docs` 与 `@skills` 是 symlink 且解析到合法目标
5. `path_governance_check.py` — 根入口与主线入口存在且 markdown 相对链接可达；`AGENTS.md` 被关键入口页引用
6. `docs/harness/README.md` 及子入口存在，继续链接 foundations/scope/artifact/Skills/workflow-families
7. `docs/` 正文保留 frontmatter；`project-maintenance/` 与 `harness/` status 匹配语义；无 `status:suspended` 误用
8. `.gitignore` 忽略 `.aw/`、`.agents/`、`.claude/`、`.autoworkflow/`、`.spec-workflow/`、`**/__pycache__/`、`.pytest_cache/`、`*.pyc`、`*.pyo`
9. `governance_semantic_check.py` — 关键承接关系存在（toolchain-layering -> scripts、docs/harness -> 子入口、product/harness -> docs/harness、artifact/worktrack -> contract/queue/gate）
10. foundations 无同名前缀 shadow 文件；关键入口无已退役 placeholder 回流；根兼容入口不引用已退役 adjacent-systems
11. `product/harness/` 及子目录保持最小 executable root 骨架
12. `docs/harness/workflow-families/` 把 `docs/` 作 ontology 上游，不从 `product/harness/` 反向定义

## 四、什么时候运行

调整主入口/foundations、新增入口页、清理 `.nav/`/hidden-layer、调整根目录分类/tracked 白名单后，或准备复用入口体系前。

## 五、如何理解结果

返回码 `0` 通过；非 `0` 表示违规/坏链/缺失入口/`.gitignore` 回退。失败时脚本列出具体问题；`folder_logic_check.py` 输出 issue code 便于 gate 锁定。

## 六、当前限制

不检查 markdown anchor、完整语义自洽性、`.nav/` 目标语义正确性；只做固定规则的最小语义检查。
