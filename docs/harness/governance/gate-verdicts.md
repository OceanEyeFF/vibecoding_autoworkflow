---
title: "Gate Verdicts"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Gate Verdicts

`Gate` 至少区分下面 4 种裁决：

| verdict | 含义 | 典型后续动作 |
|---|---|---|
| `pass` | 当前证据充分，允许进入下一合法状态 | integrating / closeout |
| `soft-fail` | 有问题，但仍可在当前 worktrack 内补证或返工 | replan / retest / rereview |
| `hard-fail` | 当前方案或路径存在结构性问题 | rollback / split-worktrack / refresh baseline |
| `blocked` | 当前无法形成有效 verdict | wait / request authority / add missing evidence |

补充约束：

- `pass` 不等于没有瑕疵
- `soft-fail` 不要求自动改写 goal
- `hard-fail` 通常意味着合同或执行路径需要重构
- `blocked` 不是失败，而是禁止继续猜测或强推
