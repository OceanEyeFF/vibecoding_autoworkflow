---
title: "Autoresearch P1.3：Feedback Distillation 与 Adaptive Scheduler"
status: active
updated: 2026-03-27
owner: aw-kernel
last_verified: 2026-03-27
---
# Autoresearch P1.3：Feedback Distillation 与 Adaptive Scheduler

> 目的：在 system 已经能自动跑多轮的前提下，把原始 round 结果压缩成可复用的 family 级反馈，再在此基础上引入真正有依据的 adaptive scheduling。P1.3 不是新的评测系统，而是现有 runner 结果上的反馈压缩层。

## 一、阶段定位

P1.3 只回答下面问题：

- 原始 round 结果应如何被压缩成可调度的反馈对象
- distillation 产物应如何和 `mutation_key` 绑定
- adaptive scheduler 至少应消费哪些 distilled signals
- 为什么这一层必须晚于 registry、worker contract 和 minimal selector

P1.3 不回答下面问题：

- 是否引入新的 judge backend
- 是否重写 run-summary schema
- 是否把 autoresearch 扩成长期数据库
- 是否让模型自由修改 keep / discard 规则

## 二、为什么它是后置层

这一层之所以不能提前，不是因为它不重要，而是因为它没有独立上游。

它依赖的前提已经很明确：

- P1.1 提供稳定的 `mutation_key`
- P1.2 提供稳定的 `worker-contract.json`
- minimal selector 让系统能自动连续跑几轮
- P0 runner 已经稳定产出 `run-summary.json`、`structured_output`、`dimension_feedback`

只有这些都成立，feedback distillation 才有意义。否则：

- 没有 `mutation_key`，反馈无法回到 family 级
- 没有自动多轮，反馈只是一次性实验日志
- 没有 worker contract，反馈无法知道 agent 当时具体接到了什么合同

因此依赖顺序必须固定为：

```text
mutation registry
  -> worker contract
  -> minimal selector
  -> feedback distillation
  -> adaptive scheduler
```

## 三、这一层不是新的评测系统

P1.3 必须明确建立在现有 runner 产物之上。

可直接复用的信号已经存在：

- lane 级 `avg_total_score`
- `parse_error_rate`
- `timeout_rate`
- task 级 `structured_output`
- `dimension_feedback`
- round 级 `decision.json`

所以 P1.3 不应该先做：

- 新的 benchmark 平台
- 新的 scoring DSL
- 新的 result database

它的工作只有一个：

- 把已有原始结果压缩成后续 selector / scheduler 能稳定消费的反馈对象

## 四、Feedback Distillation 的角色

### 1. 它解决什么问题

原始 round 结果太散，直接拿去驱动调度会出现两个问题：

- 数值信号和文本反馈分散在多个 artifact 里
- selector 很容易直接吃原始 transcript 噪声

feedback distillation 的职责就是把一轮结果压成 family 级最小反馈单元。

### 2. 它的输入

建议固定为下面几类：

- `mutation-registry.json`
- round `mutation.json`
- round `worker-contract.json`
- round `scoreboard.json`
- round `decision.json`
- `train/` 与 `validation/` 下各自的 `run-summary.json`

### 3. 它的输出

建议固定两层产物：

- per-round：
  - `.autoworkflow/autoresearch/<run-id>/rounds/round-NNN/feedback-distill.json`
- run-level ledger：
  - `.autoworkflow/autoresearch/<run-id>/feedback-ledger.jsonl`

其中：

- `feedback-distill.json` 负责描述“这一轮的 distilled 结果”
- `feedback-ledger.jsonl` 负责把多轮 feedback 累积成可搜索、可排序、可筛选的 family 级历史

## 五、Distilled Feedback 的对象模型

### 1. 最小字段

建议最小字段包括：

- 身份
  - `run_id`
  - `round`
  - `mutation_key`
  - `mutation_id`
  - `attempt`
- 结果
  - `decision`
  - `train_score_delta`
  - `validation_score_delta`
  - `parse_error_delta`
  - `timeout_rate_delta`
- family 级信号
  - `signal_strength`
  - `regression_flags`
  - `dimension_feedback_summary`
  - `suggested_adjustments`
- 溯源
  - `scoreboard_ref`
  - `decision_ref`
  - `worker_contract_ref`
  - `distilled_at`

推荐最小形状：

