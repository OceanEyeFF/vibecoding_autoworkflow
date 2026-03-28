---
title: "Autoresearch 最小闭环运行说明"
status: active
updated: 2026-03-28
owner: aw-kernel
last_verified: 2026-03-28
---
# Autoresearch 最小闭环运行说明

> 目的：把当前仓库里已经实际跑通的一轮 `autoresearch` 最小闭环固定成 repo-local runbook，说明最小输入、执行顺序、产物位置和已验证过的坑点。

## 一、适用范围

本页只覆盖当前仓库的最小 `autoresearch` 闭环：

- 单个 repo
- 单个 skill
- `train / validation` 两条 lane
- 一次 `init -> baseline -> prepare-round -> run-round -> decide-round`
- 单 prompt 的轻量 P2 profile 仅限单个 research prompt 文本

它不覆盖：

- 多 skill suite
- acceptance matrix
- 自动 mutation 搜索
- planner / proposer / critic 多角色实验
- prompt 文本之外的参数搜索

## 二、已验证的最小组合

当前文档包含两类已验证事实：

### 1. 实跑过的一轮最小闭环

`2026-03-27` 已在当前仓库实际跑过下面这组最小闭环：

- target repo：`typer`
- task：`context-routing`
- skill backend：`claude`
- judge backend：`claude`
- mutation 输入：`prepare-round --mutation <manual-mutation.json>`

这轮运行的结果是：

- baseline 可完成
- round 可完成
- fixed rule 正常做出 `discard`

说明当前代码层面的闭环已经成立，即使 round 最终没有被 `keep`。

### 2. `2026-03-28` Batch 1 到 Batch 3 代码与 smoke 验收已确认的 P2 轻量边界

这一轮不是新的 live backend 观测，而是针对已落地代码与 deterministic smoke 的验收事实：

- 只允许微调一个 research prompt 文件
- 只允许 `codex -> codex`
- 只允许四个固定 target task 之一：
  - `context-routing-skill`
  - `knowledge-base-skill`
  - `task-contract-skill`
  - `writeback-cleanup-skill`
- contract 需要同时声明：
  - `target_task`
  - `target_prompt_path`
- `mutable_paths` 必须精确收紧到 `[target_prompt_path]`
- `init / baseline / prepare-round / run-round` 会做 P2 preflight
- `decide-round` 不做无条件 CLI preflight，但如果命中 replay 条件，会在 replay 前复用同一套 P2 preflight
- `promote-round` 会做 P2 preflight
- `discard-round / cleanup-round` 不做 suite 级 preflight
- 独立的 P2 deterministic smoke 已固定在 `toolchain/scripts/research/test_autoresearch_p2_smoke.py`。注意当前 smoke 是 orchestration smoke：lane 执行使用 mock runner，只覆盖 CLI 编排与 decision/replay 产物面
- `test_run_autoresearch.py` 已覆盖 family-stop 先于 selector 空集报错、`decide-round` 的 no-replay 边界，以及 `promote-round` 的 P2 guard
- `test_autoresearch_round.py` 已覆盖 replay-needed 分支的 `provisional_decision` 与 `replay.*` 输出面

这组事实当前的主线承接位置是：

- `docs/operations/autoresearch-minimal-loop.md`
- `toolchain/scripts/research/README.md`

而 `docs/analysis/autoresearch-p2-lightweight-single-prompt-codex-loop.md` 继续只保留设计背景和收窄理由。

## 三、最小输入

最小闭环至少需要四个输入对象：

1. `contract.json`
2. `train.yaml`
3. `validation.yaml`
4. `manual-mutation.json` 或 run-local `mutation-registry.json`

最小 `contract.json` 示例：

```json
{
  "run_id": "manual-cr-typer-claude",
  "label": "Minimal Context Routing x Typer x Claude",
  "objective": "Run one minimal autoresearch loop against typer with the context-routing skill on the Claude adapter surface.",
  "target_surface": "claude context-routing adapter",
  "mutable_paths": [
    "product/memory-side/adapters/claude/skills/context-routing-skill/SKILL.md"
  ],
  "frozen_paths": [
    "docs",
    "toolchain",
    ".agents"
  ],
  "train_suites": ["train.yaml"],
  "validation_suites": ["validation.yaml"],
  "acceptance_suites": ["acceptance.yaml"],
  "primary_metrics": ["avg_total_score"],
  "guard_metrics": ["parse_error_rate", "timeout_rate"],
  "qualitative_veto_checks": [],
  "max_rounds": 1,
  "max_candidate_attempts_per_round": 1,
  "timeout_policy": { "seconds": 900 },
  "promotion_policy": { "mode": "manual" }
}
```

