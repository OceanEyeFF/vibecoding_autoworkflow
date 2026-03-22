---
title: "路径治理检查运行说明"
status: active
updated: 2026-03-22
owner: aw-kernel
last_verified: 2026-03-22
---
# 路径治理检查运行说明

> 目的：说明如何在本仓库本地执行“路径治理与 AI 告知”相关的最小回归检查。

## 一、适用范围

本页只覆盖轻量治理检查：

- markdown 相对链接是否仍然可达
- 关键主入口文件是否存在
- `path-governance-ai-routing.md` 是否仍被关键入口页回链
- `.gitignore` 是否仍继续忽略关键 hidden layers

它不替代人工审阅，也不检查所有 anchor 片段。

## 二、脚本入口

```bash
python3 toolchain/scripts/test/path_governance_check.py
```

## 三、脚本当前会检查什么

1. 根入口与文档主线入口是否存在
2. `docs/`、`product/`、`toolchain/`、根入口页和 `.nav/README.md` 内的 markdown 相对链接是否指向存在路径
3. `docs/knowledge/foundations/path-governance-ai-routing.md` 是否仍被关键入口页显式引用
4. `.gitignore` 是否仍忽略：
   - `.agents/`
   - `.claude/`
   - `.autoworkflow/`
   - `.spec-workflow/`

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
- 不检查文案语义是否自洽，只检查高价值结构性回归
- 不判断 `.nav/` 的历史软链是否应删除，只验证文档和主入口是否仍受控
