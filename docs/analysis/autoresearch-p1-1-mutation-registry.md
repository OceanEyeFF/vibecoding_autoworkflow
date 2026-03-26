---
title: "Autoresearch P1.1：Mutation Registry"
status: active
updated: 2026-03-26
owner: aw-kernel
last_verified: 2026-03-26
---
# Autoresearch P1.1：Mutation Registry

> 目的：把 mutation 从“一次性 round 文件”提升成“可被选择、可被记账、可被实例化”的稳定对象层。P1 的第一刀不是 scheduler，而是先固定系统“允许自动改什么”。

## 一、阶段定位

P1.1 只回答下面问题：

- registry 应该记录什么 mutation 对象
- registry 与 `contract.json`、`mutation.json`、`worker contract` 的依赖顺序是什么
- 哪些 mutation kind 适合第一版
- 哪些字段必须由脚本校验与持有

P1.1 不回答下面问题：

- feedback 如何压缩成新的 mutation 候选
- scheduler 如何做智能探索
- acceptance lane 是否参与每轮决策
- agent 内部是否再拆 proposer / critic / fixer 多角色

## 二、为什么它是硬前置

P0.3 已经能跑：

- `contract.json`
- baseline scoreboard
- worktree lifecycle
- 单轮 `mutation.json`
- 固定 keep / discard

但 P0.3 的 `mutation.json` 仍然是“本轮人工给定的执行 spec”，不是“系统长期维护的 mutation 对象”。

如果没有 registry，后面的 `worker contract` 与 selector 都会失去上游对象：

- `worker contract` 不知道自己是从哪一类 mutation 派生出来的
- selector 没有稳定的候选池可以选择
- 系统无法区分“同一类 mutation 再试一次”与“完全不同的新 mutation”
- fingerprint / dedup 没有持久记账位置

因此依赖顺序必须先固定为：

```text
contract.json
  -> mutation-registry.json
  -> rounds/round-NNN/mutation.json
  -> rounds/round-NNN/worker-contract.json
  -> minimal selector
```

这里的关键不是文件多少，而是 authority 顺序：

- `contract.json` 决定 run 的硬边界
- `mutation-registry.json` 决定 run 内有哪些合法 mutation 候选
- `mutation.json` 只是某个候选在单轮里的实例化
- `worker-contract.json` 只是 agent-facing 的执行信封

## 三、对象模型

### 1. 落点

建议固定三类对象：

- run 边界：
  - `.autoworkflow/autoresearch/<run-id>/contract.json`
- mutation 候选池：
  - `.autoworkflow/autoresearch/<run-id>/mutation-registry.json`
- 单轮实例：
  - `.autoworkflow/autoresearch/<run-id>/rounds/round-NNN/mutation.json`

建议同时补两类代码落点：

- schema：
  - `toolchain/evals/fixtures/schemas/autoresearch-mutation-registry.schema.json`
- loader / validator：
  - `toolchain/scripts/research/autoresearch_mutation_registry.py`

### 2. registry 顶层对象

`mutation-registry.json` 建议最小字段：

- `run_id`
- `registry_version`
- `contract_fingerprint`
- `entries`

含义：

- `run_id`：绑定当前 autoresearch run
- `registry_version`：防止后续字段演化时无版本边界
- `contract_fingerprint`：绑定生成 registry 时的 canonical contract；若 contract 变了，脚本必须拒绝继续消费旧 registry
- `entries`：本 run 可被选择的 mutation 候选

### 3. `MutationEntry` 最小对象

建议每个 entry 固定为下面几组：

- 身份
  - `mutation_key`
  - `kind`
  - `status`
- 作用域
  - `target_paths`
  - `allowed_actions`
- 语义
  - `instruction_seed`
  - `expected_effect`
- 约束
  - `guardrails`
- 去重
  - `fingerprint_basis`
  - `fingerprint`
- 来源与记账
  - `origin`
  - `attempts`
  - `last_selected_round`
  - `last_decision`

推荐最小形状：

