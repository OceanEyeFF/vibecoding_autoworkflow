---
title: "路径与文档治理检查运行说明"
status: active
updated: 2026-04-03
owner: aw-kernel
last_verified: 2026-04-03
---
# 路径与文档治理检查运行说明

> 目的：说明如何在本仓库本地执行“路径治理与文档治理”相关的最小回归检查，包括结构检查和少量高价值语义检查。

## 一、适用范围

本页只覆盖轻量治理检查：

- markdown 相对链接是否仍然可达
- 关键主入口文件是否存在
- `path-governance-ai-routing.md` 与 `docs-governance.md` 是否仍被关键入口页回链
- `docs/knowledge/` 主线入口是否仍然完整
- `.gitignore` 是否仍继续忽略关键 hidden layers
- `docs/` 下正文文档的 frontmatter 是否齐全
- `status` 是否仍和目录语义、生命周期语义一致
- `docs/analysis/README.md` 是否仍枚举当前研究文档，并保留对历史执行规划的入口
- foundations / memory-side / module entry 的关键承接关系是否仍存在
- foundations 中关键 authority/template 文档是否被影子文件分叉
- 已退役的 placeholder 口径是否回流到关键入口文档

它不替代人工审阅，也不检查所有 anchor 片段。

## 二、脚本入口

```bash
python3 toolchain/scripts/test/path_governance_check.py

python3 toolchain/scripts/test/governance_semantic_check.py
```

## 三、脚本当前会检查什么

1. `path_governance_check.py`
2. 根入口与文档主线入口是否存在
3. `docs/`、`product/`、`toolchain/`、根入口页和 `.nav/README.md` 内的 markdown 相对链接是否指向存在路径
4. `docs/knowledge/foundations/path-governance-ai-routing.md` 与 `docs/knowledge/foundations/docs-governance.md` 是否仍被关键入口页显式引用
5. `docs/knowledge/README.md` 与关键子入口是否仍存在，并继续链接 Foundations、Memory Side 与 Task Interface 主线
6. `docs/` 下除 `README.md` 以外的正文文档是否仍保留最小 frontmatter
7. `docs/reference/`、`docs/archive/`、`docs/ideas/*/` 以及 `docs/knowledge/`、`docs/operations/`、`docs/analysis/` 的 `status` 是否仍匹配目录与生命周期语义
8. `docs/analysis/README.md` 是否仍回链当前分析文档，包括 `superseded` 的历史执行规划
9. `.gitignore` 是否仍忽略：
   - `.agents/`
   - `.claude/`
   - `.opencode/`
   - `.autoworkflow/`
   - `.spec-workflow/`
10. `governance_semantic_check.py`
11. foundations 最小模板集是否仍存在：
   - `task-contract-template.md`
   - `context-entry-template.md`
   - `writeback-log-template.md`
   - `decision-record-template.md`
   - `module-entry-template.md`
12. 关键承接关系是否仍存在：
   - `toolchain-layering.md -> toolchain/scripts/README.md`
   - `toolchain-layering.md -> toolchain/evals/README.md`
   - `context-routing.md -> context-entry-template.md`
   - `writeback-cleanup.md -> writeback-log-template.md`
   - 模块入口 README -> `module-entry-template.md`
13. foundations 权威文档是否出现同名前缀 shadow 文件
14. 关键入口文档是否重新出现已退役的“预留位 / 占位”口径

说明：

- `.serena/` 当前不在这组忽略项里，因为本仓库允许受控保留项目级 Serena 配置与记忆
- `.opencode/` 与 `.agents/`、`.claude/` 一样，属于 repo-local mount/deploy target，运行说明只负责确认它仍然被忽略，不承担它的生成逻辑

## 四、什么时候运行

- 调整主入口或 foundations 文档后
- 新增模块入口页后
- 清理 `.nav/` 或 hidden-layer 说明后
- 准备让其他 AI 后端复用当前入口体系前

## 五、如何理解结果

- 返回码 `0`：当前最小治理检查通过
- 返回码非 `0`：存在坏链、缺失入口、缺失回链或 `.gitignore` 边界回退

失败时脚本会直接列出具体问题，优先按输出顺序修复。

## 六、当前限制

- 不检查 markdown anchor 是否存在
- 不检查完整文案语义是否自洽；当前只做固定规则的最小语义检查
- 不判断 `.nav/` 的历史软链是否应删除，只验证文档和主入口是否仍受控
