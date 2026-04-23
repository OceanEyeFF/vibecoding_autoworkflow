---
title: "Codex Harness Manual Run Evidence - Continuous Autonomy - 2026-04-23"
status: active
updated: 2026-04-23
owner: aw-kernel
last_verified: 2026-04-23
---

# Codex Harness Manual Run Evidence - Continuous Autonomy - 2026-04-23

本页记录一次按 [Codex Harness Manual Runbook](./codex-harness-manual-runbook.md) 执行的 `continuous-autonomy` 真实观察结果。它是运行证据摘要，不是新的 runbook。

## Run Identity

| Field | Value |
|---|---|
| `OBSERVATION_PROFILE` | `continuous-autonomy` |
| `TMP_ROOT` | `/tmp/harness-spire-lite.pq1SvT` |
| 临时 repo | `/tmp/harness-spire-lite.pq1SvT/repo` |
| 运行产物 | `/tmp/harness-spire-lite.pq1SvT/run-artifacts` |
| runner log | `/tmp/harness-spire-lite.20260423165517.208206.runner.log` |
| 最后一轮输出 | `/tmp/harness-spire-lite.pq1SvT/run-artifacts/round-020/final.txt` |
| 控制状态 | `/tmp/harness-spire-lite.pq1SvT/repo/.aw/control-state.md` |
| 执行日期 | 2026-04-23 |
| 固定题目 | CLI Slay the Spire-lite |

`/tmp` 路径不是长期归档位置。本页只写回已核对的运行事实；原始逐轮 `events.jsonl`、`stderr.txt`、`final.txt`、`exit-code.txt` 和临时 repo 文件仍以该临时路径为源证据。

## Executive Result

本次 `continuous-autonomy` 生效。流程如下：

1. `round-000` 从空 repo 初始化 `.aw/`，设置 `max_auto_new_worktracks: 20` 和 `autonomy_budget_remaining: 20`。
2. `round-000` 到 `round-005` 完成固定题目的六个 subsystem：combat、combat logger、cards、deck、map、events。
3. `round-006` 到 `round-019` 推进 run-level integration、glue 和验证切片。
4. `round-019` 关闭 `WT-020-run-loss-outcome-validation` 后预算降为 `0`。
5. `round-020` 的裸 `继续工作` 未解锁、未开新 worktrack，正确停在 strict handback。

最终控制状态：

- `repo_scope: active`
- `worktrack_scope: closed`
- `Active Worktrack: none`
- `needs_programmer_approval: true`
- `post_contract_autonomy: delegated-minimal`
- `max_auto_new_worktracks: 20`
- `handoff_state: awaiting-handoff`
- `handback_lock_active: yes`
- `autonomy_budget_remaining: 0`
- `autonomous_worktracks_opened: 20`

## Round Audit

所有轮次顶层入口均为 `harness-skill`。**本次未观察到真实 SubAgent 创建**；`round-000` 到 `round-019` 的执行均记录为 current-carrier fallback，`round-020` 未进入下游 worktrack。

技能缩写：

| 缩写 | 全称 |
|---|---|
| `H` | `harness-skill` |
| `SG` | `set-harness-goal-skill` |
| `RS` | `repo-status-skill` |
| `RN` | `repo-whats-next-skill` |
| `IW` | `init-worktrack-skill` |
| `WS` | `worktrack-status-skill` |
| `SW` | `schedule-worktrack-skill` |
| `D` | `dispatch-skills` |
| `RE` | `review-evidence-skill` |
| `TE` | `test-evidence-skill` |
| `RC` | `rule-check-skill` |
| `G` | `gate-skill` |
| `CW` | `close-worktrack-skill` |
| `RR` | `repo-refresh-skill` |

每轮通用的标准技能链（`round-020` 除外）：

```
H -> RS/RN -> IW/WS/SW/D -> RE/TE/RC/G -> CW/RR
```

| Round | Worktrack | 技能链（差异点） | 本轮完成内容 | 测试/编译 | 预算 |
|---|---|---|---|---|---|
| `round-000` | `WT-001-combat-core` | `+SG` | 初始化 `.aw/`；实现 combat、CLI、README、AI manual | 6 tests OK | 20→19 |
| `round-001` | `WT-002-combat-logger` | 标准链 | 新增结构化 replay logger、`log/replay` CLI | 11 tests OK | 19→18 |
| `round-002` | `WT-003-cards` | 标准链 | 新增 cards-only 子系统和 `cards/card` CLI | 16 tests passed | 18→17 |
| `round-003` | `WT-004-deck` | 标准链 | 新增 deck、draw/discard/hand/played piles、deck CLI | 23 tests OK | 17→16 |
| `round-004` | `WT-005-map` | 标准链 | 新增 typed map/path 子系统和 `map/paths/choosepath` CLI | 29 tests OK | 16→15 |
| `round-005` | `WT-006-events` | 标准链 | 新增事件定义、选择、效果、事件 CLI | 36 tests OK | 15→14 |
| `round-006` | `WT-007-combat-card-effects` | 标准链 | cards/deck 接入 combat，支持能量和 `playcard` | 42 tests + py_compile OK | 14→13 |
| `round-007` | `WT-008-map-combat-run` | 标准链 | 新增 `RunState`，run 从 combat map node 开始，胜利后解锁路径 | 46 tests OK | 13→12 |
| `round-008` | `WT-009-event-node-run` | 标准链 | event map node 接入 run 流程 | 48 tests + py_compile OK | 12→11 |
| `round-009` | `WT-010-starter-route-completion` | 标准链 | 补全 starter route 测试/文档 | 50 tests OK | 11→10 |
| `round-010` | `WT-011-route-variant-validation` | 标准链 | 补 event-to-rest、combat-to-rest 路线覆盖 | 52 tests OK | 10→9 |
| `round-011` | `WT-012-entrypoint-help-validation` | 标准链 | 验证 `python -m spirelite`、help/quit/EOF | 56 tests OK | 9→8 |
| `round-012` | `WT-013-error-path-validation` | 标准链 | 新增错误路径测试，确认非法输入不突变状态 | 61 tests OK | 8→7 |
| `round-013` | `WT-014-command-alias-validation` | 标准链 | 新增命令 alias 覆盖 | 73 tests OK | 7→6 |
| `round-014` | `WT-015-input-end-progress-validation` | 标准链 | 修正未完成路线 EOF 为 `Outcome: quit` | 75 tests OK | 6→5 |
| `round-015` | `WT-016-rest-shop-pass-through-validation` | 标准链 | 验证 rest/shop pass-through 和 no-active-combat 行为 | 79 tests OK | 5→4 |
| `round-016` | `WT-017-terminal-stdin-validation` | 标准链 | 验证终局后忽略后续 stdin | 80 tests OK | 4→3 |
| `round-017` | `WT-018-event-run-context-sync` | `-WS` | 同步 event/combat 的 HP、deck、run context | 82 tests + compileall OK | 3→2 |
| `round-018` | `WT-019-post-combat-replay-validation` | 标准链 | 验证 combat 结束后 `log` 仍可看最近 replay | 84 tests OK | 2→1 |
| `round-019` | `WT-020-run-loss-outcome-validation` | 标准链 | 验证 loss outcome 和非 0 exit code；预算耗尽 | 86 tests OK | 1→0 |
| `round-020` | 未创建 | `H` 只读 | 验证预算耗尽后 strict handback：裸 `继续工作` 被阻止，未开新 worktrack，未改文件 | 未跑测试 | 验证 handback |

