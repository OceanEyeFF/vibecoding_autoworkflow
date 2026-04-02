---
title: "Autoresearch P1.Final：后续任务规划"
status: superseded
updated: 2026-04-02
owner: aw-kernel
last_verified: 2026-04-02
---
# Autoresearch P1.Final：后续任务规划

> 说明：本文把 `autoresearch-p1-final-code-audit-and-followups.md` 中仍成立的问题拆成可执行任务，用于后续实现排期。它属于 `analysis` 规划文档，不替代 `toolchain/` 当前实现入口，也不替代 `docs/operations/` 的 runbook。

> 当前状态：本文仅保留为 P1 follow-up lineage 叶子页，不是当前默认入口。
>
> 当前 `analysis/` 层分流入口请先回到 [Analysis README](./README.md)；与本文最接近的现行承接位优先以 [autoresearch-p1-final-code-audit-and-followups.md](./autoresearch-p1-final-code-audit-and-followups.md) 和 [toolchain/scripts/research/README.md](../../toolchain/scripts/research/README.md) 为准。

## 一、规划目标

本规划只覆盖当前代码复核后仍成立的 follow-up 问题，目标是：

- 把残留风险拆成可安全落地的独立任务
- 预先说明每个任务的修改边界
- 明确任务间依赖，减少并行时的冲突
- 预估每个任务的思考难度和上下文长度，便于选模型

本规划不覆盖：

- 新的多角色编排
- acceptance lane 常规接入
- 脱离当前 `autoresearch` 轨道的重设计

## 二、排序原则

推荐顺序分三层：

1. 先修 authority / boundary 类问题，再动 feedback 演进层。
2. 先稳定 `prepare-round -> run-round` 的冻结链，再扩 worker-facing context。
3. legacy 退场放在最后，避免过早删兼容路径影响中途验证。

并行原则：

- 任务 1 可以最早独立推进。
- 任务 2 应早于任务 3，任务 3 应早于任务 4。
- 任务 6 可以较早并行推进，并为任务 5、任务 7 提供更好的输入。
- 任务 5、任务 7、任务 8 都依赖前面的 authority / worker-contract 稳定化，适合在中后段推进。

## 三、任务清单

### 任务1：收紧 `target_paths` 为严格子集语义

1. 任务说明，说清楚要解决什么问题|增加什么功能。
   当前 `target_paths` 仍按 overlap 判定是否落在 `contract.mutable_paths` 内，这会放宽 mutation scope。该任务要把校验语义改成真正的“只能收窄，不能放大”，使 P1.1/P1.2 的路径边界与文档约束一致。

2. 任务边界，说清楚预期修改、增加的代码|文档。
   主要修改：
   - `toolchain/scripts/research/autoresearch_mutation_registry.py`
   - `toolchain/scripts/research/autoresearch_round.py`
   - `toolchain/scripts/research/test_autoresearch_mutation_registry.py`
   - `toolchain/scripts/research/test_autoresearch_round.py`
   需要同步更新：
   - `toolchain/scripts/research/README.md`
   - 如有必要，更新 `docs/analysis/autoresearch-p1-1-mutation-registry.md`
   不应修改：
   - `product/`
   - repo-local `.autoworkflow/`

3. 任务的思考难度和上下文长度，需要额外说明推荐使用什么模型+推理等级解决问题。
   思考难度：中。
   上下文长度：中，主要集中在 mutation registry、round guardrail 和对应测试。
   推荐模型：`gpt-5.3-codex` `high`，或 `gpt-5.4` `medium`。

4. 任务依赖，主要说明为什么放在这个排序，前置任务有哪些，可以和哪些任务并行解决。
   这是最早可以独立处理的任务之一，没有强前置依赖。之所以排在前面，是因为它直接决定后续所有 mutation / worker-contract / diff guardrail 的边界。可以和任务 2 并行，但不建议和同样修改 `autoresearch_round.py` 的任务 4 同时写代码。

