---
title: Harness Runtime Dispatch Contract
status: active
updated: 2026-05-16
owner: aw-kernel
last_verified: 2026-05-16
---

# Harness Runtime Dispatch Contract

> 目的：固定 Dispatch / Implement 边界、执行载体选择和 fallback 语义。载体选择策略见 [dispatch-decision-policy.md](./dispatch-decision-policy.md)；packet 字段见 [dispatch-packet.md](../artifact/worktrack/dispatch-packet.md)。

## Control Plane And Execution Plane

Harness 本体属于控制平面。

控制平面负责：

- 选择下一合法算子
- 绑定 skill 或执行载体
- 打包任务与信息
- 定义证据面
- 裁决状态能否推进
- 安排恢复或收尾

执行平面负责实际改变 repo：

- 编码
- review
- test
- 文档更新
- merge / cleanup / rollback

## Dispatch / Implement Boundary

`Dispatch` 属控制平面：选择载体、打包任务并分派，不直接执行 repo 变更。

`Implement` 属执行平面：接收 dispatch packet，执行编码、review、测试、文档更新等变更动作，返回结构化执行结果与证据。

一次 `Dispatch` 对应一次 `Implement` 往返。`Implement` 完成后，控制权回到 `Verify` / `Judge`。控制平面决定"做什么、谁来做、怎么验收"；执行平面完成"实际做并回传结果"。

## Execution Carrier Switches

执行载体开关：

- 默认值为 `auto`
- `subagent_dispatch_mode`: `auto | delegated | current-carrier`
- `subagent_dispatch_mode_override_scope`: 默认 `worktrack-contract-primary`
- 仅 `global-override` 时，`.aw/control-state.md` 的 `subagent_dispatch_mode` 压过 worktrack contract
- worktrack 未声明 `runtime_dispatch_mode` 时使用 control-state default

模式语义：

| 模式 | 语义 |
| --- | --- |
| `auto` | 按 Dispatch Decision Policy 选择 SubAgent、专用 skill、generic worker 或 current-carrier；无法安全委派时标记 fallback |
| `delegated` | 必须真实委派。无法委派时返回运行时缺口或权限阻塞 |
| `current-carrier` | 显式关闭 SubAgent 委派，由当前载体执行同一份 bounded contract |

## Dispatch Packet Minimum

最小 dispatch packet：

- work item id 与目标
- scope / non-goals / acceptance
- 允许读取的 artifact 和代码入口
- 禁止扩展的边界
- shared fact pack
- context budget
- 预期输出
- evidence 回传格式
- rollback / recovery hint

完整字段由 [dispatch-packet.md](../artifact/worktrack/dispatch-packet.md) 承接。Runtime protocol 只规定边界和选择语义，不复制 packet schema。

## Fallback Rules

没有匹配专用 skill 时，`dispatch-skills` 可生成一次性任务指令并绑定通用执行载体。不得将此类指令写成新的 canonical skill。

只有以下情况允许 current-carrier fallback：

- `runtime_dispatch_mode` 或 `subagent_dispatch_mode` 明确为 `current-carrier`
- `auto` 判定任务强共享状态、低并行价值或不适合分派
- host runtime 缺少真实 SubAgent dispatch shell
- permission boundary 禁止委派
- dispatch package unsafe

发生 fallback 时，输出必须记录 `runtime fallback`、`permission blocked` 或 `dispatch package unsafe`。没有真实创建委派载体时，不得声称已经使用 SubAgent。
