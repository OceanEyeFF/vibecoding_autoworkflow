---
title: "Autoresearch P1.Final：代码复核、当前状态与后续动作"
status: superseded
updated: 2026-04-09
owner: aw-kernel
last_verified: 2026-04-09
---
# Autoresearch P1.Final：代码复核、当前状态与后续动作

> 当前状态：本文保留为 P1.Final 审计与 follow-up 判断的历史叶子页，不是当前默认入口。
>
> 当前 `analysis/` 分流入口请先回到 [Analysis README](./README.md)；若需要当前 `autoresearch` 研究入口，先进入：
>
> - [Autoresearch：下一阶段 CLI 模块化与插拔化建议](./autoresearch-next-stage-cli-modularity-plan.md)
>
> 本文继续只保留 audit / lineage 价值。
>
> 说明：本文是对 P1.1 - P1.3 当前代码、测试和已落地 runbook 的复核结论。它属于 `analysis`，不替代 `toolchain/` 实现入口，也不替代 `docs/operations/` 的 repo-local 运行说明。

## 一、本文定位

本文合并并取代此前两份 P1.Final 分析文档：

- 风险登记
- Agent Teams 务实审计记录

本页只保留经过当前代码、测试或已落地运行说明复核后仍成立的结论，并明确区分：

- `当前仍成立的代码事实`
- `已经被后续实现或实跑覆盖的旧结论`
- `仍值得推进的后续动作`

## 二、当前已确认的事实

### 1. 包含 P1.1 - P1.3 最小边界的一轮闭环已经实际跑通过

下列说法现在已经成立，不再应继续写成“尚未验证”：

- `init -> baseline -> prepare-round -> run-round -> decide-round` 最小链路已跑通
- 单 repo、单 skill、`train / validation` 双 lane 的最小循环是可执行的
- round 最终即使被 `discard`，也不影响“闭环已成立”的判断

承接文档见：

- `docs/operations/autoresearch-minimal-loop.md`
- `toolchain/scripts/research/README.md`

### 2. `prepare-round` 当前默认走 v2 worker-contract 链路

当前实现里，`prepare-round` 会：

- 先 materialize `mutation.json`
- 再生成 `worker-contract.json`
- 把 `worker_contract_sha256` 和 `worker_contract_materialized_at` 固定进 `round.json`

`run-round` 在 `round.json` 中存在 `worker_contract_sha256` 时，会走 current v2 校验链，而不是 legacy 分支。legacy 兼容仍存在，但它不是当前正常 prepare-flow 的默认路径。

### 3. feedback-aware selector 已经是当前实现的一部分

当前 selector 输入不是 deterministic-only。代码已明确支持：

- baseline scoreboard
- optional `feedback-ledger.jsonl`
- `adaptive_priority` / `lowest_attempt_count`
- `scheduler_reason`

因此如果继续把 P1.2 理解为“selector 只有 deterministic 选择”，就会误读当前实现。

### 4. feedback ledger 缺失时是可预期降级，不是 correctness 阻塞

当前 `load_feedback_ledger()` 在文件缺失时返回空列表，selector 以此退化为 deterministic 选择。它是 observability 边界，不是“跑不起来”的阻塞点。

近期代码还补了中途日志，能直接打印当前是 deterministic 还是 adaptive 模式。

## 三、当前仍成立的风险与缺口

下面这些结论是当前代码下更准确的状态。

### 1. `target_paths` 已经收紧成严格子集语义

当前 `autoresearch_mutation_registry.py` 和 `autoresearch_round.py` 都要求 `target_paths` 必须是 `contract.mutable_paths` 的同级或更窄子路径。

这意味着：

- 更宽的父路径会被拒绝
- “`target_paths` 只能收窄，不能放大”已经不只是文档要求

### 2. registry bookkeeping 已被明确成“普通持久化状态 + 一致性校验”

`attempts`、`last_selected_round`、`last_decision`、`status` 当前仍不是 fingerprint-bound authority 字段，但也不再是“schema-valid 就默认可信”。

当前脚本会额外校验：

- `last_selected_round` 不能脱离 `attempts`
- `last_decision` 不能脱离 `last_selected_round`
- `status = exhausted` 不能早于 attempts 达到上限
- active round 存在时，registry entry 还必须与 frozen round authority 对账

因此这组字段现在更准确地属于“可持久化 bookkeeping 状态”，而不是“可随意手改的隐式输入”。

### 3. `prepare-round` 的 authority 写盘顺序已经收紧，并有恢复路径

当前 `prepare-round` 的关键顺序已经变成：

1. 写 `mutation.json`
2. 冻结 round authority（含 registry entry、materialized mutation、frozen baseline、feedback excerpt）
3. 生成 `worker-contract.json`
4. 回写 registry bookkeeping