5. 任务完成判断标准，用于判断什么时候安全结束该任务。
   满足以下条件即可结束：
   - 更宽的父路径会被拒绝
   - 合法收窄路径继续通过
   - 现有 round diff 校验没有被放松
   - README 中对 `target_paths` 的表述与实现一致

### 任务2：明确 registry bookkeeping 的 authority 语义与 tamper 边界

1. 任务说明，说清楚要解决什么问题|增加什么功能。
   当前 `attempts / last_selected_round / last_decision / status` 属于脚本写回状态，但没有被定义成“普通持久化状态”还是“需要防篡改的 authority 字段”。该任务要先定语义，再落下最小保护策略，例如显式 tamper signal、恢复策略或更严格的校验模型。

2. 任务边界，说清楚预期修改、增加的代码|文档。
   主要修改：
   - `toolchain/scripts/research/autoresearch_mutation_registry.py`
   - `toolchain/scripts/research/run_autoresearch.py`
   - `toolchain/scripts/research/autoresearch_round.py`
   - `toolchain/scripts/research/test_autoresearch_mutation_registry.py`
   - `toolchain/scripts/research/test_run_autoresearch.py`
   需要同步更新：
   - `toolchain/scripts/research/README.md`
   - `docs/analysis/autoresearch-p1-final-code-audit-and-followups.md`
   可选：
   - 若语义足够稳定，可升格到 `docs/knowledge/`

3. 任务的思考难度和上下文长度，需要额外说明推荐使用什么模型+推理等级解决问题。
   思考难度：高。
   上下文长度：中到长，需要同时读 registry schema、prepare-round 写回、round authority 加载、history 和测试。
   推荐模型：`gpt-5.4` `high`，或 `gpt-5.3-codex` `high`。

4. 任务依赖，主要说明为什么放在这个排序，前置任务有哪些，可以和哪些任务并行解决。
   建议早于任务 3，因为 crash-safe 方案依赖这里先讲清楚“哪些字段必须可信、哪些字段只是状态”。可以和任务 1 并行。完成后会给任务 3 和任务 8 提供稳定前提。

5. 任务完成判断标准，用于判断什么时候安全结束该任务。
   满足以下条件即可结束：
   - bookkeeping 字段的语义在代码和 README 中被写清楚
   - 针对手工改写的行为有可预测结果，而不是隐含容忍
   - 相关单测覆盖 tamper / mismatch / recovery 分支

### 任务3：收紧 `prepare-round` 的 authority 写盘顺序并补恢复策略

1. 任务说明，说清楚要解决什么问题|增加什么功能。
   当前 `prepare-round` 在 registry 写回和 round authority 冻结之间仍有 crash 窗口。该任务要缩小这个窗口，或者给出明确的 crash recovery 路径，使 `prepare-round` 中断后不会留下难以判读的半提交状态。

2. 任务边界，说清楚预期修改、增加的代码|文档。
   主要修改：
   - `toolchain/scripts/research/run_autoresearch.py`
   - `toolchain/scripts/research/autoresearch_round.py`
   - `toolchain/scripts/research/test_run_autoresearch.py`
   - `toolchain/scripts/research/test_autoresearch_round.py`
   可能新增：
   - prepare recovery 相关测试夹具
   需要同步更新：
   - `toolchain/scripts/research/README.md`
   - `docs/operations/autoresearch-minimal-loop.md`，如果恢复动作需要人工介入

3. 任务的思考难度和上下文长度，需要额外说明推荐使用什么模型+推理等级解决问题。
   思考难度：高。
   上下文长度：长，因为要同时看 prepare 生命周期、active round/runtime、registry、authority snapshot 和 cleanup 逻辑。
   推荐模型：`gpt-5.4` `high`，必要时 `xhigh`。

4. 任务依赖，主要说明为什么放在这个排序，前置任务有哪些，可以和哪些任务并行解决。
   建议依赖任务 2，因为必须先明确 bookkeeping 字段的 authority 语义，才能设计 crash-safe 的写盘顺序。它和任务 4 可以先分析后并行，但不建议并行写代码，因为都会改 `run_autoresearch.py` / `autoresearch_round.py`。

