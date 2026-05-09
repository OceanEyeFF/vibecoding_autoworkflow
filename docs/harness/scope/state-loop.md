---
title: "Harness 状态闭环"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Harness 状态闭环

> 目的：固定 Harness 在 `RepoScope` 与 `WorktrackScope` 之间的闭环。

最小闭环：RepoScope 下观测并决定 -> 生成 Worktrack Contract -> 初始化 Worktrack 与 baseline -> 调度执行并收集 verify evidence -> gate verdict（失败则 recover）-> PR/merge/cleanup -> 回到 RepoScope 刷新 Repo Snapshot/Status。失败信号：只做到”PR 已发出”就结束、closeout 结果未回写 repo 级状态、RepoScope 与 WorktrackScope 被混成同一份状态文档。

## WorktrackScope 状态定义

WorktrackScope 下的合法状态共 11 个：

| 状态 | 含义 | 进入动作 |
|------|------|----------|
| `initializing` | Worktrack 刚创建，baseline 尚未建立 | 创建 Worktrack 上下文，初始化 task queue 骨架 |
| `observing` | 观测当前 repo 状态，收集分析信息 | 执行 RepoScope 观测，生成当前状态快照 |
| `scheduling` | 制定任务队列与执行计划 | 将 Contract 展开为 task queue，建立依赖图，生成覆盖矩阵 |
| `dispatching` | 将任务分派给 SubAgent | 生成 dispatch handoff packet，标记任务为 in_progress |
| `implementing` | SubAgent 执行具体任务 | 执行变更（代码/文档），记录产出物 |
| `verifying` | 收集验证证据（测试/检查/review） | 运行四路 review SubAgent，收集三类 evidence 面 |
| `judging` | 对 evidence 进行 gate verdict | 汇总 review 结果，按维度评分，输出 verdict |
| `recovering` | 处理 hard-fail 或异常后恢复 | 分析失败原因，修复问题，重新排队 |
| `closing` | 执行 PR/merge/cleanup | 创建 PR、合并、回写状态到 RepoScope |
| `blocked` | 不满足继续执行条件，需等待 | 记录阻塞原因，释放执行资源 |
| `closed` | 终端状态，Worktrack 生命周期结束 | 归档所有 artifact，清理临时状态 |

## 状态转移条件矩阵

下表定义 WorktrackScope 下每个状态允许转移到哪些目标状态及转移条件。

行 = 当前状态，列 = 目标状态。单元格为空表示该转移不允许。

| 当前 \ 目标 | initializing | observing | scheduling | dispatching | implementing | verifying | judging | recovering | closing | blocked | closed |
|-------------|:-----------:|:---------:|:----------:|:-----------:|:------------:|:---------:|:-------:|:----------:|:-------:|:-------:|:------:|
| **initializing** | - | baseline 快照完成 | - | - | - | - | - | - | - | 初始化失败或外部依赖缺失 | - |
| **observing** | - | - | 观测完成且无歧义 | - | - | - | - | - | - | 观测数据不可用 | - |
| **scheduling** | - | Contract 变更需重观测 | - | task queue 非空且无阻塞项 | - | - | - | - | - | 依赖信息不足无法生成队列 | - |
| **dispatching** | - | - | dispatch 超时或无可用 task | - | SubAgent 已领取 handoff packet | - | - | - | - | 无可用 SubAgent | - |
| **implementing** | - | - | - | - | - | 所有 task 完成或触发 early-verify | 所有 task 完成 | 需中断实施回退 | - | 外部阻塞 | - |
| **verifying** | - | - | - | - | evidence 不足需补充实施 | - | 所有 evidence 面收集完毕 | 验证过程发现严重问题 | - | 缺少必要验证工具 | - |
| **judging** | - | - | - | verdict: soft-fail 可带条件推进 | verdict: hard-fail | verdict: hard-fail 且需重验证 | verdict: pass | verdict: hard-fail | verdict: pass 或 soft-fail | evidence 不完整 | - |
| **recovering** | - | 恢复至干净状态重新观测 | 恢复后重新排队 | - | 轻量修复可直接实施 | 修复后重新验证 | - | - | 确认恢复后关闭 | 恢复失败 | - |
| **blocked** | - | 阻塞解除后重新观测 | 阻塞解除后继续调度 | - | - | - | - | 需恢复处理 | - | - | - |
| **closing** | - | - | - | - | - | - | - | closeout 失败需恢复 | - | closeout 过程中外部阻塞 | PR 合并且回写完成 |
| **closed** | - | - | - | - | - | - | - | - | - | - | - |