其中 `run_id` 在手动单轮场景里应被视为 **base run_id**，不要长期复用同一个已经跑过的真实 run id。

实际运行前，先用下面这个本地工具把 contract 刷成 fresh run id：

```bash
python3 toolchain/scripts/research/refresh_manual_run_contract.py \
  --contract /abs/path/to/contract.json
```

状态文件落点当前规则是：

- contract 在仓库内时，写到 `.autoworkflow/manual-runs/.run-id-state/<contract-parent>/`
- contract 在仓库外时，回退到 contract 同级 `.run-id-state/`

当前工具会把 `run_id` 刷成：

- `<base>-r<serial>-m<residue>`
- `serial` 单调递增，负责 freshness
- `residue` 按 `mod 100003` 生成，负责 lineage 辅助标记

如果跳过这一步而直接复用旧 `run_id`，最常见的失败是：

- 旧的 `history.tsv` / `mutation-registry.json` / `feedback-ledger.jsonl` 污染新一轮
- `prepare-round` 直接因为 `max_rounds` 或 attempts 已耗尽而失败

最小 `train.yaml` / `validation.yaml` 示例：

```yaml
version: 1
defaults:
  backend: claude
  judge_backend: claude
  with_eval: true
runs:
  - repo: /abs/path/to/.exrepos/typer
    task: context-routing
```

最小 `manual-mutation.json` 示例：

```json
{
  "mutation_id": "cr-wrapper-tighten-v1",
  "kind": "text_rephrase",
  "target_paths": [
    "product/memory-side/adapters/claude/skills/context-routing-skill/SKILL.md"
  ],
  "allowed_actions": ["edit"],
  "instruction": "Tighten the repo-adapter wording in the Claude context-routing skill wrapper while preserving the canonical-source order and the output contract.",
  "expected_effect": "Keep routing behavior stable while reducing redundant wrapper wording."
}
```

### Batch 1 单 Prompt Codex profile 的额外输入约束

如果当前 run 采用 Batch 1 的轻量 P2 profile，contract 还需要额外满足：

- `target_task` 和 `target_prompt_path` 必须同时存在
- `mutable_paths` 必须只包含这个 prompt 文件
- `target_prompt_path` 必须命中固定 task/path 映射，不能自定义漂移

最小 P2 形态示例：

```json
{
  "run_id": "manual-cr-p2-codex",
  "label": "Minimal P2 Context Routing x Codex",
  "objective": "Tune exactly one research prompt file with codex as both runner and judge.",
  "target_surface": "research prompt",
  "target_task": "context-routing-skill",
  "target_prompt_path": "toolchain/scripts/research/tasks/context-routing-skill-prompt.md",
  "mutable_paths": [
    "toolchain/scripts/research/tasks/context-routing-skill-prompt.md"
  ],
  "frozen_paths": [
    "docs",
    "product",
    ".agents"
  ],
  "train_suites": ["train.yaml"],
  "validation_suites": ["validation.yaml"],
  "acceptance_suites": ["acceptance.yaml"],
  "primary_metrics": ["avg_total_score"],
  "guard_metrics": ["parse_error_rate", "timeout_rate"],
  "qualitative_veto_checks": [],
  "max_rounds": 1,
  "max_candidate_attempts_per_round": 1,
  "timeout_policy": { "seconds": 900 },
  "promotion_policy": { "mode": "manual" }
}
```

Batch 1 的 suite 也要额外满足：

- 每个 run 只能覆盖 contract 指定的单个 task
- `backend` 必须是 `codex`
- `judge_backend` 必须是 `codex`
- `prompt_file` 若显式写出，必须解析到 `target_prompt_path`

推荐最小 suite 形态：

```yaml
version: 1
defaults:
  backend: codex
  judge_backend: codex
  with_eval: true
runs:
  - repo: /abs/path/to/.exrepos/typer
    task: context-routing
    prompt_file: /abs/path/to/repo/toolchain/scripts/research/tasks/context-routing-skill-prompt.md
```

## 四、推荐执行顺序

先刷新 contract 的 fresh `run_id`：

```bash
python3 toolchain/scripts/research/refresh_manual_run_contract.py \
  --contract /abs/path/to/contract.json
```