```json
{
  "mutation_key": "text_rephrase:knowledge-base-skill:intro-tighten-v1",
  "kind": "text_rephrase",
  "status": "active",
  "target_paths": [
    "product/memory-side/adapters/agents/skills/knowledge-base-skill/SKILL.md"
  ],
  "allowed_actions": [
    "edit"
  ],
  "instruction_seed": "Tighten the opening guidance, reduce repetition, keep path and boundary rules explicit.",
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
  "guardrails": {
    "require_non_empty_diff": true,
    "max_files_touched": 1,
    "extra_frozen_paths": []
  },
  "fingerprint_basis": {
    "kind": "text_rephrase",
    "target_paths": [
      "product/memory-side/adapters/agents/skills/knowledge-base-skill/SKILL.md"
    ],
    "allowed_actions": [
      "edit"
    ],
    "instruction_seed": "Tighten the opening guidance, reduce repetition, keep path and boundary rules explicit."
  },
  "fingerprint": "sha256:...",
  "origin": {
    "type": "manual_seed",
    "ref": "docs/analysis/autoresearch-p1-1-mutation-registry.md"
  },
  "attempts": 0,
  "last_selected_round": null,
  "last_decision": null
}
```

## 四、哪些字段必须脚本可校验

P1.1 的原则应当是：

- 语义是否“好”可以留给 round 结果判断
- 边界是否合法必须在脚本层就能拒绝

### 1. 准备阶段就必须可校验的字段

- `mutation_key`
  - 非空、唯一、格式稳定
- `kind`
  - 必须来自受控枚举，不允许自由文本
- `target_paths`
  - 非空；必须落在 `contract.mutable_paths` 内；不得与 `contract.frozen_paths` 重叠
- `allowed_actions`
  - 必须来自受控集合；P1 第一版应收敛到 `["edit"]`
- `instruction_seed`
  - 非空字符串；P1 不引入模板 DSL
- `expected_effect.primary_metrics`
  - 必须是 scoreboard 已有的稳定字段
- `expected_effect.guard_metrics`
  - 必须是 contract 已声明的 guard 指标子集
- `guardrails.max_files_touched`
  - 必须是正整数
- `guardrails.extra_frozen_paths`
  - 必须是 `target_paths` 内部进一步收窄的子路径

### 2. 必须由脚本计算的字段

- `contract_fingerprint`
- `fingerprint`
- `attempts`
- `last_selected_round`
- `last_decision`
- `status` 的状态推进

这里的判断要钉死：

- `fingerprint` 不应由人工直接填写
- `attempts` 不应由 agent 回写
- `status` 不是 prompt 建议，而是脚本状态

### 3. 哪些字段只是解释，不是 keep 依据

- `expected_effect.hypothesis`

它的作用是：

- 帮助人和 agent 理解“为什么试这个 mutation”
- 为后续 feedback distillation 提供语义挂点

它不应直接把一个低分 round 解释成 keep。

## 五、如何表达 kind、scope、dedup 与 guardrails

### 1. `kind`

`kind` 在 P1 不应是开放字符串，而应是脚本可识别的 safety class。

建议第一版固定为少量枚举：

- `text_rephrase`
- `constraint_tighten`
- `instruction_reorder`
- `example_trim`

这些 kind 的共同特点：

- 默认只允许 `edit`
- 默认只触达已有文件
- 默认只做文本层局部修改
- 能被现有 diff 校验与 scoreboard 验证覆盖

### 2. `target_paths`

`target_paths` 表示 mutation 允许触达的 repo path 边界。

规则应固定为：

- entry 级 `target_paths` 必须是 `contract.mutable_paths` 的子集
- round 内实际 git diff 只能落在这些路径里
- `target_paths` 只能收窄，不能在 round materialization 时放大

### 3. `allowed_actions`

`allowed_actions` 是 diff 级约束，不是语义级说明。

P1 第一版应明确收窄为：

- `edit`

原因：

- `create / delete / rename / copy` 会立刻把工作从“局部文本变更”推向“结构变更”
- 这会连带扩大 fingerprint、selector 和 diff validation 的复杂度

### 4. `expected_effect`

建议固定为两层：

- `hypothesis`
- `primary_metrics` / `guard_metrics`

