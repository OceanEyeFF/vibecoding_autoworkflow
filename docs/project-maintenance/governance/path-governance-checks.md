---
title: "路径与文档治理检查运行说明"
status: active
updated: 2026-04-26
owner: aw-kernel
last_verified: 2026-04-26
---
# 路径与文档治理检查运行说明

> 目的：说明如何在本仓库本地执行“路径治理与文档治理”相关的最小回归检查，包括结构检查和少量高价值语义检查。

本页属于 [Governance](./README.md) 路径簇。

## 一、适用范围

本页只覆盖轻量治理检查：

- markdown 相对链接是否仍然可达
- 关键主入口文件是否存在
- `AGENTS.md` 是否仍被关键入口页回链
- `docs/project-maintenance/` 与 `docs/harness/` 主线入口是否仍然完整
- `.gitignore` 是否仍继续忽略关键 hidden layers
- `docs/` 下正文文档的 frontmatter 是否齐全
- `status` 是否仍和目录语义、生命周期语义一致
- `docs/` 正文是否错误使用 `status: suspended`
- foundations / memory-side / module entry 的关键承接关系是否仍存在
- foundations 中关键 authority/template 文档是否被影子文件分叉
- 已退役的 placeholder 口径是否回流到关键入口文档
- `product/harness/` 是否仍保持最小 executable root 骨架，而没有回退成 doctrine 正文区
- `docs/harness/workflow-families/` 是否仍明确承接文档真相；若链接 `product/harness/`，也只把它当作下游 executable root

它不替代人工审阅，也不检查所有 anchor 片段。

## 二、脚本入口

运行治理脚本时默认保留 `PYTHONDONTWRITEBYTECODE=1`，避免检查过程自己在源码树中生成 `__pycache__` / `.pyc`。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/folder_logic_check.py

PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py

PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/governance_semantic_check.py
```

## 三、脚本当前会检查什么

1. `folder_logic_check.py`
2. 根目录对象是否仍落在声明的 allowlist 内：
   - 正式内容区：`product/`、`docs/`、`toolchain/`
   - repo-local execution config：`.codex/`
   - mount / state / navigation：`.agents/`、`.claude/`、`.opencode/`、`.aw/`、`.autoworkflow/`、`.spec-workflow/`、`.nav/`
   - compatibility shim：`tools/`
   - local ephemeral cache：`.pytest_cache/`
   - entry / infra：`README.md`、`INDEX.md`、`GUIDE.md`、`ROADMAP.md`、`AGENTS.md`、`CONTRIBUTING.md`、`.github/`、`.git*`、`.claudeignore`、`LICENSE`
3. `product/`、`docs/`、`toolchain/` 的一级子目录是否仍符合 allowlist
4. 典型错放内容是否仍被拦截：
   - `product/` 中的 runbook、缓存、logs、state/runtimes
   - `docs/` 中的脚本、可执行文件、运行产物、缓存
   - `toolchain/` 中的 canonical 业务源码目录、repo-local mount/state 内容、运行日志、运行缓存和 Python bytecode
   - `tools/` 中的 Python / pytest 运行缓存
5. hidden/state/mount 层的 tracked 真实状态是否仍受控：
   - `.agents/skills/`、`.claude/skills/`、`.opencode/skills/` 允许 tracked 的 repo-local install payload
   - 这些目录之外的 mount-layer tracked 内容仍应失败
   - `.codex/` 只允许 `config.toml` 与 `rules/repo.rules`
   - `tools/` 只允许显式 compat shim tracked 文件
   - `.pytest_cache/` 允许本地存在，但 tracked 时失败
6. `.nav/` 是否仍只包含 `README.md`、`@docs`、`@skills`
7. `.nav/@docs` 与 `.nav/@skills` 是否仍为 symlink，并在标准化后解析到合法目标
8. `path_governance_check.py`
9. 根入口与文档主线入口是否存在
10. `docs/`、`product/`、`toolchain/`、根入口页和 `.nav/README.md` 内的 markdown 相对链接是否指向存在路径
11. `AGENTS.md` 是否仍被关键入口页显式引用
12. `docs/harness/README.md` 与关键子入口是否仍存在，并继续链接 foundations / scope / artifact / Skills / adjacent-systems / workflow-families
13. `docs/` 下除 `README.md` 以外的正文文档是否仍保留最小 frontmatter
14. `docs/project-maintenance/` 与 `docs/harness/` 的 `status` 是否仍匹配目录与生命周期语义
15. `docs/` 正文文档是否仍避免使用 `status: suspended`；暂停中的共享文档应改成 `superseded`，非共享 scratch 应移出 `docs/`
16. `docs/project-maintenance/README.md` 与 `docs/harness/README.md` 是否仍维持当前入口分流
17. `.gitignore` 是否仍忽略：
   - `.aw/`
   - `.agents/`
   - `.claude/`
   - `.opencode/`
   - `.autoworkflow/`
   - `.spec-workflow/`
18. `governance_semantic_check.py`
19. 关键承接关系是否仍存在：
   - `toolchain/toolchain-layering.md -> toolchain/scripts/README.md`
   - `context-routing.md -> context-routing-output-format.md`
   - `writeback-cleanup.md -> writeback-cleanup-output-format.md`
20. foundations 权威文档是否出现同名前缀 shadow 文件
21. 关键入口文档是否重新出现已退役的“预留位 / 占位”口径
22. 相邻系统文档是否已清理对已删除 product roots 的坏链，且没有把 adjacent systems 重新写回新的源码根
23. `product/harness/README.md`、`product/harness/skills/README.md` 与 `product/harness/adapters/README.md` 是否仍作为最小 executable root 骨架存在
24. `docs/harness/workflow-families/README.md` 与 `docs/harness/workflow-families/repo-evolution/README.md` 是否仍把 `docs/` 作为 ontology 上游，而不是反向从 `product/harness/` 生长定义

说明：

- `.agents/`、`.claude/`、`.opencode/` 仍应默认被 `.gitignore` 忽略；允许 tracked 的 install payload 属于受控例外，不改变默认忽略策略
- `folder_logic_check.py` 使用 `git ls-files` 的真实 tracked 状态，而不只看 `.gitignore`

## 四、什么时候运行

- 调整主入口或 foundations 文档后
- 新增模块入口页后
- 清理 `.nav/` 或 hidden-layer 说明后
- 调整根目录对象分类或 tracked 白名单后
- 准备让其他 AI 后端复用当前入口体系前

## 五、如何理解结果

- 返回码 `0`：当前最小治理检查通过
- 返回码非 `0`：存在结构违规、坏链、缺失入口、缺失回链或 `.gitignore` 边界回退

失败时脚本会直接列出具体问题；`folder_logic_check.py` 还会输出稳定 issue code，便于 gate 和测试锁定。

## 六、当前限制

- 不检查 markdown anchor 是否存在
- 不检查完整文案语义是否自洽；当前只做固定规则的最小语义检查
- 不验证 `.nav/` 目标页面的语义是否正确；当前只检查 slot、symlink 形态和目标集合是否合法
