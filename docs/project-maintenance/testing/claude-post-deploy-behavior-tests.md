---
title: "Claude Post-Deploy Behavior Tests"
status: active
updated: 2026-05-04
owner: aw-kernel
last_verified: 2026-05-04
---
# Claude Post-Deploy Behavior Tests

> 目的：固定一条最小手动工作流，在 `tmp` 目录下初始化临时测试 repo，用无交互 `Claude Code` 连续调用 `harness-skill` 推进固定题目，并由当前环境下的 `Codex` 直接监督每轮真实执行内容。

本页属于 [Testing Runbooks](./README.md) 系列文档。通用 deploy 主流程见 [Deploy Runbook](../deploy/deploy-runbook.md)。Claude 使用入口见 [Claude Repo-local Usage Help](../usage-help/claude.md)。

## 一、适用范围

本页只回答：

- 如何在 `tmp` 下初始化临时测试 repo
- 如何用通用 deploy 脚本准备最小 Claude 项目级 skill 运行面
- 如何启动第一轮无交互 `Claude Code`
- 如何在后续轮次启动新的独立无交互 `Claude Code` 对话
- 如何用当前环境下的 `Codex` 监督每轮真实执行内容

本页不回答：

- Harness doctrine 本体
- skill 单独测试模板
- 自动化 acceptance matrix
- 评分维度
- Claude 作为 `agents` 主路径替代品的产品定位

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
- 每个子系统必须拆分为独立 worktrack，不允许在单个 worktrack 中完成多个子系统
- worktrack 完成后必须 handback，等待继续信号后再开下一个
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
TMP_PARENT="${TMP_PARENT:-$HOME/tmp}"
mkdir -p "$TMP_PARENT"
TMP_ROOT="$(mktemp -d "$TMP_PARENT/harness-claude-spire-lite.XXXXXX")"
TMP_REPO="$TMP_ROOT/repo"
TMP_CLAUDE_ROOT="$TMP_REPO/.claude/skills"
TMP_RUN_ROOT="$TMP_ROOT/run-artifacts"
CLAUDE_TEST_HOME="$TMP_ROOT/claude-home"
NPM_CONFIG_CACHE="$TMP_ROOT/npm-cache"