它的作用不是定义奖励函数，而是把 registry entry 与已有 scoreboard 语言对齐。

### 5. `fingerprint_basis` 与 `fingerprint`

P1 不需要语义级相似度去重，先做 canonical 字段去重即可。

建议脚本把下面字段 canonicalize 后求 hash：

- `kind`
- 归一化后的 `target_paths`
- 排序后的 `allowed_actions`
- 归一化后的 `instruction_seed`
- 归一化后的 `guardrails`

然后写出：

- `fingerprint_basis`
- `fingerprint`

这能先解决两个问题：

- 完全相同 mutation 不重复入池
- 同一 mutation 多轮尝试时有稳定 family identity

### 6. `guardrails`

P1 的 guardrails 不应设计成复杂 policy engine，只保留脚本可验证的局部约束。

建议第一版只保留：

- `require_non_empty_diff`
- `max_files_touched`
- `extra_frozen_paths`

不要在 P1 引入：

- 自定义正则检查器
- 文本级 AST 约束
- 多步前置条件

这些都不是当前主链的硬前置。

## 六、哪些 mutation kind 适合 P1 第一版

P1 第一版只适合“文本型、单表面、低副作用”的 mutation。

建议优先准入：

- `text_rephrase`
  - 对现有 prompt / skill / instruction 文本做同路径重写
- `constraint_tighten`
  - 对已有规则文本做更明确、更收敛的约束表达
- `instruction_reorder`
  - 在单文件内重排已有指令顺序
- `example_trim`
  - 删除冗余示例、压缩过长示例、保留主规则

这些 kind 适合第一版，不是因为它们“更高级”，而是因为它们满足：

- diff 可解释
- scope 易校验
- worktree 验证成本低
- 与当前 research runner 的得分变化有直接关系

## 七、哪些 mutation kind 应明确延后

应明确排到 P1 之后的包括：

- `file_create`
- `file_delete`
- `path_rename`
- `cross_file_refactor`
- `adapter_code_change`
- `suite_change`
- `metric_change`
- `contract_change`
- `registry_change`
- `multi_target_bundle`

延后的原因不是它们永远不做，而是它们会立刻放大下面成本：

- diff authority 变宽
- fingerprint 语义变复杂
- keep / discard 归因变混乱
- worker contract 不再是单轮局部编辑信封

P1 若一开始就允许这些 kind，主链会直接从“稳定对象层”跳成“半个 orchestrator”。

## 八、registry 与其他对象的依赖关系

### 1. 与 `contract.json` 的关系

`contract.json` 是上游硬边界；registry 只能在它内部做供给定义。

准确关系应是：

- contract 决定 run 的可变 surface、suite lane、metrics 与预算
- registry 决定在这个 run 里有哪些候选 mutation family

registry 不能做的事：

- 扩大 `mutable_paths`
- 发明新的 scoreboard 指标
- 改写 keep / discard 规则

### 2. 与每轮 `mutation.json` 的关系

`mutation.json` 不是 registry 的替代品，而是 registry entry 的单轮实例化结果。

也就是说：

- registry 记录“有哪些 mutation family”
- `mutation.json` 记录“本轮到底执行哪一个 family 的第几次尝试”

因此 round `mutation.json` 至少应比 P0.3 多出：

- `mutation_key`
- `attempt`
- `fingerprint`

而 `round`、`instruction`、`expected_effect` 这类字段则保留单轮执行视角。

### 3. 与 `worker contract` 的关系

`worker contract` 必须建立在 registry entry 已经被选中且实例化之后。

依赖顺序不能反过来：

- registry 先定义 mutation 的合法边界
- round `mutation.json` 再把它 materialize 成本轮 spec
- `worker contract` 最后才把本轮 spec 包装成 agent-facing 执行合同

没有 registry 时，`worker contract` 只是空信封，因为它没有稳定上游对象可以引用。

### 4. 哪些内容属于 registry 定义

应在 registry 固定的内容：

- `mutation_key`
- `kind`
- `target_paths`
- `allowed_actions`
- `instruction_seed`
- `expected_effect`
- `guardrails`
- `fingerprint`

