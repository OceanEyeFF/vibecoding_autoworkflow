---
title: "Autoresearch closeout acceptance gate"
status: superseded
updated: 2026-04-08
owner: aw-kernel
last_verified: 2026-04-08
---

# Autoresearch closeout acceptance gate

> 非默认入口。本文只保留 closeout acceptance gate 的审计与复跑说明；只有在复核 closeout lineage / audit 或重跑 gate 证据链时才进入。日常入口先回到 [README.md](./README.md) 中的 `autoresearch-minimal-loop / research-cli-help / tmp-exrepo-maintenance`。

> 目的：把当前 `autoresearch` closeout 的验收动作收成一条可重复的 gate 链，明确先做什么、失败时停在哪里、如何回填状态。

## 一、范围

本文只覆盖当前 closeout 的验收阶段：

- `Scope Gate`
- `Spec Gate`
- `Static Gate`
- `Test Gate`
- `Smoke Gate`

本文不负责：

- 下一阶段 implementation 规划
- runtime 语义调整
- `.autoworkflow/manual-runs/` 的内容改写

## 二、执行入口

首选真实现入口：

- `toolchain/scripts/test/closeout_acceptance_gate.py`
- `toolchain/scripts/test/scope_gate_check.py`
- `toolchain/scripts/test/gate_status_backfill.py`
- `toolchain/scripts/test/governance_semantic_check.py`

说明：

- `toolchain/scripts/test/` 承载真逻辑
- 根目录 `tools/` 保留兼容入口，内部委托到 `toolchain/scripts/test/` 的真实实现
- review-loop / harness 若要求执行 `python tools/...`，应走这些兼容入口；真实逻辑仍以 `toolchain/scripts/test/` 为准

## 三、推荐顺序

1. 先跑 `Scope Gate`
2. 再跑 `Spec Gate`
3. 再跑 `Static Gate`
4. 再跑 `Test Gate`
5. 再跑 `Smoke Gate`
6. 最后回填每个 gate 的状态

## 四、判定口径

- `Scope Gate`：确认当前工作区没有越界修改
- `Spec Gate`：先确认 doc/entrypoint 结构没有偏离当前治理主线，再确认关键模板、承接关系和 foundations 权威位没有发生最小语义回退
- `Static Gate`：确认新增脚本至少能被 Python 解析
- `Test Gate`：确认针对 gate/backfill 的最小测试仍然通过，并始终执行三路 `adapter_deploy.py verify`。如果当前 isolated worktree 只有 `missing-target-root` 这一类环境缺口，则把该 backend 记录成 `skipped`；但 CLI 失效、source root 缺失、broken symlink、wrong-type target root 等真实 drift 仍必须继续失败。
- `Smoke Gate`：优先检查当前 worktree 中 materialize 的 retained run；若当前 worktree 未 materialize 这些 fixture，则回退到 primary worktree 中对应的 retained run。只有在 retained fixture 明确存在时，才允许通过；如果当前与 primary worktree 都找不到所需 retained runtime artifact，必须失败，不能把证据缺失写成 `skipped`

## 五、状态回填

每个 gate 完成后，都应调用：

```bash
python tools/gate_status_backfill.py \
  --workflow-id autoresearch-closeout-governance-task-list-20260402 \
  --gate <gate> \
  --status <status> \
  --details '<json>'
```

其中 `<status>` 现在允许写回 `passed / failed / blocked / partial / skipped`；如果 gate 只因环境缺口被跳过，必须落成 `skipped` 并在 `details` 里带上 `skip_reasons`，不能伪装成 `passed`。

回填会同步写入：

- `.autoworkflow/state/harness-task-list.json`
- `.autoworkflow/closeout/<workflow_id>/gates/<gate>.json`
- `.autoworkflow/closeout/<workflow_id>/summary.json`

## 六、失败协议

任何一项出现失败时：

- 先停止后续 gate
- 保留当前 backfill
- 不要跳过失败项直接进入交付
- 如果需要 fallback，先报告并等待确认

## 七、与 G-401 的关系

`G-401` 负责把这条 gate 链收成正式 closeout 验收动作。
`gate_status_backfill.py` 负责把执行事实写回 harness 状态。