5. 任务完成判断标准，用于判断什么时候安全结束该任务。
   满足以下条件即可结束：
   - 存在明确的 prepare 中断恢复路径
   - registry 与 round authority 不会再轻易进入不可判读状态
   - 单测能复现并验证中断后的恢复或拒绝行为
   - runbook 写清楚人工如何处理残留状态

### 任务4：冻结 worker-contract 的 `comparison_baseline` authority

1. 任务说明，说清楚要解决什么问题|增加什么功能。
   当前 v2 worker-contract 在 `run-round` 里仍会从 run-level baseline scoreboard 重建 `comparison_baseline`。该任务要把 comparison baseline 变成 round 级冻结对象，避免 `prepare-round` 之后外部 baseline 变化导致 envelope 校验失败。

2. 任务边界，说清楚预期修改、增加的代码|文档。
   主要修改：
   - `toolchain/scripts/research/autoresearch_worker_contract.py`
   - `toolchain/scripts/research/autoresearch_round.py`
   - `toolchain/scripts/research/run_autoresearch.py`
   - `toolchain/scripts/research/test_autoresearch_worker_contract.py`
   - `toolchain/scripts/research/test_autoresearch_round.py`
   - `toolchain/scripts/research/test_run_autoresearch.py`
   需要同步更新：
   - `toolchain/scripts/research/README.md`
   - `docs/analysis/autoresearch-p1-2-worker-contract-and-minimal-selector.md`

3. 任务的思考难度和上下文长度，需要额外说明推荐使用什么模型+推理等级解决问题。
   思考难度：高。
   上下文长度：中到长，集中在 worker-contract 生成、round authority、run-round 重建校验和兼容测试。
   推荐模型：`gpt-5.3-codex` `high`，或 `gpt-5.4` `high`。

4. 任务依赖，主要说明为什么放在这个排序，前置任务有哪些，可以和哪些任务并行解决。
   建议依赖任务 3，因为它属于同一条 authority chain 的后续冻结动作。最好不要晚于任务 5 和任务 8，因为后两者都依赖 worker-contract 结构足够稳定。可以和任务 6 并行分析。

5. 任务完成判断标准，用于判断什么时候安全结束该任务。
   满足以下条件即可结束：
   - `comparison_baseline` 的来源被固定成 round authority 或等价冻结对象
   - `run-round` 不再依赖可变 run-level scoreboard 重建这一字段
   - 兼容测试覆盖 prepare 后 baseline 改动的失败或隔离行为

### 任务5：把最近反馈摘要接入 `recent_feedback_excerpt`

1. 任务说明，说清楚要解决什么问题|增加什么功能。
   当前 worker-facing envelope 里已有 `recent_feedback_excerpt` 字段，但固定为空数组。该任务要把最近一条或最近几条 distilled feedback 摘要稳定写进 worker-contract，让 agent 在下一轮能消费最小 feedback 上下文。

2. 任务边界，说清楚预期修改、增加的代码|文档。
   主要修改：
   - `toolchain/scripts/research/autoresearch_worker_contract.py`
   - `toolchain/scripts/research/autoresearch_feedback_distill.py`
   - `toolchain/scripts/research/run_autoresearch.py`
   - `toolchain/scripts/research/test_autoresearch_worker_contract.py`
   - `toolchain/scripts/research/test_autoresearch_feedback_distill.py`
   - `toolchain/scripts/research/test_run_autoresearch.py`
   需要同步更新：
   - worker-contract schema
   - `toolchain/scripts/research/README.md`
   - `docs/analysis/autoresearch-p1-3-feedback-distillation-and-adaptive-scheduler.md`

3. 任务的思考难度和上下文长度，需要额外说明推荐使用什么模型+推理等级解决问题。
   思考难度：中。
   上下文长度：中，主要看 worker-contract payload、ledger 读取和 schema。
   推荐模型：`gpt-5.3-codex` `medium` 或 `high`。

