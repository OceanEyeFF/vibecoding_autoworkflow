---
title: "Autoresearch 开发记录"
status: superseded
updated: 2026-04-09
owner: aw-kernel
last_verified: 2026-04-09
---
# Autoresearch 开发记录

> 当前状态：本文保留为 `autoresearch` 已验证开发记录的历史叶子页，不是当前默认入口。
>
> 当前 operations 入口请先回到 [Operations README](./README.md)；日常 runbook 仍以：
>
> - [Autoresearch 最小闭环运行说明](./autoresearch-minimal-loop.md)
> - [Research CLI 指令](./research-cli-help.md)
> - [TMP Exrepo 维护说明](./tmp-exrepo-maintenance.md)
>
> 为准。本文继续只保留 lineage / audit / recent-history 价值。
>
> 目的：为当前仓库的 `autoresearch` 保留一份 repo-local 开发记录页，用来承接“最近做了什么、哪些事实已验证、后续应关注什么”。本文属于 `docs/operations/`，当前只保留维护记录与审计价值，不替代 `docs/knowledge/` 的模块边界，也不替代 `toolchain/` 的实现合同。

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

### 当前唯一开发目标

- [Autoresearch：下一阶段 CLI 模块化与插拔化建议](./autoresearch-next-stage-cli-modularity-plan.md)

当前约束：

- 当前只保留这一个 `autoresearch` 开发目标作为默认关注面。
- 之前的目标与实现记录继续保留，但只作为 archived records，不再作为默认开发入口。

## 四、归档记录

### 2026-04-09：切换为“唯一当前开发目标”模式

主题：

- 把 `autoresearch` 当前默认开发面收敛为唯一目标，并将之前仍暴露为 active 的旧目标改做归档 lineage。

已验证事实：

- 当前唯一保留的开发目标入口为：
  - `docs/operations/autoresearch-next-stage-cli-modularity-plan.md`
- 旧的两个 `autoresearch` task-plan 已从默认当前目标中退出：
  - `历史规划（已移除）: autoresearch-p2-tmp-exrepo-runtime-task-plan.md`
  - `历史规划（已移除）: autoresearch-p2-repo-prompt-guidance-task-plan.md`
- 已移除旧研究目录入口，当前只把该目标作为默认关注面。
- `governance_semantic_check.py` 已通过。

承接位置：

- `docs/operations/autoresearch-next-stage-cli-modularity-plan.md`
- `旧研究目录入口（已移除）`
- `历史规划（已移除）: autoresearch-p2-tmp-exrepo-runtime-task-plan.md`
- `历史规划（已移除）: autoresearch-p2-repo-prompt-guidance-task-plan.md`

验证：

- `python3 toolchain/scripts/test/governance_semantic_check.py`

后续关注：

- 后续如需重新激活某个旧目标，必须显式重新准入，而不是直接把 archived planning 恢复成默认入口。

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

## 五、相关文档

- [Autoresearch 最小闭环运行说明](./autoresearch-minimal-loop.md)
- [Research CLI 指令](./research-cli-help.md)
- [TMP Exrepo 维护说明](./tmp-exrepo-maintenance.md)
- [Autoresearch：下一阶段 CLI 模块化与插拔化建议](./autoresearch-next-stage-cli-modularity-plan.md)
- [Autoresearch 模块总览](../knowledge/autoresearch/overview.md)
