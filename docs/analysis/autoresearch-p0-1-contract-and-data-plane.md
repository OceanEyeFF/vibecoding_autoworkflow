---
title: "Autoresearch P0.1：合同与数据面"
status: active
updated: 2026-03-26
owner: aw-kernel
last_verified: 2026-03-26
---
# Autoresearch P0.1：合同与数据面

> 目的：先把一次 autoresearch run 的静态合同、suite 分层和结果聚合口径固定下来；这一阶段不做自动变异，也不让模型直接管理实验生命周期。

## 一、阶段定位

P0.1 只回答下面问题：

- 一次 autoresearch run 应该如何描述
- baseline 应该如何落盘
- train / validation / acceptance 三层 suite 应该如何分离
- 现有 `run_skill_suite.py` 产物应如何被统一聚合成后续 round 可消费的数据面

P0.1 不回答下面问题：

- worktree 生命周期怎么跑
- 单轮 mutation 怎么生成
- subagent 如何进入 candidate worktree
- 自动 keep / discard 如何执行

## 二、为什么先做这一层

当前仓库已经具备：

- repo-local skill research runner：
  - `toolchain/scripts/research/run_skill_suite.py`
- live acceptance wrapper：
  - `toolchain/scripts/research/run_backend_acceptance_matrix.py`
- task-scoped eval schema materialization
- `run-summary.json` 与 `structured_output` 的稳定输出 contract

但这些能力目前仍然偏“单次执行”，还不是“多轮研究循环”的可复用基座。

如果没有一份稳定的 run contract，后续的：

- worktree 隔离
- round promotion / discard
- mutation 历史去重
- 多 repo train / validation 对比

都会变成临时拼接。

## 三、建议落点

### 1. 稳定 fixture / schema

放在：

- `toolchain/evals/fixtures/schemas/`
- `toolchain/evals/fixtures/suites/`

建议新增：

- `autoresearch-contract.schema.json`
- `autoresearch-scoreboard.schema.json`
- `memory-side-train.v1.yaml`
- `memory-side-validation.v1.yaml`
- `memory-side-acceptance.v1.yaml`

### 2. 运行期状态

放在：

- `.autoworkflow/autoresearch/<run-id>/`

建议最小产物：

- `contract.json`
- `history.tsv`
- `scoreboard.json`
- `baseline/`

### 3. 解析与聚合脚本

放在：

- `toolchain/scripts/research/`

建议新增：

- `autoresearch_contract.py`
- `autoresearch_scoreboard.py`

## 四、run contract 的最小字段

建议固定为如下几组：

### 1. 目标与边界

- `run_id`
- `label`
- `objective`
- `target_surface`
- `mutable_paths`
- `frozen_paths`

### 2. suite 分层

- `train_suites`
- `validation_suites`
- `acceptance_suites`

说明：

- `train_suites` 用于日常轮次优化
- `validation_suites` 用于阻断明显过拟合或 repo-specific 偏差
- `acceptance_suites` 不作为每轮必跑项，留给里程碑或最终验证

### 3. 指标

- `primary_metrics`
- `guard_metrics`
- `qualitative_veto_checks`

约束：

- `primary_metrics` 必须来自稳定可计算字段，例如 `total_score`、`parse_error_rate`、`timeout_rate`、成功率
- `qualitative_veto_checks` 只能做 veto，不作为主奖励来源

### 4. 运行预算

- `max_rounds`
- `max_candidate_attempts_per_round`
- `timeout_policy`
- `promotion_policy`

## 五、scoreboard 的最小形状

P0.1 的 scoreboard 不追求复杂，只要足够支撑后续 round decision。

建议按下面三层聚合：

### 1. run 级

- `baseline_sha`
- `generated_at`
- `rounds_completed`
- `best_round`

### 2. suite lane 级

- `lane_name`
- `suite_file`
- `backend`
- `judge_backend`
- `repos_total`
- `tasks_total`
- `pass_rate`
- `timeout_rate`
- `parse_error_rate`
- `avg_total_score`

### 3. repo / task 级

- `repo`
- `task`
- `phase`
- `total_score`
- `overall`
- `dimension_feedback`

说明：

- repo / task 级数据继续沿用 `run-summary.json` 的结果形状
- scoreboard 只负责把这些结果提升为“可比较的 round 输入”

## 六、控制边界：脚本 vs Codex

P0.1 应当明确以脚本控制为主。

### 1. 交给脚本的部分

- contract schema 校验
- suite manifest 解析
- baseline 结果采集
- scoreboard 计算
- `history.tsv` 初始化

原因：

- 这些动作是确定性、可回放、无歧义的数据处理
- 不应依赖模型“理解后再决定如何记账”

### 2. Codex 在 P0.1 的角色

- 辅助起草第一版 contract 内容
- 辅助检查字段命名是否清晰
- 不负责 contract 的最终消费逻辑

结论：

- P0.1 是“脚本主控，Codex 辅助”

## 七、建议的 baseline 流程

P0.1 只需要把 baseline 跑通：

1. 读取 `contract.json`
2. 校验 suite 引用与 mutable/frozen path 约束
3. 调用 `run_skill_suite.py` 跑 train suites
4. 调用 `run_skill_suite.py` 跑 validation suites
5. 聚合 `run-summary.json`
6. 写出 `scoreboard.json`
7. 记录 `history.tsv` 的 baseline 行

此时还没有：

- candidate branch
- worktree round
- mutation spec

## 八、建议的 `history.tsv` 初始列

P0.1 先固定列，不急着写满。

建议至少包括：

- `round`
- `kind`
- `base_sha`
- `candidate_sha`
- `train_score`
- `validation_score`
- `train_parse_error_rate`
- `validation_parse_error_rate`
- `decision`
- `notes`

baseline 行约定：

- `round = 0`
- `kind = baseline`
- `candidate_sha = -`
- `decision = baseline`

## 九、验收标准

P0.1 完成后，应满足：

1. 能读取并校验 autoresearch contract
2. 能分开执行 train / validation baseline
3. 能把现有 runner 结果聚合成统一 scoreboard
4. 能初始化 `.autoworkflow/autoresearch/<run-id>/` 的最小状态目录
5. 后续阶段不需要重新发明 contract 和 scoreboard

## 十、后续关系

P0.1 完成后，P0.2 才有稳定输入：

- `contract.json`
- `history.tsv`
- `scoreboard.json`
- `baseline_sha`

相关文档：

- [Autoresearch P0.2：Worktree 控制壳](./autoresearch-p0-2-worktree-control-shell.md)
- [Autoresearch P0.3：Baseline Loop 与 Round 执行](./autoresearch-p0-3-baseline-loop-and-round-execution.md)
- [Research 评测契约与边界](./research-eval-contracts.md)
