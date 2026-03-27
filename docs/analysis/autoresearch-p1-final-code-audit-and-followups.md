---
title: "Autoresearch P1.Final：代码复核、当前状态与后续动作"
status: active
updated: 2026-03-28
owner: aw-kernel
last_verified: 2026-03-28
---
# Autoresearch P1.Final：代码复核、当前状态与后续动作

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

下面这些结论在当前代码下仍成立。

### 1. `target_paths` 仍是 overlap 语义，不是严格子集语义

这是当前最明确的边界缺口之一。

- `autoresearch_mutation_registry.py` 和 `autoresearch_round.py` 都仍按 `paths_overlap(...)` 判断 `target_paths` 是否位于 `contract.mutable_paths` 内
- 这意味着更宽的父路径有机会被视为合法，而不是真正的“只允许收窄”

所以“`target_paths ⊆ mutable_paths` 只是文档要求、还没被严格编码”为真。

### 2. registry bookkeeping 仍然信任磁盘上的 schema-valid 值

`attempts`、`last_selected_round`、`last_decision`、`status` 这些 bookkeeping 字段目前仍属于“可持久化状态”，不是防篡改 authority 字段。

当前脚本会在运行期校验：

- `run_id`
- `contract_fingerprint`
- schema 和字段类型

但不会额外给 bookkeeping 字段加 tamper-proof 机制。因此“手工改写后仍可被继续消费”这条风险仍成立，只是它更偏完整性风险，而不是首次闭环阻塞。

### 3. round authority 与 registry 写回之间仍有 crash 窗口

`prepare-round` 当前顺序是：

1. 写 `mutation.json`
2. 写 `worker-contract.json`
3. 回写 registry 的 `attempts / last_selected_round`
4. 写 round authority 快照

因此在第 3 步成功、第 4 步失败之间，仍存在 registry 已推进但 authority 未冻结的窗口。这个结论比旧文档里“`stage_worker_contract()` 失败前就会写脏 registry”更准确。

### 4. worker contract 的 comparison baseline 仍来自 run-level scoreboard 重建

v2 路径下，`run-round` 会重新读取 run-level baseline scoreboard，并重建一份期望的 worker contract payload 来对比现存文件。

这意味着：

- comparison baseline 不是单独冻结在 round authority 里的独立对象
- 如果将来出现 `prepare-round` 之后、`run-round` 之前 baseline scoreboard 被外部改动的场景，worker-contract 可能因对不上而失败

这条仍然是代码层面的真实耦合点。

### 5. `recent_feedback_excerpt` 仍是空数组占位

P1.3 已经有 `feedback-distill.json` 和 `feedback-ledger.jsonl`，但 worker-facing envelope 里的 `recent_feedback_excerpt` 仍固定写 `[]`。

所以现在是：

- feedback 已存在于 run-level 历史
- 但没有真正压平进 agent-facing worker contract

### 6. `dimension_feedback_summary` / `suggested_adjustments` 仍是占位结构

当前 distill payload 仍固定写：

- `dimension_feedback_summary: {}`
- `suggested_adjustments: []`

因此 P1.3 当前完成的是：

- deterministic distillation
- ledger upsert
- feedback-aware family priority

但还没有进入“根据 distilled 建议生成新 proposal / 新 instruction seed”的下一层闭环。

### 7. adaptive selector 仍主要由 feedback ledger 信号驱动

当前 adaptive 排序的核心输入仍是 feedback ledger 中的 family signal。文档里如果把“champion scoreboard 摘要”写成 scheduler 的实际排序输入，会高于代码事实。

更准确的说法应是：

- baseline scoreboard 会参与 selector 的接口和上下文
- 但 family 排序的当前主导信号仍来自 ledger，而不是独立的 champion scoreboard 摘要

### 8. legacy worker-contract 兼容路径仍然是弱校验分支

legacy v1 路径仍保留 required-fields / 类型校验，以及少量 tracing 一致性校验，但不具备 v2 的 hash-bound envelope 约束强度。它不是当前主路径阻塞，但仍是一个应明确退场条件的兼容分支。

### 9. adaptive selector 已被代码和单测覆盖，但尚未被当前最小 runbook 单独证明

当前最小闭环 runbook 走的是 `prepare-round --mutation <manual-mutation.json>` 路径，已经证明：

- P1.1 registry import/materialization 可工作
- P1.2 worker contract 可工作
- P1.3 distill / ledger 落盘可工作

但它并不单独证明“依赖已有 ledger 的 adaptive selector 排序路径”已经被 repo-local 最小实跑覆盖。更准确的状态应是：

- adaptive selector 已被代码与单测覆盖
- 当前最小 runbook 还没有单独把这一路径做成实跑证明

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

1. 把 `target_paths` 校验从 overlap 收紧成真正的子集语义。
2. 明确 registry bookkeeping 是“普通持久化状态”还是“需要防篡改的 authority 字段”，并补相应测试。
3. 收紧 `prepare-round` 的写盘顺序或补恢复策略，缩小 registry/authority crash 窗口。
4. 明确 legacy worker-contract 的退场条件，避免长期保留弱校验分支。

### P1.3+ 优先

1. 把最近一条或几条 distilled feedback 摘要写进 `recent_feedback_excerpt`。
2. 给 `dimension_feedback_summary` 与 `suggested_adjustments` 落一个最小可用实现，但不要让它影响 fixed-rule decision 的可重算性。
3. 为 adaptive selector 增加更明确的 guardrail，例如负信号连续次数上限或退避策略。

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
