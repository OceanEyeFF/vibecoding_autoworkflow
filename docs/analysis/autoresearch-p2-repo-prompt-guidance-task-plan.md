---
title: "Autoresearch P2：Repo 级 Prompt 改进建议任务规划"
status: superseded
updated: 2026-04-09
owner: aw-kernel
last_verified: 2026-04-09
---
# Autoresearch P2：Repo 级 Prompt 改进建议任务规划

> 当前状态：本文保留为已归档的历史执行规划，不再作为当前默认开发目标。
>
> 当前 `analysis/` 层分流入口请先回到 [Analysis README](./README.md)；`autoresearch` 当前唯一保留的开发目标入口改为：
>
> - [Autoresearch：下一阶段 CLI 模块化与插拔化建议](./autoresearch-next-stage-cli-modularity-plan.md)
>
> 本文继续保留为 repo 级 prompt guidance 方向的一版历史任务拆解记录。

## 一、规划目标

本规划只解决下面这组已确认问题：

- 现有 `scoreboard.json` 已保留 repo 粒度结果，但 `feedback-distill.json` 仍只压 lane 级平均分
- 多 repo run 中“部分 repo 明显退化、部分 repo 明显提升”会被 lane 平均分压平
- 当前 `suggested_adjustments` 只能给出 family 级粗建议，无法说明“哪类 repo 在提示词上暴露了什么问题”
- 需要一个最终总建议，帮助判断下一轮 prompt 应该朝哪个方向改

本规划的目标是：

- 为每个 `(lane, repo, task)` 生成 repo 级 prompt 改进建议
- 在 round 级 artifact 中保留 rich 建议，便于人工复盘
- 在 run 级 ledger 中只保留 compact 的总建议，避免 selector 与 prepare-round 背上无关上下文
- 在不改 fixed-rule `decision.json` 的前提下，为下一轮 worker 提供可控的方向性输入

本规划不覆盖：

- 新的 judge backend
- 改写 keep / discard 固定规则
- acceptance lane 常规接入
- 跨 run 的 study memory 或长期知识库存储
- 直接用模型自由生成不可重算的 decision / registry / mutation

## 二、当前问题与已冻结事实

当前代码里已经有三条必须承认的事实：

1. `toolchain/scripts/research/autoresearch_scoreboard.py` 已经把 repo 级 eval 结果落到 `repo_tasks`
2. `toolchain/scripts/research/autoresearch_feedback_distill.py` 当前只消费 lane 级 `avg_total_score / parse_error_rate / timeout_rate`
3. `feedback-distill.json` 与 `feedback-ledger.jsonl` 当前共用同一套 payload 形状和校验函数

这意味着如果直接把 repo 级建议塞进现有 distill payload：

- run 级 ledger 也会被迫存下完整 repo 明细
- selector / `recent_feedback_excerpt` / worker contract 会读到过重上下文
- 现有 `load_feedback_ledger()`、`upsert_feedback_ledger_entry()` 与测试夹具都会被隐式耦合放大

真实样本已经证明这个缺口存在，而不是假设问题：

- `.autoworkflow/autoresearch/manual-cr-codex-loop-6-3-3-r000001-m046830/scoreboard.json`
- `.autoworkflow/autoresearch/manual-cr-codex-loop-6-3-3-r000001-m046830/rounds/round-001/scoreboard.json`
- `.autoworkflow/autoresearch/manual-cr-codex-loop-6-3-3-r000001-m046830/rounds/round-002/scoreboard.json`

在这组 run 中，lane 平均分能表达“整体变差”，但不能表达：

- 哪些 repo 受损最严重
- 哪些 repo 反而改善
- 哪些维度在不同 repo 上暴露出一致的 prompt 缺陷

## 三、已冻结实施决议

为避免实现时再次发散，先冻结以下决议：

### 1. fixed-rule decision 不变

- `decision.json` 继续只由既有固定规则决定
- repo 级建议和总建议都只能停留在 suggestion layer
- 它们不能反向改写 `decision`、`checks`、`replay` 或 registry bookkeeping

### 2. v1 先做 rich round artifact + compact ledger

- round 级 `feedback-distill.json` 保留完整 repo 级建议
- run 级 `feedback-ledger.jsonl` 只保留 compact 的总建议摘要
- 不继续沿用“round distill 与 ledger 完全同形”的旧耦合