如果发现中断残留的 active round，再次执行 `prepare-round` 时会先按 frozen authority 修复 `mutation.json` / `worker-contract.json`，并对账 registry bookkeeping，再拒绝直接开启新 round；如果 `mutation-registry.json` 已缺失，则当前实现会 fail closed，而不是有损重建 candidate pool。

### 4. worker contract 的 `comparison_baseline` 已冻结到 round authority

v2 路径下，`run-round` 不再从可变 run-level scoreboard 重建 `comparison_baseline`。

现在的行为是：

- `prepare-round` 冻结 `comparison_baseline`
- `worker-contract.json` 直接消费冻结对象
- `run-round` 校验时也复用同一份 frozen baseline

所以 prepare 之后外部 scoreboard 漂移不会再让 v2 worker contract 发生 envelope drift。

### 5. `recent_feedback_excerpt`、`dimension_feedback_summary` 和 `suggested_adjustments` 已有最小实现

当前 distill payload 不再固定为：

- `dimension_feedback_summary: {}`
- `suggested_adjustments: []`

同时 worker-facing envelope 也不再固定写 `recent_feedback_excerpt: []`。这些字段现在都由 deterministic rules 生成，但仍属于建议层，不影响 fixed-rule `decision.json` 的可重算性。

### 6. adaptive selector 仍主要由 feedback ledger 驱动，但 guardrail 和 smoke 都已补上

当前 adaptive 排序的主导输入仍然是 feedback ledger 中的 family signal，这一点没有变化。

但当前实现已经额外具备：

- 针对 `validation_drop` / parse-error / timeout 回退信号的 guardrail
- repo-local smoke 对 adaptive 路径的最小证明

因此它不再只是“代码和单测里存在”的分支。

### 7. legacy worker-contract 兼容路径仍保留，但身份已经更明确

legacy v1 路径仍然存在，且仍是弱校验兼容分支；这点没有变。

当前更准确的表述应是：

- 它属于 `transition_compat_weak_checks`
- 只在 `worker_contract_sha256` 缺失时进入
- 当前正常 prepare-flow 默认仍是 v2 hash-bound envelope

## 四、已经过期或需要修正的旧结论

下面这些说法不应再以当前结论的口吻保留。

### 1. “P1.1 - P1.3 从未端到端跑过”

这条已经被实际运行和 `docs/operations/autoresearch-minimal-loop.md` 覆盖，不再成立。

### 2. “Legacy worker-contract 是烟测前唯一必须先修的问题”

这条不成立。legacy 分支是完整性退化风险，不是当前最小闭环的前置阻塞。当前最小闭环正常走的是 v2 路径。

### 3. “feedback ledger 静默降级会阻塞第一轮运行”

这条不成立。更准确的说法是：它会让第一轮退化为 deterministic selector，并降低可观测性，但不会阻塞闭环。

### 4. “第一次烟测前必须先修 target_paths overlap / suggested_adjustments 空占位”

这类表述现在都太强。它们仍是值得修的边界缺口，但不再是“最小闭环不能运行”的前提条件。

### 5. “Suite 文件路径解析本身是当前核心阻塞”

这条需要降级处理。当前更准确的经验结论是：

- candidate worktree 内执行 suite 时，manifest 里的 `repo` 用绝对路径更稳
- 这已经被 repo-local runbook 吸收为运行约束

它是已知运行坑点，不是未识别的理论风险。

## 五、建议保留的后续动作

### P1.Final 优先

1. 继续评估 bookkeeping 是否还需要更强的 tamper-proof 机制；当前只做到一致性校验，不是签名式 authority。
2. 把 legacy worker-contract 的最终退场时间点和删除条件写得更硬，而不只是标成 `transition_compat_weak_checks`。

### P1.3+ 优先

1. 如果后续要继续演进 adaptive scheduler，优先在当前 deterministic 摘要层之上加更细的退避策略，而不是直接引入模型自由排序。
2. 若要继续增强 feedback，需要保持 `dimension_feedback_summary` / `suggested_adjustments` 只停留在建议层，不反向改写 fixed-rule decision。

### 文档与承接层

1. `analysis` 只保留复核结论和残留风险，不继续承接执行入口。
2. 已经稳定的运行说明继续放在 `docs/operations/`。
3. `toolchain/scripts/research/README.md` 继续作为当前脚本行为的第一承接位。

## 六、与当前文档体系的关系

如果后续接受本文中的任何稳定结论，应优先回写到：

- `toolchain/scripts/research/README.md`
- `docs/operations/autoresearch-minimal-loop.md`
- 必要时再升格到 `docs/knowledge/`

本文只保留“当前代码复核后仍成立的分析结论”，不作为执行真相入口。
