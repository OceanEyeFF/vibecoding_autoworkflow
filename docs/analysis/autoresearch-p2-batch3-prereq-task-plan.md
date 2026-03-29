---
title: "Autoresearch P2：Batch 3 前序任务规划"
status: superseded
updated: 2026-03-29
owner: aw-kernel
last_verified: 2026-03-29
---
# Autoresearch P2：Batch 3 前序任务规划

> 说明：本文是 `autoresearch-p2-lightweight-single-prompt-codex-task-plan.md` 的补充执行文档，只覆盖 Batch 3 正式开始前必须先完成的 3 个小任务。目标不是扩展设计，而是降低 smoke 与回归实现时的假阳性和夹具返工。

> 当前状态：本文仅保留为 Batch 3 开工前的历史规划；当前已验证的运行边界优先以 [docs/operations/autoresearch-minimal-loop.md](../operations/autoresearch-minimal-loop.md) 和 [autoresearch-p2-exrepo-input-hygiene-task-plan.md](./autoresearch-p2-exrepo-input-hygiene-task-plan.md) 为准。

## 一、规划目标

本规划只解决 Batch 3 开工前的三个具体风险：

- 避免误复用现有 `claude` smoke 夹具
- 固定 family-stop 的测试夹具语义
- 固定 replay 分支的触发条件与断言面

本规划不覆盖：

- Batch 3 正式 smoke 与回归的完整实现
- stop rule 规则本身再设计
- replay 策略本身再设计
- runbook 或 README 承接

## 二、任务清单

### 任务ID：T-B3-PRE-01
任务名称：隔离 P2 smoke 夹具，禁止复用旧 claude smoke
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 建立一套独立的 P2 smoke 测试入口，使 Batch 3 后续验证不再依赖现有 P1.3 的 `claude -> claude` smoke 夹具。
- 结果必须让执行 Agent 明确区分“P1.3 主链路仍可跑”和“P2 单 Prompt、Codex-only 主路径已验证”。

#### 2. 非目标（Non-goals）

- 不修改 P1.3 smoke 的既有语义
- 不引入 live Codex smoke
- 不更新 `docs/operations/`
- 不修改产品代码或 backend 实现

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/test_autoresearch_p1_3_smoke.py`
  - 如有必要，新增 `toolchain/scripts/research/test_autoresearch_p2_smoke.py`
- Out-of-scope：
  - `product/`
  - `docs/operations/`
  - `toolchain/scripts/research/backends/`

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `docs/analysis/autoresearch-p2-lightweight-single-prompt-codex-task-plan.md`
  - `toolchain/scripts/research/test_autoresearch_p1_3_smoke.py`
  - `toolchain/scripts/research/test_run_autoresearch.py`
  - `toolchain/scripts/research/test_autoresearch_round.py`
- 可选参考文件：
  - `toolchain/scripts/research/README.md`
  - `docs/operations/autoresearch-minimal-loop.md`
- 不需要读取的区域：
  - `product/`
  - `docs/knowledge/`

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：新增独立 smoke 文件，不在旧 P1.3 smoke 上堆叠 P2 语义
- 旧 smoke 只允许最小清理，不允许顺手改造成 P2 smoke
- P2 smoke 默认使用 deterministic fake runner，不依赖 live backend

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：medium
- 原因：主要是夹具边界隔离与测试入口整理，逻辑风险中等

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：无
- 可并行任务：T-B3-PRE-02、T-B3-PRE-03
- 是否属于某个批次（Batch）：Batch 3 Preflight

#### 8. 风险与不确定性（Risks）

- 若直接复用 P1.3 smoke，容易把 `claude -> claude` 假阳性误写成 P2 证据
- 若新 smoke 文件仍偷偷复用旧 helper，后续断言会继续混淆
- 若 smoke 命名不清晰，README 承接时会继续混线

#### 9. 验证计划（Validation Plan）

- Static：
  - 运行 smoke 相关测试文件
- Test：
  - 确认 P1.3 smoke 仍保持原语义
  - 确认 P2 smoke 合同显式包含 `target_task`、`target_prompt_path`、`codex -> codex`
- Runtime：
  - 不要求 live runtime
- 是否可以做 smoke test：
  - 可以，这就是本任务核心

#### 10. 完成标准（Exit Criteria）

- P1.3 smoke 继续通过
- P2 smoke 文件已独立存在，且不依赖 `claude` 默认夹具
- P2 smoke 的 contract/fixture 已能表达单 Prompt、Codex-only 约束

#### 11. 失败协议（Failure Handling）

- 若只能通过重写 P1.3 smoke 才能引入 P2 smoke，必须停止并报告夹具耦合点
- 若需要引入 live backend 才能证明 P2，必须停止并报告 deterministic 缺口
- 允许请求更多上下文，但不得扩大到 README/runbook 承接

### 任务ID：T-B3-PRE-02
任务名称：固定 family-stop 测试夹具语义
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 为 “all active mutation families have been tried at least once and the run has no final keep” 这条 stop rule 建立稳定测试夹具。
- 结果必须避免把 “selector 没有可选 mutation” 误判成 “family-stop 命中”。

#### 2. 非目标（Non-goals）

- 不修改 stop rule 规则本身
- 不重构 selector
- 不修改 mutation registry schema
- 不处理 replay 断言

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/test_run_autoresearch.py`
  - 如有必要，新增/更新 `toolchain/scripts/research/test_autoresearch_p2_smoke.py`