4. 任务依赖，主要说明为什么放在这个排序，前置任务有哪些，可以和哪些任务并行解决。
   建议依赖任务 4，并最好后于任务 6，因为 excerpt 若直接复用 richer distill 字段，会减少二次改 schema 的机会。两者都涉及 feedback distill 与 worker-contract，最好顺序落地。

5. 任务完成判断标准，用于判断什么时候安全结束该任务。
   满足以下条件即可结束：
   - 第二轮及之后的 worker-contract 会携带非空 feedback excerpt
   - excerpt 的来源、条数和裁剪规则是 deterministic 的
   - excerpt 不会改变 fixed-rule decision 的可重算性

### 任务6：实现 `dimension_feedback_summary` 与 `suggested_adjustments` 的最小可用版本

1. 任务说明，说清楚要解决什么问题|增加什么功能。
   当前 P1.3 已经有 deterministic distill 和 ledger，但 `dimension_feedback_summary` 与 `suggested_adjustments` 仍是占位。该任务要给它们落一个最小可用实现，作为下一层 mutation proposal 或 instruction seed 演进的输入。

2. 任务边界，说清楚预期修改、增加的代码|文档。
   主要修改：
   - `toolchain/scripts/research/autoresearch_feedback_distill.py`
   - `toolchain/scripts/research/test_autoresearch_feedback_distill.py`
   - 若 selector 或后续消费需要读取，可能触及：
     - `toolchain/scripts/research/autoresearch_selector.py`
     - `toolchain/scripts/research/test_autoresearch_selector.py`
   需要同步更新：
   - `toolchain/scripts/research/README.md`
   - `docs/analysis/autoresearch-p1-3-feedback-distillation-and-adaptive-scheduler.md`

3. 任务的思考难度和上下文长度，需要额外说明推荐使用什么模型+推理等级解决问题。
   思考难度：中到高。
   上下文长度：中，主要在 feedback distill 结构、已有 scoreboard 维度和 selector 消费边界。
   推荐模型：`gpt-5.4` `medium`，或 `gpt-5.3-codex` `high`。

4. 任务依赖，主要说明为什么放在这个排序，前置任务有哪些，可以和哪些任务并行解决。
   基本独立，可与任务 1、任务 2 并行。更推荐早于任务 5，这样 `recent_feedback_excerpt` 可以直接消费这里产出的稳定摘要。它和任务 7 有弱依赖关系，若任务 7 需要使用更丰富 signal，则应以后于本任务为佳。

5. 任务完成判断标准，用于判断什么时候安全结束该任务。
   满足以下条件即可结束：
   - distill payload 不再固定为空结构
   - 输出规则是 deterministic 的
   - 失败不会影响 `decision.json` 与数值 delta 的可重算性
   - 文档能说明这些字段是“建议层”而不是 authority 层

### 任务7：扩展 adaptive selector guardrail，并补一条真实 adaptive smoke 路径

1. 任务说明，说清楚要解决什么问题|增加什么功能。
   当前 adaptive selector 主要由 ledger signal 驱动，还缺更细的 guardrail；同时 repo-local 最小 runbook 还没有单独证明“依赖已有 ledger 的 adaptive selector 路径”能实跑。该任务要同时解决策略边界和验证覆盖。

2. 任务边界，说清楚预期修改、增加的代码|文档。
   主要修改：
   - `toolchain/scripts/research/autoresearch_selector.py`
   - `toolchain/scripts/research/autoresearch_feedback_distill.py`
   - `toolchain/scripts/research/test_autoresearch_selector.py`
   - 必要时补：
     - `toolchain/scripts/research/test_autoresearch_p1_3_smoke.py`
     - repo-local 最小 adaptive smoke 说明
   需要同步更新：
   - `toolchain/scripts/research/README.md`
   - `docs/operations/autoresearch-minimal-loop.md`
   - `docs/analysis/autoresearch-p1-final-code-audit-and-followups.md`

