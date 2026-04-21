---
title: "Codex Harness Manual Runbook"
status: active
updated: 2026-04-22
owner: aw-kernel
last_verified: 2026-04-22
---
# Codex Harness Manual Runbook

> 目的：固定一条最小手动工作流，在 `tmp` 目录下初始化临时测试 repo，用无交互 `Codex` 连续调用 `harness-skill` 推进固定题目，并由当前环境下的 `Codex` 直接监督每轮真实执行内容。

本页属于 [Deploy Runbooks](./README.md) 系列文档。

## 一、适用范围

本页只回答：

- 如何在 `tmp` 下初始化临时测试 repo
- 如何用通用 deploy / scaffold 脚本准备最小运行面
- 如何启动第一轮无交互 `Codex`
- 如何在后续轮次启动新的独立无交互 `Codex` 对话
- 如何用当前环境下的 `Codex` 监督每轮真实执行内容

本页不回答：

- Harness doctrine 本体
- skill 单独测试模板
- 自动化 acceptance matrix
- 评分维度

## 二、固定题目

当前固定测试题目是：

- 在临时 repo 中实现一个纯 CLI 的"杀戮尖塔-lite"，包含完整核心系统

附加约束：

- 只做终端交互，不做图形界面或 Web UI
- 核心系统至少包含以下子系统，每个子系统作为独立 worktrack 推进：
  - **战斗系统**：玩家/敌人回合、HP/block、攻击/防御、胜负判定
  - **战斗记录**：结构化战斗日志，记录每回合动作与状态变化
  - **卡牌系统**：Card 基类、数值（damage/block/cost/rarity）、特效
  - **卡组系统**：Deck 构建、抽牌/弃牌/洗牌、手牌管理
  - **地图系统**：节点图（战斗/休息/商店/事件）、玩家移动、路径选择
  - **事件系统**：随机事件生成、选项、结果影响玩家状态
- 必须提供明确运行入口，并在 `README.md` 中说明运行方式
- 交互方式必须对 AI/agent 友好：通过标准输入/标准输出按轮交互，不依赖方向键、全屏 TUI、鼠标或实时操作
- 每轮输出应清楚展示当前状态、可选动作和本轮结果，便于 agent 持续读取并决策下一步输入
- repo 内必须提供一份面向 AI/agent 的游戏说明书，说明游戏目标、启动方式、命令格式、回合规则、胜负条件，并给出最小交互示例
- 每个子系统完成后应做收敛、验证和必要测试，再进入下一个子系统
- 不追求完整复刻原作，但要求核心系统闭环可运行

这里的测试对象不是单个 skill，而是：

- 给 repo 一个明确目标
- 只连续调用 `harness-skill`
- 观察它能否正确切换 scope、持续推进状态，并尽快把 repo 往目标实现方向推进

## 三、初始化临时测试 repo

先创建一套新的临时工作目录：

```bash
TMP_ROOT="$(mktemp -d /tmp/harness-spire-lite.XXXXXX)"
TMP_REPO="$TMP_ROOT/repo"
TMP_AGENTS_ROOT="$TMP_REPO/.agents/skills"
TMP_AW_ROOT="$TMP_REPO/.aw"
TMP_RUN_ROOT="$TMP_ROOT/run-artifacts"

printf 'TMP_ROOT=%s\n' "$TMP_ROOT"
```

这里的 `TMP_ROOT` 是整个临时工作区；真正的 Git repo 根是 `"$TMP_REPO"`，而 `"$TMP_RUN_ROOT"` 用来保存 repo 外的观察产物。

### 1. 建目录并初始化 repo

```bash
mkdir -p "$TMP_REPO" "$TMP_RUN_ROOT"
git init "$TMP_REPO"
git -C "$TMP_REPO" branch -m main
```

这里的初始化基线是“空仓库起步”：

- 每次手动观察都新建一套带随机后缀的临时工作目录，不复用旧的 `tmp` 路径
- `git init` 只是为了让 `codex exec --cd` 有标准 repo 根
- 不额外创建初始提交；baseline 从空仓库状态开始
- `branch -m main` 用来让临时 repo 的默认分支名和后续 `.aw` baseline branch 保持一致

### 2. 用通用 deploy 脚本准备隔离的 `.agents/skills/`

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py prune \
  --all \
  --backend agents \
  --agents-root "$TMP_AGENTS_ROOT"

python3 toolchain/scripts/deploy/adapter_deploy.py check_paths_exist \
  --backend agents \
  --agents-root "$TMP_AGENTS_ROOT"