### 3. v1 不改 judge contract

- 不新增 eval rubric 维度
- 不要求 judge 额外输出 repo 建议字段
- 只复用现有 `repo_tasks[].total_score / overall / dimension_feedback`

### 4. v1 默认只保证 `context-routing`

- 当前真实多 repo run 样本集中在 `context-routing`
- `context-routing` 的 `EVAL_SCORE_DIMENSIONS` 已稳定，最适合作为第一落点
- 其他 task 在 v1 可以显式落成 `unsupported_task`，而不是假装已经有高质量建议能力

### 5. worker 接入后置

- 第一阶段先把 repo 级建议和总建议写成 artifact，供人工复盘与回测
- 只有在建议质量被验证后，才把 compact 总建议接入 worker-facing context
- worker 侧只消费总建议，不消费完整 repo 明细

## 四、两阶段执行策略

### Phase 1：补齐 repo 级建议和总建议 artifact

目标：

- 让每轮结果不仅有 lane 平均分，也有 repo 级 prompt guidance
- 让 `feedback-distill.json` 能回答“哪个 repo 暴露了什么提示词问题”
- 让 `feedback-ledger.jsonl` 能回答“下一轮总方向是什么”

不做：

- 不把完整 repo 建议喂进 worker contract
- 不让 selector 直接吃 repo 明细

### Phase 2：把总建议有限接入 worker

目标：

- 只把 compact 的总建议接进 `prepare-round -> round authority -> worker-contract -> worker prompt`
- 让下一轮 mutation 能明确知道“总方向”，而不是只看最近几条 family signal

不做：

- 不把多 repo 明细原样塞给 worker
- 不把 worker prompt 改成 planner / critic 多角色流程

## 五、任务清单

### 任务ID：T-001
任务名称：拆分 round distill 与 ledger 的 contract
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 打破 `feedback-distill.json` 与 `feedback-ledger.jsonl` 的同形耦合。
- 为 rich round artifact 和 compact ledger entry 建立两套明确 contract。

#### 2. 非目标（Non-goals）

- 不修改 fixed-rule decision
- 不引入新的 CLI 子命令
- 不直接实现 repo 级建议生成逻辑

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/autoresearch_feedback_distill.py`
  - `toolchain/scripts/research/autoresearch_round.py`
  - `toolchain/scripts/research/test_autoresearch_feedback_distill.py`
  - `toolchain/scripts/research/test_autoresearch_round.py`
  - 新增或更新 schema fixture
- Out-of-scope：
  - `run_autoresearch_loop.py`
  - `autoresearch_selector.py`
  - `product/`

#### 4. 执行策略（Execution Strategy）

- 新增 round artifact payload 与 ledger entry payload 的显式 builder
- 让 ledger 通过 projection 从 round payload 得到，而不是直接复用整对象
- 若 schema 不兼容，明确 bump version，不做静默兼容漂移

#### 5. 风险与不确定性（Risks）

- 现有 `load_feedback_ledger()`、excerpt、selector 都依赖旧 payload 形状
- 若版本切换不清楚，旧测试夹具会大面积失效

#### 6. 验证计划（Validation Plan）

- unit tests 覆盖：
  - rich round payload 校验
  - compact ledger entry 校验
  - old same-shape assumption 被显式替换

#### 7. 完成标准（Exit Criteria）

- `feedback-distill.json` 与 `feedback-ledger.jsonl` 已是两套明确 contract
- ledger 不再被迫携带完整 repo 明细
- 相关测试通过

### 任务ID：T-002
任务名称：实现 repo 级 prompt 改进建议生成
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 对每个 `(lane, repo, task)` 生成可复盘的 prompt 改进建议。
- 建议必须基于 baseline vs round 的 repo 粒度对比，以及现有 `dimension_feedback`。

#### 2. 非目标（Non-goals）

- 不改 eval rubric
- 不把 repo 建议写回 mutation registry
- 不让模型自由总结整轮结果

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/autoresearch_feedback_distill.py`
  - 如有必要，`toolchain/scripts/research/autoresearch_scoreboard.py`
  - `toolchain/scripts/research/test_autoresearch_feedback_distill.py`
- Out-of-scope：
  - `decision.json`
  - `autoresearch_selector.py`
  - `run_autoresearch_loop.py`

#### 4. 冻结字段形状（建议）