- Out-of-scope：
  - `toolchain/scripts/research/autoresearch_selector.py`
  - `product/`
  - `docs/operations/`

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `toolchain/scripts/research/run_autoresearch.py`
  - `toolchain/scripts/research/test_run_autoresearch.py`
  - `toolchain/scripts/research/autoresearch_mutation_registry.py`
- 可选参考文件：
  - `toolchain/scripts/research/autoresearch_selector.py`
  - `docs/analysis/autoresearch-p2-lightweight-single-prompt-codex-task-plan.md`
- 不需要读取的区域：
  - `product/`
  - `docs/knowledge/`

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：先稳定 fixture，再复用到 P2 smoke
- 不要把 `max_candidate_attempts_per_round` 默认设为 `1` 后直接断言 family-stop
- 优先保留 `status == active` 且 `attempts > 0` 的 entry，确保命中的是 stop gate 而不是 selector fail

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：medium
- 原因：风险在于测试语义偏差，不在实现复杂度

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：无
- 可并行任务：T-B3-PRE-01、T-B3-PRE-03
- 是否属于某个批次（Batch）：Batch 3 Preflight

#### 8. 风险与不确定性（Risks）

- entry 若被过早置为 `exhausted`，会绕开当前 active-entry stop gate
- smoke 若只断言 exit code，不断言错误文本，容易把 stop reason 混淆
- 测试夹具若直接消费 selector 空集异常，会丢掉 Batch 2 的 stop 语义证据

#### 9. 验证计划（Validation Plan）

- Static：
  - 运行 `test_run_autoresearch.py`
- Test：
  - 覆盖 family-stop 命中路径
  - 区分 family-stop 和无可选 mutation 的报错文本
- Runtime：
  - 不要求 live runtime
- 是否可以做 smoke test：
  - 可以，但以 deterministic 为主

#### 10. 完成标准（Exit Criteria）

- family-stop 相关测试稳定通过
- 测试能明确区分 stop gate 命中与 selector 无可选 entry
- 该 fixture 可直接被 P2 smoke 复用

#### 11. 失败协议（Failure Handling）

- 若必须修改 selector 才能做稳定断言，必须停止并报告耦合原因
- 若 stop gate 语义与现有实现不一致，必须先回报偏差，不得自行改规则
- 允许请求更多上下文，但不得扩展到 replay 逻辑修改

### 任务ID：T-B3-PRE-03
任务名称：固定 replay 触发条件与断言面
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 为 replay 分支建立一套稳定的前置夹具和断言口径。
- 结果必须确保后续 smoke 真的进入 replay 分支，而不是只测到最终 `decision`。

#### 2. 非目标（Non-goals）

