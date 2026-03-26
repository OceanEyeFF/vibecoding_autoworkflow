---
title: "Autoresearch P0.3：Baseline Loop 与 Round 执行"
status: active
updated: 2026-03-26
owner: aw-kernel
last_verified: 2026-03-26
---
# Autoresearch P0.3：Baseline Loop 与 Round 执行

> 目的：在已有 contract、scoreboard 和 worktree 控制壳的前提下，跑通第一版 baseline loop；外层 round 生命周期由脚本控制，单轮 candidate 的内容改动交给 Codex 执行。

## 一、阶段定位

P0.3 只回答下面问题：

- baseline 之后的一轮 round 如何执行
- mutation spec 如何进入 round
- 为什么这一层应采用“脚本控制外环，Codex 执行内环”
- keep / discard 的最小决策应如何固定

P0.3 不回答下面问题：

- 自动 mutation 搜索空间如何扩张
- planner / proposer / critic 多角色体系如何引入
- acceptance lane 是否每轮都跑

## 二、核心模型

P0.3 的最小 loop 形态是：

```text
baseline
  -> prepare round
  -> create candidate worktree
  -> apply one mutation spec
  -> run train suites
  -> run validation suites
  -> aggregate scoreboard
  -> keep | discard
  -> next round
```

这时的关键约束是：

- 每轮只允许一个 mutation spec
- 每轮只允许一个 candidate worktree
- 决策依据必须来自脚本聚合结果，而不是模型自由解释

## 三、为什么这一层适合混合控制

如果完全脚本化，系统只能执行静态 mutation，不足以体现 autoresearch 对语义内容的优化能力。

如果完全交给 Codex，常见问题会变成：

- round state 不稳定
- keep / discard 规则漂移
- 不同轮次的记账口径不一致

因此 P0.3 最合适的形态是：

- 外层 loop：脚本控制
- 内层 candidate 修改：Codex 控制

## 四、控制边界：脚本 vs Codex

### 1. 脚本负责外环

外环动作包括：

- round 初始化
- candidate worktree 准备
- 传入 mutation spec
- 调用 research runner
- 聚合 train / validation 结果
- 计算 keep / discard
- 记录 `decision.json`
- promote 或 cleanup

这些动作应由：

- `run_autoresearch.py`
- `autoresearch_round.py`
- `worktree_manager.py`

来负责。

### 2. Codex 负责内环

内环动作包括：

- 读取 `mutation.json`
- 在 candidate worktree 内修改允许变更的文件
- 对当前 round 输出一份简短 `agent-report.md`

这一层可以使用：

- 主控 Codex 直接执行
- 或主控 Codex 派一个 subagent 进入 candidate worktree 执行单轮修改

约束：

- subagent 只负责本轮内容改动
- subagent 不负责创建 / 删除 worktree
- subagent 不负责最终 keep / discard 裁决

## 五、mutation spec 的最小形状

P0.3 还不做自动搜索，因此 mutation spec 可以先人工给定。

建议最小字段：

- `round`
- `mutation_id`
- `kind`
- `target_paths`
- `allowed_actions`
- `instruction`
- `expected_effect`

说明：

- `kind` 例如：`prompt_rewrite`、`adapter_rephrase`、`ordering_adjustment`
- `allowed_actions` 用来限制本轮只做允许的修改类型
- `expected_effect` 不作为 keep 依据，只作为 round report 的解释字段

## 六、建议的 round 目录

每轮放在：

- `.autoworkflow/autoresearch/<run-id>/rounds/round-NNN/`

建议最小文件：

- `mutation.json`
- `round.json`
- `decision.json`
- `agent-report.md`
- `train/`
- `validation/`

其中：

- `train/` 和 `validation/` 下保存本轮 run artifacts
- `decision.json` 只记录聚合后的 round 结论

## 七、建议的 round 执行顺序

### 1. 准备阶段

1. 脚本读取 `contract.json`
2. 脚本读取 `runtime.json`
3. 脚本创建本轮 candidate worktree
4. 脚本写入 `mutation.json`

### 2. candidate 执行阶段

1. Codex 读取 `mutation.json`
2. Codex 在 candidate worktree 内完成本轮改动
3. Codex 写出 `agent-report.md`
4. Codex 退出 candidate worktree

### 3. 评测阶段

1. 脚本运行 train suites
2. 脚本运行 validation suites
3. 脚本更新本轮 scoreboard

### 4. 决策阶段

1. 脚本读取本轮 scoreboard
2. 脚本生成 `decision.json`
3. `keep` 则 promote
4. `discard` 则 cleanup

## 八、第一版 keep / discard 规则

P0.3 不应让模型自由决定结果，建议直接固定为脚本规则。

第一版可以收敛为：

### keep

同时满足：

- `train_score > baseline_train_score`
- `validation_score >= baseline_validation_score`
- `parse_error_rate` 没有显著升高
- `timeout_rate` 没有显著升高

### discard

命中任一：

- train 没提升
- validation 退化
- 出现明显 `parse_error` 回归
- 出现明显 timeout / hard fail 回归

### qualitative veto

只有 veto 权，没有奖励权。

也就是说：

- 定性检查可以阻止 keep
- 但不能单独把一个硬指标无提升的 round 提升为 keep

## 九、subagent 的使用边界

P0.3 可以安全引入 subagent，但范围必须收窄。

适合交给 subagent 的任务：

- 单轮 prompt / adapter 文本改写
- 单轮 target path 内的局部编辑
- 根据 `dimension_feedback` 做一次有边界的修订

不适合交给 subagent 的任务：

- round 主控
- worktree 生命周期
- scoreboard 聚合
- keep / discard 裁决

因此这里的准确描述应是：

- “用 subagent 跑 candidate round 的内容工作”
- 而不是“用 subagent 管整个 autoresearch loop”

## 十、建议的 CLI 切分

P0.3 可以先不做复杂 CLI，只要把职责切开。

建议最小入口：

- `run_autoresearch.py init`
- `run_autoresearch.py baseline`
- `run_autoresearch.py prepare-round`
- `run_autoresearch.py run-round`
- `run_autoresearch.py decide-round`

如果后续需要，再把实现拆到：

- `autoresearch_round.py`

## 十一、验收标准

P0.3 完成后，应满足：

1. 同一 run 能连续跑多轮
2. 每轮只消费一个 mutation spec
3. candidate 改动可由 Codex 或 subagent 执行
4. keep / discard 由脚本按固定规则输出
5. 每轮都有可追踪的 `decision.json` 与 `agent-report.md`

## 十二、后续关系

P0.3 跑通后，才有条件进入下一阶段：

- 自动 mutation 生成
- mutation fingerprint 去重
- 更复杂的 round scheduling
- 多 judge 或抽样 acceptance 策略

相关文档：

- [Autoresearch P0.1：合同与数据面](./autoresearch-p0-1-contract-and-data-plane.md)
- [Autoresearch P0.2：Worktree 控制壳](./autoresearch-p0-2-worktree-control-shell.md)
- [Research 评测观测与输出规范](./research-eval-observability.md)
