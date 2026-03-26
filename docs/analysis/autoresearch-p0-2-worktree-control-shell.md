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

## 十四、当前代码落地情况

下面内容描述的是当前仓库已经落地的 P0.2 实现，不再是建议形态。

### 1. 当前 CLI 入口

P0.2 当前实际由 `toolchain/scripts/research/run_autoresearch.py` 暴露下面几个入口：

- `init --contract <contract.json>`
- `prepare-round --contract <contract.json> --mutation <mutation.json>`
- `promote-round --contract <contract.json>`
- `discard-round --contract <contract.json>`
- `cleanup-round --contract <contract.json>`

说明：

- `prepare-round` 在当前主入口上已经带有 `--mutation` 参数，这是因为主脚本现在同时承载 P0.3 入口
- 但 P0.2 自身负责的仍然只是 worktree 生命周期，不负责 mutation 执行、round 评测或 keep / discard 打分
- `run-round` 与 `decide-round` 属于后续层的入口，不应当反向写成 P0.2 已覆盖的职责

### 2. 当前命名与路径

当前代码已经固定为：

- champion branch：`champion/<run-id>`
- candidate branch：`candidate/<run-id>/rNNN`
- round 目录：`.autoworkflow/autoresearch/<run-id>/rounds/round-NNN/`
- candidate worktree 目录：`.autoworkflow/autoresearch/<run-id>/worktrees/round-NNN/`

当前运行期状态文件为：

- `.autoworkflow/autoresearch/<run-id>/runtime.json`
- `.autoworkflow/autoresearch/<run-id>/rounds/round-NNN/round.json`
- `.autoworkflow/autoresearch/<run-id>/rounds/round-NNN/worktree.json`

其中当前代码实际会维护的关键字段包括：

- `runtime.json`：`run_id`、`champion_branch`、`champion_sha`、`active_round`、`active_candidate_branch`、`active_candidate_worktree`
- `round.json`：`round`、`state`、`base_sha`、`candidate_branch`、`candidate_worktree`、`candidate_sha`、`decision`
- `worktree.json`：`path`、`branch`、`base_sha`、`candidate_sha`、`created_at`、`cleaned_at`

## 十五、当前语义已经固定的动作

### 1. prepare-round

当前代码语义是：

1. 读取或初始化 `runtime.json`
2. 确保 `champion/<run-id>` 存在，并把它的 HEAD 作为 `base_sha`
3. 若已有 `active_round`，直接拒绝创建第二个 candidate
4. 先写 `round.json` 和 `worktree.json` 的恢复骨架
5. 再执行 `git worktree add -b candidate/<run-id>/rNNN ...`
6. worktree 创建成功后回填 `candidate_sha`，并把 round 状态推进到 `candidate_active`

这里的关键实现约束是：

- 不切换用户当前工作树
- candidate 一轮只允许一个
- 失败恢复依赖状态文件，而不是重新猜测 git 现场

### 2. promote-round

当前代码不是做通用 merge，而是：

- 只接受 fast-forward 语义
- 先检查 `champion/<run-id>` 是否是 candidate 的祖先
- 通过后用 `update-ref` 把 champion 前进到 candidate commit
- 然后统一走清理逻辑，删除 candidate branch 和 worktree

如果 candidate 已经与 champion 分叉，当前实现会直接报错，不会擅自做 merge。

### 3. discard-round

当前代码语义是：

- 将 round 标记为 `discard`
- 不执行 `git revert`
- 直接删除 candidate worktree
- 直接删除 candidate branch
- 将 round 最终状态推进为 `cleaned`

这与文档原始目标一致：失败候选只作为 runtime 记录保留，不进入长期 git 历史。

### 4. cleanup-round

`cleanup-round` 的定位是恢复与回收，而不是裁决：

- 它只要求当前存在 `active_round`
- 不要求 candidate 已评测或已裁决
- 会按记录的路径和分支尝试移除 worktree / branch
- 最后清空 `runtime.json` 里的 active 字段，并把 round 标记为 `cleaned`

## 十六、恢复入口与中断语义

当前代码已经把下面原则落地：

- `runtime.json` 是恢复入口
- `round.json` 与 `worktree.json` 是 round 级补充状态
- 脚本不会通过扫描 git 现场来推断上次做到哪里

这层目前最重要的恢复语义是：

- `prepare-round` 在 `git worktree add` 之前就会先写入 `round.json` 与 `worktree.json`
- 如果进程在 `git worktree add` 阶段失败，中断后仍然能从 `runtime.json + round.json + worktree.json` 找回 active round
- 如果 `worktree.json` 缺失，当前实现也会优先根据 `runtime.json` 和 `round.json` 重建一个最小可清理记录
- 因此 `cleanup-round` / `discard-round` 可以回收“worktree 尚未真正创建成功”这一类半完成状态

换句话说，当前恢复路径的真相层是 `.autoworkflow/autoresearch/<run-id>/`，而不是 git worktree 列表本身。

## 十七、当前已验证范围

当前仓库里的白盒测试已经覆盖下面范围，而且测试均在临时 git repo 中执行，不污染当前仓库：

- `prepare-round` 会创建 champion branch、candidate branch、candidate worktree 和状态文件
- 存在 `active_round` 时会拒绝再开第二个 candidate
- `promote-round` 能 fast-forward 推进 champion，并在完成后清理 candidate
- 非 fast-forward candidate 会被拒绝 promote
- `discard-round` 不产生 revert 噪音，且不会污染当前主工作树
- `cleanup-round` 能回收脏 candidate worktree
- `git worktree add` 中断后，仍可通过 `cleanup-round` 恢复并清理残留状态
- CLI 层至少覆盖了 `init -> prepare-round -> discard-round` 的最小链路

## 十八、当前未承诺事项

当前 P0.2 文档不应反向承诺下面能力：

- mutation 生成
- candidate worktree 内的内容编辑
- `run-round`
- `decide-round`
- 基于 score 的 keep / discard 规则
- acceptance suite 每轮执行

这些能力即使已经出现在同一个脚本入口里，也属于后续层，不应被解释为 P0.2 自身职责。

相关文档：

- [Autoresearch P0.1：合同与数据面](./autoresearch-p0-1-contract-and-data-plane.md)
- [Autoresearch P0.3：Baseline Loop 与 Round 执行](./autoresearch-p0-3-baseline-loop-and-round-execution.md)
