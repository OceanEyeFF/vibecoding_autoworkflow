# Harness Profiles

这里承接 policy profile 与 workflow variant 的正式源码入口。

当前 extracted source：

- [simple.profile.md](./simple.profile.md)
- [strict.profile.md](./strict.profile.md)
- [task-list.variant.md](./task-list.variant.md)

当前分类：

| legacy asset | 处理方式 | 目标定位 |
|---|---|---|
| `simple-workflow` | `deprecate` | `simple.profile.md` |
| `strict-workflow` | `deprecate` | `strict.profile.md` |
| `task-list-workflow` | `downgrade` | `task-list.variant.md` |

这些资产可以继续回收：

- scope freeze 规则
- evidence 阶段切分
- completion / residual risk 报告结构

但不再作为 Harness ontology 的顶层命名，也不再独占 workflow family 语义。