printf 'TMP_ROOT=%s\n' "$TMP_ROOT"
```

这里的 `TMP_ROOT` 是整个临时工作区；真正的 Git repo 根是 `"$TMP_REPO"`，而 `"$TMP_RUN_ROOT"` 用来保存 repo 外的观察产物。默认把临时根放在 `$HOME/tmp` 下，是为了满足 deploy path safety policy；不要把显式 `--claude-root` 指向不在允许前缀内的共享 `/tmp` 根。

如果当前 carrier 的 `$HOME` 不可写，必须把 `TMP_PARENT` 与 `NPM_CONFIG_CACHE` 显式放到可写临时目录，例如：

```bash
TMP_PARENT=/tmp
```

本页的 `NPM_CONFIG_CACHE="$TMP_ROOT/npm-cache"` 是固定测试条件。不要让 `npx` 或 `npm exec` 回落到宿主默认 cache；否则 sandbox 下可能因为 `$HOME/.npm` 只读而失败，并把 package 行为误判为 deploy 问题。

Claude Code 的 Bash tool 也会写入用户级 session state。若当前 carrier 的 `$HOME/.claude` 不可写，必须使用临时 Claude home，并只复制本机运行所需的登录状态：

```bash
mkdir -p "$CLAUDE_TEST_HOME/.claude"
test -f "$HOME/.claude.json" && cp "$HOME/.claude.json" "$CLAUDE_TEST_HOME/.claude.json"
test -d "$HOME/.claude" && find "$HOME/.claude" -maxdepth 1 -type f -exec cp {} "$CLAUDE_TEST_HOME/.claude/" \;
```

`CLAUDE_TEST_HOME` 只属于本次临时运行，不进入长期 evidence；整理外发日志前必须确认没有复制或泄露本机认证文件内容。

### 1. 建目录并初始化 repo

```bash
mkdir -p "$TMP_REPO" "$TMP_RUN_ROOT"
git init "$TMP_REPO"
git -C "$TMP_REPO" branch -m main
printf '.claude/\n' >> "$TMP_REPO/.git/info/exclude"
```

这里的初始化基线是“空仓库起步”：

- 每次手动观察都新建一套带随机后缀的临时工作目录，不复用旧的临时路径
- `git init` 只是为了让 `claude --bare -p` 有标准 repo 根
- `.claude/` 是本轮 deploy target，不是临时产品 repo 的源码；用 `.git/info/exclude` 排除它，避免 Claude 在后续 worktrack commit 中把安装 payload 当作业务变更提交
- 不额外创建初始提交；baseline 从空仓库状态开始
- `branch -m main` 用来让临时 repo 的默认分支名和后续 `.aw` baseline branch 保持一致

### 2. 用当前候选包准备隔离的 `.claude/skills/`

如果本轮要验证尚未发布的 Node-only candidate，优先使用本地 `.tgz` 包路径：

```bash
PACKAGE_TGZ="/path/to/aw-installer-<version>.tgz"
```

然后通过 `npx --package` 在临时 repo 中安装和验证 Claude payload：

```bash
(
  cd "$TMP_REPO"
  AW_HARNESS_REPO_ROOT="" \
  AW_HARNESS_TARGET_REPO_ROOT="" \
  NPM_CONFIG_CACHE="$NPM_CONFIG_CACHE" \
    npx --yes --package "$PACKAGE_TGZ" -- aw-installer install --backend claude

  AW_HARNESS_REPO_ROOT="" \
  AW_HARNESS_TARGET_REPO_ROOT="" \
  NPM_CONFIG_CACHE="$NPM_CONFIG_CACHE" \
    npx --yes --package "$PACKAGE_TGZ" -- aw-installer verify --backend claude
)
```

这一路径是当前本地 npx package smoke 的推荐口径：Claude payload 由 Node package 安装，Python deploy helper 不参与 package runtime。

如果不是验证 package surface，而只是观察源码 checkout 的 Claude 行为，也可以用通用 deploy 脚本准备隔离的 `.claude/skills/`：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py prune \
  --all \
  --backend claude \
  --claude-root "$TMP_CLAUDE_ROOT"

PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py check_paths_exist \
  --backend claude \
  --claude-root "$TMP_CLAUDE_ROOT"

PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py install \
  --backend claude \
  --claude-root "$TMP_CLAUDE_ROOT"

PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify \
  --backend claude \
  --claude-root "$TMP_CLAUDE_ROOT"
```

这一步的作用是：

- 在临时 repo 下准备一套隔离的 Claude project-level skill install
- 当前 `claude` install 已包含全部 19 个 skills，覆盖完整 Harness 控制回路与通用执行 worker
  - `RepoScope`：SetGoal / Observe / Decide / Close / ChangeGoal
  - `WorktrackScope`：Init / Observe / Decide / Dispatch / Verify / Judge / Recover / Close
- `set-harness-goal-skill` 自带完整的 `.aw/` 模板资产（`assets/` 目录），可在运行时根据用户动态需求生成 goal charter、control state 和 repo snapshot，无需外部 scaffold 脚本预置 `.aw/`
- `set-harness-goal-skill` 的 cold-start helper 随 payload 以 `scripts/deploy_aw.js` 分发，Python helper 只作为源码侧 reference 保留
- 不污染当前仓库自己的 repo-local install

这里的默认测试切面是"完整 Harness 冷启动"：repo 为空、`.aw/` 不存在，Harness 需要从头初始化参考信号、建立控制面，再进入 Observe -> Decide -> WorktrackScope 的完整链路。

### 3. 正式运行前二次确认运行策略

完成隔离 deploy 后、启动 `round-000` 前，operator 必须先确认本次要观察的 repo 运行策略。这里确认的是“deploy 后的临时 repo 应如何推进 worktrack”，不是确认 deploy 是否成功。

当前已验证的默认初始化行为是：

