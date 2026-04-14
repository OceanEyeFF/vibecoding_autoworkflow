# Harness Product Source

`product/harness/` 是 Harness-first 的源码叙事入口。

当前目标结构：

- [core/contracts/README.md](./core/contracts/README.md)
- [core/governance/README.md](./core/governance/README.md)
- [core/shared/README.md](./core/shared/README.md)
- [workflows/repo-evolution/README.md](./workflows/repo-evolution/README.md)
- [profiles/README.md](./profiles/README.md)
- [adapters/README.md](./adapters/README.md)
- [manifests/README.md](./manifests/README.md)

当前 ownership：

| 目标层 | 当前承接内容 | 迁移来源 |
|---|---|---|
| `core/contracts/` | Harness core contract、artifact shape、state-machine contract | `execution-contract-template`、`harness-contract-shape`、`task-planning-contract` 的可拆分部分 |
| `core/governance/` | gate、authority、illegal transitions、治理约束 | `repo-governance-evaluation` 和 `harness-contract-shape` 的治理部分 |
| `core/shared/` | shared body、shared bindings、runtime discipline | `product/harness-operations/skills/harness-standard.md` |
| `workflows/repo-evolution/` | repo evolution family 的 workflow source | `task-planning-contract`、`task-list-workflow`、`review-loop-workflow` 的可回收部分 |
| `profiles/` | policy profile 与 workflow variant | `simple-workflow`、`strict-workflow`、`task-list-workflow` |
| `adapters/` / `manifests/` | Harness-first adapter/manifests 目标位 | 迁移完成前仍以 `product/harness-operations/` 为 deploy source |

迁移说明：

- 第一阶段不强制把 `product/memory-side/` 与 `product/task-interface/` 移入本目录
- 当前 legacy skill 与 adapter source 仍主要保留在 [../harness-operations/README.md](../harness-operations/README.md)
- 新的 ontology、源码叙事与后续重组应优先落到本目录
- 新增 Harness-first 语义时，先决定它属于 `core / workflows / profiles / adapters / manifests` 哪一层，再决定是否需要回收 legacy asset

当前已抽出的第一批正式 source：

- `core/shared/`
  - [contract-runtime-boundary.md](./core/shared/contract-runtime-boundary.md)
  - [runtime-binding-policy.md](./core/shared/runtime-binding-policy.md)
  - [gate-discipline.md](./core/shared/gate-discipline.md)
  - [state-discipline.md](./core/shared/state-discipline.md)
- `core/contracts/`
  - [execution-contract.template.md](./core/contracts/execution-contract.template.md)
  - [harness-contract.template.json](./core/contracts/harness-contract.template.json)
  - [task-planning-contract.template.md](./core/contracts/task-planning-contract.template.md)
- `core/governance/`
  - [harness-governance-fields.md](./core/governance/harness-governance-fields.md)
  - [repo-governance-evaluation.contract.md](./core/governance/repo-governance-evaluation.contract.md)
