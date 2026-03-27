---
title: "Autoresearch P1.2：Worker Contract 与 Minimal Selector"
status: active
updated: 2026-03-27
owner: aw-kernel
last_verified: 2026-03-27
---
# Autoresearch P1.2：Worker Contract 与 Minimal Selector

> 目的：在 `mutation registry` 已稳定的前提下，把“agent 到底拿什么做一轮内容工作”与“脚本如何最小化地选出下一项”分开固定。P1.2 不是智能调度，而是先把执行合同与最小选择器钉死。

## 一、阶段定位

P1.2 只回答下面问题：

- round 内给 Codex / subagent 的执行合同长什么样
- `worker contract` 应该引用哪些上游对象
- minimal selector 至少需要哪些输入与输出
- 为什么 selector 只做 deterministic 版本就够

P1.2 不回答下面问题：

- 如何从多轮反馈自动生成全新 mutation kind
- 如何做 bandit、贝叶斯优化或策略学习
- 是否支持多 candidate 并发探索
- 是否引入 planner / critic / judge 多角色 round

## 二、为什么它紧跟在 registry 之后

P1.1 固定了 mutation family。P1.2 要解决的是另一个缺口：

- registry 解决“系统可试哪些 mutation”
- worker contract 解决“agent 这轮具体该做什么”
- selector 解决“脚本下一轮先拿哪个 mutation”

如果跳过 worker contract，直接让 Codex 读 registry，会出现两个问题：

- agent 被迫理解 registry 状态机与 runtime 细节
- registry 对象会被错误地当成 agent prompt 包装层

如果跳过 selector，继续手填 `mutation_key`，系统仍然停留在“人工启动自动 round”，没有进入真正的可持续循环。

因此 P1.2 的内部顺序应固定为：

```text
mutation-registry.json
  -> round mutation.json
  -> worker-contract.json
  -> minimal selector
```

这里说的是阶段落地顺序，不是单轮运行时序。单轮运行时当然是“先选，再实例化，再执行”。

## 三、Worker Contract 的角色

### 1. 它不是什么

`worker-contract.json` 不应被写成：

- 新的 truth layer
- registry 的替代品
- 自带选择权的任务计划器
- 可以扩 scope 的动态 prompt 容器

### 2. 它是什么

`worker-contract.json` 应该只是 agent-facing 执行信封。

它的职责只有三件事：

- 把本轮已选中的 mutation family materialize 成可执行指令
- 把 candidate worktree、输出路径和 guardrails 显式交给 agent
- 把需要的只读上下文整理成一次 round 足够消费的最小包

落点建议固定为：

- `.autoworkflow/autoresearch/<run-id>/rounds/round-NNN/worker-contract.json`

建议补一份 schema：

- `toolchain/evals/fixtures/schemas/autoresearch-worker-contract.schema.json`

建议补一份生成器：

- `toolchain/scripts/research/autoresearch_worker_contract.py`

## 四、Worker Contract 的对象模型

### 1. 上游依赖

`worker-contract.json` 必须只依赖下面几类上游对象：

- `contract.json`
- run-local `mutation-registry.json` 的 canonical family 定义
- round `mutation.json`
- round `round.json`
- 当前比较基线 `scoreboard.json`

它不应直接依赖：

- 原始 `run-summary.json` 全量 transcript
- agent 历史对话
- 自由输入的临时 prompt 碎片

实现上应保持一条更窄的 authority 链：

```text
contract.json
  -> mutation-registry.json
  -> round mutation.json
  -> round.json
  -> worker-contract.json
```

说明：

- `worker-contract.json` 自身不是 authority，只是 agent-facing envelope
- `runtime.json` / `worktree.json` 可以继续服务外环生命周期，但不应反向进入 worker contract 的字段真相
- 当前代码里 `build_worker_contract_payload()` 直接消费的是 `contract.json + round mutation.json + round.json + frozen comparison_baseline + frozen recent_feedback_excerpt`；registry / runtime / worktree 约束则通过 `prepare-round` 的 materialization、round authority snapshot 和 `run-round` 校验链维持

### 2. 最小字段

建议最小字段收敛为下面几组：

- 身份
  - `run_id`
  - `round`
  - `mutation_key`
  - `mutation_id`
  - `attempt`
- 执行面
  - `candidate_worktree`
  - `base_sha`
  - `candidate_branch`
  - `agent_report_path`
- 变更边界
  - `target_paths`
  - `allowed_actions`
  - `guardrails`
- 任务语义
  - `instruction`
  - `expected_effect`
- 只读上下文
  - `objective`
  - `target_surface`
  - `comparison_baseline`
  - `recent_feedback_excerpt`