然后再执行：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  init \
  --contract /abs/path/to/contract.json
```

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  baseline \
  --contract /abs/path/to/contract.json
```

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  prepare-round \
  --contract /abs/path/to/contract.json \
  --mutation /abs/path/to/manual-mutation.json
```

如果 `prepare-round` 因中途中断留下 active round，再次执行 `prepare-round` 时当前脚本会先尝试按 frozen round authority 修复 `mutation.json` / `worker-contract.json`，并对账 `mutation-registry.json` 的 bookkeeping；如果 `runtime.json` 缺失也会先重建。但如果 `mutation-registry.json` 已缺失，当前实现会直接 fail closed，不会有损重建 registry。此时应继续当前 round，或显式执行：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  cleanup-round \
  --contract /abs/path/to/contract.json
```

此时会得到：

- candidate branch
- candidate worktree
- `rounds/round-001/mutation.json`
- `rounds/round-001/worker-contract.json`
- `rounds/round-001/agent-report.md` 的目标路径

接着在 candidate worktree 内完成允许的改动，并写 `agent-report.md`。

如果当前 run 采用 P2 单 Prompt profile，`prepare-round` 在创建新 candidate 之前还会先做 stop gate。当前已落地的 stop gate 只有两条：

- 连续 `3` 轮已完成 round 都没有产生新的 validation champion，则直接停止创建新 round
- 所有 `active` mutation family 都至少尝试过 `1` 次，且当前 run 还没有任何最终 `keep`，则直接停止创建新 round

然后执行：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  run-round \
  --contract /abs/path/to/contract.json
```

最后执行：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  decide-round \
  --contract /abs/path/to/contract.json
```

如果当前 contract 带有 `target_task` / `target_prompt_path`，要注意命令分层：

- 会执行 P2 preflight：
  - `init`
  - `baseline`
  - `prepare-round`
  - `run-round`
- 不会做无条件 CLI P2 preflight：
  - `decide-round`
- 会做 P2 preflight：
  - `promote-round`
- 不会执行 P2 preflight：
  - `discard-round`
  - `cleanup-round`

补充说明：

- `decide-round` 只有在“本轮 provisional keep 且 validation 严格高于当前 champion validation”时才会进入 replay
- replay 真正执行前会复用同一套 P2 preflight；如果 preflight 失败，本轮最终会停在错误而不是盲目 replay
- `promote-round` 当前是显式受 P2 preflight 保护的收尾命令
- `discard-round / cleanup-round` 仍保留为 recovery/post-eval 命令，不会因为 suite 漂移而卡死

当前 deterministic 验收命令可以直接用下面两组：

```bash
python3 -m py_compile \
  toolchain/scripts/research/test_autoresearch_p2_smoke.py \
  toolchain/scripts/research/test_run_autoresearch.py \
  toolchain/scripts/research/test_autoresearch_round.py
```

```bash
python3 -m unittest \
  toolchain/scripts/research/test_autoresearch_p2_smoke.py \
  toolchain/scripts/research/test_run_autoresearch.py \
  toolchain/scripts/research/test_autoresearch_round.py \
  toolchain/scripts/research/test_autoresearch_p1_3_smoke.py
```

当前命令口径代表的是：

- P2 单 Prompt、`codex -> codex` 主路径可以用 deterministic smoke 证明
- legacy P1.3 smoke 仍保持独立存在，没有被 P2 夹具吞并
- 这不是 live Codex acceptance matrix；高成本 live 验收仍属于单独系统级验证

## 五、这次实跑确认的三个坑

### 1. suite 里的 `repo` 要写绝对路径

在主工作树中，`run_skill_suite.py --repo typer` 可以通过 `.exrepos/typer` 正常解析。

但 `run-round` 是在 candidate worktree 内再调用一次 `run_skill_suite.py --suite ...`。如果 suite manifest 里写的是：

```yaml
runs:
  - repo: typer
```

candidate worktree 下通常没有 `.exrepos/typer`，会直接失败：

```text
Repository not found: typer
```

因此当前最稳妥的写法是：

```yaml
runs:
  - repo: /abs/path/to/.exrepos/typer
```

### 2. `mutable_paths` / `target_paths` 要写 canonical path，不要写 deploy target alias

这次实跑里，原本尝试把可变路径写成：

```text
.claude/skills/context-routing-skill/SKILL.md
```

但当前 contract / registry 路径校验会把路径归一化到仓库真实路径，最终落到：

