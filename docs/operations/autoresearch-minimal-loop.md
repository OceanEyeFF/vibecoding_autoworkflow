---
title: "Autoresearch 最小闭环运行说明"
status: active
updated: 2026-03-27
owner: aw-kernel
last_verified: 2026-03-27
---
# Autoresearch 最小闭环运行说明

> 目的：把当前仓库里已经实际跑通的一轮 `autoresearch` 最小闭环固定成 repo-local runbook，说明最小输入、执行顺序、产物位置和已验证过的坑点。

## 一、适用范围

本页只覆盖当前仓库的最小 `autoresearch` 闭环：

- 单个 repo
- 单个 skill
- `train / validation` 两条 lane
- 一次 `init -> baseline -> prepare-round -> run-round -> decide-round`

它不覆盖：

- 多 skill suite
- acceptance matrix
- 自动 mutation 搜索
- planner / proposer / critic 多角色实验

## 二、已验证的最小组合

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

此时会得到：

- candidate branch
- candidate worktree
- `rounds/round-001/mutation.json`
- `rounds/round-001/worker-contract.json`
- `rounds/round-001/agent-report.md` 的目标路径

接着在 candidate worktree 内完成允许的改动，并写 `agent-report.md`。

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

## 五、这次实跑确认的两个坑

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

如果此时又把整个 `product/` 放进 `frozen_paths`，就会被直接拒绝，报：

```text
mutable_paths and frozen_paths overlap
```

因此当前仓库跑 wrapper surface 的最小 round 时，建议直接写 canonical path：

```text
product/memory-side/adapters/claude/skills/context-routing-skill/SKILL.md
```

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
- [Research 评测观测与输出规范](../analysis/research-eval-observability.md)