- 校验锚点
  - `contract_fingerprint`
  - `mutation_fingerprint`
  - `materialized_at`

推荐最小形状：

```json
{
  "run_id": "memory-side-kb-research",
  "round": 3,
  "mutation_key": "text_rephrase:knowledge-base-skill:intro-tighten-v1",
  "mutation_id": "r003:text_rephrase:knowledge-base-skill:intro-tighten-v1",
  "attempt": 1,
  "candidate_worktree": "/abs/path/to/candidate",
  "base_sha": "abc123",
  "candidate_branch": "candidate/memory-side-kb-research/r003",
  "agent_report_path": "/abs/path/to/agent-report.md",
  "target_paths": [
    "product/memory-side/adapters/agents/skills/knowledge-base-skill/SKILL.md"
  ],
  "allowed_actions": [
    "edit"
  ],
  "guardrails": {
    "require_non_empty_diff": true,
    "max_files_touched": 1,
    "extra_frozen_paths": []
  },
  "instruction": "Tighten the opening guidance, reduce repetition, keep path and boundary rules explicit.",
  "expected_effect": {
    "hypothesis": "Reduce verbosity while preserving routing accuracy and boundary clarity.",
    "primary_metrics": [
      "avg_total_score"
    ],
    "guard_metrics": [
      "parse_error_rate",
      "timeout_rate"
    ]
  },
  "objective": "Improve memory-side skill output quality under the current contract.",
  "target_surface": "memory-side skill text",
  "comparison_baseline": {
    "train_score": 0.78,
    "validation_score": 0.75
  },
  "recent_feedback_excerpt": [
    "round=2 | mutation=text_rephrase:demo:intro-tighten-v1 | decision=discard | signal=mixed | flags=validation_drop"
  ],
  "contract_fingerprint": "sha256:...",
  "mutation_fingerprint": "sha256:...",
  "materialized_at": "2026-03-27T00:00:00Z"
}
```

## 五、哪些字段属于 worker contract，哪些不属于

### 1. 应该放进 worker contract 的内容

- 本轮唯一的 mutation 身份
- 本轮 candidate worktree 信息
- agent 必须遵守的 scope 与 actions
- 足够完成这一轮的最小 instruction
- 只读的 baseline / feedback 摘要
- 本轮必须写出的 artifact 路径

### 2. 不应放进 worker contract 的内容

- registry 全量 entries
- selector 排序理由的长日志
- round 之后的 keep / discard 策略
- worktree cleanup 指令
- agent 可自行改写的 `target_paths`

判断标准应很简单：

- 凡是“agent 执行本轮内容工作必须知道的”，可以放
- 凡是“脚本主控外环必须独占的”，不能放

## 六、脚本与 Codex 的边界

### 1. 必须由脚本控制

- 选择 `mutation_key`
- materialize `worker-contract.json`
- 把 `instruction_seed` 转成本轮 `instruction`
- 回填 `attempt`、`mutation_id`、`base_sha`
- 在 `run-round` 前后做 scope 与 diff 校验

### 2. 由 Codex / subagent 消费即可

- `worker-contract.json` 的全部内容
- candidate worktree
- 只读反馈摘录

Codex / subagent 的职责仍然只应是：

- 在指定路径内改内容
- 写 `agent-report.md`
- 不越过 `allowed_actions`

### 3. 明确不能交给 Codex 主控

- 重选 mutation
- 调整 `attempt`
- 调整 `max_files_touched`
- 重写 `comparison_baseline`
- 扩大 `target_paths`

## 七、为什么 worker contract 先于 selector 成型

从实现顺序看，worker contract 应先于 selector 落地，原因不是运行时先后，而是接口稳定性。

原因如下：

- selector 输出的最终目标不是 prompt，而是“选中哪个 `mutation_key`”
- 只有 worker contract 形状稳定后，selector 才知道自己的输出需要喂给什么执行对象
- 否则 selector 很容易反向长成“顺便帮 agent 拼 prompt 的半执行器”

所以 P1.2 里应先冻结：

- `worker-contract.json` 的字段
- `prepare-round` 的 materialization 过程

再补 selector。

## 八、Minimal Selector 的角色

### 1. 它的目标

minimal selector 只解决一个问题：

- 在当前 run 的 active mutation entries 里，脚本下一轮选谁

它不解决：

- feedback 语义压缩
- 探索 / 利用权衡学习
- 自动生成全新 mutation

### 2. 最小输入

minimal selector 的输入应收敛为：

- `mutation-registry.json`
- `runtime.json`
- 当前 champion scoreboard 摘要

其中真正必须的最小字段只有：

- `mutation_key`
- `status`
- `attempts`
- `last_selected_round`
- `last_decision`
- `fingerprint`

