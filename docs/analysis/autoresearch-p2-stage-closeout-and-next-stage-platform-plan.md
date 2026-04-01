---
title: "Autoresearch P2：阶段收口与下一阶段平台期规划"
status: active
updated: 2026-04-01
owner: aw-kernel
last_verified: 2026-04-01
---
# Autoresearch P2：阶段收口与下一阶段平台期规划

> 说明：本文只固定当前阶段结束后的平台期工作规划，不直接驱动新的功能施工，也不替代 `docs/operations/` 的现行 runbook。目标是先把本阶段产出、清理边界、暴露问题和下一阶段入口收拢成一份受控计划，再决定下一轮 implementation contract。

## 一、当前定位

当前 `autoresearch P2` 已经具备：

- 单 prompt、`codex -> codex`、最多 `max_rounds` 的轻量闭环
- `prepare-round -> worker -> run-round -> decide-round` 的连续 loop 包装器
- 最小 stop gate：
  - `max_rounds_reached`
  - `no_new_validation_champion`
  - `mutation_families_exhausted_without_keep`
- `/tmp exrepo + materialized suite` 的运行时路径
- 基于 `feedback-ledger.jsonl` 的粗粒度 family signal 调度

当前平台期不做：

- 直接继续扩写新的训练机制
- 直接上多步 feedback-to-mutation 自动化
- 直接把 prompt 训练扩成通用优化平台

## 二、本阶段工作总结

### 1. 已稳定承接的代码与运行边界

- `run_autoresearch.py`、`autoresearch_round.py`、`run_autoresearch_loop.py` 已形成可执行的最小 P2 闭环
- `manage_tmp_exrepos.py`、`exrepo_runtime.py`、materialized suite 路径已承接 `/tmp exrepo` 运行时
- stop gate 已有实现与自动化覆盖，能够正常结束 loop，而不是只依赖人工终止
- `docs/operations/autoresearch-minimal-loop.md`、`docs/operations/research-cli-help.md`、`toolchain/scripts/research/README.md` 已描述当前真实运行边界

### 2. 已完成的实跑与观察

- 已完成 `context-routing-skill` 的 `6/3/3` loop，并补跑 acceptance，用于看不同 round 的 baseline / train / validation / test 表现
- 已完成 `knowledge-base-skill` 的 `6/3/3` loop，用于验证 stop gate 能否在真实运行中触发
- 已完成本仓库上的 `knowledge-base-skill` 单点 direct run，用于观察 prompt 在“本仓库知识层”上的输出质量

### 3. 当前阶段的结论

- `context-routing-skill` 已证明最小 loop 可跑，但 round 改善并不稳定
- `knowledge-base-skill` 当前低分主因不是 parse/timeout，而是 `mainline_entrypoint_identification` 与 `mode_and_layer_modeling` 经常只拿到部分分
- 现有 `feedback_distill` 能提供方向信号，但还不能把 repo 级错因转成下一轮足够具体的 prompt 修改建议

## 三、平台期清理规划

### A. 文档体系清理

目标：

- 把本阶段新增的 run 观察、收口结论和 still-active planning 关系整理清楚
- 避免 `docs/analysis/` 同时挂过多旧 planning 入口，导致后续 AI 把 lineage 文档误读成当前执行入口

平台期任务：

- 审核 `docs/analysis/README.md` 的当前入口清单，区分：
  - 仍作为当前 planning 的文档
  - 只保留 lineage 的历史 planning 文档
- 为本阶段已收口的运行实验补一页简短复盘或在现有文档中补“截至 2026-04-01 的运行观察”
- 对已不再驱动实现的 planning 文档补 `superseded` 状态和去入口动作

### B. 训练缓存与运行产物清理

目标：

- 保留必要 lineage 与可复核 run
- 清掉不再有直接分析价值的旧缓存，避免 `.autoworkflow/` 持续膨胀

平台期任务：