```json
{
  "run_id": "memory-side-kb-research",
  "round": 3,
  "mutation_key": "text_rephrase:knowledge-base-skill:intro-tighten-v1",
  "mutation_id": "r003:text_rephrase:knowledge-base-skill:intro-tighten-v1",
  "attempt": 1,
  "decision": "discard",
  "train_score_delta": 0.012,
  "validation_score_delta": -0.018,
  "parse_error_delta": 0.0,
  "timeout_rate_delta": 0.0,
  "signal_strength": "mixed",
  "regression_flags": [
    "validation_drop"
  ],
  "dimension_feedback_summary": {
    "clarity": "improved",
    "boundary_respect": "stable",
    "task_completion": "weaker"
  },
  "suggested_adjustments": [
    "keep boundary wording but undo over-tight compression in the opening section"
  ],
  "scoreboard_ref": "rounds/round-003/scoreboard.json",
  "decision_ref": "rounds/round-003/decision.json",
  "worker_contract_ref": "rounds/round-003/worker-contract.json",
  "distilled_at": "2026-03-27T00:00:00Z"
}
```

### 2. 哪些部分应由脚本直接产生

必须由脚本直接产生的字段：

- `decision`
- 各类 score delta
- `regression_flags`
- artifact refs
- `round` / `mutation_key` / `attempt`

这些字段都是确定性、可重算的。

### 3. 哪些部分可以允许模型辅助压缩

可以允许模型辅助，但不能越权的字段：

- `dimension_feedback_summary`
- `suggested_adjustments`

前提必须是：

- 它们只是在已有 `structured_output`、`dimension_feedback` 上做压缩
- 它们没有权力改写 `decision`
- 它们没有权力创建新 mutation 并直接入 registry

## 六、为什么 distilled feedback 要绑定到 family，而不是 round

如果只把反馈停留在 round 层，后续调度没有稳定对象可学习。

绑定到 `mutation_key` 的作用是：

- 区分“这类 mutation 总体上有效吗”
- 区分“是第一次尝试失败，还是这个 family 本身就弱”
- 为后续 adaptive scheduler 提供 family 级累积历史

所以这层的核心不是“多写一份总结”，而是：

- 把 round 结果提升成 family 级反馈资产

## 七、Adaptive Scheduler 的角色

### 1. 它应该消费什么

adaptive scheduler 只应消费已经 distilled 的结构化反馈，而不是原始 transcript。

最小输入应是：

- `mutation-registry.json`
- `feedback-ledger.jsonl`
- 当前 champion scoreboard 摘要

### 2. 它应该输出什么

最小输出仍然只应是：

- `mutation_key`
- `scheduler_reason`
- 可选的 `spawn_proposal`

这里的 `spawn_proposal` 也不应直接入池，而应先作为 proposal，再由脚本 canonicalize 成 registry entry。

### 3. 它最小能做什么

P1.3 的第一版 adaptive scheduler 只需要做到：

- 提高近期有正信号 family 的优先级
- 降低持续退化 family 的优先级
- 对 mixed signal family 允许有限重试
- 根据 distilled `suggested_adjustments` 生成新的 proposal，但不直接落真相

这已经足够称为 adaptive。没必要一开始就做复杂搜索器。

## 八、为什么它必须晚于 minimal selector

如果连 minimal selector 都没有，adaptive scheduler 就没有干净的比较基线。

没有 minimal selector 时：

- 轮次可能是人工挑选的
- selection bias 无法区分
- feedback 的分布会混入人工偏好

只有先让系统按固定规则自动跑几轮，后面的 adaptive scheduling 才有可比性。

因此 P1.3 的正确节奏不是：

- 一上来就用 feedback 做“智能调度”

而是：

- 先有 deterministic baseline
- 再在其上叠加 distilled feedback

当前代码已经把这条路径落成了第一版：distillation 是脚本确定性的，scheduler 只是 feedback-aware 的 priority 层，不是 LLM 驱动的策略学习器。

## 九、已落地实现

### 1. 代码落点

- `toolchain/scripts/research/autoresearch_feedback_distill.py`
  - 生成和校验 `feedback-distill.json`
  - 读取和写回 `feedback-ledger.jsonl`
  - 计算 family signal priority
- `toolchain/evals/fixtures/schemas/autoresearch-feedback-distill.schema.json`
  - 约束 P1.3 distilled feedback 的字段形状
- `toolchain/scripts/research/autoresearch_round.py`
  - 在 `decide-round` 阶段计算 delta、flags、signal
  - 写出 round 级 `feedback-distill.json`
  - 追加或覆盖 run 级 `feedback-ledger.jsonl`
- `toolchain/scripts/research/run_autoresearch.py`
  - `prepare-round` 自动选择时加载 ledger
  - `decide-round` 之后输出 distill/ledger 产物
