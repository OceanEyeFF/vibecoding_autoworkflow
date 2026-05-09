---
title: "Milestone Artifact"
status: active
updated: 2026-05-08
owner: aw-kernel
last_verified: 2026-05-08
---

# Milestone Artifact

> Milestone 是 RepoScope 下的聚合对象 / 控制条件 / progress counter / environment probe。它不创建第三 Scope，不接管 version management。

## 定位

- Milestone 属于 RepoScope，是 Observe/Decide 阶段的输入
- 它记录多个 worktrack 的聚合目标、完成阈值和验收边界
- 它不选择下一 Worktrack（那是 RepoScope.Decide 的职责）
- 它不初始化 worktrack（那是 init-worktrack-skill 的职责）
- 它不修改 version/release 状态

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
| environment_probe | object | 环境探测要求（如 "所有治理检查通过"） |
| aggregated_evidence | array | 聚合的 evidence 引用 |
| release_version_consideration | string | 对 version/release 的提示（不接管 decision） |
| developer_decision_boundary | array | 标记哪些决定必须由 developer 做出 |
| depends_on_milestones | array | 前置 Milestone 列表 |
| updated | date | 最后更新时间 |

## 双重验收模型

Milestone 完成判定必须同时满足两个条件：

1. **worktrack_list_finished**: 声明的 worktrack 列表已完成 / 被明确移出 / 阻塞有决策
2. **purpose_achieved**: Milestone 原始目的是否经聚合 evidence 证明达成

两者缺一时不得自动判定 Milestone 完成。

## 与 Worktrack 的关系

- Milestone 引用 Worktrack，但不控制 Worktrack 内部状态转移
- Worktrack closeout 后，Milestone progress counter 更新
- Milestone 不替代 Worktrack Contract 或 Plan/Task Queue

## 与 RepoScope 的关系

- Milestone 是 RepoScope.Observe 的 sensor 输入
- Milestone 完成/阻塞信号影响 RepoScope.Decide 的决策
- Milestone 验收边界是 continuous execution 的合法 handback 点

## 使用约定

- Milestone 由 programmer 或 harness-skill（在 RepoScope.Decide 阶段）创建
- Milestone 进度由 milestone-status-skill 独立分析
- Milestone 不自动触发 release/publish/version bump