- 建立 run 产物分层：
  - 必留：本阶段的代表性 baseline / round / acceptance 结果
  - 可归档：旧实验、已失效 prompt 变体、仅用于临时观察的 direct run
  - 可删除：重复、失败且无分析价值的缓存
- 对 `.autoworkflow/autoresearch-archive/`、`.autoworkflow/manual-runs/`、`.autoworkflow/manual-runs/*/acceptance-worktrees/` 做一次保留策略盘点
- 把“何时归档，何时删除”沉淀到 repo-local runbook，而不是继续靠人工记忆

说明：

- 本文只规划清理，不在这里直接执行删除动作

## 四、本阶段暴露出的工作问题

### 1. 评分信号强度不足

- eval 结果里已经有 `dimension_feedback` 和 `key_issues`
- 但进入 loop 的 `feedback-ledger.jsonl` 后，只剩下 score delta、signal 和少量通用 `suggested_adjustments`
- 结果是 mutation family 能被排序，但具体错因不能稳定传回下一轮 worker

### 2. prompt mutation 仍偏试探式

- 当前 registry entry 的 `instruction_seed` 仍主要靠人工猜想
- 没有一层把“跨 repo 重复出现的低分模式”显式压缩成 mutation proposal
- 导致 loop 更像 bandit 试探，而不是面向错因的稳定改进

### 3. 评测任务与目标 prompt 的耦合仍偏弱

- `knowledge-base-skill` 的评分规则更看重“入口角色识别”和“证据约束”
- 但原 prompt 没有强制区分 truth layer 与 navigation entrypoint，也没有强制在 agent-facing entrypoint 存在时显式列出
- 这类任务级约束没有在 prompt 模板层形成系统化的“易错模式清单”

### 4. 平台卫生动作缺少固定节奏

- 训练缓存归档已经发生过一次，但仍主要依赖人工判断
- 旧 planning、run artifacts、acceptance worktrees、manual direct runs 的保留规则还没有变成固定 checklist

## 五、下一阶段平台期任务

### T-201：阶段收口与入口校准

目标：

- 统一本阶段代码、runbook、analysis 入口状态

范围：

- `docs/analysis/README.md`
- 必要时，相关 `analysis` 文档 frontmatter 与入口说明

完成标准：

- 当前执行规划入口清单准确
- 不再把历史 planning 当当前执行入口

### T-202：训练缓存保留策略与归档 runbook

目标：

- 固定 `.autoworkflow/` 运行产物的保留、归档、删除规则

范围：

- `docs/operations/`
- 必要时，补一页针对 research/autoresearch artifact hygiene 的 repo-local runbook

完成标准：

- 对 run artifacts 有明确“必留 / 可归档 / 可删除”规则
- 不需要再靠口头约定决定缓存清理

### T-203：P2 训练闭环问题审计

目标：

- 只做问题审计，不直接改实现，明确当前 loop 哪些位置已经成为下一阶段的真实瓶颈

重点问题：

- feedback distill 是否过度压缩
- mutation seed 是否缺少错因约束
- scoreboard / eval 结果如何转为下一步可消费的训练输入

完成标准：

- 形成一页明确的问题清单，能直接承接下一阶段 implementation contract

### T-204：下一阶段 implementation 入口文档

目标：

- 在问题审计完成后，单独写下一阶段 task plan

要求：

- 先收敛为一个最小 implementation topic
- 不把“prompt 改写、feedback 蒸馏、selector 逻辑、自动 proposal”并成一个大任务

建议优先级：

1. 先做“细反馈保留 contract”而不是自动 proposal
2. 再决定是否需要“反馈到 mutation seed”的下一步

## 六、平台期退出条件

- 文档入口与 planning 状态已校准
- 运行产物保留策略已固定
- 当前 loop 的主要工作问题已形成独立审计结论
- 下一阶段只剩一份收敛后的 implementation task plan，而不是继续在平台期里混跑实现
