---
title: "Autoresearch closeout acceptance gate"
status: active
updated: 2026-04-02
owner: aw-kernel
last_verified: 2026-04-02
---
# Autoresearch closeout acceptance gate

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

说明：

- `toolchain/scripts/test/` 承载真逻辑
- 当前 closeout gate 不再引入额外根目录 shim；命令入口统一收敛到 `toolchain/scripts/test/`

## 三、推荐顺序

1. 先跑 `Scope Gate`
2. 再跑 `Spec Gate`
3. 再跑 `Static Gate`
4. 再跑 `Test Gate`
5. 再跑 `Smoke Gate`
6. 最后回填每个 gate 的状态

## 四、判定口径

- `Scope Gate`：确认当前工作区没有越界修改
- `Spec Gate`：确认 doc/entrypoint 结构没有偏离当前治理主线
- `Static Gate`：确认新增脚本至少能被 Python 解析
- `Test Gate`：确认针对 gate/backfill 的最小测试仍然通过，并完成三路 `adapter_deploy.py verify --target local`
- `Smoke Gate`：确认 retained run 的 `runtime.json` 没有残留 `active_round`，并对 `gate_status_backfill.py` 做一次 `--dry-run` smoke，确认真入口和参数解析可重复执行

## 五、状态回填

每个 gate 完成后，都应调用：

```bash
python toolchain/scripts/test/gate_status_backfill.py \
  --workflow-id autoresearch-closeout-governance-task-list-20260402 \
  --gate <gate> \
  --status <status> \
  --details '<json>'
```

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
