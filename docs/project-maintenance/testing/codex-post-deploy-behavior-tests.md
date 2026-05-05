---
title: "Codex Post-Deploy Behavior Tests"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# Codex Post-Deploy Behavior Tests

> 目的：固定 Codex 部署后真实 Harness 行为观察的最小手动 runbook：临时 repo、隔离 `.agents/skills/`、无交互 `codex exec`、多轮观察。

本页属于 [Testing Runbooks](./README.md)。通用 deploy 主流程见 [Deploy Runbook](../deploy/deploy-runbook.md)。

## 一、适用范围

本页只回答：

- 如何初始化临时测试 repo
- 如何安装隔离的 `agents` skill payload
- 如何启动第一轮和后续轮次的无交互 Codex
- 如何监督真实执行链路

本页不承接 Harness doctrine、skill 单测模板、自动化 acceptance matrix 或评分体系。

## 二、固定题目

固定观察题目：

```text
Build a CLI Slay the Spire-lite in this temporary repo.
Reach a full core system with combat, cards, deck, map, and events.
```

验收约束：

- 只做终端交互，不做图形界面或 Web UI。
- 核心子系统至少包括 combat、battle log、cards、deck、map、events。
- 每个子系统作为独立 worktrack 推进，不在单个 worktrack 中合并多个子系统。
- 每个 worktrack 完成后 handback，等待继续信号或显式 autonomy budget。
- 提供明确运行入口和 `README.md` 运行说明。
- CLI 交互必须适合 agent 读取：标准输入/输出、状态清楚、可选动作清楚。
- repo 内提供面向 AI/agent 的游戏说明书。
- 每个子系统完成后做验证和必要测试。

测试对象不是单个 skill，而是完整 Harness 冷启动和多轮状态推进。

## 三、初始化临时 repo

```bash
TMP_ROOT="$(mktemp -d /tmp/harness-spire-lite.XXXXXX)"
TMP_REPO="$TMP_ROOT/repo"
TMP_AGENTS_ROOT="$TMP_REPO/.agents/skills"
TMP_RUN_ROOT="$TMP_ROOT/run-artifacts"

mkdir -p "$TMP_REPO" "$TMP_RUN_ROOT"
git init "$TMP_REPO"
git -C "$TMP_REPO" branch -m main
printf 'TMP_ROOT=%s\n' "$TMP_ROOT"
```

固定条件：

- 每次观察使用新的随机临时目录。
- 不预置 `.aw/`。
- 不创建初始提交。
- `main` 是临时 repo baseline branch。

## 四、安装隔离 agents payload

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py prune \
  --all \
  --backend agents \
  --agents-root "$TMP_AGENTS_ROOT"

PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py check_paths_exist \
  --backend agents \
  --agents-root "$TMP_AGENTS_ROOT"

PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py install \
  --backend agents \
  --agents-root "$TMP_AGENTS_ROOT"

PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify \
  --backend agents \
  --agents-root "$TMP_AGENTS_ROOT"
```

当前 `agents` install 已包含全部 19 个 skills，覆盖 `RepoScope`、`WorktrackScope`、验证、裁决、恢复、收尾和通用执行 worker。`set-harness-goal-skill` 自带 `.aw/` 初始化资产；本 runbook 不通过外部 scaffold 预置 `.aw/`。

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
You are running inside a temporary repo used for Harness manual observation.

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
- If `.aw/` is missing, `harness-skill` should route to `set-harness-goal-skill` to initialize the control plane.
```

运行：

```bash
codex exec \
  --cd "$TMP_REPO" \
  --skip-git-repo-check \
  --output-last-message "$TMP_RUN_ROOT/round-000/final.txt" \
  < "$TMP_RUN_ROOT/round-000/init.prompt.md" \
  2>&1 | tee "$TMP_RUN_ROOT/round-000/session.log"
```

保留产物：

- `session.log`
- `final.txt`
- `.aw/`
- `git -C "$TMP_REPO" status --short`
- `git -C "$TMP_REPO" diff --stat`

## 七、后续轮次

默认后续 prompt 只写最小继续指令。

`round-001`：

```bash
mkdir -p "$TMP_RUN_ROOT/round-001"
cat > "$TMP_RUN_ROOT/round-001/continue.prompt.md" <<'EOF'
Continue via `harness-skill`.
Respect the current `.aw/control-state.md`, Worktrack artifacts, handback guard, and autonomy budget.
Do not unlock handback unless the control state already grants continuous autonomy.
EOF

codex exec \
  --cd "$TMP_REPO" \
  --skip-git-repo-check \
  --output-last-message "$TMP_RUN_ROOT/round-001/final.txt" \
  < "$TMP_RUN_ROOT/round-001/continue.prompt.md" \
  2>&1 | tee "$TMP_RUN_ROOT/round-001/session.log"
```

`round-0xx` 复制同一形态，只递增目录名。只有在诊断某种恢复行为时，才写长 prompt；不要把授权逻辑临时塞回每轮 prompt prose。

## 八、监督方式

监督时读取每轮完整产物，而不是只看 `final.txt`：

- `session.log`
- `final.txt`
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
- 日志显示 Codex runtime 或环境问题，而非 Harness payload 问题

## 十、相关文档

- [Testing Runbooks](./README.md)
- [Deploy Runbook](../deploy/deploy-runbook.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)
- [Harness 运行协议](../../harness/foundations/Harness运行协议.md)
