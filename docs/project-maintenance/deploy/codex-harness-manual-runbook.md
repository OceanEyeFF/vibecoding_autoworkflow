---
title: "Codex Harness Manual Runbook"
status: active
updated: 2026-04-20
owner: aw-kernel
last_verified: 2026-04-20
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

- 在临时 repo 中实现一个纯 CLI 的“杀戮尖塔-lite”最小可玩版本

附加约束：

- 只做终端交互，不做图形界面或 Web UI
- 目标是尽快形成可运行的最小闭环：玩家可进入战斗、执行回合行动，并看到胜负或结束结果
- 最小机制至少包含：玩家、敌人、生命值、攻击/防御、回合推进
- 必须提供明确运行入口，并在 `README.md` 中说明运行方式
- 交互方式必须对 AI/agent 友好：通过标准输入/标准输出按轮交互，不依赖方向键、全屏 TUI、鼠标或实时操作
- 每轮输出应清楚展示当前状态、可选动作和本轮结果，便于 agent 持续读取并决策下一步输入
- repo 内必须提供一份面向 AI/agent 的游戏说明书，说明游戏目标、启动方式、命令格式、回合规则、胜负条件，并给出最小交互示例
- 可以补最小测试或基本验证命令，但不追求完整复刻原作
- 不要求实现卡牌池、地图、遗物、存档、平衡性调优等扩展系统
- 达到最小可玩闭环后，应优先做收敛、整理和必要验证，而不是继续无界扩展

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
  --baseline-branch main \
  --worktrack-id wt-spire-lite \
  --branch feat/spire-lite
```

这一步的作用是：

- 在临时 repo 下准备最小 `.aw/` 运行样例
- 让 `harness-skill` 有一套最小 control-state / repo / worktrack artifact 可读

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
- Reach a minimal but playable command-line combat loop quickly.

In scope:
- a runnable CLI entrypoint
- one-player combat
- a small turn-based combat loop
- player and enemy state
- hp, attack, and defend actions
- turn-based terminal choices
- a clear win/lose or end-of-run result
- AI-friendly stdin/stdout interaction
- a short README with run instructions
- a short AI-facing game manual

Out of scope:
- graphics
- networking
- card pools, deckbuilding, or progression systems
- full Slay the Spire feature parity
- polish-only work with no repo-goal progress

Working rule:
- Continue across legal state transitions if no formal stop condition is hit.
- Do not stop just because one local skill round produced structured output.
- If the runtime lacks a real delegated execution carrier, report the runtime gap explicitly.

Observation priority:
- First show the real state transition and continuation logic.
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

后续轮次不恢复旧会话；每一轮都启动一个新的独立 `Codex` 对话，并让它从当前 repo 和运行产物中自行恢复上下文。

先准备 round-001 的 prompt：

```bash
mkdir -p "$TMP_RUN_ROOT/round-001"
```

把下面这段内容保存到：

- `"$TMP_RUN_ROOT/round-001/init.prompt.md"`

保存时，把文中的 `$TMP_RUN_ROOT` 替换为本次运行实际打印出来的绝对路径值，避免新对话只能看到变量名而看不到上一轮 artifacts 的真实位置。

```text
You are starting a new independent Codex conversation for the next Harness observation round.

Do not assume any conversational memory from previous rounds.
Recover context from the current repo state, the current `.aw/` state, and the saved artifacts under:
- /tmp path recorded earlier as TMP_RUN_ROOT
- round artifact directories such as `$TMP_RUN_ROOT/round-000/` and `$TMP_RUN_ROOT/round-001/`

Before acting, first read the most relevant earlier-round artifacts that are available, especially:
- prior `init.prompt.md`
- prior `final.txt`
- prior `events.jsonl`
- prior `stderr.txt`
- prior `git-status.txt`

Use only `harness-skill` as the top-level control entry.

Keep working on the same repo goal:
- Build a CLI Slay the Spire-lite in this temporary repo.

Do not restart planning from scratch.
Do not widen scope.
Only stop if a real formal stop condition is hit.
If scope changed in the previous round, continue from the new active scope instead of resetting.
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

当前建议：

- 默认每一轮都新开独立对话，不依赖会话恢复
- 连续性来自当前 repo、`.aw/` 状态和已保存的 round artifacts，而不是来自对话记忆
- 只有在真的需要重新建立临时 repo 基线时，才整体重开一套新的 `TMP_ROOT`

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