- `round-000` 可以从空 repo 自动初始化 `.aw/`，并在目标内打开一个最小 autonomous slice。
- 该 slice close / gate pass / repo refresh 后会进入 handback boundary。
- 若 control state 写成 `handback_lock_active: yes` 且 `autonomy_budget_remaining: 0`，后续独立新对话里的裸 `继续工作` 只允许复核并返回 handback，不会自动开启下一 worktrack。
- 如果要观察“连续自动拆分多个 subsystem 并推进”，不能只依赖裸 `继续工作`；必须在正式开始前显式选择 continuous-autonomy 观察策略，或在第一轮 handback 后显式解除交接锁并授权下一 worktrack。

正式开始前至少写下本轮观察 profile。这个 profile 只是 operator-facing 记录标签，不是 `.aw` 的权威字段；真正的推进权限仍以 `.aw/control-state.md` 的 `Continuation Authority`、`Handback Guard` 与 `Autonomy Ledger` 字段为准。

```text
OBSERVATION_PROFILE=strict-handback
```

或：

```text
OBSERVATION_PROFILE=continuous-autonomy
```

profile 与标准 control-state 字段的对应关系：

| Observation profile | 权威字段含义 | 观察目标 |
|---|---|---|
| `strict-handback` | `handoff_state` 进入 handback，`handback_lock_active` 或等价 guard 生效，且 `autonomy_budget_remaining: 0` 或没有显式重新授权 | 验证每个 worktrack 完成后是否稳定停在交接边界；裸 `继续工作` 不应解锁 |
| `continuous-autonomy` | `post_contract_autonomy: delegated-minimal`，`autonomy_scope: current-goal-only`，`autonomy_budget_remaining > 0`，并定义 `stop_after_autonomous_slice` | 验证 Harness 能否在当前 goal 内连续打开多个 bounded subsystem worktrack |

如果选择 `strict-handback`，保留本 runbook 默认 prompt 即可。如果选择 `continuous-autonomy`，必须在 `round-000` prompt 的 `Working rule` 中明确补充连续策略，或者在 `round-000` close 后修改 `.aw/control-state.md` 的 `Continuation Authority / Autonomy Ledger` 后再进入 `round-001`。不要把二者混在同一轮观察里，否则无法判断 Harness 是“正确停下”还是“未能继续”。

`continuous-autonomy` 不删除“每个子系统独立 worktrack”的约束。它只改变 handback 后是否允许 Harness 消费剩余预算进入下一个 bounded subsystem worktrack。换言之，handback 是 slice 边界记录；当 `autonomy_budget_remaining > 0` 时，它不应被写成需要 human unlock 的硬锁。

## 四、第一轮无交互 Claude Code

先准备 round-000 的 prompt 文件：

```bash
mkdir -p "$TMP_RUN_ROOT/round-000"
```

把下面这段内容保存到：

- `"$TMP_RUN_ROOT/round-000/init.prompt.md"`

```text
/harness-skill

You are running inside a temporary repo used for Harness manual observation.

Use only `harness-skill` as the top-level control entry.

This is a cold-start scenario: the repo is empty and `.aw/` does not exist.
Harness must initialize the reference signal first, then proceed through the full control loop.

User requirement (natural language):
Build a CLI Slay the Spire-lite in this temporary repo.
Reach a full core system with combat, cards, deck, map, and events.

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

Additional constraints:
- Each subsystem must be a separate worktrack: combat, combat logger, cards, deck, map, events
- Do not complete multiple subsystems within a single worktrack
- After each worktrack completes, hand back and wait for continuation before starting the next

Working rule:
- This is a non-interactive test. After `set-harness-goal-skill` analyzes requirements, directly generate and write the goal charter, control state, and repo snapshot to `.aw/` without waiting for confirmation.
- Continue across legal state transitions if no formal stop condition is hit.
- Do not stop just because one local skill round produced structured output.
- If the runtime lacks a real delegated execution carrier, report the runtime gap explicitly.
- Start from the current repo truth instead of assuming a preselected worktrack.
- Keep `.aw/` artifact writeback compact: write concise control-state, gate, closeout, and snapshot facts; avoid duplicating long evidence already available in git diff, test output, or round artifacts.
- Do not use large shell heredocs for any repo file, including source, tests, docs, or `.aw/` artifacts. Prefer `Edit`, short file writes, or smaller incremental changes; do not combine large file creation, test execution, and git operations into one shell command.
- Keep commit messages concise. Detailed evidence belongs in the saved round artifacts and compact `.aw/` references, not in long commit bodies.
- Round-000 must open and complete only the combat worktrack unless the repo state explicitly proves combat is already complete. Do not start cards, deck, map, or events in round-000.
- Stop immediately after the current slice is implemented, tested, checkpointed, closed, and refreshed.

Observation priority:
- First show the real state transition and continuation logic.
- If `.aw/` is missing, `harness-skill` should route to `set-harness-goal-skill` (RepoScope.SetGoal) to initialize the control plane from scratch.
- Let round-000 decide whether the repo should open a worktrack; do not assume the worktrack already exists unless the repo artifacts explicitly justify it.
- Try to keep the repo moving toward the smallest playable CLI combat build.
- Only stop when a real decision boundary, scope boundary, runtime gap, or other formal stop condition is hit.
```