```text
product/memory-side/adapters/claude/skills/context-routing-skill/SKILL.md
```

另外，当前 `target_paths` 校验已经是严格子集语义：

- `contract.mutable_paths = product/.../skills` 时，`target_paths = product/.../skills/skill.md` 可以通过
- 但把 `target_paths` 放宽成更大的父路径会被拒绝

如果此时又把整个 `product/` 放进 `frozen_paths`，就会被直接拒绝，报：

```text
mutable_paths and frozen_paths overlap
```

因此当前仓库跑 wrapper surface 的最小 round 时，建议直接写 canonical path：

```text
product/memory-side/adapters/claude/skills/context-routing-skill/SKILL.md
```

### 3. Batch 1 的单 Prompt P2 profile 不是自由组合

如果 contract 进入了 Batch 1 的 P2 profile，当前实现不是“任意 task + 任意 prompt_file”的宽松模式，而是固定约束：

- `target_task` 只能是四个已登记的 skill
- `target_prompt_path` 必须精确匹配固定映射
- `mutable_paths` 必须只剩这个 prompt 文件
- suite 必须是单 task 且 `codex -> codex`

只要其中一项不满足，`init / baseline / prepare-round / run-round` 就会直接失败。

## 六、一轮流程会产出什么

run 根目录固定在：

```text
.autoworkflow/autoresearch/<run-id>/
```

最小闭环后至少会有：

- `contract.json`
- `runtime.json`
- `history.tsv`
- `scoreboard.json`
- `mutation-registry.json`
- `feedback-ledger.jsonl`

当前仓库的 smoke 覆盖还额外证明了一条最小 adaptive 路径：

- 有既有 ledger 时，positive family 可以在第二轮优先于 fresh entry 被再次选择
- 带 `validation_drop` 的 mixed family 会被 guardrail 降权，fresh family 会优先被选择

单轮 `rounds/round-001/` 下至少会有：

- `round.json`
- `worktree.json`
- `mutation.json`
- `worker-contract.json`
- `agent-report.md`
- `train/`
- `validation/`
- `scoreboard.json`
- `decision.json`
- `feedback-distill.json`
- `replay/scoreboard.json`（仅当 round 先命中 provisional `keep` 且触发 replay 时生成）

`train/` 和 `validation/` 下还会继续落 runner artifact：

- `*.prompt.txt`
- `*.response.md`
- `*.final.txt`
- `*.raw.stdout.txt`
- `*.meta.json`
- `*.structured.json`
- `run-summary.json`

## 七、如何判断这一轮算“跑通”

最小闭环的“跑通”标准不是必须 `keep`，而是下面这些都成立：

1. `baseline` 成功写出顶层 `scoreboard.json`
2. `prepare-round` 成功写出 `mutation.json` 和 `worker-contract.json`
3. `run-round` 成功写出 round 级 `scoreboard.json`
4. `decide-round` 成功写出 `decision.json` 和 `feedback-distill.json`
5. `runtime.json.active_round` 回到 `null`

如果当前 round 触发 replay，还应额外满足：

6. `rounds/round-NNN/replay/scoreboard.json` 已写出
7. 只有当 replay validation 不低于本轮 round validation 时，最终 `decision.json` 才会保持 `keep`

也就是说：

- `keep` 是“优化成功”
- `discard` 仍然是“闭环成功”

## 八、这次验证到的真实结果

这次 `manual-cr-typer-claude` run 的 baseline 和 round 对比如下：

- baseline train：`11`
- baseline validation：`12`
- round train：`12`
- round validation：`9`

因此最终 `decision.json` 中：

- `train_score_improved = true`
- `validation_score_non_regression = false`
- 最终决策：`discard`

这个结果说明 fixed rule 正常工作，也说明最小闭环已经能真实区分“train 改善但 validation 退化”的 round。

## 九、相关文档

- [Research CLI 指令](./research-cli-help.md)
- [toolchain/scripts/research/README.md](../../toolchain/scripts/research/README.md)
- [Autoresearch P2：单 Prompt、Codex-only 轻量迭代方案](../analysis/autoresearch-p2-lightweight-single-prompt-codex-loop.md)
- [Autoresearch P2：单 Prompt、Codex-only 轻量迭代任务规划](../analysis/autoresearch-p2-lightweight-single-prompt-codex-task-plan.md)
- [Research 评测观测与输出规范](../analysis/research-eval-observability.md)