- 不修改 replay 规则本身
- 不重构 worktree 生命周期
- 不修改 stop rule
- 不更新 runbook/README

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/test_autoresearch_round.py`
  - 如有必要，新增/更新 `toolchain/scripts/research/test_autoresearch_p2_smoke.py`
- Out-of-scope：
  - `toolchain/scripts/research/worktree_manager.py`
  - `docs/operations/`
  - `product/`

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `toolchain/scripts/research/autoresearch_round.py`
  - `toolchain/scripts/research/test_autoresearch_round.py`
  - `toolchain/scripts/research/run_autoresearch.py`
- 可选参考文件：
  - `docs/analysis/autoresearch-p2-lightweight-single-prompt-codex-task-plan.md`
  - `toolchain/scripts/research/test_run_autoresearch.py`
- 不需要读取的区域：
  - `product/`
  - `docs/knowledge/`

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：先固定触发条件，再固定断言字段
- replay fixture 必须满足：
  - provisional decision 先命中 `keep`
  - `round_validation > baseline_validation`
- smoke 不允许只断言最终 `decision`
- 至少同时断言：
  - `provisional_decision`
  - `replay.status`
  - 必要时 `replay.reason`

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：medium
- 原因：这里的风险点主要是测试假阳性，而不是复杂实现

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：无
- 可并行任务：T-B3-PRE-01、T-B3-PRE-02
- 是否属于某个批次（Batch）：Batch 3 Preflight

#### 8. 风险与不确定性（Risks）

- 若 fixture 没有让 validation 严格提升，replay 根本不会执行
- 若只断言最终 `discard`，会把 replay failure 和普通 fixed-rule discard 混淆
- 若只断言 replay passed，不测字段存在性，后续 smoke 仍可能出现假阳性

#### 9. 验证计划（Validation Plan）

- Static：
  - 运行 `test_autoresearch_round.py`
- Test：
  - 至少覆盖 replay passed 或 replay failed 中的一条真实 replay 分支
  - 断言 `decision.json` 中 replay 相关字段存在
- Runtime：
  - 不要求 live runtime
- 是否可以做 smoke test：
  - 可以，但 deterministic 足够

#### 10. 完成标准（Exit Criteria）

- replay 相关测试已证明真实进入 replay 分支
- 断言面覆盖 `provisional_decision` 和 `replay.*` 关键字段
- 该 fixture 可直接服务 Batch 3 正式 smoke

#### 11. 失败协议（Failure Handling）

- 若必须改 replay 规则本身才能稳定触发，必须停止并先回报 Batch 2 语义缺口
- 若 replay 只能通过 live backend 证明，必须停止并说明 deterministic 缺口
- 允许请求更多上下文，但不得直接扩展为 Batch 3 正式 smoke 承接

## 三、任务依赖图

- T-B3-PRE-01、T-B3-PRE-02、T-B3-PRE-03 三者可并行
- 更保守的顺序是先做 T-B3-PRE-01，再并行推进 T-B3-PRE-02 与 T-B3-PRE-03
- 三者全部完成后，才能开始 Batch 3 正式任务

简化为：

```text
T-B3-PRE-01 ----\
                  -> Batch 3
T-B3-PRE-02 ----/
T-B3-PRE-03 ----/
```

## 四、推荐执行顺序（Batch 划分）

### Batch 3 Preflight

- T-B3-PRE-01
- T-B3-PRE-02
- T-B3-PRE-03

说明：

- 这是 Batch 3 的前序任务组
- 目标是先清掉 smoke 设计阶段最容易出现的三类假阳性

### Batch 3 Proper

- 正式的 P2 smoke 与回归覆盖任务

说明：

- 只有在前序任务组全部通过后才允许进入

## 五、可并行执行的任务组

- 并行组 A：
  - T-B3-PRE-01
  - T-B3-PRE-02
  - T-B3-PRE-03

说明：

- 三者写集可能都会碰到测试目录
- 并行时需提前约定文件 ownership，避免多个 Agent 同时修改同一测试文件

## 六、高风险任务列表

- T-B3-PRE-03：最容易写出“看起来测了 replay，实际没触发 replay”的假阳性
- T-B3-PRE-02：最容易把 selector 空集错误误判为 family-stop
- T-B3-PRE-01：若隔离不彻底，会把旧 `claude` smoke 继续混入 P2 证据面

## 七、推荐整体执行策略

推荐策略是：

1. 先把 Batch 3 的前序风险当成“测试语义收敛问题”，而不是功能实现问题。
2. 先隔离 smoke 夹具，再修 stop/replay 的测试语义。
3. 只有当前序夹具稳定后，才开始写 Batch 3 正式 smoke 和回归覆盖。

一句话原则：

- 先隔离旧夹具，再固定 stop/replay 断言，最后再写 Batch 3 正式验证。
