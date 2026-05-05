---
title: "Claude Post-Deploy Behavior Tests"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# Claude Post-Deploy Behavior Tests

> 目的：固定 Claude Code 部署后真实 Harness 行为观察的最小手动 runbook：临时 repo、隔离 `.claude/skills/`、无交互 `claude --bare -p`、多轮观察。

本页属于 [Testing Runbooks](./README.md)。通用 deploy 主流程见 [Deploy Runbook](../deploy/deploy-runbook.md)，Claude 使用入口见 [Claude Repo-local Usage Help](../usage-help/claude.md)。

## 一、适用范围

本页只回答：

- 如何初始化临时测试 repo
- 如何安装隔离的 Claude project-level skill payload
- 如何启动第一轮和后续轮次的无交互 Claude Code
- 如何用当前环境下的 Codex 监督真实执行链路

本页不承接 Harness doctrine、skill 单测模板、自动化 acceptance matrix、评分体系或 Claude 产品定位。

## 二、固定题目

固定观察题目与 Codex runbook 保持一致：

```text
Build a CLI Slay the Spire-lite in this temporary repo.
Reach a full core system with combat, cards, deck, map, and events.
```

验收约束：

- 只做终端交互，不做图形界面或 Web UI。
- 核心子系统至少包括 combat、battle log、cards、deck、map、events。
- 每个子系统作为独立 worktrack 推进，不在单个 worktrack 中合并多个子系统。
- 每个 worktrack 完成后 handback，等待继续信号或显式 autonomy budget。
- 提供明确运行入口、`README.md` 运行说明和面向 AI/agent 的游戏说明书。
- 每个子系统完成后做验证和必要测试。

## 三、初始化临时 repo

```bash
TMP_PARENT="${TMP_PARENT:-$HOME/tmp}"
mkdir -p "$TMP_PARENT"
TMP_ROOT="$(mktemp -d "$TMP_PARENT/harness-claude-spire-lite.XXXXXX")"
TMP_REPO="$TMP_ROOT/repo"
TMP_CLAUDE_ROOT="$TMP_REPO/.claude/skills"
TMP_RUN_ROOT="$TMP_ROOT/run-artifacts"
CLAUDE_TEST_HOME="$TMP_ROOT/claude-home"
NPM_CONFIG_CACHE="$TMP_ROOT/npm-cache"

mkdir -p "$TMP_REPO" "$TMP_RUN_ROOT"
git init "$TMP_REPO"
git -C "$TMP_REPO" branch -m main
printf '.claude/\n' >> "$TMP_REPO/.git/info/exclude"
printf 'TMP_ROOT=%s\n' "$TMP_ROOT"
```

固定条件：

- 默认临时根在 `$HOME/tmp`，满足 deploy path safety policy。
- `.claude/` 是 deploy target，用 `.git/info/exclude` 排除。
- 不预置 `.aw/`，不创建初始提交。
- `NPM_CONFIG_CACHE` 必须指向本轮临时目录，避免回落到宿主默认 cache。

如果当前 carrier 的 `$HOME/.claude` 不可写，使用临时 Claude home，只复制本机运行所需登录状态：

```bash
mkdir -p "$CLAUDE_TEST_HOME/.claude"
test -f "$HOME/.claude.json" && cp "$HOME/.claude.json" "$CLAUDE_TEST_HOME/.claude.json"
test -d "$HOME/.claude" && find "$HOME/.claude" -maxdepth 1 -type f -exec cp {} "$CLAUDE_TEST_HOME/.claude/" \;
```

整理外发日志前必须确认没有泄露本机认证文件内容。

## 四、安装隔离 Claude payload

验证本地 candidate package 时优先用 `.tgz`：

```bash
PACKAGE_TGZ="/path/to/aw-installer-<version>.tgz"

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

只观察源码 checkout 行为时，可用 repo-local Python reference：

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

当前 `claude` install 已包含全部 19 个 skills。`set-harness-goal-skill` 自带 `.aw` 初始化资产；cold-start helper 以 `scripts/deploy_aw.js` 随 payload 分发，Python helper 只作为源码侧 reference。

## 五、选择观察策略

启动 `round-000` 前记录本轮策略：

```text
OBSERVATION_PROFILE=strict-handback
```

或：

```text
OBSERVATION_PROFILE=continuous-autonomy
```

| Observation profile | 权威字段含义 | 观察目标 |
| --- | --- | --- |
| `strict-handback` | `Continuation Authority` / `Handback Guard` 让 `handoff_state` 停在 handback，`autonomy_budget_remaining: 0` 或没有显式重新授权 | 验证每个 worktrack 完成后是否稳定停在交接边界 |
| `continuous-autonomy` | `post_contract_autonomy: delegated-minimal`，`autonomy_scope: current-goal-only`，`autonomy_budget_remaining > 0` | 验证 Harness 是否能在当前 goal 内连续打开 bounded subsystem worktrack |

不要把两种策略混在同一轮观察里。`continuous-autonomy` 只改变 handback 后是否允许继续消费预算，不删除“每个子系统独立 worktrack”的约束。

## 六、round-000

```bash
mkdir -p "$TMP_RUN_ROOT/round-000"
```

写入 `"$TMP_RUN_ROOT/round-000/init.prompt.md"`：

```text
Use only `harness-skill` as the top-level control entry.