python3 toolchain/scripts/deploy/adapter_deploy.py install \
  --backend agents \
  --agents-root "$TMP_AGENTS_ROOT"

python3 toolchain/scripts/deploy/adapter_deploy.py verify \
  --backend agents \
  --agents-root "$TMP_AGENTS_ROOT"
```

这一步的作用是：

- 在临时 repo 下准备一套隔离的 `agents` skill install
- 当前 first-wave install 已包含 `schedule-worktrack-skill`，后续轮次可在 `WorktrackScope` 内先刷新队列、选出 `current next action`，再进入 `dispatch-skills`
- 不污染当前仓库自己的 repo-local install

### 3. 用通用模板脚本生成最小 `.aw/`

```bash
python3 toolchain/scripts/deploy/aw_scaffold.py validate --profile first-wave-minimal

python3 toolchain/scripts/deploy/aw_scaffold.py generate \
  --profile first-wave-minimal \
  --output-root "$TMP_AW_ROOT" \
  --repo harness-manual-spire-lite \
  --owner manual-baseline \
  --baseline-branch main
```

这一步的作用是：

- 在临时 repo 下准备最小 `.aw/` 运行样例
- 让 `harness-skill` 有一套最小 control-state / repo / worktrack artifact 可读
- 默认保持 `RepoScope` 起跑，不在 scaffold 阶段预先绑定 `worktrack_id` 或执行分支
- 允许 `.aw/worktrack/*` 以占位模板形式存在，但它们在 round-000 前不应携带 active worktrack identity，也不应替代 repo judgment

这里的默认测试切面是“完整 Harness 起跑”，不是“预置一条 worktrack 后只测执行链”。因此 round-000 应先经过 repo judgment，再决定是否进入 `WorktrackScope`。

## 四、第一轮无交互 Codex

先准备 round-000 的 prompt 文件：

```bash
mkdir -p "$TMP_RUN_ROOT/round-000"
```

把下面这段内容保存到：

- `"$TMP_RUN_ROOT/round-000/init.prompt.md"`

```text
You are running inside a temporary repo used for Harness manual observation.

Use only `harness-skill` as the top-level control entry.

Current repo goal:
- Build a CLI Slay the Spire-lite in this temporary repo.
- Reach a full core system with combat, cards, deck, map, and events.

In scope:
- a runnable CLI entrypoint
- turn-based combat with player/enemy HP and block
- structured combat logger for turn replay
- card system with stats (damage, block, cost, rarity) and effects
- deck builder with draw, discard, shuffle, and hand management
- map system with nodes (combat, rest, shop, event) and path choices
- event system with random events, choices, and outcome effects
- AI-friendly stdin/stdout interaction
- a README with run instructions
- an AI-facing game manual

Out of scope:
- graphics or Web UI
- networking or multiplayer
- full Slay the Spire feature parity (relics, achievements, etc.)
- polish-only work with no system progress

Working rule:
- Continue across legal state transitions if no formal stop condition is hit.
- Do not stop just because one local skill round produced structured output.
- If the runtime lacks a real delegated execution carrier, report the runtime gap explicitly.
- Start from the current repo truth instead of assuming a preselected worktrack.

Observation priority:
- First show the real state transition and continuation logic.
- Let round-000 decide whether the repo should open a worktrack; do not assume the worktrack already exists unless the repo artifacts explicitly justify it.
- Try to keep the repo moving toward the smallest playable CLI combat build.
- Only stop when a real decision boundary, scope boundary, runtime gap, or other formal stop condition is hit.
```

然后执行第一轮：

```bash
codex exec \
  --cd "$TMP_REPO" \
  --sandbox danger-full-access \
  --json \
  --output-last-message "$TMP_RUN_ROOT/round-000/final.txt" \
  - < "$TMP_RUN_ROOT/round-000/init.prompt.md" \
  > "$TMP_RUN_ROOT/round-000/events.jsonl" \
  2> "$TMP_RUN_ROOT/round-000/stderr.txt"

git -C "$TMP_REPO" status --short > "$TMP_RUN_ROOT/round-000/git-status.txt"
git -C "$TMP_REPO" diff --stat > "$TMP_RUN_ROOT/round-000/git-diff-stat.txt"
```

## 五、后续轮次

后续轮次不恢复旧会话；每一轮都启动一个新的独立 `Codex` 对话，并让它从当前 repo、`.aw/` 状态和已保存的 round artifacts 中自行恢复上下文。

### 1. 默认工作指令要尽量简单

手动观察用的后续轮次，不应要求 human 每轮重复输入长恢复 prompt。默认只补最小工作指令：

- `开始工作`
- `继续工作`
- `继续工作：<一条额外信息或新约束>`

如果宿主支持显式 skill 唤起，可把它理解成：

- `$harness-skill + 开始工作`
- `$harness-skill + 继续工作`
- `$harness-skill + 继续工作：<一条额外信息或新约束>`

如果宿主只接受纯文本 prompt，就把上面的意图直接写成短文本，不额外重复恢复逻辑。恢复上下文、读取 `.aw/` 与历史 round artifacts，属于 `harness-skill` 的默认内部职责，不应每轮都由 human 重述。

### 2. round-001 的默认写法

先准备 round-001 的 prompt：

```bash
mkdir -p "$TMP_RUN_ROOT/round-001"
```

把下面这段内容保存到：

- `"$TMP_RUN_ROOT/round-001/init.prompt.md"`

```text
Use only `harness-skill` as the top-level control entry.

继续工作。
```

如果这一轮只有一条需要显式补充的新信息，可以写成：

```text
Use only `harness-skill` as the top-level control entry.

继续工作：上一轮已经完成最小可玩闭环；先根据当前 `.aw/` 状态和已保存 artifacts 判断是停止回交，还是切到新的合法 scope。
```

然后启动下一轮：

```bash
codex exec \
  --cd "$TMP_REPO" \
  --sandbox danger-full-access \
  --json \
  --output-last-message "$TMP_RUN_ROOT/round-001/final.txt" \
  - < "$TMP_RUN_ROOT/round-001/init.prompt.md" \
  > "$TMP_RUN_ROOT/round-001/events.jsonl" \
  2> "$TMP_RUN_ROOT/round-001/stderr.txt"

git -C "$TMP_REPO" status --short > "$TMP_RUN_ROOT/round-001/git-status.txt"
git -C "$TMP_REPO" diff --stat > "$TMP_RUN_ROOT/round-001/git-diff-stat.txt"
```

### 3. round-0xx 的统一写法

后续任意轮都复用同一套最小模板，只替换轮次编号和一句工作指令：

```bash
ROUND_ID="round-00x"
ROUND_PROMPT='继续工作'

mkdir -p "$TMP_RUN_ROOT/$ROUND_ID"
printf 'Use only `harness-skill` as the top-level control entry.\n\n%s\n' \
  "$ROUND_PROMPT" \
  > "$TMP_RUN_ROOT/$ROUND_ID/init.prompt.md"

codex exec \
  --cd "$TMP_REPO" \
  --sandbox danger-full-access \
  --json \
  --output-last-message "$TMP_RUN_ROOT/$ROUND_ID/final.txt" \
  - < "$TMP_RUN_ROOT/$ROUND_ID/init.prompt.md" \
  > "$TMP_RUN_ROOT/$ROUND_ID/events.jsonl" \
  2> "$TMP_RUN_ROOT/$ROUND_ID/stderr.txt"

git -C "$TMP_REPO" status --short > "$TMP_RUN_ROOT/$ROUND_ID/git-status.txt"
git -C "$TMP_REPO" diff --stat > "$TMP_RUN_ROOT/$ROUND_ID/git-diff-stat.txt"
```

推荐把 `ROUND_PROMPT` 限制在下面三种口径内：

- `开始工作`
- `继续工作`
- `继续工作：<一条额外信息或新约束>`

如果你要观察“当前合同完成后，Harness 是否会继续自动开下一段最小 worktrack”，优先修改 `.aw/control-state.md` 中的 `Continuation Authority` 策略位，而不是把授权逻辑重新塞回 prompt prose。

默认观察基线应是：

- `post_contract_autonomy: delegated-minimal`
  - 允许在当前 goal 内自动挑一段低风险、最小 bounded follow-up slice
- `max_auto_new_worktracks: 5`
  - 覆盖战斗系统、战斗记录、卡牌系统、卡组系统、地图系统、事件系统等子系统
- `stop_after_autonomous_slice: yes`
  - 每个 worktrack 完成后仍然 handback，等待确认后再开下一个

只有在你刻意测试 strict handback / 不续跑行为时，才切换到：

- `post_contract_autonomy: manual-only`
  - strict handback；`继续工作` 只会复核并停在边界

如果你要观察"Harness 能否在完整系统目标下自动拆分为多个 worktrack 并连续推进"，保持 `delegated-minimal` 并将 budget 设得足够覆盖所有子系统。Harness 应基于 goal charter 和当前 repo 状态，自主决定下一个 worktrack 的 scope 和验收标准。

这类观察的重点是 control-state policy 是否生效，而不是 human 是否又在 prompt 里写了一段长恢复说明。

但要让这个判断在“每轮新开独立对话”的 runtime 下仍然成立，`.aw/control-state.md` 不能只保存 policy，还要保存 handback guard 和 autonomy ledger。

最小 fixture 语义应是：

- 某轮如果因 `contract-boundary`、`approval-gated` 或等价 handback 原因停下，应写回：
  - `handoff_state: awaiting-handoff`
  - `last_stop_reason: <实际 stop 原因>`
  - `last_handback_signature: <当前 handback 边界的稳定指纹>`
  - `handback_reaffirmed_rounds: <连续确认次数>`
- 在 `post_contract_autonomy: manual-only` 下，后续新对话即使已经回到 `RepoScope`，单独一句 `继续工作` 也只允许复核并返回同一个 handback；不得把 “已在 RepoScope” 误读成 “允许 fresh handoff / 新 worktrack”
- 在 `post_contract_autonomy: delegated-minimal` 下，只有 `handoff_state: awaiting-handoff` 且 `autonomy_budget_remaining > 0` 时才允许自动开一段 follow-up worktrack；一旦决定开启，就应立刻消费预算，并把 `handoff_state` 切到 `autonomous-slice-active`
- autonomous slice 关闭后，如果 `stop_after_autonomous_slice: yes`，必须再次写回 `handoff_state: awaiting-handoff`；不能因为又回到了 `RepoScope`，就默认继续链式扩张
- `stable-handback` 应由重复的 `last_handback_signature` 推导出来；不要把它当成唯一长期字段写死在 control-state 里

只有在你刻意做诊断、对比或研究某种恢复行为时，才需要退回到长 prompt，把“必须先读哪些 artifacts”之类的观察要求明写出来。

当前建议：

- 默认每一轮都新开独立对话，不依赖会话恢复
- 连续性来自当前 repo、`.aw/` 状态和已保存的 round artifacts，而不是来自对话记忆
- human 默认只提供最小工作意图；除非有新的事实、约束或程序员决策边界，不重复输入长说明
- 只有在真的需要重新建立临时 repo 基线时，才整体重开一套新的 `TMP_ROOT`

补充说明：

- 默认 runbook 现在测试的是完整 `Harness` 主链：
  - `RepoScope`
  - `repo-status-skill`
  - `repo-whats-next-skill`
  - `enter-worktrack`
  - `init-worktrack-skill`
  - `schedule-worktrack-skill`
  - `dispatch-skills`
- 不再把“第一条 worktrack 是什么”提前塞进 scaffold 基线里
- 如果将来确实要观察“只测 worktrack 执行链”的场景，应另开一个显式命名的 `worktrack-preseeded` 变体 runbook，而不是污染默认路径

## 六、当前环境下的 Codex 如何监督

当前环境下的 `Codex` 不做额外评分卡，只直接观察每轮真实执行内容。

`final.txt` 只保存最后一条消息，不足以完整覆盖这一轮的真实执行链路；监督时应以每轮保存下来的完整运行产物为准。

每轮至少保留：

- 本轮 prompt 原文
- 本轮 `events.jsonl`
- 本轮 `stderr.txt`
- 本轮 `final.txt`
- 本轮 `git-status.txt`
- 本轮 `git-diff-stat.txt`
- 临时 repo 中最相关的 `.aw/` 状态变化和文件快照
- 临时 repo 中最相关的文件变化和对应 diff 片段

监督时，直接把这些材料喂给当前环境下的 `Codex`，让它观察：

- 这一轮 `harness-skill` 读了什么
- 这一轮真实输出流里发生了什么
- 它怎么判断当前状态
- 它怎么切 scope
- 它为什么继续
- 它为什么停下
- 它是否真的调用了下游执行载体，还是如实暴露 runtime gap
- 它对 repo 目标实际推进了什么

当前重点不是事后整理卡片，而是直接观察真实执行链路。

## 七、继续与停止

这条工作流默认是连续推进，不是“一轮一停”。

当前更适合停下来观察的情况只有：

- 真的需要人工决策
- 明显命中 scope 切换观察点
- 出现 runtime gap
- repo 目标已经没有有效推进

如果任务足够小、边界足够清楚，可以尽量减少“需要人工决策”的中断。

## 八、相关文档

- [Deploy Runbook](./deploy-runbook.md)
- [Template Tooling MVP](./template-tooling-mvp.md)
- [Codex Usage Help](../usage-help/codex.md)