3. 任务的思考难度和上下文长度，需要额外说明推荐使用什么模型+推理等级解决问题。
   思考难度：中到高。
   上下文长度：中到长，因为既要调 selector 排序，也要考虑 runbook / smoke 验证如何最小化。
   推荐模型：`gpt-5.4` `high`。

4. 任务依赖，主要说明为什么放在这个排序，前置任务有哪些，可以和哪些任务并行解决。
   建议依赖任务 6，避免 guardrail 设计时忽略 richer distill signal。若只做最小 smoke proof，可先于任务 6 做验证覆盖，但最终策略任务仍建议后置。它可以和任务 8 并行分析。

5. 任务完成判断标准，用于判断什么时候安全结束该任务。
   满足以下条件即可结束：
   - selector guardrail 规则在代码和测试中可解释、可复现
   - 至少有一条最小 smoke 路径能证明 adaptive selector 不是只存在于单测
   - 新 guardrail 不会破坏 deterministic fallback

### 任务8：明确 legacy worker-contract 的退场条件并执行收口

1. 任务说明，说清楚要解决什么问题|增加什么功能。
   当前 legacy worker-contract v1 仍是弱校验兼容分支。该任务要决定它是长期保留的过渡兼容，还是带时限退场的迁移路径，并在文档、测试和 artifact 信号里表达清楚。

2. 任务边界，说清楚预期修改、增加的代码|文档。
   主要修改：
   - `toolchain/scripts/research/autoresearch_worker_contract.py`
   - `toolchain/scripts/research/autoresearch_round.py`
   - `toolchain/scripts/research/test_autoresearch_worker_contract.py`
   - `toolchain/scripts/research/test_autoresearch_round.py`
   需要同步更新：
   - `toolchain/scripts/research/README.md`
   - `docs/analysis/autoresearch-p1-2-worker-contract-and-minimal-selector.md`
   - `docs/analysis/autoresearch-p1-final-code-audit-and-followups.md`

3. 任务的思考难度和上下文长度，需要额外说明推荐使用什么模型+推理等级解决问题。
   思考难度：中。
   上下文长度：中，集中在 worker-contract 兼容逻辑、测试夹具和文档策略。
   推荐模型：`gpt-5.3-codex` `medium`，或 `gpt-5.4-mini` `high` 做纯文档/测试收口分析。

4. 任务依赖，主要说明为什么放在这个排序，前置任务有哪些，可以和哪些任务并行解决。
   建议放在最后，因为它依赖任务 4 完成后 current v2 路径更稳，也依赖任务 2 讲清 authority 语义。可以和任务 7 并行分析，但不建议在前面任务未稳定时过早删兼容。

5. 任务完成判断标准，用于判断什么时候安全结束该任务。
   满足以下条件即可结束：
   - legacy 路径的身份被明确写成“过渡兼容”或“长期兼容”
   - 若保留，文档和测试写清触发条件与弱校验边界
   - 若退场，代码、测试和 run artifact 不再依赖 v1 分支

## 四、推荐执行批次

建议按下面三批推进：

- 第一批：任务 1、任务 2、任务 6
  说明：先稳定 path boundary、registry authority，并把 distill 从空占位推进到最小可消费摘要。
- 第二批：任务 3、任务 4、任务 5
  说明：在 authority 语义清楚后，补 prepare crash-safe、冻结 worker-contract baseline，再把 feedback 摘要接进 worker-facing envelope。
- 第三批：任务 7、任务 8
  说明：最后补 adaptive 实跑覆盖和 legacy 收口。

## 五、任务完成后的承接要求

每个任务完成后都应检查是否需要同步更新：

- `toolchain/scripts/research/README.md`
- `docs/operations/autoresearch-minimal-loop.md`
- 对应的 `docs/analysis/autoresearch-p1-*` 阶段文档

如果某个任务把规则稳定成主线约束，再考虑升格到 `docs/knowledge/`。
