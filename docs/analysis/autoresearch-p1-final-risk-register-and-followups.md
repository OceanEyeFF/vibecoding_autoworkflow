---
title: "Autoresearch P1.Final：风险登记与后续建议"
status: active
updated: 2026-03-27
owner: aw-kernel
last_verified: 2026-03-27
---
# Autoresearch P1.Final：风险登记与后续建议

> 说明：本文是 `analysis` 阶段的风险登记与后续建议记录，不作为主线真相或执行入口。已落地实现仍应以 `toolchain/` 入口说明为准。

## 一、定位与适用范围

本页聚焦 P1.1 - P1.3 已落地实现后的残留风险与可执行的后续建议，属于 `analysis` 的阶段性记录：

- 不替代 `docs/knowledge/` 的主线规则
- 不替代 `docs/operations/` 的 repo-local runbook
- 不替代 `toolchain/` 的真实实现入口

## 二、当前已落地的 P1.1 - P1.3 关键链路

当前 P1.1 - P1.3 的实现链路保持为：

- P1.1：`mutation-registry.json` 提供可选择 family
- P1.2：`worker-contract.json` 固定 agent-facing 执行信封，selector 负责最小 deterministic 选择
- P1.3：`feedback-distill.json` 与 `feedback-ledger.jsonl` 固定 feedback 压缩与 family 级历史，selector 在 ledger 存在时做反馈感知优先级

对应的主要实现落点在 `toolchain/scripts/research/` 的 `run_autoresearch.py`、`autoresearch_round.py`、`autoresearch_selector.py`、`autoresearch_feedback_distill.py` 与相关测试。

## 三、残留风险登记（P1.Final）

### 1) P1.1：`target_paths` 仍存在“重叠即通过”的放大风险

- 现状：文档要求 `target_paths` 必须是 `contract.mutable_paths` 的子集，只允许收窄；当前实现仍按对称 overlap 判断。
- 影响：更宽的父路径可能被误判为合法 mutation scope，破坏 P1.1 的最小边界合同。
- 风险级别：高

### 2) P1.1：registry bookkeeping 仍可被手工改写后继续消费

- 现状：`attempts / last_selected_round / last_decision / status` 在文档上是脚本持有字段，但 loader/prepare-round 仍会直接信任磁盘中的 schema-valid 值。
- 影响：手工改写 `mutation-registry.json` 可以重置 attempts 或重新激活 exhausted family，而没有 tamper 信号。
- 风险级别：中

### 3) P1.2：worker contract 仍间接依赖可变 scoreboard

- 现状：`run-round` 重建 `worker-contract.json` 时会重新读取 run-level `scoreboard.json`，而不是只依赖 round authority 快照。
- 影响：如果 `prepare-round` 之后顶层 scoreboard 变化，worker contract 可能在 round authority 未变时仍然校验失败。
- 风险级别：高
- 当前复扫状态：`部分覆盖`。新增的 legacy v1 worker-contract 兼容路径不再要求这条重建链，但 current v2 路径仍然开放这个问题。

### 4) P1.2：phase contract 与实现已有漂移

- 现状：P1.2 文档仍把 selector 描述为 deterministic-only，但当前实现已经接入 `feedback_ledger`、`scheduler_reason` 与 `adaptive_priority`。
- 影响：如果继续把 P1.2 文档当成 current contract，会误读 selector 输入、输出和阶段边界。
- 风险级别：中
- 当前复扫状态：`部分覆盖`。P1.3 文档已经写明当前 selector 语义，但 P1.2 阶段文档仍旧陈旧。

### 5) P1.2：`comparison_baseline` 与 `recent_feedback_excerpt` 的消费合同仍偏弱

- 现状：`comparison_baseline` 缺 lane 时仍可退化为 `null` 值并通过 schema；`recent_feedback_excerpt` 仍固定为空数组。
- 影响：worker-facing context 字段存在，但没有被强约束为“必须有有效内容”的可消费合同。
- 风险级别：中

### 6) P1.3：adaptive selector 当前仍是 ledger-only 排序

- 现状：P1.3 文档把“当前 champion scoreboard 摘要”列为 scheduler 最小输入，但当前排序逻辑没有真正消费它。
- 影响：实现比阶段合同更窄，当前 adaptive 行为实质上只由 ledger signal 决定。
- 风险级别：高

### 7) P1.3：`suggested_adjustments` / `spawn_proposal` 仍是占位