### 3. 最小输出

selector 不应直接输出 prompt，而应输出一个稳定选择结果对象：

- `mutation_key`
- `attempt`
- `selection_reason`
- `selection_index`

当前进程内对象还会携带：

- `entry`

`selection_reason` 只需要是固定枚举或短字符串。当前最小实现收敛为：

- `lowest_attempt_count`
- `skip_duplicate_fingerprint`

### 4. 第一版选择规则

第一版可以明确收敛为：

1. 只在 `status=active` 的 entries 中选择
2. 跳过已到 `max_attempts` 的 entry
3. 跳过 fingerprint 与当前 pending round 冲突的 entry
4. 优先 `attempts` 更少的 entry
5. 再按 registry 原始顺序和 `mutation_key` 做 deterministic tie-break

`comparison_baseline` 在 P1.2 里可以进入 selector 输入边界，但第一版只要求它被显式传入，不要求它参与 adaptive 排序。

当前实现还进一步固定了两点：

- `comparison_baseline` 在 `prepare-round` 时会被冻结进 round authority，而不是在 `run-round` 时再从可变 run-level scoreboard 重建
- `recent_feedback_excerpt` 会在 `prepare-round` 时按 deterministic 规则从 ledger 裁剪，再冻结进 round authority，避免 prepare 之后的 ledger 漂移影响 envelope 校验

legacy worker-contract v1 仍保留，但应被明确看作：

- `transition_compat_weak_checks`
- 仅在 `worker_contract_sha256` 缺失时进入
- 只保留 required-fields / tracing 一致性弱校验，不承担当前主路径的 hash-bound envelope 强度

这已经足够支撑：

- 自动多轮推进
- retry 记账
- exhausted 停用

不需要在这一层就引入“智能”。

## 九、为什么它现在不该扩成 scheduler

P1.2 仍然不应把 selector 扩成 scheduler，原因很直接：

- 没有 distilled feedback，智能打分会直接绑到原始 transcript 噪声
- 没有 family 级历史压缩，所谓自适应只是在临时 round 结果上抖动
- 没有稳定 worker contract，selector 很容易被 prompt 拼接逻辑污染

因此 P1.2 最准确的表述应是：

- 有一个 deterministic selector
- 没有一个“理解一切”的 scheduler

## 十、最小落地路径

### 1. 子阶段 A：冻结 worker contract 文档

只写 `docs/analysis/`：

- 固定 `worker-contract.json` 的字段
- 固定脚本与 Codex 的 authority 边界

验收信号：

- agent 在单轮里需要读取什么，不再含糊
- `worker-contract.json` 不再和 registry 混层

### 2. 子阶段 B：worker contract schema + generator 已落地

进入 `toolchain/`：

- `toolchain/evals/fixtures/schemas/autoresearch-worker-contract.schema.json`
- `toolchain/scripts/research/autoresearch_worker_contract.py`
- `prepare-round` 结束时写出 `worker-contract.json`

验收信号：

- agent 可以只消费 worker contract 完成本轮
- `prepare-round` 会把 `worker-contract.json` 的 hash 与 `materialized_at` 固定进 `round.json`
- `run-round` 会先校验 worker contract hash，再重建 payload 校验 tracing 字段与 authority 状态仍然一致

### 3. 子阶段 C：minimal selector 已落地

进入 `toolchain/scripts/research/`：

- `autoresearch_selector.py`
- `prepare-round` 支持在未显式指定 `mutation_key` 时自动选择下一项

验收信号：

- 不手写 round `mutation.json` 也能持续推进
- 同一 exhausted entry 不会被反复选中
- 同 fingerprint 的 pending round 不会被重复选中
- selector 输出仍然只是稳定选择结果对象，没有长成调度平台

## 十一、当前阶段先不要碰

在 P1.2 内，先不要碰：

- 多 candidate 并发
- acceptance lane 抽样调度
- model-based selector
- feedback 驱动的新 mutation spawn
- 让 agent 直接修改 registry

这些都属于下一层。

## 十二、结论

P1.2 的真正工作不是“让模型更自由”，而是把 agent 的执行入口压成一个稳定信封，并给脚本补一个足够小的选择器。

只有这样，系统才会从：

- “人工指定本轮 mutation，再让 agent 去做”

进入：

- “脚本能自己选出下一项，再把本轮工作安全地下发给 agent”

相关文档：

- [Autoresearch P1.1：Mutation Registry](./autoresearch-p1-1-mutation-registry.md)
- [Autoresearch P0.3：Baseline Loop 与 Round 执行](./autoresearch-p0-3-baseline-loop-and-round-execution.md)
- [Research 评测观测与输出规范](./research-eval-observability.md)