如果本轮选择 `OBSERVATION_PROFILE=continuous-autonomy`，在同一个 prompt 的 `Working rule` 后追加下面的覆盖块：

```text
Continuous-autonomy observation override:
- This run is explicitly testing continuous autonomous subsystem progression within the current goal.
- Initialize or update `.aw/control-state.md` so `post_contract_autonomy: delegated-minimal`, `autonomy_scope: current-goal-only`, `max_auto_new_worktracks: 20`, `autonomy_budget_remaining: 20`, and `stop_after_autonomous_slice: yes`.
- Keep every subsystem as its own independent worktrack. Do not merge combat logger, cards, deck, map, or events into the same worktrack.
- After a worktrack closes, record the handback boundary, but do not set `handback_lock_active: yes` while `autonomy_budget_remaining > 0`.
- Keep each handback and closeout artifact compact. The observation checks state transitions and repo progress, not verbose evidence prose.
- Avoid large shell heredocs for all repo writes; long writeback or source/test heredocs are known Claude non-interactive timeout and API-error risks and should be treated as carrier behavior, not package deploy behavior.
- If `handoff_state: awaiting-handoff` and `autonomy_budget_remaining > 0`, a later bare `继续工作` in a new independent Claude Code conversation is authorized to consume one autonomy budget unit and open the next bounded subsystem worktrack under the same goal.
- After a worktrack closes, the next autonomous slice should prefer the next chartered subsystem. A validation-hardening or packaging-entry cleanup slice is allowed only when committed tests cannot run from repo root or another concrete blocker prevents starting the next subsystem; record that blocker as the slice rationale.
- Once the autonomy budget reaches 0, strict handback applies again and bare `继续工作` must not unlock the boundary.
```

然后执行第一轮：

```bash
(
  cd "$TMP_REPO"
  HOME="$CLAUDE_TEST_HOME" \
  XDG_CONFIG_HOME="$CLAUDE_TEST_HOME/.config" \
  XDG_CACHE_HOME="$CLAUDE_TEST_HOME/.cache" \
  claude --bare \
    --no-session-persistence \
    --permission-mode acceptEdits \
    --verbose \
    --output-format stream-json \
    -p "$(cat "$TMP_RUN_ROOT/round-000/init.prompt.md")" \
    > "$TMP_RUN_ROOT/round-000/events.jsonl" \
    2> "$TMP_RUN_ROOT/round-000/stderr.txt"
)

tail -n 1 "$TMP_RUN_ROOT/round-000/events.jsonl" > "$TMP_RUN_ROOT/round-000/final-event.json"
git -C "$TMP_REPO" status --short > "$TMP_RUN_ROOT/round-000/git-status.txt"
git -C "$TMP_REPO" diff --stat > "$TMP_RUN_ROOT/round-000/git-diff-stat.txt"
git -C "$TMP_REPO" log --oneline --decorate --all --max-count=5 > "$TMP_RUN_ROOT/round-000/git-log.txt"
```