- 现状：`dimension_feedback_summary`、`suggested_adjustments` 仍为空结构，`spawn_proposal` 仍未进入可执行链路。
- 影响：P1.3 已经完成 deterministic distillation 和 family ranking，但还没有进入“基于 distilled 建议生成 proposal”的下一层闭环。
- 风险级别：中

### 8) P1.3：正信号 family 仍可能被过度重复利用

- 现状：当前 `recent_positive_signal` 只等价于“latest signal is positive”，没有衰减或单独 retry budget。
- 影响：scheduler 可能过度复用最近赢过一次的 family，压低 fresh family 的探索机会。
- 风险级别：中

### 9) P1.3：feedback 落盘顺序仍有部分提交窗口

- 现状：`decide-round` 先写 `feedback-distill.json` 与 `feedback-ledger.jsonl`，再做 promote/discard、history 和 baseline/registry 更新。
- 影响：如果生命周期清理在中途失败，下游可能看到一份“已完成”的 feedback 记录，但 runtime state 尚未完全收敛。
- 风险级别：中

### 10) Bugfix 后新增：legacy worker-contract 兼容路径放宽了 authority/audit 模型

- 现状：`run-round` 现在允许在 `round.json` 缺少 `worker_contract_sha256` 时走 v1 legacy worker-contract 分支，不再统一要求 v2 的 hash-bound envelope 校验。
- 影响：legacy 路径只绑定少量 tracing 字段，`instruction / target_paths / allowed_actions / guardrails / expected_effect` 等 agent-facing 字段的漂移约束明显弱于 current v2 路径。
- 风险级别：高

## 四、后续建议与最小落地动作

### A. 补模型辅助摘要（P1.3 子阶段 C）

- 在不改变 authority chain 的前提下，允许只写 `dimension_feedback_summary` 与 `suggested_adjustments`。
- 失败必须不影响 `decision` 与数值 delta 的可重算性。

### B. 修正 P1.1 的 subset 校验与 registry tamper 边界（P1.Final 优先）

- 把 `target_paths ⊆ mutable_paths` 从 overlap 改成严格子集语义。
- 明确 registry bookkeeping 是“可持久化状态”还是“需要防篡改的 authority 字段”，并补对应测试。

### C. 冻结 P1.2 的 authority chain（P1.Final 优先）

- 如果 worker contract 需要比较基线，应在 `prepare-round` 时冻结成 round authority，而不是在 `run-round` 时重新读取可变 scoreboard。
- 同时明确 P1.2 文档是历史阶段记录还是仍需维护为 current contract。

### D. 加入 feedback excerpt 到 worker-contract（P1.3+）

- 将最近一条或 N 条 `feedback-ledger` 的摘要写入 `worker-contract.json` 的 `recent_feedback_excerpt`。
- 需要同步更新 schema，并确保 authority 仍由脚本生成。

### E. 扩展 scheduler 的 guardrail（P1.3+）

- 保留 banding，但增加 “连续负信号次数上限” 或 “mixed signal 退避策略”。
- 所有策略变更必须可追溯到 ledger，并保持 deterministic。

### F. Acceptance lane 接入路线（P1.Next）

- 当 acceptance suite 被纳入常规评测时，明确其对 distill 与 scheduling 的权重。
- 若 acceptance 仍是高成本路径，保持其单独 gate，而非直接混入 score delta。

### G. 运行期回写到承接层

- 任何稳定结论应同步更新 `docs/operations/` 与 `toolchain/` 入口说明。
- `analysis` 文档只保留研究记录与风险登记，不承接执行真相。

### H. 明确 legacy worker-contract 的退场条件（Bugfix 后新增）

- 如果保留 legacy v1 兼容路径，应补齐文档、负例测试和退场条件，避免它长期成为默认弱校验分支。
- 如果 legacy 只用于过渡，应明确迁移窗口，并在 round/runtime artifact 上增加更清晰的版本判定信号。

## 五、与 P1.1 - P1.3 研究合同的关系

本页不新增 P1.1 - P1.3 的 contract 内容，仅记录落地后的风险与建议。
如需更新阶段合同或主线规则，应分别回写到：

- `docs/analysis/autoresearch-p1-1-mutation-registry.md`
- `docs/analysis/autoresearch-p1-2-worker-contract-and-minimal-selector.md`
- `docs/analysis/autoresearch-p1-3-feedback-distillation-and-adaptive-scheduler.md`

并同步到 `toolchain/` 与 `docs/operations/` 的承接位。