### 5. 哪些内容属于单轮实例化

应到 round materialization 时才填入的内容：

- `round`
- `attempt`
- `mutation_id`
- `base_sha`
- `candidate_branch`
- `candidate_worktree`
- 本轮要提供给 worker 的上下文摘要

这层区分的作用是：

- registry 稳定承载 mutation family
- round 文件只承载本轮 runtime

## 九、为什么它必须早于 worker contract 与 scheduler

### 1. 早于 worker contract

因为 worker contract 只回答“这轮怎么做”，不回答“为什么轮到这个 mutation 被做”。

如果没有 registry：

- worker contract 无法引用稳定的 `mutation_key`
- agent 输出无法回写到 family 级历史
- 同类 mutation 的二次尝试没有归档位置

### 2. 早于 scheduler

因为 scheduler 的最小输入不是 prompt，而是“候选对象集合”。

如果没有 registry：

- selector 只能在临时 JSON 文件之间做调度
- dedup 只能靠 prompt 文本相等这种脆弱信号
- exhausted / disabled / retry 这些状态无处安放

所以真正的最小 selector 前置条件不是“更聪明的策略”，而是“先有稳定候选池”。

## 十、控制边界

### 1. 必须由脚本控制的部分

- registry schema 校验
- registry 与 contract 的边界校验
- `fingerprint` 计算
- `status / attempts / last_decision` 回写
- 从 registry entry materialize round `mutation.json`
- 从 round `mutation.json` 生成 `worker-contract.json`
- round 结束后的 diff 校验与 scope 校验

### 2. 由 Codex / subagent 消费即可的部分

- `worker-contract.json`
- 只读的 `mutation.json`
- candidate worktree 路径
- scoreboard 摘要与上一轮反馈摘录

Codex / subagent 的职责仍然只应是：

- 在允许路径内做内容改动
- 写 `agent-report.md`

### 3. 不能交给 Codex 主控的部分

- registry 增删改主控
- `target_paths` 放宽
- `allowed_actions` 放宽
- keep / discard 裁决
- worktree lifecycle
- `attempts` 与 `status` 记账

### 4. 如何防止通过 round 文件越权

不能只靠 prompt 约束，应叠加下面几层：

- `mutation.json` 与 `worker-contract.json` 都由脚本写出，不由 agent 回写
- `prepare-round` 时把 materialized `mutation.json` 的 hash 写入 `round.json`
- `run-round` 前重新校验：
  - `mutation.json` 未漂移
  - 它仍然能追溯到同一个 `mutation_key`
  - 它仍然满足 contract 边界
- 最终以 candidate worktree 的实际 git diff 为准，再做一次 `target_paths + allowed_actions + frozen_paths` 校验

结论：

- round 文件可以被读取，但不能成为 authority 来源
- authority 始终在脚本可重算的 registry + contract + git diff 上

## 十一、最小落地路径

### 1. 子阶段 A：冻结文档与对象边界

只写 `docs/analysis/`：

- 固定 `mutation-registry.json` 的对象模型
- 固定 P1 允许的 kind 白名单
- 固定 registry / mutation / worker contract 的依赖顺序

验收信号：

- 对 `mutation_key`、`fingerprint`、`attempts` 的 owner 没有歧义
- 不再把 selector 或 scheduler 当成 P1 起点

### 2. 子阶段 B：实现 registry schema + loader

进入 `toolchain/`：

- 新增 `autoresearch-mutation-registry.schema.json`
- 新增 `autoresearch_mutation_registry.py`
- 实现 `load / validate / canonicalize / fingerprint`

验收信号：

- 能加载一个 run-local registry
- 能拒绝越界 `target_paths`
- 能拒绝不支持的 `kind` 与 `allowed_actions`
- 能稳定算出 `fingerprint`

### 3. 子阶段 C：把 `prepare-round` 改成“从 registry 实例化”

进入 `toolchain/scripts/research/`：

- `prepare-round` 不再只吃人工 `--mutation`
- 至少支持：
  - `--mutation-key <key>`
  - 或先兼容 `--mutation`，但内部先 import/canonicalize 成 registry entry
