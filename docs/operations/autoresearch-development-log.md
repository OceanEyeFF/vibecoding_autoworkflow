---
title: "Autoresearch 开发记录"
status: active
updated: 2026-04-09
owner: aw-kernel
last_verified: 2026-04-09
---
# Autoresearch 开发记录

> 目的：为当前仓库的 `autoresearch` 保留一份 repo-local、可持续追加的开发记录页，用来承接“最近做了什么、哪些事实已验证、后续应关注什么”。本文属于 `docs/operations/`，是维护记录与协作入口，不替代 `docs/knowledge/` 的模块边界，也不替代 `toolchain/` 的实现合同。

## 一、适用范围

本文适合承接：

- 已验证的 `autoresearch` 开发里程碑
- 最近新增的 operator-facing 能力
- 已确认的结构性问题与维护注意事项
- 后续开发建议对应的最近承接点

本文不适合承接：

- 未验证的猜测
- 单次对话推理
- 详细任务拆解正文
- `.autoworkflow/` 运行时原始日志

## 二、记录规则

每次追加记录时，优先保留下面四类信息：

1. 变更主题
2. 已验证事实
3. 承接文件或入口
4. 下一步关注点

建议格式：

- 日期
- 主题
- 已验证事实
- 承接位置
- 验证
- 后续关注

只记录已经通过代码、测试、文档治理检查或实际 run 确认的内容。

## 三、当前记录

### 2026-04-09：补齐下一阶段 CLI 模块化与插拔化建议入口

主题：

- 明确把 `autoresearch` 的下一阶段问题收敛到“更适合 `codex | claude` 交互使用的 CLI 软件”，并把“当前最大问题是模块化和插拔性不足”固定为可引用建议。

已验证事实：

- 当前仓库此前没有专门承接该建议的 active `autoresearch` 文档页。
- 已新增 `analysis` 文档：
  - `docs/analysis/autoresearch-next-stage-cli-modularity-plan.md`
- `docs/analysis/README.md` 已补入口。
- `governance_semantic_check.py` 已通过。

承接位置：

- `docs/analysis/autoresearch-next-stage-cli-modularity-plan.md`
- `docs/analysis/README.md`

验证：

- `python3 toolchain/scripts/test/governance_semantic_check.py`

后续关注：

- 若下一阶段真正开工，应从该建议页继续收敛成更小的 task-plan，而不是直接做大重构。

### 2026-04-08：新增 autoresearch run/skill 状态索引

主题：

- 为 `autoresearch` 增加 run 级与 skill 级状态聚合，方便 operator 判断当前训练进度和覆盖面。

已验证事实：

- 已新增状态聚合模块：
  - `toolchain/scripts/research/autoresearch_status.py`
- `run_autoresearch.py` 已支持：
  - `refresh-status`
- 当前状态索引固定落到：
  - `.autoworkflow/autoresearch/run-status-index.json`
  - `.autoworkflow/autoresearch/skill-training-status.json`
- 已接入 `autoresearch` 的 canonical skill 当前固定为：
  - `context-routing-skill`
  - `knowledge-base-skill`
  - `task-contract-skill`
  - `writeback-cleanup-skill`
- 未接入 `autoresearch` 的 canonical skill 在 skill 状态索引中会显式标为 `not_supported_by_autoresearch`，不会再与 `not_started` 混淆。

承接位置：

- `toolchain/scripts/research/autoresearch_status.py`
- `toolchain/scripts/research/run_autoresearch.py`
- `docs/operations/research-cli-help.md`
- `docs/operations/autoresearch-minimal-loop.md`

验证：

- `python3 -m pytest toolchain/scripts/research/test_autoresearch_status.py toolchain/scripts/research/test_run_autoresearch.py`

后续关注：

- 后续如需更适合人读的 operator 视图，应在当前 JSON 索引之上加 summary 层，而不是把 authority / state artifact 直接改成人工 UI。

## 四、相关文档

- [Autoresearch 最小闭环运行说明](./autoresearch-minimal-loop.md)
- [Research CLI 指令](./research-cli-help.md)
- [TMP Exrepo 维护说明](./tmp-exrepo-maintenance.md)
- [Autoresearch：下一阶段 CLI 模块化与插拔化建议](../analysis/autoresearch-next-stage-cli-modularity-plan.md)
- [Autoresearch 模块总览](../knowledge/autoresearch/overview.md)
