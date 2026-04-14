# Harness Core Governance

这里预留给 Harness core 的治理实现与共享约束。

当前阶段优先承接：

- gate 语义
- authority 约束
- state-machine legality

当前回收映射：

| legacy asset | 处理方式 | 目标责任 |
|---|---|---|
| `repo-governance-evaluation` | `downgrade` | 治理评估子能力，而不是上位 ontology |
| `harness-contract-shape` | `split` | contract 中的 `gates / governance / risk_triage` 字段约束 |

本目录不负责 workflow profile 命名，也不直接承担 backend deploy source。