- round `mutation.json` 增加：
  - `mutation_key`
  - `attempt`
  - `fingerprint`

验收信号：

- 一轮 round 可以从 registry entry 启动
- 同一 entry 的第二次尝试能正确递增 `attempts`
- 无法通过手改 round 文件扩大 scope

### 4. 子阶段 D：生成 `worker-contract.json`

进入 `toolchain/scripts/research/`：

- `prepare-round` 结束时同时写出 `worker-contract.json`
- agent 执行入口切换成消费 worker contract

验收信号：

- Codex / subagent 不需要直接理解 registry 状态机
- `worker-contract.json` 足以独立指导单轮内容工作

### 5. 子阶段 E：补最小 deterministic selector

进入 `toolchain/scripts/research/`：

- 只做 deterministic 选择，不做智能调度
- 只需要利用：
  - `status`
  - `attempts`
  - `fingerprint`
  - 固定优先级

验收信号：

- 系统能在不手写本轮 `mutation.json` 的情况下自动挑出下一项
- exhausted / disabled entry 不再被继续选中

### 6. 实现后回归命令索引（P1.1）

建议固定成三段执行，避免只测单点模块：

- 静态检查：

```bash
python3 -m py_compile \
  toolchain/scripts/research/run_autoresearch.py \
  toolchain/scripts/research/autoresearch_mutation_registry.py \
  toolchain/scripts/research/autoresearch_worker_contract.py \
  toolchain/scripts/research/autoresearch_selector.py \
  toolchain/scripts/research/test_autoresearch_mutation_registry.py \
  toolchain/scripts/research/test_autoresearch_worker_contract.py \
  toolchain/scripts/research/test_autoresearch_selector.py \
  toolchain/scripts/research/test_autoresearch_round.py \
  toolchain/scripts/research/test_run_autoresearch.py \
  toolchain/scripts/research/test_autoresearch_p1_1_smoke.py
```

- 白盒测试：

```bash
python3 -m unittest \
  toolchain/scripts/research/test_autoresearch_mutation_registry.py \
  toolchain/scripts/research/test_autoresearch_worker_contract.py \
  toolchain/scripts/research/test_autoresearch_selector.py \
  toolchain/scripts/research/test_autoresearch_round.py \
  toolchain/scripts/research/test_run_autoresearch.py \
  toolchain/scripts/research/test_autoresearch_p1_1_smoke.py
```

- smoke 测试必须覆盖：
  - `init -> baseline -> prepare-round(auto select) -> run-round -> decide-round`
  - `prepare-round --mutation-key` 显式覆盖
  - all-unselectable 的 prepare 失败语义
  - tamper `worker-contract.json` 后 `run-round` 失败语义

## 十二、哪些阶段先不要碰

P1.1 到 P1.2 之间，先不要碰下面这些面：

- feedback distillation
- adaptive scheduler
- keep / discard 规则重写
- acceptance lane 调度策略
- worktree lifecycle 改模
- research runner / judge contract 重做
- 允许 `create / delete / rename / copy`

原因很直接：

- 这些都不是当前主链阻塞
- 现在先做，只会把 registry 设计反过来绑到下游复杂度上

## 十三、结论

P1 的真正起点不是“自动想出更多 mutation”，而是先把 mutation 定义成稳定对象。

只要这一步没做，后面的：

- `worker contract`
- minimal selector
- feedback distillation
- adaptive scheduler

都会建立在一次性 round 文件之上，系统仍然停留在“人工 round 的脚本化”，还没有进入真正可迭代的 autoresearch。

相关文档：

- [Autoresearch P0.1：合同与数据面](./autoresearch-p0-1-contract-and-data-plane.md)
- [Autoresearch P0.2：Worktree 控制壳](./autoresearch-p0-2-worktree-control-shell.md)
- [Autoresearch P0.3：Baseline Loop 与 Round 执行](./autoresearch-p0-3-baseline-loop-and-round-execution.md)
- [Research 评测契约与边界](./research-eval-contracts.md)
- [Research 评测观测与输出规范](./research-eval-observability.md)
