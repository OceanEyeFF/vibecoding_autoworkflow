---
title: "Milestone Artifact"
status: active
updated: 2026-05-10
owner: aw-kernel
last_verified: 2026-05-10
---

# Milestone Artifact

> Milestone 是 `RepoScope` 下的聚合对象/控制条件/progress counter/environment probe。不创建第三 Scope，不接管 version management。

## 定位

- 属于 `RepoScope`，是 `Observe`/`Decide` 阶段的输入。
- 记录多个 worktrack 的聚合目标、完成阈值和验收边界。
- 不选择下一 Worktrack（`RepoScope.Decide` 的职责）。
- 不初始化 worktrack（`init-worktrack-skill` 的职责）。
- 不修改 version/release 状态。

## 字段定义

| 字段 | 类型 | 说明 |
|------|------|------|
| milestone_id | string | 唯一标识 |
| title | string | Milestone 名称 |
| purpose | string | Milestone 目的描述 |
| status | enum | planned / active / completed / superseded |
| worktrack_list | array | 包含的 worktrack ID 列表及每个 worktrack 的预期状态 |
| completion_signals | array | 完成信号列表（可观察的事实） |
| acceptance_criteria | array | Milestone 级验收标准 |
| progress_counter | object | 进度计数器（total / completed / blocked / deferred） |
| environment_probe | object | [reserved] 预留字段，暂无操作语义 |
| aggregated_evidence | array | 聚合的 evidence 引用 |
| release_version_consideration | string | 对 version/release 的提示（不接管 decision） |
| developer_decision_boundary | array | 标记哪些决定必须由 developer 做出 |
| depends_on_milestones | array | 前置 Milestone 列表 |
| updated | date | 最后更新时间 |
| `priority` | integer | Pipeline 中的优先级（数值越小优先级越高） |
| `activation_rules` | string | 自动激活条件（optional，harness-inferred）；描述 harness 可自动激活的前提，空值表示仅 manual |
| `created_by` | enum | `programmer` / `harness` — 创建来源 |

## 生命周期

Milestone 在其生命周期中经历四个状态：

```
planned ──→ active ──→ completed
  │                        │
  └──────→ superseded ←────┘
```

- **planned**: 已创建，尚未激活。等待前置 milestone 完成或 programmer 手动激活。
- **active**: 当前正在推进，worktrack 执行中。同一时刻仅允许一个 active milestone。
- **completed**: 目的达成（`purpose_achieved == true`），worktrack 列表全部处理完毕（`worktrack_list_finished == true`）。双重验收通过后由 `harness-skill` 执行状态转移。
- **superseded**: 被更新的 milestone 替换（programmer override），保留历史但不参与激活队列。

## Pipeline 语义

Milestone 作为 Pipeline 中的节点，遵循以下规则：

- 多个 milestone 可同时处于 `planned` 状态，按 `priority`（升序）排列激活顺序
- 同一时刻仅允许一个 `active` milestone
- `depends_on_milestones` 中的所有前置 milestone 必须为 `completed` 或 `superseded`，当前 milestone 才可激活
- milestone 完成后（`active` → `completed`），pipeline 按优先级自动选择下一个满足条件的 `planned` milestone 激活
- `priority` 同值时按 `updated` 时间排序
- `activation_rules` 非空时，harness 可在满足描述的条件后自动激活；空值表示需 programmer 显式审批

## Latest Override 语义

同一 `milestone_id` 的写入遵循 latest-override：

- 以 `updated` 时间戳为判断依据：更新的写入覆盖旧数据
- programmer 和 harness 均可写入，同时间戳 programmer 优先
- `superseded` 状态是 override 的一种形式：创建新 milestone 时可标记旧 milestone 为 superseded

## 双重验收模型

Milestone 完成判定必须同时满足两个条件：

1. **worktrack_list_finished**: 声明的 worktrack 列表已完成 / 被明确移出 / 阻塞有决策
2. **purpose_achieved**: Milestone 原始目的是否经聚合 evidence 证明达成

两者缺一时不得自动判定 Milestone 完成。

## 与 Worktrack 的关系

- Milestone 引用 Worktrack，不控制 Worktrack 内部状态转移。
- Worktrack closeout 后，Milestone progress counter 更新。
- 不替代 `WorktrackContract` 或 `PlanTaskQueue`。

## 与 RepoScope 的关系

- Milestone 是 `RepoScope.Observe` 的 sensor 输入。
- Milestone 完成/阻塞信号影响 `RepoScope.Decide` 的决策。
- Milestone 验收边界是 continuous execution 的合法 handback 点。

## 使用约定

- 由 programmer 或 `harness-skill`（`RepoScope.Decide` 阶段）创建。
- 进度由 `milestone-status-skill` 独立分析。
- 不自动触发 release/publish/version bump。
