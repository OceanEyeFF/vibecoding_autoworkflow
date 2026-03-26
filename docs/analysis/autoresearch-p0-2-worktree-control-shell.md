---
title: "Autoresearch P0.2：Worktree 控制壳"
status: active
updated: 2026-03-26
owner: aw-kernel
last_verified: 2026-03-26
---
# Autoresearch P0.2：Worktree 控制壳

> 目的：把每一轮候选实验隔离进独立 `git worktree`，并把 promotion / discard / cleanup 这些高副作用动作收拢到脚本控制层。

## 一、阶段定位

P0.2 只回答下面问题：

- champion 与 candidate 如何建模
- 每轮 worktree 如何创建、命名和清理
- keep / discard 时哪些 git 动作必须脚本化
- 如何保证不污染用户当前工作树

P0.2 不回答下面问题：

- mutation 如何生成
- subagent 在 round 内如何改内容
- score 提升阈值如何设计

## 二、为什么 P0.2 必须单独成层

如果让模型直接掌握实验生命周期，常见失败方式包括：

- candidate branch 命名不一致
- worktree 残留未清理
- round 崩溃后留下脏状态
- 不同候选改动混入用户当前工作树

这些问题都不是“提示词再写清楚一点”可以解决的，而是执行控制面必须脚本化。

## 三、推荐控制模型

建议固定两类分支：

- `champion/<run-id>`
- `candidate/<run-id>/rNNN`

含义：

- `champion/<run-id>`：当前 run 已接受的最佳版本
- `candidate/<run-id>/rNNN`：某一轮尚未裁决的候选版本

每轮 worktree 只围绕一条 candidate branch 存在。

## 四、目录与状态落点

### 1. 脚本

放在：

- `toolchain/scripts/research/`

建议新增：

- `worktree_manager.py`
- `run_autoresearch.py`

### 2. 运行期状态

放在：

- `.autoworkflow/autoresearch/<run-id>/`

建议新增：

- `runtime.json`
- `rounds/round-001/round.json`
- `rounds/round-001/worktree.json`

## 五、worktree manager 的职责

`worktree_manager.py` 只做高副作用、确定性动作：

1. 初始化 `champion/<run-id>`
2. 从 champion HEAD 创建 candidate branch
3. 为 candidate branch 创建 worktree
4. 记录 base SHA 与 candidate SHA
5. round 结束后 promote 或 discard
6. 清理 candidate branch 与 worktree

它不做：

- prompt 改写
- score 判断
- mutation 生成
- 文本内容编辑

## 六、为什么这层不交给 Codex 主控

这层应该由脚本主控，原因很简单：

- git 生命周期必须幂等
- 失败恢复必须可预测
- 清理动作不能依赖模型临场判断
- worktree 状态必须能在下次运行时被脚本直接恢复

因此 P0.2 的控制边界是：

- 脚本负责 git / filesystem 生命周期
- Codex 不直接决定 branch / worktree 的生死

## 七、建议的最小状态机

每一轮至少有下面几个状态：

1. `prepared`
2. `candidate_active`
3. `evaluating`
4. `accepted`
5. `discarded`
6. `cleaned`

状态切换建议：

```text
prepared
  -> candidate_active
  -> evaluating
  -> accepted | discarded
  -> cleaned
```

约束：

- `accepted` 后 champion 才允许前进
- `discarded` 后 candidate branch 不进入下一轮
- `cleaned` 是终态，表示本轮 worktree 已经安全回收

## 八、建议的 round 初始化流程

P0.2 里，准备一轮的动作建议固定为：

1. 读取 `.autoworkflow/autoresearch/<run-id>/contract.json`
2. 读取当前 `runtime.json`
3. 找到 `champion/<run-id>` 的 HEAD 作为 `base_sha`
4. 创建 `candidate/<run-id>/rNNN`
5. 创建独立 candidate worktree
6. 写入 `round.json` 与 `worktree.json`

建议记录字段：

### `round.json`

- `round`
- `state`
- `base_sha`
- `candidate_branch`
- `candidate_worktree`

### `worktree.json`

- `path`
- `branch`
- `base_sha`
- `created_at`
- `cleaned_at`

## 九、promotion / discard 语义

### 1. promote

promote 不是 merge 任意 diff，而是明确执行：

- candidate 已完成评测
- decision 已经是 `keep`
- champion 指向 candidate commit

在 P0.2 阶段，不要求复杂 merge 策略；默认 candidate 来自 champion HEAD，只允许 fast-forward 语义。

### 2. discard

discard 不走 `git revert` 作为主路径，而是：

- 标记本轮为 `discarded`
- 删除 candidate worktree
- 删除 candidate branch

原因：

- 避免主实验线上堆积 revert 噪音
- 让失败候选成为运行记录，而不是长期 git 历史污染

## 十、失败恢复要求

P0.2 必须考虑中断恢复。

至少要支持：

- 进程中断后重新读取 `runtime.json`
- 识别遗留 candidate worktree
- 判断其状态是继续、放弃还是清理

因此脚本需要有一条明确原则：

- `.autoworkflow/autoresearch/<run-id>/` 才是 round runtime 的恢复入口
- 不是通过猜测 git 状态来“推断上次做到哪”

## 十一、控制边界：脚本 vs Codex

### 1. 脚本负责

- `git worktree add`
- `git worktree remove`
- candidate branch 创建与删除
- champion promote
- `runtime.json` 与 `worktree.json` 写入

### 2. Codex 负责

- 不负责 P0.2 的主控动作
- 最多只消费脚本准备好的 candidate worktree 路径

结论：

- P0.2 是“脚本强主控，Codex 只读运行上下文”

## 十二、验收标准

P0.2 完成后，应满足：

1. 当前用户工作树不被 round 污染
2. 每轮 candidate 都有明确 base SHA
3. discard 不需要 `git revert`
4. keep 后 champion 可前进到新的 accepted commit
5. 异常退出后可以恢复并清理残留 worktree

## 十三、后续关系

P0.2 完成后，P0.3 才能安全引入：

- round mutation
- Codex / subagent 进入 candidate worktree 改文件
- 基于 score 的 keep / discard

相关文档：

- [Autoresearch P0.1：合同与数据面](./autoresearch-p0-1-contract-and-data-plane.md)
- [Autoresearch P0.3：Baseline Loop 与 Round 执行](./autoresearch-p0-3-baseline-loop-and-round-execution.md)