round 级建议对象建议最小包含：

- `lane_name`
- `repo`
- `task`
- `baseline_total_score`
- `round_total_score`
- `score_delta`
- `signal_strength`
- `dimension_signals`
- `prompt_adjustments`
- `evidence_excerpt`
- `generation_status`

其中：

- `dimension_signals` 用于压缩维度层面的 `stable / improved / weaker`
- `prompt_adjustments` 是最终给 prompt 的动作建议
- `evidence_excerpt` 只保留最小引用，不复制整段 judge 文本
- `generation_status` 至少支持：
  - `generated`
  - `unsupported_task`
  - `missing_baseline_row`

#### 5. 执行策略（Execution Strategy）

- 先按 `(lane_name, repo, task)` 连接 baseline / round 的 `repo_tasks`
- 再基于 score delta 和 `dimension_feedback` 生成 deterministic guidance
- v1 只为 `context-routing` 输出高置信建议
- 非 `context-routing` task 显式输出 `unsupported_task`

#### 6. 风险与不确定性（Risks）

- baseline 与 round 的 repo 集合可能不完全一致
- 同 repo 未来可能出现多 task，join key 必须稳定
- `dimension_feedback` 是自然语言，压缩规则要避免过拟合某一份 judge 措辞

#### 7. 验证计划（Validation Plan）

- unit tests 覆盖：
  - 单 repo 改善
  - 单 repo 退化
  - 混合信号
  - 缺 baseline row
  - unsupported task

#### 8. 完成标准（Exit Criteria）

- round `feedback-distill.json` 已包含 repo 级建议列表
- 样本 run 能区分“哪些 repo 退化、哪些 repo 改善”
- 建议生成是 deterministic 的

### 任务ID：T-003
任务名称：实现总建议蒸馏与 ledger compact summary
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 从 repo 级建议中蒸馏出一份总建议，用来决定下一轮 prompt 改进方向。
- 这份总建议必须足够小，能安全进入 ledger、excerpt 和后续 worker context。

#### 2. 非目标（Non-goals）

- 不让 selector 直接按 repo 明细排序
- 不让总建议替代 family signal
- 不把总建议写成开放式长文总结

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/autoresearch_feedback_distill.py`
  - `toolchain/scripts/research/test_autoresearch_feedback_distill.py`
  - 如有必要，`toolchain/scripts/research/autoresearch_selector.py`
  - `toolchain/scripts/research/test_autoresearch_selector.py`
- Out-of-scope：
  - `run_autoresearch_loop.py`
  - `autoresearch_worker_contract.py`

#### 4. 冻结字段形状（建议）

总建议最小包含：

- `aggregate_direction`
- `aggregate_suggested_adjustments`
- `top_regression_repos`
- `top_improvement_repos`
- `dominant_dimension_signals`
- `generation_status`

建议规则：

- 最多保留 `2-3` 条方向性建议
- 最多保留少量 repo 名字，不复制完整 repo 建议列表
- 优先表达一致性问题，而不是罗列全部个例

#### 5. 执行策略（Execution Strategy）

- 先统计 repo 级建议中的主导退化模式
- 再把高频问题压成有限的方向性建议
- ledger 只保存 compact summary
- `build_recent_feedback_excerpt()` 优先复用 compact 总建议，而不是 repo 明细

#### 6. 风险与不确定性（Risks）

- 若压缩规则太弱，总建议会回退成 lane 平均分的同义反复
- 若压缩规则太强，总建议会丢失真正关键的 repo 差异

#### 7. 验证计划（Validation Plan）

- unit tests 覆盖：
  - 多 repo 退化归一成单方向建议
  - 退化与改善并存时的优先级
  - excerpt 只消费 compact summary

#### 8. 完成标准（Exit Criteria）

- round payload 中已有总建议
- ledger 只存 compact summary，不存完整 repo 明细
- excerpt 与 selector 仍能正常工作

### 任务ID：T-004
任务名称：把总建议有限接入 worker-facing context
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 在不引爆 worker context 的前提下，把总建议接入下一轮 worker。
- 让 worker 看到“本轮应该往哪个方向改 prompt”，而不是只看到 family 级 keep/discard 摘要。

#### 2. 非目标（Non-goals）

- 不把完整 repo 级建议喂给 worker
- 不新增第二套 worker prompt 生成器
- 不改变 `target_paths`、`allowed_actions` 或其它 authority 字段

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/run_autoresearch.py`
  - `toolchain/scripts/research/autoresearch_round.py`
  - `toolchain/scripts/research/autoresearch_worker_contract.py`
  - `toolchain/scripts/research/run_autoresearch_loop.py`
  - 相关测试