This is a cold-start scenario: the repo is empty and `.aw/` does not exist.
Harness must initialize the reference signal first, then proceed through the full control loop.

User requirement:
Build a CLI Slay the Spire-lite in this temporary repo.
Reach a full core system with combat, cards, deck, map, and events.

Working rules:
- This is a non-interactive test. After `set-harness-goal-skill` analyzes requirements, directly generate and write the goal charter, control state, and repo snapshot to `.aw/` without waiting for confirmation.
- Each subsystem must be a separate Worktrack.
- Complete only the first bounded subsystem slice unless the control state explicitly grants continuous autonomy.
- Use real files, real tests where useful, and record evidence in the Harness artifacts.
- If `.aw/` is missing, `harness-skill` should route to `set-harness-goal-skill`.
```

运行：

```bash
HOME="$CLAUDE_TEST_HOME" \
NPM_CONFIG_CACHE="$NPM_CONFIG_CACHE" \
claude --bare -p "$(cat "$TMP_RUN_ROOT/round-000/init.prompt.md")" \
  --cwd "$TMP_REPO" \
  2>&1 | tee "$TMP_RUN_ROOT/round-000/session.log"
```

保留产物：

- `session.log`
- Claude 最后一条事件或最终输出
- `.aw/`
- `git -C "$TMP_REPO" status --short`
- `git -C "$TMP_REPO" diff --stat`

## 七、后续轮次

默认后续 prompt：

```bash
mkdir -p "$TMP_RUN_ROOT/round-001"
cat > "$TMP_RUN_ROOT/round-001/continue.prompt.md" <<'EOF'
Continue via `harness-skill`.
Respect the current `.aw/control-state.md`, Worktrack artifacts, handback guard, and autonomy budget.
Do not unlock handback unless the control state already grants continuous autonomy.
EOF

HOME="$CLAUDE_TEST_HOME" \
NPM_CONFIG_CACHE="$NPM_CONFIG_CACHE" \
claude --bare -p "$(cat "$TMP_RUN_ROOT/round-001/continue.prompt.md")" \
  --cwd "$TMP_REPO" \
  2>&1 | tee "$TMP_RUN_ROOT/round-001/session.log"
```

`round-0xx` 复制同一形态，只递增目录名。只有在诊断恢复行为时才写长 prompt。

## 八、监督方式

监督时读取每轮完整产物：

- `session.log`
- Claude 最后一条事件或最终输出
- `.aw/control-state.md`
- `.aw/repo/*`
- `.aw/worktrack/*`
- `git status --short`
- `git diff --stat`
- 相关源码和测试结果

观察点：

- 是否从 `.aw/` 缺失正确进入 `set-harness-goal-skill`
- 是否建立 goal、snapshot、control state
- 是否进入 `RepoScope -> WorktrackScope`
- 是否只打开 bounded subsystem worktrack
- 是否使用 `dispatch-skills`
- 是否产生 review / test / rule-check / gate evidence
- 是否在 handback 或 continuous-autonomy 策略下表现一致

## 九、继续与停止

继续观察的条件：

- 当前轮没有 hit stop condition
- control state 允许下一轮
- 还有未完成 subsystem
- 当前 evidence 足以支持下一轮

停止观察的条件：

- 明显命中 handback boundary
- Gate fail / blocked
- scope 切换已经达到观察目的
- runtime dispatch gap 需要人工判断
- Claude Bash tool 因宿主 `$HOME/.claude/session-env` 只读而失败；应切换到 `CLAUDE_TEST_HOME` 后重跑，不能归因于 package payload

## 十、相关文档

- [Testing Runbooks](./README.md)
- [Codex Post-Deploy Behavior Tests](./codex-post-deploy-behavior-tests.md)
- [Deploy Runbook](../deploy/deploy-runbook.md)
- [Claude Repo-local Usage Help](../usage-help/claude.md)
- [Harness 运行协议](../../harness/foundations/Harness运行协议.md)