说明：

- `--bare` 仍支持通过 `/skill-name` 解析显式安装的 project-level skills，但不会自动读取 `CLAUDE.md`；本 runbook 的上下文必须通过 prompt、repo 状态和 explicit skill payload 提供。
- `--no-session-persistence` 配合 `CLAUDE_TEST_HOME` 使用，避免测试会话写入宿主长期 Claude state。
- `--output-format stream-json` 保存完整事件流；不要只保留最后一句自然语言输出。
- 如果当前环境需要更强权限隔离，可用 `--permission-mode default` 代替 `acceptEdits`，但冷启动写入 smoke 会因此停在权限确认边界，不能当作完整行为通过。
- 如果本轮使用 `npx --package "$PACKAGE_TGZ"` 安装 payload，所有 `npx` / `npm exec` 命令都必须继承 `NPM_CONFIG_CACHE="$TMP_ROOT/npm-cache"`。

## 五、后续轮次

后续轮次不恢复旧会话；每一轮都启动一个新的独立 `Claude Code` 对话，并让它从当前 repo、`.aw/` 状态和已保存的 round artifacts 中自行恢复上下文。

### 1. 默认工作指令要尽量简单

手动观察用的后续轮次，不应要求 human 每轮重复输入长恢复 prompt。默认只补最小工作指令：

- `开始工作`
- `继续工作`
- `继续工作：<一条额外信息或新约束>`

如果宿主支持显式 skill 唤起，可把它理解成：

- `/harness-skill + 开始工作`
- `/harness-skill + 继续工作`
- `/harness-skill + 继续工作：<一条额外信息或新约束>`

恢复上下文、读取 `.aw/` 与历史 round artifacts，属于 `harness-skill` 的默认内部职责，不应每轮都由 human 重述。

### 2. round-001 的默认写法

先准备 round-001 的 prompt：

```bash
mkdir -p "$TMP_RUN_ROOT/round-001"
```

把下面这段内容保存到：

- `"$TMP_RUN_ROOT/round-001/init.prompt.md"`

```text
/harness-skill

Use only `harness-skill` as the top-level control entry.

继续工作。

Runtime constraints:
- Keep `.aw/` artifact writeback compact.
- Do not use large shell heredocs for any repo file, including source, tests, docs, or `.aw/` artifacts.
- Keep commit messages concise.
- Prefer the next chartered subsystem. Only open validation-hardening or packaging-entry cleanup first when a concrete blocker prevents validating or extending the current baseline.
- Stop after the current legal slice reaches implementation, validation, checkpoint, closeout, and repo refresh.
```

如果这一轮只有一条需要显式补充的新信息，可以写成：

```text
/harness-skill

Use only `harness-skill` as the top-level control entry.

继续工作：上一轮已经完成最小可玩闭环；先根据当前 `.aw/` 状态和已保存 artifacts 判断是停止回交，还是切到新的合法 scope。
```

然后启动下一轮：

```bash
(
  cd "$TMP_REPO"
  HOME="$CLAUDE_TEST_HOME" \
  XDG_CONFIG_HOME="$CLAUDE_TEST_HOME/.config" \
  XDG_CACHE_HOME="$CLAUDE_TEST_HOME/.cache" \
  claude --bare \
    --no-session-persistence \
    --permission-mode acceptEdits \
    --verbose \
    --output-format stream-json \
    -p "$(cat "$TMP_RUN_ROOT/round-001/init.prompt.md")" \
    > "$TMP_RUN_ROOT/round-001/events.jsonl" \
    2> "$TMP_RUN_ROOT/round-001/stderr.txt"
)

tail -n 1 "$TMP_RUN_ROOT/round-001/events.jsonl" > "$TMP_RUN_ROOT/round-001/final-event.json"
git -C "$TMP_REPO" status --short > "$TMP_RUN_ROOT/round-001/git-status.txt"
git -C "$TMP_REPO" diff --stat > "$TMP_RUN_ROOT/round-001/git-diff-stat.txt"
git -C "$TMP_REPO" log --oneline --decorate --all --max-count=5 > "$TMP_RUN_ROOT/round-001/git-log.txt"
```

