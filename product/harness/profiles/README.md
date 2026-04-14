# Harness Profiles

这里预留给 policy profile 与 workflow variant 的源码入口。

当前阶段，legacy `simple/strict/task-list` 资产先作为可回收 profile 保留。

当前分类：

| legacy asset | 处理方式 | 目标定位 |
|---|---|---|
| `simple-workflow` | `deprecate` | legacy profile |
| `strict-workflow` | `deprecate` | legacy profile |
| `task-list-workflow` | `downgrade` | workflow/profile 变体 |

这些资产可以继续回收：

- scope freeze 规则
- evidence 阶段切分
- completion / residual risk 报告结构

但不再作为 Harness ontology 的顶层命名。