## Verified Product State

最终临时 repo 包含可运行的 lightweight starter-map run demo：

| 文件 | 职责 |
|---|---|
| `spirelite/combat.py` | HP、block、turn、enemy intent、能量、card-effect play、outcome 与命令路由 |
| `spirelite/combat_log.py` | 结构化 replay event 与 append-only combat replay log |
| `spirelite/cards.py` | starter card catalog、card lookup、JSON-line serialization |
| `spirelite/deck.py` | draw/discard/hand/played piles、seeded shuffle recycling 与 JSON serialization |
| `spirelite/map.py` | typed combat/rest/shop/event nodes、starter path、legal movement 与 terminal detection |
| `spirelite/events.py` | event definition、choice、effect、context mutation 与 deterministic unresolved-event rolling |
| `spirelite/run.py` | starter map progression、combat/event node resolution、run context sync、path locking 与 outcome propagation |
| `spirelite/cli.py` / `__main__.py` | AI-friendly stdin/stdout 入口 |
| `README.md` / `docs/ai-manual.md` | 运行、测试、命令、路线、EOF、alias、error path 与 replay 说明 |

测试覆盖文件：`tests/test_combat.py`、`test_cards.py`、`test_deck.py`、`test_map.py`、`test_events.py`、`test_run.py`、`test_cli_entrypoint.py`、`test_cli_errors.py`、`test_cli_aliases.py`。

## Verification

复跑命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests
PYTHONDONTWRITEBYTECODE=1 python -m compileall -q spirelite tests
```

结果：

- `unittest discover`：`Ran 86 tests ... OK`
- `compileall`：passed
- `round-000` 到 `round-020`：每轮 `exit-code.txt` 均为 `0`
- `round-020`：未进入下游 worktrack、未改文件、未跑测试；只验证 budget=0 后的 handback guard

部分中间轮次的 `stderr.txt` 记录了 patch/test/修复噪声，非空属于正常。最终判断以每轮 `exit-code.txt`、`final.txt`、`.aw` gate evidence、repo snapshot 和复验命令为准。

## Important Observations

- `continuous-autonomy` override 生效：`round-000` 初始化预算为 `20`，每个 autonomous worktrack 后递减，直到 `round-019` 归零。
- "每个 subsystem 独立 worktrack"和"自动连续推进"可以同时成立：每轮仍在 `stop_after_autonomous_slice` 边界 handback，但预算未耗尽时不激活硬锁。
- 固定题目六个 subsystem 在 `round-000` 到 `round-005` 完成，后续 14 个 worktrack 为 integration seam、route validation、entrypoint/help/error/alias/EOF/loss outcome 等收敛切片。
- 本次运行未创建真实 SubAgent；执行面是 current-carrier fallback。这与上一轮 strict-handback 中出现真实 worker carrier 的结果不同，属于 runtime 观察差异。
- `round-020` 证明预算耗尽后 strict handback 恢复：裸 `继续工作` 不再解锁，不再开新 worktrack。
- 临时 repo 仍为 no-commit / unborn baseline；`git status` 显示 `.agents/`、`.aw/`、product files、tests 和 docs 为 untracked，是 runbook 规定的观察状态。

## Known Residual Scope

当前产品仍不是完整 Slay the Spire 复刻，也不是完整 run 系统。以下内容仍是 deferred scope：

- shop/rest gameplay effects
- rewards
- economy spending
- scoring
- act transitions
- full-run traversal semantics
- status-effect mechanics beyond metadata
- event path rewrites

## Current Next Route

当前 `autonomy_budget_remaining: 0`，`handback_lock_active: yes`，`needs_programmer_approval: true`。后续不能再用裸 `继续工作` 解锁。

如需继续，必须显式授权，例如：

```text
批准解锁 handback，进入 RepoScope.Observe，并允许 Harness 选择下一个受限 worktrack。
```

或直接指定新的工作范围。