### 3. round-0xx 的统一写法

后续任意轮都复用同一套最小模板，只替换轮次编号和一句工作指令：

```bash
ROUND_ID="round-00x"
ROUND_PROMPT='继续工作'

mkdir -p "$TMP_RUN_ROOT/$ROUND_ID"
printf '/harness-skill\n\nUse only `harness-skill` as the top-level control entry.\n\n%s\n' \
  "$ROUND_PROMPT" \
  > "$TMP_RUN_ROOT/$ROUND_ID/init.prompt.md"

(
  cd "$TMP_REPO"
  HOME="$CLAUDE_TEST_HOME" \
  XDG_CONFIG_HOME="$CLAUDE_TEST_HOME/.config" \
  XDG_CACHE_HOME="$CLAUDE_TEST_HOME/.cache" \
  claude --bare \
    --no-session-persistence \
    --permission-mode acceptEdits \
    --verbose \
    --output-format stream-json \
    -p "$(cat "$TMP_RUN_ROOT/$ROUND_ID/init.prompt.md")" \
    > "$TMP_RUN_ROOT/$ROUND_ID/events.jsonl" \
    2> "$TMP_RUN_ROOT/$ROUND_ID/stderr.txt"
)

tail -n 1 "$TMP_RUN_ROOT/$ROUND_ID/events.jsonl" > "$TMP_RUN_ROOT/$ROUND_ID/final-event.json"
git -C "$TMP_REPO" status --short > "$TMP_RUN_ROOT/$ROUND_ID/git-status.txt"
git -C "$TMP_REPO" diff --stat > "$TMP_RUN_ROOT/$ROUND_ID/git-diff-stat.txt"
git -C "$TMP_REPO" log --oneline --decorate --all --max-count=5 > "$TMP_RUN_ROOT/$ROUND_ID/git-log.txt"
```

推荐把 `ROUND_PROMPT` 限制在下面三种口径内：

- `开始工作`
- `继续工作`
- `继续工作：<一条额外信息或新约束>`

如果你要观察“当前合同完成后，Harness 是否会继续自动开下一段最小 worktrack”，必须先完成上文的运行策略二次确认。优先修改 `.aw/control-state.md` 中的 `Continuation Authority` 和 `Autonomy Ledger` 策略位，或者在 `round-000` prompt 中显式声明 continuous-autonomy；不要把授权逻辑临时塞回每一轮 prompt prose。

当前已验证的 `strict-handback` 基线是：

- `round-000` 可自动完成一个最小 worktrack
- worktrack close 后写回 handback guard
- 后续裸 `继续工作` 只做状态复核
- 若要继续，必须显式解除交接锁或指定下一 subsystem worktrack

`continuous-autonomy` 对照基线才应设置为：

- `post_contract_autonomy: delegated-minimal`
  - 允许在当前 goal 内自动挑一段低风险、最小 bounded follow-up slice
- `max_auto_new_worktracks: <显式预算>`
  - 该值不是初始化默认值；本固定题目如需覆盖战斗记录、卡牌、卡组、地图、事件等剩余子系统，可在 continuous-autonomy 对照 run 中显式设置为 `20`
  - `20` 是观察预算，不是目标子系统数量；它需要覆盖 repo 观察、scope 切换、worktrack 初始化、执行、验证、closeout 和可能的恢复/重试轮次
- `stop_after_autonomous_slice: yes`
  - 每个 worktrack 完成后仍然 handback，等待确认后再开下一个

如果要做比默认 handback guard 更强的 strict 对照，才切换到：

- `post_contract_autonomy: manual-only`
  - strict handback；`继续工作` 只会复核并停在边界

如果你要观察"Harness 能否在完整系统目标下自动拆分为多个 worktrack 并连续推进"，保持 `delegated-minimal` 并将 budget 设得足够覆盖所有子系统。Harness 应基于 goal charter 和当前 repo 状态，自主决定下一个 worktrack 的 scope 和验收标准。