## 异常路径

### 通用异常：到 blocked 的转移

任何非终端状态在以下条件满足时，允许转移到 `blocked`：

| 触发条件 | 说明 |
|----------|------|
| 外部依赖不可用 | 如 API 服务宕机、外部工具链不可用 |
| 人工审批等待 | 如 gate verdict 需要 human reviewer 确认但未响应 |
| 资源不可用 | 如无可用 SubAgent、token 配额耗尽 |
| 证据缺失 | 如 judging 阶段发现关键 evidence 面未生成 |
| 环境异常 | 如文件系统只读、权限不足 |

进入 `blocked` 时必须记录：
- `blocked_reason`：阻塞原因
- `blocked_since`：阻塞开始时间戳
- `source_state`：从哪个状态进入 blocked
- `resolution_condition`：解除阻塞的条件（可验证的断言）

### 通用异常：到 recovering 的转移

任何非终端状态在以下条件满足时，允许转移到 `recovering`：

| 触发条件 | 说明 |
|----------|------|
| `hard-fail` verdict | judging 输出 hard-fail |
| 一致性异常 | 状态数据与 repo 实际状态不一致 |
| 合同违约 | Contract 中声明的约束被违反 |
| 未处理的异常 | 任何未被其他 handler 捕获的错误 |
| 人工干预请求 | human 要求 abort 当前流程并修复 |

进入 `recovering` 时必须记录：
- `recovery_reason`：触发恢复的原因
- `recovery_source_state`：从哪个状态进入
- `recovery_plan`：恢复计划（分析 -> 修复 -> 重新排队）

### blocked -> recovering 恢复路径

```
blocked →（阻塞解除 + 状态不一致）→ recovering
blocked →（阻塞解除 + 状态一致）→ observing（重新观测）
blocked →（阻塞解除 + 状态一致 + 任务队列完整）→ scheduling
```

从 `blocked` 到 `recovering` 的典型场景：
1. 长时间阻塞导致 baselines 过期，无法直接回到原状态
2. 阻塞期间 repo 发生了外部变更，与 blocked 前状态不一致
3. 阻塞原因是永久性的（如工具废弃），需要重新 plan

恢复步骤：
1. 分析阻塞原因和当前 repo 状态
2. 评估 blocking 期间的外部变更影响
3. 重新建立 baselines（如需）
4. 修复或调整受影响的任务队列
5. 从 `recovering` 转移到 `scheduling` 重新排队

### recovering 返回路径

```
recovering →（恢复成功 + 需重新观测）→ observing
recovering →（恢复成功 + 任务队列已修复）→ scheduling
recovering →（恢复成功 + 确认关闭）→ closing
recovering →（恢复失败）→ blocked
```

### implementing 状态异常路径

`implementing` 状态的特殊异常处理：

| 场景 | 处理方式 |
|------|----------|
| 实施过程中发现 plan 不可行 | 标记当前 task 为 blocked，返回 scheduling 重新规划 |
| 实施结果与预期偏差 | 评估偏差程度：可微调则继续；需要大改则转到 recovering |
| SubAgent 超时或无响应 | 当前 task 状态改为 blocked，dispatch 到备用 SubAgent 或等待 |
| 实施产出物冲突 | 转到 recovering 做冲突解决 |

## 状态转移的治理约束

1. 所有状态转移必须记录在 Worktrack 日志中（时间戳、源状态、目标状态、触发条件）
2. `closed` 是终端状态，不可从 `closed` 转移至任何其他状态
3. `closed` 进入条件：PR 合并完成 + repo snapshot 已刷新 + 所有 artifact 已归档
4. 不允许跨状态跳转（如从 `scheduling` 直接跳到 `verifying`，跳过 `dispatching` 和 `implementing`），除非通过异常路径
5. 同一时刻 WorktrackScope 处于唯一状态，不允许状态并存