- Out-of-scope：
  - `autoresearch_selector.py`
  - `decision.json`
  - prompt 文件本身

#### 4. 执行策略（Execution Strategy）

- 不新增大块自由文本字段
- 优先复用 `recent_feedback_excerpt` 或新增一个 compact `aggregate_prompt_guidance`
- 如果新增字段，必须冻结进 round authority，避免 prepare 之后漂移
- worker prompt 只显示总方向和有限建议，不显示 repo 全清单

#### 5. 风险与不确定性（Risks）

- 如果把 repo 明细原样塞入 worker，prompt 体积会快速膨胀
- 如果 authority 没冻结，prepare 后 ledger 漂移会污染 worker envelope

#### 6. 验证计划（Validation Plan）

- unit / integration tests 覆盖：
  - prepare-round 冻结 guidance
  - worker contract 包含 compact guidance
  - loop wrapper 正确渲染 guidance

#### 7. 完成标准（Exit Criteria）

- 下一轮 worker 能消费 compact 总建议
- round authority 保持 deterministic
- worker context 体积受控，没有引入 repo 明细爆炸

### 任务ID：T-005
任务名称：同步文档、README 与回归验证
任务类型（Task Type）：Document

#### 1. 任务目标（Goal）

- 把新的 repo 级建议 / 总建议 contract、边界和运行事实同步到文档入口。
- 补齐 deterministic 回归验证，避免后续维护时只剩 artifact 名字、没有规则说明。

#### 2. 非目标（Non-goals）

- 不扩写新的长期知识层规则
- 不把 planning 文档当实现真相替代物

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/README.md`
  - `docs/operations/research-cli-help.md`
  - `docs/operations/autoresearch-minimal-loop.md`
  - `docs/analysis/README.md`
  - 如有必要，`docs/analysis/autoresearch-p1-3-feedback-distillation-and-adaptive-scheduler.md`
- Out-of-scope：
  - `docs/knowledge/`
  - `product/`

#### 4. 执行策略（Execution Strategy）

- 代码和测试稳定后再写文档
- 先更新实现 README，再更新 operations runbook，最后补 analysis 承接
- 文档只描述已验证事实，不提前写 v2 愿景

#### 5. 验证计划（Validation Plan）

- 运行相关 deterministic 测试
- 运行必要的 docs / governance 检查
- 核对 `analysis/README.md` 当前执行规划入口

#### 6. 完成标准（Exit Criteria）

- 运行文档与 README 已反映 repo 级建议和总建议的真实 contract
- 相关测试通过
- `analysis/README.md` 的当前规划入口已对齐

## 六、推荐执行顺序

推荐顺序分两层：

1. 先拆 contract，再补 repo 建议，再补总建议。
2. worker 接入和文档更新后置，避免建议层 contract 还没稳定就把上下文写死。

推荐依赖：

- `T-001` 最先执行
- `T-002` 依赖 `T-001`
- `T-003` 依赖 `T-001`、`T-002`
- `T-004` 依赖 `T-003`
- `T-005` 最后执行

## 七、整体风险

本规划的主要风险只有三类：

- 继续沿用旧的 same-shape distill/ledger 设计，导致 ledger 无上限膨胀
- 过早把 repo 明细接进 worker，导致 prompt 体积和噪声失控
- 假装四个 task 都已具备高质量 repo 建议能力，实际只有 `context-routing` 被真实样本证明

因此 v1 的技术策略必须保持克制：

- 先拆 contract
- 先做 deterministic rules
- 先对 `context-routing` 做强保证
- 再决定是否扩到其他 task

## 八、完成判断

满足下面四条即可认为本规划对应能力已最小闭环：

- round 级 `feedback-distill.json` 能输出 repo 级 prompt 改进建议
- run 级 `feedback-ledger.jsonl` 能输出 compact 的总建议
- fixed-rule decision 与 selector 主链没有被 suggestion layer 污染
- 下一轮 worker 至少可以有限消费“总方向”，而不需要读取完整 repo 明细