这里的 `budget` 是上限，不是必须耗尽的目标值。如果当前 goal 下的 chartered subsystem 已全部完成，或者继续自动开新 worktrack 只能开始发明未 charter 的新范围，Harness 应提前回到 `stable handback`，即使 `autonomy_budget_remaining > 0` 也不应继续消耗。

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
    - `set-harness-goal-skill` (SetGoal - 仅在 .aw/ 未初始化时)
    - `repo-status-skill` (Observe)
    - `repo-whats-next-skill` (Decide)
    - `repo-refresh-skill` (Close)
    - `repo-change-goal-skill` (ChangeGoal)
  - `enter-worktrack`
  - `WorktrackScope`
    - `init-worktrack-skill` (Init)
    - `worktrack-status-skill` (Observe)
    - `schedule-worktrack-skill` (Decide)
    - `dispatch-skills` (Dispatch)
    - `review-evidence-skill` (Verify - implementation)
    - `test-evidence-skill` (Verify - validation)
    - `rule-check-skill` (Verify - policy)
    - `gate-skill` (Judge)
    - `recover-worktrack-skill` (Recover)
    - `close-worktrack-skill` (Close)
- 不再通过外部 scaffold 脚本预置 `.aw/` 基线；`.aw/` 由 `set-harness-goal-skill` 在运行时根据用户动态需求从头初始化
- 如果将来确实要观察“只测 worktrack 执行链”的场景，应另开一个显式命名的 `worktrack-preseeded` 变体 runbook，而不是污染默认路径

## 六、当前环境下的 Codex 如何监督

当前环境下的 `Codex` 不做额外评分卡，只直接观察每轮真实执行内容。

`final-event.json` 只保存最后一条事件，不足以完整覆盖这一轮的真实执行链路；监督时应以每轮保存下来的完整运行产物为准。

每轮至少保留：

- 本轮 prompt 原文
- 本轮 `events.jsonl`
- 本轮 `stderr.txt`
- 本轮 `final-event.json`
- 本轮 `git-status.txt`
- 本轮 `git-diff-stat.txt`
- 本轮 `git-log.txt`
- 临时 repo 中最相关的 `.aw/` 状态变化和文件快照
- 临时 repo 中最相关的文件变化和对应 diff 片段

如果 Claude 在临时 repo 内建立 bootstrap commit、切分支或写入 Harness baseline，记录对应 commit SHA、分支名和 `git-log.txt`。临时 repo 内的 bootstrap commit 是本轮行为证据；不要把它和当前源仓库污染混为一类问题。

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
- Claude API/server error 导致本轮无法自然收束
- Claude Bash tool 因宿主 `$HOME/.claude/session-env` 只读而失败；应切换到 `CLAUDE_TEST_HOME` 后重跑，不能把它归因于 package payload
- Claude 在单轮内使用大 heredoc、长 commit body 或过量 evidence prose，导致上下文暴涨或 API/server error；应压缩写入方式与本轮 scope 后重跑
- repo 目标已经没有有效推进
- Claude runtime 无法识别项目级 skill entry
- 冷启动写入越过临时 repo
- 临时 repo 的 commit 把 `.claude/skills/` deploy payload 纳入业务 diff；应先确认 `.git/info/exclude` 已包含 `.claude/`
- 输出声称使用了当前仓库不存在的 `claude` deploy adapter
- `.aw/` artifact 缺失或明显不符合 Harness control-plane 结构

如果任务足够小、边界足够清楚，可以尽量减少“需要人工决策”的中断。

## 八、已验证观察记录

历史 Claude smoke 路径已升级为与 Codex runbook 同构的多轮观察协议。长期测试真相只保留本页的可重复运行步骤；具体单次 evidence 应写入临时 `TMP_RUN_ROOT` 或对应 worktrack 交接，不长期写入 docs。

## 九、相关文档

- [Deploy Runbook](../deploy/deploy-runbook.md)
- [Claude Repo-local Usage Help](../usage-help/claude.md)
- [Codex Post-Deploy Behavior Tests](./codex-post-deploy-behavior-tests.md)