- `toolchain/scripts/research/autoresearch_selector.py`
  - 接收可选 `feedback_ledger`
  - 输出 `selection_reason` 和 `scheduler_reason`

### 2. 产物形状

- `feedback-distill.json`
  - `feedback_distill_version`
  - `run_id`
  - `round`
  - `mutation_key`
  - `mutation_id`
  - `attempt`
  - `decision`
  - `train_score_delta`
  - `validation_score_delta`
  - `parse_error_delta`
  - `timeout_rate_delta`
  - `signal_strength`
  - `regression_flags`
  - `dimension_feedback_summary`
  - `suggested_adjustments`
  - `scoreboard_ref`
  - `decision_ref`
  - `worker_contract_ref`
  - `distilled_at`
- `feedback-ledger.jsonl`
  - 每行一个 distilled feedback JSON object
  - 按 `(run_id, round, mutation_id)` 做 upsert，而不是无脑追加

### 3. 当前排序语义

- 没有 ledger 时，selector 仍然回退到 P1.2 的 deterministic 行为
- 有 ledger 时，selector 按 family signal priority 排序
- fingerprint 冲突的 pending round 仍然优先于 family signal 排序被跳过
- 当前 priority 顺序是：
  - `recent_positive_signal`
  - `no_feedback_history`
  - `guided_mixed_retry`
  - `mixed_signal_retry`
  - `guardrail_capped_mixed_retry`
  - `latest_negative_signal`
  - `guardrail_blocked_retry`
  - `sustained_regression_deprioritized`
- `comparison_baseline` 仍保留在 selector 入参里，用于接口兼容，但当前排序没有用它做权重

### 4. 当前实现的边界

- `dimension_feedback_summary` 现在会按 score delta / regression flags 生成 deterministic 的最小摘要
- `suggested_adjustments` 现在会按 fixed rules 生成有限建议，但仍不具备改写 `decision` 或直接写 registry 的权力
- `recent_feedback_excerpt` 会把最近几条 distilled feedback 压成短字符串，供下一轮 worker contract 只读消费
- `spawn_proposal` 仍未进入实现链
- scheduler 只改变候选顺序，不改写 registry truth
- `decision.json` 仍然完全由固定 keep / discard 规则决定

## 十、控制边界

### 1. 必须由脚本控制

- score delta 计算
- regression flag 计算
- ledger 追加与索引
- family signal priority 的排序规则
- `decision.json` 的 keep / discard 裁决

### 2. 可由 Codex / subagent 辅助

- 当前还没有接入模型辅助压缩；这些字段仍是后续能力
- 如果后续加入模型压缩，只能压缩 `dimension_feedback_summary` 与 `suggested_adjustments`
- 当前最小 smoke 已经覆盖 adaptive 路径，但只覆盖 deterministic distill + guardrail，不覆盖模型辅助压缩

### 3. 不能交给 Codex 主控

- 自己改写 `decision`
- 自己把 proposal 写进 registry 成为 active entry
- 自己提高某 family 的优先级分数
- 自己跳过脚本的 exhaustion / veto 规则

## 十一、当前状态

### 1. 已完成

- deterministic feedback distillation
- `feedback-distill.json` 与 `feedback-ledger.jsonl` 的落盘和 upsert
- feedback-aware selector priority

### 2. 仍待后续验证或实现

P1.3 里先不要碰：

- 新的 eval backend
- 新的 run-summary contract
- LLM 自由生成并直接执行 mutation
- 多 candidate 并发 bandit
- acceptance 全量纳入每轮自适应
- `dimension_feedback_summary` 与 `suggested_adjustments` 的模型辅助压缩
- `spawn_proposal` 的生成与 canonicalize
- 任何会让 scheduler 变成独立 orchestrator 的机制

这些都不是当前主链上的第一批硬前置。

## 十二、结论

P1.3 当前已经落成的是一层 deterministic feedback distillation，再加一层基于 family signal 的 feedback-aware priority selector。

它还不是：

- 直接在噪声 transcript 上做选择
- 也不是模型辅助的摘要压缩器
- 也不是带 `spawn_proposal` 的调度编排层

而是：

- 在已经稳定归档的 mutation family 历史上做有依据、可回放的排序与记录

相关文档：

- [Autoresearch P1.1：Mutation Registry](./autoresearch-p1-1-mutation-registry.md)
- [Autoresearch P1.2：Worker Contract 与 Minimal Selector](./autoresearch-p1-2-worker-contract-and-minimal-selector.md)
- [Research 评测观测与输出规范](./research-eval-observability.md)
